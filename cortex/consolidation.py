"""
🌙 CONSOLIDATION NOCTURNE - Comme Sommeil Humain

Processus multi-étapes exécuté chaque nuit (cron 3am):
1. LTD: Weaken unused concepts (strength ↓)
2. LTP: Strengthen accessed concepts (strength ↑)
3. Compression: Résumer vieilles conversations (Claude Haiku)
4. Embeddings: Générer embeddings manquants (Voyage AI)
5. Pattern extraction: Promouvoir L2 → L3
6. Graph optimization: Neo4j cleanup

Objectif: Mémoire performante et économique (pas de bloat)
"""

import asyncio
import asyncpg
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add backend to path
backend_path = str(Path(__file__).parent.parent / 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Database config
DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"


async def consolidate_memory():
    """
    Main consolidation function - Called nightly
    """

    start_time = time.time()

    report = {
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": 0,
        "actions": {},
        "stats_before": {},
        "stats_after": {},
        "errors": [],
        "cost_usd": 0.0
    }

    logger.info("🌙 ============================================")
    logger.info("🌙 NIGHTLY CONSOLIDATION STARTED")
    logger.info("🌙 ============================================")

    try:
        # Connect to database
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=5)

        # === STATS BEFORE ===
        logger.info("📊 Collecting stats before consolidation...")
        async with pool.acquire() as conn:
            stats = await conn.fetch("SELECT * FROM memory_health ORDER BY layer, table_name")
            report["stats_before"] = [dict(row) for row in stats]

            logger.info("Stats before:")
            for row in stats:
                logger.info(f"   {row['layer']}/{row['table_name']}: {row['concept_count']} concepts, avg strength: {row['avg_strength']:.3f}")

        # === ÉTAPE 1: LTD (Long-Term Depression) ===
        logger.info("")
        logger.info("📉 STEP 1: Applying LTD (Long-Term Depression)")
        logger.info("   → Weakening unused concepts (last accessed > 7 days)")

        async with pool.acquire() as conn:
            ltd_results = await conn.fetch("SELECT * FROM apply_ltd(7)")

            total_weakened = 0
            for row in ltd_results:
                count = row['weakened_count']
                total_weakened += count
                logger.info(f"   ✓ {row['table_name']}: {count} concepts weakened")

        report["actions"]["ltd_weakened"] = total_weakened

        # === ÉTAPE 2: COMPRESSION (Old Conversations) ===
        logger.info("")
        logger.info("🗜️  STEP 2: Compressing old raw conversations")
        logger.info("   → Finding conversations > 30 days old")

        compressed_count = 0
        tokens_saved = 0

        # TODO: Implement with Claude Haiku
        # For now, just mark old conversations
        async with pool.acquire() as conn:
            old_convos = await conn.fetch("""
                SELECT id, raw_conversation, summary
                FROM conversation_episodes
                WHERE timestamp < NOW() - INTERVAL '30 days'
                  AND raw_conversation IS NOT NULL
                  AND summary IS NOT NULL
                LIMIT 100
            """)

            for convo in old_convos:
                # Estimate tokens saved
                raw_len = len(convo['raw_conversation'])
                summary_len = len(convo['summary'])
                tokens_saved += (raw_len - summary_len) // 4  # Rough estimate

                # Delete raw, keep summary
                await conn.execute(
                    "UPDATE conversation_episodes SET raw_conversation = NULL WHERE id = $1",
                    convo['id']
                )

                compressed_count += 1

        logger.info(f"   ✓ Compressed {compressed_count} conversations")
        logger.info(f"   ✓ Saved ~{tokens_saved:,} tokens")

        report["actions"]["conversations_compressed"] = compressed_count
        report["actions"]["tokens_saved"] = tokens_saved

        # === ÉTAPE 3: EMBEDDINGS (Generate Missing) ===
        logger.info("")
        logger.info("🔢 STEP 3: Generating missing embeddings (Voyage AI)")

        async with pool.acquire() as conn:
            # Count missing
            missing_agi = await conn.fetchval(
                "SELECT COUNT(*) FROM agi_knowledge WHERE embedding IS NULL AND content IS NOT NULL"
            )
            missing_memory = await conn.fetchval(
                "SELECT COUNT(*) FROM memory_store WHERE embedding IS NULL AND content IS NOT NULL"
            )
            missing_episodes = await conn.fetchval(
                "SELECT COUNT(*) FROM conversation_episodes WHERE embedding IS NULL AND summary IS NOT NULL"
            )

            total_missing = missing_agi + missing_memory + missing_episodes

        logger.info(f"   → Missing embeddings: {total_missing}")
        logger.info(f"      - agi_knowledge: {missing_agi}")
        logger.info(f"      - memory_store: {missing_memory}")
        logger.info(f"      - conversation_episodes: {missing_episodes}")

        if total_missing > 0:
            logger.info("   ⚠️  Embeddings generation skipped (TODO: batch Voyage AI)")
            report["actions"]["embeddings_note"] = f"{total_missing} embeddings need generation"
        else:
            logger.info("   ✓ All embeddings up to date")

        report["actions"]["embeddings_missing"] = total_missing

        # === ÉTAPE 4: Neo4j LTD/LTP ===
        logger.info("")
        logger.info("🧠 STEP 4: Neo4j graph optimization")

        try:
            from neo4j import AsyncGraphDatabase

            driver = AsyncGraphDatabase.driver(
                "bolt://localhost:7687",
                auth=("neo4j", "Voiture789")
            )

            async with driver.session() as session:
                # LTD on all nodes
                result = await session.run("""
                    MATCH (n)
                    WHERE n.strength IS NOT NULL
                      AND (n.last_accessed IS NULL OR n.last_accessed < datetime() - duration('P7D'))
                    SET n.strength = CASE
                        WHEN n.strength * 0.95 < 0.1 THEN 0.1
                        ELSE n.strength * 0.95
                    END
                    RETURN count(n) as weakened
                """)
                record = await result.single()
                neo4j_weakened = record["weakened"] if record else 0

                # Prune weak synapses (strength < 0.2)
                prune_result = await session.run("""
                    MATCH ()-[r:SYNAPSE]->()
                    WHERE r.strength < 0.2
                    DELETE r
                    RETURN count(r) as pruned
                """)
                prune_record = await prune_result.single()
                synapses_pruned = prune_record["pruned"] if prune_record else 0

            await driver.close()

            logger.info(f"   ✓ Neo4j: {neo4j_weakened} nodes weakened")
            logger.info(f"   ✓ Neo4j: {synapses_pruned} weak synapses pruned")

            report["actions"]["neo4j_ltd_weakened"] = neo4j_weakened
            report["actions"]["neo4j_synapses_pruned"] = synapses_pruned

        except Exception as e:
            logger.warning(f"   ⚠️  Neo4j optimization skipped: {e}")
            report["errors"].append(f"Neo4j: {str(e)}")

        # === STATS AFTER ===
        logger.info("")
        logger.info("📊 Collecting stats after consolidation...")

        async with pool.acquire() as conn:
            stats = await conn.fetch("SELECT * FROM memory_health ORDER BY layer, table_name")
            report["stats_after"] = [dict(row) for row in stats]

            logger.info("Stats after:")
            for row in stats:
                logger.info(f"   {row['layer']}/{row['table_name']}: {row['concept_count']} concepts, avg strength: {row['avg_strength']:.3f}")

        # === SAVE REPORT ===
        duration = time.time() - start_time
        report["duration_seconds"] = round(duration, 2)
        report["success"] = True

        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO consolidation_history (
                    conversations_compressed,
                    ltd_weakened,
                    embeddings_generated,
                    duration_seconds,
                    cost_usd,
                    actions_log
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                report["actions"].get("conversations_compressed", 0),
                report["actions"].get("ltd_weakened", 0),
                0,  # embeddings_generated (TODO)
                duration,
                report["cost_usd"],
                json.dumps(report["actions"])
            )

        await pool.close()

        logger.info("")
        logger.info("🌙 ============================================")
        logger.info(f"🌙 CONSOLIDATION COMPLETE in {duration:.2f}s")
        logger.info("🌙 ============================================")

        return report

    except Exception as e:
        report["success"] = False
        report["errors"].append(str(e))
        report["duration_seconds"] = round(time.time() - start_time, 2)

        logger.error(f"❌ Consolidation failed: {e}", exc_info=True)

        return report


async def main():
    """Run consolidation"""
    report = await consolidate_memory()

    print("\n" + "="*60)
    print("CONSOLIDATION REPORT")
    print("="*60)
    print(json.dumps(report, indent=2, default=str))
    print("="*60)

    return report


if __name__ == "__main__":
    asyncio.run(main())
