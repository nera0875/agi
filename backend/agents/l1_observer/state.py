#!/usr/bin/env python3
"""
L1 Observer Agent - State Schema

TypedDict schema for L1 Observer LangGraph StateGraph.
Represents the state flowing through the L1 processing pipeline.

Pipeline:
  Event → Classify → Assess → Enrich → Decide → Store
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from datetime import datetime


# ═══════════════════════════════════════════════════════
# L1 STATE SCHEMA
# ═══════════════════════════════════════════════════════

class L1State(TypedDict, total=False):
    """
    State for L1 Observer Agent (LangGraph StateGraph)

    Flows through nodes:
    1. classify_event (GPT-5-nano)
    2. assess_importance (Claude Haiku)
    3. enrich_context (MCP tools: Exa, Docfork, Fetch)
    4. decide_storage_layer (routing logic)
    5. store_memory (Redis + PostgreSQL)
    """

    # ═══════════════════════════════════════════════════════
    # INPUT (From Claude Code event)
    # ═══════════════════════════════════════════════════════

    event_id: str  # UUID for tracking
    session_id: str  # Current session ID

    # Raw event data
    event_type: str  # Read, Write, Edit, Bash, think(), etc.
    file_path: Optional[str]  # File path (if applicable)
    content: Optional[str]  # Full content
    content_preview: Optional[str]  # First 500 chars
    tool_name: Optional[str]  # Tool used (Read, Write, Edit, Bash, etc.)
    timestamp: str  # ISO format timestamp

    # ═══════════════════════════════════════════════════════
    # NODE 1: classify_event (GPT-5-nano)
    # ═══════════════════════════════════════════════════════

    classified_type: Optional[str]
    """
    Classified event type:
    - code_edit: Modifying existing code
    - new_feature: Creating new functionality
    - bug_fix: Fixing a bug
    - refactor: Code refactoring
    - documentation: Writing docs
    - decision: Architectural/design decision
    - research: Using MCP tools to research
    - config: Configuration changes
    - test: Writing/running tests
    - trivial: Trivial change (skip)
    """

    classification_confidence: Optional[float]  # 0-1 confidence
    classification_reasoning: Optional[str]  # Why this classification

    # ═══════════════════════════════════════════════════════
    # NODE 2: assess_importance (Claude Haiku)
    # ═══════════════════════════════════════════════════════

    importance: Optional[int]
    """
    Importance score (0-10):
    - 0-2: Trivial (skip)
    - 3-5: Low importance (L1 only, short TTL)
    - 6-7: Medium importance (L1 → L2)
    - 8-9: High importance (L1 → L2 → L3)
    - 10: Critical (immediate L3, architectural decision)
    """

    importance_reasoning: Optional[str]  # Why this score
    impact_areas: Optional[List[str]]  # Which areas affected (frontend, backend, db, etc.)

    # ═══════════════════════════════════════════════════════
    # NODE 3: enrich_context (MCP Tools)
    # ═══════════════════════════════════════════════════════

    enriched_context: Optional[Dict[str, Any]]
    """
    Enriched context from MCP tools:
    {
        "exa_search": [...],  # Related web results
        "docfork_docs": [...],  # Documentation
        "fetch_content": [...],  # Fetched content
        "related_files": [...],  # Related files in codebase
        "related_concepts": [...]  # Related concepts from L3
    }
    """

    enrichment_used: Optional[List[str]]  # Which tools were used

    # ═══════════════════════════════════════════════════════
    # NODE 4: decide_storage_layer (Routing Logic)
    # ═══════════════════════════════════════════════════════

    storage_layer: Optional[Literal["L1", "L2", "L3", "skip"]]
    """
    Storage decision:
    - skip: Trivial event (importance 0-2)
    - L1: Working memory only (importance 3-5, TTL 24h)
    - L2: Short-term memory (importance 6-7, batch processing)
    - L3: Long-term memory (importance 8-10, immediate consolidation)
    """

    storage_reasoning: Optional[str]  # Why this layer

    # ═══════════════════════════════════════════════════════
    # NODE 5: store_memory (Redis + PostgreSQL)
    # ═══════════════════════════════════════════════════════

    stored_in_redis: Optional[bool]  # L1 working memory
    stored_in_postgres: Optional[bool]  # L2/L3 events table
    stored_in_neo4j: Optional[bool]  # L3 graph (for critical events)

    storage_ids: Optional[Dict[str, str]]
    """
    Storage IDs:
    {
        "redis_key": "working_memory:session-123",
        "postgres_id": "uuid-...",
        "neo4j_node_id": "pattern-..."
    }
    """

    # ═══════════════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════════════

    processing_started_at: Optional[str]  # ISO timestamp
    processing_completed_at: Optional[str]  # ISO timestamp
    processing_duration_ms: Optional[int]  # Total duration

    # Node-specific timings
    timings: Optional[Dict[str, int]]
    """
    Per-node timings in ms:
    {
        "classify_event": 45,
        "assess_importance": 120,
        "enrich_context": 300,
        "decide_storage_layer": 5,
        "store_memory": 15
    }
    """

    # Errors (if any)
    errors: Optional[List[Dict[str, str]]]
    """
    Errors encountered:
    [
        {"node": "enrich_context", "error": "Exa API timeout"},
        ...
    ]
    """

    # LLM cost tracking
    cost_tracking: Optional[Dict[str, Any]]
    """
    Cost tracking:
    {
        "classify": {"model": "gpt-5-nano", "tokens_in": 100, "tokens_out": 20, "cost_usd": 0.00001},
        "assess": {"model": "claude-3-5-haiku", "tokens_in": 200, "tokens_out": 50, "cost_usd": 0.00005},
        "total_cost_usd": 0.00006
    }
    """


# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

def create_initial_state(
    event_type: str,
    session_id: str,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    tool_name: Optional[str] = None
) -> L1State:
    """
    Create initial L1State from Claude Code event

    Args:
        event_type: Event type (Read, Write, Edit, etc.)
        session_id: Current session ID
        file_path: File path (optional)
        content: Content (optional)
        tool_name: Tool name (optional)

    Returns:
        Initial L1State
    """
    import uuid

    state: L1State = {
        "event_id": str(uuid.uuid4()),
        "session_id": session_id,
        "event_type": event_type,
        "file_path": file_path,
        "content": content,
        "content_preview": content[:500] if content else None,
        "tool_name": tool_name,
        "timestamp": datetime.utcnow().isoformat(),
        "processing_started_at": datetime.utcnow().isoformat(),
        "timings": {},
        "errors": [],
        "cost_tracking": {}
    }

    return state


def should_skip_event(state: L1State) -> bool:
    """
    Determine if event should be skipped (trivial)

    Returns:
        True if event should be skipped
    """
    # Skip if classified as trivial
    if state.get("classified_type") == "trivial":
        return True

    # Skip if importance too low
    if state.get("importance") is not None and state["importance"] < 3:
        return True

    # Skip if storage decision is 'skip'
    if state.get("storage_layer") == "skip":
        return True

    return False


def get_storage_priority(state: L1State) -> int:
    """
    Get storage priority (for queue ordering)

    Returns:
        Priority (0-10, higher = more urgent)
    """
    importance = state.get("importance", 0)
    storage_layer = state.get("storage_layer")

    # L3 events are highest priority
    if storage_layer == "L3":
        return 10

    # Otherwise use importance
    return importance


def estimate_processing_time(state: L1State) -> int:
    """
    Estimate remaining processing time in ms

    Returns:
        Estimated time in milliseconds
    """
    # Base times per node (ms)
    base_times = {
        "classify_event": 50,  # GPT-5-nano is fast
        "assess_importance": 150,  # Claude Haiku
        "enrich_context": 300,  # MCP tools (variable)
        "decide_storage_layer": 5,  # Pure logic
        "store_memory": 20  # Database writes
    }

    # Check which nodes are already done
    timings = state.get("timings", {})
    remaining_time = 0

    for node, time in base_times.items():
        if node not in timings:
            remaining_time += time

    return remaining_time


# ═══════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════

def validate_state(state: L1State) -> List[str]:
    """
    Validate L1State for completeness

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    required = ["event_id", "session_id", "event_type", "timestamp"]
    for field in required:
        if field not in state or state[field] is None:
            errors.append(f"Missing required field: {field}")

    # Validate importance range
    if "importance" in state and state["importance"] is not None:
        if not (0 <= state["importance"] <= 10):
            errors.append(f"Invalid importance: {state['importance']} (must be 0-10)")

    # Validate storage_layer
    if "storage_layer" in state and state["storage_layer"] is not None:
        valid_layers = ["L1", "L2", "L3", "skip"]
        if state["storage_layer"] not in valid_layers:
            errors.append(f"Invalid storage_layer: {state['storage_layer']}")

    return errors


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧠 Testing L1State Schema")
    print("=" * 60)

    # Create initial state
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session-123",
        file_path="/home/pilote/projet/agi/backend/test.py",
        content="def test():\n    return 42",
        tool_name="Edit"
    )

    print("\n1️⃣ Initial state created:")
    print(f"   Event ID: {state['event_id']}")
    print(f"   Session ID: {state['session_id']}")
    print(f"   Event Type: {state['event_type']}")
    print(f"   Content Preview: {state['content_preview']}")

    # Simulate node processing
    state["classified_type"] = "code_edit"
    state["classification_confidence"] = 0.95
    state["timings"]["classify_event"] = 45

    state["importance"] = 7
    state["importance_reasoning"] = "New function added to core module"
    state["impact_areas"] = ["backend"]
    state["timings"]["assess_importance"] = 120

    state["storage_layer"] = "L2"
    state["storage_reasoning"] = "Medium importance, batch processing appropriate"

    print("\n2️⃣ After processing:")
    print(f"   Classified Type: {state['classified_type']} (confidence: {state['classification_confidence']})")
    print(f"   Importance: {state['importance']}/10")
    print(f"   Storage Layer: {state['storage_layer']}")

    # Validate
    errors = validate_state(state)
    print(f"\n3️⃣ Validation: {'✅ Valid' if not errors else '❌ Errors: ' + str(errors)}")

    # Check skip
    should_skip = should_skip_event(state)
    print(f"   Should skip: {should_skip}")

    # Priority
    priority = get_storage_priority(state)
    print(f"   Storage priority: {priority}/10")

    # Estimate time
    remaining = estimate_processing_time(state)
    print(f"   Estimated remaining time: {remaining}ms")

    print("\n" + "=" * 60)
    print("✅ L1State schema test passed")
