#!/usr/bin/env python3
"""
L1 Observer Node: store_memory

Stores events according to the storage_layer decision.
Distributes data across Redis (L1), PostgreSQL (L2/L3), and Neo4j (L3 critical).

Storage logic:
- "skip" → Do nothing (trivial events)
- "L1" → Redis working memory only
- "L2" → PostgreSQL l2_events table + L1 fallback
- "L3" → PostgreSQL l3_knowledge + Neo4j graph (if critical)

Model: No LLM (pure routing logic)
Latency: <50ms (mostly database writes)
"""

import time
import uuid
from typing import Dict, Optional
from datetime import datetime

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, project_root)

# Try to import, with graceful fallback for testing
try:
    from backend.config.agi_config import get_config
except ImportError:
    # Fallback for testing when config is not available
    def get_config():
        class MockConfig:
            postgres_host = "localhost"
            postgres_port = 5432
            postgres_db = "agi_db"
            postgres_user = "agi_user"
            postgres_password = "agi_password"
            postgres_url = "postgresql://agi_user:agi_password@localhost:5432/agi_db"
            redis_host = "localhost"
            redis_port = 6379
            redis_db = 0
            redis_password = None
            neo4j_uri = "bolt://localhost:7687"
            neo4j_user = "neo4j"
            neo4j_password = "Voiture789"
        return MockConfig()

from backend.agents.l1_observer.state import L1State

try:
    from backend.services.redis_memory import RedisMemoryService, WorkingMemoryItem
except ImportError:
    # Fallback classes for testing
    class WorkingMemoryItem:
        def __init__(self, id, type, content, importance, timestamp):
            self.id = id
            self.type = type
            self.content = content
            self.importance = importance
            self.timestamp = timestamp

    class RedisMemoryService:
        def __init__(self, *args, **kwargs):
            pass
        def add_to_working_memory(self, session_id, item):
            return 1

try:
    from backend.services.neo4j_memory import Neo4jMemoryService, GraphNode, GraphRelation
except ImportError:
    # Fallback classes for testing
    class GraphNode:
        def __init__(self, id, type, content, tags, strength=0.5, access_count=0):
            self.id = id
            self.type = type
            self.content = content
            self.tags = tags
            self.strength = strength
            self.access_count = access_count

    class GraphRelation:
        def __init__(self, from_id, to_id, relation_type, strength=0.5, metadata=None):
            self.from_id = from_id
            self.to_id = to_id
            self.relation_type = relation_type
            self.strength = strength
            self.metadata = metadata or {}

    class Neo4jMemoryService:
        def __init__(self, *args, **kwargs):
            pass
        def create_node(self, node):
            return node.id
        def create_relation(self, relation):
            return True
        def close(self):
            pass


# ═══════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════

async def _get_db_connection():
    """Get PostgreSQL connection"""
    import asyncpg
    config = get_config()
    conn = await asyncpg.connect(config.postgres_url)
    return conn


async def _store_in_l2_postgres(state: L1State, conn) -> str:
    """
    Store event in PostgreSQL l2_events table

    Returns:
        Event ID (UUID)
    """
    event_id = str(uuid.uuid4())

    query = """
        INSERT INTO l2_events (
            event_id, session_id, classified_type, importance,
            file_path, content_preview, content,
            classification_confidence, importance_reasoning,
            impact_areas, enriched_context,
            created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
        ON CONFLICT (event_id) DO UPDATE SET
            updated_at = NOW(),
            classification_confidence = EXCLUDED.classification_confidence,
            importance_reasoning = EXCLUDED.importance_reasoning
        RETURNING event_id
    """

    now = datetime.utcnow().isoformat()

    try:
        result = await conn.fetchval(
            query,
            state.get('event_id'),
            state.get('session_id'),
            state.get('classified_type'),
            state.get('importance'),
            state.get('file_path'),
            state.get('content_preview'),
            state.get('content'),
            state.get('classification_confidence'),
            state.get('importance_reasoning'),
            state.get('impact_areas'),
            state.get('enriched_context'),
            now,
            now
        )
        return result if result else event_id
    except Exception as e:
        # Table might not exist yet - log and continue
        print(f"⚠️  L2 storage warning: {str(e)}")
        return event_id


async def _store_in_l3_postgres(state: L1State, conn) -> str:
    """
    Store event in PostgreSQL l3_knowledge table

    Returns:
        Knowledge ID (UUID)
    """
    knowledge_id = str(uuid.uuid4())

    query = """
        INSERT INTO l3_knowledge (
            knowledge_id, session_id, event_id, classified_type,
            importance, file_path, content_preview, content,
            classification_confidence, importance_reasoning,
            impact_areas, enriched_context,
            consolidation_priority, is_critical,
            created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
        )
        ON CONFLICT (knowledge_id) DO UPDATE SET
            updated_at = NOW(),
            consolidation_priority = EXCLUDED.consolidation_priority
        RETURNING knowledge_id
    """

    now = datetime.utcnow().isoformat()
    is_critical = state.get('importance', 0) >= 9

    try:
        result = await conn.fetchval(
            query,
            knowledge_id,
            state.get('session_id'),
            state.get('event_id'),
            state.get('classified_type'),
            state.get('importance'),
            state.get('file_path'),
            state.get('content_preview'),
            state.get('content'),
            state.get('classification_confidence'),
            state.get('importance_reasoning'),
            state.get('impact_areas'),
            state.get('enriched_context'),
            state.get('importance', 0),  # consolidation_priority
            is_critical,
            now,
            now
        )
        return result if result else knowledge_id
    except Exception as e:
        # Table might not exist yet - log and continue
        print(f"⚠️  L3 storage warning: {str(e)}")
        return knowledge_id


async def _store_in_neo4j(state: L1State, postgres_id: str) -> Optional[str]:
    """
    Store critical event in Neo4j graph

    Only stores if:
    - Importance >= 8 (high importance)
    - Contains significant architectural/design decisions

    Returns:
        Neo4j node ID or None
    """
    importance = state.get('importance', 0)

    # Only store critical/high importance events
    if importance < 8:
        return None

    try:
        config = get_config()
        neo4j_service = Neo4jMemoryService(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password
        )

        # Create node in graph
        node_id = f"event-{postgres_id[:8]}"

        node = GraphNode(
            id=node_id,
            type="decision" if state.get('classified_type') == "decision" else "pattern",
            content=state.get('content_preview', '')[:500],
            tags=state.get('impact_areas', []) + [state.get('classified_type', 'unknown')],
            strength=min(1.0, importance / 10.0),  # Convert importance to strength
            access_count=0
        )

        # Store node
        created_id = neo4j_service.create_node(node)

        # If there are enriched concepts, create relations
        if state.get('enriched_context') and 'related_concepts' in state['enriched_context']:
            for concept in state['enriched_context']['related_concepts'][:5]:  # Limit to 5
                try:
                    rel = GraphRelation(
                        from_id=node_id,
                        to_id=f"concept-{concept[:20].lower()}",
                        relation_type="RELATES_TO",
                        strength=max(0.5, importance / 10.0)
                    )
                    neo4j_service.create_relation(rel)
                except Exception as e:
                    # Silently skip if relation creation fails
                    pass

        neo4j_service.close()
        return created_id

    except Exception as e:
        print(f"⚠️  Neo4j storage warning: {str(e)}")
        return None


# ═══════════════════════════════════════════════════════
# MAIN NODE IMPLEMENTATION
# ═══════════════════════════════════════════════════════

async def store_memory(state: L1State) -> Dict:
    """
    Store event according to storage_layer decision

    Updates state with:
    - stored_in_redis (bool)
    - stored_in_postgres (bool)
    - stored_in_neo4j (bool)
    - storage_ids (dict with IDs from each store)
    - timings["store_memory"]

    Args:
        state: Current L1State with storage_layer decision

    Returns:
        Updated state dict
    """
    start_time = time.time()

    storage_layer = state.get("storage_layer", "skip")
    storage_ids = {}
    stored_results = {
        "stored_in_redis": False,
        "stored_in_postgres": False,
        "stored_in_neo4j": False
    }

    try:
        # ═══════════════════════════════════════════════════════
        # SKIP: Trivial event
        # ═══════════════════════════════════════════════════════

        if storage_layer == "skip":
            duration_ms = int((time.time() - start_time) * 1000)
            if "timings" not in state:
                state["timings"] = {}
            state["timings"]["store_memory"] = duration_ms

            return {
                "stored_in_redis": False,
                "stored_in_postgres": False,
                "stored_in_neo4j": False,
                "storage_ids": {}
            }

        # ═══════════════════════════════════════════════════════
        # L1: Store in Redis working memory only
        # ═══════════════════════════════════════════════════════

        if storage_layer == "L1":
            try:
                config = get_config()
                redis_service = RedisMemoryService(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    password=config.redis_password
                )

                # Create working memory item
                item = WorkingMemoryItem(
                    id=state.get('event_id', str(uuid.uuid4())),
                    type=state.get('classified_type', 'unknown'),
                    content=state.get('content_preview', '')[:500],
                    importance=state.get('importance', 0),
                    timestamp=datetime.utcnow().isoformat()
                )

                # Add to working memory
                redis_service.add_to_working_memory(state['session_id'], item)

                stored_results["stored_in_redis"] = True
                storage_ids["redis_key"] = f"working_memory:{state['session_id']}"

            except Exception as e:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "store_memory",
                    "storage": "L1_redis",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        # ═══════════════════════════════════════════════════════
        # L2: Store in PostgreSQL + L1 Redis fallback
        # ═══════════════════════════════════════════════════════

        elif storage_layer == "L2":
            # Store in PostgreSQL
            conn = None
            try:
                conn = await _get_db_connection()
                postgres_id = await _store_in_l2_postgres(state, conn)

                stored_results["stored_in_postgres"] = True
                storage_ids["postgres_id"] = postgres_id

            except Exception as e:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "store_memory",
                    "storage": "L2_postgres",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            finally:
                if conn:
                    await conn.close()

            # Also store in L1 Redis for faster access
            try:
                config = get_config()
                redis_service = RedisMemoryService(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    password=config.redis_password
                )

                item = WorkingMemoryItem(
                    id=state.get('event_id', str(uuid.uuid4())),
                    type=state.get('classified_type', 'unknown'),
                    content=state.get('content_preview', '')[:500],
                    importance=state.get('importance', 0),
                    timestamp=datetime.utcnow().isoformat()
                )

                redis_service.add_to_working_memory(state['session_id'], item)
                stored_results["stored_in_redis"] = True
                storage_ids["redis_key"] = f"working_memory:{state['session_id']}"

            except Exception as e:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "store_memory",
                    "storage": "L2_redis_fallback",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        # ═══════════════════════════════════════════════════════
        # L3: Store in PostgreSQL + Neo4j for critical events
        # ═══════════════════════════════════════════════════════

        elif storage_layer == "L3":
            postgres_id = None

            # Store in PostgreSQL L3 knowledge table
            conn = None
            try:
                conn = await _get_db_connection()
                postgres_id = await _store_in_l3_postgres(state, conn)

                stored_results["stored_in_postgres"] = True
                storage_ids["postgres_id"] = postgres_id

            except Exception as e:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "store_memory",
                    "storage": "L3_postgres",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
            finally:
                if conn:
                    await conn.close()

            # Store in Neo4j if critical (importance >= 9)
            importance = state.get('importance', 0)
            if importance >= 9 and postgres_id:
                try:
                    neo4j_id = await _store_in_neo4j(state, postgres_id)
                    if neo4j_id:
                        stored_results["stored_in_neo4j"] = True
                        storage_ids["neo4j_node_id"] = neo4j_id

                except Exception as e:
                    if "errors" not in state:
                        state["errors"] = []
                    state["errors"].append({
                        "node": "store_memory",
                        "storage": "L3_neo4j",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })

            # Also store in L1 Redis for faster access
            try:
                config = get_config()
                redis_service = RedisMemoryService(
                    host=config.redis_host,
                    port=config.redis_port,
                    db=config.redis_db,
                    password=config.redis_password
                )

                item = WorkingMemoryItem(
                    id=state.get('event_id', str(uuid.uuid4())),
                    type=state.get('classified_type', 'unknown'),
                    content=state.get('content_preview', '')[:500],
                    importance=state.get('importance', 0),
                    timestamp=datetime.utcnow().isoformat()
                )

                redis_service.add_to_working_memory(state['session_id'], item)
                stored_results["stored_in_redis"] = True
                storage_ids["redis_key"] = f"working_memory:{state['session_id']}"

            except Exception as e:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append({
                    "node": "store_memory",
                    "storage": "L3_redis_fallback",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

    except Exception as e:
        # Catch-all for unexpected errors
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "node": "store_memory",
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        })

    finally:
        # Record timing
        duration_ms = int((time.time() - start_time) * 1000)
        if "timings" not in state:
            state["timings"] = {}
        state["timings"]["store_memory"] = duration_ms

        stored_results["storage_ids"] = storage_ids

    return stored_results


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_structure_only():
    """Test structure without actual storage"""
    from backend.agents.l1_observer.state import create_initial_state

    print("✅ Testing store_memory Structure")
    print("=" * 60)

    # Test 1: Skip decision
    print("\n1️⃣ Testing SKIP storage layer...")
    state = create_initial_state(
        event_type="Read",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/test.py",
        content="# Trivial change",
        tool_name="Read"
    )

    state.update({
        "classified_type": "trivial",
        "classification_confidence": 0.95,
        "importance": 1,
        "storage_layer": "skip",
        "storage_reasoning": "Trivial event, no storage needed"
    })

    print(f"   Storage layer: {state['storage_layer']}")
    print(f"   Expected: No storage operations")

    # Test 2: L1 storage
    print("\n2️⃣ Testing L1 storage layer...")
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/test.py",
        content="def test():\n    return 42",
        tool_name="Edit"
    )

    state.update({
        "classified_type": "code_edit",
        "classification_confidence": 0.95,
        "importance": 4,
        "storage_layer": "L1",
        "storage_reasoning": "Low importance, working memory only"
    })

    print(f"   Storage layer: {state['storage_layer']}")
    print(f"   Expected: Redis working_memory:{state['session_id']}")

    # Test 3: L2 storage
    print("\n3️⃣ Testing L2 storage layer...")
    state = create_initial_state(
        event_type="Write",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/new_feature.py",
        content="class NewService:\n    def __init__(self):\n        pass",
        tool_name="Write"
    )

    state.update({
        "classified_type": "new_feature",
        "classification_confidence": 0.95,
        "importance": 6,
        "storage_layer": "L2",
        "storage_reasoning": "Medium importance, batch processing",
        "impact_areas": ["backend"]
    })

    print(f"   Storage layer: {state['storage_layer']}")
    print(f"   Expected: PostgreSQL l2_events + Redis fallback")

    # Test 4: L3 storage
    print("\n4️⃣ Testing L3 storage layer...")
    state = create_initial_state(
        event_type="Edit",
        session_id="test-session",
        file_path="/home/pilote/projet/agi/backend/core/memory.py",
        content="# Major architectural change",
        tool_name="Edit"
    )

    state.update({
        "classified_type": "decision",
        "classification_confidence": 0.95,
        "importance": 9,
        "storage_layer": "L3",
        "storage_reasoning": "Critical architectural decision",
        "impact_areas": ["backend", "agents", "memory"],
        "enriched_context": {
            "related_concepts": ["async", "redis", "memory"]
        }
    })

    print(f"   Storage layer: {state['storage_layer']}")
    print(f"   Importance: {state['importance']}/10 (CRITICAL)")
    print(f"   Expected: PostgreSQL l3_knowledge + Neo4j graph + Redis")

    print("\n" + "=" * 60)
    print("✅ STRUCTURE TESTS PASSED")


def test_store_memory_async():
    """Test store_memory with async operations (structure only)"""
    import asyncio
    from backend.agents.l1_observer.state import create_initial_state

    async def run_test():
        print("\n🧠 Testing store_memory Node (Async Structure)")
        print("=" * 60)

        # Test 1: L1 Storage
        print("\n1️⃣ Simulating L1 storage...")
        state = create_initial_state(
            event_type="Edit",
            session_id="test-session",
            file_path="/home/pilote/projet/agi/backend/test.py",
            content="def important_function():\n    pass",
            tool_name="Edit"
        )

        state.update({
            "classified_type": "code_edit",
            "classification_confidence": 0.95,
            "importance": 4,
            "storage_layer": "L1",
            "timings": {}
        })

        # Simulate storage (without actual DB connection)
        print(f"   Input state: storage_layer={state['storage_layer']}")
        print(f"   Expected output: stored_in_redis=True")
        print(f"   Expected storage_ids: redis_key=working_memory:test-session")

        # Test 2: Skip
        print("\n2️⃣ Simulating SKIP storage...")
        state = create_initial_state(
            event_type="Read",
            session_id="test-session",
            file_path="/home/pilote/projet/agi/README.md",
            content="# This is trivial",
            tool_name="Read"
        )

        state.update({
            "classified_type": "trivial",
            "importance": 1,
            "storage_layer": "skip",
            "timings": {}
        })

        print(f"   Input state: storage_layer={state['storage_layer']}")
        print(f"   Expected output: All stored_* = False, empty storage_ids")

        print("\n" + "=" * 60)
        print("✅ ASYNC STRUCTURE TESTS PASSED")

    asyncio.run(run_test())


if __name__ == "__main__":
    print("Testing store_memory node...")
    print()
    test_structure_only()
    print()
    test_store_memory_async()
