#!/usr/bin/env python3
"""
L1 Observer Node: decide_storage_layer

Decides where to store each event based on importance and classification.

Storage Rules:
- importance 0-2 → "skip" (trivial)
- importance 3-5 → "L1" (working memory only, 24h TTL)
- importance 6-7 → "L2" (short-term, batch processing)
- importance 8-10 → "L3" (long-term, immediate storage)

Special Rules:
- classified_type="trivial" → always "skip"
- classified_type="decision" AND importance >= 7 → "L3"
- classified_type="research" → "L2" (for batch analysis)

Model: Pure Logic (no API calls)
Cost: $0
Latency: ~5ms
"""

import time
from typing import Dict
from datetime import datetime

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from backend.agents.l1_observer.state import L1State


# ═══════════════════════════════════════════════════════
# DECISION LOGIC
# ═══════════════════════════════════════════════════════

def decide_storage_layer(state: L1State) -> Dict:
    """
    Decide storage layer based on importance and classification.

    Updates state with:
    - storage_layer (skip | L1 | L2 | L3)
    - storage_reasoning
    - timings["decide_storage_layer"]

    Args:
        state: Current L1State with importance and classified_type

    Returns:
        Updated state dict with storage decision
    """
    start_time = time.time()

    # Extract decision factors
    importance = state.get("importance", 0)
    classified_type = state.get("classified_type", "trivial")

    # Initialize storage layer and reasoning
    storage_layer = "skip"
    storage_reasoning = ""

    # ═══════════════════════════════════════════════════════
    # SPECIAL RULES (overrides base logic)
    # ═══════════════════════════════════════════════════════

    # Rule 1: Always skip if classified as trivial
    if classified_type == "trivial":
        storage_layer = "skip"
        storage_reasoning = f"Classified as trivial, skipping storage"

    # Rule 2: Decision events with importance >= 7 go to L3
    elif classified_type == "decision" and importance >= 7:
        storage_layer = "L3"
        storage_reasoning = (
            f"Architectural/design decision with high importance ({importance}/10) "
            f"- immediate long-term storage for pattern recognition"
        )

    # Rule 3: Research events go to L2 for batch analysis
    elif classified_type == "research":
        storage_layer = "L2"
        storage_reasoning = (
            f"Research event (importance {importance}/10) - batch processing "
            f"for knowledge synthesis"
        )

    # ═══════════════════════════════════════════════════════
    # BASE LOGIC (importance-based routing)
    # ═══════════════════════════════════════════════════════

    elif importance < 3:
        storage_layer = "skip"
        storage_reasoning = (
            f"Low importance ({importance}/10) - trivial event, "
            f"not worth storing"
        )

    elif importance <= 5:
        storage_layer = "L1"
        storage_reasoning = (
            f"Low importance ({importance}/10) - working memory only "
            f"with 24h TTL (quick access, auto-purge)"
        )

    elif importance <= 7:
        storage_layer = "L2"
        storage_reasoning = (
            f"Medium importance ({importance}/10) - short-term storage "
            f"for batch processing and consolidation"
        )

    else:  # importance >= 8
        storage_layer = "L3"
        storage_reasoning = (
            f"High importance ({importance}/10) - long-term storage "
            f"with immediate consolidation for pattern learning"
        )

    # Calculate timing
    duration_ms = int((time.time() - start_time) * 1000)

    # Update timings
    if "timings" not in state:
        state["timings"] = {}
    state["timings"]["decide_storage_layer"] = duration_ms

    # Return updates
    return {
        "storage_layer": storage_layer,
        "storage_reasoning": storage_reasoning,
    }


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_decide_storage_layer():
    """Test storage layer decision logic"""

    print("🧠 Testing decide_storage_layer Node")
    print("=" * 60)

    from backend.agents.l1_observer.state import create_initial_state

    # Test cases covering all scenarios
    test_cases = [
        {
            "name": "Trivial Event (Always Skip)",
            "importance": 2,
            "classified_type": "trivial",
            "expected_layer": "skip"
        },
        {
            "name": "Low Importance (L1)",
            "importance": 4,
            "classified_type": "code_edit",
            "expected_layer": "L1"
        },
        {
            "name": "Medium Importance (L2)",
            "importance": 6,
            "classified_type": "bug_fix",
            "expected_layer": "L2"
        },
        {
            "name": "High Importance (L3)",
            "importance": 8,
            "classified_type": "new_feature",
            "expected_layer": "L3"
        },
        {
            "name": "Critical Decision (L3)",
            "importance": 7,
            "classified_type": "decision",
            "expected_layer": "L3"
        },
        {
            "name": "Research Event (L2)",
            "importance": 5,
            "classified_type": "research",
            "expected_layer": "L2"
        },
        {
            "name": "Trivial Overrides High Importance (Skip)",
            "importance": 9,
            "classified_type": "trivial",
            "expected_layer": "skip"
        },
        {
            "name": "Very Low Decision (L2 Base Logic)",
            "importance": 6,
            "classified_type": "decision",
            "expected_layer": "L2"
        },
    ]

    print("\nTesting all scenarios:")
    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        # Create state
        state = create_initial_state(
            event_type="Test",
            session_id="test-session",
            file_path="/home/pilote/projet/agi/test.py",
            tool_name="Test"
        )

        # Add classification and importance
        state["importance"] = test_case["importance"]
        state["classified_type"] = test_case["classified_type"]

        # Run decision
        updates = decide_storage_layer(state)
        state.update(updates)

        # Check result
        storage_layer = state["storage_layer"]
        expected = test_case["expected_layer"]
        passed_test = storage_layer == expected

        status = "✅" if passed_test else "❌"
        passed += 1 if passed_test else 0
        failed += 0 if passed_test else 1

        print(f"\n{i}️⃣ {test_case['name']}")
        print(f"   Input: importance={test_case['importance']}, "
              f"type={test_case['classified_type']}")
        print(f"   Result: {status} {storage_layer}")
        print(f"   Expected: {expected}")
        print(f"   Reasoning: {state['storage_reasoning']}")
        print(f"   Timing: {state['timings']['decide_storage_layer']}ms")

    print("\n" + "=" * 60)
    print(f"✅ TESTS COMPLETED: {passed} passed, {failed} failed")
    if failed == 0:
        print("   All decision rules working correctly!")


if __name__ == "__main__":
    test_decide_storage_layer()
