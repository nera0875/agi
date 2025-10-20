"""
Git Safety Integration pour Orchestrator
Wrap agent calls avec automatic checkpoint + rollback
"""
import subprocess
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from datetime import datetime
import logging

# Setup logging
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


class GitSafetyWrapper:
    """Wrapper pour agents calls avec git safety net"""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or PROJECT_ROOT
        self.checkpoint_hook = self.project_root / ".claude/hooks/git_post_task_checkpoint.sh"
        self.rollback_hook = self.project_root / ".claude/hooks/git_rollback_on_error.sh"
        self.backup_hook = self.project_root / ".claude/hooks/git_pre_modification_backup.sh"
        self.meta_dir = self.project_root / ".claude/meta"
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def is_critical_file(self, file_path: str) -> bool:
        """
        Determine if file modification requires backup

        Args:
            file_path: Path to file being modified

        Returns:
            True if file is critical, False otherwise
        """
        critical_patterns = [
            "CLAUDE.md",
            ".claude/agents/",
            ".claude/skills/",
            ".claude/commands/",
            "backend/api/schema.py",
            "backend/services/",
            "backend/agents/",
            "cortex/agi_tools_mcp.py",
            "cortex/local_mcp_router.py",
            "cortex/consolidation.py",
            "cortex/agi_orchestrator.py",
        ]

        for pattern in critical_patterns:
            if pattern in file_path:
                return True
        return False

    def create_backup(self, task_name: str, file_path: str = "") -> bool:
        """
        Create git backup before modification

        Args:
            task_name: Name of the task for logging
            file_path: Path to file being modified

        Returns:
            True if backup created, False if skipped/failed
        """
        try:
            result = subprocess.run(
                ["bash", str(self.backup_hook), file_path or "."],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"[GitSafety] Backup created for {task_name}")
                return True
            else:
                logger.warning(f"[GitSafety] Backup skipped: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"[GitSafety] Backup timeout for {task_name}")
            return False
        except Exception as e:
            logger.error(f"[GitSafety] Backup failed: {e}")
            return False

    def create_checkpoint(self, task_name: str, agent_type: str,
                         task_status: str = "success", task_id: str = "") -> bool:
        """
        Create git checkpoint after task completion

        Args:
            task_name: Name of the task
            agent_type: Type of agent (code, frontend, debug, etc)
            task_status: Status of task (success, failed, etc)
            task_id: Optional task ID

        Returns:
            True if checkpoint created, False if skipped/failed
        """
        if task_status != "success":
            logger.info(f"[GitSafety] Checkpoint skipped (status={task_status})")
            return False

        try:
            result = subprocess.run(
                [
                    "bash", str(self.checkpoint_hook),
                    task_name, task_status, agent_type, task_id or ""
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"[GitSafety] Checkpoint created for {task_name}")
                return True
            else:
                logger.warning(f"[GitSafety] Checkpoint failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"[GitSafety] Checkpoint timeout for {task_name}")
            return False
        except Exception as e:
            logger.error(f"[GitSafety] Checkpoint error: {e}")
            return False

    def rollback(self, error_type: str, error_msg: str = "",
                rollback_mode: str = "soft") -> bool:
        """
        Rollback git state on error

        Args:
            error_type: Type of error (agent_fail, test_fail, critical_error)
            error_msg: Error message for logging
            rollback_mode: Rollback strategy (soft, hard, branch)

        Returns:
            True if rollback executed, False if failed
        """
        try:
            result = subprocess.run(
                [
                    "bash", str(self.rollback_hook),
                    error_type, error_msg or "No message", rollback_mode
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"[GitSafety] Rollback ({rollback_mode}) executed for {error_type}")
                return True
            else:
                logger.error(f"[GitSafety] Rollback failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error(f"[GitSafety] Rollback timeout")
            return False
        except Exception as e:
            logger.error(f"[GitSafety] Rollback error: {e}")
            return False

    def with_safety(self, agent_fn: Callable, task_name: str, agent_type: str,
                   critical: bool = False, file_path: str = "",
                   rollback_on_error: bool = True) -> Tuple[Any, bool, Optional[str]]:
        """
        Execute agent function with safety net (backup + checkpoint + rollback)

        Args:
            agent_fn: Async function or callable agent to execute
            task_name: Name of the task
            agent_type: Type of agent (code, frontend, debug, etc)
            critical: If True, backup before execution
            file_path: Path to file being modified (for backup decision)
            rollback_on_error: If True, rollback on error

        Returns:
            Tuple[result, success, error_message]
            - result: Output from agent_fn
            - success: Whether execution succeeded
            - error_message: Error message if failed
        """
        task_id = datetime.now().isoformat()
        result = None
        error_msg = None

        # 1. Create backup if critical
        if critical or (file_path and self.is_critical_file(file_path)):
            logger.info(f"[GitSafety] Critical task detected, creating backup...")
            self.create_backup(task_name, file_path)

        # 2. Execute agent
        try:
            logger.info(f"[GitSafety] Executing {agent_type} agent: {task_name}")
            result = agent_fn()
            success = True
        except Exception as e:
            result = None
            success = False
            error_msg = str(e)
            logger.error(f"[GitSafety] Agent failed: {error_msg}")

        # 3. Checkpoint if success
        if success:
            self.create_checkpoint(task_name, agent_type, "success", task_id)
            logger.info(f"[GitSafety] Task completed successfully: {task_name}")
        else:
            # 4. Rollback if failed and requested
            if rollback_on_error and critical:
                logger.warning(f"[GitSafety] Critical task failed, rolling back...")
                self.rollback("agent_fail", error_msg, "branch")
            else:
                logger.warning(f"[GitSafety] Task failed but rollback disabled")

        return result, success, error_msg


class SafeOrchestrator:
    """
    Orchestrator with git safety integration
    Manages agent execution with automatic checkpoints and rollback
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.safety = GitSafetyWrapper(project_root)
        self.project_root = project_root or PROJECT_ROOT
        self.task_history: Dict[str, Dict[str, Any]] = {}

    def run_agent_safe(self, agent_type: str, prompt: str,
                      critical: bool = False, file_path: str = "",
                      agent_callable: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run agent with full safety integration

        Args:
            agent_type: Type of agent (code, frontend, debug, etc)
            prompt: Prompt/task for agent
            critical: If True, backup before execution
            file_path: Path to file being modified
            agent_callable: Optional callable to execute instead of mock

        Returns:
            Dict with keys: {
                'agent': str,
                'prompt': str,
                'success': bool,
                'result': Any,
                'error': Optional[str],
                'executed_at': str,
                'duration': float
            }
        """
        start_time = datetime.now()
        task_name = f"{agent_type}_{prompt[:40].replace(' ', '_')}"

        def default_agent_fn():
            """Default mock agent function"""
            return {
                "agent": agent_type,
                "prompt": prompt,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }

        agent_fn = agent_callable or default_agent_fn
        result, success, error = self.safety.with_safety(
            agent_fn=agent_fn,
            task_name=task_name,
            agent_type=agent_type,
            critical=critical,
            file_path=file_path,
            rollback_on_error=critical
        )

        duration = (datetime.now() - start_time).total_seconds()

        response = {
            "agent": agent_type,
            "prompt": prompt[:100],
            "success": success,
            "result": result,
            "error": error,
            "executed_at": start_time.isoformat(),
            "duration": duration,
            "critical": critical,
            "file_path": file_path
        }

        # Store in history
        self.task_history[task_name] = response

        return response

    def validate_task_sequence(self, tasks: list) -> Dict[str, Any]:
        """
        Validate sequence of tasks before execution
        Checks for conflicts (e.g., multiple writes to same file)

        Args:
            tasks: List of task dicts with keys: agent_type, prompt, file_path

        Returns:
            Dict with keys: {
                'valid': bool,
                'conflicts': list,
                'warnings': list
            }
        """
        conflicts = []
        warnings = []

        # Check for multiple writes to same file
        file_writes = {}
        for task in tasks:
            file_path = task.get("file_path", "")
            if file_path:
                if file_path in file_writes:
                    conflicts.append(
                        f"Multiple writes to {file_path}: "
                        f"{file_writes[file_path]} and {task['agent_type']}"
                    )
                else:
                    file_writes[file_path] = task['agent_type']

        # Check for critical files
        for task in tasks:
            file_path = task.get("file_path", "")
            if file_path and self.safety.is_critical_file(file_path):
                if not task.get("critical"):
                    warnings.append(f"Critical file {file_path} not marked critical")

        return {
            "valid": len(conflicts) == 0,
            "conflicts": conflicts,
            "warnings": warnings,
            "total_tasks": len(tasks)
        }

    def export_history(self, output_file: Optional[Path] = None) -> str:
        """
        Export task execution history to JSON

        Args:
            output_file: Optional path to write history to

        Returns:
            JSON string of history
        """
        history_data = {
            "exported_at": datetime.now().isoformat(),
            "total_tasks": len(self.task_history),
            "tasks": self.task_history
        }

        json_str = json.dumps(history_data, indent=2)

        if output_file:
            output_file.write_text(json_str)
            logger.info(f"[SafeOrchestrator] History exported to {output_file}")

        return json_str


# Convenience function for simple agent execution
def run_with_safety(agent_type: str, prompt: str,
                   critical: bool = False,
                   file_path: str = "") -> Dict[str, Any]:
    """
    Simple function to run agent with safety

    Usage:
        result = run_with_safety(
            agent_type="code",
            prompt="Add new feature X",
            critical=True,
            file_path="backend/services/memory_service.py"
        )
    """
    orch = SafeOrchestrator()
    return orch.run_agent_safe(
        agent_type=agent_type,
        prompt=prompt,
        critical=critical,
        file_path=file_path
    )


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example 1: Simple non-critical task
    print("=" * 60)
    print("Example 1: Non-critical task")
    print("=" * 60)
    result1 = run_with_safety(
        agent_type="debug",
        prompt="Run tests for memory_service",
        critical=False
    )
    print(json.dumps(result1, indent=2))

    # Example 2: Critical task with file
    print("\n" + "=" * 60)
    print("Example 2: Critical task with file")
    print("=" * 60)
    result2 = run_with_safety(
        agent_type="code",
        prompt="Refactor memory_service.py async methods",
        critical=True,
        file_path="backend/services/memory_service.py"
    )
    print(json.dumps(result2, indent=2))

    # Example 3: Using SafeOrchestrator directly
    print("\n" + "=" * 60)
    print("Example 3: Orchestrator with sequence validation")
    print("=" * 60)
    orch = SafeOrchestrator()

    # Validate task sequence
    tasks = [
        {
            "agent_type": "code",
            "prompt": "Add endpoint",
            "critical": True,
            "file_path": "backend/routes/new_api.py"
        },
        {
            "agent_type": "frontend",
            "prompt": "Add UI component",
            "critical": False,
            "file_path": "frontend/src/components/new-component.tsx"
        },
        {
            "agent_type": "debug",
            "prompt": "Run integration tests",
            "critical": False,
            "file_path": ""
        }
    ]

    validation = orch.validate_task_sequence(tasks)
    print("Task validation:")
    print(json.dumps(validation, indent=2))

    # Export history
    print("\n" + "=" * 60)
    print("Example 4: Task history export")
    print("=" * 60)
    history = orch.export_history()
    print(history)
