# Task Decomposition - Detailed Technical Instructions

## Executive Summary

Transform a big slow task (1 agent × 5 min) into many fast tasks (N agents × 30s each). Core formula:

**Decompose → Partition → Parallelize → Aggregate = 10-20x speedup**

---

## Part 1: Understanding When to Decompose

### The Decomposition Decision

**Ask yourself:**
1. Will this task take >30 seconds solo?
2. Can it be split into ≥3 independent parts?
3. Do those parts have no cross-dependencies?
4. Can different agents handle different parts?

**If ALL YES** → Decompose and parallelize

**If ANY NO** → Run sequentially or solo

### Cost-Benefit Analysis

**When decomposition is WORTH IT:**
```python
# 50+ files to scan
# 1 agent solo: 5 min
# 5 agents parallel: 1 min
# Speedup: 5x

# Cost of decomposition: 2 min setup
# Value: Save 4 min execution = 2x time saved (break-even)

# Profit: Net 2 min saved, run 2x faster

if files > 30:
    decompose = True
else:
    decompose = False
```

**When decomposition is NOT WORTH IT:**
```python
# 5 files to scan
# 1 agent solo: 1 min
# 5 agents parallel: 1 min (overhead cancels speedup)
# Speedup: 1x (no gain)

# Not worth the complexity

if files < 10:
    decompose = False
else:
    decompose = True
```

---

## Part 2: Decomposition Rules (STRICT)

### Rule 1: Independence is Absolute

**NEVER decompose dependent tasks.**

```python
# ❌ WRONG (dependent)
Task 1: "Design system architecture"
Task 2: "Implement based on design"
→ Task 2 needs Task 1 output
→ SEQUENTIAL ONLY

# ✅ CORRECT (independent)
Task 1: "Scan backend/services/"
Task 2: "Scan backend/api/"
→ No cross-dependencies
→ PARALLEL OK
```

**Test for independence:**
- Does Agent 1's output feed into Agent 2?
- If YES → Dependent, sequential
- If NO → Independent, parallel

### Rule 2: Scope = No Overlap

Each agent gets exclusive scope. Never double-cover same area.

```python
# ❌ WRONG (overlap)
Agent 1: "Scan backend/"
Agent 2: "Scan backend/"
→ Both scan same files = wasted work

# ✅ CORRECT (partition)
Agent 1: "Scan backend/services/"
Agent 2: "Scan backend/api/"
Agent 3: "Scan backend/routes/"
→ Each covers unique area
→ Total coverage = complete, no overlap
```

**Partition strategies:**

**Strategy A: Alphabetic (for files)**
```python
patterns = [
    "services/[a-d]*.py",   # Agent 1
    "services/[e-h]*.py",   # Agent 2
    "services/[i-l]*.py",   # Agent 3
    "services/[m-p]*.py",   # Agent 4
    "services/[q-z]*.py",   # Agent 5
]
# Covers all, no overlap
```

**Strategy B: Semantic (by component)**
```python
scopes = [
    "backend/services/",    # Agent 1 (business logic)
    "backend/api/",         # Agent 2 (endpoints)
    "backend/routes/",      # Agent 3 (routes)
    "backend/models/",      # Agent 4 (data)
    "frontend/",            # Agent 5 (UI)
]
# Each agent gets logical component
```

**Strategy C: System (for infrastructure)**
```python
checks = [
    "PostgreSQL health",    # Agent 1 (DB)
    "Redis health",         # Agent 2 (cache)
    "Neo4j health",         # Agent 3 (graph)
    "API costs",            # Agent 4 (billing)
    "Log analysis",         # Agent 5 (monitoring)
]
# Each agent checks one system
```

### Rule 3: Load Balancing

Each agent should get roughly same amount of work (~30s).

```python
# Bad load distribution
Agent 1: Scan 50 files (2 min)     ❌ Overloaded
Agent 2: Scan 5 files (30s)        ✅ Balanced
Agent 3: Scan 5 files (30s)        ✅ Balanced

# Unbalanced: Agent 1 is bottleneck

# Good load distribution
Agent 1: Scan 20 files (40s)       ✅ ~30-40s
Agent 2: Scan 20 files (40s)       ✅ ~30-40s
Agent 3: Scan 15 files (30s)       ✅ ~30-40s

# Balanced: All finish in ~40s total
```

**Heuristic for parallelization:**
```python
# Based on work type:
read_only_scans = 5-10 agents       # Fast, no coordination
data_processing = 3-5 agents        # Medium complexity
feature_implementation = 2-3 agents # Slow, needs merge
architecture_design = 1 agent       # Sequential, complex
```

---

## Part 3: Prompt Engineering for Decomposition

### The 6-Part Prompt Template

```markdown
[PART 1: CONTEXT]
Why is this task being done? What's the big picture?

[PART 2: SCOPE]
What exactly is this agent responsible for?

[PART 3: TASK]
What specific actions must be performed?

[PART 4: CONSTRAINTS]
What are the limits/exclusions?

[PART 5: DEADLINE & QUALITY]
How long? How complete?

[PART 6: FORMAT]
What exactly should output look like?
```

### Example: Precise Prompt

```python
"""
CONTEXT:
Auditing backend code structure as part of health check.

SCOPE:
Only scan: backend/services/memory*.py
Exactly these files matching pattern, nothing else.

TASK:
1. List all Python classes defined in these files
2. For each class, extract:
   - Class name
   - Number of public methods
   - List of public method names
3. Ignore:
   - Private methods (start with _)
   - Dunder methods (__init__, __str__, etc.)
   - Static methods
   - Class methods

CONSTRAINTS:
- Max 10 files (if more, take first 10 alphabetically)
- Skip files > 500 lines
- Ignore test files

DEADLINE: 20 seconds MAX
- If 15s in and scanned 5/10 files: STOP and return partial
- "PARTIAL OK" - we'd rather have 70% in 20s than 100% in 5min

FORMAT: Return JSON exactly:
{
  "status": "complete|partial|timeout",
  "completed_pct": 100,
  "files_scanned": ["file1.py", "file2.py", ...],
  "total_classes": 3,
  "classes": [
    {
      "file": "memory_service.py",
      "name": "MemoryService",
      "public_methods": 7,
      "methods": ["get_memory", "store_memory", ...]
    },
    ...
  ],
  "errors": []
}
"""
```

**Why this works:**
- Agent knows EXACTLY what to do ✅
- No ambiguity about scope ✅
- Clear deadline with partial OK ✅
- JSON format for easy parsing ✅
- Takes 20s predictably ✅

### Prompt Anti-Patterns

```python
# ❌ BAD 1: Vague scope
"Analyze the backend"
→ Agent doesn't know where to start

# ✅ GOOD 1: Precise scope
"Scan backend/services/memory*.py"

# ❌ BAD 2: No deadline
"Do a thorough analysis"
→ Takes 5 min (agent perfectionism)

# ✅ GOOD 2: Hard deadline
"DEADLINE: 20s MAX"

# ❌ BAD 3: No format
"Tell me what you found"
→ Free text = hard to parse

# ✅ GOOD 3: JSON format
"Return JSON: {status: 'complete|partial', files: [...]}"

# ❌ BAD 4: Perfectionism
"Find everything, leave nothing out"
→ Agent overthinks

# ✅ GOOD 4: Pragmatism
"Get the top 80%, if timeout return what you have"
```

## Part 3b: Scope ULTRA-PRÉCIS (Anti-Dérive)

### The Problem: Scope Creep

When prompt is vague, agent expands task beyond limits:

```python
# ❌ VAGUE SCOPE (agent spirals)
Task(ask, "Analyze backend")
→ Agent scans: services/
→ Agent scans: api/
→ Agent scans: routes/
→ Agent scans: agents/
→ Agent scans: models/
→ Agent scans: tests/
→ 10 minutes later: "I'm not done"

# ✅ PRECISE SCOPE (agent focused)
Task(ask, """
Scan backend/services/memory*.py

SCOPE:
- Pattern: backend/services/memory*.py
- Max 10 files
- Stop at 10 files (ignore rest)
- Ignore: __pycache__, *.pyc, test_*

TASK: Extract classes + methods
DEADLINE: 20s MAX
""")
→ Agent scans exactly 10 files
→ Extracts exactly what asked
→ Returns in 20 seconds
```

### Strategies for Ultra-Precise Scopes

**Strategy 1: File Pattern (Alphabetic Partition)**
```python
# Bad: Too big
"Scan backend/"
→ Hundreds of files, agent overwhelmed

# Good: Partitioned
patterns = [
    "backend/[a-d]*",   # Agent 1
    "backend/[e-h]*",   # Agent 2
    "backend/[i-l]*",   # Agent 3
    "backend/[m-p]*",   # Agent 4
    "backend/[q-z]*",   # Agent 5
]
→ Each agent: ~20 files, 20s
```

**Strategy 2: Component Partition (Semantic)**
```python
# Bad: All at once
"Audit backend"

# Good: By component
Task(ask, "Scan backend/services/*.py")      # Agent 1
Task(ask, "Scan backend/api/*.py")           # Agent 2
Task(ask, "Scan backend/routes/*.py")        # Agent 3
Task(ask, "Scan backend/agents/*.py")        # Agent 4
Task(ask, "Find backend/**/*_wrapper.py")    # Agent 5
→ Each agent: clear, focused component
```

**Strategy 3: Max Items (Sample if Too Big)**
```python
# Bad: Unbounded
"Scan all services/"
→ 100 files, 5 minute task

# Good: Sample first N
"""
Scan backend/services/

SCOPE:
- Pattern: *.py
- Max 20 files: take first 20 (stop at 20)
- If more than 20 exist, sample strategy: alphabetical

DEADLINE: 20s MAX
"""
→ Exactly 20 files, 20 seconds
```

### Example: Dividing Gros Travaux

**Scenario: Audit entire backend (67 files)**

```python
# ❌ WRONG (1 agent, vague)
Task(ask, "Audit backend/services/")
→ Agent tries to scan 67 files
→ 5+ minutes
→ Bottleneck

# ✅ RIGHT (5 agents, partitioned)
# Estimate: 67 files / 5 agents = ~13-14 files each
# Each agent: ~20 seconds

patterns = [
    "[a-d]",    # aaa_service.py, authentication.py, ...
    "[e-h]",    # embedding.py, event_handler.py, ...
    "[i-l]",    # index_service.py, ...
    "[m-p]",    # memory_service.py, mcp_service.py, ...
    "[q-z]",    # query_handler.py, retrieval.py, voyage_service.py, ...
]

for prefix in patterns:
    Task(ask, f"""
    Backend audit: {prefix} files

    SCOPE:
    - Pattern: backend/services/{prefix}*.py
    - Max 20 files per agent
    - Ignore: __pycache__, *.pyc, test_*

    TASK:
    1. List all classes (extract class names)
    2. For each class, count public methods
    3. Flag if >3 wrapper classes (code smell)
    4. Flag if file >500 lines (too large)

    DEADLINE: 20 seconds MAX
    PARTIAL OK: Return files scanned so far

    FORMAT JSON:
    {{
      "status": "complete|partial",
      "prefix": "{prefix}",
      "files_scanned": [...],
      "classes": [...],
      "issues": [...],
      "completed_pct": 100
    }}
    """)

# Result: 5 agents scan in PARALLEL
# - Agent 1: 15 files in 20s
# - Agent 2: 14 files in 20s
# - Agent 3: 13 files in 20s
# - Agent 4: 13 files in 20s
# - Agent 5: 12 files in 20s
# Total: 67 files in 20 seconds (not 5 minutes)

# Aggregation:
{
    "total_files": 67,
    "total_classes": 45,
    "avg_methods_per_class": 3.2,
    "issues": [
        "memory_service.py: 520 lines (too large)",
        "wrapper_*.py: 3 wrapper classes (code smell)"
    ]
}
```

### Quality Checklist: Scope Precision

Before launching agents, verify:

- [ ] Scope is specific (not vague: "backend" vs "backend/services/[a-d]*.py")?
- [ ] Max items set (not unbounded: "max 20 files")?
- [ ] Partitions don't overlap (each agent: unique scope)?
- [ ] Load balanced (each agent: ~30s of work)?
- [ ] Files are truly independent (can process in parallel)?
- [ ] Clear exclusions stated ("ignore __pycache__")?
- [ ] Pattern matches exactly what we want (test glob first)?

---

## Part 4: Timeout & Partial Results (STRICT DEADLINES)

### Setting Appropriate Deadlines (MANDATORY)

**CRITICAL RULE:** Every agent task MUST have `DEADLINE: X seconds MAX` in prompt.

**Duration by task type (from production):**

| Task Type | Deadline | Example | Note |
|-----------|----------|---------|------|
| **Scan 1-5 files** | 10s MAX | Extract classes from 1-5 .py | Fast |
| **Scan 10-20 files** | 20s MAX | Scan services/, list functions | Sample if more |
| **Scan 50+ files** | 5 × 20s | Partition a-e, f-j, k-o, p-t, u-z | Parallelize! |
| **Grep pattern** | 15s MAX | Find "class.*X" in backend/ | Ripgrep fast |
| **Health check 1 system** | 15s MAX | PostgreSQL: connections + queries | 1 DB check |
| **Architecture design** | 30-60s | Multi-phase system plan | Requires thinking |
| **Code 1 function** | 30s MAX | Backend endpoint or React hook | Focused |
| **Code 1 API/mutation** | 60s MAX | Full endpoint implementation | Medium |
| **Tests (single file)** | 20s MAX | pytest backend/tests/test_X.py | Quick |
| **Documentation section** | 30s MAX | Update README section | Focused |
| **Full feature (3+ parts)** | 2-3 min | Break into phases (backend + frontend + tests) | Parallelize |

**Formula for custom deadlines:**
```
Deadline = (Expected_Duration × 1.5) + 5s buffer (minimum 10s)
```

Example:
```python
# Task: Scan 20 files (normally 30s)
expected = 30
deadline = (30 * 1.5) + 5 = 50 seconds

# Set DEADLINE: 50 seconds MAX
# Agent feels pressure, finishes in 40s instead of 60s
```

**Real-world comparison:**
```python
# Without deadline (❌ SLOW)
Task(ask, "Scan backend/services/")
→ 5 minutes (agent perfectionism)

# With deadline (✅ FAST)
Task(ask, """
Scan backend/services/

DEADLINE: 20 seconds MAX
PARTIAL OK: Return what you've scanned
""")
→ 20 seconds (agent rushes)
→ Get 80% useful vs 100% in 5 min
```

### Handling Timeouts Gracefully

**Golden Rule:** Partial results > no results

```python
# Mark in prompt:
"""
DEADLINE: 30 seconds MAX
PARTIAL OK: If hit deadline, return what you've done so far.

Example partial result:
{
  "status": "partial",
  "completed_pct": 75,
  "files_scanned": 3,
  "files_total": 4,
  "result": [...]
}
"""
```

**In aggregation:**
```python
results = [
    {"status": "complete", "items": 10},    # Good
    {"status": "partial", "items": 7},      # OK (75%)
    {"timeout": True, "items": 2},          # Bad (20%)
]

# Filter: Keep complete + partial (>70%)
good_results = [r for r in results
               if r.get("completed_pct", 100) > 70]

# This gives us 80% of original scope in time
if len(good_results) / len(results) > 0.7:
    aggregate(good_results)  # Good enough
else:
    # Try smaller scope with new agents
    retry_with_smaller_scope()
```

### Retry Strategy

**Attempt 1: Big scope, short deadline**
```python
result = Task(ask, "Scan backend/services/", timeout=20)
```

**If timeout:**
```python
# Attempt 2: Smaller scope, same deadline
result1 = Task(ask, "Scan backend/services/[a-m]*.py", timeout=20)
result2 = Task(ask, "Scan backend/services/[n-z]*.py", timeout=20)
result = merge(result1, result2)

# Total time: 20s original + 20s retry = 40s
# vs attempting once forever
```

---

## Part 5: Decomposition Heuristics

### When to Parallelize (Decision Tree)

```
Is this task >30 seconds?
│
├─ NO → Run solo (1 agent, no decompose)
│
└─ YES → Can it split into ≥3 independent parts?
   │
   ├─ NO → Run solo (decompose not worth it)
   │
   └─ YES → Are parts truly independent (no cross-dependencies)?
      │
      ├─ NO → Run sequential (can't parallelize dependent tasks)
      │
      └─ YES → Can different agent types handle parts?
         │
         ├─ NO → Run solo (1 agent type anyway)
         │
         └─ YES → Launch N agents in parallel
                  (Expected 5-20x speedup)
```

### Task Size Heuristics

**For file scanning:**
```python
num_files = count_matching_files(pattern)

if num_files < 10:
    agents = 1      # Solo, not worth decomposing
elif num_files < 30:
    agents = 2-3    # Maybe parallelize
else:
    agents = 5-10   # Definitely parallelize

files_per_agent = num_files / agents
expected_time_per_agent = (files_per_agent / 5) * 10  # rough estimate
```

**For system checks:**
```python
num_systems = ["PostgreSQL", "Redis", "Neo4j", "API", "Logs"]

# Each independent → parallelize
agents = len(num_systems)
total_time = max(time_per_check)  # Not sum

# Example:
# 5 systems in parallel = ~1 min total
# vs 5 systems sequential = ~5 min total
```

**For feature implementation:**
```python
components = ["backend_api", "frontend_ui", "migrations", "tests"]

# Can they run independently?
# Yes → parallelize (2-3 min)
# No (frontend needs backend) → sequential (5 min)
```

### Load Balancing Calculation

```python
def calculate_optimal_parallelization(total_work,
                                       target_per_agent=30):
    """How many agents to launch?"""

    num_agents = ceil(total_work / target_per_agent)

    # Constrain between 1 and 10
    return min(max(num_agents, 1), 10)

# Example:
calculate_optimal_parallelization(120)  # 4 min solo
→ 120 / 30 = 4 agents needed
→ Each agent: 30s
→ Total time: 30s (vs 120s solo = 4x speedup)

calculate_optimal_parallelization(150)  # 2.5 min solo
→ 150 / 30 = 5 agents
→ Total time: 30s (vs 150s solo = 5x speedup)
```

---

## Part 6: Aggregation Patterns

### Generic Aggregation Function

```python
def aggregate_parallel_results(results,
                               success_threshold=0.7):
    """
    Combine multiple agents' results into single summary.

    Success if ≥70% of agents complete successfully.
    """

    # 1. Classify results
    successful = [r for r in results
                  if r.get("status") == "complete"]
    partial = [r for r in results
               if r.get("status") == "partial"
               and r.get("completed_pct", 0) > 70]
    failed = [r for r in results
              if r.get("status") in ["failed", "timeout"]]

    usable = successful + partial

    # 2. Check success rate
    success_rate = len(usable) / len(results)
    if success_rate < success_threshold:
        return {
            "status": "failed",
            "reason": f"Too many failures ({success_rate:.0%})",
            "usable_agents": len(usable),
            "total_agents": len(results)
        }

    # 3. Merge data (depends on structure)
    # For lists:
    all_items = []
    for r in usable:
        all_items.extend(r.get("items", []))

    # Deduplicate if needed
    unique_items = list(set(all_items))

    # For dicts:
    merged = {}
    for r in usable:
        for key, value in r.get("data", {}).items():
            if key not in merged:
                merged[key] = []
            merged[key].append(value)

    # 4. Summary
    return {
        "status": "complete" if success_rate == 1.0 else "partial",
        "success_rate": success_rate,
        "successful_agents": len(successful),
        "partial_agents": len(partial),
        "failed_agents": len(failed),
        "total_agents": len(results),
        "items": unique_items if isinstance(all_items, list) else merged,
        "count": len(unique_items) if isinstance(all_items, list) else None
    }
```

### Example Aggregation: File Scanning

**Agent results:**
```python
result1 = {
    "status": "complete",
    "files": ["memory_service.py", "graph_service.py"],
    "classes": 5
}

result2 = {
    "status": "complete",
    "files": ["voyage_service.py"],
    "classes": 3
}

result3 = {
    "status": "partial",
    "completed_pct": 80,
    "files": ["embedding_service.py"],
    "classes": 2
}
```

**Aggregation:**
```python
def aggregate_scanning_results(results):
    all_files = []
    total_classes = 0

    for r in results:
        if r.get("status") in ["complete", "partial"]:
            all_files.extend(r.get("files", []))
            total_classes += r.get("classes", 0)

    return {
        "status": "complete",
        "files_scanned": len(all_files),
        "total_classes": total_classes,
        "file_list": all_files,
        "avg_classes_per_file": total_classes / len(all_files)
    }

# Aggregation output:
{
    "status": "complete",
    "files_scanned": 4,
    "total_classes": 10,
    "file_list": ["memory_service.py", "graph_service.py", ...],
    "avg_classes_per_file": 2.5
}
```

### Example Aggregation: System Checks

**Agent results:**
```python
checks = {
    "postgres": {"status": "healthy", "latency": "5ms"},
    "redis": {"status": "healthy", "memory": "42%"},
    "neo4j": {"status": "degraded", "latency": "120ms"},
    "api_costs": {"status": "healthy", "spent": "$45.32"},
}
```

**Aggregation:**
```python
def aggregate_health_checks(results):
    failed = [name for name, check in results.items()
              if check["status"] != "healthy"]

    overall = "healthy" if not failed else \
              "degraded" if len(failed) < len(results) // 2 else \
              "critical"

    return {
        "overall_status": overall,
        "healthy_systems": len(results) - len(failed),
        "total_systems": len(results),
        "failed_systems": failed,
        "details": results
    }

# Aggregation output:
{
    "overall_status": "degraded",
    "healthy_systems": 3,
    "total_systems": 4,
    "failed_systems": ["neo4j"],
    "details": {...}
}
```

---

## Part 7: Common Decomposition Scenarios

### Scenario 1: Large Codebase Audit (100+ files)

**Problem:** Scan backend for structure issues

**Decomposition:**
```python
# Estimate: 100 files × 3s per file = 5 min solo

# Plan: 5 agents × 20 files each
patterns = [
    "backend/[a-c]*",
    "backend/[d-f]*",
    "backend/[g-i]*",
    "backend/[j-l]*",
    "backend/[m-z]*",
]

# Each agent: 1 min (20 files × 3s)
# Total: 1 min (not 5 min) = 5x speedup
```

### Scenario 2: Multi-Service Health Check

**Problem:** Check PostgreSQL, Redis, Neo4j, API costs

**Decomposition:**
```python
# Estimate: 4 checks × 60s = 4 min solo

# Plan: 4 agents in parallel (independent systems)
checks = [
    "PostgreSQL health",
    "Redis health",
    "Neo4j health",
    "API costs"
]

# Each agent: 60s
# Total: 60s (not 4 min) = 4x speedup
```

### Scenario 3: Complex Feature Implementation

**Problem:** Implement real-time notifications (backend + frontend + tests)

**Decomposition:**
```python
# Phase 1: Understanding (2 min)
# Scan existing notification code, subscription patterns

# Phase 2: Research (2 min)
# Research GraphQL Subscriptions best practices

# Phase 3: Architecture (1 min)
# Design system

# Phase 4: Implementation (parallel, 5 min)
Task(code, "Backend GraphQL subscription")          # ~1-2 min
Task(frontend, "Frontend useSubscription hook")     # ~1-2 min
Task(code, "Database migration")                    # ~30s

# Phase 5: Validation (parallel, 3 min)
Task(debug, "Backend tests")                        # ~1 min
Task(debug, "Frontend tests")                       # ~1 min
Task(debug, "E2E test")                             # ~1 min

# Phase 6: Documentation (1 min)
Task(docs, "Update README")                         # ~1 min

# Total: ~15 min
# vs Solo: ~2 days
```

---

## Part 8: Anti-Patterns & Pitfalls

### Pitfall 1: "Decomposing" Dependent Tasks

```python
# ❌ WRONG (looks parallel but is sequential)
Task(code, "Design data schema")
Task(code, "Implement queries based on schema")

# Design output needed for implementation
# These MUST run sequential despite looking parallel

# ✅ CORRECT
# Run both, but acknowledge dependency
# Phase 1: Design
result_design = Task(code, "Design data schema")

# Phase 2: Implement (takes Phase 1 output)
# Can't parallelize - inherent dependency
result_impl = Task(code, f"Implement queries based on: {result_design}")
```

### Pitfall 2: Overlapping Scopes

```python
# ❌ WRONG (both agents scan same files)
Task(ask, "Scan backend/services/")
Task(ask, "Scan backend/services/")

# Duplication, wasted work

# ✅ CORRECT (non-overlapping partitions)
Task(ask, "Scan backend/services/[a-m]*.py")
Task(ask, "Scan backend/services/[n-z]*.py")
```

### Pitfall 3: Ignoring Timeout

```python
# ❌ WRONG (no handling for timeout)
result = Task(ask, "Scan backend/")
# If timeout, we get nothing

# ✅ CORRECT (graceful degradation)
result = Task(ask, """
Scan backend/

DEADLINE: 30s
PARTIAL OK: If timeout, return partial
""")
# If timeout, we get 70% instead of nothing
```

### Pitfall 4: Imbalanced Load

```python
# ❌ WRONG (unbalanced)
Agent 1: "Scan 100 files" (5 min)     ← Bottleneck
Agent 2: "Scan 10 files" (30s)
Agent 3: "Scan 10 files" (30s)

# Total: 5 min (limited by slowest agent)
# No speedup!

# ✅ CORRECT (balanced)
Agent 1: "Scan 40 files" (2 min)
Agent 2: "Scan 40 files" (2 min)
Agent 3: "Scan 30 files" (1.5 min)

# Total: 2 min (max of balanced load)
# Much better speedup
```

### Pitfall 5: Vague Prompts

```python
# ❌ WRONG
"Analyze the code"
# Agent doesn't know what to do, takes long time

# ✅ CORRECT
"Scan backend/services/memory*.py
- Extract class names
- List public methods
- Ignore private/dunder
- Max 10 files
- DEADLINE: 20s
- Return JSON: {files, classes}"
# Agent knows exactly, fast
```

---

## Part 9: Decomposition Checklist

**Before Decomposing:**
- [ ] Task will take >30s solo?
- [ ] Can split into ≥3 independent parts?
- [ ] Parts are truly independent (no cross-deps)?
- [ ] Different agents can work on parts?
- [ ] Decomposition time < speedup gained?

**Planning Phase:**
- [ ] Identified all micro-tasks (list them)?
- [ ] Each has non-overlapping scope?
- [ ] Load balanced across agents (~30s each)?
- [ ] Chose right agent type for each?
- [ ] Scope isolation clearly defined?

**Prompt Writing:**
- [ ] Ultra-precise (not vague)?
- [ ] Clear file/data scope?
- [ ] Specific actions (1, 2, 3)?
- [ ] Deadline set (20-60s)?
- [ ] "PARTIAL OK" included?
- [ ] JSON format specified?
- [ ] Example output shown?

**Execution:**
- [ ] Launch all tasks together (not sequential)?
- [ ] Set timeouts on each task?
- [ ] Plan aggregation strategy?
- [ ] Identified success threshold (70%)?

**Aggregation:**
- [ ] Filtered invalid results?
- [ ] Combined data correctly?
- [ ] Handled partial results?
- [ ] Checked success rate?
- [ ] Retried failures with smaller scope?
- [ ] Synthesized for user?

---

## Part 10: DEADLINE DISCIPLINE - Real World Examples (From CLAUDE.md)

### Critical: Time Pressure = Efficiency

Agents without deadlines take **5-10x longer** than agents with pressure.

**Why? Agent perfectionism:**
```
Without deadline:
- Agent: "I should be thorough"
- Agent: "Let me check one more thing"
- Agent: "Maybe look at edge cases"
- Result: 5 minutes later, not done

With deadline:
- Agent: "I have 30 seconds"
- Agent: "Scan TOP priority files"
- Agent: "Return what I have"
- Result: 30 seconds, 80% useful
```

### The 70% Rule (CEO Pragmatism)

**Golden Rule:** 70% useful in 30s > 100% useful in 5 min

```python
# Compare two approaches:

# Approach 1: Perfectionist
Agent scans everything → 5 min
Result: 100% complete
Wait time: 5 min

# Approach 2: Pragmatist CEO
Agent has 30s deadline → 30 sec
Result: 70% complete (enough to act)
Wait time: 30 sec

# Cost-benefit:
Saved: 4.5 min waiting
Value: 70% of information
Decision: WORTH IT
```

### Concrete Example: Audit Project (10 agents, PARALLEL)

**Scenario: "Check if backend health is OK"**

#### ❌ OLD WAY (Sequential, No Deadlines)

```python
# 1 agent does everything
Task(ask, "Audit backend completely")
→ Agent scans services/: 2 min
→ Agent scans api/: 1 min
→ Agent scans routes/: 1 min
→ Agent scans agents/: 1 min
→ Agent writes report: 1 min

Total: 6 minutes
```

#### ✅ NEW WAY (Parallel, DEADLINE-DRIVEN)

```python
# 10 agents, each with STRICT deadline

# Phase 1: Scanning (parallel, 5 agents × 20s)
Task(ask, """
Backend services audit: A-E

SCOPE:
- Pattern: backend/services/[a-e]*.py
- Max 15 files
- Ignore: __pycache__, test_*

TASK: Extract classes + method count

DEADLINE: 20 seconds MAX
PARTIAL OK: Return scanned files

FORMAT: {status, files_scanned, classes, completed_pct}
""")
# Same for [f-j], [k-o], [p-t], [u-z]

# Phase 2: API audit (parallel, 2 agents × 15s)
Task(ask, "Scan backend/api/graphql/, list schema roots")  # 15s
Task(ask, "Scan backend/routes/, list endpoints")           # 15s

# Phase 3: Config scan (1 agent × 10s)
Task(ask, "Check backend/core/ config, list settings")      # 10s

# Phase 4: Aggregation (1 agent × 5s)
→ Combine 8 agent results into single report              # 5s

Total: 20 seconds (not 6 minutes!)
Speedup: 18x faster

Result: Same audit quality
         18x faster execution
```

### Why DEADLINE is Mandatory

**In prompt, ALWAYS include:**

```python
DEADLINE: [X] seconds MAX
```

**Examples:**

```python
# ✅ CORRECT (has deadline)
Task(ask, """
Scan backend/

DEADLINE: 30 seconds MAX
PARTIAL OK: Return what you scanned
""")

# ❌ WRONG (no deadline)
Task(ask, "Scan backend/")
→ Agent takes own time (slow)

# ❌ WRONG (vague deadline)
Task(ask, "Scan backend/", "Try to finish soon")
→ "Soon" is not precise

# ✅ BEST (precise deadline)
Task(ask, """
Scan backend/

DEADLINE: 20 seconds MAX, PERIOD
""")
```

### Anti-Patterns (CEO Lessons)

| Pattern | Agent Behavior | Result | Fix |
|---------|---|---|---|
| **No deadline** | "Let me be thorough" | 5 min slow | `DEADLINE: 30s MAX` |
| **Vague deadline** | "Try your best" | 3-4 min (still slow) | `DEADLINE: X seconds MAX, PERIOD` |
| **Perfectionism language** | "Find everything" | Overthinks, 5 min | Use `PARTIAL OK: Return top 80%` |
| **Single agent big task** | "Analyze whole backend" | 10 min bottleneck | Parallelize: 5 agents × 2 min |
| **No partial results** | "All or nothing" | Fails if timeout | `completed_pct: 70% OK` |

### The CEO Mindset Summary

**Remember: You're a CEO managing 50 agents, not a solo worker.**

**Entrepreneur principles:**
1. **Parallelize ruthlessly** - If can split → split
2. **Set deadlines** - Pressure = speed
3. **Accept partial** - 70% in 30s > 100% in 5 min
4. **Aggregate quickly** - Your job is orchestration, not execution
5. **Delegate mastery** - Make agents faster, not you

**Formula for success:**
```
Understand problem (10s)
  ↓
Break into micro-tasks (5s)
  ↓
Launch N agents in parallel (1s)
  ↓
Set STRICT deadlines (mandatory)
  ↓
Wait for results (20-60s)
  ↓
Aggregate + synthesize (10s)
  ↓
DONE (90s total vs 2-3 hours solo)
```

---

**Version:** 2.0.0 (Updated with DEADLINE DISCIPLINE)
**Last Updated:** 2025-10-20
**Category:** System - Orchestration (Technical + Production)
**Maintenance:** Review when agent behavior changes
**Key Skill:** DEADLINE discipline - core to CEO mindset
