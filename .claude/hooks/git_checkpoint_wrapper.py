#!/usr/bin/env python3
"""
Git Checkpoint Wrapper for Agent Task Orchestrator
Integrates git_post_task_checkpoint.sh into agent workflow
"""

import subprocess
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class GitCheckpointManager:
    """Manages git checkpoints after agent tasks"""

    def __init__(self, project_root: str = "/home/pilote/projet/agi"):
        self.project_root = Path(project_root)
        self.hook_script = self.project_root / ".claude" / "hooks" / "git_post_task_checkpoint.sh"
        self.checkpoint_log = self.project_root / ".claude" / "hooks" / ".checkpoint_log"

    def create_checkpoint(
        self,
        task_name: str,
        agent_type: str,
        status: str = "success",
        task_id: Optional[str] = None
    ) -> dict:
        """
        Create atomic git checkpoint after task completion

        Args:
            task_name: Name of the completed task
            agent_type: Type of agent (ask, code, frontend, debug, etc)
            status: Task status (success, partial, failed)
            task_id: Optional unique task identifier

        Returns:
            dict with checkpoint result
        """
        if not task_id:
            task_id = str(uuid.uuid4())

        if status != "success":
            return {
                "status": "skipped",
                "reason": f"Task status is {status}, not creating checkpoint",
                "task_name": task_name,
                "task_id": task_id
            }

        # Verify hook script exists
        if not self.hook_script.exists():
            return {
                "status": "error",
                "reason": "Hook script not found",
                "hook_path": str(self.hook_script)
            }

        try:
            # Run checkpoint script
            result = subprocess.run(
                [
                    "bash",
                    str(self.hook_script),
                    task_name,
                    status,
                    agent_type,
                    task_id
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )

            # Parse output
            output = result.stdout + result.stderr
            success = result.returncode == 0

            checkpoint_result = {
                "status": "complete" if success else "failed",
                "task_name": task_name,
                "agent_type": agent_type,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "returncode": result.returncode,
                "output": output.strip()
            }

            # Log checkpoint
            self._log_checkpoint(checkpoint_result)

            return checkpoint_result

        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "task_name": task_name,
                "timeout_seconds": 30
            }
        except Exception as e:
            return {
                "status": "error",
                "task_name": task_name,
                "error": str(e)
            }

    def _log_checkpoint(self, checkpoint_data: dict) -> None:
        """Log checkpoint to local log file"""
        try:
            # Append to checkpoint log
            with open(self.checkpoint_log, "a") as f:
                f.write(json.dumps(checkpoint_data) + "\n")
        except Exception as e:
            print(f"Warning: Could not log checkpoint: {e}", file=sys.stderr)

    def get_recent_checkpoints(self, limit: int = 10) -> list:
        """Get recent checkpoints"""
        if not self.checkpoint_log.exists():
            return []

        try:
            with open(self.checkpoint_log, "r") as f:
                lines = f.readlines()[-limit:]
                return [json.loads(line.strip()) for line in lines if line.strip()]
        except Exception as e:
            print(f"Warning: Could not read checkpoints: {e}", file=sys.stderr)
            return []


def main():
    """CLI interface for git checkpoint"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Git checkpoint manager for agent tasks"
    )
    parser.add_argument("task_name", help="Name of the task")
    parser.add_argument("--agent", default="generic", help="Type of agent")
    parser.add_argument("--status", default="success", help="Task status")
    parser.add_argument("--task-id", help="Unique task ID")
    parser.add_argument("--project-root", default="/home/pilote/projet/agi", help="Project root")
    parser.add_argument("--show-recent", type=int, help="Show N recent checkpoints")

    args = parser.parse_args()

    manager = GitCheckpointManager(args.project_root)

    if args.show_recent:
        checkpoints = manager.get_recent_checkpoints(args.show_recent)
        for cp in checkpoints:
            print(json.dumps(cp, indent=2))
    else:
        result = manager.create_checkpoint(
            task_name=args.task_name,
            agent_type=args.agent,
            status=args.status,
            task_id=args.task_id
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
