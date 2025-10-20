# Git Safety Strategy - Detailed Instructions

## Table of Contents
1. [Quick Start](#quick-start)
2. [Feature Branch Workflow](#feature-branch-workflow)
3. [Commit Message Standards](#commit-message-standards)
4. [Rollback Procedures](#rollback-procedures)
5. [Critical File Protection](#critical-file-protection)
6. [Multi-Agent Checkpoints](#multi-agent-checkpoints)
7. [Pre/Post Modification Patterns](#prepost-modification-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### For First-Time Feature

```bash
# 1. Create feature branch
git checkout -b feature/your-feature-name

# 2. Create checkpoint commit
git commit --allow-empty -m "chore: checkpoint"

# 3. Make changes
# (edit files)

# 4. Stage and commit
git add .
git commit -m "feat(scope): description"

# 5. Push to remote
git push origin feature/your-feature-name

# 6. Create PR for review
# (in GitHub)
```

### For Critical File Modification

```bash
# 1. Check current state
git status

# 2. Create feature branch with prefix
git checkout -b refactor/critical-file-name

# 3. Create backup commit
git commit --allow-empty -m "chore: backup before modification"

# 4. Make one logical change
# (edit 1-3 related files)

# 5. Commit atomically
git add <related files>
git commit -m "refactor(scope): description"

# 6. Test thoroughly
pytest backend
npm run build

# 7. If ALL PASS: ready to push
git push origin refactor/critical-file-name
```

---

## Feature Branch Workflow

### Creating Feature Branch

**Golden Rule:** Never work directly on master. Always create feature branch.

```bash
# Good practice: branch from master
git checkout master
git pull origin master
git checkout -b feature/your-feature

# Alternative (shorthand)
git checkout -b feature/your-feature origin/master
```

### Branch Naming Conventions

**Format:** `type/scope-description`

**Type options:**
- `feature/` - New feature
- `fix/` - Bug fix
- `refactor/` - Code restructuring
- `docs/` - Documentation
- `test/` - Test improvements
- `perf/` - Performance optimization
- `chore/` - Maintenance tasks
- `experiment/` - Experimental work
- `hotfix/` - Critical production fix

**Scope options:**
- Domain area (memory, notifications, auth, etc)
- Component name (schema, service, hook)
- System name (l1-cache, neo4j-graph, etc)

**Examples (GOOD):**
```
feature/memory-l1-consolidation
fix/redis-race-condition
refactor/split-agi-tools-mcp
docs/memory-architecture
perf/n-plus-one-query-fix
hotfix/auth-token-expiry
test/add-memory-service-tests
experiment/neo4j-optimization
```

**Examples (BAD):**
```
feature/stuff                    # Too vague
feature/new                      # Not descriptive
fix/bug                          # No scope
feature/UPPERCASE               # Wrong case
feature/my_feature_with_underscores  # Use hyphens
feature/this-is-too-long-and-nobody-knows-what-it-does  # > 50 chars
```

### Working on Feature Branch

```bash
# Make changes
vim backend/services/memory_service.py

# Verify changes
git status
git diff

# Stage specific files (preferred over git add .)
git add backend/services/memory_service.py

# Verify staged changes
git diff --staged

# Commit with message
git commit -m "feat(memory): add L1/L2 consolidation"

# Make more changes if needed
vim backend/tests/test_memory_service.py
git add backend/tests/test_memory_service.py
git commit -m "test(memory): add consolidation tests"

# Push to remote
git push origin feature/memory-l1-consolidation
```

### Syncing with Master (Before Merge)

```bash
# 1. Ensure master is latest
git fetch origin

# 2. Rebase on master (preferred in open-source)
git rebase origin/master

# If conflicts, resolve them:
# Edit conflicted files
# git add resolved-files
# git rebase --continue

# Alternative: Merge from master (preferred in corporate)
git merge origin/master

# 3. Push rebased/merged branch
git push origin feature/your-feature -f  # -f only if rebased

# 4. Create PR
```

---

## Commit Message Standards

### Format Structure

```
<type>(<scope>): <subject>
<blank line>
<body>
<blank line>
<footer>
```

### Type Definition

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(api): add /memory POST endpoint` |
| `fix` | Bug fix | `fix(memory): prevent L1 cache eviction` |
| `refactor` | Code structure | `refactor(services): extract common logic` |
| `test` | Test-only changes | `test(memory): add L1/L2 consolidation tests` |
| `docs` | Documentation | `docs(readme): update setup instructions` |
| `chore` | Maintenance | `chore(deps): update FastAPI to 0.104` |
| `perf` | Performance | `perf(query): add missing database index` |
| `ci` | CI/CD changes | `ci(github): add type checking step` |
| `style` | Format (no logic) | `style(backend): run Black formatter` |

### Scope Definition

Scope = **area of code affected**

```
feat(memory): ...        # memory service
feat(api): ...           # API endpoints
feat(frontend): ...      # React components
fix(schema): ...         # GraphQL schema
refactor(agents): ...    # Agent code
docs(readme): ...        # Documentation
```

### Subject Line Rules

1. **Imperative mood:** "add feature", not "added feature"
2. **No period at end**
3. **Max 50 characters** (Linus Torvalds rule)
4. **Lowercase start**

**Examples:**

```
✅ GOOD:
feat(api): add POST /memories endpoint
fix(cache): resolve race condition in L1
refactor(schema): split large query into fragments

❌ BAD:
feat(api): Add POST /memories endpoint          # Capital A
feat(api): add POST /memories endpoint.          # Period
feat(api): added POST /memories endpoint that allows storing memories with full metadata  # Too long
feat(api): Added the endpoint.                   # Not imperative
```

### Body (Optional but Recommended)

**When to include:**
- Change not obvious from title
- Multiple files affected
- Important side effects
- References to issues

**Rules:**
- 72 characters per line max
- Explain **why**, not **what** (code shows what)
- Use bullet points for multiple changes

**Example:**

```
feat(memory): implement L1/L2 consolidation

Consolidates memory between Redis (L1) and PostgreSQL (L2).
Triggered on memory threshold or schedule.

Changes:
- Add ConsolidationService class
- Add consolidation schedule (5min)
- Add metrics tracking
- Handle edge cases: partial failures

Side effects:
- Redis flush during consolidation (brief)
- Slight latency increase during consolidation
```

### Footer (Optional)

**Use for:**
- Issue references: `Closes #123`
- Breaking changes: `BREAKING CHANGE: API endpoint changed`
- Co-authors: `Co-authored-by: Name <email@example.com>`

**Example:**

```
fix(auth): resolve token expiry validation

Tokens were not properly validated after expiry.
Added check in middleware.

Closes #456
```

### Real-World Examples

**Simple feature:**
```
feat(notifications): add GraphQL subscription support
```

**With explanation:**
```
feat(notifications): add GraphQL subscription support

- Implement Strawberry subscription resolver
- Add notification queue in Redis
- Integrate Apollo Client useSubscription hook
- Add proper cleanup and unsubscribe handling

Closes #789
```

**Bug fix with context:**
```
fix(memory): prevent concurrent L1/L2 write conflicts

Race condition occurred when multiple consolidations ran simultaneously.
Added Redis lock mechanism for atomic operations.

Fixes: #456, #457
```

**Refactoring:**
```
refactor(agi-tools): split 3000-line file into 4 modules

- memory_tools.py (memory operations)
- graph_tools.py (Neo4j operations)
- embedding_tools.py (embeddings)
- consolidation_tools.py (consolidation logic)

Each module now <500 lines for maintainability.
```

---

## Rollback Procedures

### Decision Tree: Which Rollback Mode?

```
Need to undo?
│
├─ Last commit wrong, want to redo?
│  └─ YES → Soft rollback (git reset --soft HEAD~1)
│
├─ Feature completely broken, start over?
│  └─ YES → Hard rollback (git reset --hard HEAD~1)
│
├─ Already pushed/merged, need to undo?
│  └─ YES → Revert (git revert <commit>)
│
└─ Need to go back multiple commits?
   └─ YES → Check reflog first (git reflog)
           Then soft/hard as needed
```

### Mode 1: Soft Rollback (Keep Changes)

**When to use:**
- Commit message wrong
- Forgot to add file
- Want to split into 2 commits
- Staged wrong files

**Command:**
```bash
git reset --soft HEAD~1
```

**What happens:**
- Undoes last commit
- Changes stay in working directory
- Changes remain staged

**Example:**

```bash
# Made commit with wrong message
git commit -m "wip: stuff"

# Undo it
git reset --soft HEAD~1

# Now all files are staged but not committed
git status
# On branch feature/something
# Changes to be committed:
#   modified: file1.py
#   modified: file2.py

# Fix and recommit properly
git commit -m "feat(scope): proper description"
```

### Mode 2: Hard Rollback (Complete Undo)

**When to use:**
- Feature fundamentally broken
- Started wrong direction
- Need complete restart
- Build is failing

**Command:**
```bash
git reset --hard HEAD~1
```

**What happens:**
- Undoes last commit completely
- Discards all changes
- Back to previous state

**⚠️ WARNING:** Changes are lost (unless in reflog).

**Example:**

```bash
# Made changes, committed, then realized broken
git commit -m "feat(api): new endpoint"

# Run tests
npm run build
# ERROR: Tests fail, backend broken

# Undo completely
git reset --hard HEAD~1

# All changes gone, back to previous state
git status
# On branch feature/notifications
# nothing to commit, working tree clean
```

### Mode 3: Revert (Create New Commit)

**When to use:**
- Already pushed to shared branch
- Already merged to master
- Need audit trail
- Collaborative work

**Command:**
```bash
git revert <commit-hash>
```

**What happens:**
- Creates **new commit** that undoes changes
- Preserves history (important for audit)
- Can push safely to shared branches

**Example:**

```bash
# See history
git log --oneline -5
# abc123d feat(api): add endpoint
# def456e fix(cache): improve performance
# ghi789j docs(readme): update

# Realize abc123d was wrong
git revert abc123d

# Git opens editor for commit message:
# Revert "feat(api): add endpoint"
#
# This reverts commit abc123d.

# Save and quit editor
# New commit created:
git log --oneline -5
# 123newc Revert "feat(api): add endpoint"
# abc123d feat(api): add endpoint
# def456e fix(cache): improve performance

# Push safely
git push origin feature/something
```

### Multiple Commits Rollback

**Scenario:** Last 3 commits all wrong

**Option 1: Soft rollback + redo**
```bash
# Go back 3 commits, keep changes
git reset --soft HEAD~3

# All 3 commits' changes staged
git status

# Review changes
git diff --staged

# Recommit properly (1 or multiple atomic commits)
git add backend/api/schema.py
git commit -m "feat(api): proper change 1"

git add backend/services/memory.py
git commit -m "feat(memory): proper change 2"
```

**Option 2: Hard rollback + restart**
```bash
# Go back 3 commits, discard everything
git reset --hard HEAD~3

# Start fresh
git add .
git commit -m "feat(scope): fresh start"
```

**Option 3: Interactive rebase (Advanced)**
```bash
# Edit last 3 commits
git rebase -i HEAD~3

# In editor, you can:
# - pick: keep commit
# - reword: change message
# - squash: combine with previous
# - drop: delete commit

# Save and follow prompts
```

### Emergency: Find and Undo Anything

**Git has reflog (reference log) - last 30 days of all actions:**

```bash
# See everything you've done
git reflog

# Output:
# abc123d HEAD@{0}: commit: feat(api): new endpoint
# def456e HEAD@{1}: commit: fix(cache): improve
# ghi789j HEAD@{2}: checkout: moving to feature/notifications

# Go back to any point
git reset --hard HEAD@{2}

# Now at state from 2 actions ago
```

**Worst case scenario:**

```bash
# Accidentally hard reset everything
git reflog

# Find good commit
git reset --hard HEAD@{5}

# Back to safe state
```

---

## Critical File Protection

### Files Requiring Backup Commit

These files contain critical logic. Create backup before modification:

1. **CLAUDE.md** - AGI instructions
2. **.claude/agents/*.md** - Agent definitions
3. **.claude/skills/** - Skill documentation
4. **backend/api/schema.py** - GraphQL schema (API contract)
5. **backend/services/*.py** - Business logic services
6. **cortex/agi_tools_mcp.py** - MCP tools (large file)
7. **cortex/consolidation.py** - Memory consolidation
8. **backend/agents/**/*.py** - LangGraph agents
9. **migrations/*.sql** - Database schema

### Backup Procedure

**Before modifying critical file:**

```bash
# 1. Create feature branch
git checkout -b refactor/file-name

# 2. Create explicit backup commit
git commit --allow-empty -m "chore: backup before critical modification

Modifying: /path/to/critical/file
Reason: [Brief reason]
Expected changes: [What will change]"

# 3. Now make modifications safely
# If things go wrong, rollback is trivial:
git reset --hard HEAD~1
```

**Example - Refactoring agi_tools_mcp.py:**

```bash
git checkout -b refactor/split-agi-tools-mcp

# Create backup
git commit --allow-empty -m "chore: backup before splitting agi_tools_mcp.py

File: cortex/agi_tools_mcp.py (2954 lines)
Reason: Refactoring into 4 modules (single responsibility)
Expected: Extract memory_tools, graph_tools, embedding_tools, consolidation_tools"

# Now split the file
# If broken: git reset --hard HEAD~1
# If OK: create checkpoint commits for each module
```

### Verification Before Modification

```bash
# Check file status
git status

# See file size/complexity
wc -l cortex/agi_tools_mcp.py

# See recent changes
git log -p --follow -n 5 -- cortex/agi_tools_mcp.py

# See who touches it recently
git log --oneline -n 10 -- cortex/agi_tools_mcp.py
```

---

## Multi-Agent Checkpoints

### Phase-Based Checkpoint Strategy

**When multiple agents work in parallel, use checkpoints:**

```
Phase 1: Analysis (ask agents) → Checkpoint 1 (analysis commit)
Phase 2: Research (research agents) → Checkpoint 2 (research commit)
Phase 3: Architecture (architect) → Checkpoint 3 (design commit)
Phase 4: Implementation (code/frontend) → Checkpoint 4 (code commit)
Phase 5: Validation (debug agents) → Checkpoint 5 (test commit)
Phase 6: Documentation (docs) → Checkpoint 6 (docs commit)
```

### Checkpoint Pattern

```bash
# Before phase starts
git status  # Clean working directory

# Phase work (agents work here)
# Multiple files modified

# After phase completes
# 1. Review changes
git diff

# 2. Stage related files
git add backend/api/schema.py
git add backend/services/memory_service.py

# 3. Commit as checkpoint
git commit -m "feat(memory): schema + service implementation (phase 4)"

# 4. Clear working directory
git status  # Should be clean

# Next phase can start cleanly
```

### Multi-Agent Example: Notifications Feature

```bash
# Setup
git checkout -b feature/notifications-system
git commit --allow-empty -m "chore: phase 0 - initialization"

# Phase 1: Explore existing
Task(ask, "Scan backend/services/event*.py")
Task(ask, "Scan frontend/components/notif*.tsx")
git add .
git commit -m "docs(analysis): current notification exploration"

# Phase 2: Research
Task(research, "GraphQL Subscriptions best practices")
Task(research, "Apollo Client useSubscription hook")
git add .
git commit -m "docs(research): subscription patterns research"

# Phase 3: Architecture
Task(architect, "Design notifications GraphQL subscriptions")
git add .claude/designs/notifications_architecture.md
git commit -m "docs(architecture): notification system design"

# Phase 4: Implementation (parallel)
Task(code, "Backend subscription resolver")
Task(frontend, "React useNotificationSubscription hook")
Task(code, "Database migration for notifications")
# Wait for all 3 to complete
git add backend/ frontend/ migrations/
git commit -m "feat(notifications): backend resolver + frontend hook + DB migration"

# Phase 5: Validation (parallel)
Task(debug, "Test backend subscription")
Task(debug, "Test frontend hook")
Task(debug, "Test integration E2E")
# Wait for all tests
git add tests/
git commit -m "test(notifications): all tests passing"

# Phase 6: Documentation
Task(docs, "Document notification system")
git add docs/
git commit -m "docs(notifications): API documentation + setup guide"

# Ready for merge
git push origin feature/notifications-system
```

---

## Pre/Post Modification Patterns

### PRE-Modification Pattern

**Before making significant changes:**

```bash
# 1. Ensure clean state
git status  # Should show "nothing to commit"
git log --oneline -1  # Verify last commit is good

# 2. Create feature branch
git checkout -b feature/or/refactor/your-name

# 3. Create checkpoint commit (optional but recommended)
git commit --allow-empty -m "chore: checkpoint before [change type]

Scope: [what files will change]
Reason: [why making this change]
Approach: [how will it be done]"

# 4. Now safe to make changes
# If anything goes wrong: git reset --hard HEAD~1
```

### POST-Modification Pattern (Atomic Commits)

**After each logical change completes:**

```bash
# 1. Review what changed
git status
git diff

# 2. Stage related changes only
git add backend/api/schema.py
git add backend/services/memory_service.py
# Don't use git add . unless it's all related

# 3. Verify staged changes
git diff --staged

# 4. Commit with clear message
git commit -m "feat(memory): add L1/L2 consolidation"

# 5. Next logical change?
# Repeat: edit → stage → commit

# 6. When all changes done, push
git push origin feature/your-branch
```

### Pattern: Split Large Feature into Atomic Commits

**Scenario:** Implementing large feature with 10 modified files

**Wrong approach (1 giant commit):**
```bash
git add .
git commit -m "feat: implement notifications"  # Too big
```

**Right approach (3 atomic commits):**
```bash
# Commit 1: API contract
git add backend/api/schema.py
git add backend/schemas/notification.py
git commit -m "feat(api): add notification GraphQL types"

# Commit 2: Business logic
git add backend/services/notification_service.py
git add backend/models/notification.py
git commit -m "feat(service): implement notification service"

# Commit 3: Integration
git add backend/routes/notifications.py
git add cortex/agi_tools_mcp.py
git commit -m "feat(routes): add notification endpoints"

# Each commit is reviewable independently
git log --oneline -3
# abc123d feat(routes): add notification endpoints
# def456e feat(service): implement notification service
# ghi789j feat(api): add notification GraphQL types
```

---

## Troubleshooting

### "I committed wrong file!"

```bash
# If just committed (not pushed):
git reset --soft HEAD~1

# Remove wrong file from staged
git reset HEAD <wrong-file>

# Stage correct files
git add <correct-files>

# Commit properly
git commit -m "feat(scope): description"
```

### "I committed to master instead of feature branch!"

```bash
# 1. Undo commit from master
git reset --soft HEAD~1

# 2. Create feature branch with changes
git checkout -b feature/your-feature

# 3. Commit on feature branch
git add .
git commit -m "feat(scope): description"

# 4. Go back to master (ensure clean)
git checkout master
git status  # Should be clean
```

### "I want to undo last commit but keep files"

```bash
git reset --soft HEAD~1
git status  # Files staged, ready to modify or recommit
```

### "I want to completely undo last commit"

```bash
git reset --hard HEAD~1
# Everything gone, back to previous state
```

### "I accidentally pushed broken code!"

```bash
# 1. Fix locally first
# (edit files)
git add .
git commit -m "fix: revert broken changes"

# 2. Push fix
git push origin feature/your-feature

# 3. If critical, revert entire commit
git revert <commit-hash>
git push origin master
```

### "I need to see what changed in specific commit"

```bash
git show <commit-hash>

# Or specific file in commit
git show <commit-hash> -- path/to/file
```

### "I lost my changes!"

```bash
# Check reflog (last 30 days)
git reflog

# Find your commit
git reset --hard HEAD@{5}

# Back to where you were
```

### "Feature branch is out of sync with master"

```bash
# Update from master
git fetch origin

# Option 1: Rebase (preferred in open-source)
git rebase origin/master

# Option 2: Merge (preferred in corporate)
git merge origin/master

# Push updated branch
git push origin feature/your-feature
```

### "Multiple commits need cleanup before merge"

```bash
# Interactive rebase (squash commits)
git rebase -i origin/master

# In editor, mark first commit as 'pick', others as 'squash'
# Save and follow prompts
```

---

## Integration with CI/CD

### Pre-Commit Hook

**Runs before commit allowed:**

```bash
# Checks for:
- Code format (Black, Prettier)
- Linting (Ruff, ESLint)
- Type checking (mypy, TypeScript)
- Secrets (no API keys in code)

# If fails: Fix and retry commit
```

### Pre-Push Hook

**Runs before push to remote:**

```bash
# Checks for:
- All tests pass (pytest)
- Build succeeds (npm)
- No untracked files

# If fails: Fix and retry push
```

### CI Pipeline (On Push)

```bash
# Runs on GitHub/GitLab:
1. Full test suite
2. Type checking
3. Security scan
4. Code coverage
5. Build frontend/backend
6. Deploy to staging

# If fails: PR blocked until fixed
```

---

## Summary Checklist

**Feature Development:**
- [ ] Create feature branch: `git checkout -b feature/descriptive-name`
- [ ] Create checkpoint (optional): `git commit --allow-empty -m "chore: checkpoint"`
- [ ] Make changes
- [ ] Atomic commits: `git add <related> && git commit -m "feat(scope): desc"`
- [ ] Tests pass: `pytest` and `npm run build`
- [ ] Push: `git push origin feature/your-feature`
- [ ] Create PR for review
- [ ] Merge to master

**Critical File Modification:**
- [ ] Create feature branch
- [ ] Create backup commit
- [ ] Make one logical change
- [ ] Commit atomically
- [ ] Test thoroughly
- [ ] Push and review

**If Problems:**
- [ ] Undo last commit (keep files): `git reset --soft HEAD~1`
- [ ] Undo last commit (discard files): `git reset --hard HEAD~1`
- [ ] Revert pushed commit: `git revert <hash> && git push`
- [ ] Lost commits? Check: `git reflog`

---

**Enterprise Patterns Referenced:** Google (atomic commits), Meta (feature branches), GitFlow, GitHub
