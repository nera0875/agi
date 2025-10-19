"""
Test semantic cache implementation
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.memory_service import cosine_similarity


class TestSemanticCache:
    """Test semantic cache functions"""

    def test_identical_vectors(self):
        """Two identical vectors should have similarity 1.0"""
        v1 = [0.5, 0.5, 0.707]
        v2 = [0.5, 0.5, 0.707]
        similarity = cosine_similarity(v1, v2)
        assert abs(similarity - 1.0) < 0.001, f"Expected 1.0, got {similarity}"
        print(f"✅ Identical vectors: {similarity:.3f}")

    def test_similar_vectors(self):
        """Similar vectors should have high similarity"""
        v1 = [0.123, 0.456, 0.789]
        v2 = [0.124, 0.455, 0.790]  # Slightly different
        similarity = cosine_similarity(v1, v2)
        assert similarity > 0.99, f"Expected >0.99, got {similarity}"
        print(f"✅ Similar vectors: {similarity:.3f}")

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0"""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(v1, v2)
        assert abs(similarity) < 0.001, f"Expected ~0, got {similarity}"
        print(f"✅ Orthogonal vectors: {similarity:.3f}")

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1"""
        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]
        similarity = cosine_similarity(v1, v2)
        assert abs(similarity + 1.0) < 0.001, f"Expected -1.0, got {similarity}"
        print(f"✅ Opposite vectors: {similarity:.3f}")

    def test_scaled_vectors(self):
        """Scaled versions of same vector should have similarity 1.0"""
        v1 = [1.0, 2.0, 3.0]
        v2 = [2.0, 4.0, 6.0]  # 2x scaled
        similarity = cosine_similarity(v1, v2)
        assert abs(similarity - 1.0) < 0.001, f"Expected 1.0, got {similarity}"
        print(f"✅ Scaled vectors: {similarity:.3f}")

    def test_empty_vectors(self):
        """Empty vectors should return 0"""
        similarity = cosine_similarity([], [])
        assert similarity == 0.0, f"Expected 0.0, got {similarity}"
        print(f"✅ Empty vectors: {similarity:.3f}")

    def test_one_empty_vector(self):
        """One empty vector should return 0"""
        similarity = cosine_similarity([1.0, 2.0], [])
        assert similarity == 0.0, f"Expected 0.0, got {similarity}"
        print(f"✅ One empty vector: {similarity:.3f}")

    def test_zero_vectors(self):
        """Vectors of all zeros should return 0"""
        similarity = cosine_similarity([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
        assert similarity == 0.0, f"Expected 0.0, got {similarity}"
        print(f"✅ Zero vectors: {similarity:.3f}")

    def test_real_embedding_similarity(self):
        """Test with real-looking embedding vectors"""
        # Simulating Voyage AI embeddings (1024 dims)
        import random
        random.seed(42)

        base = [random.uniform(-1, 1) for _ in range(1024)]

        # Add small noise for similarity
        noise1 = [random.uniform(-0.01, 0.01) for _ in range(1024)]
        v1 = [b + n for b, n in zip(base, noise1)]

        noise2 = [random.uniform(-0.01, 0.01) for _ in range(1024)]
        v2 = [b + n for b, n in zip(base, noise2)]

        similarity = cosine_similarity(v1, v2)
        assert 0.95 < similarity < 1.0, f"Expected 0.95-1.0, got {similarity}"
        print(f"✅ Real embeddings with noise: {similarity:.3f}")

    def test_threshold_scenarios(self):
        """Test threshold scenarios for cache hits"""
        # Scenario 1: Perfect match (cache hit at 0.95)
        v1 = [0.5, 0.5, 0.707]
        v2 = [0.5, 0.5, 0.707]
        sim = cosine_similarity(v1, v2)
        assert sim >= 0.95, f"Should be cache hit"
        print(f"✅ Perfect match threshold: {sim:.3f} >= 0.95")

        # Scenario 2: Close match (cache hit at 0.95)
        v1 = [0.1, 0.2, 0.3, 0.4, 0.5]
        v2 = [0.101, 0.201, 0.301, 0.401, 0.501]
        sim = cosine_similarity(v1, v2)
        assert sim >= 0.95, f"Should be cache hit"
        print(f"✅ Close match threshold: {sim:.3f} >= 0.95")

        # Scenario 3: Different queries (cache miss at 0.95)
        v1 = [1.0, 0.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0, 0.0, 0.0]
        sim = cosine_similarity(v1, v2)
        assert sim < 0.95, f"Should be cache miss, got {sim}"
        print(f"✅ Different queries threshold: {sim:.3f} < 0.95")


def test_all():
    """Run all tests"""
    print("\n" + "="*50)
    print("SEMANTIC CACHE TESTS")
    print("="*50 + "\n")

    test = TestSemanticCache()

    test.test_identical_vectors()
    test.test_similar_vectors()
    test.test_orthogonal_vectors()
    test.test_opposite_vectors()
    test.test_scaled_vectors()
    test.test_empty_vectors()
    test.test_one_empty_vector()
    test.test_zero_vectors()
    test.test_real_embedding_similarity()
    test.test_threshold_scenarios()

    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50 + "\n")


if __name__ == "__main__":
    test_all()
