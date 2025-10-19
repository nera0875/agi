#!/usr/bin/env python3
"""
Cohere Rerank Service - L3 Result Re-ranking

Uses Cohere Rerank v3.5 model to improve search result relevance.
Integrates with L3 spreading activation and hybrid search results.

Features:
- Rerank L3 search results with state-of-the-art model
- Top-k retrieval support
- Relevance scoring
- Batch processing support
"""

from typing import List, Dict, Optional
import logging

try:
    import cohere
except ImportError:
    raise ImportError("cohere package required: pip install cohere")

from backend.config.agi_config import get_config


logger = logging.getLogger(__name__)


class CohereRerankService:
    """
    Reranking service using Cohere's Rerank v3.5 model

    Improves relevance of L3 search results by:
    1. Taking query and document list
    2. Computing semantic relevance scores
    3. Reordering by relevance with top-k filtering
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Cohere Rerank service

        Args:
            api_key: Cohere API key (loads from config if not provided)
        """
        if api_key is None:
            config = get_config()
            api_key = config.cohere_api_key

        if not api_key:
            raise ValueError(
                "Cohere API key not provided. Set COHERE_API_KEY in .env"
            )

        self.client = cohere.ClientV2(api_key=api_key)
        logger.info("Cohere Rerank Service initialized")

    def rerank_l3_results(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        model: str = "rerank-3.5-turbo"
    ) -> List[Dict]:
        """
        Rerank L3 search results using Cohere Rerank v3.5

        Takes query and list of documents, computes relevance scores,
        and returns top_k results reordered by relevance.

        Args:
            query: Search query string
            documents: List of document texts to rerank
            top_k: Number of top results to return (default 10)
            model: Cohere model to use (default rerank-3.5-turbo)

        Returns:
            List of dicts with format:
            [
                {
                    'index': 0,
                    'relevance_score': 0.95,
                    'document': 'document text',
                    'position': 1  # rank position after reranking
                },
                ...
            ]

        Raises:
            ValueError: If query or documents are invalid
            cohere.CohereAPIError: If API call fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not documents:
            raise ValueError("Documents list cannot be empty")

        if len(documents) > 1000:
            logger.warning(
                f"Large document list ({len(documents)}). "
                "Consider batching for better performance."
            )

        try:
            # Call Cohere rerank API
            response = self.client.rerank(
                model=model,
                query=query,
                documents=documents,
                top_n=min(top_k, len(documents)),
                return_documents=False  # We'll map indices back ourselves
            )

            # Transform response to our format
            ranked_results = []
            for position, result in enumerate(response.results, 1):
                ranked_results.append({
                    'index': result.index,
                    'relevance_score': round(float(result.relevance_score), 4),
                    'document': documents[result.index],
                    'position': position
                })

            logger.info(
                f"Reranked {len(documents)} documents for query '{query[:50]}...'. "
                f"Top-{top_k} results returned."
            )

            return ranked_results

        except cohere.CohereAPIError as e:
            logger.error(f"Cohere API error during reranking: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during reranking: {e}")
            raise

    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, any]],
        doc_text_key: str = "content",
        top_k: int = 10,
        model: str = "rerank-3.5-turbo"
    ) -> List[Dict]:
        """
        Rerank documents that have metadata

        Useful when documents are already enriched with metadata
        (source, score, timestamp, etc.)

        Args:
            query: Search query
            documents: List of dicts with at least doc_text_key field
            doc_text_key: Key in document dict containing the text
            top_k: Number of top results to return
            model: Cohere model to use

        Returns:
            List of reranked documents with their metadata + relevance_score

        Example:
            docs = [
                {"content": "async/await patterns", "source": "docs.md", "score": 0.8},
                {"content": "Redis caching", "source": "redis.md", "score": 0.7}
            ]
            ranked = service.rerank_with_metadata(
                query="async programming",
                documents=docs,
                doc_text_key="content"
            )
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")

        # Extract texts for reranking
        doc_texts = []
        original_docs = []
        for doc in documents:
            if isinstance(doc, dict):
                if doc_text_key not in doc:
                    raise ValueError(
                        f"Document missing '{doc_text_key}' field"
                    )
                doc_texts.append(doc[doc_text_key])
                original_docs.append(doc)
            else:
                raise ValueError(
                    "Documents must be dicts when using rerank_with_metadata"
                )

        # Rerank
        reranked = self.rerank_l3_results(
            query=query,
            documents=doc_texts,
            top_k=top_k,
            model=model
        )

        # Merge back with original metadata
        results_with_metadata = []
        for result in reranked:
            original_doc = original_docs[result['index']]
            merged = {
                **original_doc,  # Include all original metadata
                'relevance_score': result['relevance_score'],
                'rank_position': result['position'],
                'original_index': result['index']
            }
            results_with_metadata.append(merged)

        return results_with_metadata

    def rerank_batch(
        self,
        queries: List[str],
        documents_per_query: List[List[str]],
        top_k: int = 10,
        model: str = "rerank-3.5-turbo"
    ) -> List[List[Dict]]:
        """
        Batch rerank multiple queries

        Reranks documents for multiple queries in sequence.

        Args:
            queries: List of query strings
            documents_per_query: List[List[str]] - documents for each query
            top_k: Number of top results per query
            model: Cohere model to use

        Returns:
            List[List[Dict]] - Reranked results for each query

        Example:
            queries = ["async programming", "Redis cache"]
            docs = [
                ["doc1 about async", "doc2 about async", ...],
                ["doc1 about Redis", "doc2 about Redis", ...]
            ]
            all_results = service.rerank_batch(queries, docs, top_k=5)
        """
        if len(queries) != len(documents_per_query):
            raise ValueError(
                "queries and documents_per_query must have same length"
            )

        all_results = []
        for query, documents in zip(queries, documents_per_query):
            try:
                results = self.rerank_l3_results(
                    query=query,
                    documents=documents,
                    top_k=top_k,
                    model=model
                )
                all_results.append(results)
            except Exception as e:
                logger.error(
                    f"Error reranking batch for query '{query}': {e}"
                )
                all_results.append([])  # Return empty on error

        return all_results

    def rerank_spreading_activation_results(
        self,
        query: str,
        activation_results: List[Dict],
        top_k: int = 10,
        model: str = "rerank-3.5-turbo"
    ) -> List[Dict]:
        """
        Rerank results from spreading activation search

        Combines spreading activation relevance with Cohere reranking
        for hybrid scoring.

        Args:
            query: Original search query
            activation_results: Results from spreading_activation_advanced()
                Should contain 'content' and 'activation' fields
            top_k: Number of top results to return
            model: Cohere model to use

        Returns:
            List of reranked results with both activation and relevance scores:
            [
                {
                    'id': node_id,
                    'content': content,
                    'type': node_type,
                    'activation': original_activation_score,
                    'relevance_score': cohere_relevance,
                    'hybrid_score': combined_score,
                    'rank_position': position
                },
                ...
            ]
        """
        if not activation_results:
            return []

        # Extract content for reranking
        contents = [r.get('content', '') for r in activation_results]
        if not contents:
            return []

        # Rerank with Cohere
        reranked = self.rerank_l3_results(
            query=query,
            documents=contents,
            top_k=top_k,
            model=model
        )

        # Merge with original activation data
        results_hybrid = []
        for rank_result in reranked:
            original_result = activation_results[rank_result['index']]

            # Hybrid score: weighted average of activation and relevance
            activation_score = original_result.get('activation', 0.0)
            relevance_score = rank_result['relevance_score']

            # Weight: 40% activation (semantic spreading), 60% relevance (Cohere)
            hybrid_score = (0.4 * activation_score) + (0.6 * relevance_score)

            merged = {
                **original_result,  # Keep all original fields
                'relevance_score': relevance_score,
                'hybrid_score': round(hybrid_score, 4),
                'rank_position': rank_result['position'],
                'rerank_index': rank_result['index']
            }
            results_hybrid.append(merged)

        return results_hybrid


def create_cohere_rerank_service(api_key: Optional[str] = None) -> CohereRerankService:
    """
    Factory function to create CohereRerankService

    Args:
        api_key: Optional Cohere API key

    Returns:
        Initialized CohereRerankService instance
    """
    return CohereRerankService(api_key=api_key)


# ═══════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════

def rerank_results(
    query: str,
    documents: List[str],
    top_k: int = 10
) -> List[Dict]:
    """
    Quick rerank without explicit service creation

    Args:
        query: Search query
        documents: List of document texts
        top_k: Number of top results

    Returns:
        Reranked results
    """
    service = create_cohere_rerank_service()
    return service.rerank_l3_results(query=query, documents=documents, top_k=top_k)


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_cohere_rerank():
    """Test Cohere Rerank Service"""

    print("Cohere Rerank Service Test")
    print("=" * 60)

    try:
        # Initialize service
        service = create_cohere_rerank_service()
        print("OK: Cohere Rerank service initialized")

        # Test 1: Basic reranking
        print("\n1. Basic reranking...")
        query = "async programming patterns"
        documents = [
            "Async/await patterns in Python with asyncio library",
            "Redis cache implementation for web servers",
            "Concurrency models: async, threading, multiprocessing",
            "FastAPI framework with async request handlers",
            "Database optimization techniques"
        ]

        results = service.rerank_l3_results(query=query, documents=documents, top_k=3)
        print(f"   Reranked {len(results)} top results:")
        for r in results:
            print(
                f"   [{r['position']}] "
                f"Score: {r['relevance_score']:.3f} | "
                f"Doc: {r['document'][:50]}..."
            )

        # Test 2: Reranking with metadata
        print("\n2. Reranking with metadata...")
        docs_with_meta = [
            {
                "content": "Redis caching patterns",
                "source": "redis.md",
                "score": 0.8
            },
            {
                "content": "Python async/await examples",
                "source": "async.md",
                "score": 0.9
            },
            {
                "content": "FastAPI async handlers",
                "source": "fastapi.md",
                "score": 0.7
            }
        ]

        results_meta = service.rerank_with_metadata(
            query="async programming",
            documents=docs_with_meta,
            doc_text_key="content",
            top_k=2
        )
        print(f"   Reranked {len(results_meta)} results with metadata:")
        for r in results_meta:
            print(
                f"   [{r['rank_position']}] "
                f"Source: {r['source']} | "
                f"Relevance: {r['relevance_score']:.3f}"
            )

        print("\n" + "=" * 60)
        print("OK: All tests passed")

    except Exception as e:
        print(f"ERROR: {e}")
        raise


if __name__ == "__main__":
    test_cohere_rerank()
