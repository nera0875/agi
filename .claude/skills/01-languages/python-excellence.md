---
name: Python Excellence
description: Python type hints, async patterns, FastAPI best practices, and professional code organization
category: languages
language: python
version: 1.0
---

## Type Hints (Mandatory)

All Python functions must have explicit type hints:

```python
# ✅ CORRECT
def get_memory(key: str) -> dict[str, Any]:
    """Retrieve memory by key."""
    pass

async def fetch_data(url: str) -> list[dict]:
    """Fetch and parse data."""
    pass

# ❌ WRONG
def get_memory(key):
    pass

def fetch_data(url):
    pass
```

## Async/Await for I/O

Always use async/await for I/O operations:

```python
# ✅ CORRECT
async def query_database(query: str) -> list[dict]:
    """Query database asynchronously."""
    async with self.db_pool.acquire() as conn:
        return await conn.fetch(query)

# ❌ WRONG
def query_database(query: str) -> list[dict]:
    return blocking_db_query(query)
```

## FastAPI Best Practices

### Structure
- **Routes** → FastAPI endpoints (request/response handling)
- **Services** → Business logic (pure functions)
- **Models** → SQLAlchemy DB models
- **Schemas** → Pydantic validation schemas

```python
# api/rest/memory.py - Route layer
from fastapi import APIRouter, Depends
from services.memory_service import MemoryService

router = APIRouter(prefix="/memory")

@router.get("/{key}")
async def get_memory(key: str, service: MemoryService = Depends()) -> dict:
    return await service.retrieve(key)

# services/memory_service.py - Business logic
class MemoryService:
    async def retrieve(self, key: str) -> dict:
        """Pure business logic."""
        pass
```

## Python Naming Conventions

### Files
- **snake_case**: `memory_service.py`, `graph_operations.py`
- Never PascalCase for Python files

### Classes
- **PascalCase**: `class MemoryService`, `class GraphAnalyzer`

### Functions/Methods
- **snake_case**: `def get_memory()`, `async def fetch_embeddings()`

### Constants
- **UPPER_SNAKE_CASE**: `MAX_RETRIES = 3`, `API_TIMEOUT = 30`

## Imports Organization

Organize imports in this exact order:

```python
# 1. Standard library
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# 2. Third party
from fastapi import FastAPI, Depends
from sqlalchemy import Column, Integer
from pydantic import BaseModel

# 3. Local
from app.services.memory_service import MemoryService
from app.core.config import settings

# ❌ NEVER use wildcard imports
# from app.services import *  # FORBIDDEN
```

## Error Handling

Use explicit error handling:

```python
# ✅ CORRECT
try:
    result = await fetch_embeddings(text)
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise HTTPException(status_code=503)

# ❌ WRONG
try:
    result = await fetch_embeddings(text)
except:
    pass
```

## Logging (Not Print)

Always use logging, never `print()`:

```python
# ✅ CORRECT
import logging
logger = logging.getLogger(__name__)
logger.info("Processing memory")

# ❌ WRONG
print("Processing memory")
```

## Docstrings

Add docstrings to all public functions:

```python
async def store_memory(key: str, value: dict) -> bool:
    """Store memory in L1 cache.

    Args:
        key: Memory key identifier
        value: Memory data to store

    Returns:
        True if successful, False otherwise
    """
    pass
```

## Project Structure

Strict backend structure:

```
backend/
├── api/              # All endpoints
│   ├── graphql/      # GraphQL schemas
│   └── rest/         # FastAPI routes
├── services/         # Business logic (always)
├── models/           # SQLAlchemy DB models
├── schemas/          # Pydantic validation
├── core/             # Config, dependencies
├── utils/            # Utilities (organized)
├── agents/           # LangGraph agents
├── migrations/       # Alembic only
├── tests/            # Tests (mirror structure)
└── main.py           # Entry point
```

## Testing

Create tests mirroring source structure:

```
backend/
  services/memory_service.py

tests/
  services/test_memory_service.py
```

Use pytest:
```python
@pytest.mark.asyncio
async def test_retrieve_memory():
    service = MemoryService()
    result = await service.retrieve("key1")
    assert result is not None
```

## Key Rules Summary

- ✅ Type hints everywhere
- ✅ Async/await for I/O
- ✅ Layer separation (routes → services → models)
- ✅ Explicit imports (no wildcards)
- ✅ Error handling with try/except
- ✅ Logging, not print()
- ✅ Structure first, code second
- ✅ Tests mirror source structure
