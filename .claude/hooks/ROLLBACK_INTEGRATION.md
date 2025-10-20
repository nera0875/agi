# Git Rollback On Error - Integration Guide

## Overview

Automatic git rollback when agent fails or tests fail. Prevents accumulating broken commits.

**Components:**
- `git_rollback_on_error.sh` - Main rollback logic (bash)
- `rollback_manager.py` - Python wrapper for easy integration

## Installation

Already done! Scripts are in `.claude/hooks/` and executable.

Verify:
```bash
ls -la .claude/hooks/git_rollback_on_error.sh
ls -la .claude/hooks/rollback_manager.py
```

## Rollback Modes

### 1. Soft (Default)
**Use when:** Agent fails, can recover
- Keeps changes in staging
- Undoes last commit only
- Safe for development

```bash
./.claude/hooks/git_rollback_on_error.sh agent_fail "error message" soft
```

**When to use:**
- Agent crashed mid-execution
- Tests failed but easy to fix
- Want to preserve work

### 2. Hard
**Use when:** Bad commit, need clean slate
- Discards all changes
- Creates backup branch
- Safe with backup

```bash
./.claude/hooks/git_rollback_on_error.sh test_fail "tests failed" hard
```

**When to use:**
- Merge conflict broke everything
- Need clean state to retry
- Can lose work (backup created)

**Backup location:**
```
backup/before-rollback-20251020_163000
```

### 3. Branch
**Use when:** Critical error, restore from known-good
- Finds safety backup branch
- Creates recovery branch
- Most conservative

```bash
./.claude/hooks/git_rollback_on_error.sh critical_error "database migration failed" branch
```

**When to use:**
- System unstable
- Need known-good state
- Critical infrastructure changes

## Integration Points

### 1. Agent Execution (Python)

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path("/home/pilote/projet/agi/.claude/hooks")))
from rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

try:
    result = Task(agent, prompt)
except Exception as e:
    # On agent fail → soft rollback (preserve work)
    manager.on_agent_fail(
        agent_name="code",
        error=str(e),
        mode=RollbackMode.SOFT
    )
    raise
```

### 2. Test Execution (Python)

```python
import subprocess
from rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

result = subprocess.run(["pytest", "backend/tests/"], capture_output=True)

if result.returncode != 0:
    # On tests fail → branch rollback (safety first)
    manager.on_test_fail(
        test_file="backend/tests/",
        error=result.stdout.decode(),
        mode=RollbackMode.BRANCH
    )
    sys.exit(1)
```

### 3. CI/CD Pipeline (Bash)

```bash
#!/bin/bash
set -e

PROJECT_ROOT="/home/pilote/projet/agi"
cd "$PROJECT_ROOT"

# Run tests
if ! pytest backend/tests/ -v; then
    echo "Tests failed, rolling back..."
    bash .claude/hooks/git_rollback_on_error.sh test_fail "pytest failed" branch
    exit 1
fi

# Build frontend
if ! npm run build; then
    echo "Frontend build failed, rolling back..."
    bash .claude/hooks/git_rollback_on_error.sh critical_error "frontend build failed" hard
    exit 1
fi

echo "✅ All checks passed"
```

### 4. Agent Execution Wrapper

In your agent executor:

```python
class AgentExecutor:
    def __init__(self):
        self.rollback = RollbackManager()

    def execute_task(self, agent_type, prompt):
        try:
            # Execute agent
            result = Task(agent_type, prompt)
            return result

        except TimeoutError:
            print(f"⏱️ Agent timeout")
            self.rollback.on_agent_fail(
                agent_name=agent_type,
                error="Execution timeout",
                mode=RollbackMode.SOFT
            )
            raise

        except Exception as e:
            print(f"❌ Agent failed: {e}")
            self.rollback.on_agent_fail(
                agent_name=agent_type,
                error=str(e),
                mode=RollbackMode.SOFT
            )
            raise
```

## CLI Usage

### Direct Bash

```bash
# Soft rollback (preserve changes)
./.claude/hooks/git_rollback_on_error.sh agent_fail "NPE in memory service" soft

# Hard rollback (discard changes)
./.claude/hooks/git_rollback_on_error.sh test_fail "assertion failed" hard

# Branch rollback (restore from backup)
./.claude/hooks/git_rollback_on_error.sh critical_error "db migration failed" branch
```

### Python CLI

```bash
# Via rollback_manager.py
python .claude/hooks/rollback_manager.py agent_fail "Error message" soft

# Check history
python .claude/hooks/rollback_manager.py --status
```

## Rollback History

All rollbacks logged to `.claude/meta/rollback.log`:

```
2025-10-20 16:30:45 | SOFT | agent_fail:code | From: abc1234 | Changes preserved
2025-10-20 16:31:12 | HARD | test_fail:pytest | From: def5678 | Backup: backup/before-rollback-20251020_163112
2025-10-20 16:32:00 | BRANCH | critical_error | From: ghi9012 | To: recovery/from-error-20251020_163200
```

View history:

```bash
# Last 10 rollbacks
tail -10 .claude/meta/rollback.log

# All rollbacks
cat .claude/meta/rollback.log
```

## Best Practices

### 1. Choose Right Mode

| Situation | Mode | Why |
|-----------|------|-----|
| Agent crashed | `soft` | Keep work, retry |
| Tests failed (easy fix) | `soft` | Debug quickly |
| Tests failed (complex) | `branch` | Start fresh |
| Bad merge | `hard` | Clean slate |
| Critical infrastructure | `branch` | Safety first |

### 2. Always Make Backups First

Before hard operations:
```bash
# Create safety branch
git branch safety/backup-$(date +%Y%m%d_%H%M%S)

# Then rollback
bash .claude/hooks/git_rollback_on_error.sh ... hard
```

### 3. Monitor Rollback Frequency

If rolling back too often:
```bash
# Check frequency
cat .claude/meta/rollback.log | wc -l

# Review failures
tail -20 .claude/meta/rollback.log
```

**High rollback rate = underlying issues:**
- Flaky tests
- Unstable agents
- Bad environment

## Troubleshooting

### "No previous commit"
- Rollback tried but nothing to rollback
- Normal on first commit
- Script handles gracefully

### "No safety branch found"
- Fallback to soft reset
- Create safety branches regularly:
  ```bash
  git branch safety/backup-$(date +%Y%m%d_%H%M%S)
  ```

### "Rollback timeout"
- Rollback took >30s (rare)
- Check git status: `git status --short`
- May need manual intervention

### Script not executable
```bash
chmod +x .claude/hooks/git_rollback_on_error.sh
chmod +x .claude/hooks/rollback_manager.py
```

## Safety Guarantees

✅ **Always backed up:**
- Hard rollback creates backup branch
- Original commit never lost
- Recovery branch marked with timestamp

✅ **No silent failures:**
- All operations logged
- Errors printed to console
- Exit codes indicate success/failure

✅ **Idempotent:**
- Safe to run multiple times
- Won't cause additional damage
- Each run is independent

## Examples

### Example 1: Agent Fail → Soft Rollback

```bash
# Agent crashed
bash .claude/hooks/git_rollback_on_error.sh agent_fail \
  "Memory service NullPointerException" soft

# Result:
# - Commit undone
# - Changes preserved in staging
# - Ready to fix and recommit
```

### Example 2: Tests Fail → Branch Rollback

```bash
# Tests failed
bash .claude/hooks/git_rollback_on_error.sh test_fail \
  "5 tests failed in backend/tests/test_memory.py" branch

# Result:
# - Switched to safe branch
# - Created recovery/from-error-* branch
# - Ready to investigate
```

### Example 3: Critical Error → Hard Rollback

```bash
# Database migration corrupted data
bash .claude/hooks/git_rollback_on_error.sh critical_error \
  "PostgreSQL migration: ALTER TABLE failed, rolled back manually" hard

# Result:
# - Created backup branch
# - Hard reset to previous commit
# - Clean slate for retry
```

## Logs

### Log Format

```
TIMESTAMP | MODE | ERROR_TYPE | FROM: commit | DETAILS
```

Example:
```
2025-10-20 16:30:45 | SOFT | agent_fail:code | From: abc1234 | Changes preserved
2025-10-20 16:31:12 | HARD | test_fail:pytest | From: def5678 | Backup: backup/before-rollback-20251020_163112
2025-10-20 16:32:00 | BRANCH | critical_error | From: ghi9012 | To: recovery/from-error-20251020_163200
```

### View Logs

```bash
# View in .claude/meta/rollback.log
cat .claude/meta/rollback.log

# Via Python manager
python .claude/hooks/rollback_manager.py --status
```

## Integration Checklist

- [x] Scripts created and executable
- [ ] Integrate with agent executor
- [ ] Integrate with test runner
- [ ] Add CI/CD hooks
- [ ] Monitor rollback frequency
- [ ] Document failures in runbooks

---

**Status:** Ready for integration
**Version:** 1.0
**Last updated:** 2025-10-20
