---
name: "Agent Orchestration"
description: "When to invoke which agent (ask/research/architect/code/frontend/debug/docs/sre), pipeline phases"
categories: ["agents", "workflow", "orchestration"]
tags: ["Task", "agents", "pipeline", "ask", "research", "code", "frontend", "debug"]
version: "1.0.0"
enabled: true
---

## Overview

8 specialized agents available for orchestrating work in parallel:

1. **ask** - Exploration codebase interne (read-only)
2. **research** - Recherche externe (exa, fetch, context7)
3. **architect** - Design architecture, ADR, patterns
4. **code** - Implémentation backend/générale
5. **frontend** - Implémentation React/TypeScript
6. **debug** - Tests, validation, debugging
7. **docs** - Documentation technique
8. **sre** - Infrastructure, monitoring

## Pipeline Phases (Sequential)

```
PHASE 1: UNDERSTANDING (ask × N)
    ↓ MOI agrège
PHASE 2: RESEARCH (research × N)
    ↓ MOI agrège
PHASE 3: ARCHITECTURE (architect × 1-3)
    ↓ MOI valide
PHASE 4: IMPLEMENTATION (code/frontend × N)
    ↓ MOI agrège
PHASE 5: VALIDATION (debug × N)
    ↓ MOI vérifie
PHASE 6: DOCUMENTATION (docs × 1)
```

## When to use

- **Deciding which agent to invoke** for a specific task
- **Understanding agent capabilities and boundaries**
- **Planning pipeline phase selection** (Understanding → Research → Architecture → Implementation → Validation → Documentation)
- **Parallelizing work** (agents within phase run in parallel)
- **Orchestrating complex features** (full-stack work)

## Key Rules

- Agents **within a phase** run in parallel (×10-20 simultaneous)
- Phases are **sequential** (strict order)
- **You (MOI) alone** invoke agents - agents never call each other
- Each agent has **clear scope** (no overlaps)
- **Partial results OK** - pragmatic CEO approach
