---
name: "Decision Framework"
description: "Quand invoquer quel agent? Decision tree rapide pour routing optimal des tâches."
categories: ["system", "orchestration", "decision"]
tags: ["agents", "routing", "decision-tree", "pattern-matching", "workflow"]
version: "1.0.0"
enabled: true
---

## Overview

Framework décisionnel pour router tâches vers agents appropriés. Decision tree binaire optimisé + pattern matching rules + logique parallélisation.

**Core insight:** Bonne décision d'agent = 10x plus rapide + meilleur résultat.

## When to Use This Skill

**Use decision-framework when:**
- User demande quelque chose
- Besoin identifier quel agent invoquer
- Choix entre multiple agents (ask vs research?)
- Question: parallélisable ou séquentiel?
- Question: phase 1, 2, 3, ... ou skip?

**Exemple triggers:**
```
User: "Audit le backend"
→ Use decision-framework
→ Route → ask agents (Phase 1) + docs agent (Phase 6)

User: "Implémente notifications temps réel"
→ Use decision-framework
→ Route → ask (Phase 1) + research (Phase 2) + architect (Phase 3) + code+frontend (Phase 4) + debug (Phase 5) + docs (Phase 6)

User: "C'est quoi les meilleures pratiques GraphQL?"
→ Use decision-framework
→ Route → research agent ONLY
```

## Quick Pattern Matching

**Pattern → Agent mapping (ultra-rapide):**

| Pattern | Agent | Reasoning |
|---------|-------|-----------|
| "où est", "audit", "explore", "scan", "check code" | **ask** | Codebase local = read-only exploration |
| "meilleure pratique", "doc", "comment marche", "exemple", "tutorial" | **research** | Externe = web search |
| "architecturer", "design", "ADR", "tech choice", "tradeoff" | **architect** | System design specialist |
| "implémente", "coder", "backend", "API", "DB migration" | **code** | Python/FastAPI/GraphQL |
| "UI", "frontend", "React", "component", "hook" | **frontend** | React/TypeScript specialist |
| "test", "debug", "fix bug", "validation", "E2E" | **debug** | Quality assurance |
| "documentation", "README", "diagram", "API doc" | **docs** | Technical writing |
| "monitoring", "health", "infrastructure", "cost", "logs" | **sre** | DevOps/infrastructure |

## Decision Tree (Binary)

```
User Request
    ↓
[Is it CODE EXPLORATION?] (read-only codebase)
├─ YES → ask agent(s) ✅
└─ NO
    ↓
[Is it EXTERNAL RESEARCH?] (web, docs, best practices)
├─ YES → research agent(s) ✅
└─ NO
    ↓
[Is it SYSTEM DESIGN?] (architecture, trade-offs, ADR)
├─ YES → architect agent ✅
└─ NO
    ↓
[Is it IMPLEMENTATION?] (coding features)
├─ YES
│   ↓
│   [Is it FRONTEND?] (React/UI)
│   ├─ YES → frontend agent ✅
│   └─ NO → code agent ✅
└─ NO
    ↓
[Is it VALIDATION?] (testing, debugging, fixes)
├─ YES → debug agent(s) ✅
└─ NO
    ↓
[Is it DOCUMENTATION?] (README, API docs, diagrams)
├─ YES → docs agent ✅
└─ NO
    ↓
[Is it INFRASTRUCTURE?] (monitoring, health, DevOps)
├─ YES → sre agent ✅
└─ NO
    ↓
❓ UNCLEAR → Ask CEO (you) to clarify
```

## Phase Decision Logic

**6 phases workflow (skip when not needed):**

```
Phase 1: UNDERSTANDING (Parallel ask)
├─ Skip if: feature from scratch, codebase unknown
├─ Use if: existing code to understand, refactoring, migration
└─ Duration: 1-2 min

Phase 2: RESEARCH (Parallel research)
├─ Skip if: pattern known, stack familiar
├─ Use if: new technology, best practices needed, external context
└─ Duration: 2-3 min

Phase 3: ARCHITECTURE (Single architect)
├─ Skip if: simple change, bug fix, pattern established
├─ Use if: major design, trade-offs needed, refactoring scope
└─ Duration: 1-2 min

Phase 4: IMPLEMENTATION (Parallel code+frontend)
├─ Skip if: design-only request
├─ Use if: build feature, fix bug, implement
└─ Duration: 2-5 min

Phase 5: VALIDATION (Parallel debug)
├─ Skip if: documentation-only, no code changes
├─ Use if: code changed, need quality assurance
└─ Duration: 2-3 min

Phase 6: DOCUMENTATION (Single docs)
├─ Skip if: internal change, minor update
├─ Use if: feature user-facing, architecture changed, new capability
└─ Duration: 1-2 min
```

## Parallel vs Sequential Logic

**Parallel = independent tasks (can run same time):**
```python
✅ Parallel:
Task(ask, "Scan services/")
Task(ask, "Scan api/")
Task(ask, "Scan routes/")
→ All 3 run simultaneously = 20s total

❌ Sequential (if dependent):
result1 = Task(architect, "Design system")
# Needs result1
result2 = Task(code, "Implement: {architecture from result1}")
→ Must wait design first = sequential
```

**Rule:** If task A needs output of task B → Sequential. Otherwise → Parallel.

## Advanced Patterns

### Pattern 1: Cascading Decision

**When result of Phase N affects decision for Phase N+1:**

```python
# Phase 1: Understanding
existing_code = Task(ask, "Check if notification code exists?")

# CEO decision based on result
if existing_code['has_subscriptions']:
    # Already have GraphQL Subscriptions
    # SKIP Phase 2 research
    research = None
else:
    # No subscriptions, need research
    research = Task(research, "GraphQL Subscriptions best practices")

# Phase 3: Architecture uses findings
architecture = Task(architect, f"Design based on existing={existing_code}, research={research}")
```

### Pattern 2: Adaptive Parallelization

**Number of parallel tasks depends on scope:**

```python
files_count = 100
agents_count = max(5, files_count // 20)  # 1 agent per 20 files

# Dynamically create tasks
for i in range(agents_count):
    start = chr(97 + i)  # a, b, c, ...
    end = chr(97 + i + 1)
    pattern = f"backend/services/[{start}-{end}]*.py"
    Task(ask, f"Scan {pattern}")
```

### Pattern 3: Error Recovery

**If agent timeout/fails, fallback to smaller scope:**

```python
try:
    result = Task(ask, "Scan backend/", timeout=20)
    if result.get("timeout"):
        # Timeout, split scope
        result1 = Task(ask, "Scan backend/services/", timeout=15)
        result2 = Task(ask, "Scan backend/api/", timeout=15)
        result = merge(result1, result2)
except Exception as e:
    # Critical error, log and skip
    log(f"Agent failed: {e}")
```

## Checklist: Before Routing

**For every request:**
- [ ] Decoded user intention? (understand goal, not just keywords)
- [ ] Pattern matched to primary agent?
- [ ] Dependencies identified? (sequential or parallel?)
- [ ] Phase(s) determined? (which phases needed?)
- [ ] Scope clear? (exact boundaries)
- [ ] Deadline set? (20-120s depending on phase)
- [ ] Aggregation strategy planned? (how to combine results?)

## When to Skip Phases

### Skip Phase 1 (Understanding) when:
- Feature completely new from scratch
- Codebase already explored recently
- Time-critical feature

### Skip Phase 2 (Research) when:
- Technology stack well-known
- Pattern already established
- Internal-only feature

### Skip Phase 3 (Architecture) when:
- Simple bug fix
- Pattern already follows standard
- Minimal design needed

### Skip Phase 4 (Implementation) when:
- Architecture/design only request
- Documentation-only task
- Analysis/report only

### Skip Phase 5 (Validation) when:
- No code changes made
- Change too small to test (typo fix)
- Already thoroughly tested

### Skip Phase 6 (Documentation) when:
- Internal refactoring
- Minor fix
- Feature not user-facing

## Related Skills

- **CEO Mindset** - How to delegate 10-50 agents in parallel
- **Agent Collaboration** - How agents work together
- **Workflow Implementation** - How to execute decided workflow
- **Workflow Bootstrap** - Initialization + think() loading

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** System - Orchestration
**Maintenance:** Review quarterly for new patterns
