---
name: "CEO Mindset - Parallel Delegation"
description: "Entrepreneur mindset: delegate 10-50 agents in parallel, ultra-precise prompts, CEO efficiency patterns"
categories: ["workflow", "delegation", "optimization", "system"]
tags: ["CEO", "parallel", "agents", "Task", "efficiency", "scaling", "delegation", "management"]
version: "1.0.0"
enabled: true
---

## Overview

**CEO Mindset** transforms from individual contributor to delegation leader. Instead of doing work solo, orchestrate 10-50 agents in parallel for 20x faster results.

This is the **core efficiency multiplier** for AGI: one smart director + many fast workers = exponential output.

## Key Principle

### From Solo Worker to CEO

**Before (Solo Worker - 1 hour):**
```
Me: Scan backend/services
Me: Analyze 67 files manually
Me: Grep doublons
Me: Check structure
Result: Audit report (takes 1 hour)
```

**After (CEO - 3 minutes):**
```
CEO: Task(ask, "Scan services/[a-c]*.py")
CEO: Task(ask, "Scan services/[d-f]*.py")
CEO: Task(ask, "Scan services/[g-i]*.py")
     ... 7 more tasks in parallel
Result: Same audit report (takes 3 minutes)
= 20x faster
```

## When to Use This Skill

### Use CEO Mindset when:
- Complex tasks with multiple independent steps
- Codebase exploration (50+ files)
- Multi-phase implementations (analysis → design → code → test)
- Bottleneck work waiting on results
- Need rapid iteration on multiple fronts
- **Any task parallelizable into 5+ independent pieces**

### Avoid parallelization when:
- Simple, focused task (1-2 files)
- Sequential dependencies (phase 2 needs phase 1 output)
- Single agent sufficient (low complexity)
- Overhead of coordination > speedup

## Related Skills

- **Project Structure** - Where code goes (context for delegation)
- **Workflow Implementation** - How to execute on plan
- **Agent Collaboration** - How agents work together

## Core Concepts

### 1. Decomposition (Divide and Conquer)

**Big task → micro-tasks**

```python
# Bad: 1 agent does everything (slow)
Task(ask, "Analyze entire backend")

# Good: 10 agents, each does part (fast)
Task(ask, "Scan services/[a-c]*.py")  # Agent 1
Task(ask, "Scan services/[d-f]*.py")  # Agent 2
Task(ask, "Scan services/[g-i]*.py")  # Agent 3
...
```

**Rule:** If task takes >30s, split into ≥3 parallel pieces

### 2. Ultra-Precise Prompts

**Flaky agents need crystal-clear instructions**

```python
# Bad: Agent confused, takes 5min
"Analyze the backend"

# Good: Agent knows exactly what to do, takes 30s
"Scan backend/services/memory*.py
- List all classes
- Extract public methods
- Ignore test files
- Max 10 files (sample if more)
- 15s deadline
- Return JSON: {files: [], classes: []}"
```

### 3. Scope Discipline

**Each agent has ONE clear scope**

```python
Agent 1: "Scan services/ only"
Agent 2: "Scan api/ only"
Agent 3: "Scan routes/ only"
   ✅ Clear boundaries, no overlap

Agent 1: "Scan everything"
   ❌ Chaos, agents stepping on each other
```

### 4. Deadline Management

**Agents work faster with time pressure**

```python
"DEADLINE: 20s MAX
PARTIAL OK: If timeout, return what you have"

Result:
- Agent rushes, gets 80% in 20s
- CEO gets useful partial data
- Better than 1 agent taking 5min for perfection
```

### 5. Aggregation

**CEO's critical job: combine N results into 1 vision**

```python
# Agents return:
result1 = {files: [a, b], errors: 2}
result2 = {files: [c, d, e], errors: 0}
result3 = {files: [f], errors: 1}

# CEO aggregates:
all_files = result1['files'] + result2['files'] + result3['files']
total_errors = result1['errors'] + result2['errors'] + result3['errors']
print(f"Total: {len(all_files)} files, {total_errors} errors")
```

## Workflow: 6 Phases

### Phase 1: UNDERSTANDING (parallel - ask agents)
- Explore existing codebase
- Scan directory structure
- Find similar code patterns
- **Duration:** 1-2 min (10 agents × 20s max)

### Phase 2: RESEARCH (parallel - research agents)
- Search external docs/examples
- Learn library best practices
- Find code patterns online
- **Duration:** 2-3 min (5 agents × 30s max)

### Phase 3: ARCHITECTURE (single - architect)
- Design solution based on context
- Evaluate trade-offs
- Create implementation plan
- **Duration:** 1-2 min (wait for aggregated Phase 1-2 results)

### Phase 4: IMPLEMENTATION (parallel - code/frontend)
- Backend code (code agent)
- Frontend code (frontend agent)
- Database migrations (code agent)
- Configuration (code agent)
- **Duration:** 2-5 min (3-5 agents × 30s - 2min each)

### Phase 5: VALIDATION (parallel - debug agents)
- Unit tests
- Integration tests
- E2E tests
- **Duration:** 2-3 min (3 agents × 30-60s each)

### Phase 6: DOCUMENTATION (single - docs)
- README
- API documentation
- Architecture diagram
- **Duration:** 1-2 min (wait for code to be done)

## Anti-Patterns to Avoid

### Pattern 1: Sequential When Should Be Parallel

```python
# ❌ Bad: Wait for each to finish
Task(ask, "Scan api/")
wait()
Task(ask, "Scan routes/")
wait()
Task(ask, "Scan services/")
wait()
# Total: 1+1+1 = 3 min

# ✅ Good: Launch all at once
Task(ask, "Scan api/")  # All in parallel
Task(ask, "Scan routes/")
Task(ask, "Scan services/")
# Total: 1 min (3 agents × 20s simultaneous)
```

### Pattern 2: Vague Instructions

```python
# ❌ Bad: Agent doesn't know what to do
"Analyze the code"

# ✅ Good: Agent knows exactly
"Scan backend/services/*.py
- Extract class names
- Find public methods
- Return JSON"
```

### Pattern 3: Overlapping Scope

```python
# ❌ Bad: Both agents scan same files
Agent 1: "Scan backend/"
Agent 2: "Scan backend/"
# Risk: Duplicated work, conflicting results

# ✅ Good: Each covers part
Agent 1: "Scan backend/services/"
Agent 2: "Scan backend/api/"
```

### Pattern 4: No Deadline

```python
# ❌ Bad: Agent takes 5min for perfection
"Analyze completely, 100% thorough"

# ✅ Good: Agent rushes but useful
"DEADLINE: 30s, PARTIAL OK if timeout"
# Gets 80% in 30s > waiting 5min for 100%
```

### Pattern 5: Wrong Agent Type

```python
# ❌ Bad: Use code agent for research
Task(code, "Find best practices for GraphQL")

# ✅ Good: Use research agent
Task(research, "Find best practices for GraphQL")
```

## Agent Types and When to Use

| Agent | Best For | Deadline | Parallelizable |
|-------|----------|----------|-----------------|
| **ask** | Code exploration (read-only) | 10-20s | ✅ Yes (×10) |
| **research** | External research | 20-30s | ✅ Yes (×5) |
| **architect** | System design | 30-60s | ❌ No (×1) |
| **code** | Backend implementation | 30-120s | ✅ Yes (×5) |
| **frontend** | React/UI implementation | 30-120s | ✅ Yes (×3) |
| **debug** | Testing/validation | 30-60s | ✅ Yes (×3) |
| **docs** | Documentation | 30-120s | ❌ No (×1) |

## Practical Examples

### Example 1: Quick Code Audit

**Objective:** Find duplicated code in backend (67 files)

**Solo (1 hour):**
1. Manually scan each file
2. Look for similar patterns
3. Write report

**CEO (5 minutes):**
```python
# Phase 1: Scan (parallel × 5 agents, 20s each)
Task(ask, "Scan backend/services/[a-m]*.py - find classes")
Task(ask, "Scan backend/services/[n-z]*.py - find classes")
Task(ask, "Scan backend/api/*.py - find endpoints")
Task(ask, "Scan backend/routes/*.py - find routes")
Task(ask, "Find all *_wrapper.py vs *_service.py files")

# CEO aggregates → identifies duplicates

# Phase 2: Verify (parallel × 2 agents)
Task(code, "Scan for copy-pasted code patterns")
Task(code, "Check imports for circular deps")

# Result: Same audit, 12x faster
```

### Example 2: Feature Implementation

**Objective:** Implement notifications feature

**Solo (2 days):**
1. Design system (1 hour)
2. Backend code (3 hours)
3. Frontend code (3 hours)
4. Tests (2 hours)
5. Docs (1 hour)

**CEO (15 minutes):**
```python
# Phase 1: Understanding (parallel)
Task(ask, "Find notification-related code")
Task(ask, "Check WebSocket usage")
Task(ask, "Check GraphQL subscriptions")

# Phase 2: Research (parallel)
Task(research, "GraphQL Subscriptions best practices")
Task(research, "React hooks for subscriptions")

# Phase 3: Architecture
Task(architect, "Design real-time notifications system")
# CEO validates design

# Phase 4: Implement (parallel)
Task(code, "Backend: GraphQL subscription")
Task(frontend, "Frontend: useSubscription hook")
Task(code, "Database: notifications table migration")

# Phase 5: Validate (parallel)
Task(debug, "Test backend subscription")
Task(debug, "Test frontend hook")
Task(debug, "E2E test")

# Phase 6: Document
Task(docs, "Document notifications feature")

# Result: Full feature, faster + more thorough
```

### Example 3: Infrastructure Check

**Objective:** Audit system health

**Solo (30 minutes):**
1. Check database
2. Check API costs
3. Check logs
4. Check performance

**CEO (5 minutes):**
```python
# Phase 1: Parallel health checks
Task(sre, "PostgreSQL health")
Task(sre, "Neo4j health")
Task(sre, "Redis health")
Task(sre, "Check API costs (Anthropic, Voyage)")
Task(ask, "Find recent errors in logs")

# CEO aggregates → generates report

# Result: Full health report, 6x faster
```

---

## Implementation Rules

1. **Always decompose first** - Think before launching agents
2. **Ultra-precise prompts** - Clear scope, deadline, format
3. **Parallel when independent** - Sequential only when dependent
4. **Aggregate results carefully** - Combine without losing info
5. **Timeout gracefully** - Partial results > no results
6. **Monitor token usage** - Parallel agents = more tokens
7. **Use JSON formats** - Easy aggregation

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System Architecture
**Audience:** CEO/Director Mode (Advanced)
