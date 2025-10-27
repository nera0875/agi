---
name: backend-config-patterns
description: Environment variables, database async connections, structured logging, Docker containerization patterns
---

**Pattern**: Configuration management with Settings class, async DB pools, structured logging.

**Usage**: Setting up environment configs, database connections, logging, Docker containers.

**Instructions**:
- Use `pydantic-settings.Settings` for configuration
- Load `.env` files via `dotenv` library
- Implement async SQLAlchemy engine with connection pooling
- Use structured logging (structlog or python logging with JSON)
- Create Dockerfile with multi-stage builds
- Use docker-compose.yml for local development

**Config Pattern**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

**Logging Pattern**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Event", extra={"user_id": id})
```

**Database Pattern**:
```python
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine(url, echo=False, pool_size=10)
```
