#!/usr/bin/env python3
"""
Neural Consolidation Job - Nightly maintenance

Exécuté chaque nuit à 3h du matin (comme sommeil REM humain)

Processus:
1. LTD - Decay synapses non utilisées depuis 7 jours (strength *= 0.95)
2. Pruning - Supprimer synapses < 0.1
3. Consolidation - Fusionner concepts similaires co-activés
4. Metrics - Tracking santé système

Comme cerveau humain pendant sommeil:
- Consolidation mémoires importantes
- Suppression connexions inutiles
- Optimisation structure neurale
- Économie de ressources
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from redis import asyncio as aioredis

from services.neural_memory import NeuralMemory
from services.database import db
from services.redis_client import redis_client
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def run_consolidation():
    """
    Consolidation nocturne du système neural

    Processus inspiré du sommeil humain (REM sleep):
    - LTD: Affaiblir connexions inutilisées
    - Pruning: Supprimer connexions mortes
    - Consolidation: Fusionner patterns similaires
    - Renforcement: Booster connexions importantes
    """

    logger.info("=" * 80)
    logger.info("🌙 NEURAL CONSOLIDATION - Nightly Maintenance")
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # Initialize connections
    db_pool = await db.connect()
    redis = await redis_client.get_client()

    neural = NeuralMemory(
        db_pool=db_pool,
        redis_client=redis
    )

    try:
        # PHASE 1 - Metrics BEFORE
        logger.info("\n📊 Metrics BEFORE consolidation:")
        metrics_before = await neural.get_neural_metrics()
        logger.info(f"  Nodes: {metrics_before['graph']['total_nodes']}")
        logger.info(f"  Synapses: {metrics_before['graph']['total_synapses']}")
        logger.info(f"  Density: {metrics_before['graph']['density']:.6f}")
        logger.info(f"  Avg strength: {metrics_before['synapses']['avg_strength']:.3f}")
        logger.info(f"  Avg use count: {metrics_before['synapses']['avg_use_count']:.1f}")

        # PHASE 2 - LTD (Long-Term Depression)
        logger.info("\n📉 PHASE 1: LTD - Weakening unused synapses...")
        decayed = await neural.decay_synapses(
            days_threshold=7,      # 7 jours sans usage
            decay_factor=0.95      # -5% force par semaine
        )
        logger.info(f"  ✅ Decayed {decayed} synapses")

        # PHASE 3 - Synaptic Pruning
        logger.info("\n✂️  PHASE 2: PRUNING - Removing weak synapses...")
        pruned = await neural.prune_weak_synapses(
            strength_threshold=0.1  # Supprimer si force < 10%
        )
        logger.info(f"  ✅ Pruned {pruned} weak synapses")

        # PHASE 4 - Consolidation
        logger.info("\n🔗 PHASE 3: CONSOLIDATION - Merging similar concepts...")
        consolidated = await neural.consolidate_concepts(
            similarity_threshold=0.95,  # 95% similarité
            min_use_count=10           # Min 10 co-activations
        )
        logger.info(f"  ✅ Consolidated {consolidated} concept pairs")

        # PHASE 5 - Metrics AFTER
        logger.info("\n📊 Metrics AFTER consolidation:")
        metrics_after = await neural.get_neural_metrics()
        logger.info(f"  Nodes: {metrics_after['graph']['total_nodes']}")
        logger.info(f"  Synapses: {metrics_after['graph']['total_synapses']} (Δ {metrics_after['graph']['total_synapses'] - metrics_before['graph']['total_synapses']})")
        logger.info(f"  Density: {metrics_after['graph']['density']:.6f} (Δ {metrics_after['graph']['density'] - metrics_before['graph']['density']:.6f})")
        logger.info(f"  Avg strength: {metrics_after['synapses']['avg_strength']:.3f} (Δ {metrics_after['synapses']['avg_strength'] - metrics_before['synapses']['avg_strength']:.3f})")

        # PHASE 6 - Top concepts
        logger.info("\n🏆 TOP 10 Most Activated Concepts:")
        for i, concept in enumerate(metrics_after['top_concepts'][:10], 1):
            logger.info(f"  {i}. [{concept['access_count']:4d}x] {concept['content']}")

        # PHASE 7 - Store consolidation metrics
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO memory_metrics (
                    metric_type,
                    metric_data,
                    created_at
                ) VALUES ($1, $2, NOW())
            """,
                "neural_consolidation",
                {
                    "before": metrics_before,
                    "after": metrics_after,
                    "operations": {
                        "decayed": decayed,
                        "pruned": pruned,
                        "consolidated": consolidated
                    }
                }
            )

        logger.info("\n" + "=" * 80)
        logger.info("✅ CONSOLIDATION COMPLETE")
        logger.info(f"Finished at: {datetime.now().isoformat()}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Consolidation failed: {e}", exc_info=True)
        raise

    finally:
        await neural.close()
        await db_pool.close()
        await redis.close()


async def main():
    """Entry point"""
    await run_consolidation()


if __name__ == "__main__":
    asyncio.run(main())
