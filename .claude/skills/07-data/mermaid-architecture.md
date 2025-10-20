---
name: Mermaid Architecture Diagrams
description: Architecture visualization patterns, components, and styling with Mermaid
category: documentation
---

# Mermaid Architecture Diagrams

Expertise in creating architecture diagrams, system components, and data flow visualizations using Mermaid syntax.

## System Architecture Pattern

### High-Level System Diagram

```mermaid
graph TB
    Client["🖥️ Client<br/>React 18 + Vite"]
    API["⚡ API Layer<br/>FastAPI + GraphQL"]
    Services["🔧 Services<br/>Memory, Graph, Embeddings"]
    Data["💾 Data Layer<br/>Redis + PostgreSQL + Neo4j"]

    Client -->|HTTP/WebSocket| API
    API -->|Business Logic| Services
    Services -->|Read/Write| Data

    style Client fill:#e1f5ff
    style API fill:#fff3e0
    style Services fill:#f3e5f5
    style Data fill:#e8f5e9
```

### Component Interaction Diagram

```mermaid
graph LR
    UI["Frontend<br/>React Components"]
    Apollo["Apollo Client<br/>GraphQL Cache"]
    GQL["GraphQL Server<br/>Strawberry"]
    Memory["Memory Service<br/>L1/L2/L3"]
    Voyage["Voyage AI<br/>Embeddings"]

    UI -->|useQuery/useMutation| Apollo
    Apollo -->|HTTP| GQL
    GQL -->|Call| Memory
    Memory -->|Embed| Voyage

    style UI fill:#e3f2fd
    style Apollo fill:#fff9c4
    style GQL fill:#f8bbd0
    style Memory fill:#c8e6c9
    style Voyage fill:#b2dfdb
```

## Database Architecture

### Memory System (L1/L2/L3)

```mermaid
graph TB
    Query["Query Request"]

    L1["L1: Redis<br/>Hot Cache<br/>TTL: 1 hour"]
    L2["L2: PostgreSQL<br/>Warm Store<br/>Full History"]
    L3["L3: Neo4j<br/>Cold Graph<br/>Semantic Links"]

    Embedding["Voyage AI<br/>Embeddings"]

    Query -->|Fast Lookup| L1
    L1 -->|Miss| L2
    L2 -->|Graph Queries| L3
    L3 -->|Similarity| Embedding

    style Query fill:#ffeb3b
    style L1 fill:#c8e6c9
    style L2 fill:#bbdefb
    style L3 fill:#ffe0b2
    style Embedding fill:#f8bbd0
```

### Entity Relationship (Simplified)

```mermaid
erDiagram
    MEMORY ||--o{ EMBEDDING : has
    MEMORY ||--o{ NEUROTRANSMITTER : uses
    AGENT ||--o{ MEMORY : creates
    AGENT ||--o{ TASK : executes
    TASK ||--o{ RESULT : produces

    MEMORY {
        int id PK
        string content
        timestamp created_at
        timestamp updated_at
    }

    EMBEDDING {
        int id PK
        int memory_id FK
        vector vector_data
    }

    AGENT {
        int id PK
        string name
        string role
    }

    NEUROTRANSMITTER {
        int id PK
        string name
        float weight
    }
```

## Data Flow Architecture

### GraphQL Query Flow

```mermaid
sequenceDiagram
    participant Client as React Client
    participant Apollo as Apollo Cache
    participant GQL as GraphQL Server
    participant Service as Memory Service
    participant DB as PostgreSQL

    Client->>Apollo: useQuery(GET_MEMORIES)
    Apollo-->>Apollo: Check cache
    alt Cache HIT
        Apollo->>Client: Return cached data
    else Cache MISS
        Apollo->>GQL: HTTP POST query
        GQL->>Service: get_memories()
        Service->>DB: SELECT * FROM memories
        DB-->>Service: [Memory rows]
        Service-->>GQL: [Memory objects]
        GQL-->>Apollo: { data, extensions }
        Apollo-->>Client: Update cache + return
    end
```

### Agent Execution Flow

```mermaid
graph TD
    Start["User Input"] -->|Dispatch| Router["Orchestrator<br/>Routes to Agent"]

    Router -->|Analyze| Agent1["CodeGuardian<br/>Test + Quality"]
    Router -->|Monitor| Agent2["InfraWatch<br/>Health Check"]
    Router -->|Optimize| Agent3["PerformanceOpt<br/>DB + API"]

    Agent1 -->|Report| Results["Aggregate<br/>Results"]
    Agent2 -->|Report| Results
    Agent3 -->|Report| Results

    Results -->|Store| Memory["Memory Service<br/>L1/L2/L3"]
    Memory -->|Notify| Client["Return to<br/>Client"]

    style Start fill:#ffeb3b
    style Router fill:#fff9c4
    style Agent1 fill:#c8e6c9
    style Agent2 fill:#bbdefb
    style Agent3 fill:#ffe0b2
    style Memory fill:#f8bbd0
    style Client fill:#ffccbc
```

## Deployment Architecture

### Infrastructure Stack

```mermaid
graph TB
    VPS["VPS: Ubuntu 22.04<br/>8 vCPU, 32GB RAM"]

    subgraph Services["🚀 Services Layer"]
        API["FastAPI Server<br/>:8000"]
        WebSocket["WebSocket Server<br/>:8001"]
    end

    subgraph Databases["💾 Database Layer"]
        Redis["Redis<br/>Cache"]
        PG["PostgreSQL<br/>Main DB"]
        Neo4j["Neo4j<br/>Graph DB"]
    end

    subgraph External["☁️ External Services"]
        Voyage["Voyage AI API"]
        Exa["Exa Search API"]
        Anthropic["Anthropic Claude API"]
    end

    VPS -->|Hosts| Services
    VPS -->|Hosts| Databases
    Services -->|Query| Databases
    Services -->|Call| External

    style VPS fill:#e3f2fd
    style API fill:#fff9c4
    style WebSocket fill:#fff9c4
    style Redis fill:#c8e6c9
    style PG fill:#bbdefb
    style Neo4j fill:#ffe0b2
    style Voyage fill:#f8bbd0
    style Exa fill:#f8bbd0
    style Anthropic fill:#f8bbd0
```

## State Machine Diagram

### Memory Consolidation State

```mermaid
stateDiagram-v2
    [*] --> Raw: New memory<br/>created

    Raw --> L1: Consolidate<br/>short-term
    L1 --> L2: After 1 hour<br/>or manual trigger
    L2 --> L3: After 7 days<br/>or search-heavy
    L3 --> Archived: After 90 days<br/>or low relevance

    L1 -.->|Cache Miss| L2
    L2 -.->|Graph Query| L3

    Archived --> [*]

    note right of Raw
        Direct input from
        hooks, API, agents
    end note

    note right of L1
        Hot cache
        Redis, TTL=1h
    end note

    note right of L2
        Warm store
        PostgreSQL
        Full history
    end note

    note right of L3
        Cold graph
        Neo4j
        Semantic links
    end note
```

## Styling Reference

### Color Palette (Accessibility-First)

| Component | Color | Hex | Use Case |
|-----------|-------|-----|----------|
| Frontend | Light Blue | #e3f2fd | Client-side |
| Backend API | Light Yellow | #fff9c4 | Server logic |
| Services | Light Purple | #f3e5f5 | Business logic |
| Cache | Light Green | #c8e6c9 | In-memory |
| Primary DB | Light Blue | #bbdefb | Main storage |
| Graph DB | Light Orange | #ffe0b2 | Relationships |
| External API | Light Pink | #f8bbd0 | Third-party |
| User/Input | Light Amber | #ffeb3b | User action |

### Styling Syntax

```mermaid
graph TB
    A["Component Name"]
    B["Another Component"]

    A --> B

    style A fill:#e3f2fd,color:#1565c0,stroke:#0d47a1,stroke-width:2px
    style B fill:#c8e6c9,color:#2e7d32,stroke:#1b5e20,stroke-width:2px
```

### Common Patterns

```mermaid
graph LR
    A["Client Request"]
    B["Authorization Check"]
    C["Business Logic"]
    D["Data Access"]
    E["Response"]

    A --> B
    B -->|Authorized| C
    B -->|Denied| reject["401 Error"]
    C --> D
    D --> E

    style A fill:#ffeb3b
    style B fill:#fff9c4
    style C fill:#f3e5f5
    style D fill:#bbdefb
    style E fill:#c8e6c9
    style reject fill:#ffccbc
```

## Class Diagram (Backend Models)

```mermaid
classDiagram
    class Memory {
        +int id
        +string content
        +list[float] embedding
        +datetime created_at
        +list[int] neurotransmitter_ids
        +get_similarity(other: Memory) -> float
        +consolidate() -> void
    }

    class Agent {
        +int id
        +string name
        +string role
        +execute(task: Task) -> Result
        +report() -> str
    }

    class MemoryService {
        +store(memory: Memory) -> void
        +retrieve(query: str) -> list[Memory]
        +consolidate() -> void
        +search_semantic(embedding: list) -> list[Memory]
    }

    class GraphQLSchema {
        +Query query_memory()
        +Mutation create_memory()
        +Subscription on_memory_update()
    }

    Memory <|-- MemoryService
    Agent <|-- MemoryService
    MemoryService <|-- GraphQLSchema
```

## Timeline (Feature Rollout)

```mermaid
timeline
    title Feature Rollout Timeline

    Phase1 : Memory System v1
          : L1 + L2 (Redis + PostgreSQL)
          : Basic consolidation

    Phase2 : Graph Database
          : L3 (Neo4j integration)
          : Semantic linking

    Phase3 : Agent Team
          : 6 autonomous agents
          : Daily standup automation

    Phase4 : Real-time Subscriptions
          : GraphQL subscriptions
          : WebSocket support

    Phase5 : Frontend Dashboard
          : React components
          : Memory visualization
```

## Gitflow Diagram

```mermaid
gitGraph
    commit id: "Initial commit"
    commit id: "Add memory service"

    branch develop
    checkout develop
    commit id: "Feature: L1 cache"
    commit id: "Feature: embeddings"

    branch feature/agents
    checkout feature/agents
    commit id: "Add agent base"
    commit id: "Implement CodeGuardian"

    checkout develop
    merge feature/agents
    commit id: "Release v0.2"

    checkout main
    merge develop
    tag v0.2.0

    checkout develop
    commit id: "Feature: subscriptions"
```

## Mermaid Best Practices

### DO

✅ Use meaningful labels (not just "A", "B", "C")
✅ Keep arrows clear (single direction when possible)
✅ Color-code by layer/responsibility
✅ Add notes for context
✅ Test rendering in GitHub/docs platform
✅ Version in comments (top of diagram)

### DON'T

❌ Create diagrams > 15 nodes (split into multiple)
❌ Use colors that fail accessibility (WCAG AA)
❌ Cross same edge multiple times (hard to read)
❌ Mix different diagram types randomly
❌ Leave diagrams without title/legend

## Tools & Resources

```bash
# Mermaid editor (web)
https://mermaid.live

# Local rendering
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagram.mmd -o diagram.svg

# GitHub Markdown (native support)
# Just paste mermaid block in .md

# Documentation
https://mermaid.js.org
```

---

**Version:** 2025-10-19 v1 - Mermaid Architecture Skill
**For:** DocsKeeper agent + architecture design
**Rendering:** GitHub + Mermaid Live Editor
