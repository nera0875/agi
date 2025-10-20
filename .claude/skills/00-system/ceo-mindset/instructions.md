# CEO Mindset - Detailed Instructions for Parallel Delegation

## Executive Summary

Transform from solo worker to CEO directing 50+ agents. Key insight: **decompose complex tasks into independent micro-tasks, delegate to agents in parallel, aggregate results.**

Single director (smart, slow) + many workers (dumb, fast) = exponential output.

---

## Part 1: CEO's Core Responsibilities

### What CEO Does

1. **Analyze** user request (5-10s)
2. **Decompose** into micro-tasks (5-10s)
3. **Assign** to agents (parallel) (20-60s work)
4. **Aggregate** results (5-10s)
5. **Synthesize** into answer for user (5-10s)

### What CEO DOESN'T Do

- ❌ Direct coding (use code agent)
- ❌ Manual file scanning (use ask agent)
- ❌ External research (use research agent)
- ❌ Sequential boring work

### Token Economy

**Solo worker approach:**
- You do all work directly: 5,000-10,000 tokens per task
- Slow (3-5 minutes)

**CEO approach:**
- You: 100-200 tokens thinking + 50 tokens aggregation × 6 phases = 400 tokens
- Agents: 500 tokens × 6 phases (isolated conversations) = 3,000 tokens
- **Total: 3,400 tokens (66% savings)**
- Fast (1-2 minutes)

**Winner: CEO always**

---

## Part 2: Decomposition Strategy

### Step 1: Understand the Need

```python
# User asks: "Check if backend is healthy"

# CEO thinks:
- Need to check databases (PostgreSQL, Neo4j, Redis)
- Need to check API costs
- Need to check logs for errors
- Need to check performance metrics
- Can ALL be done in parallel!

# Result: 5 independent tasks
```

### Step 2: Identify Independent Tasks

**Rule: If task A doesn't need output of task B, they're independent**

```python
# Independent ✅
- Scan services/
- Scan api/
- Scan routes/
→ Can all run at same time

# Dependent ❌
- Design architecture
- Implement based on design
→ Implementation needs architecture first
→ Must run sequential
```

### Step 3: Partition Work Fairly

**Each agent should get ~30 seconds of work**

```python
# Bad: One agent gets 5 minutes of work
Task(ask, "Analyze entire backend")

# Good: 5 agents, each ~30s
Task(ask, "Scan services/ - find classes only")
Task(ask, "Scan api/ - list endpoints")
Task(ask, "Scan routes/ - list routes")
Task(ask, "Scan agents/ - list agent names")
Task(ask, "Find all *_wrapper.py files")
```

### Step 4: Choose Right Agent Type

```
ask         → Read-only code exploration
research    → External research (docs, web)
architect   → System design
code        → Backend implementation
frontend    → React/UI implementation
debug       → Testing/validation
docs        → Documentation
sre         → Infrastructure monitoring
```

### Step 5: Create Ultra-Precise Prompts

**Bad prompt (agent confused, slow):**
```
"Analyze services"
```

**Good prompt (agent knows exactly, fast):**
```
"Scan backend/services/memory*.py

TASK:
1. List all classes defined
2. For each class, list public methods
3. Ignore __init__, private methods

DEADLINE: 20 seconds
PARTIAL OK: If timeout, return what you scanned

FORMAT JSON:
{
  "files": ["memory_service.py", ...],
  "classes": [
    {
      "name": "MemoryService",
      "methods": ["get_memory", "store_memory", ...]
    },
    ...
  ]
}
"
```

**Key differences:**
- Exact file pattern
- Specific actions (list, find, etc.)
- Clear format (JSON structure)
- Deadline
- Partial OK allowed

---

## Part 3: Parallel Task Launching

### Rule 1: Launch All Tasks Together

```python
# ❌ Sequential (slow)
result1 = Task(ask, "Scan services/")
print(result1)
result2 = Task(ask, "Scan api/")
print(result2)
# Total time: T1 + T2 + T3 = 90s

# ✅ Parallel (fast)
task1 = Task(ask, "Scan services/")
task2 = Task(ask, "Scan api/")
task3 = Task(ask, "Scan routes/")
# All run simultaneously
# Total time: max(T1, T2, T3) = 30s
```

### Rule 2: Scope Isolation

Each agent gets ONE clear scope, no overlap:

```python
# ❌ Overlapping (agents step on each other)
Agent 1: "Scan backend/"
Agent 2: "Scan backend/"

# ✅ Clear partition (Divide and Conquer)
Agent 1: "Scan backend/services/[a-j]*.py"
Agent 2: "Scan backend/services/[k-z]*.py"
Agent 3: "Scan backend/api/"
```

### Rule 3: Deadline Pressure

Agents work faster with deadlines:

```python
# ❌ No deadline (agent takes own time)
"Analyze and provide thorough report"
→ Takes 5 minutes

# ✅ Deadline (agent rushes)
"DEADLINE: 20 seconds MAX
PARTIAL OK: Return what you have if timeout"
→ Takes 20 seconds, 80% complete is useful
→ Better than perfect but slow
```

### Rule 4: Handle Timeouts

```python
results = await launch_tasks([
    Task(ask, "Scan api/", timeout=20),
    Task(ask, "Scan services/", timeout=20),
    Task(ask, "Scan routes/", timeout=20),
])

# Some might timeout
for result in results:
    if result.get("timeout"):
        print(f"Partial result (timeout): {result['completed']}%")
    else:
        print(f"Complete result")

# CEO decision: Use partial results if >70% complete
complete = [r for r in results if not r.get("timeout")]
partial = [r for r in results if r.get("timeout") and r.get("completed", 0) > 70]
usable = complete + partial
if len(usable) / len(results) > 0.7:
    # Enough data, continue
    aggregate(usable)
else:
    # Too much timeout, retry smaller scope
    retry_with_smaller_scope(partial)
```

---

## Part 4: Result Aggregation

### Aggregation Pattern

```python
def aggregate_results(results: List[Dict]) -> Dict:
    """Combine N agent results into single vision"""

    # 1. Validate results
    valid = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    # 2. Merge data
    merged = {}
    for result in valid:
        for key, value in result.items():
            if key not in merged:
                merged[key] = []
            merged[key].extend(value if isinstance(value, list) else [value])

    # 3. Deduplicate
    for key in merged:
        merged[key] = list(set(merged[key]))

    # 4. Summarize
    summary = {
        "total_items": sum(len(v) for v in merged.values()),
        "successful_agents": len(valid),
        "failed_agents": len(failed),
        "data": merged
    }

    return summary
```

### Example Aggregation

**Agent results:**
```python
result1 = {"files": ["a.py", "b.py"], "classes": 5, "errors": 0}
result2 = {"files": ["c.py", "d.py"], "classes": 8, "errors": 1}
result3 = {"timeout": True, "files": ["e.py"], "classes": 2}
```

**CEO aggregates:**
```python
all_files = ["a.py", "b.py", "c.py", "d.py", "e.py"]
total_classes = 5 + 8 + 2 = 15
total_errors = 0 + 1 = 1
success_rate = 2/3 = 67%

# Synthesis:
"Scanned 5 files, found 15 classes, 1 error (timeout on result3)"
```

---

## Part 5: 6-Phase Workflow

### Phase 1: UNDERSTANDING (Parallel - Ask Agents)

**Goal:** Understand current state

**Tasks:**
- Scan existing code structure
- Find similar patterns
- Check naming conventions
- Find duplicates

**Example:**
```python
Task(ask, "Scan backend/services/ - list all classes")
Task(ask, "Scan backend/api/ - list all endpoints")
Task(ask, "Scan tests/ - find test files")
Task(ask, "Find all *_wrapper.py files - possible duplicates")
```

**Agent Type:** `ask` (read-only exploration)

**Deadline:** 20 seconds per task

**Output:** JSON with findings

**CEO Action:** Aggregate, identify patterns/issues

---

### Phase 2: RESEARCH (Parallel - Research Agents)

**Goal:** External knowledge gathering

**Tasks:**
- Best practices for technology
- Library documentation
- Example implementations
- Industry standards

**Example:**
```python
Task(research, "GraphQL Subscriptions best practices 2025")
Task(research, "React hooks for real-time subscriptions")
Task(research, "PostgreSQL performance tips for subscriptions")
```

**Agent Type:** `research` (web search, doc fetching)

**Deadline:** 30 seconds per task

**Output:** Markdown with findings

**CEO Action:** Extract actionable insights

---

### Phase 3: ARCHITECTURE (Single - Architect)

**Goal:** Design solution

**Tasks:**
- Create architecture plan
- Evaluate trade-offs
- Define data structures
- Plan phases

**Example:**
```python
Task(architect, """
Design real-time notifications system

Context:
- Backend has EventEmitter
- Frontend needs useSubscription hook
- Database needs notifications table

Options:
1. GraphQL Subscriptions
2. WebSocket + custom protocol
3. Server-Sent Events (SSE)

Requirements:
- Low latency (<100ms)
- Scalable (10k concurrent users)
- Easy frontend integration

Return:
{
  "choice": "GraphQL Subscriptions",
  "reasoning": "...",
  "phases": [
    {"phase": 1, "task": "Backend subscription"},
    {"phase": 2, "task": "Frontend hook"},
    ...
  ]
}
""")
```

**Agent Type:** `architect` (design, not code)

**Deadline:** 60 seconds

**Output:** JSON architecture plan

**CEO Action:** Review, validate, use for Phase 4

---

### Phase 4: IMPLEMENTATION (Parallel - Code/Frontend)

**Goal:** Build the solution

**Tasks:**
- Backend code
- Frontend code
- Database migrations
- Configuration

**Example:**
```python
Task(code, "Backend: Create GraphQL subscription for notifications")
Task(frontend, "Frontend: Create useNotificationSubscription hook")
Task(code, "Database: Migration for notifications table")
Task(code, "Config: Add notification settings to .env")
```

**Agent Types:** `code` (backend), `frontend` (React)

**Deadline:** 60-120 seconds per task

**Output:** Code files (full feature complete)

**CEO Action:** Combine code pieces, resolve conflicts

---

### Phase 5: VALIDATION (Parallel - Debug Agents)

**Goal:** Ensure quality

**Tasks:**
- Unit tests
- Integration tests
- E2E tests
- Manual validation

**Example:**
```python
Task(debug, "Write and run unit tests for GraphQL subscription")
Task(debug, "Write and run integration tests backend+frontend")
Task(debug, "Write E2E test: create notification, verify in UI")
```

**Agent Type:** `debug` (testing, debugging)

**Deadline:** 60 seconds per task

**Output:** Test results + fixes

**CEO Action:** Check all pass, merge fixes

---

### Phase 6: DOCUMENTATION (Single - Docs)

**Goal:** Document for future

**Tasks:**
- README update
- API documentation
- Architecture diagram
- Changelog

**Example:**
```python
Task(docs, """
Document notifications feature

Include:
- Overview (1 paragraph)
- Architecture diagram (Mermaid)
- API documentation (subscription + fields)
- Example usage (frontend + backend)
- Configuration options
- Troubleshooting

Return: Markdown file ready for README
""")
```

**Agent Type:** `docs` (documentation)

**Deadline:** 120 seconds

**Output:** Markdown documentation

**CEO Action:** Add to README/docs

---

## Part 6: Workflow Examples

### Example 1: Backend Audit (5 minutes)

**User:** "Is the backend well-organized?"

**CEO Workflow:**

**Phase 1 (1 min):** Understanding
```python
Task(ask, "Scan backend/services/ - list all classes and their files")
Task(ask, "Scan backend/api/ - list all endpoints by route")
Task(ask, "Find all files in backend/ that shouldn't be there")
Task(ask, "Check backend/ structure - expected vs actual")
```

**Phase 2 (skip):** Research not needed (internal audit)

**Phase 3 (skip):** Architecture not needed

**Phase 4 (skip):** No implementation

**Phase 5 (skip):** No validation

**Phase 6 (1 min):** Documentation
```python
Task(docs, "Create audit report: structure analysis, findings, recommendations")
```

**Result:** Audit report in 2 minutes

---

### Example 2: New Feature (15 minutes)

**User:** "Add real-time notifications"

**CEO Workflow:**

**Phase 1 (2 min):** Understanding
```python
Task(ask, "Check existing notification code")
Task(ask, "Find WebSocket/GraphQL subscription usage")
Task(ask, "Check frontend hooks for subscriptions")
```
→ CEO finds: "No existing notifications, no subscriptions, need from scratch"

**Phase 2 (2 min):** Research
```python
Task(research, "GraphQL Subscriptions best practices")
Task(research, "Apollo Client useSubscription examples")
Task(research, "Strawberry GraphQL subscription tutorial")
```
→ CEO finds: "GraphQL Subscriptions is standard, Apollo has hooks"

**Phase 3 (1 min):** Architecture
```python
Task(architect, "Design notifications: GraphQL Subscriptions + Apollo + PostgreSQL")
```
→ CEO validates plan

**Phase 4 (5 min):** Implementation (parallel)
```python
Task(code, "Backend: GraphQL subscription resolver")
Task(frontend, "Frontend: useSubscription hook + UI component")
Task(code, "Database: notification schema and migration")
```
→ CEO combines code

**Phase 5 (3 min):** Validation (parallel)
```python
Task(debug, "Test GraphQL subscription backend")
Task(debug, "Test React hook + UI rendering")
Task(debug, "E2E: create notification, verify in UI")
```
→ CEO checks all pass

**Phase 6 (2 min):** Documentation
```python
Task(docs, "Document notifications feature in README")
```

**Total:** 15 minutes (vs 2 days solo)

---

### Example 3: Tech Debt Cleanup (10 minutes)

**User:** "Project is messy, clean it up"

**CEO Workflow:**

**Phase 1 (2 min):** Understanding (parallel)
```python
Task(ask, "Find large files (>500 lines)")
Task(ask, "Find duplicate code patterns")
Task(ask, "Find poorly named files/classes")
```

**Phase 2 (skip):** Research

**Phase 3 (2 min):** Architecture
```python
Task(architect, "Plan refactoring: prioritize by impact, create phase plan")
```

**Phase 4 (4 min):** Implementation (parallel)
```python
Task(code, "Refactor: split large files")
Task(code, "Refactor: remove duplicates")
Task(code, "Refactor: rename poorly named items")
```

**Phase 5 (2 min):** Validation
```python
Task(debug, "Run all tests after refactoring")
```

**Phase 6 (skip):** Documentation

**Total:** 10 minutes planning + 10 minutes refactoring = 20 minutes

---

## Part 7: Advanced Patterns

### Pattern 1: Cascading Tasks

**When:** Results of Phase N needed for Phase N+1

```python
# Phase 1: Understanding
understanding = Task(ask, "What notification code exists?")

# CEO analyzes results
# Phase 2: Research
if not understanding['has_subscriptions']:
    research = Task(research, "GraphQL Subscriptions best practices")
else:
    research = skip()  # Already have subscriptions

# Phase 3: Architecture based on findings
architecture = Task(architect, f"Design based on: {understanding} + {research}")
```

### Pattern 2: Adaptive Parallelization

**When:** Number of parallel tasks depends on scope

```python
# Codebase size: 100 files
# Strategy: 5 agents × 20 files each

file_patterns = [
    "backend/services/[a-e]*.py",
    "backend/services/[f-j]*.py",
    "backend/services/[k-o]*.py",
    "backend/services/[p-t]*.py",
    "backend/services/[u-z]*.py",
]

results = []
for pattern in file_patterns:
    results.append(Task(ask, f"Scan {pattern}"))

# Aggregate all
aggregated = aggregate_results(results)
```

### Pattern 3: Error Recovery

**When:** Some agents timeout or fail

```python
try:
    results = Task(ask, "Scan backend/", timeout=30)
except TimeoutError:
    # Fallback: split scope
    result1 = Task(ask, "Scan backend/services/", timeout=20)
    result2 = Task(ask, "Scan backend/api/", timeout=20)
    results = merge(result1, result2)
```

---

## Part 8: Anti-Patterns Summary

| Pattern | Bad | Good |
|---------|-----|------|
| **Speed** | Sequential tasks | Parallel independent |
| **Scope** | Vague ("analyze") | Precise ("scan services/, list classes") |
| **Overlap** | Multiple agents same file | Partition by pattern |
| **Deadline** | No limit | 30s target, partial OK |
| **Agents** | Wrong type for task | Match agent to task |
| **Format** | Free text | JSON structured |
| **Aggregation** | Manual merge | Programmatic combine |

---

## Checklist: CEO Workflow

**Before launching tasks:**
- [ ] Decomposed into ≥3 independent tasks?
- [ ] Each task has clear scope (what exactly)?
- [ ] Chose right agent type for each?
- [ ] Created ultra-precise prompt?
- [ ] Set reasonable deadline (20-60s)?
- [ ] "PARTIAL OK" in prompt?
- [ ] Planned aggregation strategy?

**After tasks complete:**
- [ ] All successful? If not, handle timeouts
- [ ] Aggregated results correctly?
- [ ] Identified next phase?
- [ ] Synthesized for user?

**Post-workflow:**
- [ ] Stored learnings in memory?
- [ ] Updated agent prompts if needed?
- [ ] Checked token usage (token budget)?

---

## Quick Reference: When to Use CEO Mindset

### Definitely Use CEO:
- Complex audit (50+ files)
- Multi-phase implementation
- Research-heavy feature
- Infrastructure health check
- Parallel data processing

### Maybe Use CEO:
- Single bug fix (if simple → solo, if complex → CEO)
- Small feature (if <30min effort → solo, if >2h → CEO)
- Documentation update (usually solo, unless huge)

### Never Use CEO:
- Simple, single-file changes
- Real-time debugging (interactive)
- Code review (one-on-one task)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System - Management Patterns
**Maintenance:** Review quarterly for new patterns
