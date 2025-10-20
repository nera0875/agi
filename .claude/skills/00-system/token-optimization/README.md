---
name: "Token Optimization"
description: "Minimize tokens via isolated agents, strict deadlines, progressive disclosure. Economy 89% vs solo"
categories: ["system", "optimization", "tokens", "efficiency"]
tags: ["tokens", "economy", "cost", "parallel", "deadlines", "agents", "throughput"]
version: "1.0.0"
enabled: true
---

## Overview

**Token Optimization** is the efficiency multiplier for AGI orchestration. By leveraging **isolated agent conversations**, **strict deadlines**, and **phase skipping**, we achieve **89% token reduction** compared to solo orchestration.

### The Magic Formula

**Solo (No optimization):**
- Self: 5,000 tokens × 6 phases = **30,000 tokens**

**Optimized (With agents):**
- Self: 100 tokens (thinking) + 50×6 (aggregation) = 400 tokens
- Agents (isolated): 500 tokens × 6 phases = 3,000 tokens
- **Total: 3,400 tokens (89% economy)**

## Key Principles

### 1. Isolated Agent Conversations

**Critical insight:** Agents run in **separate LLM conversations**.

Each agent's work:
- ✅ Doesn't count in main conversation history
- ✅ Costs only agent's tokens (cheap Haiku)
- ✅ Doesn't bloat orchestrator context window
- ✅ Results return as JSON to orchestrator

**Result:** 20 agents working = ~500 tokens each (10k total) vs 100k tokens if orchestrator did it all.

### 2. Strict Deadlines

**Agents work faster when pressed:**

```python
# Loose deadline (no pressure)
"Analyze thoroughly" → Agent takes 5 minutes

# Strict deadline (pressure)
"DEADLINE: 30s, PARTIAL OK if timeout" → Agent rushes, 80% in 30s
```

**Philosophy:** 80% in 30s > 100% in 5 minutes. Partial data is still useful.

### 3. Progressive Disclosure

**Don't ask for everything at once:**

```python
# ❌ Expensive (full scope)
"Scan 50 files, analyze each, find duplicates, check patterns, test"
→ Takes 10 min, massive token overhead

# ✅ Cheap (progressive)
Task 1: "List 50 files" → 20s
Task 2: "Find duplicates in results" → 20s
Task 3: "Analyze patterns" → 20s
→ Total: 60s, tokenomically efficient
```

## When to Use

### Use Token Optimization when:
- ✅ Complex multi-phase task (analysis → design → code → test)
- ✅ Large codebase exploration (50+ files)
- ✅ Multiple independent tasks (parallelizable)
- ✅ Budget token is tight
- ✅ Speed is critical (users waiting)

### Avoid when:
- ❌ Simple focused task (1-2 files, 1 agent enough)
- ❌ Sequential dependencies (phase 2 needs phase 1)
- ❌ One-shot answers (no phases)
- ❌ Overhead > benefit

## Techniques

### Technique 1: Phase Isolation

**Separate work into phases, each phase is parallel:**

```
Phase 1: Understanding (parallel × 10 agents)
  ├─ Task(ask, "Scan services/[a-m]*.py")
  ├─ Task(ask, "Scan services/[n-z]*.py")
  ├─ Task(ask, "Scan api/*.py")
  └─ ... (7 more agents)

↓ CEO aggregates Phase 1

Phase 2: Research (parallel × 5 agents)
  ├─ Task(research, "GraphQL patterns")
  ├─ Task(research, "React patterns")
  └─ ... (3 more agents)

↓ CEO aggregates Phase 2

Phase 3: Architecture (single)
  └─ Task(architect, "Design based on Phase 1+2")

↓ CEO validates

Phase 4: Implementation (parallel × 5 agents)
  ├─ Task(code, "Backend API")
  ├─ Task(frontend, "React UI")
  └─ ... (3 more agents)

↓ CEO aggregates Phase 4

Phase 5: Validation (parallel × 3 agents)
  ├─ Task(debug, "Unit tests")
  ├─ Task(debug, "Integration tests")
  └─ Task(debug, "E2E tests")
```

**Result:** Each phase is 20-30s, total ~2 min vs 2 hours solo.

### Technique 2: Scope Partitioning

**Divide work by file patterns or domains:**

```python
# 67 backend files → 5 agents
Task(ask, "Scan backend/services/[a-m]*.py")  # ~14 files
Task(ask, "Scan backend/services/[n-z]*.py")  # ~13 files
Task(ask, "Scan backend/api/*.py")             # ~15 files
Task(ask, "Scan backend/routes/*.py")          # ~15 files
Task(ask, "Scan backend/agents/*.py")          # ~10 files

# Each agent: 20s max
# Total: 20s (parallel) vs 100s (sequential)
```

### Technique 3: Deadline Enforcement

**Every task must have strict deadline and PARTIAL OK clause:**

```python
Task(ask, """
Scan backend/services/memory*.py

DEADLINE: 20s MAX
SCOPE: List classes + public methods only
PARTIAL OK: If timeout, return what you have
FORMAT: JSON {files: [], classes: []}

Output: {...}
""")
```

**Result:**
- Agent doesn't procrastinate
- Partial results still useful
- No blocked waiting
- Predictable throughput

### Technique 4: Early Phase Skipping

**Skip phases if not needed:**

```python
# Feature: Add GraphQL query (known pattern)

❌ Full pipeline:
Phase 1: Ask "explore existing schema" → 20s
Phase 2: Research "GraphQL patterns" → 30s
Phase 3: Architect "new query design" → 60s
Phase 4: Code "implement query" → 120s
Total: 230s

✅ Optimized:
Phase 3: Architect "add query to existing pattern" → 60s
Phase 4: Code "implement query" → 120s
Total: 180s (Save 50 seconds!)

# Rule: Skip Phase 1+2 if pattern is known/local
```

### Technique 5: Result Aggregation

**CEO's critical job: combine N results efficiently:**

```python
# From agents:
result1 = {"files": ["a.py", "b.py"], "classes": 5, "methods": 23}
result2 = {"files": ["c.py", "d.py"], "classes": 3, "methods": 12}
result3 = {"files": ["e.py"], "classes": 1, "methods": 4}

# CEO aggregates (10 tokens):
all_files = result1["files"] + result2["files"] + result3["files"]
total_classes = result1["classes"] + result2["classes"] + result3["classes"]
total_methods = result1["methods"] + result2["methods"] + result3["methods"]

output = {
  "files": all_files,           # 5 files
  "total_classes": total_classes,  # 9 classes
  "total_methods": total_methods    # 39 methods
}
```

## Token Cost Calculations

### Example 1: Backend Audit (67 files)

**Solo approach (orchestrator does it all):**
```
Phase 1: Read & analyze 67 files in chunks
  - Tokens per file: ~20 tokens
  - 67 files × 20 = 1,340 tokens
Phase 2: Grep for patterns
  - Tokens: 500
Phase 3: Synthesize report
  - Tokens: 500
Total: 2,340 tokens (takes 5 min)
```

**Optimized approach (5 agents × Phase 1):**
```
Agent 1: Scan files [a-m] → 500 tokens
Agent 2: Scan files [n-z] → 500 tokens
Agent 3: Scan api/ → 500 tokens
Agent 4: Scan routes/ → 500 tokens
Agent 5: Find duplicates → 500 tokens

Orchestrator aggregates: 50 tokens
Total: 2,550 tokens (takes 20s)
= Same results, 15x faster!
```

### Example 2: Feature Implementation (Notifications)

**Solo approach (2 hours):**
```
Self analysis: 30 min = 5,000 tokens
Self design: 30 min = 5,000 tokens
Self backend: 30 min = 5,000 tokens
Self frontend: 30 min = 5,000 tokens
Total: 20,000 tokens + 2 hours
```

**Optimized approach (15 min):**
```
Phase 1: ask × 3 (explore notification code)
  - 500 tokens each = 1,500 tokens

Phase 2: research × 2 (GraphQL Subscriptions, React patterns)
  - 500 tokens each = 1,000 tokens

Phase 3: architect × 1 (design)
  - 1,000 tokens

Phase 4: code × 3, frontend × 2 (implement)
  - 1,000 tokens each = 5,000 tokens

Phase 5: debug × 3 (test)
  - 1,000 tokens each = 3,000 tokens

Orchestrator aggregation: 200 tokens

Total: 11,700 tokens + 15 min
= 44% token save, 8x faster!
```

## Anti-Patterns

### ❌ Anti-Pattern 1: No Deadline

```python
# Bad: Agent takes forever
Task(ask, "Analyze backend")

# Good: Agent rushes
Task(ask, """
Analyze backend/services
DEADLINE: 30s
PARTIAL OK: yes
""")
```

### ❌ Anti-Pattern 2: Overlapping Scopes

```python
# Bad: Both agents scan same files
Agent 1: "Scan backend/"
Agent 2: "Scan backend/"
# Duplicate work, no parallelization benefit

# Good: Each has clear scope
Agent 1: "Scan backend/services/"
Agent 2: "Scan backend/api/"
```

### ❌ Anti-Pattern 3: No Phase Separation

```python
# Bad: Mix everything in one prompt
Task(code, """
Design and implement notifications,
write tests, update docs, deploy
""")
# Takes 10 min, agent confused, bloated

# Good: Separate phases
Phase 3: Task(architect, "Design notifications") → 60s
Phase 4: Task(code, "Implement notifications") → 120s
Phase 5: Task(debug, "Test") → 60s
Phase 6: Task(docs, "Document") → 60s
# Total 300s, each agent focused
```

### ❌ Anti-Pattern 4: Sequential When Parallel

```python
# Bad: Wait for each
Task(ask, "Scan api/")
wait()
Task(ask, "Scan routes/")
wait()
Task(ask, "Scan services/")
# Takes 3 min

# Good: Launch all at once
Task(ask, "Scan api/")
Task(ask, "Scan routes/")
Task(ask, "Scan services/")
# Takes 1 min (all parallel)
```

## Monitoring Token Usage

### Track Efficiency Metrics

```python
# Metric 1: Parallelization Factor
parallelization_factor = (agents_count × avg_agent_time) / total_wall_time
# 10 agents × 30s / 30s = 10x

# Metric 2: Token Multiplier
token_multiplier = solo_tokens / optimized_tokens
# 20,000 / 3,400 = 5.88x

# Metric 3: Cost per Feature
cost_per_feature = total_tokens / feature_count
# Target: <5,000 tokens per feature
```

### Optimization Goals

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Parallelization Factor | >3x | >5x | >10x |
| Token Multiplier | >2x | >3x | >5x |
| Cost per Feature | <10k | <5k | <3k |
| Deadline adherence | 80% | 90% | 95% |

## Related Skills

- **CEO Mindset** - Delegation strategy (foundation)
- **Agent Collaboration** - Multi-agent workflows
- **Workflow Implementation** - Practical execution
- **Project Structure** - Where code goes (reduces exploration overhead)

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System Architecture
**Audience:** CEO/Director Mode (Advanced)
**Status:** Production
