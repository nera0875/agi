"""
Voyage AI Wrapper - Embeddings Sémantiques
Modèle: voyage-3 (1024 dimensions)
Coût: $0.13 per 1M tokens
"""

import hashlib
import httpx
import asyncpg
import os
from typing import List, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file for API keys
load_dotenv()

# Voyage AI Config
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-3"

# Database pool (initialisé depuis l'extérieur)
db_pool: Optional[asyncpg.Pool] = None


def set_db_pool(pool: asyncpg.Pool):
    """Set database pool for caching"""
    global db_pool
    db_pool = pool


def compute_text_hash(text: str) -> str:
    """Compute SHA256 hash for caching"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


async def get_embeddings(
    texts: List[str],
    model: str = VOYAGE_MODEL,
    use_cache: bool = True
) -> List[List[float]]:
    """
    Get embeddings from Voyage AI with caching

    Args:
        texts: List of texts to embed
        model: Voyage model (default: voyage-3)
        use_cache: Use PostgreSQL cache (default: True)

    Returns:
        List of embeddings (1024 dimensions each)
    """

    embeddings = []
    texts_to_fetch = []
    fetch_indices = []

    # 1. Check cache first
    if use_cache and db_pool:
        for i, text in enumerate(texts):
            text_hash = compute_text_hash(text)

            try:
                async with db_pool.acquire() as conn:
                    cached = await conn.fetchrow(
                        """
                        SELECT embedding, hit_count
                        FROM voyage_ai_cache
                        WHERE text_hash = $1 AND model = $2
                        """,
                        text_hash, model
                    )

                    if cached:
                        # Cache HIT
                        embeddings.append(list(cached['embedding']))

                        # Update hit count
                        await conn.execute(
                            """
                            UPDATE voyage_ai_cache
                            SET hit_count = hit_count + 1, last_hit = NOW()
                            WHERE text_hash = $1
                            """,
                            text_hash
                        )

                        logger.info(f"✅ Cache HIT for text (hash: {text_hash[:8]}..., hits: {cached['hit_count']})")
                    else:
                        # Cache MISS
                        embeddings.append(None)
                        texts_to_fetch.append(text)
                        fetch_indices.append(i)
            except Exception as e:
                logger.warning(f"Cache read error: {e}, fetching from API")
                embeddings.append(None)
                texts_to_fetch.append(text)
                fetch_indices.append(i)
    else:
        # No cache, fetch all
        texts_to_fetch = texts
        fetch_indices = list(range(len(texts)))
        embeddings = [None] * len(texts)

    # 2. Fetch from Voyage AI for cache misses
    if texts_to_fetch:
        logger.info(f"🌐 Fetching {len(texts_to_fetch)} embeddings from Voyage AI...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    VOYAGE_API_URL,
                    headers={
                        "Authorization": f"Bearer {VOYAGE_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": texts_to_fetch,
                        "model": model
                    }
                )

                response.raise_for_status()
                data = response.json()

                # Extract embeddings
                fetched_embeddings = [item['embedding'] for item in data['data']]

                # 3. Cache results
                if use_cache and db_pool:
                    async with db_pool.acquire() as conn:
                        for text, embedding in zip(texts_to_fetch, fetched_embeddings):
                            text_hash = compute_text_hash(text)

                            try:
                                await conn.execute(
                                    """
                                    INSERT INTO voyage_ai_cache (text_hash, text, embedding, model)
                                    VALUES ($1, $2, $3, $4)
                                    ON CONFLICT (text_hash) DO NOTHING
                                    """,
                                    text_hash, text, embedding, model
                                )
                            except Exception as e:
                                logger.warning(f"Cache write error: {e}")

                # 4. Merge with cached results
                for i, idx in enumerate(fetch_indices):
                    embeddings[idx] = fetched_embeddings[i]

                logger.info(f"✅ Fetched {len(fetched_embeddings)} embeddings from Voyage AI")

        except httpx.HTTPStatusError as e:
            logger.error(f"Voyage AI API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Voyage AI error: {e}")
            raise

    return embeddings


async def embed_single(text: str, model: str = VOYAGE_MODEL, use_cache: bool = True) -> List[float]:
    """
    Embed single text (convenience function)

    Args:
        text: Text to embed
        model: Voyage model
        use_cache: Use cache

    Returns:
        Embedding (1024 dimensions)
    """
    embeddings = await get_embeddings([text], model, use_cache)
    return embeddings[0]


async def semantic_search(
    query: str,
    table_name: str = "agi_knowledge",
    limit: int = 20,
    threshold: float = 0.0
) -> List[dict]:
    """
    Semantic search using pgvector cosine similarity

    Args:
        query: Search query
        table_name: Table to search (must have 'embedding' column)
        limit: Max results
        threshold: Minimum similarity (0.0-1.0)

    Returns:
        List of {id, content, similarity, ...}
    """

    if not db_pool:
        raise RuntimeError("Database pool not initialized. Call set_db_pool() first.")

    # 1. Get query embedding
    query_embedding = await embed_single(query)

    # 2. Search in PostgreSQL with pgvector
    async with db_pool.acquire() as conn:
        # Different queries per table
        if table_name == "agi_knowledge":
            results = await conn.fetch(
                f"""
                SELECT
                    id,
                    section,
                    content,
                    tags,
                    priority,
                    strength,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {table_name}
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                query_embedding, threshold, limit
            )
        elif table_name == "conversation_episodes":
            results = await conn.fetch(
                f"""
                SELECT
                    id,
                    summary,
                    key_learnings,
                    decisions_made,
                    next_session_context,
                    strength,
                    timestamp,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {table_name}
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                query_embedding, threshold, limit
            )
        elif table_name == "memory_store":
            results = await conn.fetch(
                f"""
                SELECT
                    id,
                    content,
                    metadata,
                    strength,
                    created_at,
                    1 - (embedding <=> $1::vector) as similarity
                FROM {table_name}
                WHERE embedding IS NOT NULL
                  AND 1 - (embedding <=> $1::vector) >= $2
                ORDER BY embedding <=> $1::vector
                LIMIT $3
                """,
                query_embedding, threshold, limit
            )
        else:
            raise ValueError(f"Unsupported table: {table_name}")

        return [dict(row) for row in results]


async def embed_and_store(
    table_name: str,
    record_id: str,
    text: str,
    update: bool = True
):
    """
    Generate embedding and store in table

    Args:
        table_name: Table name
        record_id: Record ID (UUID)
        text: Text to embed
        update: Update existing record (default: True)
    """

    if not db_pool:
        raise RuntimeError("Database pool not initialized")

    # Get embedding
    embedding = await embed_single(text)

    # Store in table
    async with db_pool.acquire() as conn:
        if update:
            await conn.execute(
                f"UPDATE {table_name} SET embedding = $1 WHERE id = $2",
                embedding, record_id
            )
        else:
            # Assume INSERT (table-specific logic needed)
            raise NotImplementedError("INSERT mode not implemented, use update=True")

    logger.info(f"✅ Embedded and stored in {table_name} (id: {record_id})")


# ═══════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════

"""
# Initialize
import asyncpg
from voyage_wrapper import set_db_pool, semantic_search, embed_and_store

pool = await asyncpg.create_pool("postgresql://agi_user:agi_password@localhost/agi_db")
set_db_pool(pool)

# Semantic search
results = await semantic_search(
    query="How does spreading activation work?",
    table_name="agi_knowledge",
    limit=5,
    threshold=0.7
)

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Content: {result['content'][:200]}...")

# Embed and store
await embed_and_store(
    table_name="agi_knowledge",
    record_id="some-uuid",
    text="New knowledge to store",
    update=True
)
"""
