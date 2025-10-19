#!/usr/bin/env python3
"""
Unit tests for store_memory node

Tests:
- SKIP storage layer (trivial events)
- L1 storage (Redis only)
- L2 storage (PostgreSQL + Redis fallback)
- L3 storage (PostgreSQL + Neo4j + Redis)
- Error handling
- Timing tracking
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..'))
sys.path.insert(0, project_root)

from backend.agents.l1_observer.state import create_initial_state, L1State
from backend.agents.l1_observer.nodes.store_memory import (
    store_memory,
    _store_in_l2_postgres,
    _store_in_l3_postgres,
    _store_in_neo4j
)


# ═══════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════

@pytest.fixture
def base_state():
    """Create a basic L1State for testing"""
    return create_initial_state(
        event_type="Edit",
        session_id="test-session-123",
        file_path="/home/pilote/projet/agi/backend/test.py",
        content="def test():\n    return 42",
        tool_name="Edit"
    )


@pytest.fixture
def classified_state(base_state):
    """Create a classified L1State"""
    base_state.update({
        "classified_type": "code_edit",
        "classification_confidence": 0.95,
        "classification_reasoning": "Modifying existing code"
    })
    return base_state


@pytest.fixture
def assessed_state(classified_state):
    """Create an assessed L1State with importance"""
    classified_state.update({
        "importance": 6,
        "importance_reasoning": "New function in core module",
        "impact_areas": ["backend", "core"]
    })
    return classified_state


# ═══════════════════════════════════════════════════════
# TEST: SKIP STORAGE LAYER
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_skip_trivial(assessed_state):
    """Test SKIP storage for trivial events"""

    assessed_state.update({
        "importance": 1,
        "classified_type": "trivial",
        "storage_layer": "skip"
    })

    # Execute
    result = await store_memory(assessed_state)

    # Assertions
    assert result["stored_in_redis"] == False
    assert result["stored_in_postgres"] == False
    assert result["stored_in_neo4j"] == False
    assert result["storage_ids"] == {}
    assert "store_memory" in assessed_state["timings"]
    assert assessed_state["timings"]["store_memory"] >= 0


# ═══════════════════════════════════════════════════════
# TEST: L1 STORAGE LAYER
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_l1_redis(assessed_state):
    """Test L1 storage in Redis working memory"""

    assessed_state.update({
        "importance": 4,
        "storage_layer": "L1"
    })

    # Mock RedisMemoryService
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
        mock_service = Mock()
        mock_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert result["stored_in_redis"] == True
        assert result["stored_in_postgres"] == False
        assert result["stored_in_neo4j"] == False
        assert "redis_key" in result["storage_ids"]
        assert "store_memory" in assessed_state["timings"]

        # Verify Redis was called
        mock_redis.assert_called_once()
        mock_service.add_to_working_memory.assert_called_once()


@pytest.mark.asyncio
async def test_store_memory_l1_redis_error_handling(assessed_state):
    """Test L1 storage with Redis connection error"""

    assessed_state.update({
        "importance": 4,
        "storage_layer": "L1"
    })

    # Mock RedisMemoryService to raise error
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
        mock_redis.side_effect = ConnectionError("Redis connection failed")

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert result["stored_in_redis"] == False
        assert "errors" in assessed_state
        assert len(assessed_state["errors"]) > 0
        assert "L1_redis" in assessed_state["errors"][0].get("storage", "")


# ═══════════════════════════════════════════════════════
# TEST: L2 STORAGE LAYER
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_l2_postgres_and_redis(assessed_state):
    """Test L2 storage in PostgreSQL + Redis fallback"""

    assessed_state.update({
        "importance": 6,
        "storage_layer": "L2"
    })

    # Mock database connection
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = "postgres-uuid-123"

    # Mock RedisMemoryService
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis, \
         patch('backend.agents.l1_observer.nodes.store_memory._get_db_connection') as mock_get_conn:

        mock_get_conn.return_value = mock_conn
        mock_service = Mock()
        mock_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert result["stored_in_postgres"] == True
        assert result["stored_in_redis"] == True
        assert result["stored_in_neo4j"] == False
        assert "postgres_id" in result["storage_ids"]
        assert "redis_key" in result["storage_ids"]
        assert "store_memory" in assessed_state["timings"]

        # Verify operations
        mock_get_conn.assert_called_once()
        assert mock_conn.fetchval.called
        assert mock_service.add_to_working_memory.called


@pytest.mark.asyncio
async def test_store_memory_l2_postgres_error_fallback_to_redis(assessed_state):
    """Test L2 storage: PostgreSQL fails but Redis succeeds"""

    assessed_state.update({
        "importance": 6,
        "storage_layer": "L2"
    })

    # Mock database connection to fail
    mock_conn = AsyncMock()
    mock_conn.fetchval.side_effect = Exception("PostgreSQL connection failed")

    # Mock RedisMemoryService to succeed
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis, \
         patch('backend.agents.l1_observer.nodes.store_memory._get_db_connection') as mock_get_conn:

        mock_get_conn.return_value = mock_conn
        mock_service = Mock()
        mock_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        # PostgreSQL failed but Redis succeeded
        assert result["stored_in_postgres"] == False
        assert result["stored_in_redis"] == True
        assert "errors" in assessed_state
        assert "L2_postgres" in assessed_state["errors"][0].get("storage", "")


# ═══════════════════════════════════════════════════════
# TEST: L3 STORAGE LAYER
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_l3_all_stores(assessed_state):
    """Test L3 storage in PostgreSQL + Neo4j + Redis"""

    assessed_state.update({
        "importance": 9,  # Critical
        "classified_type": "decision",
        "storage_layer": "L3",
        "enriched_context": {
            "related_concepts": ["async", "redis", "memory"]
        }
    })

    # Mock database connection
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = "postgres-uuid-l3"

    # Mock RedisMemoryService
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis, \
         patch('backend.agents.l1_observer.nodes.store_memory._get_db_connection') as mock_get_conn, \
         patch('backend.agents.l1_observer.nodes.store_memory.Neo4jMemoryService') as mock_neo4j:

        mock_get_conn.return_value = mock_conn

        mock_redis_service = Mock()
        mock_redis_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_redis_service

        mock_neo4j_service = Mock()
        mock_neo4j_service.create_node.return_value = "neo4j-node-123"
        mock_neo4j.return_value = mock_neo4j_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert result["stored_in_postgres"] == True
        assert result["stored_in_redis"] == True
        assert result["stored_in_neo4j"] == True
        assert "postgres_id" in result["storage_ids"]
        assert "redis_key" in result["storage_ids"]
        assert "neo4j_node_id" in result["storage_ids"]
        assert "store_memory" in assessed_state["timings"]

        # Verify all operations were called
        assert mock_conn.fetchval.called
        assert mock_redis_service.add_to_working_memory.called
        assert mock_neo4j_service.create_node.called
        assert mock_neo4j_service.close.called


@pytest.mark.asyncio
async def test_store_memory_l3_low_importance_no_neo4j(assessed_state):
    """Test L3 storage without Neo4j when importance < 9"""

    assessed_state.update({
        "importance": 7,  # Not critical enough for Neo4j
        "storage_layer": "L3"
    })

    # Mock database connection
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = "postgres-uuid-l3"

    # Mock RedisMemoryService
    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis, \
         patch('backend.agents.l1_observer.nodes.store_memory._get_db_connection') as mock_get_conn, \
         patch('backend.agents.l1_observer.nodes.store_memory.Neo4jMemoryService') as mock_neo4j:

        mock_get_conn.return_value = mock_conn

        mock_redis_service = Mock()
        mock_redis_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_redis_service

        # Neo4j should NOT be called
        mock_neo4j_service = Mock()
        mock_neo4j.return_value = mock_neo4j_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert result["stored_in_postgres"] == True
        assert result["stored_in_redis"] == True
        assert result["stored_in_neo4j"] == False
        assert "neo4j_node_id" not in result["storage_ids"]

        # Neo4j should NOT be called
        mock_neo4j.assert_not_called()


# ═══════════════════════════════════════════════════════
# TEST: TIMING TRACKING
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_timing_tracking(assessed_state):
    """Test timing is tracked for all storage layers"""

    for storage_layer in ["skip", "L1", "L2", "L3"]:
        assessed_state.update({
            "storage_layer": storage_layer,
            "timings": {}
        })

        if storage_layer != "skip":
            assessed_state["importance"] = 5 if storage_layer == "L1" else (6 if storage_layer == "L2" else 9)

        with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis, \
             patch('backend.agents.l1_observer.nodes.store_memory._get_db_connection') as mock_get_conn, \
             patch('backend.agents.l1_observer.nodes.store_memory.Neo4jMemoryService') as mock_neo4j:

            mock_redis.return_value.add_to_working_memory.return_value = 5
            mock_get_conn.return_value.fetchval = AsyncMock(return_value="test-id")
            mock_neo4j.return_value.create_node.return_value = "neo4j-id"

            # Execute
            result = await store_memory(assessed_state)

            # Assertions
            assert "store_memory" in assessed_state["timings"]
            assert assessed_state["timings"]["store_memory"] >= 0


# ═══════════════════════════════════════════════════════
# TEST: STATE UPDATES
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_returns_storage_ids(assessed_state):
    """Test that storage_ids are properly returned"""

    assessed_state.update({
        "importance": 4,
        "storage_layer": "L1"
    })

    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
        mock_service = Mock()
        mock_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_service

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert "storage_ids" in result
        assert isinstance(result["storage_ids"], dict)


@pytest.mark.asyncio
async def test_store_memory_error_collection(assessed_state):
    """Test that errors are properly collected in state"""

    assessed_state.update({
        "importance": 4,
        "storage_layer": "L1"
    })

    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
        mock_redis.side_effect = Exception("Test error")

        # Execute
        result = await store_memory(assessed_state)

        # Assertions
        assert "errors" in assessed_state
        assert len(assessed_state["errors"]) > 0
        error = assessed_state["errors"][0]
        assert "node" in error
        assert error["node"] == "store_memory"
        assert "error" in error
        assert "timestamp" in error


# ═══════════════════════════════════════════════════════
# INTEGRATION TESTS (STRUCTURE ONLY)
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_full_pipeline_skip():
    """Test full pipeline with skip decision"""

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

    # Execute
    result = await store_memory(state)

    # Assertions
    assert result["stored_in_redis"] == False
    assert result["stored_in_postgres"] == False
    assert "store_memory" in state["timings"]


@pytest.mark.asyncio
async def test_store_memory_full_pipeline_l1():
    """Test full pipeline with L1 decision"""

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

    with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
        mock_service = Mock()
        mock_service.add_to_working_memory.return_value = 5
        mock_redis.return_value = mock_service

        # Execute
        result = await store_memory(state)

        # Assertions
        assert result["stored_in_redis"] == True
        assert result["stored_in_postgres"] == False
        assert "store_memory" in state["timings"]


# ═══════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_store_memory_performance_skip_fast():
    """Test SKIP path is very fast (<10ms)"""

    state = create_initial_state(
        event_type="Read",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/test.py",
        content="# trivial",
        tool_name="Read"
    )

    state.update({
        "storage_layer": "skip"
    })

    # Execute
    result = await store_memory(state)

    # Assertions
    timing = state["timings"]["store_memory"]
    assert timing < 50, f"SKIP should be <50ms, got {timing}ms"


@pytest.mark.asyncio
async def test_store_memory_all_paths_complete_quickly():
    """Test all storage paths complete in reasonable time"""

    for storage_layer in ["skip", "L1"]:
        state = create_initial_state(
            event_type="Edit",
            session_id="test-session",
            file_path="/home/pilote/projet/agi/test.py",
            content="test code",
            tool_name="Edit"
        )

        state.update({
            "storage_layer": storage_layer,
            "importance": 4 if storage_layer == "L1" else 1
        })

        if storage_layer != "skip":
            with patch('backend.agents.l1_observer.nodes.store_memory.RedisMemoryService') as mock_redis:
                mock_redis.return_value.add_to_working_memory.return_value = 5

                result = await store_memory(state)
                timing = state["timings"]["store_memory"]
                assert timing < 500, f"{storage_layer} should complete in <500ms, got {timing}ms"
        else:
            result = await store_memory(state)
            timing = state["timings"]["store_memory"]
            assert timing < 100, f"{storage_layer} should complete in <100ms, got {timing}ms"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
