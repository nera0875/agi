# Git Rollback - Integration Checklist

Follow this checklist to integrate the rollback hook into your pipeline.

## Phase 1: Verify Installation

- [ ] All scripts exist in `.claude/hooks/`
- [ ] All scripts are executable: `ls -l *.sh *.py`
- [ ] Test suite passes: `bash test_rollback.sh`
- [ ] Log directory exists: `.claude/meta/`

```bash
# Verify
bash .claude/hooks/test_rollback.sh
# Should show: ✅ All tests passed!
```

## Phase 2: Understand the System

- [ ] Read `README_ROLLBACK.md` (5 min)
- [ ] Read `QUICK_REFERENCE.md` (5 min)
- [ ] Read `AGENT_INTEGRATION.md` (10 min)
- [ ] Review `INTEGRATION_EXAMPLES.py` (5 min)

## Phase 3: Plan Integration Points

Identify where rollback should trigger:

### Agent Executor
- [ ] Identify agent execution code location
- [ ] Check for error handling
- [ ] Decide rollback mode (typically SOFT)
- [ ] Location: `_________________________________`

### Test Runner
- [ ] Identify pytest/test runner location
- [ ] Check failure handling
- [ ] Decide rollback mode (typically BRANCH)
- [ ] Location: `_________________________________`

### CI/CD Pipeline
- [ ] Identify build script location
- [ ] Check for failure conditions
- [ ] Decide rollback modes per phase
- [ ] Location: `_________________________________`

## Phase 4: Create Safety Branches

Before integrating, create safety backups:

```bash
# Create initial safety branch
git branch safety/backup-initial

# Script to create timestamped backups
#!/bin/bash
git branch safety/backup-$(date +%Y%m%d_%H%M%S)
```

- [ ] Create initial safety branch: `git branch safety/backup-initial`
- [ ] Test rollback with BRANCH mode (uses safety branch)
- [ ] Consider automating safety branch creation

## Phase 5: Integrate Agent Executor

**Step 1:** Add import
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".." / ".claude" / "hooks"))
from rollback_manager import RollbackManager, RollbackMode
```

**Step 2:** Add manager initialization
```python
manager = RollbackManager()
```

**Step 3:** Wrap agent execution
```python
try:
    result = execute_agent(agent_type, prompt)
except Exception as e:
    manager.on_agent_fail(agent_type, str(e), RollbackMode.SOFT)
    raise
```

**Checklist:**
- [ ] Import rollback_manager
- [ ] Initialize RollbackManager
- [ ] Wrap all agent execution in try/except
- [ ] Call `on_agent_fail()` in except block
- [ ] Test with dry-run (no actual changes)
- [ ] Test with actual agent (verify rollback works)

## Phase 6: Integrate Test Runner

**Step 1:** Import rollback_manager (same as Phase 5)

**Step 2:** Wrap test execution
```python
if result.returncode != 0:
    manager.on_test_fail(test_file, error_msg, RollbackMode.BRANCH)
    raise SystemExit(1)
```

**Checklist:**
- [ ] Import rollback_manager
- [ ] Initialize RollbackManager
- [ ] Check test result after pytest/npm run
- [ ] Call `on_test_fail()` on failure
- [ ] Test with failing tests (verify rollback works)

## Phase 7: Integrate CI/CD

**Step 1:** Add bash hook calls to CI script
```bash
if ! pytest backend/tests/; then
    bash .claude/hooks/git_rollback_on_error.sh test_fail "pytest failed" branch
    exit 1
fi
```

**Checklist:**
- [ ] Add hook calls to CI script
- [ ] Test CI pipeline locally
- [ ] Verify rollback triggers on failure
- [ ] Check rollback.log for entries

## Phase 8: Monitor and Verify

**Week 1:**
- [ ] Monitor `.claude/meta/rollback.log`
- [ ] Check rollback frequency (target: 0-2 per day)
- [ ] Review each rollback entry
- [ ] Verify backup branches exist

**Week 2:**
- [ ] If working well: Expand to more integration points
- [ ] If issues: Debug and review

**Ongoing:**
- [ ] Monitor rollback frequency weekly
- [ ] Create new safety branches monthly
- [ ] Review rollback history for patterns
- [ ] Fix underlying issues causing rollbacks

## Phase 9: Document Your Integration

For your team:

```markdown
# Rollback Hook Integration

This project uses automatic git rollback on:
- Agent failures → soft rollback (preserve work)
- Test failures → branch rollback (restore from backup)
- Critical errors → hard rollback (clean slate)

## Viewing rollback history
tail .claude/meta/rollback.log

## Manual rollback (if needed)
bash .claude/hooks/git_rollback_on_error.sh <type> <msg> <mode>

## Creating safety branches
git branch safety/backup-$(date +%Y%m%d_%H%M%S)
```

- [ ] Document integration in README
- [ ] Add rollback info to onboarding guide
- [ ] Share with team members

## Phase 10: Optimization (Optional)

After 2 weeks of successful operation:

- [ ] Review most common rollback causes
- [ ] Fix top 3 issues
- [ ] Optimize timeout values if needed
- [ ] Consider expanding to more integration points

## Troubleshooting

### Issue: "No previous commit"
- **Cause:** Rollback triggered on first commit
- **Solution:** Normal behavior, script handles gracefully

### Issue: "No safety branch found"
- **Cause:** Safety branches not created
- **Solution:** Run `git branch safety/backup-$(date +%Y%m%d_%H%M%S)`

### Issue: High rollback frequency
- **Cause:** Underlying system issues
- **Solution:**
  1. Review rollback causes
  2. Fix top issues
  3. Monitor improvement

### Issue: Rollback timeout (>30s)
- **Cause:** Rare, git operation slow
- **Solution:** Check disk space, git status, fragmentation

## Success Criteria

✅ **Phase Complete When:**
- [ ] All tests passing
- [ ] Rollback working for soft/hard/branch modes
- [ ] Logging to `.claude/meta/rollback.log`
- [ ] Team trained on usage
- [ ] Monitoring in place
- [ ] Low rollback frequency (<5 per week)

## Quick Reference During Integration

```bash
# Test hook
bash .claude/hooks/test_rollback.sh

# Manual rollback (testing)
bash .claude/hooks/git_rollback_on_error.sh test_type "message" soft

# View history
tail .claude/meta/rollback.log

# Create safety branch
git branch safety/backup-$(date +%Y%m%d_%H%M%S)

# Check Python import
python3 -c "from .claude.hooks.rollback_manager import RollbackManager; print('OK')"
```

## Sign-Off

Once complete:

```
Integration Lead: _______________________  Date: __________
QA Approval:     _______________________  Date: __________
Team Notification: _______________________  Date: __________
```

---

**Estimated time:** 2-4 hours total
**Complexity:** Medium
**Risk:** Low (with safety branches)
**Support:** See AGENT_INTEGRATION.md for code examples
