#!/usr/bin/env python3
"""
Auto-Continue System
AGI predicts next action and continues automatically
"""

import asyncio
import asyncpg
import json
from typing import Dict, List, Optional

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def analyze_current_state() -> Dict:
    """Analyze what's done, what's next"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Check system state
        tables_status = {}

        # Memory store count
        tables_status["memory_patterns"] = await conn.fetchval(
            "SELECT COUNT(*) FROM memory_store WHERE source_type = 'architectural_pattern'"
        )

        # Agent configs
        tables_status["agents_configured"] = await conn.fetchval(
            "SELECT COUNT(*) FROM agent_prompts"
        )

        # Knowledge sections
        tables_status["knowledge_sections"] = await conn.fetchval(
            "SELECT COUNT(*) FROM agi_knowledge"
        )

        # Recent tasks
        tables_status["recent_tasks"] = await conn.fetchval(
            """
            SELECT COUNT(*) FROM worker_tasks
            WHERE created_at > NOW() - INTERVAL '1 hour'
            """
        )

        # Completed vs pending
        pending = await conn.fetchval(
            "SELECT COUNT(*) FROM worker_tasks WHERE status = 'pending'"
        )
        completed = await conn.fetchval(
            "SELECT COUNT(*) FROM worker_tasks WHERE status = 'completed'"
        )

        tables_status["tasks_pending"] = pending
        tables_status["tasks_completed"] = completed

        return tables_status

    finally:
        await conn.close()


async def predict_next_action(current_state: Dict) -> Dict:
    """
    Predict next best action based on system state

    Logic:
    1. If memory < 20 patterns → Research + store more patterns
    2. If agents not tested live → Test real agent execution
    3. If no use case → Build first real use case
    4. Default → Optimize existing system
    """

    # Decision tree
    if current_state["memory_patterns"] < 20:
        return {
            "action": "research_and_store_patterns",
            "reason": "Memory has only {} patterns, need more architectural knowledge".format(
                current_state["memory_patterns"]
            ),
            "tasks": [
                {
                    "type": "research",
                    "query": "Advanced RAG patterns 2025",
                    "agent": "research-agent"
                },
                {
                    "type": "research",
                    "query": "Agent orchestration patterns",
                    "agent": "research-agent"
                },
                {
                    "type": "memory",
                    "operation": "store_patterns"
                }
            ],
            "priority": 100
        }

    elif current_state["tasks_completed"] == 0:
        return {
            "action": "test_real_agent_execution",
            "reason": "No completed tasks yet, need to validate agents work",
            "tasks": [
                {
                    "type": "test",
                    "command": "python3 cortex/test_full_workflow.py",
                    "agent": "task-executor"
                }
            ],
            "priority": 95
        }

    else:
        return {
            "action": "build_use_case",
            "reason": "System operational, time to build real use case",
            "tasks": [
                {
                    "type": "research",
                    "query": "Best business use cases for AGI memory system",
                    "agent": "research-agent"
                },
                {
                    "type": "code",
                    "feature": "Auto-documentation generator using memory",
                    "agent": "task-executor"
                }
            ],
            "priority": 90
        }


async def store_roadmap(prediction: Dict):
    """Store predicted next action in roadmap"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        await conn.execute(
            """
            INSERT INTO agi_roadmap (phase, next_actions, predicted_next, priority)
            VALUES ($1, $2::jsonb, $3, $4)
            """,
            "auto-continue",
            json.dumps(prediction["tasks"]),
            prediction["action"],
            prediction["priority"]
        )

        print(f"✓ Roadmap stored: {prediction['action']}")

    finally:
        await conn.close()


async def get_next_action() -> Optional[Dict]:
    """Get next action from roadmap"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        roadmap = await conn.fetchrow(
            """
            SELECT * FROM agi_roadmap
            WHERE status = 'active'
            ORDER BY priority DESC, created_at DESC
            LIMIT 1
            """
        )

        if not roadmap:
            return None

        next_actions = roadmap["next_actions"]
        if isinstance(next_actions, str):
            next_actions = json.loads(next_actions)

        return {
            "id": str(roadmap["id"]),
            "phase": roadmap["phase"],
            "predicted_next": roadmap["predicted_next"],
            "next_actions": next_actions,
            "priority": roadmap["priority"]
        }

    finally:
        await conn.close()


async def main():
    """Auto-continue workflow"""

    print("="*60)
    print("AUTO-CONTINUE SYSTEM")
    print("="*60)

    # Step 1: Analyze current state
    print("\n[1] Analyzing current state...")
    state = await analyze_current_state()

    print("\n  System State:")
    for key, value in state.items():
        print(f"    - {key}: {value}")

    # Step 2: Predict next action
    print("\n[2] Predicting next action...")
    prediction = await predict_next_action(state)

    print(f"\n  Predicted Action: {prediction['action']}")
    print(f"  Reason: {prediction['reason']}")
    print(f"  Priority: {prediction['priority']}")
    print(f"\n  Tasks to execute:")
    for i, task in enumerate(prediction['tasks'], 1):
        print(f"    {i}. {task['type']}: {task.get('query') or task.get('command') or task.get('feature')}")

    # Step 3: Store in roadmap
    print("\n[3] Storing in roadmap...")
    await store_roadmap(prediction)

    # Step 4: Display next session instructions
    print("\n" + "="*60)
    print("NEXT SESSION AUTO-START")
    print("="*60)
    print("\nAt next session start, run:")
    print("  python3 cortex/auto_continue.py --execute")
    print("\nOr I (AGI) will automatically:")
    print(f"  1. Load roadmap from PostgreSQL")
    print(f"  2. Execute: {prediction['action']}")
    print(f"  3. Update roadmap with progress")
    print(f"  4. Predict next action again")
    print(f"  5. LOOP infinitely")

    print("\n🔄 BOUCLE INFINIE CONFIGURÉE")


if __name__ == "__main__":
    asyncio.run(main())
