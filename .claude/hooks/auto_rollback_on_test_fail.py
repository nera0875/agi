#!/usr/bin/env python3
"""
Auto-Rollback on Test Fail Hook
Trigger: Après modifications critiques, run tests → si fail, rollback auto
Protects: backend/services/*, backend/api/schema.py, cortex/agi_tools_mcp.py
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path("/home/pilote/projet/agi")


def run_tests(test_path: str = "backend/tests/", timeout: int = 60) -> Tuple[bool, str]:
    """
    Run pytest et return (success, output)

    Args:
        test_path: Path to tests directory
        timeout: Timeout in seconds

    Returns:
        Tuple[bool, str]: (success, output)
    """
    try:
        result = subprocess.run(
            ["pytest", test_path, "-v", "--tb=short", "--timeout=30", "-q"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        success = result.returncode == 0
        output = result.stdout + "\n" + result.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, f"Tests timeout exceeded ({timeout}s)"
    except FileNotFoundError:
        return False, "pytest not found - install with: pip install pytest pytest-timeout"
    except Exception as e:
        return False, f"Test execution failed: {e}"


def is_critical_file(file_path: str) -> bool:
    """
    Détermine si le fichier modifié est critique (nécessite tests)

    Critical patterns:
    - backend/services/* → Business logic
    - backend/api/schema.py → GraphQL schema
    - backend/routes/* → API routes
    - cortex/agi_tools_mcp.py → Core MCP tools
    - backend/agents/* → Agent logic
    """
    critical_patterns = [
        "backend/services/",
        "backend/api/schema.py",
        "backend/routes/",
        "backend/agents/",
        "cortex/agi_tools_mcp.py",
        "cortex/local_mcp_router.py",
    ]

    return any(pattern in file_path for pattern in critical_patterns)


def get_relevant_tests(file_path: str) -> str:
    """
    Retourne le chemin des tests pertinents selon le fichier modifié
    """
    if "memory" in file_path:
        return "backend/tests/services/test_memory_service.py"
    elif "graph" in file_path:
        return "backend/tests/services/test_graph_service.py"
    elif "schema" in file_path:
        return "backend/tests/api/"
    elif "routes" in file_path:
        return "backend/tests/routes/"
    elif "agents" in file_path:
        return "backend/tests/agents/"
    elif "mcp" in file_path:
        return "cortex/"
    else:
        return "backend/tests/"


def log_test_failure(file_path: str, test_output: str, rollback_result: dict) -> None:
    """Log test failure to meta directory"""
    log_dir = PROJECT_ROOT / ".claude" / "meta"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "test_failures.log"
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "file": file_path,
        "test_output_last_200": test_output[-200:],
        "rollback_success": rollback_result.get("success", False),
        "rollback_mode": rollback_result.get("mode_used", "unknown"),
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def trigger_rollback(file_path: str, test_output: str, mode: str = "branch") -> dict:
    """
    Trigger rollback via RollbackManager

    Args:
        file_path: File that was modified
        test_output: Test failure output
        mode: "soft", "hard", or "branch"

    Returns:
        dict: Rollback result
    """
    from rollback_manager import RollbackManager

    manager = RollbackManager(str(PROJECT_ROOT))
    result = manager.on_test_fail(
        test_file=file_path,
        error=f"Tests failed for {file_path}. Output: {test_output[-100:]}",
        mode=mode,
    )

    return result


def main():
    """Main hook logic"""

    # Get file changed from environment (set by Claude Code hooks)
    file_changed = os.environ.get("CLAUDE_FILE_PATH", "")

    if not file_changed:
        print("[Auto-Rollback] ℹ️ No file path provided, skipping")
        return 0

    if not is_critical_file(file_changed):
        print(f"[Auto-Rollback] ℹ️ File not critical: {file_changed}")
        return 0

    print(f"[Auto-Rollback] 🧪 Running tests for: {file_changed}")

    # Determine relevant tests
    test_path = get_relevant_tests(file_changed)
    print(f"[Auto-Rollback] 📂 Test path: {test_path}")

    # Run tests
    success, output = run_tests(test_path=test_path, timeout=60)

    if success:
        print("[Auto-Rollback] ✅ Tests PASSED - no rollback needed")
        return 0

    # Tests failed - prepare rollback
    print("[Auto-Rollback] ❌ Tests FAILED")
    print(f"[Auto-Rollback] 📋 Output (last 300 chars):")
    print(output[-300:])
    print("[Auto-Rollback] 🔄 AUTO-ROLLBACK TRIGGERED")

    # Execute rollback (mode: branch = safe, restores from safety backup)
    rollback_result = trigger_rollback(
        file_path=file_changed,
        test_output=output,
        mode="branch"
    )

    # Log failure
    log_test_failure(file_changed, output, rollback_result)

    if rollback_result.get("success"):
        print("[Auto-Rollback] ✅ Rollback completed successfully")
        print(f"[Auto-Rollback] 💡 Rolled back to safety backup")
        print(f"[Auto-Rollback] 📝 Fix tests in {test_path}, then retry")
        return 1  # Exit 1 to signal problem
    else:
        print("[Auto-Rollback] ⚠️ Rollback attempted but encountered issues")
        print(f"[Auto-Rollback] Error: {rollback_result.get('error', 'Unknown')}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"[Auto-Rollback] 💥 Fatal error: {e}")
        sys.exit(1)
