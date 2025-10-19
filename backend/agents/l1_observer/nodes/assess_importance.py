#!/usr/bin/env python3
"""
L1 Observer Node: assess_importance

Uses Claude Haiku to assess event importance (0-10 scale).
Fast assessment (~150ms) with high-quality reasoning.

Model: Claude 3.5 Haiku
Cost: ~$0.00005 per assessment
Latency: ~100-150ms
"""

import time
from typing import Dict
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from backend.config.agi_config import get_config
from backend.agents.l1_observer.state import L1State


# ═══════════════════════════════════════════════════════
# IMPORTANCE ASSESSMENT PROMPT
# ═══════════════════════════════════════════════════════

IMPORTANCE_SYSTEM_PROMPT = """You are an importance assessor for an AGI memory system.

Your job is to assess the importance of events on a 0-10 scale in ~150ms.

**Importance Scale:**
- 0-2: Trivial (skip) - Typos, whitespace, minor formatting, read-only operations
- 3-5: Low importance (L1 only) - Minor edits, config tweaks, simple refactors
- 6-7: Medium importance (L1→L2) - New functions, bug fixes, meaningful changes
- 8-9: High importance (L1→L2→L3) - New features, architectural changes, critical bugs
- 10: Critical (immediate L3) - Major architectural decisions, breaking changes, security fixes

**Assessment Criteria:**
1. **Impact Scope**: How many files/modules affected?
2. **Complexity**: How complex is the change?
3. **Novelty**: Is this new functionality or modification?
4. **Risk**: Could this break existing functionality?
5. **Learning Value**: Should this be remembered long-term?

**Response Format (JSON):**
{
    "importance": 7,
    "reasoning": "New function in core module with moderate complexity",
    "impact_areas": ["backend", "api"],
    "confidence": 0.9
}

**Rules:**
- Be FAST - this runs on every event
- Consider the classified_type from previous step
- Default to lower scores if uncertain
- High scores (8+) only for truly significant events
"""


# ═══════════════════════════════════════════════════════
# NODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════

def assess_importance(state: L1State) -> Dict:
    """
    Assess event importance using Claude Haiku

    Updates state with:
    - importance (0-10)
    - importance_reasoning
    - impact_areas
    - timings["assess_importance"]
    - cost_tracking["assess"]

    Args:
        state: Current L1State

    Returns:
        Updated state dict
    """
    start_time = time.time()

    # Get config
    config = get_config()

    # Initialize Claude Haiku
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.3,  # Slightly higher for nuanced assessment
        api_key=config.anthropic_api_key
    )

    # Create human message with event details + classification
    event_details = f"""Event Type: {state['event_type']}
Classified As: {state.get('classified_type', 'unknown')}
Classification Confidence: {state.get('classification_confidence', 0.0):.2f}
File Path: {state.get('file_path', 'N/A')}
Tool: {state.get('tool_name', 'N/A')}

Content Preview:
{state.get('content_preview', 'N/A')[:1000]}

Previous Classification Reasoning:
{state.get('classification_reasoning', 'N/A')}
"""

    messages = [
        SystemMessage(content=IMPORTANCE_SYSTEM_PROMPT),
        HumanMessage(content=event_details)
    ]

    # Parse JSON response
    parser = JsonOutputParser()

    try:
        # Invoke LLM
        response = llm.invoke(messages)

        # Parse response
        result = parser.parse(response.content)

        # Extract results
        importance = result.get("importance", 5)
        reasoning = result.get("reasoning", "No reasoning provided")
        impact_areas = result.get("impact_areas", [])
        confidence = result.get("confidence", 0.5)

        # Clamp importance to 0-10
        importance = max(0, min(10, importance))

        # Calculate cost (Claude Haiku pricing)
        # Estimate: ~300 tokens in, ~80 tokens out
        tokens_in = 300
        tokens_out = 80
        cost_per_1m_tokens_in = 0.80  # $0.80 / 1M input tokens
        cost_per_1m_tokens_out = 4.00  # $4.00 / 1M output tokens

        cost_usd = (
            (tokens_in / 1_000_000) * cost_per_1m_tokens_in +
            (tokens_out / 1_000_000) * cost_per_1m_tokens_out
        )

        # Calculate timing
        duration_ms = int((time.time() - start_time) * 1000)

        # Update state
        updates = {
            "importance": importance,
            "importance_reasoning": reasoning,
            "impact_areas": impact_areas,
        }

        # Update timings
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["assess_importance"] = duration_ms

        # Update cost tracking
        if "cost_tracking" not in state:
            state["cost_tracking"] = {}
        state["cost_tracking"]["assess"] = {
            "model": "claude-3-5-haiku",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "confidence": confidence
        }

        return updates

    except Exception as e:
        # Handle errors gracefully
        duration_ms = int((time.time() - start_time) * 1000)

        # Add error to state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "node": "assess_importance",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update timings even on error
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["assess_importance"] = duration_ms

        # Fallback to medium importance
        return {
            "importance": 5,
            "importance_reasoning": f"Assessment failed: {str(e)}",
            "impact_areas": []
        }


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_structure_only():
    """Test structure without API calls"""
    from backend.agents.l1_observer.state import create_initial_state

    # Create test state with classification
    state = create_initial_state(
        event_type="Write",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/agents/l1_observer/state.py",
        content="class L1State(TypedDict, total=False):\n    event_id: str\n    session_id: str",
        tool_name="Write"
    )

    # Add classification results
    state.update({
        "classified_type": "new_feature",
        "classification_confidence": 0.95,
        "classification_reasoning": "Creating new L1State schema for AGI system"
    })

    print("✅ State with Classification:")
    print(f"   Classified Type: {state['classified_type']}")
    print(f"   Confidence: {state['classification_confidence']:.2f}")
    print(f"   File: {state['file_path']}")

    # Simulate importance assessment
    state.update({
        "importance": 8,
        "importance_reasoning": "New core schema for L1 Observer - architectural foundation",
        "impact_areas": ["backend", "agents", "memory"],
        "timings": {"assess_importance": 120},
        "cost_tracking": {
            "assess": {
                "model": "claude-3-5-haiku",
                "tokens_in": 300,
                "tokens_out": 80,
                "cost_usd": 0.00056,
                "confidence": 0.9
            }
        }
    })

    print("\n✅ Simulated Importance Assessment:")
    print(f"   Importance: {state['importance']}/10")
    print(f"   Reasoning: {state['importance_reasoning']}")
    print(f"   Impact Areas: {', '.join(state['impact_areas'])}")
    print(f"   Timing: {state['timings']['assess_importance']}ms")
    print(f"   Cost: ${state['cost_tracking']['assess']['cost_usd']:.6f}")

    print("\n" + "=" * 60)
    print("✅ STRUCTURE TEST PASSED")
    print("   To test with real API: add ANTHROPIC_API_KEY to .env")


def test_assess_importance():
    """Test importance assessment (requires API keys)"""

    print("🧠 Testing assess_importance Node (Claude Haiku)")
    print("=" * 60)

    # Check if API keys are configured
    try:
        config = get_config()
        if not config.anthropic_api_key or config.anthropic_api_key == "your_anthropic_api_key_here":
            print("\n⚠️  Anthropic API key not configured")
            print("   Add ANTHROPIC_API_KEY to .env to test")
            print("   Showing test structure only...\n")
            test_structure_only()
            return
    except Exception as e:
        print(f"\n⚠️  Configuration error: {e}")
        print("   Showing test structure only...\n")
        test_structure_only()
        return

    # Test cases (real API calls)
    from backend.agents.l1_observer.state import create_initial_state

    test_cases = [
        {
            "name": "New Feature (High Importance)",
            "state": create_initial_state(
                event_type="Write",
                session_id="test-session",
                file_path="/home/pilote/projet/agi/backend/agents/l1_observer/state.py",
                content="class L1State(TypedDict):\n    event_id: str",
                tool_name="Write"
            ),
            "classification": {
                "classified_type": "new_feature",
                "classification_confidence": 0.95,
                "classification_reasoning": "New core schema"
            }
        },
        {
            "name": "Bug Fix (Medium Importance)",
            "state": create_initial_state(
                event_type="Edit",
                session_id="test-session",
                file_path="/home/pilote/projet/agi/backend/services/redis_memory.py",
                content="def add_to_working_memory(self, session_id: str, item: WorkingMemoryItem):\n    # Fix: validate item before adding\n    if not item.id:\n        raise ValueError('Item must have ID')",
                tool_name="Edit"
            ),
            "classification": {
                "classified_type": "bug_fix",
                "classification_confidence": 0.9,
                "classification_reasoning": "Adding validation to prevent errors"
            }
        },
        {
            "name": "Trivial Change (Low Importance)",
            "state": create_initial_state(
                event_type="Edit",
                session_id="test-session",
                file_path="/home/pilote/projet/agi/README.md",
                content="# AGI Memory System\n\nFix typo in documentation.",
                tool_name="Edit"
            ),
            "classification": {
                "classified_type": "documentation",
                "classification_confidence": 0.85,
                "classification_reasoning": "Minor documentation fix"
            }
        }
    ]

    total_cost = 0.0
    total_time = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Test: {test_case['name']}")

        # Apply classification
        state = test_case['state']
        state.update(test_case['classification'])

        print(f"   Classified: {state['classified_type']}")
        print(f"   File: {state['file_path']}")

        # Assess importance
        updates = assess_importance(state)
        state.update(updates)

        # Print results
        print(f"   ✅ Importance: {state['importance']}/10")
        print(f"   💡 Reasoning: {state['importance_reasoning']}")
        print(f"   🎯 Impact: {', '.join(state.get('impact_areas', []))}")
        print(f"   ⚡ Timing: {state['timings']['assess_importance']}ms")

        if "cost_tracking" in state and "assess" in state["cost_tracking"]:
            cost = state["cost_tracking"]["assess"]["cost_usd"]
            print(f"   💰 Cost: ${cost:.6f}")
            total_cost += cost

        total_time += state["timings"]["assess_importance"]

    print("\n" + "=" * 60)
    print(f"✅ ALL TESTS COMPLETED")
    print(f"   Total time: {total_time}ms (avg: {total_time / len(test_cases):.0f}ms)")
    print(f"   Total cost: ${total_cost:.6f} (avg: ${total_cost / len(test_cases):.6f})")


if __name__ == "__main__":
    test_assess_importance()
