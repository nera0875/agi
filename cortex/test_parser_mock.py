#!/usr/bin/env python3
"""
Test Parser with Mock Data
Validates: Parser → Auto-store → Metrics increase
"""

import asyncio
import asyncpg
from uuid import uuid4
import json

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}

# Import parser from task_worker
import sys
sys.path.insert(0, '/home/pilote/projet/agi')
from cortex.task_worker import auto_store_patterns


async def test_parser():
    """Test parser with mock research output"""

    print("="*60)
    print("TEST PARSER + AUTO-STORE (MOCK DATA)")
    print("="*60)

    # Measure BEFORE
    conn = await asyncpg.connect(**DB_CONFIG)
    patterns_before = await conn.fetchval(
        "SELECT COUNT(*) FROM memory_store WHERE source_type = 'architectural_pattern'"
    )
    await conn.close()

    print(f"\n[1] Patterns BEFORE: {patterns_before}")

    # Mock research output (realistic Claude response)
    mock_output = """
# Vector Search Optimization Techniques

Here are the key patterns and techniques for optimizing vector search:

**1. HNSW (Hierarchical Navigable Small World)**
- Graph-based approximate nearest neighbor search
- Excellent recall with low latency
- Used by Pinecone, Weaviate, Qdrant

**2. Product Quantization (PQ)**
- Compresses vectors to reduce memory footprint
- 8-32x compression with minimal accuracy loss
- Essential for billion-scale deployments

**3. Hybrid Search (Vector + BM25)**
- Combine semantic similarity with keyword matching
- RRF (Reciprocal Rank Fusion) for merging results
- Best recall for diverse queries

**4. IVF (Inverted File Index)**
- Partitions vector space into clusters
- Reduces search space significantly
- Trade-off: slight recall loss for speed

**5. DiskANN**
- Disk-based ANN for massive datasets
- Uses graph-based index with SSD-optimized layout
- Enables trillion-scale vector search

Sources:
- Pinecone blog: https://www.pinecone.io/learn/vector-search/
- Weaviate docs: https://weaviate.io/
- Research papers on HNSW and IVF-PQ
"""

    print(f"\n[2] Parsing mock output ({len(mock_output)} chars)...")

    # Call parser
    query = "Vector search optimization"
    patterns_stored = await auto_store_patterns(mock_output, query)

    print(f"  ✓ Patterns stored: {patterns_stored}")

    # Measure AFTER
    conn = await asyncpg.connect(**DB_CONFIG)
    patterns_after = await conn.fetchval(
        "SELECT COUNT(*) FROM memory_store WHERE source_type = 'architectural_pattern'"
    )

    # Get latest patterns
    latest = await conn.fetch(
        """
        SELECT LEFT(content, 100) as preview, metadata->>'auto_parsed' as auto_parsed
        FROM memory_store
        WHERE source_type = 'architectural_pattern'
        ORDER BY created_at DESC
        LIMIT 5
        """
    )

    await conn.close()

    print(f"\n[3] Patterns AFTER: {patterns_after}")
    print(f"  Delta: +{patterns_after - patterns_before}")

    print(f"\n[4] Latest patterns auto-stored:")
    for i, row in enumerate(latest, 1):
        auto = "✓" if row['auto_parsed'] == 'true' else ""
        print(f"  {i}. {row['preview'][:80]}... {auto}")

    print("\n" + "="*60)

    if patterns_after > patterns_before:
        print("✅ TEST PASSED - Parser + Auto-store working!")
    else:
        print("❌ TEST FAILED - No patterns stored")

    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_parser())
