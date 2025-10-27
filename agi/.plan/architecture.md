# AGI-V2 System Architecture

**Generated:** 2025-10-27 (Retrospective Analysis)
**Version:** 1.0
**Status:** Mature Production System

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ App.tsx → Components (UI) → Hooks (State) → API Client   │ │
│  │ Port: 3000                                                │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────────────┘
                     │ HTTP/WS (CORS enabled)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                         │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ Routes: /api/tasks, /api/agents, /api/memory, /api/auth  ││
│  │ Port: 8000                                                 ││
│  │ Middleware: CORS, Logging, Error handling                 ││
│  └────────────────────────────────────────────────────────────┘│
└─┬──────────┬──────────┬──────────┬─────────────────────────────┘
  │          │          │          │
  │          │          │          │
  ▼          ▼          ▼          ▼
┌───────┐ ┌──────┐ ┌───────┐ ┌──────────────┐
│       │ │      │ │       │ │              │
│  PG   │ │Neo4j │ │Redis  │ │External APIs │
│Vector │ │Graph │ │Cache  │ │(Anthropic,   │
│       │ │      │ │       │ │Voyage,       │
│ 5432  │ │7687  │ │6379   │ │Cohere)       │
│       │ │      │ │       │ │              │
└───────┘ └──────┘ └───────┘ └──────────────┘
```

---

## Backend Architecture

### Layer 1: API Routes (FastAPI)

**Location:** `backend/api/routes/`

| Route | Module | Endpoints | Purpose |
|-------|--------|-----------|---------|
| `/api/tasks` | `tasks.py` | CRUD task operations | Task management |
| `/api/agents` | `agents.py` | Agent lifecycle control | Agent management |
| `/api/memory` | `memory.py` | L1/L2/L3 memory access | Memory retrieval |
| `/api/auth` | `auth.py` | JWT token management | Authentication |
| `/health` | `health.py` | System health check | Monitoring |

**Shared:** `dependencies.py` (FastAPI dependencies, DB connections)

### Layer 2: Agent System (LangGraph)

**Location:** `backend/agents/`

#### Core Agents:

1. **BaseAgent** (`base_agent.py`)
   - Abstract base class
   - State management (AgentState: messages, context, metadata)
   - Configuration (AgentConfig: name, timeouts, retries)
   - Error handling + logging

2. **ConsolidatorAgent** (`consolidator_agent.py`)
   - Purpose: L1→L2→L3 memory migration
   - Triggers: TTL expiry, manual consolidation
   - Output: Updated memory records

3. **ValidatorAgent** (`validator_agent.py`)
   - Purpose: Knowledge quality assurance
   - Validates: Embeddings, connections, data integrity
   - Output: Validation reports

4. **PatternExtractorAgent** (`pattern_extractor_agent.py`)
   - Purpose: Discover patterns in memory + graph
   - Uses: Embedding similarity, graph clustering
   - Output: Pattern definitions

5. **ConnectorAgent** (`connector_agent.py`)
   - Purpose: Build/update knowledge graph connections
   - Creates: Entity relationships, contextual links
   - Uses: Neo4j APOC procedures

#### Workflows:

**Location:** `backend/agents/workflows/`

1. **MultiAgentOrchestrator** (`multi_agent_orchestrator.py`)
   - Central hub for all agent coordination
   - Manages: Agent lifecycle, message passing, state synchronization
   - Implements: Parallel + sequential execution patterns

2. **MemoryConsolidationWorkflow** (`memory_consolidation_workflow.py`)
   - Orchestrates: ConsolidatorAgent + external services
   - Handles: Vector regeneration, metadata migration
   - Frequency: Periodic (hourly/daily) + on-demand

3. **KnowledgeValidationWorkflow** (`knowledge_validation_workflow.py`)
   - Orchestrates: ValidatorAgent over memory + graph
   - Ensures: Data consistency, embedding accuracy
   - Reports: Validation metrics

4. **PatternAnalysisWorkflow** (`pattern_analysis_workflow.py`)
   - Orchestrates: PatternExtractorAgent + graph analysis
   - Discovers: Recurring patterns, anomalies
   - Output: Pattern library + confidence scores

### Layer 3: Services (Business Logic)

**Location:** `backend/services/`

1. **MemoryService** (`memory_service.py`)
   - Manages hierarchical memory (L1, L2, L3)
   - Methods:
     - `store()` - Store new memory with level selection
     - `retrieve()` - Fetch from specific level or all
     - `consolidate()` - Migrate up hierarchy
     - `purge()` - TTL-based cleanup
   - Integration: PostgreSQL async, pgvector

2. **GraphService** (`graph_service.py`)
   - Neo4j knowledge graph operations
   - Methods:
     - `create_node()` - Add entities
     - `create_relationship()` - Add connections
     - `query()` - Cypher queries
     - `find_patterns()` - GDS algorithms

3. **EmbeddingService** (`embedding_service.py`)
   - Vector generation via Voyage AI
   - Methods:
     - `embed()` - Generate embeddings
     - `embed_batch()` - Bulk operation
     - `find_similar()` - Similarity search

4. **DatabaseService** (`database.py`)
   - PostgreSQL connection pooling
   - async context managers
   - Health checks

5. **ExternalServicesManager** (`external_services.py`)
   - Centralized API credential management
   - Methods for: Voyage, Cohere, Anthropic APIs
   - Error handling + retries

### Layer 4: Configuration

**Location:** `backend/config/`

**settings.py**
- Pydantic BaseSettings
- Sources: Environment variables, .env file
- Validation: Field validators for URLs, CORS origins
- Caching: @lru_cache() for singleton

---

## Frontend Architecture

### Component Structure

**Location:** `frontend/src/`

```
src/
├── App.tsx              # Root component, routing
├── main.tsx             # React DOM mount
├── index.css            # TailwindCSS (95KB)
├── api/                 # HTTP client
├── components/          # UI components (12+)
│   ├── layout/
│   ├── forms/
│   ├── dialogs/
│   └── data-display/
├── hooks/               # Custom React hooks
├── lib/                 # Utilities
└── assets/              # Static files
```

### Key Technologies

- **Build Tool:** Vite (fast refresh, optimized bundles)
- **Component Library:** shadcn/ui (Radix + Tailwind)
- **Icons:** lucide-react (20+ icons)
- **State Management:** React Hooks + Context (if needed)

---

## Data Flow

### Task Creation Flow

```
Frontend (App.tsx)
  │ user submits task form
  ▼
API Client
  │ POST /api/tasks
  ▼
FastAPI Route (tasks.py)
  │ validate request
  ▼
Task Service
  │ save to PostgreSQL
  ▼
MemoryService.store()
  │ determine level + generate embedding
  ▼
GraphService.create_node()
  │ create entity in Neo4j
  ▼
Response (201 Created)
  │
  ▼
Frontend (reload task list)
```

### Memory Consolidation Flow

```
Scheduler (or manual trigger)
  │
  ▼
MultiAgentOrchestrator.execute()
  │
  ▼
MemoryConsolidationWorkflow
  │ 1. Identify L1 records TTL-expired
  │ 2. Fetch from Redis
  │ 3. Regenerate embeddings (EmbeddingService)
  │ 4. Migrate to PostgreSQL L2
  ▼
ConsolidatorAgent
  │ process with LangChain reasoning
  │
  ▼
MemoryService.consolidate()
  │ move records, update metadata
  │
  ▼
Completion + logging
```

---

## Database Schema (Implicit)

### PostgreSQL Tables
- `tasks` - Task records
- `memories` - L2/L3 consolidated memories
- `memory_embeddings` - pgvector vectors
- `agents` - Agent configurations
- `validation_logs` - Validator reports

### Redis Keys
- `memory:L1:{id}` - Immediate memory (TTL 1h)
- `session:{token}` - JWT sessions (TTL 30m)
- `cache:{key}` - General cache

### Neo4j Graph
- **Nodes:** Entity, Task, Agent, Memory, Pattern
- **Relationships:** RELATES_TO, CREATED_BY, EXTRACTED_FROM, SIMILAR_TO

---

## Performance Characteristics

### Database Pooling
- PostgreSQL: 20 min, 30 max overflow
- Redis: 50 max connections
- Neo4j: 50 connection pool

### Memory TTLs
- L1: 1 hour (immediate context)
- L2: 24 hours (working memory)
- L3: 30 days (long-term archive)

### Async Strategy
- All I/O: asyncpg, Redis async client, Neo4j async driver
- Non-blocking: FastAPI ASGI + uvicorn
- Concurrent: 10+ simultaneous requests

---

## Security Considerations

1. **JWT Authentication:** HS256 algorithm (configurable secret)
2. **CORS:** Whitelist-based (localhost:3000 in dev)
3. **Environment Variables:** Secrets in .env (not in code)
4. **Database:** Connection pooling with credentials
5. **Rate Limiting:** Per-minute limits configurable

---

## Deployment

### Docker Compose
- Services: PostgreSQL, Neo4j, Redis, FastAPI, React
- Networks: `agi_network` (internal)
- Volumes: Data persistence for all DBs
- Health Checks: All services monitored

### Environment
- Development: debug=true, Swagger UI enabled
- Production: debug=false, reduced logging, optimized pooling

---

## Future Enhancement Points

1. **Load Balancing:** Multiple API instances behind nginx
2. **Caching Layer:** Redis for frequent queries
3. **Message Queue:** Celery/RabbitMQ for async task processing
4. **Observability:** Prometheus metrics + Grafana dashboards
5. **Search:** Elasticsearch for full-text search
6. **Streaming:** WebSocket connections for real-time updates

---

**Note:** This architecture document was created retroactively from code analysis (2025-10-27). All components referenced have been verified in the codebase.
