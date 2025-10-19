#!/usr/bin/env python3
"""
Launch Claude Code Headless Worker
Helper pour lancer workers en background
"""

import asyncio
import asyncpg
import json
import subprocess
from uuid import uuid4
from typing import Dict, Any

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def launch_worker(task_type: str, instructions: Dict[str, Any]) -> str:
    """
    Launch headless worker for task

    Args:
        task_type: Type of task (research, code, test, install, memory)
        instructions: Task instructions dict

    Returns:
        task_id: UUID of created task
    """

    # Connect to DB
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Store task in DB
        task_id = await conn.fetchval(
            """
            INSERT INTO worker_tasks (task_type, instructions, status)
            VALUES ($1, $2, 'pending')
            RETURNING id
            """,
            task_type,
            json.dumps(instructions)
        )

        task_id = str(task_id)

        print(f"Created task {task_id}")

        # Launch worker process (detached)
        subprocess.Popen(
            ["python3", "/home/pilote/projet/agi/cortex/headless_worker.py", task_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        print(f"Launched worker for task {task_id}")

        return task_id

    finally:
        await conn.close()


async def check_task_status(task_id: str) -> Dict[str, Any]:
    """Check task status and result"""

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        task = await conn.fetchrow(
            "SELECT * FROM worker_tasks WHERE id = $1",
            task_id
        )

        if not task:
            return {"error": "Task not found"}

        return {
            "id": str(task["id"]),
            "task_type": task["task_type"],
            "status": task["status"],
            "result": task["result"],
            "error": task["error"],
            "created_at": task["created_at"].isoformat() if task["created_at"] else None,
            "completed_at": task["completed_at"].isoformat() if task["completed_at"] else None
        }

    finally:
        await conn.close()


async def main():
    """Example usage"""

    # Launch research task
    task_id = await launch_worker(
        "research",
        {
            "query": "Latest vector database optimizations 2025",
            "sources": ["exa", "docs"],
            "output_format": "summary"
        }
    )

    print(f"Task launched: {task_id}")

    # Wait a bit
    await asyncio.sleep(2)

    # Check status
    status = await check_task_status(task_id)
    print(f"Status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
