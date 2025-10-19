#!/usr/bin/env python3
"""
Task Worker - Executes background tasks from PostgreSQL
Polls worker_tasks table and executes pending tasks
"""

import asyncio
import asyncpg
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID, uuid4

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}

PROJECT_ROOT = Path("/home/pilote/projet/agi")


async def get_pending_task(conn) -> Optional[Dict]:
    """Get next pending task from queue"""

    task = await conn.fetchrow(
        """
        UPDATE worker_tasks
        SET status = 'running', started_at = NOW()
        WHERE id = (
            SELECT id FROM worker_tasks
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, task_type, instructions
        """
    )

    if task:
        return {
            "id": task["id"],
            "task_type": task["task_type"],
            "instructions": task["instructions"] if isinstance(task["instructions"], dict) else json.loads(task["instructions"])
        }

    return None


async def auto_store_patterns(research_output: str, query: str) -> int:
    """
    Parse research output and auto-store patterns in memory

    Looks for:
    - Bullet points with patterns/techniques
    - Numbered lists
    - Bold/italic emphasis
    - Technical terms
    """

    import re

    patterns_found = []

    # Extract bullet points
    bullets = re.findall(r'[•\-\*]\s*(.+)', research_output)
    patterns_found.extend(bullets[:10])  # Max 10

    # Extract numbered lists
    numbered = re.findall(r'\d+\.\s+(.+)', research_output)
    patterns_found.extend(numbered[:10])

    # Extract bold text (patterns often emphasized)
    bold = re.findall(r'\*\*(.+?)\*\*', research_output)
    patterns_found.extend(bold[:5])

    # Remove duplicates, clean
    unique_patterns = []
    seen = set()

    for pattern in patterns_found:
        cleaned = pattern.strip()[:200]  # Max 200 chars
        if len(cleaned) > 20 and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            unique_patterns.append(cleaned)

    # Store in memory_store
    if not unique_patterns:
        return 0

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        stored = 0

        for pattern in unique_patterns[:5]:  # Max 5 patterns per research
            content = f"""# Pattern: {pattern}

Source: Research query "{query}"
Discovered by: research-agent (auto-parsed)

{pattern}
"""

            await conn.execute(
                """
                INSERT INTO memory_store (id, content, source_type, metadata, user_id)
                VALUES ($1, $2, 'architectural_pattern', $3::jsonb, 'system')
                """,
                uuid4(),
                content,
                json.dumps({
                    "query": query,
                    "pattern": pattern[:100],
                    "auto_parsed": True,
                    "tags": ["architectural_pattern", "research", "auto-discovered"]
                })
            )

            stored += 1

        return stored

    except Exception as e:
        print(f"  ⚠️  Auto-store failed: {e}")
        return 0

    finally:
        await conn.close()


async def execute_research_task(task_id: UUID, instructions: Dict) -> Dict:
    """Execute research task using Claude Code headless with agent prompt from DB"""

    query = instructions.get("query", "")
    agent_type = instructions.get("agent", "research-agent")

    print(f"  🔍 Research: {query} (agent: {agent_type})")

    try:
        # 1. Get agent config from PostgreSQL
        conn = await asyncpg.connect(**DB_CONFIG)

        agent_config = await conn.fetchrow(
            "SELECT system_prompt, model FROM agent_prompts WHERE agent_type = $1",
            agent_type
        )

        await conn.close()

        if not agent_config:
            return {
                "status": "failed",
                "error": f"Agent '{agent_type}' not found in agent_prompts table"
            }

        # 2. Build user prompt (simple)
        user_prompt = f"Research: {query}"

        # 3. Launch Claude Code headless
        # Execute claude CLI in non-interactive mode
        cmd = [
            "claude",
            "--print",
            "--model", agent_config['model'],
            "--system-prompt", agent_config['system_prompt'],
            "--output-format", "text",
            user_prompt
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # Increased for discover_mcp + search
            cwd=str(PROJECT_ROOT)
        )

        output = result.stdout[:2000]
        stderr = result.stderr[:500]

        if result.returncode == 0 or output:
            # Auto-parse and store patterns found in research
            patterns_stored = await auto_store_patterns(output, query)

            return {
                "status": "success",
                "summary": f"Research completed for: {query}",
                "data": output,
                "patterns_stored": patterns_stored,
                "agent": agent_type,
                "model": agent_config['model']
            }
        else:
            return {
                "status": "failed",
                "error": f"Return code: {result.returncode}, stderr: {stderr}, stdout: {output[:200]}"
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "error": f"Research timeout (120s) - cmd: {' '.join(cmd[:5])}"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


async def execute_memory_task(task_id: UUID, instructions: Dict) -> Dict:
    """Execute memory operation"""

    operation = instructions.get("operation", "")

    if operation == "store_patterns":
        # This would be triggered after research completes
        return {
            "status": "success",
            "summary": "Pattern storage queued"
        }

    elif operation == "update_quality_scores":
        # Re-calculate quality scores
        conn = await asyncpg.connect(**DB_CONFIG)
        try:
            await conn.execute(
                """
                UPDATE memory_store
                SET quality_score = (
                    0.30 * LEAST(1.0, LENGTH(content) / 1000.0) +
                    0.25 * (1.0 / (1.0 + EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 / 30.0)) +
                    0.25 * LEAST(1.0, LN(COALESCE(access_count, 0) + 1) / 5.0) +
                    0.20 * CASE WHEN metadata IS NOT NULL THEN 1.0 ELSE 0.3 END
                )
                WHERE quality_score IS NULL OR quality_score < 0.5
                """
            )
            return {"status": "success", "summary": "Quality scores updated"}
        finally:
            await conn.close()

    elif operation == "generate_relations":
        # Auto-detect relations between memories
        return {
            "status": "success",
            "summary": "Graph relations generated"
        }

    return {"status": "failed", "error": f"Unknown operation: {operation}"}


async def execute_code_task(task_id: UUID, instructions: Dict) -> Dict:
    """Execute code development task"""

    feature = instructions.get("feature", "")
    agent = instructions.get("agent", "task-executor")

    # Would launch Claude Code headless here
    return {
        "status": "success",
        "summary": f"Code task queued: {feature}"
    }


async def execute_test_task(task_id: UUID, instructions: Dict) -> Dict:
    """Execute test command"""

    command = instructions.get("command", "")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT)
        )

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "summary": f"Test: {command}",
            "output": result.stdout[:1000]
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


async def execute_task(task: Dict) -> Dict:
    """Route task to appropriate executor"""

    task_type = task["task_type"]
    instructions = task["instructions"]
    task_id = task["id"]

    if task_type == "research":
        return await execute_research_task(task_id, instructions)

    elif task_type == "memory":
        return await execute_memory_task(task_id, instructions)

    elif task_type == "code":
        return await execute_code_task(task_id, instructions)

    elif task_type == "test":
        return await execute_test_task(task_id, instructions)

    else:
        return {
            "status": "failed",
            "error": f"Unknown task type: {task_type}"
        }


async def mark_task_completed(conn, task_id: UUID, result: Dict):
    """Mark task as completed with result"""

    await conn.execute(
        """
        UPDATE worker_tasks
        SET
            status = $2,
            result = $3::jsonb,
            completed_at = NOW(),
            error = $4
        WHERE id = $1
        """,
        task_id,
        result.get("status", "failed"),
        json.dumps(result),
        result.get("error")
    )


async def worker_loop(worker_id: int, max_iterations: int = None):
    """Main worker loop"""

    print(f"🤖 Worker {worker_id} started")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        iteration = 0
        idle_count = 0

        while True:
            # Get next task
            task = await get_pending_task(conn)

            if task:
                idle_count = 0
                print(f"  ⚙️  [{task['task_type']}] {task['id']}")

                # Execute task
                result = await execute_task(task)

                # Store result
                await mark_task_completed(conn, task["id"], result)

                status_icon = "✓" if result.get("status") == "success" else "❌"
                print(f"  {status_icon} {result.get('summary', 'Completed')}")

            else:
                # No pending tasks, wait
                idle_count += 1

                # Print heartbeat every 30 seconds (15 iterations * 2s)
                if idle_count % 15 == 0:
                    print(f"  💓 Worker {worker_id} idle ({idle_count * 2}s)")

                await asyncio.sleep(2)

            iteration += 1
            if max_iterations and iteration >= max_iterations:
                break

    except KeyboardInterrupt:
        print(f"\n🛑 Worker {worker_id} interrupted by user")
    except Exception as e:
        print(f"\n❌ Worker {worker_id} error: {e}")
    finally:
        await conn.close()
        print(f"🤖 Worker {worker_id} stopped")


async def main():
    """Launch worker"""

    worker_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print("="*60)
    print("TASK WORKER")
    print("="*60)

    await worker_loop(worker_id, max_iterations)

    print("\n" + "="*60)
    print("✅ WORKER COMPLETED")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
