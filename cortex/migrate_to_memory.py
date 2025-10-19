#!/usr/bin/env python3
"""
Migration: system_rules + system_bootstrap → memory_store
Utilise ton système memory avec Voyage AI embeddings
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import asyncpg
from langchain_voyageai import VoyageAIEmbeddings
from services.memory_service import MemoryService
from services.database import db
from services.redis_client import redis_client

async def migrate():
    print("🚀 Migration vers memory_store avec embeddings...")

    # Connect
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='agi_user',
        password='agi_password',
        database='agi_db'
    )

    # Initialize memory service
    db_pool = await db.connect()
    redis = await redis_client.get_client()
    memory_service = MemoryService(db_pool=db_pool, redis_client=redis)

    print("✅ Memory service initialized")

    # ========================================
    # MIGRATE SYSTEM_RULES
    # ========================================
    print("\n📋 Migrating system_rules...")

    async with pool.acquire() as conn:
        rules = await conn.fetch("""
            SELECT rule_type, rule_content, priority
            FROM system_rules
            WHERE active = true
        """)

        for i, rule in enumerate(rules, 1):
            content = f"[RULE:{rule['rule_type']}] {rule['rule_content']}"

            # Store with metadata
            memory_id = await memory_service.add_memory(
                content=content,
                metadata={
                    "rule_type": rule['rule_type'],
                    "priority": rule['priority'],
                    "original_table": "system_rules",
                    "tags": ["system-rule", rule['rule_type'], f"priority-{rule['priority']}"]
                },
                source_type="system_rule",
                user_id="agi-system"
            )

            print(f"  [{i}/{len(rules)}] ✅ {content[:70]}... → {memory_id}")

    print(f"✅ Migrated {len(rules)} system rules")

    # ========================================
    # MIGRATE SYSTEM_BOOTSTRAP
    # ========================================
    print("\n📋 Migrating system_bootstrap...")

    async with pool.acquire() as conn:
        instructions = await conn.fetch("""
            SELECT instruction_type, instruction_content, priority, tags
            FROM system_bootstrap
            WHERE active = true
        """)

        for i, instr in enumerate(instructions, 1):
            content = f"[BOOTSTRAP:{instr['instruction_type']}] {instr['instruction_content']}"

            # Store with metadata
            memory_id = await memory_service.add_memory(
                content=content,
                metadata={
                    "instruction_type": instr['instruction_type'],
                    "priority": instr['priority'],
                    "original_table": "system_bootstrap",
                    "tags": instr['tags'] + ["bootstrap", instr['instruction_type']]
                },
                source_type="bootstrap_instruction",
                user_id="agi-system"
            )

            print(f"  [{i}/{len(instructions)}] ✅ {content[:70]}... → {memory_id}")

    print(f"✅ Migrated {len(instructions)} bootstrap instructions")

    # ========================================
    # VERIFY MIGRATION
    # ========================================
    print("\n🔍 Verifying migration...")

    # Test semantic search
    test_query = "workflow rules"
    results = await memory_service.hybrid_search(
        query=test_query,
        top_k=3,
        user_id="agi-system"
    )

    print(f"\n🔎 Test search: '{test_query}'")
    for i, doc in enumerate(results, 1):
        score = doc.metadata.get("rrf_score", 0)
        print(f"  {i}. [score:{score:.3f}] {doc.page_content[:80]}...")

    # Stats
    async with pool.acquire() as conn:
        total = await conn.fetchval("""
            SELECT COUNT(*) FROM memory_store
            WHERE source_type IN ('system_rule', 'bootstrap_instruction')
        """)

        print(f"\n📊 Total memories stored: {total}")

    await pool.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
