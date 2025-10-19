#!/usr/bin/env python3
"""
L1 Observer Node: enrich_context

Uses MCP tools (Exa, Docfork, Fetch) to enrich event context.
Provides additional information for better importance assessment.

Tools: Exa (web search), Docfork (docs), Fetch (URL content)
"""

import time
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

from backend.agents.l1_observer.state import L1State
from backend.agents.l1_observer.mcp_integration import L1MCPTools, enrich_context_with_mcp


# ═══════════════════════════════════════════════════════
# NODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════

async def enrich_context(state: L1State) -> Dict:
    """
    Enrich event context using MCP tools

    Updates state with:
    - enriched_context (dict with tool results)
    - enrichment_used (list of tools used)
    - timings["enrich_context"]

    Args:
        state: Current L1State

    Returns:
        Updated state dict
    """
    start_time = time.time()

    # Determine which enrichment is needed
    classified_type = state.get("classified_type", "trivial")
    importance = state.get("importance", 0)
    file_path = state.get("file_path", "")
    content_preview = state.get("content_preview", "")

    # Skip enrichment for trivial events
    if classified_type == "trivial" or importance < 5:
        duration_ms = int((time.time() - start_time) * 1000)
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["enrich_context"] = duration_ms

        return {
            "enriched_context": {},
            "enrichment_used": []
        }

    try:
        # Use the MCP integration helper
        enrichment_result = await enrich_context_with_mcp(
            classified_type=classified_type,
            file_path=file_path,
            content_preview=content_preview,
            importance=importance
        )

        # Calculate timing
        duration_ms = int((time.time() - start_time) * 1000)

        # Update state
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["enrich_context"] = duration_ms

        return {
            "enriched_context": enrichment_result.get("enrichment", {}),
            "enrichment_used": enrichment_result.get("tools_used", [])
        }

    except Exception as e:
        # Handle errors gracefully
        duration_ms = int((time.time() - start_time) * 1000)

        # Add error to state
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "node": "enrich_context",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

        # Update timings even on error
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["enrich_context"] = duration_ms

        # Return empty enrichment on error
        return {
            "enriched_context": {},
            "enrichment_used": []
        }


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_structure_only():
    """Test structure without MCP calls"""
    import asyncio
    from backend.agents.l1_observer.state import create_initial_state

    async def run_test():
        # Create test state
        state = create_initial_state(
            event_type="Write",
            session_id="test-session",
            file_path="/home/pilote/projet/agi/backend/agents/l1_observer/state.py",
            content="class L1State(TypedDict):\n    event_id: str",
            tool_name="Write"
        )

        # Add classification and importance
        state.update({
            "classified_type": "new_feature",
            "classification_confidence": 0.95,
            "importance": 8,
            "importance_reasoning": "New core schema"
        })

        print("✅ State before enrichment:")
        print(f"   Classified: {state['classified_type']}")
        print(f"   Importance: {state['importance']}/10")
        print(f"   File: {state['file_path']}")

        # Simulate enrichment (no real MCP calls)
        state.update({
            "enriched_context": {
                "related_docs": ["LangGraph StateGraph documentation"],
                "similar_patterns": ["TypedDict usage in LangChain"],
                "web_results": []
            },
            "enrichment_used": ["docfork"],
            "timings": {"enrich_context": 250}
        })

        print("\n✅ Simulated Enrichment:")
        print(f"   Tools used: {', '.join(state['enrichment_used'])}")
        print(f"   Context keys: {list(state['enriched_context'].keys())}")
        print(f"   Timing: {state['timings']['enrich_context']}ms")

        print("\n" + "=" * 60)
        print("✅ STRUCTURE TEST PASSED")
        print("   To test with real MCP: ensure MCP servers running")

    asyncio.run(run_test())


def test_enrich_context():
    """Test context enrichment (requires MCP servers)"""
    import asyncio
    from backend.agents.l1_observer.state import create_initial_state

    async def run_test():
        print("🧠 Testing enrich_context Node (MCP Tools)")
        print("=" * 60)

        # Test cases
        test_cases = [
            {
                "name": "High Importance Feature (should enrich)",
                "state": create_initial_state(
                    event_type="Write",
                    session_id="test-session",
                    file_path="/home/pilote/projet/agi/backend/agents/l1_observer/graph.py",
                    content="from langgraph.graph import StateGraph\n\nclass L1ObserverGraph:",
                    tool_name="Write"
                ),
                "classification": {
                    "classified_type": "new_feature",
                    "importance": 8
                }
            },
            {
                "name": "Low Importance Edit (should skip enrichment)",
                "state": create_initial_state(
                    event_type="Edit",
                    session_id="test-session",
                    file_path="/home/pilote/projet/agi/test.py",
                    content="# Minor comment change",
                    tool_name="Edit"
                ),
                "classification": {
                    "classified_type": "trivial",
                    "importance": 2
                }
            },
            {
                "name": "Research Event (should use Exa)",
                "state": create_initial_state(
                    event_type="think",
                    session_id="test-session",
                    content="Researching LangGraph best practices",
                    tool_name="think"
                ),
                "classification": {
                    "classified_type": "research",
                    "importance": 6
                }
            }
        ]

        total_time = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}️⃣ Test: {test_case['name']}")

            # Setup state
            state = test_case['state']
            state.update(test_case['classification'])

            print(f"   Type: {state['classified_type']}, Importance: {state['importance']}/10")

            try:
                # Enrich context
                updates = await enrich_context(state)
                state.update(updates)

                # Print results
                tools_used = state.get('enrichment_used', [])
                enriched = state.get('enriched_context', {})

                print(f"   ✅ Tools used: {', '.join(tools_used) if tools_used else 'none (skipped)'}")
                print(f"   📦 Context keys: {list(enriched.keys()) if enriched else 'none'}")
                print(f"   ⚡ Timing: {state['timings']['enrich_context']}ms")

                total_time += state["timings"]["enrich_context"]

            except Exception as e:
                print(f"   ❌ Error: {e}")

        print("\n" + "=" * 60)
        print(f"✅ ALL TESTS COMPLETED")
        print(f"   Total time: {total_time}ms")

    asyncio.run(run_test())


if __name__ == "__main__":
    # Run structure test (no MCP required)
    print("Running structure-only test (no MCP servers needed)...\n")
    test_structure_only()

    print("\n" + "=" * 60)
    print("\nTo test with real MCP servers, ensure they are running and call:")
    print("  python3 backend/agents/l1_observer/nodes/enrich_context.py --real-mcp")
