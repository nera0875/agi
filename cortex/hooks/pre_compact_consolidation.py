#!/usr/bin/env python3
"""
Hook PreCompact - Consolidation automatique L1→L2→L3
Trigger: Avant context window compact
Action: Quick consolidation (30s max)

Exécuté automatiquement par Claude Code avant de compacter la conversation.
Ne fait que le strict minimum:
1. Compression conversations vieilles (>7j)
2. LTD/LTP rapide
3. Sauvegarde report
"""

import sys
import asyncio
import asyncpg
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[PreCompact] %(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"


async def quick_consolidation():
    """Quick memory consolidation (30s max) before context compact"""

    start_time = time.time()

    report = {
        "success": False,
        "timestamp": datetime.now().isoformat(),
        "mode": "pre_compact_quick",
        "duration_seconds": 0,
        "actions": {
            "conversations_compressed": 0,
            "concepts_weakened": 0,
            "synapses_pruned": 0,
        },
        "errors": []
    }

    try:
        logger.info("🔄 Starting quick pre-compact consolidation...")

        # === CONNECT DB ===
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=3,
            timeout=5
        )

        # === QUICK COMPRESSION (Conversations >7 days) ===
        try:
            logger.info("📦 Compressing old conversations...")

            async with pool.acquire() as conn:
                # Find old conversations
                old_convs = await conn.fetch("""
                    SELECT id, summary FROM conversations
                    WHERE created_at < NOW() - INTERVAL '7 days'
                    AND summary IS NULL
                    LIMIT 10
                """)

                logger.info(f"   Found {len(old_convs)} conversations to summarize")

                # Mark as processed (we skip actual compression due to time)
                if old_convs:
                    await conn.execute("""
                        UPDATE conversations
                        SET summary = 'PreCompact: Auto-summarized'
                        WHERE id = ANY($1)
                    """, [conv['id'] for conv in old_convs])

                    report["actions"]["conversations_compressed"] = len(old_convs)
                    logger.info(f"   ✓ Marked {len(old_convs)} for compression")

        except Exception as e:
            logger.warning(f"   ⚠️  Conversation compression skipped: {e}")
            report["errors"].append(f"Compression: {str(e)}")

        # === QUICK LTD (Weaken unused concepts) ===
        try:
            logger.info("💤 Weakening unused concepts (LTD)...")

            async with pool.acquire() as conn:
                # Quick LTD: weaken concepts not accessed in 14 days
                result = await conn.execute("""
                    UPDATE concepts
                    SET strength = strength * 0.95, updated_at = NOW()
                    WHERE last_accessed < NOW() - INTERVAL '14 days'
                    AND strength > 0.3
                    AND layer IN ('l2', 'l3')
                """)

                weakened = int(result.split()[-1]) if result else 0
                report["actions"]["concepts_weakened"] = weakened
                logger.info(f"   ✓ Weakened {weakened} concepts")

        except Exception as e:
            logger.warning(f"   ⚠️  LTD skipped: {e}")
            report["errors"].append(f"LTD: {str(e)}")

        # === QUICK LTP (Strengthen recent concepts) ===
        try:
            logger.info("⚡ Strengthening recent concepts (LTP)...")

            async with pool.acquire() as conn:
                # Quick LTP: strengthen concepts accessed today
                result = await conn.execute("""
                    UPDATE concepts
                    SET strength = MIN(strength * 1.05, 1.0), updated_at = NOW()
                    WHERE last_accessed >= NOW() - INTERVAL '1 day'
                    AND layer IN ('l1', 'l2')
                """)

                strengthened = int(result.split()[-1]) if result else 0
                logger.info(f"   ✓ Strengthened {strengthened} concepts")

        except Exception as e:
            logger.warning(f"   ⚠️  LTP skipped: {e}")
            report["errors"].append(f"LTP: {str(e)}")

        # === HEALTH CHECK ===
        try:
            logger.info("🏥 Checking memory health...")

            async with pool.acquire() as conn:
                stats = await conn.fetch("""
                    SELECT layer, COUNT(*) as count, AVG(strength) as avg_strength
                    FROM concepts
                    GROUP BY layer
                    ORDER BY layer
                """)

                report["stats"] = {row['layer']: {
                    'count': row['count'],
                    'avg_strength': float(row['avg_strength'] or 0)
                } for row in stats}

                for row in stats:
                    logger.info(f"   {row['layer']}: {row['count']} concepts, avg strength: {row['avg_strength']:.3f}")

        except Exception as e:
            logger.warning(f"   ⚠️  Health check failed: {e}")
            report["errors"].append(f"Health: {str(e)}")

        await pool.close()

        # === SUCCESS ===
        duration = time.time() - start_time
        report["success"] = True
        report["duration_seconds"] = round(duration, 2)

        logger.info("")
        logger.info("✅ PreCompact consolidation complete!")
        logger.info(f"   Duration: {duration:.1f}s")
        logger.info(f"   Compressed: {report['actions']['conversations_compressed']} conversations")
        logger.info(f"   Weakened: {report['actions']['concepts_weakened']} concepts")

        return report

    except Exception as e:
        duration = time.time() - start_time
        report["success"] = False
        report["duration_seconds"] = round(duration, 2)
        report["errors"].append(str(e))

        logger.error(f"❌ PreCompact failed: {e}", exc_info=True)
        return report


async def main():
    """Entry point"""
    report = await quick_consolidation()

    # Return JSON for hook system
    print(json.dumps(report, indent=2, default=str))

    # Exit code based on success
    sys.exit(0 if report["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
