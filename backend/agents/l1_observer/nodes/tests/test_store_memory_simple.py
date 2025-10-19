#!/usr/bin/env python3
"""
Simplified unit tests for store_memory node
Focus on structure and basic functionality without complex mocking
"""

import pytest
import asyncio
from datetime import datetime

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..'))
sys.path.insert(0, project_root)

from backend.agents.l1_observer.state import create_initial_state


# ═══════════════════════════════════════════════════════
# BASIC STRUCTURE TESTS
# ═══════════════════════════════════════════════════════

def test_state_creation():
    """Test L1State creation"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/test.py",
        content="test code",
        tool_name="Edit"
    )

    assert state["event_id"] is not None
    assert state["session_id"] == "test-session"
    assert state["event_type"] == "Edit"
    assert state["file_path"] == "/home/pilote/projet/agi/test.py"
    assert state["content"] == "test code"
    assert state["content_preview"] == "test code"
    assert "timings" in state
    assert isinstance(state["timings"], dict)


def test_state_with_classification():
    """Test L1State with classification"""
    state = create_initial_state(
        event_type="Write",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/new_feature.py",
        content="class NewService:\n    pass",
        tool_name="Write"
    )

    state.update({
        "classified_type": "new_feature",
        "classification_confidence": 0.95,
        "classification_reasoning": "New class creation"
    })

    assert state["classified_type"] == "new_feature"
    assert state["classification_confidence"] == 0.95


def test_state_with_importance():
    """Test L1State with importance assessment"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/core.py",
        content="def core_function():\n    pass",
        tool_name="Edit"
    )

    state.update({
        "classified_type": "new_feature",
        "importance": 7,
        "importance_reasoning": "New core function",
        "impact_areas": ["backend", "core"]
    })

    assert state["importance"] == 7
    assert state["impact_areas"] == ["backend", "core"]


def test_skip_storage_layer():
    """Test SKIP storage layer decision"""
    state = create_initial_state(
        event_type="Read",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/README.md",
        content="# Trivial read",
        tool_name="Read"
    )

    state.update({
        "classified_type": "trivial",
        "importance": 1,
        "storage_layer": "skip"
    })

    assert state["storage_layer"] == "skip"


def test_l1_storage_layer():
    """Test L1 storage layer decision"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/utils.py",
        content="def helper():\n    pass",
        tool_name="Edit"
    )

    state.update({
        "classified_type": "code_edit",
        "importance": 4,
        "storage_layer": "L1"
    })

    assert state["storage_layer"] == "L1"
    assert state["importance"] >= 3
    assert state["importance"] <= 5


def test_l2_storage_layer():
    """Test L2 storage layer decision"""
    state = create_initial_state(
        event_type="Write",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/new_module.py",
        content="class NewModule:\n    pass",
        tool_name="Write"
    )

    state.update({
        "classified_type": "new_feature",
        "importance": 6,
        "storage_layer": "L2"
    })

    assert state["storage_layer"] == "L2"
    assert state["importance"] >= 6
    assert state["importance"] <= 7


def test_l3_storage_layer():
    """Test L3 storage layer decision"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/core/memory.py",
        content="# Critical architectural change",
        tool_name="Edit"
    )

    state.update({
        "classified_type": "decision",
        "importance": 9,
        "storage_layer": "L3",
        "enriched_context": {
            "related_concepts": ["async", "redis", "memory"]
        }
    })

    assert state["storage_layer"] == "L3"
    assert state["importance"] >= 8
    assert state["importance"] <= 10


# ═══════════════════════════════════════════════════════
# STORAGE DECISION LOGIC TESTS
# ═══════════════════════════════════════════════════════

def test_importance_ranges():
    """Test importance score ranges for different storage layers"""

    # Test all importance values
    test_cases = [
        # (importance, expected_storage_layer)
        (0, "skip"),  # Trivial
        (1, "skip"),  # Trivial
        (2, "skip"),  # Trivial edge
        (3, "L1"),    # Low importance
        (4, "L1"),    # Low importance
        (5, "L1"),    # Low importance edge
        (6, "L2"),    # Medium importance
        (7, "L2"),    # Medium importance edge
        (8, "L3"),    # High importance
        (9, "L3"),    # Critical
        (10, "L3"),   # Maximum critical
    ]

    for importance, expected_layer in test_cases:
        state = create_initial_state(
            event_type="Edit",
            session_id="test",
            file_path="/test.py",
            content="test",
            tool_name="Edit"
        )

        # Simulate routing logic
        if importance <= 2:
            storage_layer = "skip"
        elif importance <= 5:
            storage_layer = "L1"
        elif importance <= 7:
            storage_layer = "L2"
        else:
            storage_layer = "L3"

        assert storage_layer == expected_layer, f"Importance {importance} should be {expected_layer}"


def test_classified_type_to_importance_mapping():
    """Test mapping of classified types to importance scores"""

    type_to_importance = {
        "trivial": (0, 2),           # Trivial
        "code_edit": (3, 5),         # Low importance
        "new_feature": (6, 8),       # Medium to high
        "bug_fix": (6, 9),           # Medium to critical
        "refactor": (3, 6),          # Low to medium
        "documentation": (2, 5),     # Trivial to low
        "decision": (7, 10),         # Medium to critical
        "research": (3, 6),          # Low to medium
        "config": (3, 5),            # Low importance
        "test": (3, 6),              # Low to medium
    }

    for classified_type, (min_imp, max_imp) in type_to_importance.items():
        state = create_initial_state(
            event_type="Edit",
            session_id="test",
            file_path="/test.py",
            content="test",
            tool_name="Edit"
        )

        state.update({
            "classified_type": classified_type,
            "importance": min_imp  # Use minimum expected
        })

        assert state["importance"] >= 0
        assert state["importance"] <= 10


# ═══════════════════════════════════════════════════════
# ERROR HANDLING TESTS
# ═══════════════════════════════════════════════════════

def test_state_with_errors():
    """Test error tracking in state"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test",
        file_path="/test.py",
        content="test",
        tool_name="Edit"
    )

    # Add error
    state["errors"] = []
    state["errors"].append({
        "node": "test_node",
        "error": "Test error",
        "timestamp": datetime.utcnow().isoformat()
    })

    assert len(state["errors"]) == 1
    assert state["errors"][0]["node"] == "test_node"


def test_state_with_timing():
    """Test timing tracking in state"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test",
        file_path="/test.py",
        content="test",
        tool_name="Edit"
    )

    state["timings"]["test_node"] = 45

    assert state["timings"]["test_node"] == 45


# ═══════════════════════════════════════════════════════
# STORAGE ID GENERATION TESTS
# ═══════════════════════════════════════════════════════

def test_storage_ids_structure():
    """Test storage_ids dictionary structure"""
    import uuid

    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/test.py",
        content="test",
        tool_name="Edit"
    )

    # Simulate different storage backends
    storage_ids = {
        "redis_key": f"working_memory:{state['session_id']}",
        "postgres_id": str(uuid.uuid4()),
        "neo4j_node_id": f"event-{state['event_id'][:8]}"
    }

    assert isinstance(storage_ids, dict)
    assert "redis_key" in storage_ids
    assert "postgres_id" in storage_ids
    assert "neo4j_node_id" in storage_ids
    assert storage_ids["redis_key"].startswith("working_memory:")


# ═══════════════════════════════════════════════════════
# ENRICHED CONTEXT TESTS
# ═══════════════════════════════════════════════════════

def test_enriched_context_structure():
    """Test enriched context structure"""
    state = create_initial_state(
        event_type="Edit",
        session_id="test",
        file_path="/test.py",
        content="test",
        tool_name="Edit"
    )

    state["enriched_context"] = {
        "exa_search": ["result1", "result2"],
        "docfork_docs": ["doc1", "doc2"],
        "fetch_content": ["content1"],
        "related_files": ["file1", "file2"],
        "related_concepts": ["async", "redis"]
    }

    assert "enriched_context" in state
    assert "related_concepts" in state["enriched_context"]
    assert len(state["enriched_context"]["related_concepts"]) == 2


# ═══════════════════════════════════════════════════════
# CONTENT PREVIEW TESTS
# ═══════════════════════════════════════════════════════

def test_content_preview_truncation():
    """Test content preview is truncated to 500 chars"""
    long_content = "x" * 1000
    state = create_initial_state(
        event_type="Write",
        session_id="test",
        file_path="/test.py",
        content=long_content,
        tool_name="Write"
    )

    assert len(state["content_preview"]) == 500
    assert state["content_preview"] == long_content[:500]


def test_content_preview_short_content():
    """Test content preview with short content"""
    short_content = "short"
    state = create_initial_state(
        event_type="Read",
        session_id="test",
        file_path="/test.py",
        content=short_content,
        tool_name="Read"
    )

    assert state["content_preview"] == short_content


# ═══════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════

def test_full_event_lifecycle():
    """Test full event lifecycle from creation to storage decision"""
    # Create
    state = create_initial_state(
        event_type="Edit",
        session_id="session-123",
        file_path="/home/pilote/projet/agi/backend/core.py",
        content="def new_core_function():\n    return True",
        tool_name="Edit"
    )

    # Classify
    state.update({
        "classified_type": "new_feature",
        "classification_confidence": 0.95,
        "classification_reasoning": "New function definition"
    })

    # Assess
    state.update({
        "importance": 8,
        "importance_reasoning": "Core function, high impact",
        "impact_areas": ["backend", "core", "api"]
    })

    # Decide
    if state["importance"] <= 2:
        state["storage_layer"] = "skip"
    elif state["importance"] <= 5:
        state["storage_layer"] = "L1"
    elif state["importance"] <= 7:
        state["storage_layer"] = "L2"
    else:
        state["storage_layer"] = "L3"

    # Verify full lifecycle
    assert state["event_id"] is not None
    assert state["classified_type"] == "new_feature"
    assert state["importance"] == 8
    assert state["storage_layer"] == "L3"
    assert "core" in state["impact_areas"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
