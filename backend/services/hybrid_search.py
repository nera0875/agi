#!/usr/bin/env python3
"""
Hybrid Search Service - Multi-Source Search Fusion

Combines three search paradigms:
1. BM25 - Keyword matching (PostgreSQL full-text search)
2. Semantic Search - Vector similarity (pgvector + Voyage embeddings)
3. Graph Search - Relationship traversal (Neo4j spreading activation)

Architecture:
  Query → [BM25, Semantic, Graph] → Weighted Fusion → Rerank → Top Results
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from uuid import UUID

import asyncpg
from redis import asyncio as aioredis

from backend.config.agi_config import get_config
from backend.services.voyage_embeddings import get_voyage_service
from backend.services.cohere_rerank import CohereRerankService
from backend.services.neo4j_memory import Neo4jMemoryService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result from any source"""
    id: str
    content: str
    source_type: str  # "bm25", "semantic", "graph"
    score: float  # Normalized 0-1
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class HybridSearchService:
    """
    High-performance hybrid search combining:
    - BM25 for exact/keyword matching
    - Semantic search for conceptual similarity
    - Graph search for relationship discovery

    Features:
    - Configurable weights for each search type
    - Automatic query term extraction for BM25
    - Spreading activation from query concepts in graph
    - Cohere reranking for final ranking
    - Result deduplication and merging
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: aioredis.Redis,
        neo4j_service: Optional[Neo4jMemoryService] = None
    ):
        """
        Initialize hybrid search service

        Args:
            db_pool: AsyncPG connection pool
            redis_client: Async Redis client
            neo4j_service: Optional Neo4j service for graph search
        """
        self.db_pool = db_pool
        self.redis = redis_client
        self.voyage = get_voyage_service()
        self.rerank = CohereRerankService()
        self.neo4j = neo4j_service
        self.config = get_config()

        logger.info("HybridSearchService initialized")

    # ========================================================================
    # MAIN HYBRID SEARCH
    # ========================================================================

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
        limit_per_source: int = 50
    ) -> List[Dict]:
        """
        Hybrid search combining BM25 + Semantic + Graph

        Query flows through three parallel searches, results fused with weighted scoring,
        then reranked with Cohere for final ranking.

        Args:
            query: Search query string
            top_k: Number of final results to return
            weights: Weight distribution {"bm25": 0.3, "semantic": 0.4, "graph": 0.3}
                    Default: semantic=0.4, bm25=0.3, graph=0.3
            limit_per_source: How many results to fetch from each source before fusion (default 50)

        Returns:
            List of top_k results with format:
            [
                {
                    "id": result_id,
                    "content": result_content,
                    "score": final_score,
                    "rank_position": 1,
                    "relevance_score": cohere_score,
                    "sources": ["semantic", "bm25"],
                    "metadata": {...}
                },
                ...
            ]
        """
        # Default weights
        if weights is None:
            weights = {"bm25": 0.3, "semantic": 0.4, "graph": 0.3}

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight != 1.0:
            weights = {k: v / total_weight for k, v in weights.items()}
            logger.debug(f"Normalized weights: {weights}")

        try:
            # Execute all three searches in parallel
            results = await asyncio.gather(
                self._bm25_search(query, limit=limit_per_source),
                self._semantic_search(query, limit=limit_per_source),
                self._graph_search(query, limit=limit_per_source),
                return_exceptions=True
            )

            bm25_results = results[0] if not isinstance(results[0], Exception) else []
            semantic_results = results[1] if not isinstance(results[1], Exception) else []
            graph_results = results[2] if not isinstance(results[2], Exception) else []

            logger.debug(
                f"Search results: BM25={len(bm25_results)}, "
                f"Semantic={len(semantic_results)}, Graph={len(graph_results)}"
            )

            # Fuse results with weighted scoring
            fused = self._fuse_results(
                bm25_results, semantic_results, graph_results, weights
            )

            if not fused:
                logger.warning("No results from any search source")
                return []

            logger.debug(f"Fused {len(fused)} unique results")

            # Rerank with Cohere
            reranked = await self._rerank_fused_results(query, fused, top_k)

            logger.info(f"Hybrid search returned {len(reranked)} results")
            return reranked

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}", exc_info=True)
            raise

    # ========================================================================
    # INDIVIDUAL SEARCH IMPLEMENTATIONS
    # ========================================================================

    async def _bm25_search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        BM25 full-text search using PostgreSQL

        BM25 is best for:
        - Exact keyword matching
        - Technical queries with specific terms
        - Short, precise queries

        Args:
            query: Query string
            limit: Maximum results to fetch

        Returns:
            List of SearchResult objects with BM25 scores
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Use PostgreSQL full-text search with BM25 ranking
                results = await conn.fetch(
                    """
                    SELECT
                        id,
                        content,
                        metadata,
                        ts_rank(to_tsvector('english', content),
                               plainto_tsquery('english', $1)) as bm25_score
                    FROM memory_store
                    WHERE to_tsvector('english', content) @@
                          plainto_tsquery('english', $1)
                    ORDER BY bm25_score DESC
                    LIMIT $2
                    """,
                    query,
                    limit
                )

            search_results = []
            for row in results:
                score = float(row["bm25_score"]) if row["bm25_score"] else 0.0
                # Normalize BM25 score to 0-1 range
                normalized_score = min(1.0, score / 10.0)  # BM25 typically ranges 0-10

                search_results.append(SearchResult(
                    id=str(row["id"]),
                    content=row["content"],
                    source_type="bm25",
                    score=normalized_score,
                    metadata=row["metadata"] or {}
                ))

            logger.debug(f"BM25 search found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []

    async def _semantic_search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Semantic search using Voyage embeddings + pgvector

        Semantic search is best for:
        - Conceptual similarity
        - Paraphrased queries
        - Long, natural language queries
        - Finding related ideas

        Args:
            query: Query string
            limit: Maximum results to fetch

        Returns:
            List of SearchResult objects with cosine similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.voyage.embed_text_query(query)
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            async with self.db_pool.acquire() as conn:
                # Vector similarity search
                results = await conn.fetch(
                    """
                    SELECT
                        id,
                        content,
                        metadata,
                        1 - (embedding <=> $1::vector(1024)) as cosine_similarity
                    FROM memory_store
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector(1024)
                    LIMIT $2
                    """,
                    embedding_str,
                    limit
                )

            search_results = []
            for row in results:
                similarity = float(row["cosine_similarity"]) if row["cosine_similarity"] else 0.0
                # Cosine similarity already in 0-1 range

                search_results.append(SearchResult(
                    id=str(row["id"]),
                    content=row["content"],
                    source_type="semantic",
                    score=max(0.0, similarity),  # Ensure non-negative
                    metadata=row["metadata"] or {}
                ))

            logger.debug(f"Semantic search found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def _graph_search(self, query: str, limit: int = 50) -> List[SearchResult]:
        """
        Graph-based search using Neo4j spreading activation

        Graph search is best for:
        - Finding related concepts through connections
        - Discovering patterns and relationships
        - Long-term memory associations
        - Context expansion

        Args:
            query: Query string
            limit: Maximum results to fetch

        Returns:
            List of SearchResult objects with activation scores
        """
        if not self.neo4j:
            logger.debug("Neo4j not available, skipping graph search")
            return []

        try:
            # Extract concepts from query (simple: split on spaces, filter stopwords)
            concepts = await self._extract_concepts(query)
            if not concepts:
                logger.debug("No concepts extracted for graph search")
                return []

            # Run spreading activation from concepts
            activated = self.neo4j.spreading_activation_advanced(
                start_concepts=concepts,
                max_depth=3,
                min_activation=0.1,
                decay_factor=0.7,
                use_temporal_decay=True
            )

            search_results = []
            for node in activated[:limit]:
                search_results.append(SearchResult(
                    id=node["id"],
                    content=node["content"],
                    source_type="graph",
                    score=float(node["activation"]),  # Already normalized in spreading activation
                    metadata={
                        "type": node.get("type"),
                        "depth": node.get("depth"),
                        "base_activation": node.get("base_activation"),
                        "recency_boost": node.get("recency_boost"),
                        "access_count": node.get("access_count")
                    }
                ))

            logger.debug(f"Graph search found {len(search_results)} results")
            return search_results

        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []

    # ========================================================================
    # RESULT FUSION
    # ========================================================================

    def _fuse_results(
        self,
        bm25_results: List[SearchResult],
        semantic_results: List[SearchResult],
        graph_results: List[SearchResult],
        weights: Dict[str, float]
    ) -> List[Dict]:
        """
        Fuse results from three sources using weighted scoring

        Algorithm:
        1. Normalize all scores to 0-1 range
        2. Deduplicate by ID (keep highest score)
        3. Calculate fused score: sum(weight * normalized_score for each source)
        4. Return deduplicated results sorted by fused score

        Args:
            bm25_results: Results from BM25 search
            semantic_results: Results from semantic search
            graph_results: Results from graph search
            weights: Weight for each source

        Returns:
            List of fused results with deduplicated IDs and fused scores
        """
        # Collect all results by ID
        results_by_id = {}

        for result in bm25_results:
            if result.id not in results_by_id:
                results_by_id[result.id] = {
                    "id": result.id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "scores": {},
                    "sources": []
                }
            results_by_id[result.id]["scores"]["bm25"] = result.score
            results_by_id[result.id]["sources"].append("bm25")

        for result in semantic_results:
            if result.id not in results_by_id:
                results_by_id[result.id] = {
                    "id": result.id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "scores": {},
                    "sources": []
                }
            results_by_id[result.id]["scores"]["semantic"] = result.score
            results_by_id[result.id]["sources"].append("semantic")

        for result in graph_results:
            if result.id not in results_by_id:
                results_by_id[result.id] = {
                    "id": result.id,
                    "content": result.content,
                    "metadata": result.metadata,
                    "scores": {},
                    "sources": []
                }
            results_by_id[result.id]["scores"]["graph"] = result.score
            results_by_id[result.id]["sources"].append("graph")

        # Calculate fused scores
        fused_results = []
        for item in results_by_id.values():
            scores = item["scores"]

            # Calculate weighted sum (treat missing scores as 0)
            fused_score = (
                weights.get("bm25", 0.0) * scores.get("bm25", 0.0) +
                weights.get("semantic", 0.0) * scores.get("semantic", 0.0) +
                weights.get("graph", 0.0) * scores.get("graph", 0.0)
            )

            item["fused_score"] = round(fused_score, 4)
            item["sources"] = list(set(item["sources"]))  # Deduplicate sources
            fused_results.append(item)

        # Sort by fused score (descending)
        fused_results.sort(key=lambda x: x["fused_score"], reverse=True)

        logger.debug(
            f"Fused {len(fused_results)} unique results. "
            f"Top score: {fused_results[0]['fused_score'] if fused_results else 0}"
        )

        return fused_results

    # ========================================================================
    # RERANKING
    # ========================================================================

    async def _rerank_fused_results(
        self,
        query: str,
        fused_results: List[Dict],
        top_k: int
    ) -> List[Dict]:
        """
        Rerank fused results using Cohere Rerank

        Final reranking step using Cohere's state-of-the-art model
        to ensure top results are most relevant to the query.

        Args:
            query: Original query
            fused_results: Results after fusion
            top_k: Number of results to return

        Returns:
            Top-k reranked results with relevance scores
        """
        try:
            if not fused_results:
                return []

            # Extract content for reranking
            documents = [r["content"] for r in fused_results]

            # Rerank with Cohere
            reranked = self.rerank.rerank_l3_results(
                query=query,
                documents=documents,
                top_k=top_k
            )

            # Map back to original data with Cohere scores
            result_map = {r["id"]: r for r in fused_results}
            final_results = []

            for rank_result in reranked:
                original_idx = rank_result["index"]
                original_result = fused_results[original_idx]

                final_results.append({
                    "id": original_result["id"],
                    "content": original_result["content"],
                    "score": original_result["fused_score"],
                    "relevance_score": rank_result["relevance_score"],
                    "rank_position": rank_result["position"],
                    "sources": original_result["sources"],
                    "metadata": original_result["metadata"]
                })

            logger.debug(f"Reranked {len(fused_results)} -> {len(final_results)} results")
            return final_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return top fused results sorted by score
            logger.info("Falling back to fused scores without Cohere reranking")
            return [
                {
                    "id": r["id"],
                    "content": r["content"],
                    "score": r["fused_score"],
                    "relevance_score": r["fused_score"],
                    "rank_position": i + 1,
                    "sources": r["sources"],
                    "metadata": r["metadata"]
                }
                for i, r in enumerate(fused_results[:top_k])
            ]

    # ========================================================================
    # UTILITIES
    # ========================================================================

    async def _extract_concepts(self, query: str) -> List[str]:
        """
        Extract key concepts from query for graph search

        Simple implementation: split on spaces and filter stopwords.
        In production, could use NER or keyword extraction.

        Args:
            query: Query string

        Returns:
            List of concept strings
        """
        stopwords = {
            "a", "an", "the", "and", "or", "is", "are", "am", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "it", "its", "in",
            "on", "at", "to", "from", "for", "by", "of", "with", "as", "if", "then"
        }

        # Simple tokenization
        tokens = query.lower().split()
        concepts = [t.strip(".,!?;:") for t in tokens if t.lower() not in stopwords and len(t) > 2]

        return list(set(concepts))  # Deduplicate

    async def hybrid_search_with_options(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.3,
        semantic_weight: float = 0.4,
        graph_weight: float = 0.3,
        skip_sources: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Hybrid search with fine-grained source control

        Allows disabling specific sources (e.g., skip BM25 if not relevant).

        Args:
            query: Search query
            top_k: Number of results
            bm25_weight: BM25 source weight
            semantic_weight: Semantic source weight
            graph_weight: Graph source weight
            skip_sources: List of sources to skip ["bm25", "semantic", "graph"]

        Returns:
            Reranked search results
        """
        # Build weights dict
        weights = {
            "bm25": bm25_weight if "bm25" not in (skip_sources or []) else 0.0,
            "semantic": semantic_weight if "semantic" not in (skip_sources or []) else 0.0,
            "graph": graph_weight if "graph" not in (skip_sources or []) else 0.0
        }

        return await self.hybrid_search(query, top_k=top_k, weights=weights)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_hybrid_search_service(
    db_pool: asyncpg.Pool,
    redis_client: aioredis.Redis,
    neo4j_service: Optional[Neo4jMemoryService] = None
) -> HybridSearchService:
    """
    Factory function to create HybridSearchService

    Args:
        db_pool: AsyncPG connection pool
        redis_client: Async Redis client
        neo4j_service: Optional Neo4j service

    Returns:
        Initialized HybridSearchService instance
    """
    return HybridSearchService(db_pool, redis_client, neo4j_service)


# ============================================================================
# TESTING
# ============================================================================

async def test_hybrid_search():
    """Test hybrid search service"""

    print("Testing HybridSearchService")
    print("=" * 70)

    # Note: This is a simplified test. In real usage, you'd have:
    # - Populated PostgreSQL database with memories
    # - Populated Neo4j graph with concepts
    # - Redis running for caching

    print("\nTest setup:")
    print("  Database: PostgreSQL with memory_store table")
    print("  Graph: Neo4j with concept nodes")
    print("  Cache: Redis for L1/L2 caching")
    print("  Embeddings: Voyage AI (via VoyageEmbeddingService)")
    print("  Reranking: Cohere Rerank v3.5")

    print("\nHybrid search architecture:")
    print("  1. BM25 Search (PostgreSQL full-text)")
    print("     - Best for: Exact keywords, technical terms")
    print("     - Weight: 0.3 (30%)")
    print()
    print("  2. Semantic Search (pgvector + Voyage)")
    print("     - Best for: Conceptual similarity, paraphrasing")
    print("     - Weight: 0.4 (40%)")
    print()
    print("  3. Graph Search (Neo4j spreading activation)")
    print("     - Best for: Relationship discovery, context")
    print("     - Weight: 0.3 (30%)")
    print()
    print("  Result Fusion:")
    print("    - Deduplicate results by ID")
    print("    - Calculate weighted fused score")
    print("    - Rerank with Cohere")
    print()

    print("\nExample usage:")
    print("""
    # Initialize
    service = HybridSearchService(db_pool, redis, neo4j)

    # Default weights (semantic-heavy)
    results = await service.hybrid_search(
        query="async programming patterns",
        top_k=10
    )

    # Custom weights (emphasize graph relationships)
    results = await service.hybrid_search(
        query="memory optimization techniques",
        top_k=5,
        weights={"bm25": 0.2, "semantic": 0.3, "graph": 0.5}
    )

    # Skip sources
    results = await service.hybrid_search_with_options(
        query="Redis caching",
        top_k=10,
        skip_sources=["graph"]  # Only BM25 + Semantic
    )

    # Results format:
    [
        {
            "id": "memory-uuid",
            "content": "Memory content",
            "score": 0.75,  # Fused score before Cohere
            "relevance_score": 0.82,  # Cohere final score
            "rank_position": 1,
            "sources": ["semantic", "bm25"],
            "metadata": {...}
        },
        ...
    ]
    """)

    print("\n" + "=" * 70)
    print("Test guide: Deploy with populated DB/Graph to test fully")


if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
