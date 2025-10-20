# ADR-0001: Restructuration Backend Safe (26 Issues Audit)

**Date:** 2025-10-20  
**Statut:** Proposed  
**Audit Baseline:** 26 Issues (5 critiques, 12 majeurs, 9 mineurs)  
**Constraint:** Zero downtime - Backend en production  

---

## Executive Summary

Audit qualité révèle **26 issues architectural** bloquant la scalabilité future.  
Plan en **6 phases sécurisées** avec tests à chaque étape.

**Impact critique identifié:**
- ⚠️ **Cohere API key exposée en dur** (SÉCURITÉ URGENT)
- 2,954 lignes dans agi_tools_mcp.py (maintenabilité)
- Doublons: voyage_wrapper/voyage_embeddings (814 lignes)
- Doublons: cohere_wrapper/cohere_rerank (914 lignes)
- Tests éparpillés en root backend/

---

## Contexte

### Issues Critiques (5)

| Issue | Fichier | Impact | Severity |
|-------|---------|--------|----------|
| API key exposée | cohere_wrapper.py:17 | Security breach | **URGENT** |
| Monolithe massive | agi_tools_mcp.py (2954) | Maintenabilité | HIGH |
| Doublons Voyage | wrapper + service | Confusion | HIGH |
| Doublons Cohere | wrapper + service | Confusion | HIGH |
| Memory confusion | memory_service.py (1084) | Architecture | HIGH |

### Issues Majeurs (12)
- api/ vs routes/ (confusion)
- Manque models/ directory
- Manque exceptions/ directory  
- Imports incohérents (relatifs vs absolus)
- Migrations numérotation chaotique
- Tests en root (manque organisation)
- graph_service.py + neo4j_memory.py (overlap)
- hybrid_search.py + memory_service.py (split)
- Agent communication tight-coupled
- Cache invalidation missing
- Observability scattered
- Middleware désorganisé

### Issues Mineurs (9)
- utils/ manquant
- constants/ manquant
- Models/types scattered
- Missing ConsolidatorAgent
- Missing ValidatorAgent
- Missing PatternExtractor
- Code style inconsistencies
- Documentation gaps
- Missing type hints

---

## Solution: 6 Phases Safe

**Principe ABSOLU:** Pas d'interruption production + tests à chaque phase + rollback plan.

---

## PHASE 0: SECURITY (URGENT - 1h)

**Objectif:** Éliminer risques sécurité avant tout

### Problème Identifié
```python
# backend/services/cohere_wrapper.py:17 - EXPOSÉ!
COHERE_API_KEY = "TkkNADrL73TjYBwD6c4jNi3jRvL4h5PbslZ8W7C8"
```

### Actions

1. **Révoquer API key immédiatement**
   - Contact Cohere support → revoke key
   - Generate new key
   - Update .env sécurisé

2. **Charger depuis .env**
   ```python
   # cohere_wrapper.py - BEFORE
   COHERE_API_KEY = "TkkNADrL73TjYBwD6c4jNi3jRvL4h5PbslZ8W7C8"
   
   # cohere_wrapper.py - AFTER
   COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
   if not COHERE_API_KEY:
       raise ValueError("COHERE_API_KEY not set in .env")
   ```

3. **voyage_wrapper.py - même traitement**
   ```python
   # BEFORE: blank (bon)
   VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
   
   # AFTER: strict check
   if not VOYAGE_API_KEY:
       logger.warning("VOYAGE_API_KEY not configured")
   ```

4. **Add pre-commit hook** (détection secrets)
   ```yaml
   # .pre-commit-config.yaml
   - repo: https://github.com/Yelp/detect-secrets
     rev: v1.4.0
     hooks:
     - id: detect-secrets
       args: ['--baseline', '.secrets.baseline']
   ```

### Tests Validation
```bash
# Vérifier app démarre avec .env
pytest -k "test_cohere_init" -v

# Vérifier pas de hardcoded keys
grep -r 'COHERE_API_KEY = "' backend/  # Should be empty
grep -r 'VOYAGE_API_KEY = "' backend/  # Should be empty

# Git secrets check
git secrets scan

# Pre-commit hook active
pre-commit run detect-secrets --all-files
```

### Rollback
```bash
git checkout HEAD -- backend/services/cohere_wrapper.py
git checkout HEAD -- backend/services/voyage_wrapper.py
# (restore old .env from backup)
```

### Risque
**Faible** - Lecteur seul + immediate fix

---

## PHASE 1: DOUBLONS CRITIQUES (2h)

**Objectif:** Unifier Voyage + Cohere (éliminer 814+914 lignes overlap)

### Analyse Doublons

**Voyage:**
- `voyage_wrapper.py` (336 lignes) - HTTP API raw wrapper
- `voyage_embeddings.py` (478 lignes) - Service classe
- **Overlap:** Search logic, caching, error handling

**Cohere:**
- `cohere_wrapper.py` (336 lignes) - HTTP API raw wrapper
- `cohere_rerank.py` (457 lignes) - Service classe
- **Overlap:** Reranking logic, caching, error handling

### Structure After Phase 1

```
backend/services/
├── embeddings/           ← NEW
│   ├── __init__.py
│   ├── voyage.py        ← MERGED (wrapper + service)
│   └── cache.py         ← Shared cache logic
├── reranking/            ← NEW
│   ├── __init__.py
│   ├── cohere.py        ← MERGED (wrapper + service)
│   └── cache.py         ← Shared cache logic
├── [existing others]
└── voyage_wrapper.py    ← REMOVED after tests
    cohere_wrapper.py    ← REMOVED after tests
```

### Implémentation (Ordre STRICT)

**Step 1: Create structure**
```bash
mkdir -p backend/services/embeddings
mkdir -p backend/services/reranking
touch backend/services/embeddings/__init__.py
touch backend/services/reranking/__init__.py
```

**Step 2: Merge Voyage**
- Keep `VoyageEmbeddingService` class (best API)
- Extract caching from `voyage_wrapper.py` → voyage.py
- Result: `backend/services/embeddings/voyage.py` (~450 lines)

**Step 3: Merge Cohere**
- Keep `CohereRerankService` class (best API)
- Extract caching from `cohere_wrapper.py` → cohere.py
- Result: `backend/services/reranking/cohere.py` (~400 lines)

**Step 4: Update imports (audit all):**
```bash
grep -r "from voyage_wrapper import" backend/  # Find all usages
grep -r "from cohere_wrapper import" backend/  # Find all usages
grep -r "import voyage_wrapper" backend/
grep -r "import cohere_wrapper" backend/
```

Update each to:
```python
# OLD
from voyage_wrapper import get_embeddings
from cohere_wrapper import rerank

# NEW
from backend.services.embeddings.voyage import VoyageEmbeddingService
from backend.services.reranking.cohere import CohereRerankService
```

**Step 5: Delete old files** (après tests)
```bash
rm backend/services/voyage_wrapper.py
rm backend/services/cohere_wrapper.py
```

### Tests Validation
```bash
# Module imports work
pytest -k "test_embedding_init" -v
pytest -k "test_rerank_init" -v

# Old usages still work (agi_tools_mcp.py uses old imports)
python -c "from backend.services.embeddings.voyage import VoyageEmbeddingService"
python -c "from backend.services.reranking.cohere import CohereRerankService"

# Semantic search functionality
pytest -k "test_semantic_search" -v

# Reranking functionality
pytest -k "test_rerank" -v

# Full MCP works (uses merged services)
pytest cortex/test_*.py -v
```

### Rollback
```bash
git checkout HEAD -- backend/services/
```

### Risque
**Medium** - Imports change across codebase → Mitigé via grep + test coverage

---

## PHASE 2: STRUCTURE FOLDERS (1h)

**Objectif:** Créer models/, exceptions/, middleware/ (empty structure)

### Structure Created

```
backend/
├── models/              ← NEW (empty for now)
│   └── __init__.py
├── exceptions/          ← NEW (empty for now)
│   └── __init__.py
├── middleware/          ← NEW (organized)
│   ├── __init__.py
│   ├── observability.py ← moved from core/
│   └── auth.py
└── [existing]
```

### Implémentation

```bash
# Create directories
mkdir -p backend/models
mkdir -p backend/exceptions
mkdir -p backend/middleware

# Create __init__.py
touch backend/models/__init__.py
touch backend/exceptions/__init__.py
touch backend/middleware/__init__.py

# Note: DON'T move files yet (Phase 4+)
# Just create empty structure
```

### Tests Validation
```bash
# Directories exist
ls -d backend/models backend/exceptions backend/middleware

# __init__.py exist
ls backend/models/__init__.py

# Backend imports still work
python -c "from backend import services; print('✅')"
python -c "from backend.core import observability; print('✅')"
```

### Rollback
```bash
rmdir backend/models backend/exceptions backend/middleware
```

### Risque
**Très faible** - Structure vide seulement, pas d'imports affectés

---

## PHASE 3: ORGANIZE TESTS (30min)

**Objectif:** Tester move root tests → tests/

### Current State
```
backend/
├── test_memory_optimization.py (105 lignes) ← root
├── test_graphql.py (29 lignes) ← root
├── test_schema.py (33 lignes) ← root
└── tests/
    ├── test_semantic_cache.py (144 lignes)
    ├── [others organized]
    └── ...
```

### Target State
```
backend/
└── tests/
    ├── test_memory_optimization.py ← moved
    ├── test_graphql.py ← moved
    ├── test_schema.py ← moved
    ├── test_semantic_cache.py
    └── ...
```

### Implémentation

```bash
# Move all root test_*.py files
mv backend/test_*.py backend/tests/

# Verify pytest discovers all
pytest backend/tests --collect-only | grep -c "test_"
```

### Tests Validation
```bash
# All tests still discoverable
pytest backend/tests --collect-only

# All tests still pass
pytest backend/tests -v --tb=short

# No import issues
python -m pytest backend/tests --collect-only 2>&1 | grep -i "error"
```

### Rollback
```bash
mv backend/tests/test_*.py backend/
# (keep only those that should be in root - none)
```

### Risque
**Très faible** - Simple filesystem move

---

## PHASE 4: API ORGANIZATION (3h)

**Objectif:** Unifier api/ structure (api/ vs routes/ confusion)

### Current State
```
backend/
├── api/
│   ├── schema.py (1611 lignes) ← MONOLITHE
│   ├── agi_schema.py
│   ├── context.py
│   └── __init__.py
├── routes/
│   ├── memory.py
│   ├── mcp.py
│   └── __init__.py
```

### Target State
```
backend/api/
├── __init__.py (exports)
├── graphql/
│   ├── __init__.py
│   ├── schema.py (memory schema ~400 lignes)
│   ├── agent.py (agent schema ~400 lignes)
│   └── graph.py (graph schema ~400 lignes)
├── rest/
│   ├── __init__.py
│   ├── memory.py ← from routes/
│   └── mcp.py ← from routes/
├── models.py (request/response ~300 lignes)
└── context.py (GraphQL context)

# Removed: routes/ directory
```

### Implémentation

**Step 1: Create structure**
```bash
mkdir -p backend/api/graphql
mkdir -p backend/api/rest
touch backend/api/graphql/__init__.py
touch backend/api/rest/__init__.py
```

**Step 2: Split schema.py (1611 → 3 files)**
- Extract memory-related types → graphql/schema.py (~400 lines)
- Extract agent-related types → graphql/agent.py (~400 lines)
- Extract graph-related types → graphql/graph.py (~400 lines)
- Keep generic models → api/models.py (~300 lines)

**Step 3: Move REST routes**
```bash
mv backend/routes/memory.py backend/api/rest/
mv backend/routes/mcp.py backend/api/rest/
```

**Step 4: Update imports** (audit all files)
```bash
grep -r "from routes import" backend/
grep -r "from api.schema import" backend/
grep -r "from api import schema" backend/
```

Update to:
```python
# OLD
from routes import memory_router
from api.schema import Query, Mutation

# NEW
from api.rest import memory_router
from api.graphql.schema import Query, Mutation
```

**Step 5: Update main.py**
```python
# OLD
from routes import memory_router
app.include_router(memory_router)

# NEW
from api.rest import memory_router
app.include_router(memory_router)
```

**Step 6: Delete routes/ directory**
```bash
rm -rf backend/routes/
```

### Tests Validation
```bash
# API server starts
python backend/main.py &
sleep 3
curl http://localhost:8000/docs 2>/dev/null | grep -q "Swagger"

# GraphQL endpoint responds
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' | grep -q "data"

# All REST routes work
curl http://localhost:8000/api/memory/search 2>/dev/null | head -20

# Import paths resolved
python -c "from api.graphql.schema import Query; print('✅')"
python -c "from api.rest import memory_router; print('✅')"

# No circular imports
python -c "from backend import main; print('✅')" 2>&1 | grep -v "ResourceWarning"
```

### Rollback
```bash
git checkout HEAD -- backend/api/ backend/routes/
```

### Risque
**Medium** - Structural change across imports → Mitigé via grep audit + tests

---

## PHASE 5: SPLIT AGI_TOOLS_MCP (4h)

**Objectif:** Refactor 2,954 lignes → 4 modules

### Current State
```
cortex/agi_tools_mcp.py (2954 lignes) ← MONOLITHE
├── Memory tools: search, store, stats (~600 lines)
├── Database tools: query, execute (~500 lines)
├── Agent tools: launch, results (~400 lines)
├── MCP discovery: Smithery (~200 lines)
└── Utilities & setup (~250 lines)
```

### Target State
```
cortex/mcp_tools/
├── __init__.py (export all tools)
├── memory_tools.py (search, store, stats ~600)
├── database_tools.py (query, execute ~500)
├── agent_tools.py (launch agents ~400)
├── mcp_discovery_tools.py (Smithery ~200)
├── shared.py (utilities ~250)
└── server.py (MCP server setup ~150)

cortex/agi_tools_mcp.py (NEW: thin dispatcher)
```

### Implémentation

**Step 1: Create module**
```bash
mkdir -p cortex/mcp_tools
touch cortex/mcp_tools/__init__.py
```

**Step 2: Extract memory_tools.py**
- `search_memory()` function
- `store_memory()` function
- `get_memory_stats()` function
- Helper: database connection

**Step 3: Extract database_tools.py**
- `query_database()` function
- `execute_query()` function
- `get_schema()` function

**Step 4: Extract agent_tools.py**
- `launch_agent()` function
- `get_agent_results()` function
- `list_agents()` function

**Step 5: Extract mcp_discovery_tools.py**
- `discover_mcps()` function
- `use_mcp()` function
- `get_mcp_info()` function

**Step 6: Extract shared.py**
- Database pool setup
- Error handlers
- Logging utilities
- MCP server helpers

**Step 7: Refactor agi_tools_mcp.py to thin dispatcher**
```python
#!/usr/bin/env python3
"""AGI Tools MCP - Thin dispatcher"""

from cortex.mcp_tools import (
    memory_tools,
    database_tools,
    agent_tools,
    mcp_discovery_tools,
    server
)

# Re-export for backward compatibility
__all__ = [
    "memory_tools",
    "database_tools",
    "agent_tools",
    "mcp_discovery_tools",
]

if __name__ == "__main__":
    server.start_mcp_server()
```

**Step 8: Update imports in cortex/**
```bash
grep -r "from agi_tools_mcp import" cortex/
grep -r "import agi_tools_mcp" cortex/
```

Update to:
```python
# OLD
from agi_tools_mcp import search_memory

# NEW
from cortex.mcp_tools.memory_tools import search_memory
```

### Tests Validation
```bash
# MCP server starts
python cortex/agi_tools_mcp.py &
sleep 2
ps aux | grep "agi_tools_mcp" | grep -v grep

# Tools discoverable via MCP
curl http://localhost:9000 2>/dev/null | grep -q "tools"

# Each tool works
pytest cortex/mcp_tools/test_memory_tools.py -v
pytest cortex/mcp_tools/test_database_tools.py -v
pytest cortex/mcp_tools/test_agent_tools.py -v
pytest cortex/mcp_tools/test_mcp_discovery_tools.py -v

# Backward compat (old imports still work)
python -c "from cortex.agi_tools_mcp import memory_tools; print('✅')"

# Integration with local_mcp_router.py
python cortex/local_mcp_router.py --list | grep -i "memory"
```

### Rollback
```bash
git checkout HEAD -- cortex/agi_tools_mcp.py cortex/mcp_tools/
```

### Risque
**Medium** - Large refactor → Mitigé via backward compat layer

---

## PHASE 6: VALIDATION & DOCUMENTATION (1h)

**Objectif:** Valider cohérence système + documenter

### Validation Checklist

#### 1. Backend Clean Check
```bash
# All tests pass
pytest backend/ -v --tb=short

# MCP tests pass
pytest cortex/mcp_tools/ -v --tb=short

# Code quality metrics
radon cc backend/ -a  # Should be < 10 avg
radon mi backend/ -s  # Should be > 7 (maintainable)

# No hardcoded secrets
git secrets scan
detect-secrets scan --baseline .secrets.baseline

# No console.log type commits
git log --oneline -5
```

#### 2. Import Verification
```bash
# No relative imports (must be absolute)
grep -r "^from \.\." backend/ | wc -l  # Should be 0
grep -r "^from \.\." cortex/mcp_tools/ | wc -l  # Should be 0

# No circular dependencies
python -c "import backend; print('✅ Backend OK')"
python -c "import cortex; print('✅ Cortex OK')"

# Dependency tree (optional)
pydeps backend/ --max-bacon 2 -o backend_deps.svg
```

#### 3. Production Simulation
```bash
# Start stack
docker-compose down
docker-compose up -d

# Wait for services
sleep 10

# Health checks
curl http://localhost:5432 2>&1 | grep -q "pg"  # PostgreSQL
curl http://localhost:6379 2>&1 | grep -q "redis"  # Redis
curl http://localhost:7687 2>&1 | grep -q "neo4j"  # Neo4j

# Backend API
uvicorn backend.main:app --reload &
sleep 3
curl http://localhost:8000/docs 2>/dev/null | grep -q "Swagger"

# GraphQL
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' | grep -q "data"

# L1 event simulation
python cortex/workers/task_executor.py --test

# Check logs
tail -50 /tmp/agi.log | grep -i "error"
```

#### 4. File Structure Verification
```bash
# Expected new structure
ls -d backend/models backend/exceptions backend/middleware backend/api/graphql backend/api/rest
ls -d backend/tests
ls -d cortex/mcp_tools

# Unwanted files removed
test -f backend/services/voyage_wrapper.py && echo "ERROR: voyage_wrapper.py still exists"
test -f backend/services/cohere_wrapper.py && echo "ERROR: cohere_wrapper.py still exists"
test -f backend/routes && echo "ERROR: routes/ still exists"

# Expected files deleted
ls backend/test_*.py 2>/dev/null | wc -l  # Should be 0
```

### Documentation Updates

**1. Update docs/ARCHITECTURE.md**
```markdown
## Backend Structure (Post-Phase 6)

### Services Organization
- **embeddings/**: Voyage AI wrapper + caching
- **reranking/**: Cohere reranker + caching
- **memory/**: Memory orchestration
- **graph/**: Neo4j integration

### API Organization
- **api/graphql/**: GraphQL schema definitions
- **api/rest/**: REST routes
- **api/models.py**: Request/response models

### MCP Tools Organization
- **mcp_tools/memory_tools.py**: Memory operations
- **mcp_tools/database_tools.py**: PostgreSQL
- **mcp_tools/agent_tools.py**: Agent orchestration
- **mcp_tools/mcp_discovery_tools.py**: MCP registry

### Import Conventions
- All imports: absolute (`from backend.services`)
- No relative imports allowed
- Circular dependencies: forbidden (use mediators)
```

**2. Update README.md**
```markdown
## Project Structure

### Backend Architecture
[New structure overview]

### Setup & Development
```bash
# Install deps
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with API keys

# Run backend
uvicorn backend.main:app --reload

# Run tests
pytest backend/ -v
pytest cortex/mcp_tools/ -v
```

**3. Create docs/MIGRATION.md**
```markdown
## Phase 6 Migration Summary

### Changes Made
- API keys secured in .env
- Voyage/Cohere wrappers merged with services
- Backend folders reorganized (models, exceptions, middleware)
- Tests moved to backend/tests/
- API split: graphql/ + rest/
- MCP tools refactored into modules

### Breaking Changes
- None (all phases backward compatible)

### Import Changes (Recommended)
```

---

## Timeline & Effort Estimate

| Phase | Duration | Tasks | Risk | Blocking |
|-------|----------|-------|------|----------|
| 0 | 1h | Security (API keys) | LOW | YES |
| 1 | 2h | Merge Voyage+Cohere | MEDIUM | YES |
| 2 | 1h | Create folders | LOW | NO |
| 3 | 30min | Move tests | LOW | NO |
| 4 | 3h | Split API schema | MEDIUM | YES |
| 5 | 4h | Split agi_tools_mcp | MEDIUM | YES |
| 6 | 1h | Validate + document | LOW | NO |
| **TOTAL** | **~11.5h** | - | MEDIUM | - |

---

## Implementation Delegation

**Agent tasks:**

```bash
# Phase 0 (CRITICAL)
Task(code, "Phase 0: Secure API keys + pre-commit hook")

# Phase 1
Task(code, "Phase 1: Merge Voyage wrapper + service")
Task(code, "Phase 1: Merge Cohere wrapper + service")
Task(debug, "Phase 1: Validate merged services")

# Phase 2-3
Task(code, "Phase 2-3: Create folders + move tests")
Task(debug, "Phase 2-3: Verify pytest discovery")

# Phase 4
Task(code, "Phase 4: Split schema.py into 3 files")
Task(code, "Phase 4: Move routes to api/rest")
Task(debug, "Phase 4: Validate API endpoints")

# Phase 5
Task(code, "Phase 5: Split agi_tools_mcp into modules")
Task(debug, "Phase 5: Validate MCP tool discovery")

# Phase 6
Task(debug, "Phase 6: Full system validation")
Task(docs, "Phase 6: Update documentation")
```

---

## Risques & Mitigations

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| API key leak before revoke | CRITICAL | Immediate Phase 0 + pre-commit hook |
| Import path breaks | HIGH | Grep audit + comprehensive test suite |
| Tests fail mid-phase | MEDIUM | Run tests before/after each step |
| Circular imports | MEDIUM | pydeps analysis + manual review |
| Production downtime | CRITICAL | All phases backward compatible |
| Missed refactorings | MEDIUM | Code review on each phase |

---

## Success Criteria

✅ **Phase 0:** API keys removed from codebase, .env configured  
✅ **Phase 1:** No voyage_wrapper.py + cohere_wrapper.py, tests pass  
✅ **Phase 2-3:** Organized structure, tests discoverable  
✅ **Phase 4:** API split working (GraphQL + REST), no broken imports  
✅ **Phase 5:** MCP tools discoverable, backend still works  
✅ **Phase 6:** All tests green, documentation updated, zero production issues  

---

## Décisions Architecturales Clés

1. **Backward Compatibility:** All phases maintain old import paths (deprecated wrappers)
2. **No Forced Migration:** Existing code works as-is (gradual adoption encouraged)
3. **Testing First:** Green tests = phase completion signature
4. **Git Branches:** Each phase in separate branch for easy review + rollback
5. **Documentation:** Update docs AFTER phase validates (not before)

---

## Next Steps (Phase 7+)

Post-Phase 6 (Future roadmap):

**Phase 7: Memory Consolidation** (Days 2-3)
- Extract neo4j logic from memory_service.py
- Create graph_coordinator.py
- Reduce memory_service from 1084 → 600 lines

**Phase 8: Event Bus** (Days 3-4)
- Redis pub/sub wrapper
- Event-driven agent communication
- Decouple services

**Phase 9: Missing Agents** (Days 4-5)
- Implement ConsolidatorAgent
- Implement ValidatorAgent
- Implement PatternExtractor

---

## Références

- Audit complet: `.claude/agi_architecture_analysis.json`
- Security best practices: OWASP Secrets Management
- Python imports: PEP 8 Style Guide
- Refactoring patterns: Martin Fowler Refactoring Catalog

---

**ADR Status:** Proposed  
**Review Required:** Architecture + Security teams  
**Approval Gate:** Phase 0 (Security) before proceeding  

