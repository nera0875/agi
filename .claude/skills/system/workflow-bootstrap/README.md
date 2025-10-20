---
name: "Workflow Bootstrap"
description: "think() → agents → memory() workflow, L1/L2/L3 cascade"
categories: ["workflow", "bootstrap", "memory"]
tags: ["think", "memory", "database", "control", "MCP", "agi-tools"]
version: "1.0.0"
enabled: true
---

## Overview

**Workflow Absolu** - Mandatory execution flow:

```
1. think("bootstrap") ← Load context from L1/L2/L3
2. Analyze results (L1=Redis, L2=PostgreSQL, L3=Neo4j)
3. Task(agents) ← Invoke 10-50 agents in parallel
4. Aggregate results JSON
5. memory(action="store") ← Persist important findings
6. Hooks capture automatically (background)
```

## When to use

- **Start of every conversation** - bootstrap context
- **Before answering user question** - ensure L1/L2/L3 loaded
- **After significant task completion** - persist to memory
- **Making decisions** - leverage accumulated knowledge

## Tools Reference

**think() - Bootstrap & Context Loading**
- `think("bootstrap")` - Full cascade L1→L2→L3
- `think("contexte [subject]")` - Load specific topic
- Returns: {memory: "JSON context from cascades"}

**memory() - Persistent Storage**
- `memory(action="store", data={...})` - Save to L1/L2
- `memory(action="retrieve", query="...")` - Query memories
- `memory(action="consolidate")` - Trigger consolidation

**database() - Direct Data Access**
- `database(query="SELECT ...")` - PostgreSQL queries
- `database(action="update", ...)` - Mutations
- Returns: Raw data

**Task() - Agent Orchestration**
- `Task(agent_type, prompt)` - Invoke agent
- Run 10-50 in parallel for speed
- Agents use isolated Haiku conversations (cheap tokens)

## Key Rules

- **Phases are sequential** - Think → Task agents → Memory
- **Agents within phase run parallel** - 10-50 simultaneous
- **Partial results OK** - Pragmatic CEO approach
- **Agents have deadlines** - DEADLINE: Xs in prompt
- **Never delegate to yourself** - Always use Task() for real work

## L1/L2/L3 Cascade

**L1 (Redis)** - Hot cache, fast retrieval
- Recent interactions
- Current session state

**L2 (PostgreSQL)** - Persistent structured data
- Memories with metadata
- Relationships
- Full-text search

**L3 (Neo4j)** - Knowledge graph
- Entity connections
- Semantic relationships
- Pattern detection
