#!/usr/bin/env python3
"""
L1 Observer Node: classify_event

Uses GPT-5-nano to classify events into semantic types.
Ultra-fast classification (<50ms) for real-time processing.

Model: GPT-5-nano
Cost: ~$0.00001 per classification
Latency: ~30-50ms
"""

import time
from typing import Dict
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser

import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# Direct import to avoid conflicts with old settings
from backend.config.agi_config import get_config
from backend.agents.l1_observer.state import L1State


# ═══════════════════════════════════════════════════════
# CLASSIFICATION PROMPT
# ═══════════════════════════════════════════════════════

CLASSIFICATION_SYSTEM_PROMPT = """You are an ultra-fast event classifier for an AGI memory system.

Your job is to classify Claude Code events into semantic types in <50ms.

**Event Types:**
- code_edit: Modifying existing code
- new_feature: Creating new functionality
- bug_fix: Fixing a bug
- refactor: Code refactoring without functionality change
- documentation: Writing/updating docs, comments, README
- decision: Architectural or design decision
- research: Using MCP tools (Exa, Docfork, Fetch) to research
- config: Configuration changes (.env, .json, .yaml, etc.)
- test: Writing or running tests
- trivial: Trivial change (typo, whitespace, minor formatting)

**Instructions:**
1. Analyze the event type, file path, and content preview
2. Classify into ONE type above
3. Assign confidence (0-1)
4. Provide brief reasoning (1 sentence)

**Response Format (JSON):**
{
    "type": "code_edit",
    "confidence": 0.95,
    "reasoning": "Modifying existing function in core module"
}

**Rules:**
- Be FAST - this runs on every event
- Default to "trivial" if unsure
- Use file extension hints (.py, .md, .test.py, etc.)
- Consider context from file path
"""


# ═══════════════════════════════════════════════════════
# NODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════

def classify_event(state: L1State) -> Dict:
    """
    Classify event using GPT-5-nano

    Updates state with:
    - classified_type
    - classification_confidence
    - classification_reasoning
    - timings["classify_event"]
    - cost_tracking["classify"]

    Args:
        state: Current L1State

    Returns:
        Updated state dict
    """
    start_time = time.time()

    # Get config
    config = get_config()

    # Initialize GPT-5-nano
    llm = ChatOpenAI(
        model="gpt-5-nano",  # Ultra-fast, ultra-cheap
        temperature=0.1,  # Low temperature for consistent classification
        api_key=config.openai_api_key,
        organization=config.openai_organization
    )

    # Create human message with event details
    event_details = f"""Event Type: {state['event_type']}
File Path: {state.get('file_path', 'N/A')}
Tool: {state.get('tool_name', 'N/A')}
Content Preview:
{state.get('content_preview', 'N/A')}
"""

    messages = [
        SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
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
        classified_type = result.get("type", "trivial")
        confidence = result.get("confidence", 0.5)
        reasoning = result.get("reasoning", "No reasoning provided")

        # Calculate cost (GPT-5-nano pricing)
        # Estimate: ~150 tokens in, ~30 tokens out
        tokens_in = 150
        tokens_out = 30
        cost_per_1m_tokens_in = 0.10  # $0.10 / 1M tokens
        cost_per_1m_tokens_out = 0.40  # $0.40 / 1M tokens

        cost_usd = (
            (tokens_in / 1_000_000) * cost_per_1m_tokens_in +
            (tokens_out / 1_000_000) * cost_per_1m_tokens_out
        )

        # Calculate timing
        duration_ms = int((time.time() - start_time) * 1000)

        # Update state
        updates = {
            "classified_type": classified_type,
            "classification_confidence": confidence,
            "classification_reasoning": reasoning,
        }

        # Update timings
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["classify_event"] = duration_ms

        # Update cost tracking
        if "cost_tracking" not in state:
            state["cost_tracking"] = {}
        state["cost_tracking"]["classify"] = {
            "model": "gpt-5-nano",
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd
        }

        return updates

    except Exception as e:
        # Handle errors gracefully
        duration_ms = int((time.time() - start_time) * 1000)

        # Add error to state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "node": "classify_event",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update timings even on error
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["classify_event"] = duration_ms

        # Fallback to trivial
        return {
            "classified_type": "trivial",
            "classification_confidence": 0.0,
            "classification_reasoning": f"Classification failed: {str(e)}"
        }


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_structure_only():
    """Test structure without API calls"""
    from backend.agents.l1_observer.state import create_initial_state

    # Create test state
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/test.py",
        content="def test():\n    return 42",
        tool_name="Edit"
    )

    print("✅ State Structure Test:")
    print(f"   Event ID: {state['event_id']}")
    print(f"   Event Type: {state['event_type']}")
    print(f"   File Path: {state['file_path']}")
    print(f"   Content Preview: {state['content_preview']}")

    # Simulate classification result
    state.update({
        "classified_type": "code_edit",
        "classification_confidence": 0.95,
        "classification_reasoning": "Simulated: Modifying existing code",
        "timings": {"classify_event": 45},
        "cost_tracking": {
            "classify": {
                "model": "gpt-5-nano",
                "tokens_in": 150,
                "tokens_out": 30,
                "cost_usd": 0.000015
            }
        }
    })

    print("\n✅ Simulated Classification:")
    print(f"   Type: {state['classified_type']}")
    print(f"   Confidence: {state['classification_confidence']:.2f}")
    print(f"   Reasoning: {state['classification_reasoning']}")
    print(f"   Timing: {state['timings']['classify_event']}ms")
    print(f"   Cost: ${state['cost_tracking']['classify']['cost_usd']:.6f}")

    print("\n" + "=" * 60)
    print("✅ STRUCTURE TEST PASSED")
    print("   To test with real API: add OPENAI_API_KEY to .env")


def test_classify_event():
    """Test event classification (requires API keys)"""

    print("🧠 Testing classify_event Node (GPT-5-nano)")
    print("=" * 60)

    # Check if API keys are configured
    try:
        config = get_config()
        if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
            print("\n⚠️  OpenAI API key not configured")
            print("   Add OPENAI_API_KEY to .env to test")
            print("   Showing test structure only...\n")
            test_structure_only()
            return
    except Exception as e:
        print(f"\n⚠️  Configuration error: {e}")
        print("   Showing test structure only...\n")
        test_structure_only()
        return

    # Test cases (real API calls)
    test_cases = [
        {
            "name": "Code Edit",
            "state": {
                "event_id": "test-1",
                "session_id": "test-session",
                "event_type": "Edit",
                "file_path": "/home/pilote/projet/agi/backend/services/redis_memory.py",
                "content_preview": "def add_to_working_memory(self, session_id: str, item: WorkingMemoryItem):",
                "tool_name": "Edit",
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "name": "New Feature",
            "state": {
                "event_id": "test-2",
                "session_id": "test-session",
                "event_type": "Write",
                "file_path": "/home/pilote/projet/agi/backend/agents/l1_observer/state.py",
                "content_preview": "class L1State(TypedDict, total=False):\n    event_id: str",
                "tool_name": "Write",
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "name": "Documentation",
            "state": {
                "event_id": "test-3",
                "session_id": "test-session",
                "event_type": "Write",
                "file_path": "/home/pilote/projet/agi/README.md",
                "content_preview": "# AGI Memory System\n\nThis is the documentation for...",
                "tool_name": "Write",
                "timestamp": datetime.utcnow().isoformat()
            }
        },
        {
            "name": "Config Change",
            "state": {
                "event_id": "test-4",
                "session_id": "test-session",
                "event_type": "Edit",
                "file_path": "/home/pilote/projet/agi/.env",
                "content_preview": "OPENAI_API_KEY=sk-...",
                "tool_name": "Edit",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    ]

    total_cost = 0.0
    total_time = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Test: {test_case['name']}")
        print(f"   File: {test_case['state']['file_path']}")

        # Classify
        state = test_case['state']
        updates = classify_event(state)

        # Apply updates
        state.update(updates)

        # Print results
        print(f"   ✅ Type: {state['classified_type']}")
        print(f"   📊 Confidence: {state['classification_confidence']:.2f}")
        print(f"   💡 Reasoning: {state['classification_reasoning']}")
        print(f"   ⚡ Timing: {state['timings']['classify_event']}ms")

        if "cost_tracking" in state and "classify" in state["cost_tracking"]:
            cost = state["cost_tracking"]["classify"]["cost_usd"]
            print(f"   💰 Cost: ${cost:.6f}")
            total_cost += cost

        total_time += state["timings"]["classify_event"]

    print("\n" + "=" * 60)
    print(f"✅ ALL TESTS COMPLETED")
    print(f"   Total time: {total_time}ms (avg: {total_time / len(test_cases):.0f}ms)")
    print(f"   Total cost: ${total_cost:.6f} (avg: ${total_cost / len(test_cases):.6f})")


if __name__ == "__main__":
    test_classify_event()
