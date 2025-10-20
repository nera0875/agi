# Task Decomposition - Checklists & Validation

## CHECKLIST 1: Before Decomposing Any Task

**Analysis Phase:**
- [ ] Does this task take >30 seconds solo?
- [ ] Can it split into ≥3 independent parts?
- [ ] Are parts truly independent (no cross-dependencies)?
- [ ] Can different agent types handle parts?
- [ ] Is decomposition overhead < speedup gained?

**If all YES** → Proceed to decomposition
**If any NO** → Run solo (1 agent only)

---

## CHECKLIST 2: Planning Decomposition

**Task Breakdown:**
- [ ] Listed all micro-tasks explicitly (write them down)?
- [ ] Each task has non-overlapping scope?
- [ ] Load balanced across agents (~30s each)?
- [ ] Chose right agent type for each task?
- [ ] Scope isolation is clear (no fuzzy boundaries)?

**Partition Strategy:**
- [ ] Using alphabetic partition (for files)?
  - [ ] [a-d], [e-h], [i-l], [m-p], [q-z]?
- [ ] Using semantic partition (by component)?
  - [ ] services/, api/, routes/, agents/, models/?
- [ ] Using system partition (by infrastructure)?
  - [ ] PostgreSQL, Redis, Neo4j, API costs, Logs?

**Estimation:**
- [ ] Estimated work per agent (target ~30s)?
- [ ] Calculated number of agents needed?
- [ ] Estimated total execution time?

---

## CHECKLIST 3: Prompt Writing (MOST CRITICAL)

**Structure:**
- [ ] [1] Context: 1-2 sentences explaining purpose?
- [ ] [2] SCOPE: Exact files/data to process?
- [ ] [3] TASK: 3 specific numbered actions?
- [ ] [4] CONSTRAINTS: Max items, ignore patterns?
- [ ] [5] DEADLINE: X seconds MAX (MANDATORY)?
- [ ] [6] PARTIAL OK: Clause included?
- [ ] [7] FORMAT: JSON specification shown?
- [ ] [8] EXAMPLE: Expected output format shown?

**Content Quality:**
- [ ] Scope is ultra-precise (not vague)?
- [ ] File patterns are exact (tested with Glob)?
- [ ] Task steps are sequential numbered?
- [ ] Deadline is firm number (not "soon")?
- [ ] "PARTIAL OK" explains what partial means?
- [ ] JSON format has all required fields?
- [ ] Example output is realistic?

**Anti-Patterns to Avoid:**
- [ ] No vague phrases: "thoroughly", "comprehensively"?
- [ ] No perfectionism language: "find everything"?
- [ ] No missing deadline?
- [ ] No missing JSON format specification?
- [ ] No missing "PARTIAL OK" clause?

---

## CHECKLIST 4: Execution Setup

**Parallelization:**
- [ ] All independent tasks launched together?
- [ ] Not waiting between task launches?
- [ ] Task count chosen correctly?
  - [ ] Read-only: 3-10 agents?
  - [ ] Data processing: 3-5 agents?
  - [ ] Implementation: 2-3 agents?
  - [ ] Architecture: 1 agent?

**Timeout & Partial:**
- [ ] Deadlines set on each task?
- [ ] Understanding how to handle partial results?
- [ ] 70% threshold configured for success?
- [ ] Retry strategy planned if <70% succeed?

**Aggregation Strategy:**
- [ ] Planned how to combine N results?
- [ ] Identified success metric (70% of agents)?
- [ ] Prepared JSON parsing for results?
- [ ] Planned deduplication if needed?

---

## CHECKLIST 5: After Execution

**Results Validation:**
- [ ] Checked all agent responses received?
- [ ] Filtered invalid results (< 70%)?
- [ ] Combined data structures correctly?
- [ ] Handled partial results gracefully?
- [ ] Verified no data loss from timeouts?

**Aggregation:**
- [ ] Calculated success rate?
- [ ] Confirmed >= 70% succeeded?
- [ ] If <70%: Planned retry with smaller scope?
- [ ] Combined all items into single structure?
- [ ] Deduplication done (if needed)?

**Synthesis:**
- [ ] Extracted key findings from aggregated data?
- [ ] Wrote clear summary for user?
- [ ] Highlighted issues/warnings?
- [ ] Connected findings to original request?

---

## DEADLINE CHECKLIST (MANDATORY)

**Every task MUST include DEADLINE:**

- [ ] `DEADLINE: X seconds MAX` in prompt?
- [ ] X is reasonable for task type?
  - [ ] Scan 1-5 files: 10s?
  - [ ] Scan 10-20 files: 20s?
  - [ ] Grep/analysis: 15s?
  - [ ] Code 1 function: 30s?
  - [ ] Code 1 API: 60s?
  - [ ] Architecture: 30-60s?
- [ ] `PARTIAL OK:` clause included?
- [ ] Understood 70% is enough?
- [ ] Not asking for perfectionism?

---

## COMMON MISTAKES (Learn From Them)

### Mistake 1: Overlapping Scopes

```python
# ❌ WRONG
Task(ask, "Scan backend/services/")
Task(ask, "Scan backend/services/")

# ✅ CORRECT
Task(ask, "Scan backend/services/[a-m]*.py")
Task(ask, "Scan backend/services/[n-z]*.py")
```

**Check:** Each agent has unique partition?

---

### Mistake 2: Dependent Tasks Parallelized

```python
# ❌ WRONG (parallelized dependent tasks)
Task(code, "Design database schema")
Task(code, "Write queries based on schema")

# ✅ CORRECT (sequential dependent)
result_schema = Task(code, "Design schema")
result_queries = Task(code, f"Write queries: {result_schema}")
```

**Check:** Each task independent from others?

---

### Mistake 3: No Deadline

```python
# ❌ WRONG
Task(ask, "Scan backend/")
→ Agent takes 5 minutes

# ✅ CORRECT
Task(ask, """
Scan backend/

DEADLINE: 20 seconds MAX
""")
→ Agent finishes in 20 seconds
```

**Check:** DEADLINE field present + firm number?

---

### Mistake 4: Vague Scope

```python
# ❌ WRONG
Task(ask, "Analyze code")
→ Agent scans everything (1 hour?)

# ✅ CORRECT
Task(ask, """
Scan backend/services/memory*.py

SCOPE:
- Max 10 files
- Ignore test_*

DEADLINE: 20s
""")
→ Agent focuses (20 seconds)
```

**Check:** Scope is precise + bounded?

---

### Mistake 5: Perfectionism Language

```python
# ❌ WRONG
"Find all issues comprehensively"
→ Agent overthinks (5 minutes)

# ✅ CORRECT
"""
Find top issues

PARTIAL OK: Return top 5 issues found, stop if timeout
"""
→ Agent focuses on top items (30 seconds)
```

**Check:** Accept partial results?

---

## QUICK VALIDATION SCRIPT

Run this mentally before launching agents:

```python
def validate_decomposition(tasks):
    # 1. Independence check
    for task in tasks:
        for other_task in tasks:
            if task != other_task:
                if depends_on(task, other_task):
                    return "ERROR: Tasks are dependent"

    # 2. Scope overlap check
    scopes = [t['scope'] for t in tasks]
    if has_overlap(scopes):
        return "ERROR: Overlapping scopes"

    # 3. Deadline check
    for task in tasks:
        if 'DEADLINE' not in task['prompt']:
            return "ERROR: No deadline in task"

    # 4. Load balance check
    workloads = [estimate_work(t['scope']) for t in tasks]
    if max(workloads) > 2 * min(workloads):
        return "WARNING: Unbalanced load"

    # 5. Partial results check
    for task in tasks:
        if 'PARTIAL OK' not in task['prompt']:
            return "ERROR: No partial OK clause"

    # 6. Format check
    for task in tasks:
        if 'FORMAT' not in task['prompt']:
            return "ERROR: No JSON format specified"

    return "VALID - Ready to launch"
```

---

## TIMELINE EXPECTATIONS

### Typical Execution Timeline

```
Understand problem (10s)
├─ What exactly is being asked?
├─ What are sub-tasks?
└─ Can it be parallelized?

Plan decomposition (5s)
├─ Identify micro-tasks
├─ Design partitions
└─ Choose agent types

Write prompts (10-15s)
├─ Template + context
├─ Scope + task
├─ Deadline + format
└─ Review for anti-patterns

Launch agents (1s)
├─ All tasks submitted together
└─ No waiting between launches

Wait for results (20-60s)
├─ Execution happens in parallel
└─ Typically completes in deadline time

Aggregate results (10-15s)
├─ Parse JSON responses
├─ Combine data structures
└─ Calculate success rate

Synthesize for user (5-10s)
├─ Extract key findings
├─ Write clear summary
└─ Highlight issues

TOTAL: 90s (instead of 3-5 hours solo)
```

---

## SUCCESS INDICATORS

**You did it right if:**

- ✅ All agents complete around same time (balanced load)
- ✅ Success rate > 70%
- ✅ Results can be easily combined (proper JSON)
- ✅ Total execution < 2 minutes
- ✅ User gets clear findings in synthesized report
- ✅ No regrets about task decomposition

**Something went wrong if:**

- ❌ One agent much slower than others (load imbalance)
- ❌ Many agents timeout (scope too big or deadline too short)
- ❌ Results are inconsistent/conflicting (overlapping scopes)
- ❌ Total execution > 5 minutes (should be 1-2 min)
- ❌ Hard to combine results (wrong format)
- ❌ Wondering if should have done it solo

---

## TEMPLATE CHEATSHEET

### Task Decomposition Template (Copy-Paste Ready)

```python
# Step 1: Understand
print("Analyzing: [USER REQUEST]")
print("Expected: [WHAT SUCCESS LOOKS LIKE]")

# Step 2: Decompose
tasks = [
    "Task 1: [description]",
    "Task 2: [description]",
    "Task 3: [description]",
    "..."
]
print(f"Decomposed into {len(tasks)} micro-tasks")

# Step 3: Launch (all at once, not sequential)
for task_desc in tasks:
    Task(agent_type, f"""
{task_desc}

SCOPE:
- [EXACTLY WHAT TO PROCESS]
- Max [N] items
- Ignore [PATTERNS]

TASK:
1. [Action 1]
2. [Action 2]
3. [Action 3]

DEADLINE: [X] seconds MAX
PARTIAL OK: Return what you have

FORMAT: Return JSON:
{{
  "status": "complete|partial",
  "completed_pct": 100,
  ...
}}
""")

# Step 4: Aggregate (after all complete)
results = [r1, r2, r3, ...]
valid = [r for r in results if r.get('completed_pct', 100) >= 70]

if len(valid) >= len(results) * 0.7:  # 70% success
    aggregated = combine(valid)
    print(f"SUCCESS: {len(valid)}/{len(results)} agents completed")
    return synthesize_for_user(aggregated)
else:
    print(f"FAILED: Only {len(valid)}/{len(results)} completed")
    return retry_with_smaller_scope()
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Use:** Before decomposing any task
**Key:** Follow checklists = success guaranteed
