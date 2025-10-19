"""
BM25 Full-Text Search Service
Implements PostgreSQL BM25 (Best Matching 25) using tsvector
- Fast full-text search using trigram and GIN indexes
- BM25 ranking with ts_rank_cd (Cover Density)
- Websearch query parsing support
- Support for knowledge_type filtering
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any, Tuple
from uuid import UUID
import json

import asyncpg
from langchain_core.documents import Document

from config import settings
from core import trace_retrieval, retry_on_db_error, error_handler

logger = logging.getLogger(__name__)


class BM25SearchService:
    """
    PostgreSQL BM25 full-text search service

    Uses tsvector for keyword indexing with:
    - ts_rank_cd for BM25-style ranking (Cover Density)
    - websearch_to_tsquery for natural language query support
    - GIN index for fast lookups
    - Optional filtering by knowledge_type
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize BM25 search service

        Args:
            db_pool: AsyncPG connection pool
        """
        self.db_pool = db_pool
        logger.info("BM25SearchService initialized")

    @trace_retrieval(name="bm25_search")
    @retry_on_db_error()
    async def search_agi_knowledge(
        self,
        query: str,
        limit: int = 20,
        knowledge_type: Optional[str] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[Document]:
        """
        BM25 full-text search in agi_knowledge table

        Uses PostgreSQL ts_rank_cd for BM25-style ranking.
        Query is parsed using websearch_to_tsquery for natural language support.

        Args:
            query: Search query text (natural language supported)
            limit: Maximum number of results (default: 20)
            knowledge_type: Optional filter by knowledge_type
            tags_filter: Optional filter by tags array

        Returns:
            List of Document objects with metadata

        Raises:
            Exception: If database query fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Build dynamic SQL with optional filters
                sql = """
                    SELECT
                        id,
                        content,
                        knowledge_type,
                        tags,
                        context,
                        created_at,
                        updated_at,
                        ts_rank_cd(content_tsv, websearch_to_tsquery('english', $1)) AS bm25_rank
                    FROM agi_knowledge
                    WHERE content_tsv @@ websearch_to_tsquery('english', $1)
                """

                params = [query]
                param_idx = 2

                # Add knowledge_type filter if provided
                if knowledge_type:
                    sql += f" AND knowledge_type = ${param_idx}"
                    params.append(knowledge_type)
                    param_idx += 1

                # Add tags filter if provided
                if tags_filter and len(tags_filter) > 0:
                    sql += f" AND tags && ${param_idx}::text[]"
                    params.append(tags_filter)
                    param_idx += 1

                # Order by BM25 rank and recency
                sql += f"""
                    ORDER BY bm25_rank DESC, created_at DESC
                    LIMIT ${param_idx}
                """
                params.append(limit)

                # Execute search
                results = await conn.fetch(sql, *params)

                # Convert to Document objects
                documents = []
                for row in results:
                    metadata = {
                        "id": str(row["id"]),
                        "knowledge_type": row["knowledge_type"],
                        "tags": row["tags"] or [],
                        "bm25_rank": float(row["bm25_rank"]),
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    }

                    if row["context"]:
                        try:
                            metadata["context"] = json.loads(row["context"]) if isinstance(row["context"], str) else row["context"]
                        except (json.JSONDecodeError, TypeError):
                            pass

                    doc = Document(
                        page_content=row["content"],
                        metadata=metadata
                    )
                    documents.append(doc)

                logger.info(f"BM25 search returned {len(documents)} results for query: {query[:50]}")
                return documents

        except Exception as e:
            error_handler.handle_retrieval_error(e, query)
            raise

    @trace_retrieval(name="bm25_search_l3")
    @retry_on_db_error()
    async def search_l3_bm25(
        self,
        query: str,
        limit: int = 20,
        knowledge_type: Optional[str] = None
    ) -> List[Document]:
        """
        BM25 full-text search in l3_knowledge table (for Layer 3 knowledge)

        Uses ts_rank_cd for ranking with query normalization.

        Args:
            query: Search query text
            limit: Maximum number of results
            knowledge_type: Optional filter by knowledge_type

        Returns:
            List of Document objects
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Check if l3_knowledge table exists
                table_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'l3_knowledge'
                    )
                    """
                )

                if not table_exists:
                    logger.warning("l3_knowledge table does not exist")
                    return []

                # Build SQL query
                sql = """
                    SELECT
                        id,
                        content,
                        knowledge_type,
                        importance,
                        created_at,
                        updated_at,
                        ts_rank_cd(content_tsv, websearch_to_tsquery('english', $1)) AS rank
                    FROM l3_knowledge
                    WHERE content_tsv @@ websearch_to_tsquery('english', $1)
                """

                params = [query]
                param_idx = 2

                if knowledge_type:
                    sql += f" AND knowledge_type = ${param_idx}"
                    params.append(knowledge_type)
                    param_idx += 1

                sql += f"""
                    ORDER BY rank DESC, created_at DESC
                    LIMIT ${param_idx}
                """
                params.append(limit)

                results = await conn.fetch(sql, *params)

                # Convert to Document objects
                documents = []
                for row in results:
                    metadata = {
                        "id": str(row["id"]),
                        "knowledge_type": row["knowledge_type"],
                        "importance": row.get("importance"),
                        "bm25_rank": float(row["rank"]),
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                    }

                    doc = Document(
                        page_content=row["content"],
                        metadata=metadata
                    )
                    documents.append(doc)

                logger.info(f"L3 BM25 search returned {len(documents)} results")
                return documents

        except Exception as e:
            error_handler.handle_retrieval_error(e, query)
            raise

    @trace_retrieval(name="bm25_stats")
    async def get_search_stats(self) -> Dict[str, Any]:
        """
        Get BM25 index statistics

        Returns:
            Dictionary with:
            - total_documents: Total indexed documents
            - indexed_documents: Documents with tsvector index
            - table_size: Size of agi_knowledge table
            - index_size: Size of tsvector GIN index
        """
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        count(*) as total_documents,
                        count(content_tsv) as indexed_documents,
                        pg_size_pretty(pg_total_relation_size('agi_knowledge')) as table_size,
                        pg_size_pretty(pg_total_relation_size('idx_agi_knowledge_tsv')) as index_size
                    FROM agi_knowledge
                    """
                )

                return {
                    "total_documents": stats["total_documents"],
                    "indexed_documents": stats["indexed_documents"],
                    "table_size": stats["table_size"],
                    "index_size": stats["index_size"]
                }

        except Exception as e:
            logger.error(f"Failed to get search stats: {e}")
            return {
                "error": str(e)
            }

    async def rebuild_tsvector_index(self) -> Dict[str, Any]:
        """
        Rebuild tsvector index for all documents

        Useful after bulk updates or data imports.

        Returns:
            Dictionary with:
            - updated_count: Number of documents updated
            - status: Operation status message
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Update all tsvector columns
                result = await conn.execute(
                    """
                    UPDATE agi_knowledge
                    SET content_tsv = to_tsvector('english',
                        COALESCE(content, '') || ' ' ||
                        COALESCE(context::text, '') || ' ' ||
                        COALESCE(array_to_string(tags, ' '), '')
                    )
                    """
                )

                # Parse result string to extract count
                # Format: "UPDATE <count>"
                count = int(result.split()[-1]) if result else 0

                logger.info(f"Rebuilt tsvector index for {count} documents")

                return {
                    "updated_count": count,
                    "status": f"Successfully rebuilt index for {count} documents"
                }

        except Exception as e:
            logger.error(f"Failed to rebuild tsvector index: {e}")
            raise

    @trace_retrieval(name="bm25_hybrid")
    async def hybrid_bm25_semantic(
        self,
        query: str,
        semantic_results: List[Document],
        limit: int = 20,
        bm25_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> List[Document]:
        """
        Hybrid search combining BM25 and semantic results using RRF

        Reciprocal Rank Fusion (RRF) combines multiple ranking functions:
        score = sum(1 / (k + rank_i))
        where k=60 (standard RRF constant)

        Args:
            query: Search query
            semantic_results: Results from semantic search
            limit: Maximum results to return
            bm25_weight: Weight for BM25 results (0-1)
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            Merged and ranked Document list
        """
        try:
            # Get BM25 results
            bm25_results = await self.search_agi_knowledge(query, limit=limit)

            if not bm25_results and not semantic_results:
                return []

            # Create ranking maps
            bm25_map = {doc.metadata["id"]: (i, doc) for i, doc in enumerate(bm25_results)}
            semantic_map = {doc.metadata["id"]: (i, doc) for i, doc in enumerate(semantic_results)}

            # Calculate RRF scores
            k = 60  # Standard RRF constant
            rrf_scores = {}
            all_ids = set(bm25_map.keys()) | set(semantic_map.keys())

            for doc_id in all_ids:
                bm25_rank = bm25_map.get(doc_id, (float('inf'), None))[0]
                semantic_rank = semantic_map.get(doc_id, (float('inf'), None))[0]

                rrf_score = 0.0
                if bm25_rank != float('inf'):
                    rrf_score += bm25_weight / (k + bm25_rank + 1)
                if semantic_rank != float('inf'):
                    rrf_score += semantic_weight / (k + semantic_rank + 1)

                rrf_scores[doc_id] = rrf_score

            # Sort by RRF score
            sorted_ids = sorted(all_ids, key=lambda x: rrf_scores[x], reverse=True)[:limit]

            # Build result list with merged metadata
            results = []
            for doc_id in sorted_ids:
                doc = bm25_map.get(doc_id, (None, semantic_map[doc_id][1]))[1]
                if doc:
                    doc.metadata["rrf_score"] = rrf_scores[doc_id]
                    results.append(doc)

            logger.info(f"Hybrid search returned {len(results)} documents")
            return results

        except Exception as e:
            error_handler.handle_retrieval_error(e, query)
            logger.warning(f"Hybrid search failed, returning semantic results: {e}")
            return semantic_results
