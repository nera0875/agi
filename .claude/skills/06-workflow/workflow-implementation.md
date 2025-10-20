---
title: Workflow Implementation & Agent Delegation
category: workflow
priority: critical
updated: 2025-10-20
version: 1.0
agent: architect
---

# Workflow Implementation & Agent Delegation

## CEO Mindset: Delegate, Don't Execute

**You are NOT a worker. You are a CEO directing 50+ agents.**

### The Problem: Solo Worker

```python
# Solo worker approach (WRONG)
ME: Read codebase
ME: Analyse
ME: Decide
ME: Code
ME: Test

Result: 2 hours to complete task
Agents doing: Nothing
```

### The Solution: CEO Directing Team

```python
# CEO approach (RIGHT)
ME: Decide what to analyze
AGENTS: Read/Analyse/Code/Test in PARALLEL

# Example: Audit 50 backend files
Solo: 50 files × 2 min per file = 100 minutes
CEO: Divide into 5 agents × 10 files each × 2 min = 20 minutes

= 80% time savings via parallelization
```

## Agent Workflow Architecture

### The 6-Phase Pipeline

```
┌─────────────────────┐
│ PHASE 1: UNDERSTAND │ ← ask agents (parallel)
│ Explore codebase    │   Max 3-5 agents
└─────────────────────┘
         ↓
┌─────────────────────┐
│ PHASE 2: RESEARCH   │ ← research agents (parallel)
│ External context    │   Max 3-5 agents
└─────────────────────┘
         ↓
┌─────────────────────┐
│ PHASE 3: ARCHITECT  │ ← architect (1-3 agents)
│ Design solution     │   Sequential, not parallel
└─────────────────────┘
         ↓
┌─────────────────────┐
│ PHASE 4: IMPLEMENT  │ ← code/frontend (parallel)
│ Build features      │   Max 5-10 agents
└─────────────────────┘
         ↓
┌─────────────────────┐
│ PHASE 5: VALIDATE   │ ← debug agents (parallel)
│ Test everything     │   Max 3-5 agents
└─────────────────────┘
         ↓
┌─────────────────────┐
│ PHASE 6: DOCUMENT   │ ← docs (1 agent)
│ Write docs          │   Sequential
└─────────────────────┘
```

### Key Principle: No Agent Calls Other Agent

```python
❌ WRONG: Agent → calls other agent → causes chaos
Agent1: Task(ask, "Explore X")
  ↓ (Agent1 calls Agent2)
Agent2: Task(ask, "Expand on X")
  ↓ (Agent2 calls Agent3)
Agent3: Does something
(Unpredictable, expensive, loops possible)

✅ RIGHT: Orchestrator calls all agents
Orchestrator (ME): Task(ask, ...)
Orchestrator (ME): Task(ask, ...)
Orchestrator (ME): Task(research, ...)
(All independent, predictable, all in parallel)
```

### Prompt Structure (Ultra-Precise)

Every agent prompt MUST have:

```markdown
# REQUIRED FORMAT

[Clear Task Description]

DEADLINE: [X seconds] MAX
SCOPE: [Exactly what to do - no more]
PARTIAL OK: [If timeout, return what you have]
FORMAT: JSON

Output Expected:
{
  "status": "complete|partial",
  "result": [...],
  "message": "..."
}
```

### Example: Audit Backend Codebase (45s deadline)

**Parallel Agent Assignments:**

```python
# Agent 1: Scan services
Task(ask, """
Scan backend/services/*.py

DEADLINE: 15s
SCOPE:
  - List all Python files
  - Extract class names
  - Extract public method names

OUTPUT: {files: [name], classes: [{name, methods: []}]}
PARTIAL OK: If timeout, return what you have
""")

# Agent 2: Scan API routes
Task(ask, """
Scan backend/api/*.py

DEADLINE: 15s
SCOPE:
  - List all Python files
  - Find @app routes
  - Extract endpoint paths

OUTPUT: {files: [...], endpoints: [{path, method}]}
PARTIAL OK: Return partial results
""")

# Agent 3: Find tests
Task(ask, """
Scan backend/tests/test_*.py

DEADLINE: 15s
SCOPE:
  - List test files
  - Count test functions
  - Estimate coverage areas

OUTPUT: {test_files: [...], total_tests: N}
PARTIAL OK: Return count of what you scanned
""")

# ME: Aggregate after all complete (max 5s)
results = [agent1, agent2, agent3]
audit = aggregate(results)
# Results: Complete audit in 20s vs 30min solo
```

## When to Use Each Agent

### PHASE 1: ask (Codebase Exploration)

**When:**
- Exploring existing codebase
- Finding where logic lives
- Understanding current architecture
- Identifying duplicates

**NOT:**
- External research (use research)
- Designing architecture (use architect)
- Coding (use code/frontend)

**Example:**
```python
Task(ask, """
Find all classes related to memory in backend/

Scan:
- backend/services/memory*.py
- backend/models/memory*.py
- backend/tests/*memory*.py

DEADLINE: 20s
SCOPE: List classes, their methods, brief purpose

OUTPUT: List of {file, class, methods}
""")
```

### PHASE 2: research (External Context)

**When:**
- Need documentation patterns
- Looking for best practices
- Researching libraries
- Understanding frameworks

**NOT:**
- Internal codebase exploration (use ask)
- Architecture design (use architect)
- Implementation (use code)

**Example:**
```python
Task(research, """
Find best practices for GraphQL Subscriptions

Sources:
- Official Strawberry documentation
- Apollo Client useSubscription patterns
- Production examples

DEADLINE: 30s
SCOPE: Top 3 patterns, pros/cons, code examples

OUTPUT: {patterns: [{name, pros, cons, example}]}
""")
```

### PHASE 3: architect (Design System)

**When:**
- Designing new feature
- Planning refactoring
- Creating ADR (Architectural Decision Record)
- Deciding between options

**NOT:**
- Small bug fixes (skip to code)
- Implementation details (use code)
- Infrastructure setup (use sre)

**Example:**
```python
Task(architect, """
Design notifications system (real-time)

Constraints:
- Must update frontend instantly
- Current stack: FastAPI, Neo4j, React
- Need scalability for 1M+ users

DEADLINE: 30s
SCOPE:
  - Top 2 architecture options
  - Pros/cons comparison
  - Recommendation with reasoning

OUTPUT: {options: [{name, pros, cons}], recommendation: {}}
""")
```

### PHASE 4a: code (Backend/Python)

**When:**
- Implement API endpoints
- Create services
- Database migrations
- Configuration

**Scope:**
```
✅ backend/api/schema.py (GraphQL)
✅ backend/routes/*.py
✅ backend/services/*.py
✅ backend/models/*.py
✅ backend/migrations/
✅ Scripts, config, general Python
```

**NOT:**
```
❌ React components (use frontend)
❌ Infrastructure setup (use sre)
❌ Testing only (use debug)
```

**Example:**
```python
Task(code, """
Implement notification mutation in GraphQL

Location: backend/api/schema.py

Task:
1. Add Notification model if missing
2. Create sendNotification mutation
3. Connect to service

DEADLINE: 30s
SCOPE: Just the mutation, no service logic yet

OUTPUT: Code snippet + location
""")
```

### PHASE 4b: frontend (React/TypeScript)

**When:**
- Create React components
- Implement hooks
- Design UI with shadcn/ui
- TanStack Table

**Scope:**
```
✅ frontend/src/components/*.tsx
✅ frontend/src/pages/*.tsx
✅ frontend/src/hooks/*.ts
✅ Tailwind CSS styling
✅ Apollo Client hooks
✅ shadcn/ui usage
```

**NOT:**
```
❌ Backend API (use code)
❌ Creating new shadcn/ui components (already exist)
❌ Infrastructure (use sre)
```

**Example:**
```python
Task(frontend, """
Create NotificationCenter component

Use:
- shadcn/ui components (Button, Card, Badge)
- Apollo useSubscriptionToNotifications hook
- TanStack Table for notification list

DEADLINE: 30s
SCOPE: Component with basic styling

IMPORTANT: Follow Figma design if it exists
OUTPUT: JSX code + hook usage
""")
```

### PHASE 5: debug (Testing & Validation)

**When:**
- Writing tests
- Finding bugs
- Integration testing
- E2E validation

**Scope:**
```
✅ pytest for backend
✅ Integration tests
✅ Testing data flow
✅ Validation of changes
✅ Bug fixing
```

**NOT:**
```
❌ New features (use code/frontend)
❌ Infrastructure (use sre)
❌ Documentation (use docs)
```

**Example:**
```python
Task(debug, """
Test notification flow end-to-end

Steps:
1. Create notification in DB
2. Trigger GraphQL subscription
3. Verify frontend receives update

DEADLINE: 20s
SCOPE: Basic flow validation

OUTPUT: Pass/fail + any issues found
""")
```

### PHASE 6: docs (Documentation)

**When:**
- Writing README
- Documenting API
- Creating diagrams
- Architecture docs

**NOT:**
- Code comments (done by code agent)
- Inline documentation (done by developer)

**Example:**
```python
Task(docs, """
Document notification system

Create:
1. Architecture diagram (Mermaid)
2. API documentation
3. How to use from frontend

DEADLINE: 30s
OUTPUT: Markdown + diagrams
""")
```

### ON-CALL: sre (Infrastructure)

**When:**
- Health checks
- Monitoring alerts
- Scaling issues
- Infrastructure problems

**Example:**
```python
Task(sre, """
Check infrastructure health

DEADLINE: 20s
CHECK:
- PostgreSQL responding
- Neo4j responding
- Redis memory usage
- API error rate

OUTPUT: Health status + any alerts
""")
```

## Prompt Writing Rules

### Rule 1: DEADLINE is MANDATORY

```python
❌ WRONG (no deadline):
Task(ask, "Analyze backend")
→ Agent takes 5 minutes

✅ RIGHT (has deadline):
Task(ask, "Analyze backend\nDEADLINE: 20s")
→ Agent works efficiently, returns partial if timeout
```

### Rule 2: SCOPE is ULTRA-PRECISE

```python
❌ WRONG (vague):
Task(ask, "Look at memory stuff")
→ Agent confused, scans everything

✅ RIGHT (precise):
Task(ask, """
Scan backend/services/memory*.py
Extract: Class names, public methods, line count
Sample max 5 files if more exist
DEADLINE: 15s
""")
→ Agent knows EXACTLY what to do
```

### Rule 3: Output Format is REQUIRED

```python
❌ WRONG (unclear output):
Task(ask, "Find services")
→ Response is unstructured text

✅ RIGHT (structured output):
Task(ask, """
Find services
OUTPUT: {services: [{name, file, methods_count}]}
""")
→ Response is JSON, parseable, reliable
```

### Rule 4: PARTIAL OK Prevents Timeout Waiting

```python
❌ WRONG (perfection required):
Task(ask, "Scan ALL 100 backend files")
→ Timeout at 80 files, returns nothing

✅ RIGHT (partial acceptable):
Task(ask, """
Scan backend/ files (max 30s)
PARTIAL OK: Return what you have
""")
→ Timeout at 80 files, returns 25 scanned results (helpful)
```

## Avoiding Common Mistakes

### Mistake 1: Agents Calling Agents
```python
❌ Agent1 calls Task(agent2, ...)
→ Creates loops, expensive, unpredictable

✅ Orchestrator (ME) calls all agents
→ Clean, predictable, efficient
```

### Mistake 2: Too Many Parallel Agents
```python
❌ Task × 50 agents simultaneously
→ Response time = slowest agent = 1 min

✅ Task × 5 agents, batch them
→ Response time = ~20s per batch
→ Multiple batches if needed
```

### Mistake 3: Vague Scope
```python
❌ "Analyze the project"
→ Agent scans EVERYTHING (5 min)

✅ "Scan backend/services/ for duplicate patterns"
→ Agent focused (20s)
```

### Mistake 4: No Output Format
```python
❌ "Find services"
→ Free-form text response (hard to parse)

✅ "Find services\nOUTPUT: JSON list"
→ Structured response (easy to parse)
```

## Phases: When to Use Sequentially vs Parallel

### Sequential (Wait for Previous Phase)

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Reason: Each phase depends on previous
- UNDERSTAND (need results to research)
- RESEARCH (need research for architecture)
- ARCHITECT (need architecture for implementation)
- IMPLEMENT (need design for code)
- VALIDATE (need code for testing)
- DOCUMENT (need final version for docs)
```

### Within Phase: Parallel

```
PHASE 1: ask (Explore codebase)
Agent1: Scan services/
Agent2: Scan api/
Agent3: Scan models/

→ All run simultaneously (independent)
→ Complete 3x faster
```

## Deadlines: Realistic Estimates

| Task | Solo Time | Agent Time | Agents Needed |
|------|-----------|-----------|--------------|
| Scan 1-5 files | 5 min | 20s | 1 |
| Scan 20 files | 20 min | 20s | 5 (4 files each) |
| Scan 100 files | 100 min | 30s | 5 batches × 20s |
| Design architecture | 30 min | 30s | 1 architect |
| Implement 1 feature | 90 min | 30s × 5 agents | 5 (api, service, model, test, doc) |
| Full system design | 4h | 2 min | All phases |

---

**Remember:** A CEO's job is orchestration, not execution. Delegate everything that can be parallelized.
