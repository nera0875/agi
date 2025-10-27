# AGI-V2 Project Requirements

**Project Type:** Multi-Agent Orchestration System for Task Management
**Stack:** FastAPI + React + PostgreSQL + Neo4j + Redis
**Status:** Mature Codebase (Retrospective Planning)
**Last Updated:** 2025-10-27

---

## Core Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **Database:** PostgreSQL 15 + pgvector (vector embeddings)
- **Graph DB:** Neo4j 5.15 (knowledge graph)
- **Cache:** Redis 7 (session + memory L1)
- **Agents:** LangGraph + LangChain
- **Async:** asyncpg, asyncio
- **Logging:** structlog

### Frontend
- **Framework:** React 18 (TypeScript)
- **Build:** Vite (dev server on port 3000)
- **UI Components:** shadcn/ui
- **Icons:** lucide-react
- **CSS:** TailwindCSS (via index.css)

### External Services
- **Embeddings:** Voyage AI
- **LLM:** Cohere + Anthropic
- **API Keys:** Environment-configured

---

## Architecture Overview

### Backend Services
1. **API Routes:**
   - `/api/tasks` - Task management endpoints
   - `/api/agents` - Agent lifecycle + control
   - `/api/memory` - Memory L1/L2/L3 access
   - `/api/auth` - Authentication (JWT-based)
   - `/health` - Health check

2. **Agent System:**
   - `BaseAgent` - Abstract base for all agents
   - `ConsolidatorAgent` - Memory consolidation
   - `ValidatorAgent` - Knowledge validation
   - `PatternExtractorAgent` - Pattern discovery
   - `ConnectorAgent` - Graph connections

3. **Workflows:**
   - `MultiAgentOrchestrator` - Central orchestration
   - `MemoryConsolidationWorkflow` - L1→L2→L3 migration
   - `KnowledgeValidationWorkflow` - Data quality checks
   - `PatternAnalysisWorkflow` - Pattern discovery

4. **Core Services:**
   - `MemoryService` - Hierarchical memory management
   - `GraphService` - Neo4j knowledge graph operations
   - `EmbeddingService` - Vector generation (Voyage)
   - `DatabaseService` - PostgreSQL pooling
   - `ExternalServicesManager` - API integrations

### Frontend Components
- **App.tsx** - Main entry point
- **components/** - UI component library (12+ components)
- **hooks/** - Custom React hooks
- **api/** - API client
- **lib/** - Utilities (shadcn setup, etc)

---

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection
- `NEO4J_URL`, `NEO4J_USER`, `NEO4J_PASSWORD` - Graph DB
- `REDIS_URL` - Cache connection
- `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `COHERE_API_KEY` - External APIs
- `ENVIRONMENT` - development|production
- `CORS_ORIGINS` - Frontend URL list
- `LOG_LEVEL` - Logging verbosity

### Performance Settings
- DB Pool: 20 connections (max 30 overflow)
- Redis: 50 max connections
- Neo4j: 50 connection pool
- Memory TTLs: L1 (1h), L2 (24h), L3 (30d)

---

## Features Implemented

1. **Multi-Agent System**
   - [x] Base agent architecture
   - [x] LangGraph state management
   - [x] Agent isolation + messaging
   - [x] Orchestrator coordination

2. **Hierarchical Memory**
   - [x] L1 (immediate, Redis-backed)
   - [x] L2 (working, PostgreSQL)
   - [x] L3 (long-term, PostgreSQL archive)
   - [x] Consolidation workflow

3. **Knowledge Graph**
   - [x] Neo4j integration
   - [x] Pattern extraction
   - [x] Connection analysis

4. **Task Management**
   - [x] CRUD endpoints
   - [x] Agent assignment
   - [x] Status tracking

5. **API + Frontend**
   - [x] FastAPI REST endpoints
   - [x] React UI (Vite)
   - [x] WebSocket ready (ws:// configured)

---

## Testing

- **Backend Tests:** `backend/tests/test_agents_api.py`, `test_agents_integration.py`
- **Coverage:** Agent APIs, integration workflows
- **Tool:** pytest

---

## Development Setup

```bash
# Docker Compose (all services)
docker-compose up -d

# Backend dev server (requires services)
cd backend && python -m uvicorn main:app --reload

# Frontend dev server
cd frontend/src && npm run dev
```

---

## Known Architecture Decisions

- **Async-first:** All database operations use asyncio
- **pgvector:** PostgreSQL for vectors (not separate Pinecone)
- **Neo4j + PostgreSQL:** Hybrid (graph + relational)
- **Redis TTL:** Memory hierarchy enforced via TTL
- **JWT stateless:** No session table needed

---

## Next Phase Recommendations

1. **Testing Suite:** Expand test coverage beyond integration
2. **CI/CD:** GitHub Actions or similar
3. **Monitoring:** Logging dashboards, metrics collection
4. **Performance:** Load testing, optimization tuning
5. **Documentation:** API docs (Swagger exists), agent decision trees

---

**Archive Note:** This requirements file was generated retroactively from existing codebase (2025-10-27). Represents mature system state.
