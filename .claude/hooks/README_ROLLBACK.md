# Git Rollback on Error - Complete System

Automatic git rollback when agent fails or tests fail. Prevents accumulating broken commits.

## What's New

**✨ Files Created (Today):**
- `git_rollback_on_error.sh` - Main rollback hook (bash) - executable
- `rollback_manager.py` - Python wrapper for easy integration - executable
- `test_rollback.sh` - Test suite - executable
- `ROLLBACK_INTEGRATION.md` - Complete technical guide
- `AGENT_INTEGRATION.md` - Agent-specific integration patterns
- `QUICK_REFERENCE.md` - One-liner commands
- `INTEGRATION_EXAMPLES.py` - Real-world code examples
- `README_ROLLBACK.md` - This file (navigation guide)

## Quick Start (30 seconds)

### Option 1: Bash (Direct)

```bash
# Soft rollback (preserve changes)
bash .claude/hooks/git_rollback_on_error.sh agent_fail "error message" soft

# Hard rollback (clean slate)
bash .claude/hooks/git_rollback_on_error.sh test_fail "error message" hard

# Branch rollback (restore from backup)
bash .claude/hooks/git_rollback_on_error.sh critical_error "error message" branch
```

### Option 2: Python (Recommended for Integration)

```python
from .claude.hooks.rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

# On agent fail
manager.on_agent_fail("code", "error message", RollbackMode.SOFT)

# On test fail
manager.on_test_fail("test_memory.py", "5 tests failed", RollbackMode.BRANCH)

# On critical error
manager.on_critical_error("database corrupted", RollbackMode.HARD)
```

## Which File to Read?

### I want to...

| Goal | Read This |
|------|-----------|
| **Understand the system** | `ROLLBACK_INTEGRATION.md` |
| **Integrate with agents** | `AGENT_INTEGRATION.md` |
| **Get quick commands** | `QUICK_REFERENCE.md` |
| **See real code examples** | `INTEGRATION_EXAMPLES.py` |
| **Test the hook** | Run `bash test_rollback.sh` |
| **Understand Python wrapper** | `rollback_manager.py` (code) |
| **Understand bash hook** | `git_rollback_on_error.sh` (code) |

## Rollback Modes Explained

### 1. SOFT (Default)
Use when: Agent crashed, tests failed (recoverable)
- Keeps changes in staging area
- Undoes last commit only
- Safe for development
- Best for: `on_agent_fail()`

```bash
bash .claude/hooks/git_rollback_on_error.sh agent_fail "error" soft
```

### 2. HARD
Use when: Bad merge, corrupt commit
- Discards all changes
- Creates backup branch automatically
- Clean slate
- Best for: `on_test_fail()`

```bash
bash .claude/hooks/git_rollback_on_error.sh test_fail "error" hard
```

### 3. BRANCH
Use when: Critical infrastructure failure, need known-good state
- Restores from safety backup branch
- Creates recovery branch with timestamp
- Most conservative option
- Best for: `on_critical_error()`

```bash
bash .claude/hooks/git_rollback_on_error.sh critical_error "error" branch
```

## Integration Examples

### Agent Executor

```python
from rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

try:
    result = Task("code", prompt)
except Exception as e:
    manager.on_agent_fail("code", str(e), RollbackMode.SOFT)
    raise
```

### Test Runner

```python
from rollback_manager import RollbackManager, RollbackMode

manager = RollbackManager()

result = subprocess.run(["pytest", "backend/tests/"])
if result.returncode != 0:
    manager.on_test_fail("backend/tests/", "tests failed", RollbackMode.BRANCH)
```

### CI Pipeline

```bash
#!/bin/bash

# Backend tests
if ! pytest backend/tests/; then
    bash .claude/hooks/git_rollback_on_error.sh test_fail "pytest failed" branch
    exit 1
fi

# Frontend build
if ! npm run build; then
    bash .claude/hooks/git_rollback_on_error.sh critical_error "build failed" hard
    exit 1
fi
```

## File Structure

```
.claude/hooks/
├── git_rollback_on_error.sh          (Main hook - bash)
├── rollback_manager.py               (Python wrapper)
├── test_rollback.sh                  (Test suite)
├── ROLLBACK_INTEGRATION.md           (Complete guide)
├── AGENT_INTEGRATION.md              (Agent patterns)
├── QUICK_REFERENCE.md                (Quick commands)
├── INTEGRATION_EXAMPLES.py           (Code examples)
└── README_ROLLBACK.md                (This file)

.claude/meta/
└── rollback.log                      (All rollback history)

git branches:
├── backup/before-rollback-*          (Auto-created backups)
└── recovery/from-error-*             (Recovery branches)
```

## Features

✅ **Three rollback modes** - soft, hard, branch
✅ **Python wrapper** - easy integration
✅ **Automatic logging** - .claude/meta/rollback.log
✅ **Backup creation** - never lose work
✅ **Test suite included** - validate before use
✅ **Colored output** - clear status messages
✅ **Error handling** - graceful fallbacks

## Logging

All rollbacks automatically logged to `.claude/meta/rollback.log`:

```
2025-10-20 16:30:45 | SOFT | agent_fail:code | From: abc1234 | Changes preserved
2025-10-20 16:31:12 | HARD | test_fail:pytest | From: def5678 | Backup: backup/before-rollback-20251020_163112
2025-10-20 16:32:00 | BRANCH | critical_error | From: ghi9012 | To: recovery/from-error-20251020_163200
```

View:
```bash
tail .claude/meta/rollback.log
cat .claude/meta/rollback.log | wc -l  # Count
```

## Verification

Test the hook before using:

```bash
bash .claude/hooks/test_rollback.sh
```

Should show all tests passing.

## Next Steps

1. Read `AGENT_INTEGRATION.md` for your use case
2. Integrate into your agent executor or test runner
3. Monitor `rollback.log` for issues
4. Create safety branches regularly: `git branch safety/backup-$(date +%Y%m%d_%H%M%S)`

## Support

**Questions about:**
- **What to integrate** → Read `AGENT_INTEGRATION.md`
- **How to use** → Read `QUICK_REFERENCE.md`
- **Complete details** → Read `ROLLBACK_INTEGRATION.md`
- **See real code** → Read `INTEGRATION_EXAMPLES.py`
- **Test it** → Run `bash test_rollback.sh`

## Status

✅ **Ready for production**
- All tests passing
- All documentation complete
- Real-world examples included
- Logging implemented
- Safety features enabled

---

**Version:** 1.0
**Status:** Production ready
**Last updated:** 2025-10-20
**Location:** `/home/pilote/projet/agi/.claude/hooks/`
