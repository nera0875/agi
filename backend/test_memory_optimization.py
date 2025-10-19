"""
Test script for memory optimization features:
- Deduplication
- Quality scoring
- Cleanup
- Graph expansion
"""

import asyncio
import asyncpg
from redis import asyncio as aioredis
from services.memory_service import MemoryService

async def main():
    # Connect to DB and Redis
    db_pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="agi_user",
        password="agi_password",
        database="agi_db",
        min_size=5,
        max_size=20
    )

    redis = await aioredis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=False
    )

    memory_service = MemoryService(db_pool, redis)

    print("=" * 60)
    print("MEMORY OPTIMIZATION TESTS")
    print("=" * 60)

    # Test 1: Deduplication
    print("\n[TEST 1] Deduplication")
    content = "This is a test memory for deduplication checking."

    id1 = await memory_service.add_memory(
        content=content,
        source_type="test",
        metadata={"tags": ["test", "dedup"]},
        skip_validation=True
    )
    print(f"  First store: {id1}")

    id2 = await memory_service.add_memory(
        content=content,
        source_type="test",
        metadata={"tags": ["test", "dedup"]},
        skip_validation=True
    )
    print(f"  Second store (duplicate): {id2}")
    print(f"  ✓ Deduplication: {'PASS' if id1 == id2 else 'FAIL'}")

    # Test 2: Quality scoring
    print("\n[TEST 2] Quality Scoring")
    print("  Calculating quality scores for all memories...")
    updated_count = await memory_service.update_quality_scores()
    print(f"  ✓ Updated {updated_count} memories")

    # Test 3: Cleanup test data
    print("\n[TEST 3] Cleanup Test Data")
    cleaned = await memory_service.cleanup_test_data()
    print(f"  ✓ Cleaned {cleaned} test entries")

    # Test 4: Stats with quality distribution
    print("\n[TEST 4] Memory Stats")
    stats = await memory_service.get_stats()
    print(f"  Total memories: {stats['total_memories']}")
    print(f"  By type: {stats['by_source_type']}")
    if "quality_distribution" in stats:
        print(f"  Quality distribution: {stats['quality_distribution']}")
    print("  ✓ Stats retrieved")

    # Test 5: Graph expansion (if relations exist)
    print("\n[TEST 5] Graph Expansion")
    results = await memory_service.hybrid_search(
        query="AGI memory system",
        top_k=3,
        expand_graph=False
    )
    print(f"  Without graph: {len(results)} results")

    results_expanded = await memory_service.hybrid_search(
        query="AGI memory system",
        top_k=3,
        expand_graph=True,
        graph_depth=1
    )
    print(f"  With graph (depth=1): {len(results_expanded)} results")
    print("  ✓ Graph expansion tested")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED ✓")
    print("=" * 60)

    await db_pool.close()
    await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
