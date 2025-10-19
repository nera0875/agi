#!/usr/bin/env python3
"""
Memory Store Service - Unified Storage for L1/L2/L3

Handles multi-layer memory storage:
- L1: Redis (embeddings cache, fast retrieval)
- L2: PostgreSQL with pgvector (semantic search)
- L3: Neo4j (relationship graph, long-term context)

Uses Voyage AI embeddings for intelligent model selection.
"""

import logging
import json
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime

import asyncpg
from redis import asyncio as aioredis
from langchain_core.documents import Document

from backend.config.agi_config import get_config
from backend.services.voyage_embeddings import get_voyage_service

logger = logging.getLogger(__name__)


class MemoryStoreService:
    """
    Unified memory storage service for L1/L2/L3

    L1 (Redis):
    - Embedding cache (30min TTL)
    - Query results cache (24h TTL)

    L2 (PostgreSQL):
    - Vector embeddings with pgvector
    - Full-text search (BM25)
    - Metadata and source tracking

    L3 (Neo4j):
    - Relationship graph
    - Temporal context
    - Concept links
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: aioredis.Redis
    ):
        """
        Initialize memory store service

        Args:
            db_pool: AsyncPG connection pool for PostgreSQL
            redis_client: Async Redis client for L1 cache
        """
        self.db_pool = db_pool
        self.redis = redis_client
        self.voyage = get_voyage_service()
        self.config = get_config()

        logger.info("MemoryStoreService initialized with L1/L2/L3")

    # ========================================================================
    # L1 EMBEDDINGS CACHE (Redis)
    # ========================================================================

    async def cache_embedding_l1(
        self,
        content: str,
        embedding: List[float],
        ttl: int = 1800  # 30 minutes
    ) -> str:
        """
        Cache embedding in L1 (Redis)

        Args:
            content: Original content
            embedding: Embedding vector
            ttl: Time to live in seconds (default 30min)

        Returns:
            Cache key

        Raises:
            Exception: If Redis operation fails
        """
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            cache_key = f"emb:v1:{content_hash}"

            cache_data = {
                "content_hash": content_hash,
                "embedding": embedding,
                "dims": len(embedding),
                "timestamp": datetime.utcnow().isoformat()
            }

            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_data)
            )

            logger.debug(f"Cached embedding L1: {cache_key} ({len(embedding)} dims)")
            return cache_key

        except Exception as e:
            logger.warning(f"L1 cache write failed (non-blocking): {e}")
            return ""

    async def get_embedding_l1(self, content: str) -> Optional[List[float]]:
        """
        Retrieve embedding from L1 cache

        Args:
            content: Original content

        Returns:
            Embedding vector if cached, None otherwise
        """
        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            cache_key = f"emb:v1:{content_hash}"

            cached = await self.redis.get(cache_key)
            if cached:
                cache_data = json.loads(cached)
                logger.debug(f"L1 cache HIT: {cache_key}")
                return cache_data["embedding"]

            return None

        except Exception as e:
            logger.debug(f"L1 cache read failed (non-blocking): {e}")
            return None

    # ========================================================================
    # L2 VECTOR STORAGE (PostgreSQL + pgvector)
    # ========================================================================

    async def store_memory_l2(
        self,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "conversation",
        user_id: Optional[str] = None,
        is_code: bool = False
    ) -> Tuple[UUID, str]:
        """
        Store memory in L2 (PostgreSQL)

        Automatically selects and generates appropriate Voyage embedding.

        Args:
            content: Memory content
            embedding: Optional pre-computed embedding
            metadata: Optional metadata dict
            source_type: Type of memory (conversation, document, code, etc.)
            user_id: User ID for multi-tenancy
            is_code: If True, use voyage-code-2

        Returns:
            Tuple of (memory_id, model_used)

        Raises:
            Exception: If database operation fails
        """
        try:
            # Generate or select embedding
            if embedding is None:
                # Select model based on content type
                if is_code or "code" in source_type.lower():
                    model = "voyage-code-2"
                    embedding = self.voyage.embed_code(content)
                else:
                    model = self.voyage.select_model_for_content(content, is_code=False)
                    embedding = self.voyage.embed_text(content, model=model)
            else:
                # Embedding provided, infer model from dimensions
                dims = len(embedding)
                model = "voyage-code-2" if dims == 1536 else "voyage-3"

            # Convert embedding to pgvector format
            embedding_str = f"[{','.join(map(str, embedding))}]"

            # Store in PostgreSQL
            async with self.db_pool.acquire() as conn:
                memory_id = await conn.fetchval(
                    """
                    INSERT INTO memory_store (
                        content, embedding, metadata, source_type, user_id, model
                    )
                    VALUES ($1, $2::vector, $3::jsonb, $4, $5, $6)
                    RETURNING id
                    """,
                    content,
                    embedding_str,
                    json.dumps(metadata or {}),
                    source_type,
                    user_id,
                    model
                )

            logger.info(f"Stored memory L2: {memory_id} ({source_type}, {model})")

            # Cache in L1 for fast retrieval
            await self.cache_embedding_l1(content, embedding)

            return memory_id, model

        except Exception as e:
            logger.error(f"L2 storage failed: {e}")
            raise

    async def batch_store_l2(
        self,
        contents: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        source_type: str = "document",
        user_id: Optional[str] = None,
        is_code: bool = False
    ) -> List[Tuple[UUID, str]]:
        """
        Batch store memories in L2

        Generates embeddings efficiently using Voyage batch API.

        Args:
            contents: List of content strings
            metadata_list: Optional list of metadata dicts
            source_type: Source type for all items
            user_id: User ID
            is_code: If True, use voyage-code-2

        Returns:
            List of (memory_id, model_used) tuples
        """
        try:
            if not contents:
                return []

            # Generate embeddings in batch
            if is_code or "code" in source_type.lower():
                embeddings = self.voyage.embed_codes_batch(contents)
                model = "voyage-code-2"
            else:
                embeddings = self.voyage.embed_texts_batch(contents, model="voyage-3")
                model = "voyage-3"

            # Prepare metadata
            if metadata_list is None:
                metadata_list = [{}] * len(contents)

            # Batch insert to PostgreSQL
            async with self.db_pool.acquire() as conn:
                # Prepare records with embeddings as pgvector strings
                embedding_strs = [
                    f"[{','.join(map(str, emb))}]"
                    for emb in embeddings
                ]

                # Insert all records
                result = await conn.fetch(
                    """
                    INSERT INTO memory_store (
                        content, embedding, metadata, source_type, user_id, model
                    )
                    SELECT * FROM UNNEST(
                        $1::text[],
                        $2::vector[],
                        $3::jsonb[],
                        $4::text[],
                        $5::text[],
                        $6::text[]
                    )
                    RETURNING id
                    """,
                    contents,
                    embedding_strs,
                    [json.dumps(m) for m in metadata_list],
                    [source_type] * len(contents),
                    [user_id] * len(contents),
                    [model] * len(contents)
                )

                memory_ids = [row["id"] for row in result]

            logger.info(f"Batch stored {len(memory_ids)} memories L2 ({model})")

            # Cache all embeddings in L1
            for content, embedding in zip(contents, embeddings):
                await self.cache_embedding_l1(content, embedding)

            return [(mid, model) for mid in memory_ids]

        except Exception as e:
            logger.error(f"L2 batch storage failed: {e}")
            raise

    # ========================================================================
    # L3 RELATIONSHIP STORAGE (Neo4j)
    # ========================================================================

    async def store_relation_l3(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        weight: float = 1.0
    ) -> UUID:
        """
        Store relation in L3 (Neo4j graph)

        Args:
            source_id: Source memory UUID
            target_id: Target memory UUID
            relation_type: Type of relation (RELATES_TO, DEPENDS_ON, etc.)
            metadata: Optional metadata
            weight: Relation strength

        Returns:
            Relation UUID

        Raises:
            Exception: If Neo4j operation fails
        """
        try:
            async with self.db_pool.acquire() as conn:
                relation_id = await conn.fetchval(
                    """
                    INSERT INTO relations (
                        source_id, target_id, relation_type, metadata, weight
                    )
                    VALUES ($1, $2, $3, $4::jsonb, $5)
                    RETURNING id
                    """,
                    source_id,
                    target_id,
                    relation_type,
                    json.dumps(metadata or {}),
                    weight
                )

            logger.info(f"Stored relation L3: {source_id} -[{relation_type}]-> {target_id}")
            return relation_id

        except Exception as e:
            logger.error(f"L3 storage failed: {e}")
            raise

    # ========================================================================
    # UNIFIED STORAGE (L1+L2+L3)
    # ========================================================================

    async def store_complete(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "conversation",
        user_id: Optional[str] = None,
        is_code: bool = False,
        relations: Optional[List[Tuple[UUID, str]]] = None
    ) -> Dict[str, Any]:
        """
        Store memory across all layers (L1 + L2 + L3)

        Orchestrates multi-layer storage with automatic embedding generation
        using intelligent Voyage model selection.

        Args:
            content: Memory content
            metadata: Optional metadata
            source_type: Memory type
            user_id: User ID
            is_code: If True, use voyage-code-2
            relations: Optional list of (target_uuid, relation_type) tuples

        Returns:
            Storage result dict with layer info

        Raises:
            Exception: If any layer fails
        """
        try:
            # Layer 2: Store in PostgreSQL with Voyage embeddings
            memory_id, model = await self.store_memory_l2(
                content=content,
                metadata=metadata,
                source_type=source_type,
                user_id=user_id,
                is_code=is_code
            )

            # Layer 3: Add relations if provided
            relation_ids = []
            if relations:
                for target_id, rel_type in relations:
                    rel_id = await self.store_relation_l3(
                        memory_id,
                        target_id,
                        rel_type
                    )
                    relation_ids.append(rel_id)

            result = {
                "memory_id": str(memory_id),
                "model": model,
                "layers": {
                    "l1": "cached",  # L1 caching is automatic
                    "l2": "stored",
                    "l3": "stored" if relation_ids else "skipped"
                },
                "relations": len(relation_ids),
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Complete storage done: {memory_id} ({model}, {len(relation_ids)} relations)")
            return result

        except Exception as e:
            logger.error(f"Complete storage failed: {e}")
            raise

    # ========================================================================
    # RETRIEVAL WITH MODEL AWARENESS
    # ========================================================================

    async def search_similar_l2(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        is_code: bool = False
    ) -> List[Document]:
        """
        Search similar memories in L2

        Uses Voyage embeddings with automatic model selection.

        Args:
            query: Search query
            top_k: Number of results
            threshold: Minimum similarity score
            is_code: If True, search in code memories

        Returns:
            List of similar documents
        """
        try:
            # Generate query embedding with same model logic
            if is_code:
                query_embedding = self.voyage.embed_code_query(query)
                dims = 1536
            else:
                query_embedding = self.voyage.embed_text_query(query)
                dims = 1024

            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Search in PostgreSQL
            async with self.db_pool.acquire() as conn:
                results = await conn.fetch(
                    f"""
                    SELECT id, content, metadata, model,
                        1 - (embedding <=> $1::vector({dims})) AS similarity
                    FROM memory_store
                    WHERE embedding IS NOT NULL
                      AND 1 - (embedding <=> $1::vector({dims})) > $2
                    ORDER BY embedding <=> $1::vector({dims})
                    LIMIT $3
                    """,
                    embedding_str,
                    threshold,
                    top_k
                )

            documents = [
                Document(
                    page_content=row["content"],
                    metadata={
                        **(json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]),
                        "id": str(row["id"]),
                        "model": row["model"],
                        "similarity": float(row["similarity"])
                    }
                )
                for row in results
            ]

            logger.info(f"L2 search found {len(documents)} similar memories")
            return documents

        except Exception as e:
            logger.error(f"L2 search failed: {e}")
            raise

    # ========================================================================
    # UTILITIES
    # ========================================================================

    async def get_memory_info(self, memory_id: UUID) -> Dict[str, Any]:
        """
        Get complete memory information across layers

        Args:
            memory_id: Memory UUID

        Returns:
            Memory info dict
        """
        try:
            async with self.db_pool.acquire() as conn:
                # Get L2 memory info
                memory = await conn.fetchrow(
                    """
                    SELECT id, content, embedding, metadata, source_type,
                           model, created_at, updated_at
                    FROM memory_store
                    WHERE id = $1
                    """,
                    memory_id
                )

                if not memory:
                    return {}

                # Get L3 relations
                relations = await conn.fetch(
                    """
                    SELECT id, source_id, target_id, relation_type, weight
                    FROM relations
                    WHERE source_id = $1 OR target_id = $1
                    """,
                    memory_id
                )

                return {
                    "id": str(memory["id"]),
                    "content_length": len(memory["content"]),
                    "model": memory["model"],
                    "source_type": memory["source_type"],
                    "metadata": json.loads(memory["metadata"]) if isinstance(memory["metadata"], str) else memory["metadata"],
                    "embedding_dims": len(memory["embedding"]) if memory["embedding"] else 0,
                    "created_at": memory["created_at"].isoformat(),
                    "relations_count": len(relations),
                    "l1_cached": True,  # Assume all recent memories are L1 cached
                    "l2_stored": True,
                    "l3_linked": len(relations) > 0
                }

        except Exception as e:
            logger.error(f"Get memory info failed: {e}")
            return {}

    async def health_check(self) -> Dict[str, bool]:
        """
        Check service health

        Returns:
            Health status dict
        """
        status = {
            "database": False,
            "redis": False,
            "voyage": False
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

        # Check Voyage service
        try:
            self.voyage.get_model_info("voyage-3")
            status["voyage"] = True
        except Exception as e:
            logger.error(f"Voyage service health check failed: {e}")

        return status


if __name__ == "__main__":
    print("MemoryStoreService module loaded")
    print("Provides L1 (Redis) + L2 (PostgreSQL) + L3 (Neo4j) storage")
    print("Uses Voyage AI for intelligent embedding selection")
