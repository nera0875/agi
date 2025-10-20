---
name: "AGI Memory Management"
description: "L1/L2/L3 memory architecture, consolidation workflows, neurotransmitter systems (LTP/LTD)"
categories: ["agi", "memory", "architecture", "system"]
tags: ["L1", "L2", "L3", "Redis", "PostgreSQL", "Neo4j", "consolidation", "LTP", "LTD", "neurotransmitters", "working-memory"]
version: "1.0.0"
enabled: true
---

## Overview

**Memory Management System** for AGI: Three-tier architecture with Redis (L1 working memory), PostgreSQL (L2 short-term), and Neo4j (L3 long-term graph knowledge).

Critical for autonomous learning: consolidation workflows move information from short-term to long-term memory, applying neurotransmitter rules (LTP/LTD) for selective retention.

## Core Components

### L1 Memory (Redis - Working Memory)
- Fast, ephemeral storage (seconds to minutes)
- Current task context, active tokens, conversation state
- Immediate access for decision-making
- Auto-expires after inactivity

### L2 Memory (PostgreSQL - Short-Term)
- Medium-term storage (hours to days)
- Recent decisions, embeddings, conversation history
- Structured rows, queryable schemas
- Consolidation source: L1 → L2 → L3

### L3 Memory (Neo4j - Long-Term Graph)
- Permanent knowledge graph (months, years)
- Conceptual relationships, learned patterns
- Semantic connections between decisions
- Slow to query but rich relationship data

### Neurotransmitter System
- **LTP (Long-Term Potentiation):** Strengthen important memories (frequent use → stored in L3)
- **LTD (Long-Term Depression):** Weaken irrelevant memories (forgotten → deleted from L3)
- **Triggers:** Access patterns, relevance decay, explicit marking

## When to Use This Skill

### Use this skill when:
- Working with memory storage/retrieval patterns
- Understanding consolidation workflows
- Implementing neurotransmitter logic (LTP/LTD triggers)
- Designing memory-dependent features
- Debugging memory consistency issues
- Optimizing memory layer performance

### DON'T use this skill for:
- General AI/ML concepts
- Database administration (use SRE agent)
- Feature implementation (use Code agent)
- Performance tuning (use PerformanceOptimizer agent)

## Related Files

- `backend/services/memory_service.py` - Memory operations (get, store, query)
- `backend/services/neurotransmitter_system.py` - LTP/LTD rules
- `cortex/consolidation.py` - L1→L2→L3 consolidation workflow
- `backend/migrations/` - Memory schema history
- `docs/memory-architecture.md` - Detailed memory design

## Key Concepts

### Consolidation Pipeline
```
L1 (Redis) → [Age > 5min] → L2 (PostgreSQL) → [Relevance > threshold] → L3 (Neo4j)
```

### Decision Making with Memory
1. Query L1 for immediate context (fast)
2. If not in L1, query L2 for recent history (medium)
3. If pattern needed, query L3 for conceptual knowledge (slow)

### Neurotransmitter Application
- Memory accessed frequently? Strengthen with LTP
- Memory aged without use? Apply LTD (decay)
- Memory marked important? Force into L3
- Memory marked irrelevant? Trigger LTD (deletion)

## Implementation Patterns

### Store to Memory
- Call `memory_service.store()` with metadata
- Auto-expires from L1, moves to L2 after duration
- Consolidation job moves L2→L3 if relevant

### Query Memory
- Use `memory_service.query()` with filters
- Searches L1 first (fast), then L2 if needed
- Never queries L3 for speed (too slow)

### Apply Neurotransmitters
- LTP: `neurotransmitter_system.strengthen()`
- LTD: `neurotransmitter_system.weaken()`
- Triggers consolidation or deletion

## Troubleshooting

**Memory not persisting?**
- Check L2 consolidation job running
- Verify neurotransmitter rules allow storage

**Queries too slow?**
- L1 cache miss? Data not yet consolidated
- Use timeouts, don't wait for L3 queries

**Memory bloat?**
- LTD not triggering? Check neurotransmitter decay rules
- Old data stuck in L1? Run manual consolidation

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Critical System:** Yes (AGI core)
