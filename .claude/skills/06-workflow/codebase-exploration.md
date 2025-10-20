---
title: Codebase Exploration Strategy
category: workflow
priority: high
updated: 2025-10-20
version: 1.0
agent: ask
---

# Codebase Exploration Strategy

## Overview
Systematic codebase analysis using Glob/Grep patterns without creating duplicate files or code.

## Pattern-Based Discovery

### 1. File Structure Mapping
```bash
# Backend services layer
Glob: backend/services/*.py
→ Extract: class definitions, public methods, type hints

# API endpoints
Glob: backend/api/**/*.py
→ Extract: routes, mutations, queries, resolvers

# Data models
Glob: backend/models/*.py
→ Extract: SQLAlchemy models, relationships, constraints

# Test coverage
Glob: backend/tests/**/*.py
→ Extract: test classes, fixtures, coverage areas
```

### 2. Dependency Graph Analysis
```python
# Identify imports
Grep: "^from .* import|^import" --type py

# Find circular dependencies
Grep: "from app.services import" backend/

# Locate external API calls
Grep: "requests\.|httpx\.|aiohttp\." --type py
```

### 3. Code Duplication Detection
```bash
# Find similar patterns
Grep: "class.*Service" backend/services/
Grep: "def.*memory|def.*graph" backend/

# Identify wrapper/service pairs
Glob: **/*wrapper*.py
Glob: **/*service*.py
→ Compare if same functionality
```

## Before Creating New Files

### Step 1: Scanner Existence
```python
# Pattern you want to create: memory_service.py
Glob: "**/*memory*"
→ If exists: Edit existing (NEVER Write new)
→ If not: Check for similar patterns
```

### Step 2: Search Similar Logic
```python
# Looking for memory management
Grep: "class.*Memory" --type py
Grep: "def.*consolidate" --type py
→ Reuse existing class/function if possible
```

### Step 3: Verify Project Structure
```markdown
REQUIRED STRUCTURE:

backend/
  ├── api/          → GraphQL/REST endpoints ONLY
  ├── services/     → Business logic (MemoryService, GraphService)
  ├── models/       → SQLAlchemy DB models
  ├── schemas/      → Pydantic validation
  ├── agents/       → LangGraph agents
  ├── migrations/   → Alembic migrations
  └── tests/        → Mirror structure exactly

cortex/
  └── agi_tools_mcp.py  → MCP tools (consolidated here)

frontend/src/
  ├── components/ui/    → shadcn/ui (don't create)
  ├── components/       → Feature components
  ├── pages/            → Page components
  ├── hooks/            → Custom React hooks
  └── lib/              → Utilities (organized)

NEVER:
- Random files at root
- Vague names (utils.py, helper.py, misc.py)
- SQL files outside migrations/
- Creating under wrong directory
```

## Architecture Discovery Questions

### Backend Analysis
1. **Service Layer:** Which services handle which domains?
   - `memory_service.py` → L1/L2/L3 memory management
   - `voyage_wrapper.py` → Embeddings via Voyage AI
   - `graph_service.py` → Neo4j graph operations

2. **API Structure:** What's exposed?
   - GraphQL schema in `backend/api/schema.py`
   - REST routes in `backend/routes/`
   - Mutation/Query resolvers

3. **Data Models:** Core entities?
   - Memory model
   - Graph nodes/edges
   - User sessions
   - Embeddings

4. **Agent Infrastructure:**
   - Base agent class
   - L1Observer implementation
   - LangGraph chains

### Frontend Analysis
1. **Component Organization:**
   - shadcn/ui components (already exist)
   - Feature-specific components
   - Layout components

2. **State Management:**
   - Apollo Client for GraphQL
   - useQuery/useMutation/useSubscription hooks
   - Local state vs server state

3. **Routing:** Page structure and navigation

## Naming Conventions to Verify

### Python (Backend)
```python
✅ memory_service.py              (snake_case files)
✅ class MemoryService            (PascalCase classes)
✅ def get_memory()               (snake_case functions)
✅ MAX_RETRIES = 3                (UPPER_CASE constants)

❌ MemoryService.py               (not Python style)
❌ def GetMemory()                (not Python style)
❌ memory_service_v2.py           (avoid versions)
```

### TypeScript/React (Frontend)
```typescript
✅ memory-card.tsx                (kebab-case components)
✅ use-memory.ts                  (kebab-case hooks)
✅ memory.module.css              (kebab-case styles)

❌ MemoryCard.tsx                 (should be kebab)
❌ useMemory.ts                   (should be kebab)
❌ memory_component.tsx           (should be kebab)
```

## Exploration Checklist

- [ ] Map all services and their responsibilities
- [ ] Identify existing utilities (don't duplicate)
- [ ] Find test patterns and coverage gaps
- [ ] Check for naming consistency
- [ ] Verify import organization
- [ ] Map API endpoints to services
- [ ] Document data model relationships
- [ ] Check for hardcoded config values
- [ ] Identify error handling patterns
- [ ] Find performance hotspots

## Tools & Commands

```bash
# Find all Python services
Glob: backend/services/*.py

# Find all tests
Glob: backend/tests/test_*.py

# Find config files
Glob: backend/**/*.env

# Find migrations
Glob: backend/migrations/

# Search for specific patterns
Grep: "async def" --type py      # Async functions
Grep: "TODO|FIXME|HACK" --type py  # Marked issues

# Frontend component discovery
Glob: frontend/src/components/**/*.tsx
```

## When to Reuse vs Create

| Situation | Action |
|-----------|--------|
| Function exists with exact logic | Use existing |
| Similar logic in different file | Extract to shared util |
| Multiple "v1/v2/v3" versions | Consolidate into one |
| Duplicate code in N files | Refactor into service |
| Code in wrong location | Move to correct layer |
| New feature, nothing similar | Create in correct location |

## Key Questions Before Coding

1. Does this logic already exist somewhere?
2. Is this in the right directory?
3. Should this be a new file or extend existing?
4. Does naming follow project conventions?
5. Will this create a duplicate of another component?
6. Is this handling one responsibility (SRP)?
7. Are tests already in place for similar code?

---

**Remember:** Better to spend 2 minutes exploring than 20 minutes refactoring duplicates later.
