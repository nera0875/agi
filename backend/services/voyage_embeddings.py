#!/usr/bin/env python3
"""
Voyage AI Embeddings Service

Integrates Voyage AI for multi-model embeddings:
- voyage-code-2 (1536 dims) - Specialized for code
- voyage-3 (1024 dims) - For general text
- voyage-3-large (1024 dims) - For larger texts

Provides unified interface for embedding code, text, and queries.
"""

import logging
from typing import List, Optional
from functools import lru_cache

try:
    from voyageai import Client as VoyageClient
except ImportError:
    raise ImportError("voyageai package required: pip install voyageai")

from backend.config.agi_config import get_config

logger = logging.getLogger(__name__)


class VoyageEmbeddingService:
    """
    Service for generating embeddings using Voyage AI models

    Supports:
    - voyage-code-2: Specialized for code (1536 dims)
    - voyage-3: General text (1024 dims)
    - voyage-3-large: Large texts (1024 dims)

    Features:
    - Model selection based on input type
    - Input type hints (document vs query)
    - Error handling and logging
    """

    def __init__(self):
        """Initialize Voyage AI client with API key from config"""
        config = get_config()
        self.client = VoyageClient(api_key=config.voyage_api_key)
        self.config = config

        logger.info("VoyageEmbeddingService initialized")

    # ========================================================================
    # CODE EMBEDDINGS
    # ========================================================================

    def embed_code(self, code: str) -> List[float]:
        """
        Generate embedding for code using voyage-code-2

        Args:
            code: Code snippet or document

        Returns:
            Embedding vector (1536 dimensions)

        Raises:
            Exception: If API call fails
        """
        try:
            result = self.client.embed(
                [code],
                model="voyage-code-2",
                input_type="document"
            )
            embedding = result.embeddings[0]
            logger.debug(f"Generated code embedding (1536 dims, {len(code)} chars)")
            return embedding

        except Exception as e:
            logger.error(f"Code embedding failed: {e}")
            raise

    def embed_code_query(self, query: str) -> List[float]:
        """
        Generate embedding for code search query using voyage-code-2

        Args:
            query: Code search query

        Returns:
            Embedding vector (1536 dimensions)

        Raises:
            Exception: If API call fails
        """
        try:
            result = self.client.embed(
                [query],
                model="voyage-code-2",
                input_type="query"
            )
            embedding = result.embeddings[0]
            logger.debug(f"Generated code query embedding (1536 dims)")
            return embedding

        except Exception as e:
            logger.error(f"Code query embedding failed: {e}")
            raise

    # ========================================================================
    # TEXT EMBEDDINGS
    # ========================================================================

    def embed_text(self, text: str, model: str = "voyage-3") -> List[float]:
        """
        Generate embedding for text using voyage-3 or voyage-3-large

        Args:
            text: Text to embed
            model: Model to use ("voyage-3" or "voyage-3-large"), default: "voyage-3"

        Returns:
            Embedding vector (1024 dimensions)

        Raises:
            Exception: If API call fails
        """
        if model not in ["voyage-3", "voyage-3-large"]:
            raise ValueError(f"Invalid model: {model}. Use 'voyage-3' or 'voyage-3-large'")

        try:
            result = self.client.embed(
                [text],
                model=model,
                input_type="document"
            )
            embedding = result.embeddings[0]
            logger.debug(f"Generated text embedding ({model}, 1024 dims, {len(text)} chars)")
            return embedding

        except Exception as e:
            logger.error(f"Text embedding failed ({model}): {e}")
            raise

    def embed_text_query(self, query: str, model: str = "voyage-3") -> List[float]:
        """
        Generate embedding for text search query using voyage-3

        Args:
            query: Search query text
            model: Model to use ("voyage-3" or "voyage-3-large"), default: "voyage-3"

        Returns:
            Embedding vector (1024 dimensions)

        Raises:
            Exception: If API call fails
        """
        if model not in ["voyage-3", "voyage-3-large"]:
            raise ValueError(f"Invalid model: {model}. Use 'voyage-3' or 'voyage-3-large'")

        try:
            result = self.client.embed(
                [query],
                model=model,
                input_type="query"
            )
            embedding = result.embeddings[0]
            logger.debug(f"Generated text query embedding ({model}, 1024 dims)")
            return embedding

        except Exception as e:
            logger.error(f"Text query embedding failed ({model}): {e}")
            raise

    # ========================================================================
    # SEMANTIC SEARCH EMBEDDINGS
    # ========================================================================

    def embed_query(
        self,
        query: str,
        for_code: bool = False,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for semantic search query

        Automatically selects appropriate model based on input type.
        Used for L1/L2/L3 memory retrieval.

        Args:
            query: Search query
            for_code: If True, use voyage-code-2. Otherwise use voyage-3
            model: Override model selection (optional)

        Returns:
            Embedding vector

        Raises:
            Exception: If API call fails
        """
        if model:
            if model == "voyage-code-2":
                return self.embed_code_query(query)
            elif model in ["voyage-3", "voyage-3-large"]:
                return self.embed_text_query(query, model=model)
            else:
                raise ValueError(f"Invalid model: {model}")

        # Auto-select based on for_code flag
        if for_code:
            return self.embed_code_query(query)
        else:
            return self.embed_text_query(query)

    # ========================================================================
    # BATCH EMBEDDINGS
    # ========================================================================

    def embed_texts_batch(
        self,
        texts: List[str],
        model: str = "voyage-3"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed
            model: Model to use ("voyage-3" or "voyage-3-large")

        Returns:
            List of embedding vectors

        Raises:
            Exception: If API call fails
        """
        if not texts:
            return []

        if model not in ["voyage-3", "voyage-3-large"]:
            raise ValueError(f"Invalid model: {model}. Use 'voyage-3' or 'voyage-3-large'")

        try:
            result = self.client.embed(
                texts,
                model=model,
                input_type="document"
            )
            embeddings = result.embeddings
            logger.info(f"Generated batch embeddings ({model}, {len(embeddings)} texts, 1024 dims)")
            return embeddings

        except Exception as e:
            logger.error(f"Batch text embedding failed ({model}): {e}")
            raise

    def embed_codes_batch(self, codes: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple code snippets in batch

        Args:
            codes: List of code snippets to embed

        Returns:
            List of embedding vectors (1536 dimensions each)

        Raises:
            Exception: If API call fails
        """
        if not codes:
            return []

        try:
            result = self.client.embed(
                codes,
                model="voyage-code-2",
                input_type="document"
            )
            embeddings = result.embeddings
            logger.info(f"Generated batch code embeddings ({len(embeddings)} codes, 1536 dims)")
            return embeddings

        except Exception as e:
            logger.error(f"Batch code embedding failed: {e}")
            raise

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def get_model_info(self, model: str) -> dict:
        """
        Get model information and specifications

        Args:
            model: Model name

        Returns:
            Dict with model specs
        """
        models_info = {
            "voyage-code-2": {
                "name": "Voyage Code 2",
                "dimensions": 1536,
                "purpose": "Code embedding",
                "input_types": ["document", "query"]
            },
            "voyage-3": {
                "name": "Voyage 3",
                "dimensions": 1024,
                "purpose": "General text embedding",
                "input_types": ["document", "query"]
            },
            "voyage-3-large": {
                "name": "Voyage 3 Large",
                "dimensions": 1024,
                "purpose": "Large text embedding",
                "input_types": ["document", "query"]
            }
        }

        if model not in models_info:
            raise ValueError(f"Unknown model: {model}")

        return models_info[model]

    def select_model_for_content(self, content: str, is_code: bool = False) -> str:
        """
        Intelligently select embedding model based on content

        Args:
            content: Content to embed
            is_code: If True, prefer code model

        Returns:
            Recommended model name
        """
        # If explicit code hint
        if is_code:
            return "voyage-code-2"

        # Heuristics for content type detection
        content_len = len(content)

        # Large texts use voyage-3-large
        if content_len > 5000:
            logger.debug(f"Selecting voyage-3-large for large text ({content_len} chars)")
            return "voyage-3-large"

        # Default to voyage-3
        logger.debug(f"Selecting voyage-3 for text ({content_len} chars)")
        return "voyage-3"

    # ========================================================================
    # L3 KNOWLEDGE EMBEDDINGS
    # ========================================================================

    def embed_l3_knowledge(self, content: str) -> List[float]:
        """
        Embed L3 knowledge with voyage-3-large (1024 dims)
        For long-term memory storage

        Args:
            content: Knowledge content to embed

        Returns:
            Embedding vector (1024 dimensions)

        Raises:
            Exception: If API call fails
        """
        try:
            result = self.client.embed(
                [content],
                model="voyage-3-large",
                input_type="document"
            )
            embedding = result.embeddings[0]
            logger.debug(f"Generated L3 knowledge embedding (1024 dims, {len(content)} chars)")
            return embedding

        except Exception as e:
            logger.error(f"L3 knowledge embedding failed: {e}")
            raise

    def search_l3_similar(
        self,
        query: str,
        embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[int]:
        """
        Find similar L3 knowledge items using cosine similarity

        Args:
            query: Search query
            embeddings: List of embedding vectors to search
            top_k: Number of top results to return

        Returns:
            List of indices sorted by similarity (highest first)

        Raises:
            Exception: If API call fails
        """
        try:
            from sklearn.metrics.pairwise import cosine_similarity

            # Embed query
            query_emb = self.client.embed(
                [query],
                model="voyage-3-large",
                input_type="query"
            ).embeddings[0]

            # Calculate cosine similarity scores
            scores = [cosine_similarity([query_emb], [emb])[0][0] for emb in embeddings]

            # Return sorted indices (highest similarity first)
            sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            result_indices = sorted_indices[:top_k]

            logger.debug(f"Found {len(result_indices)} similar L3 knowledge items")
            return result_indices

        except ImportError:
            logger.error("scikit-learn required for similarity search: pip install scikit-learn")
            raise
        except Exception as e:
            logger.error(f"L3 similarity search failed: {e}")
            raise


# Singleton instance
_voyage_service: Optional[VoyageEmbeddingService] = None


def get_voyage_service() -> VoyageEmbeddingService:
    """
    Get or create Voyage embedding service singleton

    Returns:
        VoyageEmbeddingService instance
    """
    global _voyage_service
    if _voyage_service is None:
        _voyage_service = VoyageEmbeddingService()
    return _voyage_service


if __name__ == "__main__":
    # Test embeddings service
    import asyncio

    service = get_voyage_service()

    # Test code embedding
    code_sample = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """

    code_emb = service.embed_code(code_sample)
    print(f"Code embedding dims: {len(code_emb)}")

    # Test text embedding
    text_sample = "This is a sample text for embedding"
    text_emb = service.embed_text(text_sample)
    print(f"Text embedding dims: {len(text_emb)}")

    # Test query embedding
    query_emb = service.embed_query("Find fibonacci implementation", for_code=True)
    print(f"Query embedding dims: {len(query_emb)}")

    # Test model info
    print("\nVoyage Code 2 specs:", service.get_model_info("voyage-code-2"))
