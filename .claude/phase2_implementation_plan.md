# PHASE 2: BACKEND STRUCTURE - IMPLEMENTATION PLAN

**Status:** ADR Approved - Ready for agents  
**ADR Reference:** `/home/pilote/projet/agi/docs/adr/ADR-0002-backend-folder-structure.md`  
**Timeline:** 1-2 days (9 hours work)  
**Agents:** code, frontend, debug  

---

## QUICK REFERENCE

**What we're doing:** Reorganizing backend folders from confused structure to clear 5-layer architecture.

**Why:** Developers confused about where to add code. Models duplicated in 5 places. No exception hierarchy.

**How:** 8 incremental phases. Each tested. No breaking changes.

**Result:** Clear backend structure. Single source of truth. Safe to scale.

---

## PHASE A: Create Folder Structure

**Duration:** 30 minutes  
**Agent:** code  
**Risk:** None  

**Task:**
```bash
mkdir -p backend/models
mkdir -p backend/exceptions
mkdir -p backend/api/graphql/types
mkdir -p backend/api/graphql/subscriptions
mkdir -p backend/api/rest

touch backend/models/__init__.py
touch backend/exceptions/__init__.py
touch backend/api/graphql/__init__.py
touch backend/api/graphql/types/__init__.py
touch backend/api/graphql/subscriptions/__init__.py
touch backend/api/rest/__init__.py
```

**Validation:**
```bash
pytest tests/ -xvs  # Should all still pass
python -m pydeps backend/ --max-bacon 2 --show-cycle  # No cycles
```

**Commit Message:**
```
feat(architecture): Create Phase 2 folder structure

- Add backend/models/ (domain models + schemas)
- Add backend/exceptions/ (exception hierarchy)
- Add backend/api/graphql/types/ (Strawberry types by domain)
- Add backend/api/graphql/subscriptions/ (WebSocket subscriptions)
- Add backend/api/rest/ (REST endpoints location)

All new folders have __init__.py stubs. No code changes yet.
```

**Success Criteria:**
- [ ] All 5 new folders created
- [ ] All __init__.py files created
- [ ] Existing tests still pass
- [ ] No circular imports

---

## PHASE B: Create Exception Hierarchy

**Duration:** 1 hour  
**Agent:** code  
**Risk:** Low  

**Create:** `backend/exceptions/base.py`

```python
"""
Base exception hierarchy for AGI system

Enables consistent error handling and proper HTTP status codes
"""

class BaseAGIError(Exception):
    """Root exception for all AGI errors"""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or "AGI_ERROR"
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message
        }


class ValidationError(BaseAGIError):
    """Validation failed"""
    
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(BaseAGIError):
    """Resource not found"""
    
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND")


class ConflictError(BaseAGIError):
    """Resource conflict (e.g., duplicate)"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT")
```

**Create:** `backend/exceptions/memory.py`

```python
"""Memory system exceptions"""

from .base import BaseAGIError, ValidationError

class MemoryError(BaseAGIError):
    """Memory system error"""
    pass

class MemoryValidationError(ValidationError):
    """Memory validation failed"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.code = "MEMORY_VALIDATION_ERROR"

class MemoryNotFoundError(BaseAGIError):
    """Memory not found"""
    
    def __init__(self, memory_id: str):
        super().__init__(f"Memory {memory_id} not found", "MEMORY_NOT_FOUND")
```

**Create:** `backend/exceptions/agent.py`

```python
"""Agent system exceptions"""

from .base import BaseAGIError

class AgentError(BaseAGIError):
    """Agent error"""
    pass

class AgentTimeoutError(AgentError):
    """Agent execution timeout"""
    
    def __init__(self, agent_id: str):
        super().__init__(f"Agent {agent_id} timeout", "AGENT_TIMEOUT")
```

**Create:** `backend/exceptions/mcp.py`

```python
"""MCP (Model Context Protocol) exceptions"""

from .base import BaseAGIError

class MCPError(BaseAGIError):
    """MCP error"""
    pass

class MCPTimeoutError(MCPError):
    """MCP operation timeout"""
    
    def __init__(self, operation: str):
        super().__init__(f"MCP operation '{operation}' timeout", "MCP_TIMEOUT")

class MCPConnectionError(MCPError):
    """MCP connection error"""
    
    def __init__(self, server: str):
        super().__init__(f"Failed to connect to MCP server: {server}", "MCP_CONNECTION_ERROR")
```

**Create:** `backend/exceptions/graph.py`

```python
"""Graph system exceptions"""

from .base import BaseAGIError

class GraphError(BaseAGIError):
    """Graph error"""
    pass

class GraphValidationError(GraphError):
    """Graph validation failed"""
    
    def __init__(self, message: str):
        super().__init__(message, "GRAPH_VALIDATION_ERROR")
```

**Create:** `backend/exceptions/__init__.py`

```python
"""Exception hierarchy - centralized error handling"""

from .base import BaseAGIError, ValidationError, NotFoundError, ConflictError
from .memory import MemoryError, MemoryValidationError, MemoryNotFoundError
from .agent import AgentError, AgentTimeoutError
from .mcp import MCPError, MCPTimeoutError, MCPConnectionError
from .graph import GraphError, GraphValidationError

__all__ = [
    "BaseAGIError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "MemoryError",
    "MemoryValidationError",
    "MemoryNotFoundError",
    "AgentError",
    "AgentTimeoutError",
    "MCPError",
    "MCPTimeoutError",
    "MCPConnectionError",
    "GraphError",
    "GraphValidationError",
]
```

**Validation:**
```python
# Test imports work
from backend.exceptions import MemoryValidationError, MCPTimeoutError
pytest tests/unit/exceptions/ -xvs
```

**Commit Message:**
```
feat(exceptions): Create centralized exception hierarchy

- BaseAGIError (root, with to_dict() for API responses)
- ValidationError, NotFoundError, ConflictError (base types)
- Domain-specific: MemoryError, AgentError, MCPError, GraphError
- All inherit from BaseAGIError for consistent handling

Enables:
- Proper HTTP status codes (400 for validation, 404 for not found, etc.)
- Consistent error responses with code + message
- Exception hierarchy for catching/re-raising
```

**Success Criteria:**
- [ ] All exception files created
- [ ] Exception hierarchy tests pass
- [ ] Can import all exceptions
- [ ] to_dict() works on all exceptions

---

## PHASE C: Create Base Model Classes

**Duration:** 1 hour  
**Agent:** code  
**Risk:** Low  

**Create:** `backend/models/base.py`

```python
"""
Base model classes for all domain objects

Provides:
- Timestamp tracking (created_at, updated_at)
- Metadata dictionary
- JSON encoding
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class BaseAGIModel(BaseModel):
    """Base model for all domain objects"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    def to_dict(self):
        return self.dict()


class TimestampMixin:
    """Mixin for timestamped objects"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MetadataMixin:
    """Mixin for metadata support"""
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

**Create:** `backend/models/common.py`

```python
"""Common models used across domains"""

from pydantic import BaseModel, Field
from typing import List, Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar('T')

class PaginationInput(BaseModel):
    """Pagination parameters"""
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CursorPaginationInput(BaseModel):
    """Cursor-based pagination"""
    limit: int = Field(default=10, ge=1, le=100)
    cursor: Optional[str] = None  # Base64 encoded


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int
    limit: int
    offset: int
    has_more: bool


class CursorPaginationMeta(BaseModel):
    """Cursor pagination metadata"""
    limit: int
    cursor: Optional[str]  # Next cursor
    has_more: bool


class PagedResponse(BaseModel, Generic[T]):
    """Generic paged response"""
    items: List[T]
    meta: PaginationMeta
```

**Create:** `backend/models/__init__.py`

```python
"""Domain models - single source of truth for data structures"""

from .base import BaseAGIModel, TimestampMixin, MetadataMixin
from .common import (
    PaginationInput,
    CursorPaginationInput,
    PaginationMeta,
    CursorPaginationMeta,
    PagedResponse,
)

__all__ = [
    "BaseAGIModel",
    "TimestampMixin",
    "MetadataMixin",
    "PaginationInput",
    "CursorPaginationInput",
    "PaginationMeta",
    "CursorPaginationMeta",
    "PagedResponse",
]
```

**Validation:**
```python
from backend.models import BaseAGIModel, PaginationInput
pytest tests/unit/models/ -xvs
```

**Commit Message:**
```
feat(models): Create base model classes

- BaseAGIModel (timestamp tracking, metadata, JSON encoding)
- TimestampMixin, MetadataMixin for composition
- PaginationInput, CursorPaginationInput for consistency
- PaginationMeta, CursorPaginationMeta for responses
- Common types for reuse across domains
```

**Success Criteria:**
- [ ] base.py and common.py created
- [ ] BaseAGIModel generates IDs + timestamps
- [ ] Pagination models work
- [ ] Can inherit from BaseAGIModel

---

## PHASE D: Extract Pydantic Models

**Duration:** 2 hours  
**Agent:** code  
**Approach:** One domain at a time (start with memory)  

### D1: Memory Models

**Extract from:** `backend/routes/memory.py`  
**Create:** `backend/models/memory.py`

```python
"""Memory domain models"""

from .base import BaseAGIModel
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Request/Response schemas
class MemorySearchRequest(BaseModel):
    """Search memory request"""
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=50)
    type: Optional[str] = None
    project: str = Field(default="default")


class MemoryStoreRequest(BaseModel):
    """Store memory request"""
    text: str = Field(..., min_length=1, max_length=10000)
    type: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    project: str = Field(default="default")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchResponse(BaseModel):
    """Search results response"""
    results: List[Dict[str, Any]]
    count: int
    query: str


class MemoryStoreResponse(BaseModel):
    """Store confirmation response"""
    memory_id: str
    status: str


class MemoryStatsResponse(BaseModel):
    """Memory statistics response"""
    total_memories: int
    memory_types: Dict[str, int]
    total_relations: int
    total_checkpoints: int
    backend: str = "PostgreSQL"
    cache: str = "Redis Stack"


# Domain models
class Memory(BaseAGIModel):
    """Memory domain object"""
    content: str
    source_type: str
    user_id: str
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    relations: List[str] = Field(default_factory=list)


class MemoryCreate(BaseModel):
    """Memory creation schema"""
    content: str = Field(..., min_length=1, max_length=10000)
    source_type: str
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    """Memory update schema"""
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
```

**Update:** `backend/routes/memory.py`

Replace:
```python
class MemorySearchRequest(BaseModel):
    ...
```

With:
```python
from models.memory import (
    MemorySearchRequest,
    MemoryStoreRequest,
    MemorySearchResponse,
    MemoryStoreResponse,
    MemoryStatsResponse,
)
```

**Test:**
```bash
pytest tests/routes/test_memory.py -xvs
```

### D2-D3: Agent, Graph, etc.

Repeat same pattern for other domains as needed.

**Commit Message:**
```
feat(models): Extract Pydantic models to models/memory.py

Moved from routes/memory.py:
- MemorySearchRequest, MemoryStoreRequest
- MemorySearchResponse, MemoryStoreResponse
- MemoryStatsResponse

Added domain models:
- Memory (domain object with BaseAGIModel)
- MemoryCreate, MemoryUpdate (schemas)

Routes now import from models/ instead of defining locally.
```

**Success Criteria:**
- [ ] models/memory.py created
- [ ] routes/memory.py imports from models/
- [ ] All memory route tests pass
- [ ] No import errors

---

## PHASE E: Extract Strawberry Types

**Duration:** 2 hours  
**Agent:** code  

**Extract from:** `backend/api/schema.py` (1766 lines)  
**Create:** `backend/api/graphql/types/memory.py`

```python
"""GraphQL types for memory domain"""

import strawberry
from typing import List, Optional

@strawberry.type
class MemoryType:
    """GraphQL type for Memory object"""
    id: str
    content: str
    source_type: str
    user_id: str
    created_at: str
    updated_at: str
    tags: List[str]
    embedding: Optional[List[float]] = None


@strawberry.type
class MemoryConnectionType:
    """Cursor-based connection for paginated memories"""
    edges: List['MemoryEdgeType']
    page_info: 'PageInfoType'


@strawberry.type
class MemoryEdgeType:
    """Edge in memory connection"""
    cursor: str
    node: MemoryType


@strawberry.type
class PageInfoType:
    """Pagination info"""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
```

**Update:** `backend/api/schema.py`

Replace inline type definitions with imports:
```python
from api.graphql.types.memory import MemoryType, MemoryConnectionType
from api.graphql.types.agent import AgentType
# ... etc
```

**Result:** `api/schema.py` reduces from 1766 to ~200 lines (just Query/Mutation/Subscription)

**Test:**
```bash
pytest tests/api/test_graphql.py -xvs
```

**Commit Message:**
```
feat(graphql): Extract Strawberry types to api/graphql/types/

- Create api/graphql/types/memory.py (MemoryType, MemoryConnectionType, etc.)
- Create api/graphql/types/agent.py (AgentType, etc.) [if applicable]
- Update api/schema.py imports
- Reduce api/schema.py from 1766 to ~200 lines

GraphQL schema now organized by domain.
```

**Success Criteria:**
- [ ] api/graphql/types/ folder has memory.py, agent.py, etc.
- [ ] api/schema.py imports from types/
- [ ] api/schema.py < 500 lines
- [ ] All GraphQL tests pass
- [ ] Schema validation passes

---

## PHASE F: Rename routes/ → api/rest/

**Duration:** 1.5 hours  
**Agent:** code  
**Risk:** Medium  

**Actions:**

1. Move files:
```bash
mv backend/routes/memory.py backend/api/rest/memory.py
mv backend/routes/mcp.py backend/api/rest/mcp.py
```

2. Create health endpoint:
```
backend/api/rest/health.py
```

3. Update `backend/api/rest/__init__.py`:
```python
"""REST endpoints"""

from .memory import router as memory_router
from .mcp import router as mcp_router
from .health import router as health_router

__all__ = ["memory_router", "mcp_router", "health_router"]
```

4. Update `backend/main.py`:

Before:
```python
from routes import memory_router, mcp_router
```

After:
```python
from api.rest import memory_router, mcp_router, health_router
```

5. Test:
```bash
pytest tests/ -xvs
```

6. Delete old `routes/` folder once confirmed all imports updated

**Commit Message:**
```
feat(api): Move routes to api/rest/

- Move routes/memory.py → api/rest/memory.py
- Move routes/mcp.py → api/rest/mcp.py
- Create api/rest/health.py
- Update main.py imports
- Delete old routes/ folder

Clarifies that REST endpoints are under api/, not parallel to it.
```

**Success Criteria:**
- [ ] routes/memory.py moved to api/rest/memory.py
- [ ] routes/mcp.py moved to api/rest/mcp.py
- [ ] main.py imports updated
- [ ] All REST tests pass
- [ ] All routes still work (curl test)

---

## PHASE G: Clean Validators

**Duration:** 1 hour  
**Agent:** code  

**Update:** `backend/validators/memory_validator.py`

Remove:
```python
class ValidationResult(BaseModel):
    is_valid: bool
    score: float = Field(ge=0.0, le=1.0)
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
```

Import instead:
```python
from models.memory import ValidationResult  # or create in models/
from exceptions.memory import MemoryValidationError
```

Keep validation functions pure:
```python
def validate_memory_content(content: str) -> ValidationResult:
    """Pure validation function - no side effects"""
    ...
```

Result: validators/ becomes pure logic without model definitions.

**Commit Message:**
```
refactor(validators): Remove model definitions, keep pure validation

- Move ValidationResult to models/
- Keep validation functions (pure, no models defined)
- Update imports to use models/
- Validators now pure functions (testable without mocks)
```

**Success Criteria:**
- [ ] No Pydantic BaseModel definitions in validators/
- [ ] All validation functions are pure
- [ ] Validator tests pass
- [ ] No import cycles

---

## PHASE H: Final Cleanup

**Duration:** 30 minutes  
**Agent:** code  

**Actions:**

1. Delete old `routes/` folder:
```bash
rm -rf backend/routes/
```

2. Verify `api/agi_schema.py` not used:
```bash
grep -r "agi_schema" backend/ --include="*.py"  # Should be 0 results
```
If unused, delete it too.

3. Update documentation files:
   - Add import rules to CONTRIBUTING.md
   - Update README.md backend section

4. Final validation:
```bash
pytest tests/ -xvs --cov=backend
python -m pydeps backend/ --max-bacon 2 --show-cycle
```

**Commit Message:**
```
chore(cleanup): Complete Phase 2 backend restructuring

- Delete old routes/ folder (migrated to api/rest/)
- Delete agi_schema.py if unused
- Update CONTRIBUTING.md with import rules
- Update README.md with new structure

Backend now follows 5-layer architecture:
- api/ (presentation: GraphQL + REST)
- models/ (domain: Pydantic + base classes)
- exceptions/ (domain: exception hierarchy)
- validators/ (business: pure validation)
- services/ (business: no changes)

All tests passing. No circular imports. Clean DAG.
```

**Success Criteria:**
- [ ] routes/ deleted
- [ ] All tests pass
- [ ] No circular imports
- [ ] CONTRIBUTING.md updated
- [ ] README.md updated

---

## DEBUG VALIDATION (Per Phase)

After each phase, run:

```bash
# Tests
pytest tests/ -xvs --cov=backend

# Circular imports
python -m pydeps backend/ --max-bacon 2 --show-cycle

# Structure check
python scripts/verify_backend_structure.py
```

---

## SUCCESS CHECKLIST

- [ ] Phase A: Folders created (0% code change)
- [ ] Phase B: Exception hierarchy complete
- [ ] Phase C: Base models working
- [ ] Phase D: Pydantic models extracted
- [ ] Phase E: Strawberry types extracted
- [ ] Phase F: Routes renamed to api/rest/
- [ ] Phase G: Validators cleaned
- [ ] Phase H: Old code deleted + docs updated
- [ ] All tests passing
- [ ] No circular imports
- [ ] No breaking changes
- [ ] Backend developers happy

---

## DELEGATION MATRIX

| Phase | Code Agent | Debug Agent | Status |
|-------|-----------|------------|--------|
| A | Create folders | Verify structure | → Ready |
| B | Write exceptions | Test imports | → Ready |
| C | Write base models | Test inheritance | → Ready |
| D | Extract models | Test each domain | → Ready |
| E | Extract types | GraphQL tests | → Ready |
| F | Rename/move | Integration tests | → Ready |
| G | Clean validators | Pure logic tests | → Ready |
| H | Delete + docs | Final validation | → Ready |

---

**Start with Phase A. One phase at a time. Keep testing.** ✅

