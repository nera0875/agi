---
name: python-fastapi-conventions
description: FastAPI routing structure, Pydantic models, error handling, project layout patterns for backend implementations
---

**Pattern**: FastAPI backend standard structure following async/await patterns.

**Usage**: Implementing FastAPI routes, models, validation, project initialization.

**Instructions**:
- Use `FastAPI()` instance in `main.py`
- Organize routes in `routers/` directory with APIRouter
- Define Pydantic models in `models/` with validation
- Use `schemas/` for request/response DTOs
- Implement error handling with HTTPException(status_code, detail)
- Use async def for all endpoints (async-first)
- Add type hints on all functions

**Structure**:
```
backend/
├── main.py
├── routers/
│   ├── users.py
│   └── items.py
├── models/
│   └── user.py
└── schemas/
    └── user_schema.py
```

**Example Error Handling**:
```python
from fastapi import HTTPException

@app.get("/items/{id}")
async def get_item(id: int):
    if not found:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```
