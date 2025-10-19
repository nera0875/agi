"""
Memory Service - Hybrid RAG System
Combines semantic search (pgvector) + BM25 (PostgreSQL tsvector) with RRF fusion
Uses Voyage AI embeddings and Cohere reranking
"""

import asyncio
import logging
import json
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

import numpy as np
import asyncpg
from langchain_voyageai import VoyageAIEmbeddings
from langchain_cohere import CohereRerank
from langchain_core.documents import Document
from redis import asyncio as aioredis

from config import settings
from core import (
    trace_retrieval,
    retry_on_llm_error,
    retry_on_db_error,
    retry_on_redis_error,
    error_handler,
    performance_monitor,
    embedding_circuit_breaker,
    rerank_circuit_breaker
)
from validators import default_validator, MemoryValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# SEMANTIC CACHE HELPERS
# ============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Similarity score between 0 and 1
    """
    if not vec1 or not vec2:
        return 0.0

    v1 = np.array(vec1, dtype=np.float32)
    v2 = np.array(vec2, dtype=np.float32)

    # Cosine similarity = dot(v1, v2) / (norm(v1) * norm(v2))
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot / (norm1 * norm2))


class MemoryService:
    """
    Hybrid RAG memory service with:
    - Voyage AI embeddings (voyage-3, 1024 dimensions)
    - RRF fusion (70% semantic + 30% BM25)
    - Cohere reranking
    - Redis caching (L1: embeddings, L2: semantic responses)
    - Full observability with LangSmith + Sentry
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: aioredis.Redis
    ):
        self.db_pool = db_pool
        self.redis = redis_client

        # Initialize Voyage AI embeddings
        self.embeddings = VoyageAIEmbeddings(
            voyage_api_key=settings.voyage_api_key,
            model=settings.voyage_model,
            batch_size=128
        )
        logger.info("Voyage AI embeddings initialized (voyage-3, 1024 dims)")

        # Initialize Cohere reranker
        from pydantic import SecretStr
        self.reranker = CohereRerank(
            cohere_api_key=SecretStr(settings.cohere_api_key),
            top_n=settings.rerank_top_n,
            model="rerank-english-v3.0"
        )
        logger.info("Cohere reranker initialized (rerank-english-v3.0)")

        logger.info("MemoryService initialized with Voyage AI + Cohere reranking")

    # ========================================================================
    # CORE RETRIEVAL
    # ========================================================================

    @trace_retrieval(name="hybrid_search")
    @performance_monitor.track_latency("hybrid_search")
    @retry_on_db_error()
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        user_id: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        expand_graph: bool = False,
        graph_depth: int = 1
    ) -> List[Document]:
        """
        Hybrid search using RRF (Reciprocal Rank Fusion)
        Combines semantic (pgvector) + BM25 (PostgreSQL full-text)

        Args:
            query: User query text
            top_k: Number of results to return
            user_id: Optional user ID for multi-tenant filtering
            metadata_filter: Optional metadata filtering
            expand_graph: Expand results with related memories via graph
            graph_depth: Depth for graph traversal (default: 1)

        Returns:
            List of Document objects ranked by RRF score
        """
        try:
            # Check semantic cache first (L2)
            cache_result = await self._check_semantic_cache(query)
            if cache_result:
                cached_docs, similarity = cache_result
                logger.info(f"Semantic cache HIT: {similarity:.3f} similarity")

                # Reconstruct Document objects from cached data
                documents = [
                    Document(
                        page_content=doc["page_content"],
                        metadata=doc["metadata"]
                    )
                    for doc in cached_docs
                ]
                return documents

            # Generate query embedding with cache (L1)
            query_embedding = await self._get_embedding_cached(query)
            # Convert to pgvector format
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Execute hybrid search using PostgreSQL function
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    """
                    SELECT * FROM hybrid_search_memory(
                        query_embedding := $1::vector(1024),
                        query_text := $2,
                        match_count := $3,
                        semantic_weight := $4,
                        bm25_weight := $5
                    )
                    """,
                    query_embedding_str,
                    query,
                    top_k * 2,  # Retrieve more for reranking
                    settings.semantic_weight,
                    settings.bm25_weight
                )

            # Convert to Document objects
            import json
            documents = [
                Document(
                    page_content=row["content"],
                    metadata={
                        **(json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]),
                        "id": str(row["id"]),
                        "rrf_score": float(row["similarity_score"])
                    }
                )
                for row in results
            ]

            # Apply Cohere reranking
            if documents:
                documents = await self._rerank_documents(query, documents)

            # Track access for quality scoring (async, non-blocking)
            for doc in documents:
                if "id" in doc.metadata:
                    try:
                        memory_id = UUID(doc.metadata["id"])
                        asyncio.create_task(self.track_access(memory_id))
                    except (ValueError, KeyError):
                        pass

            # Expand with graph relations if requested
            if expand_graph and documents:
                related_docs = []
                seen_ids = {doc.metadata.get("id") for doc in documents if "id" in doc.metadata}

                for doc in documents[:5]:  # Expand top 5 results only
                    if "id" in doc.metadata:
                        try:
                            memory_id = UUID(doc.metadata["id"])
                            related = await self.get_related_memories(
                                memory_id,
                                max_depth=graph_depth
                            )
                            # Filter duplicates
                            for rel_doc in related:
                                rel_id = rel_doc.metadata.get("id")
                                if rel_id and rel_id not in seen_ids:
                                    related_docs.append(rel_doc)
                                    seen_ids.add(rel_id)
                        except Exception as e:
                            logger.debug(f"Graph expansion failed for {doc.metadata['id']}: {e}")

                if related_docs:
                    documents.extend(related_docs[:top_k // 2])  # Add up to 50% more
                    logger.info(f"Graph expansion added {len(related_docs[:top_k // 2])} related docs")

            # Cache results (L2 semantic cache)
            await self._cache_semantic_results(query, documents)

            logger.info(f"Hybrid search returned {len(documents)} documents")
            return documents

        except Exception as e:
            error_handler.handle_retrieval_error(e, query)
            raise

    @trace_retrieval(name="semantic_search")
    @retry_on_db_error()
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[Document]:
        """
        Pure semantic search using pgvector cosine similarity

        Args:
            query: Query text
            top_k: Number of results
            threshold: Minimum similarity score

        Returns:
            List of similar documents
        """
        try:
            query_embedding = await self._get_embedding_cached(query)
            # Convert to pgvector format
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    """
                    SELECT
                        id, content, metadata,
                        1 - (embedding <=> $1::vector(1024)) AS similarity
                    FROM memory_store
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> $1::vector(1024)) > $2
                    ORDER BY embedding <=> $1::vector(1024)
                    LIMIT $3
                    """,
                    query_embedding_str,
                    threshold,
                    top_k
                )

            import json
            return [
                Document(
                    page_content=row["content"],
                    metadata={
                        **(json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]),
                        "id": str(row["id"]),
                        "similarity": float(row["similarity"])
                    }
                )
                for row in results
            ]

        except Exception as e:
            error_handler.handle_retrieval_error(e, query)
            raise

    # ========================================================================
    # STORAGE
    # ========================================================================

    @retry_on_db_error()
    async def check_duplicate(
        self,
        content: str,
        similarity_threshold: float = 0.95
    ) -> Optional[UUID]:
        """
        Check if similar content already exists (deduplication)

        Args:
            content: Content to check
            similarity_threshold: Minimum similarity to consider duplicate

        Returns:
            UUID of existing memory if duplicate found, None otherwise
        """
        try:
            # Generate embedding
            embedding = await self._get_embedding_cached(content)
            embedding_str = f"[{','.join(map(str, embedding))}]"

            # Search for similar content
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT id, 1 - (embedding <=> $1::vector(1024)) AS similarity
                    FROM memory_store
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> $1::vector(1024)
                    LIMIT 1
                    """,
                    embedding_str
                )

                if result and result["similarity"] >= similarity_threshold:
                    logger.info(f"Duplicate found: {result['id']} ({result['similarity']:.3f} similarity)")
                    return result["id"]

            return None

        except Exception as e:
            logger.warning(f"Duplicate check failed (non-blocking): {e}")
            return None

    @retry_on_db_error()
    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "conversation",
        user_id: Optional[str] = None,
        skip_dedup: bool = False,
        skip_validation: bool = False
    ) -> UUID:
        """
        Add new memory to vector store with validation and deduplication

        Args:
            content: Text content to store
            metadata: Optional metadata
            source_type: Type of source (conversation, document, etc.)
            user_id: User ID for multi-tenant
            skip_dedup: Skip deduplication check (default: False)
            skip_validation: Skip content validation (default: False)

        Returns:
            UUID of created memory (existing if duplicate found)

        Raises:
            MemoryValidationError: If validation fails and skip_validation=False
        """
        try:
            # Validate content and metadata unless skipped
            if not skip_validation:
                is_valid, validation_result = default_validator.validate_memory(
                    content, metadata, source_type
                )

                if not is_valid:
                    error_msg = f"Memory validation failed: {', '.join(validation_result.errors)}"
                    logger.warning(error_msg)
                    raise MemoryValidationError(error_msg)

                if validation_result.warnings:
                    logger.info(f"Validation warnings: {', '.join(validation_result.warnings)}")

            # Check for duplicates unless explicitly skipped
            if not skip_dedup:
                existing_id = await self.check_duplicate(content, similarity_threshold=0.95)
                if existing_id:
                    logger.info(f"Skipping duplicate, returning existing memory {existing_id}")
                    return existing_id

            # Generate embedding
            embedding = await self._get_embedding_cached(content)

            # Insert into database
            import json
            # Convert embedding list to pgvector format
            embedding_str = f"[{','.join(map(str, embedding))}]"

            async with self.db_pool.acquire() as conn:
                memory_id = await conn.fetchval(
                    """
                    INSERT INTO memory_store (content, metadata, embedding, source_type, user_id)
                    VALUES ($1, $2::jsonb, $3::vector(1024), $4, $5)
                    RETURNING id
                    """,
                    content,
                    json.dumps(metadata or {}),
                    embedding_str,
                    source_type,
                    user_id
                )

            logger.info(f"Added memory {memory_id}")
            return memory_id

        except Exception as e:
            error_handler.handle_database_error(e, "add_memory")
            raise

    @retry_on_db_error()
    async def add_memories_batch(
        self,
        contents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        source_type: str = "document",
        user_id: Optional[str] = None
    ) -> List[UUID]:
        """
        Batch insert memories (optimized for large ingestion)

        Args:
            contents: List of text contents
            metadatas: List of metadata dicts (optional)
            source_type: Source type
            user_id: User ID

        Returns:
            List of created UUIDs
        """
        try:
            # Generate embeddings in batch (with circuit breaker)
            embeddings = await embedding_circuit_breaker.call(
                self.embeddings.aembed_documents,
                contents
            )

            if metadatas is None:
                metadatas = [{}] * len(contents)

            # Batch insert
            async with self.db_pool.acquire() as conn:
                records = [
                    (content, metadata, embedding, source_type, user_id)
                    for content, metadata, embedding in zip(contents, metadatas, embeddings)
                ]

                memory_ids = await conn.fetch(
                    """
                    INSERT INTO memory_store (content, metadata, embedding, source_type, user_id)
                    SELECT * FROM UNNEST($1::text[], $2::jsonb[], $3::vector(1024)[], $4::text[], $5::text[])
                    RETURNING id
                    """,
                    [r[0] for r in records],
                    [r[1] for r in records],
                    [r[2] for r in records],
                    [r[3] for r in records],
                    [r[4] for r in records]
                )

            logger.info(f"Batch inserted {len(memory_ids)} memories")
            return [row["id"] for row in memory_ids]

        except Exception as e:
            error_handler.handle_database_error(e, "add_memories_batch")
            raise

    # ========================================================================
    # GRAPH RELATIONS
    # ========================================================================

    @retry_on_db_error()
    async def add_relation(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ) -> UUID:
        """
        Add relation between two memories (graph structure)

        Args:
            source_id: Source memory UUID
            target_id: Target memory UUID
            relation_type: Type (RELATES_TO, DEPENDS_ON, etc.)
            metadata: Optional metadata
            weight: Relation strength

        Returns:
            Relation UUID
        """
        try:
            async with self.db_pool.acquire() as conn:
                relation_id = await conn.fetchval(
                    """
                    INSERT INTO relations (source_id, target_id, relation_type, metadata, weight)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    source_id,
                    target_id,
                    relation_type,
                    metadata or {},
                    weight
                )

            return relation_id

        except Exception as e:
            error_handler.handle_database_error(e, "add_relation")
            raise

    @trace_retrieval(name="get_related_memories")
    @retry_on_db_error()
    async def get_related_memories(
        self,
        memory_id: UUID,
        max_depth: int = 3,
        relation_filter: Optional[str] = None
    ) -> List[Document]:
        """
        Traverse graph relations using recursive CTE

        Args:
            memory_id: Starting memory ID
            max_depth: Maximum traversal depth
            relation_filter: Optional relation type filter

        Returns:
            List of related documents
        """
        try:
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    """
                    SELECT * FROM get_related_memories($1, $2, $3)
                    """,
                    memory_id,
                    max_depth,
                    relation_filter
                )

            return [
                Document(
                    page_content=row["content"],
                    metadata={
                        "id": str(row["id"]),
                        "relation_path": row["relation_path"],
                        "depth": row["depth"]
                    }
                )
                for row in results
            ]

        except Exception as e:
            error_handler.handle_retrieval_error(e, f"memory_id: {memory_id}")
            raise

    # ========================================================================
    # CACHING
    # ========================================================================

    @retry_on_redis_error()
    @retry_on_llm_error()
    async def _get_embedding_cached(self, text: str) -> List[float]:
        """
        Get embedding with L1 cache (Redis, 30min TTL)

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cache_key = f"emb:{text_hash}"

        # Try cache
        cached = await self.redis.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        # Generate embedding (with circuit breaker)
        embedding = await embedding_circuit_breaker.call(
            self.embeddings.aembed_query,
            text
        )

        # Cache for 30 minutes
        import json
        await self.redis.setex(cache_key, 1800, json.dumps(embedding))

        return embedding

    @retry_on_redis_error()
    async def _check_semantic_cache(
        self,
        query: str,
        similarity_threshold: float = 0.95
    ) -> Optional[Tuple[List[Document], float]]:
        """
        Check L2 semantic cache with similarity matching

        Uses cosine similarity on embeddings to find similar cached queries.
        If a similar query is found (similarity > threshold), returns cached results.

        Args:
            query: Query text
            similarity_threshold: Minimum similarity for cache hit (default 0.95)

        Returns:
            Tuple of (cached documents, similarity score) if hit, None otherwise
        """
        try:
            # Step 1: Get query embedding
            query_embedding = await self._get_embedding_cached(query)

            # Step 2: Scan Redis for cached search results
            # Pattern: search:*
            cursor = 0
            best_match = None
            best_similarity = 0.0

            while True:
                cursor, keys = await self.redis.scan(cursor, match="search_cache:*", count=100)

                for key in keys:
                    try:
                        # Get cached entry: {embedding, documents}
                        cached_data = await self.redis.get(key)
                        if not cached_data:
                            continue

                        cache_entry = json.loads(cached_data)
                        cached_embedding = cache_entry.get("embedding")
                        cached_documents = cache_entry.get("documents")

                        if not cached_embedding or not cached_documents:
                            continue

                        # Step 3: Calculate similarity
                        similarity = cosine_similarity(query_embedding, cached_embedding)

                        # Step 4: Track best match
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = cached_documents

                            # If we found a very good match, return early
                            if similarity > 0.98:
                                logger.info(f"Semantic cache HIT: {similarity:.3f} similarity")
                                return (best_match, similarity)

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Error processing cached entry {key}: {e}")
                        continue

                # Break if no more keys
                if cursor == 0:
                    break

            # Step 5: Return if above threshold
            if best_match and best_similarity >= similarity_threshold:
                logger.info(f"Semantic cache HIT: {best_similarity:.3f} similarity")
                return (best_match, best_similarity)

            logger.debug(f"Semantic cache MISS (best: {best_similarity:.3f})")
            return None

        except Exception as e:
            logger.debug(f"Semantic cache check failed (non-blocking): {e}")
            return None

    @retry_on_redis_error()
    async def _cache_semantic_results(
        self,
        query: str,
        documents: List[Document],
        ttl: int = 86400  # 24 hours (increased from 3600)
    ):
        """
        Cache search results with embeddings (L2 semantic cache)

        Stores:
        - Query embedding (for similarity matching)
        - Documents (as JSON)

        Args:
            query: Query text
            documents: Result documents
            ttl: Time to live in seconds (default 24h)
        """
        try:
            # Get query embedding for semantic matching
            query_embedding = await self._get_embedding_cached(query)

            # Serialize documents to JSON-safe format
            serialized_docs = []
            for doc in documents:
                serialized_docs.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata or {}
                })

            # Create cache entry with embedding + documents
            cache_entry = {
                "embedding": query_embedding,
                "documents": serialized_docs,
                "query": query,
                "timestamp": asyncio.get_event_loop().time()
            }

            # Store in Redis with unique key based on query hash
            query_hash = hashlib.sha256(query.encode()).hexdigest()
            cache_key = f"search_cache:{query_hash}"

            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_entry)
            )

            logger.debug(f"Cached search results for query (TTL: {ttl}s)")

        except Exception as e:
            logger.debug(f"Failed to cache semantic results (non-blocking): {e}")

    # ========================================================================
    # RERANKING
    # ========================================================================

    @retry_on_llm_error()
    async def _rerank_documents(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Document]:
        """
        Rerank documents using Cohere Rerank API

        Args:
            query: Query text
            documents: Documents to rerank

        Returns:
            Reranked documents (top_n)
        """
        if not documents:
            return documents

        try:
            # Rerank with circuit breaker
            loop = asyncio.get_event_loop()
            reranked = await loop.run_in_executor(
                None,
                lambda: rerank_circuit_breaker.call(
                    self.reranker.compress_documents,
                    documents,
                    query
                )
            )

            logger.info(f"Reranked {len(documents)} -> {len(reranked)} documents")
            return reranked

        except Exception as e:
            logger.warning(f"Reranking failed, returning original order: {e}")
            return documents[:settings.rerank_top_n]

    # ========================================================================
    # UTILITIES
    # ========================================================================

    async def health_check(self) -> Dict[str, bool]:
        """
        Check service health

        Returns:
            Status dict
        """
        status = {
            "database": False,
            "redis": False,
            "embeddings": False
        }

        # Check database
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            status["database"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check Redis
        try:
            await self.redis.ping()
            status["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

        # Check embeddings (simple test)
        try:
            await self.embeddings.aembed_query("test")
            status["embeddings"] = True
        except Exception as e:
            logger.error(f"Embeddings health check failed: {e}")

        return status

    @retry_on_db_error()
    async def cleanup_test_data(self) -> int:
        """
        Remove test/temporary data from memory store

        Returns:
            Number of entries removed
        """
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    """
                    DELETE FROM memory_store
                    WHERE metadata->>'test' = 'true'
                       OR source_type = 'test'
                       OR content LIKE '%[TEST]%'
                    """
                )

                # Parse "DELETE N" result
                count = int(result.split()[-1])
                logger.info(f"Cleaned up {count} test entries")
                return count

        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            raise

    @retry_on_db_error()
    async def cleanup_old_memories(
        self,
        days: int = 90,
        source_types: Optional[List[str]] = None
    ) -> int:
        """
        Remove old memories based on age and source type

        Args:
            days: Remove memories older than N days
            source_types: Optional list of source types to target

        Returns:
            Number of entries removed
        """
        try:
            async with self.db_pool.acquire() as conn:
                if source_types:
                    result = await conn.execute(
                        """
                        DELETE FROM memory_store
                        WHERE created_at < NOW() - INTERVAL '$1 days'
                          AND source_type = ANY($2)
                        """,
                        days,
                        source_types
                    )
                else:
                    result = await conn.execute(
                        """
                        DELETE FROM memory_store
                        WHERE created_at < NOW() - INTERVAL '$1 days'
                        """,
                        days
                    )

                count = int(result.split()[-1])
                logger.info(f"Cleaned up {count} old memories (>{days} days)")
                return count

        except Exception as e:
            logger.error(f"Old memories cleanup error: {e}")
            raise

    @retry_on_db_error()
    async def calculate_quality_score(
        self,
        memory_id: UUID,
        content_length: int,
        access_count: int,
        days_old: int,
        has_metadata: bool
    ) -> float:
        """
        Calculate quality score based on multiple factors

        Scoring factors:
        - Content quality (30%): Length, structure
        - Freshness (25%): Recency of creation
        - Usage (25%): Access frequency
        - Metadata richness (20%): Tags, relations

        Args:
            memory_id: Memory UUID
            content_length: Character count
            access_count: Number of accesses
            days_old: Age in days
            has_metadata: Has metadata/tags

        Returns:
            Quality score (0.0 to 1.0)
        """
        # Content quality (0-1): Penalize too short (<50) or too long (>5000)
        content_score = min(1.0, max(0.3, content_length / 1000))
        if content_length < 50:
            content_score *= 0.5

        # Freshness (0-1): Decay over time (half-life = 30 days)
        freshness_score = 1.0 / (1.0 + (days_old / 30.0))

        # Usage (0-1): Logarithmic scale (diminishing returns)
        usage_score = min(1.0, np.log1p(access_count) / 5.0)

        # Metadata richness (0-1)
        metadata_score = 1.0 if has_metadata else 0.3

        # Weighted sum
        quality = (
            0.30 * content_score +
            0.25 * freshness_score +
            0.25 * usage_score +
            0.20 * metadata_score
        )

        return round(quality, 3)

    @retry_on_db_error()
    async def update_quality_scores(self, batch_size: int = 1000) -> int:
        """
        Recalculate quality scores for all memories in batches

        Args:
            batch_size: Process N memories at a time

        Returns:
            Number of memories updated
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get all memories with required data
                memories = await conn.fetch(
                    """
                    SELECT
                        id,
                        LENGTH(content) as content_length,
                        COALESCE(access_count, 0) as access_count,
                        EXTRACT(DAY FROM NOW() - created_at)::int as days_old,
                        CASE WHEN metadata IS NOT NULL AND metadata != '{}'::jsonb THEN true ELSE false END as has_metadata
                    FROM memory_store
                    """
                )

                updated = 0
                for memory in memories:
                    score = await self.calculate_quality_score(
                        memory["id"],
                        memory["content_length"],
                        memory["access_count"],
                        memory["days_old"],
                        memory["has_metadata"]
                    )

                    await conn.execute(
                        "UPDATE memory_store SET quality_score = $1 WHERE id = $2",
                        score,
                        memory["id"]
                    )
                    updated += 1

                logger.info(f"Updated quality scores for {updated} memories")
                return updated

        except Exception as e:
            logger.error(f"Quality score update error: {e}")
            raise

    @retry_on_db_error()
    async def track_access(self, memory_id: UUID):
        """
        Track memory access for quality scoring

        Args:
            memory_id: Memory UUID
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE memory_store
                    SET access_count = COALESCE(access_count, 0) + 1,
                        last_accessed_at = NOW()
                    WHERE id = $1
                    """,
                    memory_id
                )
        except Exception as e:
            logger.warning(f"Access tracking failed (non-blocking): {e}")

    @retry_on_db_error()
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics

        Returns:
            Statistics dict with counts, types, and metadata
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Total memories
                total = await conn.fetchval("SELECT COUNT(*) FROM memory_store")

                # By source type
                by_type = await conn.fetch(
                    """
                    SELECT source_type, COUNT(*) as count
                    FROM memory_store
                    GROUP BY source_type
                    ORDER BY count DESC
                    """
                )

                # Recent additions (last 24h)
                recent = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM memory_store
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    """
                )

                # Quality score distribution
                quality_dist = await conn.fetch(
                    """
                    SELECT
                        CASE
                            WHEN quality_score >= 0.8 THEN 'excellent'
                            WHEN quality_score >= 0.6 THEN 'good'
                            WHEN quality_score >= 0.4 THEN 'fair'
                            ELSE 'poor'
                        END as quality_tier,
                        COUNT(*) as count
                    FROM memory_store
                    GROUP BY quality_tier
                    """
                )

            return {
                "total_memories": total,
                "by_source_type": {row["source_type"]: row["count"] for row in by_type},
                "recent_24h": recent,
                "quality_distribution": {row["quality_tier"]: row["count"] for row in quality_dist},
                "database": "connected",
                "redis": "connected" if await self.redis.ping() else "disconnected"
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            raise
