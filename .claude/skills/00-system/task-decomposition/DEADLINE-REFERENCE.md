# DEADLINE REFERENCE - Quick Copy-Paste (2min MAX to complete)

## CRITICAL RULE

**EVERY task to agents MUST include `DEADLINE: X seconds MAX`**

Without it: Agent takes 5-10x longer (perfectionism)
With it: Agent finishes in time (pressure = speed)

---

## Timeout by Task Type (PRODUCTION TESTED)

Copy-paste appropriate deadline for your task:

### QUICK SCAN TASKS (10-20s)

```python
# Scan 1-5 files - Extract classes/methods
DEADLINE: 10 seconds MAX
PARTIAL OK: Return scanned files

# Scan 10-20 files - List functions
DEADLINE: 20 seconds MAX
PARTIAL OK: Return files processed so far

# Scan 50+ files - USE 5 AGENTS × 20s
Task(ask, "Scan backend/services/[a-e]*.py")  # 20s
Task(ask, "Scan backend/services/[f-j]*.py")  # 20s
Task(ask, "Scan backend/services/[k-o]*.py")  # 20s
Task(ask, "Scan backend/services/[p-t]*.py")  # 20s
Task(ask, "Scan backend/services/[u-z]*.py")  # 20s

# Grep pattern - Find "class.*X" in backend/
DEADLINE: 15 seconds MAX
PARTIAL OK: Return matches found so far
```

### ANALYSIS TASKS (15-30s)

```python
# Health check 1 system (PostgreSQL/Redis/Neo4j)
DEADLINE: 15 seconds MAX
PARTIAL OK: Return checks completed

# Parse logs - Find errors/warnings
DEADLINE: 20 seconds MAX
PARTIAL OK: Return patterns found

# Architecture design - Plan multi-phase system
DEADLINE: 30 seconds MAX
PARTIAL OK: Return high-level phases

# Documentation section - Update README part
DEADLINE: 30 seconds MAX
PARTIAL OK: Return draft content
```

### CODE TASKS (30-60s)

```python
# Code 1 function/hook - Backend endpoint or React hook
DEADLINE: 30 seconds MAX
PARTIAL OK: Return scaffold/outline

# Code 1 API/mutation - Full endpoint implementation
DEADLINE: 60 seconds MAX
PARTIAL OK: Return working version

# Database migration - Create + schema
DEADLINE: 30 seconds MAX
PARTIAL OK: Return migration file

# Run tests (single file) - pytest backend/tests/test_X.py
DEADLINE: 20 seconds MAX
PARTIAL OK: Return test results so far
```

### COMPLEX TASKS (Break into phases!)

```python
# Full feature (backend + frontend + tests)
# DON'T: 1 agent × 3 min
# DO: Break into phases

# Phase 1: Backend (60s)
Task(code, "GraphQL subscription...")  # 60s

# Phase 2: Frontend (60s, parallel to Phase 1)
Task(frontend, "useSubscription hook...")  # 60s

# Phase 3: Tests (both parallel, 30s each)
Task(debug, "Backend tests...")  # 30s
Task(debug, "Frontend tests...")  # 30s

# Total: 60s (not 3-5 min)
```

---

## MANDATORY PROMPT TEMPLATE

**Use this for EVERY agent task:**

```python
Task(agent_type, """
[Context: 1-2 sentences what this is part of]

SCOPE:
- Files/data: [EXACTLY what to process]
- Max items: [If >N items, stop at N]
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

---

## The 70% Rule (ACCEPT PARTIAL)

- **100% complete in 5 min** ❌ Too slow
- **70% complete in 30s** ✅ Fast enough
- **70% < threshold** ❌ Retry with smaller scope

```python
results = [r for r in agent_results
          if r.get("completed_pct", 100) >= 70]

if len(results) >= len(all_results) * 0.7:  # 70% success
    aggregate(results)  # GO
else:
    retry_with_smaller_scope()  # Retry
```

---

## ANTI-PATTERNS (AVOID THESE)

| Pattern | Result | Fix |
|---------|--------|-----|
| No deadline | 5-10 min slow | Add `DEADLINE: X seconds MAX` |
| Vague scope | Agent confused | Be precise: "backend/services/[a-e]*.py" |
| "Find everything" | Perfectionism, 5 min | Use `PARTIAL OK: Return top 80%` |
| 1 agent × big task | Bottleneck | Split: 5 agents × smaller scopes |
| All-or-nothing | Fails on timeout | Accept 70%+ complete |

---

## CEO SUCCESS FORMULA

```
Understand (10s)
  ↓
Decompose (5s)
  ↓
Launch N agents PARALLEL (1s)
  ↓
DEADLINES MANDATORY ← KEY
  ↓
Wait (20-60s)
  ↓
Aggregate (10s)
  ↓
DONE (90s total vs 2-3 hours solo)
```

---

## EXAMPLES (Copy-Paste Ready)

### Example 1: Scan 50 files fast

```python
# ❌ WRONG (slow)
Task(ask, "Scan backend/services/")

# ✅ RIGHT (fast)
for prefix in ['a-d', 'e-h', 'i-l', 'm-p', 'q-z']:
    Task(ask, f"""
    Scan backend/services/{prefix}*.py

    SCOPE:
    - Pattern: backend/services/{prefix}*.py
    - Max 15 files

    TASK: List classes + method count

    DEADLINE: 20 seconds MAX
    PARTIAL OK: Return files scanned

    FORMAT: {{"status": "...", "files": [...], "classes": [...]}}
    """)

# Result: 50 files scanned in 20 seconds (not 5 minutes)
```

### Example 2: Health check 4 systems

```python
# ❌ WRONG (sequential, 4 min)
Task(sre, "Check PostgreSQL")      # 1 min
→ Wait
Task(sre, "Check Redis")           # 1 min
→ Wait
Task(sre, "Check Neo4j")           # 1 min
→ Wait
Task(sre, "Check API costs")       # 1 min

# ✅ RIGHT (parallel, 1 min)
Task(sre, """
Check PostgreSQL

SCOPE: Connection status, slow queries, disk space

DEADLINE: 15 seconds MAX
PARTIAL OK: Return checks completed

FORMAT: {status: "healthy|degraded|critical", ...}
""")

Task(sre, "Check Redis...")  # 15s
Task(sre, "Check Neo4j...")  # 15s
Task(sre, "Check API costs...")  # 15s

# Result: All 4 in parallel = 15s (not 4 min)
```

### Example 3: Audit project (FULL EXAMPLE)

```python
# Problem: Audit backend (67 files)

# ❌ WRONG (1 agent, 5 min)
Task(ask, "Audit backend/services/ completely")

# ✅ RIGHT (5 agents parallel, 20s)

patterns = ['[a-d]', '[e-h]', '[i-l]', '[m-p]', '[q-z]']

for prefix in patterns:
    Task(ask, f"""
    Backend audit: {prefix} files

    SCOPE:
    - Pattern: backend/services/{prefix}*.py
    - Max 20 files per agent
    - Ignore: __pycache__, test_*

    TASK:
    1. List all classes
    2. Count public methods per class
    3. Flag if >500 lines (too large)
    4. Flag if >3 wrapper classes (code smell)

    DEADLINE: 20 seconds MAX
    PARTIAL OK: Return files scanned

    FORMAT:
    {{
      "status": "complete|partial",
      "files_scanned": [...],
      "classes": [...],
      "issues": [...]
    }}
    """)

# Result: 67 files in 20 seconds
# Aggregation:
{
    "total_files": 67,
    "total_classes": 45,
    "issues": [
        "agi_tools_mcp.py: 2954 lines (HUGE)",
        "3 wrapper classes found (refactor)"
    ]
}
```

---

## KEY TAKEAWAYS

1. **ALWAYS SET DEADLINE** - No deadline = perfectionism = slow
2. **PARTITION BIG WORK** - 5 agents × 20s > 1 agent × 5 min
3. **ACCEPT 70%** - Partial results are OK, embrace pragmatism
4. **SCOPE ULTRA-PRECISE** - "backend" is vague, "backend/services/[a-e]*.py" is precise
5. **PARALLEL = DEFAULT** - If independent → parallelize always
6. **AGGREGATE QUICKLY** - Your job is CEO, not executor

---

**Version:** 1.0.0 (Quick Reference)
**Last Updated:** 2025-10-20
**Use:** When creating agent tasks - copy template above
**Key Skill:** DEADLINE discipline = 5-20x speedup
