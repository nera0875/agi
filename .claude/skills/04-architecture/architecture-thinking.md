---
title: "Architecture Thinking Framework"
description: "System design patterns, layer separation, and architectural decisions for AGI memory system"
category: "Architecture"
level: "Advanced"
tags: ["design", "layers", "patterns", "system-design", "memory-system"]
---

# Architecture Thinking Framework

## Overview
Effective architecture balances multiple concerns: scalability, maintainability, performance, and flexibility. This skill provides frameworks for designing systems systematically.

## Core Domains of Expertise

### 1. Layered Architecture

**Backend Python (FastAPI):**
```
┌─────────────────────────┐
│   API Layer             │  Routes, GraphQL schema
│   (routes, api/)        │  - Input validation
│                         │  - Request routing
├─────────────────────────┤
│   Service Layer         │  Business logic
│   (services/)           │  - Use cases
│                         │  - Orchestration
├─────────────────────────┤
│   Data Access Layer     │  Database queries
│   (models, schemas/)    │  - ORM mapping
│                         │  - Query optimization
├─────────────────────────┤
│   External Services     │  APIs, embeddings
│   (agents, utils/)      │  - LangGraph agents
│                         │  - Voyage embeddings
└─────────────────────────┘
```

**Separation Benefits:**
- Routes don't contain business logic
- Services don't execute queries directly
- Models separate from validation
- Each layer testable independently

**Frontend React:**
```
┌─────────────────────────┐
│   Pages/Containers      │  Route handlers
│   (pages/)              │  - Business orchestration
│                         │  - State management
├─────────────────────────┤
│   Smart Components      │  Data fetching
│   (components/)         │  - Apollo hooks
│                         │  - State updates
├─────────────────────────┤
│   Presentational        │  Rendering only
│   (ui/, shadcn/)        │  - No logic
│                         │  - Reusable
├─────────────────────────┤
│   Custom Hooks          │  Logic extraction
│   (hooks/)              │  - Data fetching
│                         │  - State mgmt
└─────────────────────────┘
```

### 2. System Design Patterns

**Memory System (L0-L5):**
```
L0 (Working Memory)     → In-process cache
                          - Current thinking context
                          - Fast access

L1 (Short-term)         → Redis
                          - Session state
                          - Temporary data
                          - TTL: hours/days

L2 (Long-term)          → PostgreSQL
                          - Conversation history
                          - Entity relations
                          - Full-text search

L3-L5 (Deep Memory)     → Neo4j + Embeddings
                          - Semantic relationships
                          - Graph queries
                          - Vector similarity
```

**Agent System:**
```
┌──────────────────┐
│  Main AGI (Sonnet)
│  (thinking entity)
└────────┬─────────┘
         │ coordinates
         v
┌──────────────────────────┐
│ Orchestrator            │
│ (task decomposition)     │
└─────────┬────────────────┘
          │
    ┌─────┼─────┐
    │     │     │
    v     v     v
  Ask  Code  Debug  ... (Haiku executors)
  (parallel execution)
```

**Data Flow:**
```
User Input
    ↓
think("context: memory")  ← Retrieve from L1/L2/L3
    ↓
process_with_context     ← Combine with current state
    ↓
generate_response
    ↓
memory(action="store")   ← Save for future
    ↓ (background)
consolidation_async     ← Optimize memory layers
```

### 3. Design Patterns

**Backend Patterns:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| Repository | Abstract data access | `MemoryService` wraps `MemoryModel` |
| Factory | Create complex objects | Agent creation (code, debug, ask) |
| Singleton | Shared resource | Database connections, Redis client |
| Strategy | Swap implementations | Embedding providers (Voyage, Cohere) |
| Observer | Event handling | Neurotransmitter system triggers |
| Decorator | Add behavior | Async wrappers, logging, caching |

**Frontend Patterns:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| Compound | Related components | `Table` + `TableHeader` + `TableRow` |
| Render Props | Logic extraction | TanStack Table column definitions |
| Custom Hooks | Reusable logic | `useMemory()`, `useGraphQuery()` |
| Provider | Context sharing | Apollo Client provider |
| Higher-Order | Component wrapping | withErrorBoundary, withAuth |
| Container | Smart wrappers | Page containers fetching data |

### 4. Anti-Patterns to Avoid

**Backend Anti-Patterns:**

❌ **God Objects** (>500 lines):
```python
# BAD: Everything in one class
class Memory:
    def store()
    def retrieve()
    def consolidate()
    def search()
    def rank()
    def cluster()
    # ... 50 more methods

# GOOD: Separated concerns
class MemoryService:      # Orchestration
    def store()
    def retrieve()

class ConsolidationService:  # Specific task
    def consolidate()

class SearchService:         # Specific task
    def search()
    def rank()
```

❌ **Circular Dependencies:**
```python
# BAD
# services/memory_service.py imports from services/graph_service.py
# services/graph_service.py imports from services/memory_service.py
# → Circular import error

# GOOD
# Create mediator or extract common logic
services/
├── memory_service.py  (no imports from other services)
├── graph_service.py   (no imports from other services)
└── orchestrator.py    (imports both, coordinates)
```

❌ **N+1 Queries:**
```python
# BAD
memories = Memory.query.all()  # Query 1
for memory in memories:
    entity = Entity.query.get(memory.entity_id)  # Query N
    print(entity.name)

# GOOD: Use joins
memories = (
    Memory.query
    .options(joinedload(Memory.entity))
    .all()
)  # Single query with JOIN
```

❌ **Tight Coupling:**
```python
# BAD: Frontend knows DB schema
const query = gql`
  query {
    memory {
      id
      raw_vector_data_internal_field_
      neurotransmitter_level_percentage
    }
  }
`
# → Any DB change breaks UI

# GOOD: Use GraphQL contracts
const query = gql`
  query {
    memory {
      id
      summary
      confidence
    }
  }
`
# → DB can change, API contract stays
```

## Architectural Thinking Process

### Step 1: Understand Problem
- What are we solving?
- Who are the users?
- What constraints exist? (performance, scale, budget)

### Step 2: Identify Concerns
- What are the different aspects? (compute, storage, sync)
- Which are critical? (vs. nice-to-have)
- What might fail? (database, network, concurrency)

### Step 3: Design Layers
- Input: How does data enter?
- Processing: How is it transformed?
- Storage: Where does it live?
- Output: How does it leave?

### Step 4: Choose Patterns
- What proven patterns exist?
- Which fit our constraints?
- What trade-offs do they introduce?

### Step 5: Document Decisions
- Why this architecture?
- What alternatives considered?
- What are consequences?

## Complex System Example: Memory Consolidation

**Problem:** Move long-term memories to Neo4j, cluster semantically

**Design Thinking:**

1. **Layers:**
   - API: Endpoint to trigger consolidation
   - Service: Orchestrate workflow
   - Data Access: Query PostgreSQL, write Neo4j
   - Utils: Clustering, embedding

2. **Concerns:**
   - Performance: Consolidate async, batch operations
   - Correctness: Atomic moves, no data loss
   - Scalability: Process in chunks, avoid memory blowup
   - Monitoring: Track progress, log errors

3. **Architecture:**
   ```
   ConsolidationService (orchestrator)
     ├── MemoryService (read from PostgreSQL)
     ├── EmbeddingService (create vectors)
     ├── ClusteringService (group similar)
     └── GraphService (write to Neo4j)
   ```

4. **Patterns:**
   - Repository: Abstract DB access
   - Strategy: Swappable clustering algorithm
   - Batch: Process in chunks
   - Async: Non-blocking execution

5. **Decisions:**
   - Batch size: 1000 memories per cycle
   - Embedding model: Voyage AI (semantic richness)
   - Clustering: K-means on embeddings
   - Safety: Rollback if >10% fail

## Implementation Considerations

### Performance Optimization
- Cache frequently accessed data (Redis L1)
- Use indexes on query columns
- Batch operations, avoid N+1
- Async for I/O-bound operations

### Maintainability
- Clear layer separation
- Single responsibility per class
- Comprehensive tests (unit + integration)
- Documentation of decisions

### Scalability
- Stateless services (horizontal scaling)
- Database sharding (if needed)
- Queue for async tasks
- Monitoring and alerting

### Debugging
- Structured logging
- Request tracing
- Database query profiling
- Frontend performance monitoring

## References
- SOLID principles
- Layered architecture patterns
- Design patterns catalog
- System design fundamentals
