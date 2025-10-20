# Decision Framework - Detailed Instructions for Agent Routing

## Executive Summary

Transform raw user request → optimal agent routing in <10 seconds.

**Framework:** Decision tree (binary) + Pattern matching + Phase logic + Parallel/Sequential rules

---

## Part 1: Decision Tree (Step-by-Step)

### Level 1: Code Exploration?

**Question:** "Is user asking to explore/audit/find/understand existing code?"

**Indicators (YES):**
- "audit", "explore", "where is", "find", "check", "scan", "examine"
- "how does", "what exists", "is there", "find duplicate"
- Keywords: `analyze code structure`, `code review`, `search pattern`

**Indicators (NO):**
- "implement", "create", "add", "fix bug", "build", "design"
- "what's best practice", "how to", "documentation"

**Decision:**
- ✅ YES → **ask agent** (local codebase read-only)
- ❌ NO → Go to Level 2

**Example YES:**
```
User: "Where is the memory service implemented?"
Route: ask agent with pattern "backend/services/memory*.py"

User: "Audit the backend structure"
Route: ask agents (parallel, 5x)

User: "Find all duplicate code in services/"
Route: ask agents (parallel, grep patterns)
```

---

### Level 2: External Research?

**Question:** "Is user asking for external knowledge (web, docs, best practices)?"

**Indicators (YES):**
- "best practice", "how to", "documentation", "example", "tutorial"
- "what's the", "tell me about", "explain", "guide"
- Keywords: `research`, `learn`, `find pattern online`, `documentation`

**Indicators (NO):**
- "implement", "create", "build", "fix bug"
- "architecture", "design", "ADR"

**Decision:**
- ✅ YES → **research agent** (web search, external docs)
- ❌ NO → Go to Level 3

**Example YES:**
```
User: "What are best practices for GraphQL subscriptions?"
Route: research agent

User: "Find Apollo Client documentation for subscriptions"
Route: research agent

User: "What's the standard way to implement caching in React?"
Route: research agent
```

---

### Level 3: System Design?

**Question:** "Is user asking to design/architect/plan solution?"

**Indicators (YES):**
- "design", "architect", "architecture", "ADR", "technical decision"
- "how should we structure", "trade-offs", "choose between X and Y"
- Keywords: `plan`, `strategy`, `design decision`, `technical debt plan`

**Indicators (NO):**
- "implement", "code", "create", "fix bug"
- "test", "validate", "documentation"

**Decision:**
- ✅ YES → **architect agent** (single, design specialist)
- ❌ NO → Go to Level 4

**Example YES:**
```
User: "Design a real-time notification system"
Route: architect agent

User: "Should we use WebSocket or GraphQL Subscriptions?"
Route: architect agent

User: "Plan refactoring of memory service"
Route: architect agent
```

---

### Level 4: Implementation?

**Question:** "Is user asking to code/implement/build?"

**Indicators (YES):**
- "implement", "create", "build", "fix", "refactor", "add feature"
- "write", "code", "develop"

**Sub-question 4a: Is it Frontend?**
- "React", "UI", "component", "hook", "Tailwind", "frontend"
- "button", "form", "modal", "display"

**Decision:**
- ✅ YES → **frontend agent** (React/TypeScript specialist)
- ❌ NO → **code agent** (Python/backend specialist)

**Example YES (Frontend):**
```
User: "Create a notification bell icon component"
Route: frontend agent

User: "Add useNotificationSubscription hook"
Route: frontend agent

User: "Build form for user settings"
Route: frontend agent
```

**Example YES (Backend):**
```
User: "Create GraphQL subscription resolver"
Route: code agent

User: "Add notification table to database"
Route: code agent (DB migration)

User: "Fix memory service memory leak"
Route: code agent
```

---

### Level 5: Validation?

**Question:** "Is user asking to test/validate/debug/fix?"

**Indicators (YES):**
- "test", "validate", "debug", "fix bug", "broken", "error", "check"
- "E2E", "integration test", "unit test"
- Keywords: `verify`, `ensure works`, `troubleshoot`

**Indicators (NO):**
- "documentation", "document", "README", "write"

**Decision:**
- ✅ YES → **debug agent(s)** (testing/debugging specialist)
- ❌ NO → Go to Level 6

**Example YES:**
```
User: "Tests are failing, fix them"
Route: debug agents (find issues + fix)

User: "E2E test the notification feature"
Route: debug agent

User: "Backend API is slow, optimize"
Route: debug agent (performance debugging)
```

---

### Level 6: Documentation?

**Question:** "Is user asking to document/write/explain?"

**Indicators (YES):**
- "document", "write", "README", "API docs", "diagram", "explain"
- Keywords: `documentation`, `changelog`, `guide`, `tutorial write`

**Indicators (NO):**
- Handled by previous levels

**Decision:**
- ✅ YES → **docs agent** (technical writing specialist)
- ❌ NO → Unclear, ask CEO (you) to clarify

**Example YES:**
```
User: "Document the notification feature"
Route: docs agent

User: "Create architecture diagram for memory system"
Route: docs agent

User: "Update README with new features"
Route: docs agent
```

---

### Fallback: Infrastructure?

**If Level 1-6 didn't match, check:**

**Question:** "Is user asking about infrastructure/monitoring/DevOps?"

**Indicators:**
- "monitoring", "health check", "costs", "performance", "metrics"
- "infrastructure", "deployment", "scaling", "logs"

**Decision:**
- ✅ YES → **sre agent** (DevOps specialist)
- ❌ NO → Unclear, ask CEO to clarify

**Example:**
```
User: "Check system health"
Route: sre agent

User: "What are our API costs?"
Route: sre agent

User: "PostgreSQL is slow, analyze"
Route: sre agent
```

---

## Part 2: Pattern Matching (Quick Reference)

**Keyword mapping (fastest routing):**

```python
patterns = {
    # ask agent
    "audit": "ask",
    "explore": "ask",
    "where is": "ask",
    "find": "ask",
    "scan": "ask",
    "examine": "ask",
    "code review": "ask",
    "check code": "ask",

    # research agent
    "best practice": "research",
    "best practices": "research",
    "documentation": "research",
    "how to": "research",
    "tutorial": "research",
    "example": "research",
    "guide": "research",

    # architect agent
    "design": "architect",
    "architect": "architect",
    "architecture": "architect",
    "ADR": "architect",
    "trade-off": "architect",
    "technical decision": "architect",
    "plan refactoring": "architect",

    # code agent
    "implement": "code",
    "create": "code",
    "backend": "code",
    "API": "code",
    "database": "code",
    "migration": "code",
    "GraphQL": "code",
    "FastAPI": "code",

    # frontend agent
    "React": "frontend",
    "component": "frontend",
    "UI": "frontend",
    "hook": "frontend",
    "Tailwind": "frontend",
    "button": "frontend",
    "form": "frontend",
    "modal": "frontend",

    # debug agent
    "test": "debug",
    "debug": "debug",
    "E2E": "debug",
    "fix bug": "debug",
    "validate": "debug",
    "broken": "debug",
    "error": "debug",

    # docs agent
    "document": "docs",
    "README": "docs",
    "API doc": "docs",
    "diagram": "docs",
    "changelog": "docs",

    # sre agent
    "monitoring": "sre",
    "health": "sre",
    "infrastructure": "sre",
    "costs": "sre",
    "performance": "sre",
}

def quick_match(user_request: str) -> str:
    """Fastest pattern matching"""
    for keyword, agent in patterns.items():
        if keyword.lower() in user_request.lower():
            return agent
    return None  # No match, use decision tree
```

---

## Part 3: Phase Decision Logic

### Phase 1: UNDERSTANDING (ask agents)

**When to include:**
- ✅ Existing code to understand
- ✅ Refactoring/migration (need baseline)
- ✅ Audit/exploration
- ✅ Finding patterns/duplicates

**When to skip:**
- ❌ Feature completely new from scratch
- ❌ Codebase already explored
- ❌ Quick bug fix

**Parallelization:** 5-10 agents × 20s each

**Example:**
```
User: "Improve memory service"

Phase 1 decision:
- YES (need to understand existing code)

Tasks:
Task(ask, "Scan backend/services/memory*.py")
Task(ask, "Find all *memory* related code")
Task(ask, "Check imports/dependencies")
```

---

### Phase 2: RESEARCH (research agents)

**When to include:**
- ✅ New technology/library
- ✅ Best practices needed
- ✅ External context required
- ✅ Learning phase

**When to skip:**
- ❌ Stack well-known
- ❌ Pattern established
- ❌ Pure refactoring

**Parallelization:** 3-5 agents × 30s each

**Example:**
```
User: "Add real-time notifications"

Phase 2 decision:
- YES (need best practices: GraphQL vs WebSocket vs SSE)

Tasks:
Task(research, "GraphQL Subscriptions best practices 2025")
Task(research, "Apollo Client useSubscription examples")
Task(research, "PostgreSQL performance for subscriptions")
```

---

### Phase 3: ARCHITECTURE (architect agent)

**When to include:**
- ✅ Major design decision
- ✅ Trade-offs evaluation
- ✅ Refactoring scope
- ✅ Integration planning

**When to skip:**
- ❌ Simple bug fix
- ❌ Pattern already known
- ❌ Straightforward implementation

**Parallelization:** Single architect (NOT parallel)

**Example:**
```
User: "Add real-time notifications"

Phase 3 decision:
- YES (need to choose: GraphQL Subscriptions vs WebSocket)

Task:
Task(architect, """
Design notifications system.
Context: GraphQL already used, React frontend
Choose between:
1. GraphQL Subscriptions
2. WebSocket custom
3. SSE (Server-Sent Events)
Evaluate: latency, scalability, complexity, team expertise
Return: decision + reasoning + implementation phases
""")
```

---

### Phase 4: IMPLEMENTATION (code + frontend agents)

**When to include:**
- ✅ Feature coding
- ✅ Bug fixes
- ✅ Refactoring code
- ✅ Database migrations

**When to skip:**
- ❌ Design/architecture only
- ❌ Documentation only
- ❌ Analysis only

**Parallelization:** 3-5 agents × 30-120s each

**Example:**
```
User: "Add real-time notifications"

Phase 4 decision:
- YES (implement after architecture decided)

Tasks (parallel):
Task(code, "Backend: Create GraphQL subscription")
Task(frontend, "Frontend: useNotificationSubscription hook")
Task(code, "Database: Add notifications table migration")
Task(code, "Config: Add notification settings")
```

---

### Phase 5: VALIDATION (debug agents)

**When to include:**
- ✅ Code changed
- ✅ Need quality assurance
- ✅ Tests need fixing
- ✅ Performance validation

**When to skip:**
- ❌ No code changes
- ❌ Documentation only
- ❌ Analysis only

**Parallelization:** 3-5 agents × 30-60s each

**Example:**
```
User: "Add real-time notifications"

Phase 5 decision:
- YES (validate implementation)

Tasks (parallel):
Task(debug, "Unit tests: GraphQL subscription")
Task(debug, "Integration tests: backend + frontend")
Task(debug, "E2E test: create notification → UI update")
```

---

### Phase 6: DOCUMENTATION (docs agent)

**When to include:**
- ✅ Feature user-facing
- ✅ Architecture changed
- ✅ New capability
- ✅ API changes

**When to skip:**
- ❌ Internal refactoring
- ❌ Minor fix
- ❌ Not user-facing

**Parallelization:** Single docs (NOT parallel)

**Example:**
```
User: "Add real-time notifications"

Phase 6 decision:
- YES (user-facing feature, document it)

Task:
Task(docs, """
Document real-time notifications feature.
Include:
- Overview paragraph
- Architecture diagram (Mermaid)
- API documentation (subscription + fields)
- Example usage (backend + frontend)
- Configuration options
- Troubleshooting
""")
```

---

## Part 4: Parallel vs Sequential Logic

### Rule 1: Identify Dependencies

```python
def has_dependency(task_a, task_b) -> bool:
    """Does A depend on output of B?"""
    if task_a.needs_input_from(task_b):
        return True
    return False

# Example:
# Task A: Architecture design
# Task B: Implementation (needs Task A design)
# → has_dependency(B, A) = True → Sequential (B after A)

# Example:
# Task A: Scan services/
# Task B: Scan api/
# → has_dependency(A, B) = False → Parallel (simultaneous)
```

### Rule 2: Parallel When Independent

```
Independent tasks = can run at same time

✅ PARALLEL:
Phase 1: ask × 5 agents
- Agent 1: Scan services/[a-d]*.py
- Agent 2: Scan services/[e-h]*.py
- Agent 3: Scan services/[i-l]*.py
- Agent 4: Scan api/
- Agent 5: Find duplicates

→ Total time: max(20s, 20s, 20s, 20s, 20s) = 20s

❌ SEQUENTIAL:
Phase 1: Understanding
Phase 2: Research (depends on Phase 1)
Phase 3: Architecture (depends on Phase 1 + 2)
→ Total time: 20s + 30s + 60s = 110s
```

### Rule 3: Skip Dependent Phase if Not Needed

```python
# Example:
Phase 1: Understanding
result = Task(ask, "Existing notification code?")

# CEO decision based on result
if result['has_no_code']:
    # Must do Phase 2: Research (dependency)
    research = Task(research, "GraphQL Subscriptions")
else:
    # Already have code, skip Phase 2
    # Go directly to Phase 3: Architecture

# Example 2:
Phase 2: Research
research = Task(research, "...")

# CEO decision
if research['complex_decision']:
    # Need Phase 3: Architecture
    architecture = Task(architect, f"Context: {research}")
else:
    # Simple pattern, skip Phase 3
    # Go directly to Phase 4: Implementation
```

---

## Part 5: Advanced Patterns

### Pattern: Cascading Decision

**When Phase N results determine Phase N+1 tasks:**

```python
# Phase 1: Understanding
existing = Task(ask, "Check if notifications exist?")

# CEO evaluates result
if existing['found_graphql_subscriptions']:
    print("✅ GraphQL Subscriptions already used")
    # Phase 2: SKIP research
    # Phase 3: Minimal architecture (extend existing)
elif existing['found_websockets']:
    print("⚠️ WebSocket implementation exists")
    # Phase 2: Research (compare WebSocket vs GraphQL)
    research = Task(research, "GraphQL vs WebSocket comparison")
else:
    print("❌ No notification system")
    # Phase 2: Full research (all options)
    research = Task(research, "GraphQL Subscriptions best practices")
    research += Task(research, "WebSocket implementation guide")

# Phase 3: Architecture (informed by decision)
architecture = Task(architect, f"""
Design based on:
- Existing: {existing}
- Research: {research}
""")
```

### Pattern: Adaptive Scope

**Number of agents adapts to task complexity:**

```python
def estimate_agents(scope_size: int) -> int:
    """How many parallel agents needed?"""

    if scope_size < 5:
        return 1  # Single agent
    elif scope_size < 20:
        return 2  # Pair
    elif scope_size < 50:
        return 3  # Small team
    elif scope_size < 100:
        return 5  # Team
    else:
        return 10  # Large team

# Example: Scan 100 files
files = glob.glob("backend/**/*.py")  # 100 files
agents_count = estimate_agents(len(files))  # 10 agents

for i in range(agents_count):
    start_idx = i * (len(files) // agents_count)
    end_idx = (i + 1) * (len(files) // agents_count)
    batch = files[start_idx:end_idx]

    Task(ask, f"""
    Scan these files: {batch}
    - Find classes
    - List public methods
    """)
```

### Pattern: Error Recovery

**If agent timeout/fails, split scope:**

```python
def robust_ask(pattern: str, timeout: int = 20) -> Dict:
    """Ask with fallback on timeout"""

    try:
        result = Task(ask, f"Scan {pattern}", timeout=timeout)
        if result.get('timeout'):
            # Timeout occurred, reduce scope
            return split_scope_and_retry(pattern, timeout)
        return result
    except Exception as e:
        # Critical error
        log(f"Error: {e}")
        return {"error": str(e), "status": "failed"}

def split_scope_and_retry(pattern: str, timeout: int) -> Dict:
    """Split pattern into smaller pieces"""

    # Example: "backend/**/*.py" → ["backend/services/", "backend/api/", ...]
    sub_patterns = split_glob_pattern(pattern)

    results = []
    for sub in sub_patterns:
        result = Task(ask, f"Scan {sub}", timeout=timeout-5)
        if not result.get('timeout'):
            results.append(result)

    # Aggregate partial results
    return aggregate_results(results)
```

---

## Part 6: Decision Checklist

**Before routing (validate your decision):**

```python
checklist = {
    "Intent Decoded": False,           # Understand user GOAL
    "Agent Selected": False,           # Which agent(s)?
    "Dependencies Identified": False,  # Sequential or parallel?
    "Phases Determined": False,        # Which phases needed?
    "Scope Clear": False,              # Exact boundaries?
    "Deadline Set": False,             # 20-120s?
    "Parallelization Planned": False,  # How many agents?
    "Aggregation Strategy": False,     # How combine results?
}

def validate_decision(decision: Dict) -> bool:
    """All checkboxes checked?"""
    return all(decision.values())

# Usage:
decision = {
    "Intent Decoded": "Add notifications",
    "Agent Selected": ["ask", "research", "architect", "code", "frontend", "debug", "docs"],
    "Dependencies Identified": "Cascading (Phase 1→2→3→4→5→6)",
    "Phases Determined": "All 6 phases",
    "Scope Clear": "Real-time notifications system",
    "Deadline Set": "Phase 1-2: 30s, Phase 3: 60s, Phase 4: 120s, Phase 5: 60s, Phase 6: 60s",
    "Parallelization Planned": "Phase 1: 5 ask, Phase 2: 3 research, Phase 4: 4 code/frontend, Phase 5: 3 debug",
    "Aggregation Strategy": "CEO aggregates each phase, validates before next phase",
}

if validate_decision(decision):
    print("✅ Decision ready")
else:
    print("❌ Missing elements, review")
```

---

## Part 7: When to Skip What

### Skip Decisions (Quick Reference)

```markdown
SKIP Phase 1 when:
- Feature entirely new (nothing to explore)
- Codebase explored recently
- Time-critical (no exploration time)

SKIP Phase 2 when:
- Technology stack well-known
- Pattern already established
- Internal refactoring only

SKIP Phase 3 when:
- Bug fix (no major design)
- Straightforward implementation
- Pattern already follows standard

SKIP Phase 4 when:
- Architecture/design only
- Documentation only
- Analysis only

SKIP Phase 5 when:
- No code changes
- Change too small (typo fix)
- Already thoroughly tested

SKIP Phase 6 when:
- Internal refactoring
- Minor fix
- Not user-facing
```

---

## Part 8: Examples

### Example 1: Quick Audit

**User:** "Is the backend well-organized?"

**Decision:**
```
Intent: Code audit + quality report
Decision Tree: Level 1 → ask (YES)
Phase 1: Understanding (YES) → scan backend
Phase 2-4: Skip (analysis only)
Phase 5: Skip (no code changes)
Phase 6: YES (documentation/report)

Routing:
Phase 1: Task(ask, "Scan backend structure") ×3 agents
Phase 6: Task(docs, "Generate audit report")
```

---

### Example 2: New Feature

**User:** "Add real-time notifications"

**Decision:**
```
Intent: Implement new feature
Decision Tree: Level 4 → implement
Phase 1: YES (understand existing patterns)
Phase 2: YES (research best practices)
Phase 3: YES (design architecture)
Phase 4: YES (implement code)
Phase 5: YES (validate tests)
Phase 6: YES (document for users)

Routing:
Phase 1: Task(ask, "Find notification patterns") ×3 agents
Phase 2: Task(research, "GraphQL Subscriptions") ×3 agents
Phase 3: Task(architect, "Design notifications system")
Phase 4: Task(code, "Backend subscription") + Task(frontend, "React hook") + Task(code, "DB migration")
Phase 5: Task(debug, "Unit tests") + Task(debug, "E2E tests")
Phase 6: Task(docs, "Document notifications feature")
```

---

### Example 3: Bug Fix

**User:** "API endpoint returns 500 error"

**Decision:**
```
Intent: Debug + fix bug
Decision Tree: Level 5 → debug
Phase 1: SKIP (bug is known)
Phase 2-3: SKIP (no research/design needed)
Phase 4: YES (fix code)
Phase 5: YES (validate fix)
Phase 6: NO (internal bug fix)

Routing:
Phase 4: Task(debug, "Find 500 error root cause")
Phase 5: Task(debug, "Write test + validate fix")
```

---

## Part 9: Quick Reference Card

**Use this when speed matters:**

```
User says:          → Agent(s)           → Phases
─────────────────────────────────────────────────────
"audit backend"     → ask ×5             → 1, 6
"find duplicate"    → ask ×3             → 1
"how to X?"         → research           → 2
"design Y"          → architect          → 3
"implement Z"       → code/frontend      → 1,2,3,4,5,6
"React component"   → frontend           → 4,5
"test/debug"        → debug ×3           → 5
"document"          → docs               → 6
"slow query"        → debug + code       → 5, 4
"check health"      → sre                → (no phases)
```

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System - Decision Making
**Maintenance:** Review monthly for new patterns
