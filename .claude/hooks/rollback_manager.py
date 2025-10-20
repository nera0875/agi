#!/usr/bin/env python3
"""
Rollback Manager - Orchestrates git rollback on agent/test failures
Integrates with agent execution pipeline and test runners
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path("/home/pilote/projet/agi")
HOOK_SCRIPT = PROJECT_ROOT / ".claude" / "hooks" / "git_rollback_on_error.sh"
ROLLBACK_LOG = PROJECT_ROOT / ".claude" / "meta" / "rollback.log"


class RollbackMode:
    """Rollback modes"""
    SOFT = "soft"      # Keep changes, undo commit
    HARD = "hard"      # Discard changes, backup branch
    BRANCH = "branch"  # Restore from safety backup


class RollbackManager:
    """Manages git rollback on failures"""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or PROJECT_ROOT)
        self.hook = self.project_root / ".claude" / "hooks" / "git_rollback_on_error.sh"

    def rollback(
        self,
        error_type: str,
        error_msg: str = "Unknown error",
        mode: str = RollbackMode.SOFT,
    ) -> dict:
        """
        Execute rollback

        Args:
            error_type: "agent_fail", "test_fail", "critical_error"
            error_msg: Error description
            mode: "soft", "hard", "branch"

        Returns:
            {success, mode_used, commit_before, error, details}
        """
        if not self.hook.exists():
            return {
                "success": False,
                "error": f"Rollback hook not found: {self.hook}",
                "mode_used": mode,
            }

        try:
            result = subprocess.run(
                ["bash", str(self.hook), error_type, error_msg, mode],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            success = result.returncode == 0

            return {
                "success": success,
                "mode_used": mode,
                "error_type": error_type,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Rollback timeout (30s)",
                "mode_used": mode,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode_used": mode,
            }

    def on_agent_fail(self, agent_name: str, error: str, mode: str = RollbackMode.SOFT) -> dict:
        """Rollback if agent fails"""
        return self.rollback(
            error_type=f"agent_fail:{agent_name}",
            error_msg=error,
            mode=mode,
        )

    def on_test_fail(self, test_file: str, error: str, mode: str = RollbackMode.BRANCH) -> dict:
        """Rollback if tests fail - defaults to branch mode for safety"""
        return self.rollback(
            error_type=f"test_fail:{test_file}",
            error_msg=error,
            mode=mode,
        )

    def on_critical_error(self, error: str, mode: str = RollbackMode.HARD) -> dict:
        """Rollback on critical errors - defaults to hard mode"""
        return self.rollback(
            error_type="critical_error",
            error_msg=error,
            mode=mode,
        )

    def get_log(self) -> list:
        """Get rollback history"""
        log_path = self.project_root / ".claude" / "meta" / "rollback.log"
        if not log_path.exists():
            return []

        with open(log_path, "r") as f:
            lines = f.readlines()

        return [line.strip() for line in lines if line.strip()]

    def print_status(self) -> None:
        """Print rollback status"""
        history = self.get_log()
        print(f"\n🔄 Rollback History ({len(history)} entries):")
        for line in history[-5:]:  # Last 5 entries
            print(f"  {line}")


def main():
    """CLI usage"""
    if len(sys.argv) < 3:
        print("Usage: rollback_manager.py <error_type> <error_msg> [mode]")
        print("  error_type: agent_fail, test_fail, critical_error")
        print("  error_msg: Error description")
        print("  mode: soft (default), hard, branch")
        sys.exit(1)

    error_type = sys.argv[1]
    error_msg = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else RollbackMode.SOFT

    manager = RollbackManager()
    result = manager.rollback(error_type, error_msg, mode)

    print(f"\n✅ Rollback executed" if result["success"] else f"\n❌ Rollback failed")
    print(f"Result: {result}")

    manager.print_status()

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
