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
