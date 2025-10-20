# AGI Time Blocking

**Full-stack time blocking application with AI-powered memory and task management.**

## 📁 Monorepo Structure

```
agi/
├── frontend/          # React + Vite + TypeScript + Tailwind
├── backend/           # FastAPI + GraphQL + PostgreSQL + pgvector
├── .claude/           # Claude Code configuration
└── README.md
```

## 🚀 Tech Stack

### Frontend
- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **GraphQL Client**: urql
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI
- **API**: GraphQL (Strawberry)
- **Database**: PostgreSQL with pgvector extension
- **Search**: Hybrid search (Voyage AI embeddings + BM25)
- **Deployment**: Railway

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension

### Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 🌐 Deployment

### Automatic Deployments

- **Frontend** (Vercel): Auto-deploys on push to `master` (root directory: `/frontend`)
- **Backend** (Railway): Auto-deploys on push to `master` (root directory: `/backend`)

### Preview Deployments

- Every PR creates preview deployments for both frontend and backend
- Frontend preview: `https://[branch]-[hash].vercel.app`
- Backend preview: `https://[branch]-[hash].up.railway.app`

## 📊 Features

- ✅ Time blocking with containers and blocks
- ✅ Hybrid memory search (semantic + keyword)
- ✅ GraphQL API with real-time subscriptions
- ✅ Neo4j graph database integration
- ✅ Vector embeddings with Voyage AI
- ✅ BM25 full-text search

## Architecture

### Monorepo Layout

```
agi/
├── frontend/               # Next.js frontend (Vercel)
│   ├── app/               # Next.js 14 app router
│   ├── components/        # React components (shadcn/ui)
│   ├── src/guidelines/    # figma.md design rules
│   └── package.json
├── backend/               # Python backend + API
│   ├── api/              # FastAPI routes
│   ├── services/         # Business logic
│   └── agents/           # Autonomous agents
│       ├── base_agent.py
│       ├── frontend_manager.py
│       ├── consolidator.py (TODO)
│       └── validator.py (TODO)
├── cortex/               # Memory system core
│   ├── agi_tools_mcp.py  # MCP server
│   ├── daemon/           # Agent orchestrator
│   └── hooks/            # Claude Code hooks
├── scripts/
│   └── systemd/          # Service files
├── mcp_servers/          # Local MCP servers
│   ├── exa-mcp-server    # Exa search API
│   ├── fetch-mcp         # Web fetch
│   └── context7-mcp      # Context API
└── .env                  # Environment variables
```

### Boucle Fermée (Autonomous Loop)

```
Events (DB/Redis) → Agents (Python) → Actions (DB/API) → Events (feedback)
        ↑                                                      ↓
        └──────────────────── Continuous Loop ────────────────┘
```

**Frontend (Next.js) = Monitoring only** (not in loop)

### Services Management

#### 1. AGI Agents Daemon
```bash
sudo systemctl start agi-agents
sudo systemctl status agi-agents
journalctl -u agi-agents -f
```

#### 2. Backend API
```bash
cd backend
uvicorn api.main:app --reload
```

#### 3. Frontend Dev
```bash
cd frontend
npm run dev
```

### Agents Directory

| Agent | Type | Schedule | Purpose |
|-------|------|----------|---------|
| FrontendManager | Event-driven | - | Generate/update React components |
| Consolidator | Scheduled | 1h | LTP/LTD intelligent consolidation |
| Validator | Event-driven | - | Check memory contradictions |
| PatternExtractor | Scheduled | 6h | Detect insights from events |
| Connector | Scheduled | 12h | Neo4j graph optimization |

## Memory System

- **PostgreSQL**: Transactional storage (events, tasks, memories)
- **Neo4j**: Graph database (relationships, patterns, knowledge graph)
- **Redis**: Caching and event queue
- **Voyage AI**: Vector embeddings for semantic search
- **pgvector**: PostgreSQL extension for similarity search
