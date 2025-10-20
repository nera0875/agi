---
name: "Task Decomposition"
description: "How to break down complex tasks into independent micro-tasks with optimal deadlines and parallelization strategies."
categories: ["system", "orchestration", "decomposition", "efficiency"]
tags: ["parallel", "micro-tasks", "deadlines", "isolation", "CEO-mindset", "task-planning"]
version: "1.0.0"
enabled: true
---

## Overview

**Task Decomposition** is the art of breaking complex work into independent micro-tasks that can run in parallel. It's the CEO's superpower: instead of one agent spending 5 minutes on a big task, launch 10 agents in parallel, each doing 30 seconds of focused work.

**Core insight:** Decomposition → Parallelization → Aggregation = 10-20x speedup

## When to Use This Skill

### Use Task Decomposition when:
- Task will take >30 seconds to complete
- Task has multiple independent steps
- Multiple agents could work on different parts simultaneously
- Need to analyze large codebase (50+ files)
- Building complex feature (multiple backend/frontend components)
- Doing infrastructure checks (multiple systems to verify)

### Don't use when:
- Task is simple and focused (<20s effort)
- Task has hard dependencies (step 2 needs step 1 output)
- Only 1 agent type applies
- Task is already fully parallelized

## Related Skills

- **CEO Mindset** - Why parallelization matters (business perspective)
- **Workflow Implementation** - How to execute decomposed tasks
- **Agent Collaboration** - How agents work together

## Key Principles

### Principle 1: Independence = Parallelizable

**Rule:** If Task A doesn't need output of Task B, they're independent and can run in parallel.

```python
# ❌ Dependent (sequential only)
Task 1: "Design architecture"
Task 2: "Implement based on architecture"
→ Must run one after the other

# ✅ Independent (parallel OK)
Task 1: "Scan backend/services/"
Task 2: "Scan backend/api/"
Task 3: "Scan backend/routes/"
→ Can run simultaneously
```

### Principle 2: Scope Isolation

**Rule:** Each micro-task has ONE clear, non-overlapping scope.

```python
# ❌ Overlapping (agents step on each other)
Agent 1: "Scan backend/"
Agent 2: "Scan backend/"
→ Both scanning same files = wasted work

# ✅ Clear partition (divide and conquer)
Agent 1: "Scan backend/services/[a-m]*.py"
Agent 2: "Scan backend/services/[n-z]*.py"
Agent 3: "Scan backend/api/"
→ Each covers unique part
```

### Principle 3: Deadline Discipline

**Rule:** Agents work faster with time pressure. 70% of useful results in 30s beats 100% in 5 minutes.

```python
# ❌ No deadline (agent takes own time)
"Analyze thoroughly"
→ 5 minutes of deliberation

# ✅ Hard deadline (agent rushes)
"DEADLINE: 30s MAX
PARTIAL OK: Return what you have if timeout"
→ 30 seconds, 80% useful
```

### Principle 4: Ultra-Precise Prompts

**Rule:** Vague prompt = confused agent = slow + wrong results.

```python
# ❌ Vague (agent confused)
"Analyze the backend"
→ Agent doesn't know what to do

# ✅ Precise (agent knows exactly)
"Scan backend/services/memory*.py

TASK:
1. List all classes
2. For each class, extract public methods
3. Ignore private/dunder methods

DEADLINE: 20s
PARTIAL OK: Return what you scanned

FORMAT JSON:
{
  'files': [...],
  'classes': [
    {'name': 'X', 'methods': [...]},
    ...
  ]
}"
```

## Decomposition Strategy

### Step 1: Understand the Need

Analyze user request to identify **all sub-tasks**:

```python
# User: "Check if backend is healthy"

# CEO thinks:
- Check PostgreSQL
- Check Neo4j
- Check Redis
- Check API costs
- Check logs for errors
→ 5 independent checks!
```

### Step 2: Identify Independent Tasks

Use this test:
- If Task A output ≠ needed for Task B
- Then A and B are independent
- Then A and B can run in parallel

```python
# Independent tests:
Test("Does PostgreSQL respond?")  # Needs: DB connection
Test("Does Redis respond?")       # Needs: Redis connection
→ No dependencies, parallel OK

# Dependent:
Design("System architecture")     # Needs: Requirements
Implement("Based on design")      # Needs: Design output
→ Sequential required
```

### Step 3: Partition Work Fairly

Each agent should get ~20-60 seconds of focused work:

```python
# Bad: One agent overloaded (5 min work)
Task(ask, "Analyze entire backend")

# Good: 5 agents, each ~30s
Task(ask, "Scan services/[a-d]*.py")      # Agent 1
Task(ask, "Scan services/[e-h]*.py")      # Agent 2
Task(ask, "Scan services/[i-l]*.py")      # Agent 3
Task(ask, "Scan api/ endpoints")          # Agent 4
Task(ask, "Find *_wrapper.py files")      # Agent 5
```

**Heuristic:**
- Read-only exploration: 3-5 parallel agents
- Data scanning: 5-10 parallel agents (by partition)
- Implementation: 2-3 parallel agents (complex features)
- Architecture: 1 agent (requires full context)

### Step 4: Choose Right Agent Type

Match agent to task type:

```python
ask         → Code exploration (read-only, fast)
research    → External research (docs, web)
architect   → System design (high-level planning)
code        → Backend implementation (Python/FastAPI)
frontend    → React/UI implementation (TypeScript)
debug       → Testing & validation (pytest)
docs        → Documentation (README, API docs)
sre         → Infrastructure monitoring (health checks)
```

### Step 5: Create Ultra-Precise Prompts

Template for maximum clarity:

```python
"""
[CONTEXT - 1-2 sentences what this task is part of]

TASK:
1. [Action 1]
2. [Action 2]
3. [Action 3]

SCOPE:
- File pattern: [exactly what files]
- Max items: [if too many, sample first N]
- Ignore: [what to skip]

DEADLINE: [X] seconds MAX
PARTIAL OK: If timeout, return what you have

FORMAT:
```json
{
  "status": "success|partial|timeout",
  "completed": "XX%",
  "result": {...}
}
```

EXAMPLE OUTPUT:
[Show exactly what you want back]
"""
```

**Example prompt:**
```python
"""
Part of backend health audit.

TASK:
1. Scan backend/services/ directory
2. List all Python files
3. For each file, extract class names

SCOPE:
- Pattern: backend/services/*.py
- Max files: 20 (stop if more)
- Ignore: __pycache__, *.pyc

DEADLINE: 20 seconds MAX
PARTIAL OK: Return files scanned so far

FORMAT JSON:
{
  "status": "success|partial",
  "completed_pct": 100,
  "files_scanned": [...],
  "total_classes": 15,
  "classes": [
    {"file": "memory_service.py", "names": ["MemoryService"]},
    ...
  ]
}
"""
```

## Decomposition Patterns

### Pattern 1: File Scanning (Alphabetic Partition)

**When:** Need to scan 50+ files but 1 agent would timeout

**Strategy:** Partition by filename prefix

```python
# 67 files in backend/services/
# → Split into 5 agents

patterns = [
    "backend/services/[a-d]*.py",
    "backend/services/[e-h]*.py",
    "backend/services/[i-l]*.py",
    "backend/services/[m-p]*.py",
    "backend/services/[q-z]*.py",
]

for pattern in patterns:
    Task(ask, f"Scan {pattern}, extract classes")
```

### Pattern 2: Independent System Checks

**When:** Multiple systems to check (DB, cache, API, logs)

**Strategy:** One agent per system

```python
# Infrastructure health check
Task(sre, "Check PostgreSQL - connections, queries, performance")
Task(sre, "Check Redis - memory, keys, operations")
Task(sre, "Check Neo4j - nodes, relationships, queries")
Task(sre, "Check API costs - Anthropic, Voyage, other")
```

### Pattern 3: Component Implementation

**When:** Feature needs backend + frontend + migrations + tests

**Strategy:** One agent per component

```python
# Implement notifications feature
Task(code, "Backend: GraphQL subscription")
Task(frontend, "Frontend: useSubscription hook + UI")
Task(code, "Database: notifications migration")
Task(code, "Config: env variables")
```

### Pattern 4: Multi-Phase Pipeline

**When:** Need sequential phases (understand → design → code → test)

**Strategy:** Parallelize within each phase

```python
# Phase 1: Understanding (parallel)
Task(ask, "Scan backend/")
Task(ask, "Scan frontend/")
Task(ask, "Check existing patterns")
# Wait for all results...

# Phase 2: Research (parallel)
Task(research, "Best practices")
Task(research, "Library docs")
# Wait for all results...

# Phase 3: Architecture (single)
Task(architect, "Design based on findings")
# Wait...

# Phase 4: Implementation (parallel)
Task(code, "Implement backend")
Task(frontend, "Implement frontend")
# Wait...

# Phase 5: Validation (parallel)
Task(debug, "Test backend")
Task(debug, "Test frontend")
Task(debug, "E2E test")
```

## Timeout Management

### Rule 1: DEADLINES ARE STRICT (CEO Discipline)

Agents work 10-20x faster with hard time pressure. **70% useful results in 30s beats 100% in 5 minutes.**

```python
# ❌ WRONG (agent takes own time)
Task(ask, "Scan backend/")
→ 5 minutes, agent perfectionism

# ✅ CORRECT (hard deadline)
Task(ask, """
Scan backend/

DEADLINE: 30 seconds MAX
PARTIAL OK: Return what you have if timeout
""")
→ 30 seconds, 80% useful
```

**Golden Rule:** `DEADLINE` field is MANDATORY in every prompt.

### Rule 2: Timeouts by Task Type (Reference Table)

**Strict deadlines - ALWAYS include in prompts:**

| Task Type | Timeout | Example | Notes |
|-----------|---------|---------|-------|
| **Scan 1-5 files** | 10s MAX | Extract classes from 1-5 .py files | Fast glob + read |
| **Scan 10-20 files** | 20s MAX | Scan services/, list functions | Sample if more |
| **Scan 50+ files** | 5 agents × 20s | Partition by prefix (a-z) | Parallelize! |
| **Grep pattern** | 15s MAX | Find all "class.*X" in backend/ | Ripgrep = quick |
| **Health check 1 system** | 15s MAX | PostgreSQL connections + queries | 1 DB check |
| **Architecture design** | 30-60s | Plan multi-phase system | Requires thinking |
| **Code 1 function** | 30s MAX | Backend endpoint or React hook | Focused scope |
| **Code 1 API/mutation** | 60s MAX | Full endpoint implementation | Medium complexity |
| **Run tests (single file)** | 20s MAX | pytest backend/tests/test_X.py | Quick validation |
| **Documentation section** | 30s MAX | Update README section | Focused writing |
| **Full feature (3+ parts)** | 2-3 min | Backend + Frontend + Migrations | Break into phases |

**Formula for custom deadlines:**
```
Deadline = (Expected_Duration × 1.5) + 5s buffer (minimum 10s)
```

Example:
```python
# Task expected to take 30s
deadline = (30 * 1.5) + 5 = 50 seconds

# Agent feels pressure, finishes in 40s vs 60s
```

### Rule 3: Format Prompt Standard (MANDATORY)

**EVERY task to agents MUST include:**

```python
Task(agent_type, """
[1-2 sentences: CONTEXT]
What is this task part of?

SCOPE:
- Files/data: [EXACTLY what to process]
- Max items: [If >N, sample first N]
- Ignore: [What to skip]

TASK:
1. [Action 1]
2. [Action 2]
3. [Action 3]

DEADLINE: [X] seconds MAX
PARTIAL OK: If timeout, return what you have

FORMAT: Return JSON exactly:
{
  "status": "complete|partial|timeout",
  "completed_pct": 100,
  ...
}
""")
```

**Required fields:**
- ✅ `DEADLINE: X seconds MAX`
- ✅ `PARTIAL OK:` clause
- ✅ `FORMAT: JSON` specification
- ✅ Clear `SCOPE:` boundaries

### Rule 4: Accept Partial Results (70% Rule)

Incomplete results are ACCEPTABLE if >70% complete.

```python
# ✅ GOOD (75% complete)
{
  "status": "partial",
  "completed_pct": 75,
  "files": 3,
  "result": [...]
}
→ Accept this, meets 70% threshold

# ❌ BAD (40% complete)
{
  "status": "timeout",
  "completed_pct": 40,
  "result": [...]
}
→ Reject, below 70% threshold
```

**In aggregation:**
```python
results = [
    {"status": "complete", "items": 10},    # 100% ✅
    {"status": "partial", "completed_pct": 80, "items": 7},   # 80% ✅
    {"status": "timeout", "completed_pct": 40, "items": 2},   # 40% ❌
]

# Filter: Keep >70%
good_results = [r for r in results
               if r.get("completed_pct", 100) >= 70]

# Success if ≥70% of agents succeed
success_rate = len(good_results) / len(results)
if success_rate >= 0.7:
    aggregate(good_results)  # GO
else:
    retry_with_smaller_scope()  # Retry
```

### Rule 5: Retry Strategy (Smart Fallback)

**Attempt 1: Big scope, short deadline**
```python
result = Task(ask, "Scan backend/services/", timeout=20)
```

**If timeout < 70%:**
```python
# Attempt 2: Split into smaller partitions
result1 = Task(ask, "Scan backend/services/[a-m]*.py", timeout=20)
result2 = Task(ask, "Scan backend/services/[n-z]*.py", timeout=20)
final = merge(result1, result2)

# Total time: 20s original + 20s retry = 40s
# vs forcing one agent to work forever
```

### Rule 6: Real-World Timeout Discipline

**Anti-patterns to AVOID:**

| Anti-Pattern | Result | Fix |
|--------------|--------|-----|
| No deadline | 5-10 min (agent perfectionism) | Set `DEADLINE: 30s MAX` |
| Vague scope | Agent confused, overthinks | Be ultra-precise: "files: services/*.py" |
| Perfectionism pressure | "Find everything" | Accept partial: "PARTIAL OK" |
| Single agent big task | 5 min slow | Parallelize: 5 agents × 1 min |
| No partial results | All-or-nothing failure | `completed_pct: 70%` OK |

**Pragmatism wins:**
```python
# ❌ WRONG (perfectionist)
"Analyze thoroughly, find everything"
→ Agent takes 5 minutes
→ We wait 5 minutes

# ✅ RIGHT (pragmatist CEO)
"""
DEADLINE: 30s MAX
PARTIAL OK: Return top 80%, stop if timeout
"""
→ Agent rushes, finishes in 30s
→ We get 80% useful in 30s instead of 100% in 5 min
```

## Aggregation Strategy

### Template: Combine N Results

```python
def aggregate(results):
    """Combine multiple agent outputs into single result"""

    # 1. Filter valid results
    valid = [r for r in results if r.get("status") in ["success", "partial"]]
    failed = [r for r in results if r.get("status") == "timeout" and r.get("completed", 0) < 70]

    # 2. Combine data structures
    all_items = []
    for r in valid:
        all_items.extend(r.get("items", []))

    # 3. Deduplicate (if needed)
    unique_items = list(set(all_items))

    # 4. Summary stats
    return {
        "status": "complete" if not failed else "partial",
        "total_results": len(results),
        "successful": len(valid),
        "failed": len(failed),
        "success_rate": len(valid) / len(results),
        "items": unique_items,
        "count": len(unique_items)
    }
```

### Example Aggregation

**Agent outputs:**
```python
result1 = {"files": ["a.py", "b.py"], "classes": 5}
result2 = {"files": ["c.py", "d.py"], "classes": 8}
result3 = {"timeout": True, "files": ["e.py"], "classes": 2}
```

**CEO aggregates:**
```python
all_files = ["a.py", "b.py", "c.py", "d.py", "e.py"]
total_classes = 5 + 8 + 2 = 15
success_rate = 2/3 = 67%

summary = {
    "status": "complete",
    "files": 5,
    "classes": 15,
    "agents": 3,
    "successful_agents": 3,
    "message": "Scanned 5 files, found 15 classes"
}
```

## Anti-Patterns to Avoid

| Pattern | Bad ❌ | Good ✅ | Why |
|---------|--------|--------|-----|
| **Scope Clarity** | "Analyze backend" | "Scan services/, list classes" | Vague = agent confused |
| **Overlapping** | 2 agents scan same files | Each agent gets unique partition | Wasted work |
| **Deadline** | "Do your best" | "DEADLINE: 30s MAX" | Pressure = faster |
| **Parallelization** | Sequential tasks | Independent tasks in parallel | 10x speedup |
| **Aggregation** | Manual text merge | Programmatic JSON combine | Reliable + quick |
| **Error Handling** | Fail if any timeout | Accept 70%+ complete | Pragmatism wins |
| **Scope Size** | 1 agent scans 100 files | 5 agents × 20 files each | Balanced load |

## Checklist: Before Decomposing

**Task Analysis:**
- [ ] Will this take >30 seconds?
- [ ] Can it be split into ≥3 independent parts?
- [ ] Are the parts truly independent (no cross-dependencies)?
- [ ] Can different agents work on different parts?

**Decomposition Plan:**
- [ ] Identified all micro-tasks (list them)?
- [ ] Each task has clear scope (files/data exactly)?
- [ ] Chose right agent type for each?
- [ ] Partitions are non-overlapping?
- [ ] Load is balanced (~30s per agent)?

**Execution Setup:**
- [ ] Created ultra-precise prompts?
- [ ] Set reasonable deadlines (20-60s)?
- [ ] Added "PARTIAL OK" in prompts?
- [ ] Planned aggregation strategy?
- [ ] Prepared JSON format for results?

**Post-Execution:**
- [ ] Handled timeouts gracefully?
- [ ] Aggregated results correctly?
- [ ] Checked success rate (>70%)?
- [ ] Synthesized findings for user?

## Examples

### Example 1: Large Codebase Scan (5 files → 1 agent, 50+ files → 5 agents)

```python
# Problem: Scan 67 files in backend/services/
# Solo approach: 1 agent × 5 min = slow
# CEO approach: 5 agents × 1 min = 5x faster

tasks = [
    ("services/[a-d]*.py", "Agent 1"),
    ("services/[e-h]*.py", "Agent 2"),
    ("services/[i-l]*.py", "Agent 3"),
    ("services/[m-p]*.py", "Agent 4"),
    ("services/[q-z]*.py", "Agent 5"),
]

for pattern, agent_name in tasks:
    Task(ask, f"""
    Scan backend/{pattern}

    TASK: List all classes and public methods

    SCOPE: Pattern={pattern}, max 20 files

    DEADLINE: 20s MAX
    PARTIAL OK: Return scanned files

    FORMAT JSON: {{"files": [...], "classes": [...]}}
    """)

# Aggregation: CEO combines 5 results into 1 master list
```

### Example 2: Health Check (DB + Cache + API + Logs)

```python
# Problem: Check 4 independent systems
# Solo: Check one, wait for result, check next = 10 min
# CEO: Check all 4 in parallel = 2.5 min

Task(sre, "Check PostgreSQL: connections, slow queries, disk space")
Task(sre, "Check Redis: memory usage, key count, latency")
Task(sre, "Check Neo4j: node count, relationship count, query performance")
Task(sre, "Check API costs: Anthropic, Voyage, other services")

# All 4 run simultaneously, each takes ~30s
# Total: 30s (not 2 min sequential)
```

### Example 3: Feature Implementation (Backend + Frontend + Migrations)

```python
# Problem: Build notifications feature with 3 components
# Solo: Backend (1h) → Frontend (1h) → Migrations (30m) = 2.5h
# CEO: All 3 in parallel = 1h

Task(code, """
Backend: GraphQL subscription for notifications

Context: Notifications feature requires pub/sub

TASK:
1. Create onNotification subscription in schema.py
2. Implement resolver with event listener
3. Add send_notification mutation

DEADLINE: 60s
FORMAT JSON: {"status": "done", "files_modified": [...]}
""")

Task(frontend, """
Frontend: useNotificationSubscription hook

TASK:
1. Create hook with Apollo useSubscription
2. Create NotificationUI component
3. Connect to GraphQL subscription

DEADLINE: 60s
FORMAT JSON: {"status": "done", "components": [...]}
""")

Task(code, """
Database: Notifications table migration

TASK:
1. Create migration file
2. Define notifications schema
3. Add indexes

DEADLINE: 30s
FORMAT JSON: {"status": "done", "migration": "..."}
""")

# All 3 code in parallel, takes ~1min total
# vs 2.5h if sequential
```

---

## Related Sections

- **CEO Mindset** - Why delegation matters
- **Workflow Implementation** - How to execute plan
- **Agent Types** - Choosing the right agent

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System - Orchestration
**Audience:** CEO/Director Mode (Advanced)
