#!/usr/bin/env python3
"""
Execute Roadmap Action
Automatically execute the next predicted action
"""

import asyncio
import asyncpg
import json
from auto_continue import get_next_action, analyze_current_state, predict_next_action, store_roadmap

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def execute_research_task(task: dict) -> dict:
    """Execute research task"""

    print(f"\n  Launching research: {task['query']}")

    # Create task in worker_tasks
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        task_id = await conn.fetchval(
            """
            INSERT INTO worker_tasks (task_type, instructions, status)
            VALUES ($1, $2::jsonb, 'pending')
            RETURNING id
            """,
            "research",
            json.dumps({"query": task["query"], "agent": task.get("agent")})
        )

        print(f"    ✓ Task created: {task_id}")
        return {"task_id": str(task_id), "status": "launched"}

    finally:
        await conn.close()


async def execute_memory_task(task: dict) -> dict:
    """Execute memory operation"""

    print(f"\n  Executing memory: {task['operation']}")

    # Mock: In real implementation, would call memory_service
    return {"status": "completed", "operation": task["operation"]}


async def mark_roadmap_completed(roadmap_id: str):
    """Mark roadmap action as completed"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        await conn.execute(
            """
            UPDATE agi_roadmap
            SET status = 'completed',
                updated_at = NOW()
            WHERE id = $1
            """,
            roadmap_id
        )

    finally:
        await conn.close()


async def main():
    """Execute next action from roadmap"""

    print("="*60)
    print("EXECUTING ROADMAP")
    print("="*60)

    # Step 1: Get next action
    print("\n[1] Loading next action from roadmap...")
    next_action = await get_next_action()

    if not next_action:
        print("  ⚠️  No action in roadmap")
        print("  Running prediction...")

        state = await analyze_current_state()
        prediction = await predict_next_action(state)
        await store_roadmap(prediction)

        next_action = await get_next_action()

    print(f"\n  Action: {next_action['predicted_next']}")
    print(f"  Priority: {next_action['priority']}")
    print(f"  Tasks: {len(next_action['next_actions'])}")

    # Step 2: Execute tasks
    print("\n[2] Executing tasks...")

    results = []
    for task in next_action['next_actions']:
        task_type = task.get('type')

        if task_type == 'research':
            result = await execute_research_task(task)
            results.append(result)

        elif task_type == 'memory':
            result = await execute_memory_task(task)
            results.append(result)

        elif task_type == 'test':
            print(f"\n  Test task: {task['command']}")
            results.append({"status": "skipped", "reason": "manual test"})

        elif task_type == 'code':
            print(f"\n  Code task: {task['feature']}")
            results.append({"status": "skipped", "reason": "requires implementation"})

    # Step 3: Mark completed
    print("\n[3] Marking roadmap completed...")
    await mark_roadmap_completed(next_action['id'])
    print("  ✓ Roadmap action completed")

    # Step 4: Predict NEXT action (LOOP)
    print("\n[4] Predicting NEXT action...")
    state = await analyze_current_state()
    prediction = await predict_next_action(state)

    print(f"\n  Next predicted: {prediction['action']}")
    print(f"  Reason: {prediction['reason']}")

    await store_roadmap(prediction)

    print("\n" + "="*60)
    print("✅ CYCLE COMPLETED")
    print("="*60)
    print("\n🔄 Roadmap updated with next action")
    print("🔄 Ready for next cycle")
    print("\nRun again: python3 cortex/execute_roadmap.py")


if __name__ == "__main__":
    asyncio.run(main())
