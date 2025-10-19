#!/usr/bin/env python3
"""
Claude Code Headless Worker
Lit task depuis PostgreSQL, exécute, store résultat
"""

import asyncio
import asyncpg
import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# DB Config
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def execute_task(task_id: str):
    """Execute worker task from database"""

    # Connect
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Fetch task
        task = await conn.fetchrow(
            "SELECT * FROM worker_tasks WHERE id = $1",
            task_id
        )

        if not task:
            print(f"Task {task_id} not found")
            return

        if task["status"] != "pending":
            print(f"Task {task_id} already {task['status']}")
            return

        # Mark as running
        await conn.execute(
            "UPDATE worker_tasks SET status = 'running', started_at = NOW() WHERE id = $1",
            task_id
        )

        # Get instructions
        task_type = task["task_type"]
        instructions = task["instructions"]

        print(f"Executing {task_type} task: {task_id}")

        # Execute based on type
        result = None
        error = None

        try:
            if task_type == "research":
                result = await execute_research(instructions)
            elif task_type == "code":
                result = await execute_code(instructions)
            elif task_type == "test":
                result = await execute_test(instructions)
            elif task_type == "install":
                result = await execute_install(instructions)
            elif task_type == "memory":
                result = await execute_memory(instructions)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Mark as completed
            await conn.execute(
                """
                UPDATE worker_tasks
                SET status = 'completed',
                    result = $1,
                    completed_at = NOW()
                WHERE id = $2
                """,
                json.dumps(result),
                task_id
            )

            print(f"Task {task_id} completed successfully")

        except Exception as e:
            error = str(e)
            print(f"Task {task_id} failed: {error}")

            await conn.execute(
                """
                UPDATE worker_tasks
                SET status = 'failed',
                    error = $1,
                    completed_at = NOW()
                WHERE id = $2
                """,
                error,
                task_id
            )

    finally:
        await conn.close()


async def execute_research(instructions: dict) -> dict:
    """Execute research task"""
    # TODO: Implement Exa search, doc fetching
    query = instructions.get("query")
    sources = instructions.get("sources", [])

    return {
        "query": query,
        "sources_used": sources,
        "summary": f"Research on: {query}",
        "findings": []
    }


async def execute_code(instructions: dict) -> dict:
    """Execute code implementation task"""
    # TODO: Implement code generation
    feature = instructions.get("feature")

    return {
        "feature": feature,
        "files_modified": [],
        "tests_passed": True
    }


async def execute_test(instructions: dict) -> dict:
    """Execute test task"""
    test_command = instructions.get("command")

    # Run test
    result = subprocess.run(
        test_command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=300
    )

    return {
        "command": test_command,
        "exit_code": result.returncode,
        "stdout": result.stdout[:1000],  # Limit output
        "stderr": result.stderr[:1000],
        "passed": result.returncode == 0
    }


async def execute_install(instructions: dict) -> dict:
    """Execute installation task"""
    package = instructions.get("package")
    install_type = instructions.get("type", "pip")

    if install_type == "pip":
        cmd = f"pip3 install {package}"
    elif install_type == "apt":
        cmd = f"sudo apt install -y {package}"
    else:
        raise ValueError(f"Unknown install type: {install_type}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)

    return {
        "package": package,
        "success": result.returncode == 0,
        "output": result.stdout[-500:]
    }


async def execute_memory(instructions: dict) -> dict:
    """Execute memory operation task"""
    operation = instructions.get("operation")

    if operation == "cleanup":
        # TODO: Call memory_service.cleanup_test_data()
        return {"cleaned": 0}

    elif operation == "quality_score":
        # TODO: Call memory_service.update_quality_scores()
        return {"updated": 0}

    else:
        raise ValueError(f"Unknown memory operation: {operation}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 headless_worker.py <task_id>")
        sys.exit(1)

    task_id = sys.argv[1]
    asyncio.run(execute_task(task_id))
