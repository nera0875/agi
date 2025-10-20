# Git Rollback - Quick Reference

## One-Liners

### Soft Rollback (Preserve Changes)
```bash
bash .claude/hooks/git_rollback_on_error.sh agent_fail "error message" soft
```
👉 Use when: Agent crashed, tests need retry

### Hard Rollback (Clean Slate)
```bash
bash .claude/hooks/git_rollback_on_error.sh test_fail "error message" hard
```
👉 Use when: Bad merge, corrupt commit

### Branch Rollback (Restore from Backup)
```bash
bash .claude/hooks/git_rollback_on_error.sh critical_error "error message" branch
```
👉 Use when: Critical infrastructure failure

## Python Integration

### Simple Usage
```python
from .claude.hooks.rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

# Agent failed
manager.on_agent_fail("code", "NullPointerException", RollbackMode.SOFT)

# Tests failed
manager.on_test_fail("test_memory.py", "5 tests failed", RollbackMode.BRANCH)

# Critical error
manager.on_critical_error("database corrupted", RollbackMode.HARD)
```

### Check Status
```python
manager.get_log()  # Returns list of rollback history
manager.print_status()  # Prints last 5 rollbacks
```

## Log Locations

```
.claude/meta/rollback.log          # All rollback history
backup/before-rollback-*           # Backup branches from hard rollbacks
recovery/from-error-*              # Recovery branches from branch rollbacks
```

## Modes Comparison

| Mode | Changes | Commit | Backup | Use When |
|------|---------|--------|--------|----------|
| `soft` | Kept | Undone | No | Recoverable errors |
| `hard` | Lost | Undone | Yes | Merge issues |
| `branch` | Lost | Lost | Yes | Critical failures |

## Dry Run

```bash
# Test without actual rollback
bash -n .claude/hooks/git_rollback_on_error.sh
```

## Troubleshooting

```bash
# Check if executable
ls -l .claude/hooks/git_rollback_on_error.sh

# Fix permissions
chmod +x .claude/hooks/git_rollback_on_error.sh

# View history
tail .claude/meta/rollback.log

# Check git status
git status
git branch -a
```

## Integration Points

**Agent Executor:**
```python
try:
    Task(agent, prompt)
except Exception as e:
    manager.on_agent_fail(agent, str(e), RollbackMode.SOFT)
```

**Test Runner:**
```python
if not pytest.main():
    manager.on_test_fail("tests", "pytest failed", RollbackMode.BRANCH)
```

**CI/CD:**
```bash
bash .claude/hooks/git_rollback_on_error.sh test_fail "build failed" branch
```

---

Full docs: `ROLLBACK_INTEGRATION.md`
