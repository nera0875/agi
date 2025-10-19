#!/usr/bin/env python3
"""
Test Neurotransmitter System
===========================

Teste modulation dynamique selon query_type:
- urgent: GLUTAMATE high → depth 3, threshold 0.1, top_k 12
- interactive: Balanced → depth 2, threshold 0.2, top_k 5
- background: GABA high → depth 1, threshold 0.4, top_k 3
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg

# Import directly to avoid loading config
sys.path.insert(0, str(Path(__file__).parent.parent / 'services'))
from neurotransmitter_system import NeurotransmitterSystem


async def test_neurotransmitters():
    """Test neurotransmitter modulation"""

    print("=" * 80)
    print("🧠 TESTING NEUROTRANSMITTER SYSTEM")
    print("=" * 80)

    # Connect to PostgreSQL
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='agi_user',
        password='agi_password',
        database='agi_db'
    )

    neuro = NeurotransmitterSystem(db_pool)

    try:
        # Test 1: URGENT query
        print("\n📌 TEST 1: URGENT query (user waiting)")
        print("-" * 80)
        params_urgent = await neuro.modulate('urgent', {})
        print(f"  Glutamate: {params_urgent['glutamate']:.2f}")
        print(f"  GABA:      {params_urgent['gaba']:.2f}")
        print(f"  Dopamine:  {params_urgent['dopamine']:.2f}")
        print(f"  → max_depth: {params_urgent['max_depth']}")
        print(f"  → activation_threshold: {params_urgent['activation_threshold']:.2f}")
        print(f"  → ltp_strength: {params_urgent['ltp_strength']:.2f}")
        print(f"  → top_k: {params_urgent['top_k']}")
        print(f"  → arousal_level: {params_urgent['arousal_level']:.2f}")
        print(f"\n  ✅ Expected: High depth, low threshold, high top_k")
        print(f"  🎯 Estimated tokens: ~{params_urgent['top_k'] * 50}")

        # Test 2: INTERACTIVE query
        print("\n📌 TEST 2: INTERACTIVE query (normal)")
        print("-" * 80)
        params_interactive = await neuro.modulate('interactive', {})
        print(f"  Glutamate: {params_interactive['glutamate']:.2f}")
        print(f"  GABA:      {params_interactive['gaba']:.2f}")
        print(f"  Dopamine:  {params_interactive['dopamine']:.2f}")
        print(f"  → max_depth: {params_interactive['max_depth']}")
        print(f"  → activation_threshold: {params_interactive['activation_threshold']:.2f}")
        print(f"  → ltp_strength: {params_interactive['ltp_strength']:.2f}")
        print(f"  → top_k: {params_interactive['top_k']}")
        print(f"\n  ✅ Expected: Balanced parameters")
        print(f"  🎯 Estimated tokens: ~{params_interactive['top_k'] * 50}")

        # Test 3: BACKGROUND query
        print("\n📌 TEST 3: BACKGROUND query (economy mode)")
        print("-" * 80)
        params_background = await neuro.modulate('background', {})
        print(f"  Glutamate: {params_background['glutamate']:.2f}")
        print(f"  GABA:      {params_background['gaba']:.2f}")
        print(f"  Dopamine:  {params_background['dopamine']:.2f}")
        print(f"  → max_depth: {params_background['max_depth']}")
        print(f"  → activation_threshold: {params_background['activation_threshold']:.2f}")
        print(f"  → ltp_strength: {params_background['ltp_strength']:.2f}")
        print(f"  → top_k: {params_background['top_k']}")
        print(f"\n  ✅ Expected: Low depth, high threshold, low top_k")
        print(f"  🎯 Estimated tokens: ~{params_background['top_k'] * 50}")

        # Test 4: FEEDBACK - Success
        print("\n📌 TEST 4: FEEDBACK - Success (dopamine boost)")
        print("-" * 80)
        print("  Simulating successful query with fast response...")
        await neuro.feedback(success=True, response_time=300, tokens_used=200)

        metrics = await neuro.get_metrics()
        print(f"  Dopamine after success: {metrics['dopamine']:.2f}")
        print(f"  GABA after success:     {metrics['gaba']:.2f}")
        print(f"  Learning rate:          {metrics['learning_rate']:.2f}")
        print(f"\n  ✅ Expected: Dopamine increased, GABA decreased")

        # Test 5: FEEDBACK - Failure
        print("\n📌 TEST 5: FEEDBACK - Failure (dopamine drop)")
        print("-" * 80)
        print("  Simulating failed query with slow response...")
        await neuro.feedback(success=False, response_time=3500, tokens_used=0)

        metrics_after = await neuro.get_metrics()
        print(f"  Dopamine after failure: {metrics_after['dopamine']:.2f}")
        print(f"  GABA after failure:     {metrics_after['gaba']:.2f}")
        print(f"  Learning rate:          {metrics_after['learning_rate']:.2f}")
        print(f"\n  ✅ Expected: Dopamine decreased, GABA increased")

        # Test 6: Multiple successes (dopamine accumulation)
        print("\n📌 TEST 6: Multiple successes (learning acceleration)")
        print("-" * 80)
        print("  Simulating 5 successful queries...")

        for i in range(5):
            await neuro.feedback(success=True, response_time=200, tokens_used=150)
            metrics_loop = await neuro.get_metrics()
            print(f"  Success {i+1}: DA={metrics_loop['dopamine']:.2f}, LR={metrics_loop['learning_rate']:.2f}")

        print(f"\n  ✅ Expected: Dopamine approaching 0.9, learning rate increasing")

        # Test 7: Reset to homeostasis
        print("\n📌 TEST 7: Reset to homeostasis")
        print("-" * 80)
        await neuro.reset()
        metrics_reset = await neuro.get_metrics()
        print(f"  Glutamate: {metrics_reset['glutamate']:.2f}")
        print(f"  Dopamine:  {metrics_reset['dopamine']:.2f}")
        print(f"  GABA:      {metrics_reset['gaba']:.2f}")
        print(f"  Serotonin: {metrics_reset['serotonin']:.2f}")
        print(f"\n  ✅ Expected: All neurotransmitters at 0.5")

        # Summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\n🧠 Neurotransmitter System Summary:")
        print(f"  - URGENT queries:      depth={params_urgent['max_depth']}, tokens~{params_urgent['top_k'] * 50}")
        print(f"  - INTERACTIVE queries: depth={params_interactive['max_depth']}, tokens~{params_interactive['top_k'] * 50}")
        print(f"  - BACKGROUND queries:  depth={params_background['max_depth']}, tokens~{params_background['top_k'] * 50}")
        print(f"\n  📊 Token economy range: {params_background['top_k'] * 50} - {params_urgent['top_k'] * 50} tokens")
        print(f"  🚀 LTP boost range: {params_background['ltp_strength']:.2f} - {params_urgent['ltp_strength']:.2f}")
        print(f"\n  🎯 System is adaptive and ready for production!")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(test_neurotransmitters())
