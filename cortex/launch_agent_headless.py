#!/usr/bin/env python3
"""
Launch Claude Code Agent in Headless Mode
Uses agent prompts from PostgreSQL instead of .md files
"""

import asyncio
import asyncpg
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def get_agent_config(agent_type: str) -> Optional[Dict[str, Any]]:
    """Fetch agent configuration from PostgreSQL"""
    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        row = await conn.fetchrow(
            "SELECT * FROM agent_prompts WHERE agent_type = $1",
            agent_type
        )

        if not row:
            return None

        return {
            "agent_type": row["agent_type"],
            "system_prompt": row["system_prompt"],
            "model": row["model"],
            "tools": list(row["tools"]) if row["tools"] else []
        }
    finally:
        await conn.close()


async def launch_agent_headless(
    agent_type: str,
    task_prompt: str,
    output_file: Optional[str] = None
) -> Dict[str, str]:
    """
    Launch Claude Code agent in headless mode

    Args:
        agent_type: Type of agent (research-agent, task-executor, etc.)
        task_prompt: Specific task instructions for this run
        output_file: Optional file to capture output (default: /tmp/<agent>_<uuid>.json)

    Returns:
        Dict with process_id and output_file path
    """

    # Get agent config from DB
    config = await get_agent_config(agent_type)
    if not config:
        raise ValueError(f"Agent type '{agent_type}' not found in database")

    # Generate output file
    if not output_file:
        import uuid
        output_file = f"/tmp/{agent_type}_{uuid.uuid4().hex[:8]}.json"

    # Build full prompt
    full_prompt = f"""
{config['system_prompt']}

TASK:
{task_prompt}

OUTPUT FORMAT:
Return result as JSON with structure:
{{
  "success": true/false,
  "result": <your result>,
  "error": <error if failed>
}}
"""

    # Write prompt to temp file
    prompt_file = f"/tmp/prompt_{Path(output_file).stem}.txt"
    Path(prompt_file).write_text(full_prompt)

    # Launch claude code headless
    cmd = [
        "claude", "code",
        "--model", f"claude-{config['model']}",
        "--prompt-file", prompt_file,
        "--output-file", output_file
    ]

    # Launch detached process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

    print(f"[LAUNCHED] {agent_type} (PID: {process.pid})")
    print(f"  Model: {config['model']}")
    print(f"  Output: {output_file}")

    return {
        "process_id": str(process.pid),
        "output_file": output_file,
        "agent_type": agent_type,
        "model": config["model"]
    }


async def check_agent_output(output_file: str) -> Optional[Dict[str, Any]]:
    """Check if agent has completed and return result"""

    output_path = Path(output_file)

    if not output_path.exists():
        return {"status": "running", "result": None}

    try:
        content = output_path.read_text()
        result = json.loads(content)
        return {"status": "completed", "result": result}
    except json.JSONDecodeError:
        return {"status": "running", "result": None}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def main():
    """Demo usage"""

    if len(sys.argv) < 3:
        print("Usage: python3 launch_agent_headless.py <agent-type> <task-prompt>")
        print("\nAvailable agents:")

        conn = await asyncpg.connect(**DB_CONFIG)
        agents = await conn.fetch("SELECT agent_type, model FROM agent_prompts ORDER BY agent_type")
        await conn.close()

        for agent in agents:
            print(f"  - {agent['agent_type']} ({agent['model']})")

        sys.exit(1)

    agent_type = sys.argv[1]
    task_prompt = sys.argv[2]

    # Launch agent
    result = await launch_agent_headless(agent_type, task_prompt)

    print("\n✓ Agent launched in background")
    print(f"  Check output: cat {result['output_file']}")

    # Demo: wait and check
    print("\nWaiting 5 seconds...")
    await asyncio.sleep(5)

    status = await check_agent_output(result['output_file'])
    print(f"\nStatus: {status['status']}")
    if status.get('result'):
        print(f"Result: {json.dumps(status['result'], indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
