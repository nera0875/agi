"""
🔍 AUDIT MCP AGI-TOOLS

Test tous les tools MCP pour identifier bugs et erreurs
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

# Import MCP functions
from agi_tools_mcp import (
    think,
    memory_search, memory_store, memory_stats,
    pg_query, pg_execute, pg_tables, pg_schema,
    bootstrap_agi,
    init_db, db_pool
)

DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"


async def test_think():
    """Test think() tool"""
    print("\n" + "="*60)
    print("TEST: think()")
    print("="*60)

    try:
        result = await think("test bootstrap")
        print(f"✅ SUCCESS")
        print(f"   Keys: {list(result.keys())}")
        print(f"   Understanding: {result.get('understanding', 'N/A')[:100]}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_memory():
    """Test memory tools"""
    print("\n" + "="*60)
    print("TEST: memory()")
    print("="*60)

    # Test stats
    try:
        stats = await memory_stats()
        print(f"✅ memory_stats() SUCCESS")
        print(f"   Total: {stats.get('total_memories', 0)}")
    except Exception as e:
        print(f"❌ memory_stats() FAIL: {e}")
        return False

    # Test search
    try:
        results = await memory_search("test", limit=3)
        print(f"✅ memory_search() SUCCESS")
        print(f"   Results: {results.get('count', 0)}")
    except Exception as e:
        print(f"❌ memory_search() FAIL: {e}")
        return False

    # Test store
    try:
        result = await memory_store(
            "Test memory from audit",
            "test",
            ["audit", "test"],
            "default"
        )
        print(f"✅ memory_store() SUCCESS")
        print(f"   ID: {result.get('memory_id', 'N/A')}")
    except Exception as e:
        print(f"❌ memory_store() FAIL: {e}")
        return False

    return True


async def test_database():
    """Test database tools"""
    print("\n" + "="*60)
    print("TEST: database()")
    print("="*60)

    # Test tables
    try:
        tables = await pg_tables()
        print(f"✅ pg_tables() SUCCESS")
        print(f"   Tables: {len(tables)}")
    except Exception as e:
        print(f"❌ pg_tables() FAIL: {e}")
        return False

    # Test query
    try:
        result = await pg_query("SELECT COUNT(*) as count FROM agi_knowledge")
        print(f"✅ pg_query() SUCCESS")
        print(f"   Count: {result[0]['count'] if result else 0}")
    except Exception as e:
        print(f"❌ pg_query() FAIL: {e}")
        return False

    # Test schema
    try:
        schema = await pg_schema("agi_knowledge")
        print(f"✅ pg_schema() SUCCESS")
        print(f"   Columns: {len(schema.get('columns', []))}")
    except Exception as e:
        print(f"❌ pg_schema() FAIL: {e}")
        return False

    return True


async def test_bootstrap():
    """Test bootstrap_agi()"""
    print("\n" + "="*60)
    print("TEST: bootstrap_agi()")
    print("="*60)

    try:
        result = await bootstrap_agi()
        print(f"✅ SUCCESS")
        print(f"   Ready: {result.get('ready', False)}")
        print(f"   Session: {result.get('session', {}).get('session_id', 'N/A')}")
        print(f"   Rules: {len(result.get('reinforced_rules', []))}")
        print(f"   Tasks: {len(result.get('running_tasks', []))}")
        return True
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""

    print("🔍 AUDIT MCP AGI-TOOLS")
    print("="*60)

    # Initialize DB
    await init_db()

    results = {
        "think": await test_think(),
        "memory": await test_memory(),
        "database": await test_database(),
        "bootstrap": await test_bootstrap()
    }

    # Summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)

    total = len(results)
    passed = sum(results.values())
    failed = total - passed

    for tool, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {tool}()")

    print("-"*60)
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/total*100:.1f}%")
    print("="*60)

    if failed > 0:
        print("\n⚠️  ISSUES FOUND - Needs fixing!")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
