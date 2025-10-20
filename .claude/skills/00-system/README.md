# System Skills Collection

Core system and management skills for AGI autonomous operation.

## Skills Overview

### 1. AGI Memory Management (`agi-memory-management/`)

**Three-tier memory architecture (L1/L2/L3) with neurotransmitter system**

- **Files:**
  - `README.md` - Overview and when to use
  - `instructions.md` - Detailed implementation guide

- **Key Topics:**
  - L1 (Redis) working memory: ephemeral, fast
  - L2 (PostgreSQL) short-term: recent context
  - L3 (Neo4j) long-term: knowledge graph
  - Consolidation workflow: L1→L2→L3 pipeline
  - Neurotransmitter system: LTP (strengthen), LTD (weaken)
  - Memory operations: store, query, consolidate
  - Performance optimization: timeouts, caching

- **Use when:**
  - Understanding memory storage patterns
  - Implementing consolidation workflows
  - Applying LTP/LTD rules
  - Debugging memory consistency
  - Designing memory-dependent features

- **Total content:** ~500 lines
- **Status:** Complete and documented

---

### 2. CEO Mindset - Parallel Delegation (`ceo-mindset/`)

**Entrepreneur mindset: delegate 10-50 agents in parallel, ultra-precise prompts**

- **Files:**
  - `README.md` - Overview and patterns
  - `instructions.md` - Detailed delegation strategies

- **Key Topics:**
  - From solo worker to CEO (20x faster)
  - Decomposition strategy (divide and conquer)
  - Ultra-precise prompts (clarity for agents)
  - Scope isolation (no overlap)
  - Deadline management (time pressure)
  - Result aggregation (combine N→1)
  - 6-phase workflow (Understanding→Research→Architecture→Implementation→Validation→Documentation)
  - Agent types and when to use each
  - Anti-patterns to avoid
  - Practical examples (code audit, features, infra checks)

- **Use when:**
  - Complex tasks with independent steps
  - Codebase exploration (50+ files)
  - Multi-phase implementations
  - Need rapid iteration
  - Parallelizable work (5+ tasks)

- **Total content:** ~1,100 lines
- **Status:** Complete and documented

---

## Quick Reference

### When to Use Which Skill?

| Situation | Skill | Why |
|-----------|-------|-----|
| "How does memory work?" | AGI Memory Management | Core memory system |
| "Design memory consolidation" | AGI Memory Management | L1→L2→L3 workflow |
| "Store decision in memory" | AGI Memory Management | Memory service API |
| "Large task, need speed" | CEO Mindset | Parallel delegation |
| "Need to audit 50 files" | CEO Mindset | Decompose + agents |
| "Implement feature fast" | CEO Mindset | 6-phase workflow |

---

## Directory Structure

```
00-system/
├── README.md (this file)
├── agi-memory-management/
│   ├── README.md
│   └── instructions.md
└── ceo-mindset/
    ├── README.md
    └── instructions.md
```

---

## Integration Points

### With Claude Code CLI

System skills inform how Claude Code (you) work:

1. **AGI Memory Management** - WHAT to remember
   - Use `memory()` tool to store important decisions
   - Leverage L1/L2/L3 for context
   - Apply neurotransmitters to strengthen/weaken

2. **CEO Mindset** - HOW to work efficiently
   - Decompose large tasks
   - Use Task() to delegate to agents
   - Aggregate results intelligently

### With Other Skills

- **Project Structure** (04-architecture) - WHERE code goes
- **Workflow Implementation** (06-workflow) - DETAILED execution
- **Agent Collaboration** (06-workflow) - HOW agents coordinate
- **Architecture Thinking** (04-architecture) - WHEN to use memory/agents

---

## Key Concepts Summary

### Memory System

```
L1 (Redis)
  ↓ [5 min age]
L2 (PostgreSQL)
  ↓ [1 hour + relevance]
L3 (Neo4j)

Neurotransmitters: LTP (strengthen), LTD (weaken)
```

### CEO Workflow

```
1. UNDERSTANDING (parallel) - ask agents
2. RESEARCH (parallel) - research agents
3. ARCHITECTURE (single) - architect agent
4. IMPLEMENTATION (parallel) - code/frontend agents
5. VALIDATION (parallel) - debug agents
6. DOCUMENTATION (single) - docs agent
```

---

## Performance Metrics

### Memory System
- L1 query: <1ms (Redis)
- L2 query: 1-10ms (PostgreSQL)
- L3 query: 100-1000ms (Neo4j)
- Consolidation: 5min interval

### CEO Workflow
- Solo approach: 5,000-10,000 tokens, 3-5 minutes
- CEO approach: 3,400 tokens, 1-2 minutes
- Speedup: 3-5x faster, 66% token savings

---

## Related Documentation

- `backend/services/memory_service.py` - Memory operations implementation
- `backend/services/neurotransmitter_system.py` - LTP/LTD implementation
- `cortex/consolidation.py` - Consolidation workflow
- `docs/memory-architecture.md` - Detailed memory design

---

## Maintenance

**Review:** Quarterly

**Update when:**
- New memory layer added (L4+)
- Consolidation algorithm changes
- New agent types introduced
- CEO workflow patterns evolve

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Category:** Core System Skills
**Audience:** AGI Core, Claude Code, Agents
**Status:** Production Ready
