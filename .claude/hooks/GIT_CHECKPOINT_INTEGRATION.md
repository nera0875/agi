# Git Post-Task Checkpoint Hook

## Overview

Automatic git checkpoint creation after each agent task completion. Creates atomic commits with contextual information about the task.

**Location:** `/home/pilote/projet/agi/.claude/hooks/`

**Files:**
- `git_post_task_checkpoint.sh` - Main hook script (bash)
- `git_checkpoint_wrapper.py` - Python wrapper for orchestrator integration
- `.checkpoint_log` - Log of all checkpoints (JSON lines)

---

## Architecture

```
Agent Task Execution
        ↓
    Task Complete (success)
        ↓
    Orchestrator calls wrapper
        ↓
    GitCheckpointManager.create_checkpoint()
        ↓
    Executes git_post_task_checkpoint.sh
        ↓
    Creates atomic commit
        ↓
    Logs to .checkpoint_log
```

---

## Integration with Orchestrator

### Method 1: Python Wrapper (Recommended)

```python
from .claude.hooks.git_checkpoint_wrapper import GitCheckpointManager

manager = GitCheckpointManager()

# After agent task completes
result = manager.create_checkpoint(
    task_name="feature_authentication_backend",
    agent_type="code",
    status="success"  # Only creates checkpoint if success
)

print(result)
# {
#   "status": "complete",
#   "task_name": "feature_authentication_backend",
#   "agent_type": "code",
#   "task_id": "550e8400-e29b-41d4-a716-446655440000",
#   "timestamp": "2025-10-20T16:30:45.123456",
#   "output": "✅ Checkpoint saved (12 files)"
# }
```

### Method 2: Direct Shell Call

```python
import subprocess

result = subprocess.run(
    [
        "bash",
        "/home/pilote/projet/agi/.claude/hooks/git_post_task_checkpoint.sh",
        "task_name",
        "success",
        "agent_type",
        "optional_task_id"
    ],
    cwd="/home/pilote/projet/agi",
    capture_output=True,
    text=True,
    timeout=30
)
```

---

## Hook Script Interface

### Bash Script: `git_post_task_checkpoint.sh`

**Parameters:**
1. `$1` - Task name (required)
2. `$2` - Task status: `success`, `partial`, `failed` (default: unknown)
3. `$3` - Agent type: `ask`, `code`, `frontend`, `debug`, `research`, `architect`, `docs`, `sre` (default: generic)
4. `$4` - Task ID / UUID (optional, auto-generated if not provided)

**Returns:**
- Exit code 0: Success
- Exit code 1: Failure

**Behavior:**
- Only creates checkpoint if `$2 == "success"`
- Stages all changes with `git add -A`
- Creates atomic commit with formatted message
- Includes file count in commit
- Logs to `.checkpoint_log` via Python wrapper

**Commit Message Format:**
```
checkpoint: task_name [agent_type]

Task: task_name
Agent: agent_type
Status: success
Timestamp: YYYY-MM-DD_HH:MM:SS
TaskID: uuid
Files: N

Automated checkpoint after agent task execution.
```

---

## Python Wrapper: `git_checkpoint_wrapper.py`

### GitCheckpointManager Class

```python
class GitCheckpointManager:
    def __init__(self, project_root="/home/pilote/projet/agi")
    def create_checkpoint(
        task_name: str,
        agent_type: str,
        status: str = "success",
        task_id: Optional[str] = None
    ) -> dict
    def get_recent_checkpoints(limit: int = 10) -> list
```

### CLI Usage

```bash
# Create checkpoint
python .claude/hooks/git_checkpoint_wrapper.py \
    "feature_auth" \
    --agent code \
    --status success

# Show recent checkpoints
python .claude/hooks/git_checkpoint_wrapper.py \
    dummy_task \
    --show-recent 5
```

---

## Checkpoint Log

**Location:** `/home/pilote/projet/agi/.claude/hooks/.checkpoint_log`

**Format:** JSON lines (one checkpoint per line)

**Entry Structure:**
```json
{
  "status": "complete|skipped|failed|error",
  "task_name": "string",
  "agent_type": "string",
  "task_id": "uuid",
  "timestamp": "ISO8601",
  "returncode": 0,
  "output": "checkpoint output"
}
```

**Example:**
```
{"status": "complete", "task_name": "memory_service_tests", "agent_type": "debug", "task_id": "abc123", "timestamp": "2025-10-20T16:30:45", "returncode": 0, "output": "✅ Checkpoint saved (5 files)"}
{"status": "skipped", "task_name": "failed_task", "agent_type": "code", "status": "failed"}
{"status": "complete", "task_name": "backend_refactor", "agent_type": "code", "task_id": "def456", "timestamp": "2025-10-20T16:35:12", "returncode": 0, "output": "✅ Checkpoint saved (23 files)"}
```

---

## Workflow Integration

### Phase: Implementation (code agent)

```python
# 1. Code agent completes feature
result = Task(code, "Implement notification system")

# 2. Orchestrator creates checkpoint
if result.status == "success":
    checkpoint = manager.create_checkpoint(
        task_name="implement_notification_system",
        agent_type="code",
        status="success"
    )
    logger.info(f"Checkpoint: {checkpoint['status']}")
```

### Phase: Validation (debug agent)

```python
# 1. Tests run successfully
result = Task(debug, "Run backend tests")

# 2. Create checkpoint
if all_tests_pass:
    checkpoint = manager.create_checkpoint(
        task_name="backend_tests_notification_system",
        agent_type="debug"
    )
```

---

## Checkpoint Strategy

### When to Create Checkpoints

✅ **Create after:**
- Successful feature implementation
- Successful test runs
- Successful refactoring
- Successful documentation updates

❌ **Skip when:**
- Task status is "failed" or "partial"
- No actual changes made
- Already checkpointed (duplicate prevention)

### Checkpoint Granularity

**Per-task basis:**
- One checkpoint per agent task
- Atomic commits (one logical unit)
- Allows easy git revert if needed

**Example workflow:**
```
Task 1: Code feature → Checkpoint 1
Task 2: Write tests → Checkpoint 2
Task 3: Update docs → Checkpoint 3

vs

All together → 1 mega-commit (harder to debug)
```

---

## Debugging

### View Recent Checkpoints

```bash
# Via CLI
python .claude/hooks/git_checkpoint_wrapper.py dummy \
    --show-recent 10

# Via direct log read
tail -20 .claude/hooks/.checkpoint_log | python -m json.tool
```

### Check Git History

```bash
# See checkpoints in git log
git log --oneline | grep "checkpoint:"

# See full checkpoint commit
git log -1 --format=fuller <commit_hash>

# See checkpoint diffs
git show <commit_hash>
```

### Troubleshooting

**Problem: Checkpoint not created**
- Verify task status is "success"
- Check `git status` for uncommitted changes
- Verify hook script is executable: `ls -l git_post_task_checkpoint.sh`

**Problem: Commit failed**
- Check git config: `git config --global user.email`
- Verify write permissions on project root
- Check available disk space

**Problem: Hook timeout**
- Default timeout: 30 seconds
- Check git status for large changesets
- Monitor system resources

---

## Performance Considerations

- **Execution time:** Typically 0.5-2 seconds per checkpoint
- **Overhead:** Minimal (git operations are fast for small commits)
- **Storage:** Negligible (commit metadata only, diffs already in git)
- **Parallelization:** Safe to call from multiple agents (git handles concurrency)

---

## Future Enhancements

1. **Checkpoint batching** - Group related tasks before checkpoint
2. **Checkpoint signing** - GPG sign commits for verification
3. **Checkpoint filtering** - Skip minor changes (e.g., comment-only edits)
4. **Checkpoint retention** - Cleanup old checkpoints periodically
5. **Checkpoint tagging** - Tag checkpoints by phase/milestone

---

**Version:** 1.0 (2025-10-20)
**Maintainer:** AGI Orchestrator
**Status:** Ready for integration
