---
name: "Git Safety Strategy"
description: "Backup workflow, rollback procedures, best practices entreprise (Google/Meta pattern)"
categories: ["system", "git", "safety", "backup"]
tags: ["git", "backup", "rollback", "feature-branches", "atomic-commits", "CI/CD"]
version: "1.0.0"
enabled: true
---

## Overview

Safety net pour modifications critiques via git. Automatise backup avant Edit/Write, atomic commits après tasks, rollback si erreur.

**Goal:** Zéro risque de perte de code lors de modifications massives.

## When to Use

- **Before Major Refactoring:** CLAUDE.md, agents, services
- **Critical File Modifications:** schema.py, memory_service.py, migrations
- **Multi-Agent Workflows:** Checkpoints entre phases
- **Experimental Features:** Feature branches pour tests avant merge
- **Pre-Deployment:** Backup complet avant push production

## Workflow Pattern (Google/Meta Enterprise)

```
┌─────────────────────────────────────────────────────────┐
│ 1. PRE-MODIFICATION (Setup)                             │
│    git status → branch creation → backup commit        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 2. MODIFICATION PHASE (Implementation)                  │
│    Agents parallèle (code, frontend, debug)            │
│    Chaque agent issu de commit de référence            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 3. CHECKPOINT COMMITS (Safety)                          │
│    Après chaque phase complétée                         │
│    Atomic: 1 commit = 1 feature logique                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 4. VALIDATION (Tests)                                   │
│    Tests pytest, npm build, Type checks                │
│    Si PASS → Ready to merge                            │
│    Si FAIL → Rollback ou fix + retry                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ 5. MERGE (Integration)                                  │
│    Rebase-and-merge → master branch                    │
│    Backup tag créé avant merge                         │
└─────────────────────────────────────────────────────────┘
```

## Critical Files Protected

**Backup commit créé si modification de:**
- CLAUDE.md (instructions AGI)
- .claude/agents/*.md (agent definitions)
- .claude/skills/** (skill documentation)
- backend/api/schema.py (GraphQL schema)
- backend/services/*.py (business logic)
- cortex/agi_tools_mcp.py (MCP tools)
- cortex/consolidation.py (memory consolidation)
- backend/agents/**/*.py (LangGraph agents)
- migrations/*.sql (DB schema)

## Feature Branch Naming

**Convention:** `type/scope-description`

```
feature/notifications-system
fix/memory-leak-redis-cache
refactor/split-agi-tools-mcp
docs/memory-architecture
experiment/neo4j-query-optimization
hotfix/schema-validation-bug
chore/update-dependencies
```

**Rules:**
- Lowercase + hyphens only
- Max 50 chars
- Descriptive scope (2-3 words)
- Link to issue if exists: `feature/notifications-system-123`

## Commit Message Standards

**Format:** Atomic commit convention

```
type(scope): description

Body (optional, 72 chars max per line):
- What changed
- Why changed
- Side effects

Footer (optional):
Closes #123
```

**Type Values:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code structure change
- `test` - Test additions/changes
- `docs` - Documentation
- `chore` - Build, deps, etc
- `perf` - Performance optimization
- `ci` - CI/CD changes

**Examples:**

```
feat(notifications): add GraphQL subscription support

- Implement onNotification subscription
- Add notification queue to backend
- Integrate with Apollo Client useSubscription

Closes #456
```

```
fix(memory-service): prevent concurrent write conflicts

Race condition in L1/L2 consolidation caused duplicate entries.
Added atomic lock mechanism via Redis.

Closes #123
```

## Rollback Procedures (3 Modes)

### Mode 1: Soft Rollback (Undo + Keep Staged)

**When:** Made mistakes in last commit, want to redo

```bash
git reset --soft HEAD~1
# Files staged, modifications kept
# Re-commit with fixes
```

**Safe for:**
- Commit message wrong
- Forgot to include file
- Want to split into 2 commits

### Mode 2: Hard Rollback (Complete Undo)

**When:** Feature broken, need start over

```bash
git reset --hard HEAD~1
# Completely discard last commit
# Back to previous state
```

**Safe for:**
- Feature fundamentally broken
- Started wrong direction
- Need new approach

### Mode 3: Branch Rollback (Revert Previous Commit)

**When:** Need to undo merged commit without rewriting history

```bash
git revert <commit-hash>
# Creates NEW commit that undoes changes
# Preserves history for audit
```

**Safe for:**
- Already pushed to shared branch
- Need audit trail
- Collaborative repos

## When to Commit

### BEFORE Patterns (Pre-modification checkpoint)

```python
# Situation: About to refactor critical file
Action:
1. git checkout -b refactor/split-agi-tools
2. git commit -m "chore: checkpoint before refactor" --allow-empty
   → Creates safe point to rollback to
3. Start modifications
```

### AFTER Patterns (Post-task atomic commits)

```python
# Situation: Completed 1 feature logically
Action:
1. git add <related files>
2. git commit -m "feat(scope): description"
   → Each logical feature = 1 commit
   → Easy to revert individual features
   → Clear history

# Situation: Multi-agent phase completed
Action:
1. git add backend/api/schema.py backend/services/memory_service.py
2. git commit -m "feat(memory): add L1/L2 consolidation"
3. Next phase starts with fresh checkpoint
```

## Best Practices (Enterprise Patterns)

### 1. Atomic Commits (Google Pattern)

Each commit = one logical change, reviewable independently.

```bash
# ✅ GOOD (3 atomic commits)
commit 1: feat(api): add endpoint /memories GET
commit 2: feat(service): implement memory retrieval
commit 3: test(memory): add unit tests

# ❌ BAD (1 massive commit)
commit 1: Added 5 features, 10 files, 2000 lines
```

**Benefit:** Easy to bisect bugs, revert specific features, understand history.

### 2. Feature Branches (Meta Pattern)

Never modify master directly. Always via feature branch + PR workflow.

```bash
# ✅ GOOD
git checkout -b feature/notifications
# Make changes
git push origin feature/notifications
# Create PR, review, merge

# ❌ BAD
git checkout master
# Direct modifications
git push master
```

**Benefit:** Code review checkpoint, CI/CD validation, safety net.

### 3. Commit Before Large Refactoring

```bash
# ✅ GOOD (before refactoring)
git commit -m "chore: checkpoint before refactor" --allow-empty

# Make refactoring changes
# If broken:
git reset --hard HEAD~1  # Safe rollback

# ❌ RISKY
# Start refactoring without commit
# If broken, can't easily rollback
```

### 4. Tag Release Versions

```bash
# Before deploying to production
git tag -a v1.0.0 -m "Release: Memory system v1.0"
git push origin v1.0.0

# Later, if need revert to v1.0:
git checkout v1.0.0
git reset --hard v1.0.0
```

### 5. Backup Tags for Critical Moments

```bash
# Before major deployment
git tag backup/before-migration-2025-10-20
git push origin backup/before-migration-2025-10-20

# Before major refactoring
git tag backup/before-split-agi-tools-2025-10-20
git push origin backup/before-split-agi-tools-2025-10-20
```

## CI/CD Integration Points

### Pre-Commit Validation

```bash
git commit
→ Pre-commit hooks run:
  - Black/Prettier format check
  - Ruff linting
  - Type checking mypy
  - Secret scanning
→ If FAIL: Fix and re-commit
→ If PASS: Commit succeeds
```

### Pre-Push Validation

```bash
git push
→ Pre-push hooks run:
  - pytest backend
  - npm run build frontend
  - Type checks
→ If FAIL: Fix locally, push again
→ If PASS: Push succeeds → triggers CI
```

### CI Pipeline (GitHub Actions/GitLab CI)

```yaml
on: push
  - Run tests (pytest)
  - Build frontend (npm)
  - Type checks (mypy, tsc)
  - Security scan
  - Deploy staging

on: merge_request
  - All above +
  - Code review requirements
  - Approval needed
```

## Recovery Scenarios

### Scenario 1: "Oops, broke production!"

```bash
# 1. Identify last known good commit
git log --oneline | head -20

# 2. Soft reset to good state
git reset --soft <good-commit>

# 3. Identify broken changes
git diff --staged

# 4. Fix broken changes locally
# (edit files)

# 5. Commit fixed version
git add .
git commit -m "fix: revert broken feature + fixes"

# 6. Push
git push origin master
```

### Scenario 2: "Need to undo last 3 commits but keep changes"

```bash
# Soft reset to 3 commits ago
git reset --soft HEAD~3

# All changes staged
# Review and recommit properly
git add .
git commit -m "feat: properly refactored 3 changes"
```

### Scenario 3: "Already merged to master, need to revert"

```bash
# 1. Find commit hash
git log --oneline | grep "broken feature"
# Result: abc123d feat: broken feature

# 2. Revert via new commit
git revert abc123d

# 3. This creates:
# Commit: Revert "feat: broken feature"
# Undoes changes, keeps history

# 4. Push
git push origin master
```

### Scenario 4: "Feature branch got messy, start fresh"

```bash
# 1. Go back to master
git checkout master

# 2. Create new clean branch
git checkout -b feature/clean-attempt

# 3. Old branch still exists for reference
# Can delete old messy branch when confident
git branch -D feature/messy-attempt
```

## Status Check Commands

**Before any major operation:**

```bash
# Check current state
git status

# See recent commits
git log --oneline -5

# See branch history
git branch -a

# See uncommitted changes
git diff

# See staged changes
git diff --staged
```

## Checklists

### Before Major Refactoring

- [ ] git status → no uncommitted changes
- [ ] git log → verify recent commit stable
- [ ] git checkout -b refactor/descriptive-name
- [ ] Create checkpoint: `git commit --allow-empty -m "chore: checkpoint"`
- [ ] Start modifications
- [ ] git add <related files>
- [ ] git commit -m "refactor(scope): description"
- [ ] Run tests: pytest / npm build
- [ ] If PASS: ready for merge
- [ ] If FAIL: fix + retry

### Before Pushing to Master

- [ ] git log --oneline -5 → verify commits look good
- [ ] git diff master..HEAD → review changes
- [ ] pytest backend → all tests pass
- [ ] npm run build frontend → no errors
- [ ] git push origin feature/branch-name
- [ ] Create PR in GitHub
- [ ] Code review approved
- [ ] Merge → CI pipeline runs
- [ ] Verify production deployment successful

## Emergency Commands (Use Carefully)

```bash
# See everything you've done (can undo anything)
git reflog

# Go back to any point in reflog
git reset --hard HEAD@{5}

# See what changed in specific commit
git show abc123d

# See who changed specific line
git blame filename.py

# Find commit that introduced bug (binary search)
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
```

## Integration with Agent Workflows

**Multi-Agent Phase Pattern:**

```python
# Phase 1: Setup
git checkout -b feature/notifications-system
git commit --allow-empty -m "chore: phase 1 checkpoint"

# Phase 2: Parallel agents work
Task(code, "Backend subscription...")
Task(frontend, "React hook...")
Task(debug, "Tests...")

# Phase 3: Checkpoint after phase
git add backend/ frontend/
git commit -m "feat(notifications): backend + frontend complete"

# Phase 4: Validation
pytest backend
npm run build

# Phase 5: Merge
git push origin feature/notifications-system
# Create PR, merge to master
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Enterprise Standards:** Google (atomic commits), Meta (feature branches), GitFlow (release management)
