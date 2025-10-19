#!/usr/bin/env python3
"""
DEMO: How Sonnet should orchestrate parallel work

This demonstrates the optimal pattern:
1. Launch multiple background tasks
2. Continue doing useful work
3. Poll results when ready
"""

import subprocess
import time
import json
from pathlib import Path


def launch_background_task(script: str, args: list, log_file: str) -> subprocess.Popen:
    """Launch a background task, return process"""
    cmd = ["python3", script] + args
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent.parent
        )
    return proc


def main():
    """Demonstration of optimal orchestration"""

    print("=" * 60)
    print("ORCHESTRATOR DEMO - Parallel Work Pattern")
    print("=" * 60)

    # Step 1: Launch multiple background tasks (simulate 3 MCP installations)
    print("\n[1] Launching 3 background tasks...")

    processes = []
    mcp_configs = [
        ("test-mcp-1", '{"command": "echo", "args": ["test1"]}'),
        ("test-mcp-2", '{"command": "echo", "args": ["test2"]}'),
        ("test-mcp-3", '{"command": "echo", "args": ["test3"]}'),
    ]

    for mcp_name, config in mcp_configs:
        log_file = f"/tmp/install_{mcp_name}.log"
        proc = launch_background_task(
            "workers/install_mcp.py",
            [mcp_name, config],
            log_file
        )
        processes.append((mcp_name, proc, log_file))
        print(f"  ✓ Launched: {mcp_name} (PID: {proc.pid})")

    # Step 2: DO USEFUL WORK while background tasks run
    print("\n[2] Doing useful work while tasks run in background...")
    print("  - Update documentation")
    print("  - Store patterns in memory")
    print("  - Analyze codebase")
    print("  - Prepare next tasks")

    # Simulate work (in reality, Sonnet would use Read, Write, memory_store, etc)
    time.sleep(2)

    # Step 3: Poll results (check if tasks finished)
    print("\n[3] Polling background tasks...")

    results = []
    for mcp_name, proc, log_file in processes:
        # Check if process finished
        returncode = proc.poll()

        if returncode is None:
            # Still running, wait a bit more
            print(f"  ⏳ {mcp_name}: still running, waiting...")
            proc.wait(timeout=10)
            returncode = proc.returncode

        # Read result
        result_file = f"/tmp/mcp_install_{mcp_name}.json"
        if Path(result_file).exists():
            with open(result_file) as f:
                result = json.load(f)
            status = "✓" if result["status"] == "success" else "✗"
            print(f"  {status} {mcp_name}: {result['status']}")
            results.append(result)
        else:
            print(f"  ✗ {mcp_name}: no result file")

    # Step 4: Synthesize results
    print("\n[4] Synthesis:")
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"  Total: {len(results)} tasks")
    print(f"  Success: {success_count}")
    print(f"  Failed: {len(results) - success_count}")

    print("\n" + "=" * 60)
    print("PATTERN: Launch → Work → Poll → Synthesize")
    print("BENEFIT: Zero blocking time, maximum efficiency")
    print("=" * 60)


if __name__ == "__main__":
    main()
