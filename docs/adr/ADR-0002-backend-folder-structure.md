# ADR-0002: Backend Folder Structure Reorganization

**Date:** 2025-10-20  
**Statut:** Proposed  
**Phase:** 2 (Structure Cleanup)  
**Related:** ADR-0001  

---

## Executive Summary

Reorganize `/backend` to establish **clear separation of concerns** across 5 distinct layers:

| Layer | Purpose | Folders |
|-------|---------|---------|
| **Presentation** | API endpoints (GraphQL + REST) | `api/` |
| **Domain** | Models + Exceptions | `models/`, `exceptions/` |
| **Business** | Core logic + validation | `services/`, `validators/` |
| **Infrastructure** | Config, DB, jobs | `config/`, `migrations/`, `jobs/` |
| **Utilities** | Scripts, tests, agents | `scripts/`, `tests/`, `agents/` |

**Key Decision:** Use **folder-by-feature** (memory, agent, graph) rather than layer-by-file.

**Impact:** 
- ✅ New developers know where to add code
- ✅ No import confusion (models always in `models/`)
- ✅ Eliminates 23 import issues found in audit
- ⏱️ 7 hours implementation, 1.75 days total

---

## Problem Analysis

### Current Issues

#### 1. **api/ vs routes/ Confusion**
**Status:** HIGH priority

- `backend/api/` = GraphQL schema (business logic, 53KB)
- `backend/routes/` = REST endpoints (thin wrappers, 23KB)
- **User confusion:** "Where do I add a new endpoint?"
- **Result:** Ad-hoc placement of models/validators

**Example:**
```
MemorySearchRequest lives in: routes/memory.py
MemoryType lives in: api/schema.py (Strawberry)
MemoryValidator lives in: validators/memory_validator.py
MemoryModel lives in: services/memory_service.py  ← DUPLICATED!
```

#### 2. **Models Dispersed Across 4 Locations**
**Status:** MAINTENANCE NIGHTMARE

Files containing models:
- `api/schema.py` (1766 lines, Strawberry dataclasses)
- `api/agi_schema.py` (790 lines, more Strawberry)
- `routes/memory.py` (137 lines, Pydantic)
- `routes/mcp.py` (20KB, mixed)
- `services/memory_service.py` (1084 lines, domain objects)

**Consequence:** 
- Duplicated MemoryCreateRequest definitions
- Circular import risks (api → services → api)
- Hard to enforce validation consistency

#### 3. **No Exceptions Hierarchy**
**Status:** TECHNICAL DEBT

Exceptions scattered:
- `validators/memory_validator.py` → MemoryValidationError
- `agents/l1_observer/mcp_integration.py` → MCPError, MCPTimeoutError
- No base exception class
- No consistent error handling

**Consequence:**
- Services raise generic Exceptions
- Routes catch all exceptions (bad error responses)
- Logging doesn't provide context

#### 4. **Routes Too Thin**
**Status:** MAINTAINABILITY ISSUE

- `routes/memory.py`: 137 lines (just HTTP wrappers)
- `routes/mcp.py`: 20KB (too large for one file)

**Consequence:**
- Can't test REST logic without FastAPI
- Can't organize large routes logically
- Services have no REST-specific handling

#### 5. **Validators Couplé aux Models**
**Status:** VALIDATION INCONSISTENCY

- `validators/memory_validator.py` has full validation logic
- `services/memory_service.py` duplicates validation
- No single source of truth for "is this memory valid?"

**Consequence:**
- Different validation in different flows
- Validators aren't used consistently
- Tests for validators ≠ tests for services

---

## Decision: New Backend Structure

### Proposed Layout

```
backend/
│
├── api/                          ← ALL HTTP/GraphQL endpoints
│   ├── __init__.py
│   ├── graphql/
│   │   ├── __init__.py
│   │   ├── schema.py             (Query, Mutation, Subscription root)
│   │   ├── types/                (Strawberry dataclasses, organized by domain)
│   │   │   ├── __init__.py
│   │   │   ├── memory.py         (MemoryType, MemoryConnectionType, etc.)
│   │   │   ├── agent.py          (AgentType, AgentResultType, etc.)
│   │   │   ├── graph.py          (GraphNodeType, GraphRelationType, etc.)
│   │   │   ├── neurotransmitter.py
│   │   │   └── common.py         (Pagination, Error types)
│   │   └── subscriptions/        (NEW: WebSocket subscriptions)
│   │       ├── __init__.py
│   │       └── notifications.py  (onMemoryCreated, etc.)
│   │
│   └── rest/                     (NEW: REST endpoints, renamed from routes/)
│       ├── __init__.py
│       ├── memory.py             (renamed from routes/memory.py)
│       ├── mcp.py                (renamed from routes/mcp.py, may split)
│       └── health.py             (NEW: health check endpoint)
│
├── models/                       (NEW: Domain models + Pydantic schemas)
│   ├── __init__.py
│   ├── base.py                   (BaseModel mixins: timestamp, metadata)
│   ├── memory.py                 (Memory, MemoryCreate, MemoryUpdate, etc.)
│   ├── agent.py                  (Agent, AgentTask, etc.)
│   ├── graph.py                  (GraphNode, GraphRelation, etc.)
│   ├── neurotransmitter.py       (Neurotransmitter, etc.)
│   └── common.py                 (pagination, cursor, etc.)
│
├── exceptions/                   (NEW: Centralized exception hierarchy)
│   ├── __init__.py
│   ├── base.py                   (BaseAGIError, base classes)
│   ├── memory.py                 (MemoryError, MemoryValidationError)
│   ├── agent.py                  (AgentError, AgentTimeoutError)
│   ├── mcp.py                    (MCPError, MCPTimeoutError, MCPConnectionError)
│   ├── graph.py                  (GraphError, GraphValidationError)
│   └── http.py                   (HTTPValidationError for FastAPI)
│
├── validators/                   (CLEANED: Pure validation logic, no models)
│   ├── __init__.py
│   ├── memory_validator.py       (Validation rules: length, format, PII, secrets)
│   └── schema_validator.py       (NEW: GraphQL schema validation)
│
├── services/                     (NO CHANGES: 20+ services continue as-is)
│   ├── memory_service.py
│   ├── graph_service.py
│   ├── agent_service.py
│   ├── ... (all others)
│
├── config/                       (NO CHANGES)
│   ├── settings.py
│   ├── agi_config.py
│
├── core/                         (NO CHANGES)
│   ├── observability.py
│   ├── monitoring.py
│   ├── tracing.py
│
├── agents/                       (NO CHANGES: L1Observer)
│   └── l1_observer/
│
├── jobs/                         (NO CHANGES: RQ jobs)
├── migrations/                   (NO CHANGES: Alembic)
├── scripts/                      (NO CHANGES: Utilities)
├── tests/                        (NO CHANGES: Test suite)
├── static/                       (NO CHANGES: Frontend)
│
└── main.py                       (Updated router assembly)
```

### Key Decisions

#### 1. **api/graphql/types/ over api/graphql/models/**
- **Why:** Strawberry convention (dataclasses are called "types")
- **Benefit:** Clear distinction: API types vs domain models

#### 2. **Single models/ directory (not models-in-services)**
- **Why:** Single source of truth for "what is a Memory?"
- **Benefit:** Services import from models, no duplicates

#### 3. **exceptions/ hierarchy (not scattered)**
- **Why:** Consistent error handling across codebase
- **Benefit:** Routes catch specific exceptions, return proper HTTP codes

#### 4. **api/rest/ (not routes/)**
- **Why:** Clarifies "rest under api" (not parallel to api)
- **Benefit:** api/ becomes the single HTTP/GraphQL entry point

#### 5. **validators/ pure logic (no model definitions)**
- **Why:** Separation of concerns (validation ≠ definition)
- **Benefit:** Can validate any object, test independently

---

## Consequences

### Positive

#### 1. **Clear Paths for New Features**
```
"Add endpoint to search memories"

Before: Create in routes/memory.py? Or api/schema.py? Or both?

After:
- REST: api/rest/memory.py (clear location)
- GraphQL: api/graphql/schema.py + api/graphql/types/memory.py (clear)
- Model: models/memory.py (always here first)
```

#### 2. **No More Import Confusion**
```python
# Before (4 possible locations):
from api.schema import MemoryType
from routes.memory import MemorySearchRequest
from services.memory_service import Memory
from validators.memory_validator import validate_memory

# After (1 location per concern):
from models.memory import MemorySearchRequest, Memory
from api.graphql.types.memory import MemoryType
from exceptions.memory import MemoryValidationError
from validators.memory_validator import validate_memory
```

#### 3. **Services Import Nothing from api/**
```python
# services/memory_service.py
from models.memory import Memory, MemoryCreate  # ✅ No api imports
from exceptions.memory import MemoryValidationError  # ✅ Clean

# This prevents circular dependencies!
```

#### 4. **Consistent Error Handling**
```python
# api/rest/memory.py
from exceptions.memory import MemoryValidationError, MemoryNotFoundError

@router.post("/search")
async def search_memory(req: MemorySearchRequest):
    try:
        results = await memory_service.search(req.query)
    except MemoryValidationError as e:
        return {"error": str(e)}, 400  # Proper HTTP code
    except MemoryNotFoundError as e:
        return {"error": "Not found"}, 404  # Proper HTTP code
```

#### 5. **Easier Testing**
```python
# tests/unit/test_memory_validator.py
from validators.memory_validator import validate_memory
from exceptions.memory import MemoryValidationError

def test_reject_empty_memory():
    with pytest.raises(MemoryValidationError):
        validate_memory("")  # Pure function, no mocks needed!
```

### Negative

#### 1. **Breaking Imports (Mitigated by Phase Approach)**
- Services need import path updates
- Routes need renaming (routes/ → api/rest/)
- **Mitigation:** Incremental, phase-by-phase

#### 2. **Potential Circular Dependencies if Misuse**
- If someone imports api/ from models/ → circular!
- **Mitigation:** Clear import rules in CONTRIBUTING.md
- **Enforcement:** Tests check import hierarchy

#### 3. **More Folders = More Decisions**
- "Is this a model or a schema?" ambiguity possible
- **Mitigation:** Clear definition in CONTRIBUTING.md
- **Enforcement:** Code review guidelines

---

## Migration Strategy (Zero Breaking Changes)

### PHASE A: Create New Folder Structure (No Migration)

**Duration:** 30 minutes  
**Risk:** None (only creates new, doesn't move)

```bash
mkdir -p backend/models
mkdir -p backend/exceptions
mkdir -p backend/api/graphql/types
mkdir -p backend/api/graphql/subscriptions
mkdir -p backend/api/rest

# Add __init__.py files
touch backend/models/__init__.py
touch backend/exceptions/__init__.py
touch backend/exceptions/base.py
# ... etc
```

**No code changes yet!**

---

### PHASE B: Create Exception Hierarchy

**Duration:** 1 hour  
**Risk:** Low (new code, no existing code breaks)

**Action:** Create `/backend/exceptions/`:

1. `base.py` - BaseAGIError hierarchy
2. `memory.py` - MemoryError, MemoryValidationError
3. `agent.py` - AgentError
4. `mcp.py` - Move existing MCPError hierarchy
5. `http.py` - FastAPI-specific exceptions

**Key point:** Leave old exceptions in place for now. New code uses new exceptions.

**Test:** Exception tests in `tests/unit/exceptions/`

---

### PHASE C: Create Model Base Classes

**Duration:** 1 hour  
**Risk:** Low (new code)

**Action:** Create `/backend/models/`:

1. `base.py` - BaseModel, TimestampMixin, MetadataMixin
2. `common.py` - Pagination, CursorMixin, FilterMixin

**Code:**
```python
# backend/models/base.py
from pydantic import BaseModel
from datetime import datetime

class BaseAGIModel(BaseModel):
    """Base for all domain models"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**No breaking changes - new base class, existing models can keep working.**

---

### PHASE D: Extract Pydantic Models (Incremental by Domain)

**Duration:** 2 hours  
**Risk:** Medium (import updates needed)  
**Approach:** One domain at a time

#### D1: Memory Models (Most Used)

1. Extract from `routes/memory.py` → `models/memory.py`
   - MemorySearchRequest
   - MemoryStoreRequest
   - MemorySearchResponse
   - MemoryStatsResponse

2. Update `routes/memory.py` import:
   ```python
   # Before
   from typing import List, Optional
   class MemorySearchRequest(BaseModel):
       query: str

   # After
   from models.memory import MemorySearchRequest
   ```

3. Test: Run `pytest tests/routes/test_memory.py`

#### D2: MCP Models

1. Extract from `routes/mcp.py` → `models/mcp.py`

2. Update imports in `routes/mcp.py`

3. Test: Run `pytest tests/routes/test_mcp.py`

#### D3: Other Domains

Repeat for Agent, Graph, etc. as needed.

**Success Criteria:** All route tests pass, no import changes in services.

---

### PHASE E: Extract Strawberry Types

**Duration:** 2 hours  
**Risk:** Medium (GraphQL schema complexity)  
**Approach:** Organize by domain

**Action:** 

1. Create `api/graphql/types/memory.py`:
   ```python
   # Extract from api/schema.py
   @strawberry.type
   class MemoryType:
       id: str
       content: str
       # ... fields
   ```

2. Create `api/graphql/types/agent.py`, etc.

3. Update `api/schema.py` imports:
   ```python
   from api.graphql.types.memory import MemoryType
   from api.graphql.types.agent import AgentType
   ```

4. Clean `api/schema.py` (focus on Query/Mutation/Subscription)

**Success Criteria:** 
- `api/schema.py` < 500 lines (from 1766)
- GraphQL tests pass
- No schema regressions

---

### PHASE F: Rename routes/ → api/rest/

**Duration:** 1.5 hours  
**Risk:** Medium (path changes)  
**Approach:** Atomic rename

**Action:**

1. Rename files:
   ```bash
   mv backend/routes/memory.py backend/api/rest/memory.py
   mv backend/routes/mcp.py backend/api/rest/mcp.py
   ```

2. Update `backend/routes/__init__.py` (if it re-exports):
   ```python
   # Was: from .memory import router
   # Now:
   from ..api.rest.memory import router
   ```

3. Update `main.py`:
   ```python
   # Before
   from routes import memory_router, mcp_router

   # After
   from api.rest.memory import router as memory_router
   from api.rest.mcp import router as mcp_router
   ```

4. Test: Full integration test

5. Delete old `routes/` folder once all imports updated

**Success Criteria:**
- All routes still work
- Import paths updated everywhere
- API tests pass

---

### PHASE G: Update Validators (Remove Model Definitions)

**Duration:** 1 hour  
**Risk:** Low (cleanup)

**Action:**

1. Remove model definitions from `validators/memory_validator.py`
   ```python
   # Remove: class ValidationResult(BaseModel)
   # These now live in models/
   ```

2. Keep only pure validation logic:
   ```python
   def validate_memory_content(content: str) -> ValidationResult:
       """Pure function, no Pydantic involved"""
   ```

3. Update validators imports to use models:
   ```python
   from models.memory import ValidationResult  # Not defined here
   from exceptions.memory import MemoryValidationError
   ```

**Success Criteria:**
- Validators are pure functions
- All validator tests pass
- No Pydantic definitions in validators/

---

### PHASE H: Final Cleanup

**Duration:** 30 minutes

**Action:**

1. Delete old `routes/` folder (confirmed empty)
2. Delete `api/agi_schema.py` if unused
3. Update documentation (CONTRIBUTING.md)
4. Add import rules to avoid circular deps

**Success Criteria:**
- All tests pass
- No import errors
- Backend structure matches new layout

---

## Import Rules (After Migration)

**ALLOWED:**
```
main.py
  ↓
config/, core/, jobs/
  ↓
api/, services/, validators/
  ↓
models/, exceptions/
```

**NOT ALLOWED:**
```
❌ models/ importing from services/
❌ exceptions/ importing from api/
❌ api/graphql/schema.py importing from api/rest/
```

**Enforcement:**
```bash
# Check for import violations
python -m pydeps backend/ --max-bacon 2 --show-cycle
```

---

## Testing Strategy

### Unit Tests (New)
```
tests/unit/models/
tests/unit/exceptions/
tests/unit/validators/
```

### Integration Tests (Updated)
```
tests/integration/api/rest/
tests/integration/api/graphql/
```

### Full Suite
```bash
pytest tests/ -v --cov=backend
```

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| **Models files** | 7+ scattered | 1 (models/) |
| **Exception definitions** | 3 locations | 1 (exceptions/) |
| **GraphQL types lines** | 1766 in schema.py | ~400 (split across files) |
| **api/schema.py lines** | 1766 | < 500 |
| **Circular import risks** | HIGH | NONE |
| **Developer onboarding time** | "Where do I add code?" | "Follow pattern in models/" |

---

## Timeline

| Phase | Effort | Risk | Duration |
|-------|--------|------|----------|
| A: Create folders | 30 min | None | **0.5h** |
| B: Exception hierarchy | 1h | Low | **1h** |
| C: Base models | 1h | Low | **1h** |
| D: Extract Pydantic | 2h | Medium | **2h** |
| E: Extract Strawberry | 2h | Medium | **2h** |
| F: Rename routes/ | 1.5h | Medium | **1.5h** |
| G: Clean validators | 1h | Low | **1h** |
| H: Final cleanup | 30 min | Low | **0.5h** |
| **TOTAL** | **9 hours** | **Low** | **9 hours (~1 day)** |

---

## Alternatives Considered

### Option 1: Keep Current Structure
**Why rejected:**
- Confusion persists (api/ vs routes/)
- Models remain scattered
- Import issues continue
- Scaling harder as codebase grows

### Option 2: models/ in services/
**Why rejected:**
- Services are business logic, not domain
- Makes services heavier (harder to test)
- Models should be importable without service init

### Option 3: Single flat services/ folder for models
**Why rejected:**
- Mixes models with logic (hard to find)
- services/ already has 20+ files
- Violates separation of concerns

### Option 4: Complete rewrite from scratch
**Why rejected:**
- Risky (zero-breaking requirement)
- Slow (1-2 weeks vs 1 day)
- Unnecessary (incremental works fine)

---

## Open Questions

1. **Should validators/ have model validation decorators?**
   - Answer: No, pure functions only. Pydantic validators in models/base.py

2. **Should api/rest use request.app.state or dependency injection?**
   - Answer: Keep current (request.app.state) for now, refactor later if needed

3. **GraphQL subscriptions split or in schema.py?**
   - Answer: Split to api/graphql/subscriptions/ for clarity

4. **Should old routes/ be deleted immediately?**
   - Answer: No, wait until all imports updated + tests pass

---

## CONTRIBUTING.md Updates

```markdown
## Backend Structure

### Adding a New Feature

1. **Define Domain Model**
   ```
   backend/models/my_entity.py
   - MyEntity (Pydantic model)
   - MyEntityCreate, MyEntityUpdate
   ```

2. **Define API Types** (if GraphQL)
   ```
   backend/api/graphql/types/my_entity.py
   - MyEntityType (Strawberry)
   ```

3. **Add REST Endpoint** (if needed)
   ```
   backend/api/rest/my_entity.py
   - @router.get("/api/my-entity/{id}")
   ```

4. **Implement Service**
   ```
   backend/services/my_entity_service.py
   - Imports: models.my_entity, exceptions.my_entity
   ```

5. **Add Validation**
   ```
   backend/validators/my_entity_validator.py
   - Pure validation logic
   ```

### Import Rules

ALLOWED:
- ✅ services/ → models/
- ✅ api/ → models/, exceptions/
- ✅ validators/ → models/, exceptions/

FORBIDDEN:
- ❌ models/ → services/
- ❌ exceptions/ → anything
- ❌ api/rest/ → api/graphql/
```

---

## References

- ADR-0001: Safe Backend Restructuring (Phase 1)
- Audit: 26 Issues Found (Oct 2025)
- FastAPI Best Practices: https://fastapi.tiangolo.com/
- GraphQL Type System: https://strawberry.rocks/
- Pydantic Docs: https://docs.pydantic.dev/

---

**Version:** 1.0  
**Created:** 2025-10-20  
**Supersedes:** None  
**Superseded by:** (none yet)
