"""
Cohere Rerank Wrapper - Précision Retrieval
Modèle: rerank-v3.5
Coût: $2 per 1K searches
"""

import hashlib
import httpx
import asyncpg
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)

# Cohere Config
COHERE_API_KEY = "TkkNADrL73TjYBwD6c4jNi3jRvL4h5PbslZ8W7C8"  # Depuis .env
COHERE_API_URL = "https://api.cohere.com/v2/rerank"
COHERE_MODEL = "rerank-v3.5"

# Database pool
db_pool: Optional[asyncpg.Pool] = None


def set_db_pool(pool: asyncpg.Pool):
    """Set database pool for caching"""
    global db_pool
    db_pool = pool


def compute_rerank_hash(query: str, document_ids: List[str]) -> str:
    """Compute hash for caching (query + sorted doc IDs)"""
    sorted_ids = sorted(document_ids)
    combined = f"{query}::{':'.join(sorted_ids)}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


async def rerank(
    query: str,
    documents: List[Dict],
    top_n: int = 5,
    model: str = COHERE_MODEL,
    use_cache: bool = True
) -> List[Dict]:
    """
    Rerank documents using Cohere Rerank API

    Args:
        query: Search query
        documents: List of documents with 'id' and 'text' fields
        top_n: Number of top results to return
        model: Cohere model (default: rerank-v3.5)
        use_cache: Use PostgreSQL cache

    Returns:
        Reranked documents with relevance_score
    """

    document_ids = [str(doc.get('id', i)) for i, doc in enumerate(documents)]
    document_texts = [doc['text'] for doc in documents]

    # 1. Check cache
    if use_cache and db_pool:
        rerank_hash = compute_rerank_hash(query, document_ids)

        try:
            async with db_pool.acquire() as conn:
                cached = await conn.fetchrow(
                    """
                    SELECT reranked_ids, relevance_scores, hit_count
                    FROM cohere_rerank_cache
                    WHERE query_hash = $1
                    """,
                    rerank_hash
                )

                if cached:
                    # Cache HIT
                    reranked_ids = cached['reranked_ids']
                    relevance_scores = cached['relevance_scores']

                    # Update hit count
                    await conn.execute(
                        """
                        UPDATE cohere_rerank_cache
                        SET hit_count = hit_count + 1, last_hit = NOW()
                        WHERE query_hash = $1
                        """,
                        rerank_hash
                    )

                    logger.info(f"✅ Rerank cache HIT (hash: {rerank_hash[:8]}..., hits: {cached['hit_count']})")

                    # Reconstruct results from cache
                    id_to_doc = {str(doc.get('id', i)): doc for i, doc in enumerate(documents)}
                    results = []

                    for doc_id, score in zip(reranked_ids[:top_n], relevance_scores[:top_n]):
                        doc = id_to_doc.get(doc_id)
                        if doc:
                            doc['relevance_score'] = score
                            results.append(doc)

                    return results

        except Exception as e:
            logger.warning(f"Rerank cache read error: {e}, fetching from API")

    # 2. Fetch from Cohere API (cache miss)
    logger.info(f"🌐 Reranking {len(documents)} documents via Cohere API...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                COHERE_API_URL,
                headers={
                    "Authorization": f"Bearer {COHERE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "query": query,
                    "documents": [{"text": text} for text in document_texts],
                    "top_n": top_n,
                    "return_documents": False  # We already have them
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract results
            reranked_results = []
            reranked_ids = []
            relevance_scores = []

            for item in data.get('results', []):
                index = item['index']
                score = item['relevance_score']

                doc = documents[index].copy()
                doc['relevance_score'] = score

                reranked_results.append(doc)
                reranked_ids.append(document_ids[index])
                relevance_scores.append(score)

            # 3. Cache results
            if use_cache and db_pool:
                rerank_hash = compute_rerank_hash(query, document_ids)

                try:
                    async with db_pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO cohere_rerank_cache
                                (query_hash, query, document_ids, reranked_ids, relevance_scores)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (query_hash) DO UPDATE
                            SET hit_count = cohere_rerank_cache.hit_count + 1,
                                last_hit = NOW()
                            """,
                            rerank_hash, query, document_ids, reranked_ids, relevance_scores
                        )
                except Exception as e:
                    logger.warning(f"Rerank cache write error: {e}")

            logger.info(f"✅ Reranked {len(reranked_results)} documents via Cohere")

            return reranked_results

    except httpx.HTTPStatusError as e:
        logger.error(f"Cohere API error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Cohere rerank error: {e}")
        raise


async def hybrid_search_and_rerank(
    query: str,
    table_name: str = "agi_knowledge",
    semantic_limit: int = 20,
    top_n: int = 5,
    semantic_threshold: float = 0.5
) -> List[Dict]:
    """
    Complete hybrid search workflow:
    1. Semantic search (Voyage AI + pgvector)
    2. Rerank (Cohere)

    Args:
        query: Search query
        table_name: Table to search
        semantic_limit: Initial candidates from semantic search
        top_n: Final top results after reranking
        semantic_threshold: Minimum similarity for semantic search

    Returns:
        Top reranked documents
    """

    # Import here to avoid circular dependency
    from voyage_wrapper import semantic_search

    # 1. Semantic search (broad recall)
    logger.info(f"🔍 Step 1: Semantic search (top {semantic_limit})...")
    semantic_results = await semantic_search(
        query=query,
        table_name=table_name,
        limit=semantic_limit,
        threshold=semantic_threshold
    )

    if not semantic_results:
        logger.warning("No semantic search results found")
        return []

    # 2. Prepare documents for reranking
    documents = []
    for result in semantic_results:
        # Extract text field based on table
        if table_name == "agi_knowledge":
            text = result.get('content', '')
        elif table_name == "conversation_episodes":
            text = result.get('summary', '')
        elif table_name == "memory_store":
            text = result.get('content', '')
        else:
            text = str(result)

        documents.append({
            'id': str(result['id']),
            'text': text,
            **result  # Include all original fields
        })

    # 3. Rerank (precision)
    logger.info(f"🎯 Step 2: Reranking (top {top_n})...")
    reranked = await rerank(
        query=query,
        documents=documents,
        top_n=top_n
    )

    return reranked


# ═══════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════

"""
# Initialize
import asyncpg
from cohere_wrapper import set_db_pool, hybrid_search_and_rerank

pool = await asyncpg.create_pool("postgresql://agi_user:agi_password@localhost/agi_db")
set_db_pool(pool)

# Also set for voyage_wrapper
from voyage_wrapper import set_db_pool as set_voyage_pool
set_voyage_pool(pool)

# Hybrid search + rerank
results = await hybrid_search_and_rerank(
    query="How does LTP reinforcement work?",
    table_name="agi_knowledge",
    semantic_limit=20,  # Broad recall
    top_n=5             # Precision rerank
)

for i, result in enumerate(results, 1):
    print(f"{i}. Relevance: {result['relevance_score']:.3f}")
    print(f"   Similarity: {result['similarity']:.3f}")
    print(f"   Content: {result.get('content', result.get('summary', ''))[:200]}...")
    print()
"""
