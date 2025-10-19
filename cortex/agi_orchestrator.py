#!/usr/bin/env python3
"""
AGI Autonomous Orchestrator
Self-managing system for parallel task execution

Mental: AGI never blocks, always progressing
"""

import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class BackgroundTask:
    """Represents a task running in background"""
    task_id: str
    process: subprocess.Popen
    log_file: str
    result_file: str
    start_time: float
    task_type: str  # "worker" or "claude"


class AGIOrchestrator:
    """
    Autonomous orchestration system

    Manages parallel execution of tasks while continuing to work
    Polls results, handles errors, makes decisions
    """

    def __init__(self, work_dir: str = "/home/pilote/projet/agi"):
        self.work_dir = Path(work_dir)
        self.tasks: List[BackgroundTask] = []
        self.results: List[Dict[str, Any]] = []

    def launch_worker(self, script: str, args: List[str], task_id: str) -> BackgroundTask:
        """Launch Python worker script in background"""
        log_file = f"/tmp/{task_id}.log"
        result_file = f"/tmp/{task_id}_result.json"

        cmd = ["python3", str(self.work_dir / "cortex" / "workers" / script)] + args

        with open(log_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=self.work_dir
            )

        task = BackgroundTask(
            task_id=task_id,
            process=proc,
            log_file=log_file,
            result_file=result_file,
            start_time=time.time(),
            task_type="worker"
        )

        self.tasks.append(task)
        print(f"  🚀 Launched worker: {task_id} (PID: {proc.pid})")
        return task

    def launch_claude(self, prompt: str, task_id: str, allowed_tools: str = "") -> BackgroundTask:
        """Launch Claude headless in background"""
        log_file = f"/tmp/{task_id}.log"
        result_file = f"/tmp/{task_id}_result.json"

        cmd = [
            "claude", "-p", prompt,
            "--output-format", "json"
        ]

        if allowed_tools:
            cmd.extend(["--allowedTools", allowed_tools])

        with open(log_file, 'w') as log_f:
            with open(result_file, 'w') as result_f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=result_f,
                    stderr=log_f,
                    cwd=self.work_dir
                )

        task = BackgroundTask(
            task_id=task_id,
            process=proc,
            log_file=log_file,
            result_file=result_file,
            start_time=time.time(),
            task_type="claude"
        )

        self.tasks.append(task)
        print(f"  🧠 Launched Claude: {task_id} (PID: {proc.pid})")
        return task

    def do_useful_work(self):
        """
        AGI continues working while background tasks run

        This is where Sonnet would:
        - Update documentation
        - Store patterns in memory
        - Analyze codebase
        - Plan next steps
        """
        print("\n  💡 Doing useful work while tasks run...")
        print("     - Analyzing architecture patterns")
        print("     - Updating knowledge base")
        print("     - Planning next development phase")
        time.sleep(1)  # Simulate work

    def poll_tasks(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Poll all background tasks, collect results"""
        print("\n  📊 Polling background tasks...")

        deadline = time.time() + timeout
        completed = []

        while self.tasks and time.time() < deadline:
            for task in self.tasks[:]:  # Copy list to allow removal
                returncode = task.process.poll()

                if returncode is not None:
                    # Task finished
                    duration = int((time.time() - task.start_time) * 1000)

                    result = {
                        "task_id": task.task_id,
                        "status": "success" if returncode == 0 else "failed",
                        "returncode": returncode,
                        "duration_ms": duration,
                        "task_type": task.task_type
                    }

                    # Try to load result file
                    if Path(task.result_file).exists():
                        try:
                            with open(task.result_file) as f:
                                result["data"] = json.load(f)
                        except:
                            pass

                    completed.append(result)
                    self.results.append(result)
                    self.tasks.remove(task)

                    status_icon = "✅" if returncode == 0 else "❌"
                    print(f"     {status_icon} {task.task_id}: {result['status']} ({duration}ms)")

            if self.tasks:
                time.sleep(0.5)  # Poll every 500ms

        # Handle timeouts
        for task in self.tasks:
            task.process.kill()
            print(f"     ⏱️  {task.task_id}: TIMEOUT (killed)")
            completed.append({
                "task_id": task.task_id,
                "status": "timeout",
                "task_type": task.task_type
            })

        self.tasks.clear()
        return completed

    def synthesize(self) -> Dict[str, Any]:
        """Synthesize all results and make decisions"""
        success_count = sum(1 for r in self.results if r.get("status") == "success")
        failed_count = len(self.results) - success_count

        synthesis = {
            "total_tasks": len(self.results),
            "success": success_count,
            "failed": failed_count,
            "success_rate": success_count / len(self.results) if self.results else 0,
            "results": self.results
        }

        return synthesis


def demo():
    """Demonstration of AGI autonomous orchestration"""
    print("=" * 60)
    print("AGI AUTONOMOUS ORCHESTRATOR - Self-Development Demo")
    print("=" * 60)

    agi = AGIOrchestrator()

    # Step 1: Launch multiple background tasks
    print("\n[1] Launching parallel tasks...")
    agi.launch_worker(
        "install_mcp.py",
        ["test-parallel-1", '{"command":"echo","args":["test1"]}'],
        "mcp_install_1"
    )
    agi.launch_worker(
        "install_mcp.py",
        ["test-parallel-2", '{"command":"echo","args":["test2"]}'],
        "mcp_install_2"
    )

    # Step 2: Do useful work while tasks run
    agi.do_useful_work()

    # Step 3: Poll results
    print("\n[2] Polling results...")
    completed = agi.poll_tasks(timeout=30)

    # Step 4: Synthesize and decide
    print("\n[3] Synthesis:")
    synthesis = agi.synthesize()
    print(f"  Total: {synthesis['total_tasks']}")
    print(f"  Success: {synthesis['success']}")
    print(f"  Failed: {synthesis['failed']}")
    print(f"  Success Rate: {synthesis['success_rate']*100:.1f}%")

    print("\n" + "=" * 60)
    print("AGI PATTERN: Launch → Work → Poll → Synthesize → Decide")
    print("RESULT: Zero blocking, autonomous evolution")
    print("=" * 60)


if __name__ == "__main__":
    demo()
