# Token Optimization - Detailed Instructions

## Foundation: Why Token Economy Matters

Every API call to Claude costs tokens. Orchestrator working alone = massive token overhead. Using agents isolated reduces tokens by **89%**.

**Real numbers:**

```
Solo orchestrator handling 6-phase feature:
  Phase 1: 5,000 tokens (analysis)
  Phase 2: 5,000 tokens (research)
  Phase 3: 5,000 tokens (design)
  Phase 4: 5,000 tokens (backend code)
  Phase 5: 5,000 tokens (frontend code)
  Phase 6: 5,000 tokens (testing)
  TOTAL: 30,000 tokens (2-3 hours)

With agents (isolated conversations):
  Orchestrator: 100 (thinking) + 300 (aggregations) = 400 tokens
  Agent Phase 1: 500 tokens
  Agent Phase 2: 500 tokens
  Agent Phase 3: 500 tokens
  Agent Phase 4: 500 tokens
  Agent Phase 5: 500 tokens
  Agent Phase 6: 500 tokens
  TOTAL: 3,400 tokens (15 minutes)

SAVINGS: 26,600 tokens (89% reduction)
```

## Strategy #1: Isolated Agent Conversations

### The Key Insight

**Agents run in SEPARATE LLM conversations from orchestrator.**

```
Orchestrator (Main Conversation)
├─ Agent 1 conversation (isolated)
│  └─ Tokens counted only for Agent 1
├─ Agent 2 conversation (isolated)
│  └─ Tokens counted only for Agent 2
├─ Agent 3 conversation (isolated)
│  └─ Tokens counted only for Agent 3
└─ CEO aggregation (minimal tokens)
   └─ Combine results + decide next
```

### Why This Saves Tokens

**Solo approach (all in one conversation):**
```
Turn 1: "Analyze backend" → 5,000 tokens
Turn 2: "Now research GraphQL" → 5,000 tokens (context = Turn 1+2)
Turn 3: "Now design system" → 7,000 tokens (context = Turn 1+2+3)
Turn 4: "Now code" → 8,000 tokens (context = Turn 1+2+3+4)
Turn 5: "Now test" → 9,000 tokens (context = all previous)
Total: 34,000 tokens (growing context window = more tokens each turn)
```

**Agent approach (isolated conversations):**
```
Agent 1: "Analyze" → 500 tokens (fresh context)
Agent 2: "Research" → 500 tokens (fresh context)
Agent 3: "Design" → 500 tokens (fresh context)
Agent 4: "Code" → 500 tokens (fresh context)
Agent 5: "Test" → 500 tokens (fresh context)
CEO: "Combine results" → 50 tokens (only results matter)
Total: 3,050 tokens (each agent fresh = smaller tokens)
```

### Implementation

**Always use Task() tool, NEVER do work directly:**

```python
# ❌ EXPENSIVE: Orchestrator does everything
# (10,000 tokens bloated in main conversation)
me_analyzing_code = "..."
me_designing = "..."
me_implementing = "..."

# ✅ CHEAP: Agents work, orchestrator aggregates
# (500 + 500 + 500 + 50 = 1,550 tokens)
Task(ask, "Analyze code")              # 500 tokens (isolated)
Task(architect, "Design system")       # 500 tokens (isolated)
Task(code, "Implement")                # 500 tokens (isolated)
# CEO: Combine results = 50 tokens
```

## Strategy #2: Strict Deadlines

### Philosophy

**Agents work faster when pressed. Partial results beat waiting.**

```
No deadline: "Analyze thoroughly"
  → Agent takes 5 minutes
  → Produces exhaustive analysis
  → But you've been waiting 5 minutes
  → Total: 5 minutes wasted

Strict deadline: "DEADLINE: 30s, PARTIAL OK"
  → Agent rushes
  → Produces 80% analysis in 30s
  → You get useful data immediately
  → Can ask follow-up questions
  → Total: 30s + 10s (follow-up) = 40s
```

**Math:** 80% in 30s > 100% in 5 min

### Deadline Guidelines by Agent Type

| Agent Type | Deadline | Why |
|-----------|----------|-----|
| **ask** (codebase scan) | 10-20s | Many files, sample OK |
| **research** (external) | 20-30s | Web slow, partial results fine |
| **architect** (design) | 30-60s | Single brain, can be thorough |
| **code** (implementation) | 60-120s | Complex work, but focus on core |
| **frontend** (UI) | 60-120s | Complex work, but focus on core |
| **debug** (testing) | 30-60s | Run tests, report results |
| **docs** (documentation) | 30-120s | Write README, not exhaustive |

### Deadline Template

**Every task must include:**

```python
Task(agent_type, """
[Your actual task description]

DEADLINE: [Xs] MAX
SCOPE: [What exactly to do - no more]
PARTIAL OK: If timeout, return what you have
FORMAT: JSON {key: value}

Output: {...}
""")
```

### Examples

**✅ Good (strict deadline):**
```python
Task(ask, """
Scan backend/services/memory*.py

DEADLINE: 20s MAX
SCOPE: List class names + public methods only
IGNORE: Private methods, docstrings, tests
PARTIAL OK: Yes, if timeout return partial list

Output JSON:
{
  "files": ["file1.py", "file2.py"],
  "classes": [
    {"name": "MemoryService", "methods": ["get", "store", "clear"]}
  ]
}
""")
```

**❌ Bad (no deadline, vague):**
```python
Task(ask, """
Analyze the backend code thoroughly and give me
a complete understanding of how everything works,
including all the classes, methods, dependencies,
and potential issues you find.
""")
```

## Strategy #3: Progressive Disclosure

### Concept

**Don't ask for everything at once. Ask in phases.**

```
❌ One big request (expensive):
"Scan 67 files, find duplicates, analyze patterns,
 suggest refactoring, write test coverage, estimate work"
→ Confuses agent
→ Takes 10 minutes
→ Expensive

✅ Progressive steps (cheap):
Step 1: "List 67 files with class counts" → 20s
Step 2: "Find duplicate patterns" → 20s
Step 3: "Suggest refactoring" → 20s
Step 4: "Estimate effort" → 20s
→ Total: 80s, clear phases
→ Can stop early if needed
```

### Implementation Pattern

```python
# Phase 1: Understanding (20s)
files_data = Task(ask, """
List backend/services files
DEADLINE: 20s, PARTIAL OK
""")

# Phase 2: Analysis (20s)
duplicates = Task(ask, """
Find duplicate patterns in:
{files_data}

DEADLINE: 20s, PARTIAL OK
""")

# Phase 3: Recommendations (20s)
recommendations = Task(architect, """
Suggest refactoring based on:
{duplicates}

DEADLINE: 20s, PARTIAL OK
""")

# Phase 4: Summary (aggregate)
summary = aggregate([files_data, duplicates, recommendations])
```

## Strategy #4: Phase Isolation

### 6-Phase Workflow Structure

```
Phase 1: UNDERSTANDING (parallel ask × 10)
  Goal: Map current state
  Duration: 20s
  Tokens: 5,000

Phase 2: RESEARCH (parallel research × 5)
  Goal: External knowledge
  Duration: 30s
  Tokens: 2,500

Phase 3: ARCHITECTURE (single architect × 1)
  Goal: Design solution
  Duration: 60s
  Tokens: 1,000

Phase 4: IMPLEMENTATION (parallel code/frontend × 5)
  Goal: Build solution
  Duration: 120s
  Tokens: 2,500

Phase 5: VALIDATION (parallel debug × 3)
  Goal: Test solution
  Duration: 60s
  Tokens: 1,500

Phase 6: DOCUMENTATION (single docs × 1)
  Goal: Document solution
  Duration: 60s
  Tokens: 1,000

TOTAL: ~6 minutes, 13,500 tokens
(vs 2 hours, 30,000 tokens solo)
```

### Phase Skipping Rules

**Skip phases if not needed:**

```python
# Rule 1: Skip Phase 1 if pattern known
Task(architect, """
Add GraphQL query for notifications
(Already know existing schema/patterns)

DEADLINE: 60s
""")
# Saves 5,000 tokens from Phase 1

# Rule 2: Skip Phase 2 if stack familiar
# Use research only for new technologies
known_stack = ["GraphQL", "React", "FastAPI"]
new_tech = ["Neo4j integration"]  # Only research this

# Rule 3: Skip Phase 3 for simple tasks
# Bug fix, small feature = go straight to Phase 4

# Rule 4: Skip Phase 6 for internal work
# Only document user-facing features
```

### Optimization

**The more you skip, the less tokens:**

```
Full pipeline (all 6 phases): 13,500 tokens
Skip Phase 1 (known pattern): 8,500 tokens
Skip Phase 1+2 (very known): 5,500 tokens
Skip Phase 1+2+6 (internal bug fix): 4,500 tokens

= Dramatic savings for repeated tasks
```

## Strategy #5: Scope Partitioning

### Divide Big Tasks Into Smaller Pieces

**Principle: Each agent gets <15 files or <5 min of work**

```
Backend audit (67 files):

❌ Wrong (1 agent, everything):
Task(ask, "Audit all backend")
→ 5 minutes, 1,000+ tokens

✅ Right (5 agents, each part):
Task(ask, "Scan backend/services/[a-m]*.py")    # ~14 files
Task(ask, "Scan backend/services/[n-z]*.py")    # ~13 files
Task(ask, "Scan backend/api/*.py")               # ~15 files
Task(ask, "Scan backend/routes/*.py")            # ~15 files
Task(ask, "Find duplicates")                     # 1 file analysis
→ 20s total, 500×5 = 2,500 tokens
```

### Partitioning Strategies

**Strategy A: By file pattern**
```python
Task(ask, "Scan backend/services/[a-m]*.py")
Task(ask, "Scan backend/services/[n-z]*.py")
```

**Strategy B: By domain**
```python
Task(ask, "Scan memory-related files")
Task(ask, "Scan graph-related files")
Task(ask, "Scan embedding-related files")
```

**Strategy C: By concern**
```python
Task(ask, "Find all test files")
Task(ask, "Find all config files")
Task(ask, "Find all migration files")
```

**Strategy D: By layer**
```python
Task(ask, "Scan backend/api/")
Task(ask, "Scan backend/services/")
Task(ask, "Scan backend/models/")
Task(ask, "Scan backend/routes/")
```

## Calculation: Token Savings Formula

### Formula 1: Phase Optimization

```
Token Savings = (Solo Tokens - Optimized Tokens) / Solo Tokens

Solo Tokens = tokens_per_phase × phases_in_series
Optimized Tokens = (tokens_per_phase × phases_parallel_multiplier) + aggregation_tokens

Example:
Solo: 5,000 × 6 = 30,000 tokens
Optimized: (500 × 6) + 400 = 3,400 tokens
Savings = (30,000 - 3,400) / 30,000 = 88.7% ✅
```

### Formula 2: Parallelization Factor

```
Parallelization Factor = (agents_count × agent_duration) / wall_time

Example:
10 agents × 30s each = 300s of work
Wall time = 30s (all parallel)
Factor = 300/30 = 10x speedup
```

### Formula 3: Token Efficiency

```
Token Efficiency = feature_value / tokens_spent

Good feature: 100 value, 5,000 tokens = 0.02 value/token
Great feature: 100 value, 1,000 tokens = 0.1 value/token
= 5x more efficient
```

## Real-World Examples

### Example 1: Audit Backend (89% Savings)

**Solo (Old Way):**
```
Me: Scan backend (3 min) → 5,000 tokens
Me: Grep patterns (2 min) → 3,000 tokens
Me: Synthesis report (2 min) → 2,000 tokens
Total: 10,000 tokens, 7 minutes
```

**Optimized (New Way):**
```
Agent 1: Scan services/ → 500 tokens (20s)
Agent 2: Scan api/ → 500 tokens (20s)
Agent 3: Scan routes/ → 500 tokens (20s)
Agent 4: Find duplicates → 500 tokens (20s)
Agent 5: Find issues → 500 tokens (20s)
CEO: Aggregate → 50 tokens (20s)
Total: 2,550 tokens, 20s

Savings: 75% tokens, 99.5% time
```

### Example 2: Implement Feature (72% Savings)

**Solo (Old Way):**
```
Phase 1: Understand (2h) → 8,000 tokens
Phase 2: Design (1h) → 4,000 tokens
Phase 3: Code (2h) → 8,000 tokens
Phase 4: Test (1h) → 4,000 tokens
Phase 5: Document (30m) → 2,000 tokens
Total: 26,000 tokens, 6.5 hours
```

**Optimized (New Way):**
```
Phase 1: Task(ask, ...) × 5 = 2,500 tokens (20s)
Phase 2: Task(research, ...) × 2 = 1,000 tokens (30s)
Phase 3: Task(architect, ...) = 1,000 tokens (60s)
Phase 4: Task(code, ...) + Task(frontend, ...) = 2,000 tokens (120s)
Phase 5: Task(debug, ...) × 2 = 1,000 tokens (60s)
Phase 6: Task(docs, ...) = 1,000 tokens (60s)
CEO aggregation = 500 tokens
Total: 9,000 tokens, 15 minutes

Savings: 65% tokens, 98% time
```

## Practical Checklist

### Before Starting Task

- [ ] **Can this be parallelized?** (multiple files/domains)
- [ ] **Estimate token cost if solo** (phases × tokens/phase)
- [ ] **Identify phases** (understanding → research → design → implement → test → document)
- [ ] **Plan scope partitioning** (which files to which agents)
- [ ] **Set deadlines** (20-30s for exploration, 60-120s for implementation)
- [ ] **Prepare aggregation logic** (how to combine results)

### During Execution

- [ ] **Launch all Phase N tasks at once** (no waiting)
- [ ] **Collect results in JSON** (easy to aggregate)
- [ ] **Skip phases if possible** (known pattern?)
- [ ] **Accept partial results** (80% in 30s > 100% in 5 min)
- [ ] **Monitor token spend** (track vs budget)

### After Completion

- [ ] **Compare solo vs optimized cost** (calculate savings)
- [ ] **Record pattern** (for future similar tasks)
- [ ] **Optimize further** (if bottleneck found)
- [ ] **Share learnings** (with other orchestrators)

## Common Mistakes

### Mistake 1: Overlapping Scopes

```python
# ❌ Bad: Both scan same files
Task(ask, "Scan backend/")
Task(ask, "Scan backend/")

# ✅ Good: Clear boundaries
Task(ask, "Scan backend/services/")
Task(ask, "Scan backend/api/")
```

### Mistake 2: No Deadline

```python
# ❌ Bad: Agent procrastinates
"Analyze code"

# ✅ Good: Agent rushes
"Analyze code - DEADLINE: 30s"
```

### Mistake 3: Expecting 100% Accuracy

```python
# ❌ Bad: Waits for perfection
"Find every bug in the code"

# ✅ Good: Accept 80%
"Find major bugs - DEADLINE: 20s, PARTIAL OK"
```

### Mistake 4: Sequential When Parallel

```python
# ❌ Bad: Wait for each
Task(ask, "Scan api/")
wait()
Task(ask, "Scan services/")

# ✅ Good: Parallel
Task(ask, "Scan api/")
Task(ask, "Scan services/")
# (no wait between)
```

## Token Budget Planning

### Project Budget Allocation

```
Small feature: <5,000 tokens
  - Phase 3 (architect) + Phase 4 (code) only
  - Skip 1, 2, 5, 6
  - Deadline: 10 min

Medium feature: 5,000-15,000 tokens
  - All phases
  - Partitioned smartly
  - Deadline: 30 min

Large feature: 15,000-50,000 tokens
  - Multiple architecture revisions
  - Extensive testing
  - Thorough documentation
  - Deadline: 2 hours

Refactoring: 10,000-30,000 tokens
  - Phase 1 (understand current)
  - Phase 3 (design new)
  - Phase 4 (implement)
  - Phase 5 (validate)
```

### Cost Control

**Monthly budget: 1M tokens**

```
Daily budget: 1M / 30 = 33,333 tokens/day

Distribution:
- Features (60%): 20,000 tokens
- Bug fixes (20%): 6,666 tokens
- Refactoring (10%): 3,333 tokens
- Research (10%): 3,333 tokens
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Audience:** CEO/Orchestrator Mode
**Status:** Production Ready
