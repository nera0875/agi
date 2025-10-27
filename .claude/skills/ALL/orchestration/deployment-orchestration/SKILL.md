---
name: deployment-orchestration
description: Complete reference for Docker, CI/CD, environment config, logging/monitoring, database migrations
type: documentation
---

# Deployment Orchestration

## Overview

Production deployment patterns covering Docker multi-stage builds, environment variable strategies, GitHub Actions CI/CD, structured logging and monitoring, database migration orchestration.

## Docker Multi-Stage Builds

### Python Backend Dockerfile
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install --user --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /root/.local /root/.local

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Node.js Frontend Dockerfile
```dockerfile
# Stage 1: Builder
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:18-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY package*.json ./
RUN npm ci --only=production

EXPOSE 3000
CMD ["npm", "start"]
```

### Docker Compose
```yaml
version: '3.9'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "${DB_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Environment Variables Strategy

### .env File Structure
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30

# Authentication
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://example.com

# External Services
SENDGRID_API_KEY=sg_xxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Environment Detection
ENVIRONMENT=development
DEBUG=false
```

### Environment Loading in Python
```python
from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Environment Loading in Node.js
```javascript
// config.js
require('dotenv').config();

const config = {
  database: {
    url: process.env.DATABASE_URL,
    pool: parseInt(process.env.DB_POOL_SIZE || '20'),
  },
  jwt: {
    secret: process.env.SECRET_KEY,
    algorithm: process.env.JWT_ALGORITHM || 'HS256',
    expiresIn: parseInt(process.env.JWT_EXPIRATION_HOURS || '24') + 'h',
  },
  cors: {
    origins: (process.env.CORS_ORIGINS || 'http://localhost:3000').split(','),
  },
  environment: process.env.ENVIRONMENT || 'development',
  debug: process.env.DEBUG === 'true',
};

module.exports = config;
```

## CI/CD Patterns (GitHub Actions)

### Basic Workflow
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        run: pytest --cov=src tests/

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Build and Deploy
```yaml
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

## Logging + Monitoring

### Structured Logging with ELK Stack
```python
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage
logger.info("User action", extra={"user_id": 123})
```

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Middleware
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)

    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Database Migrations Deployment

### Alembic Migration Strategy
```bash
# Initialize migrations directory
alembic init alembic

# Create migration (auto-generate)
alembic revision --autogenerate -m "Add users table"

# Create migration (manual)
alembic revision -m "Custom migration"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Show current revision
alembic current

# Show history
alembic history --verbose
```

### Migration Management in CI/CD
```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
          SECRET_KEY: ${{ secrets.PROD_SECRET_KEY }}
        run: |
          # Run migrations
          alembic upgrade head
          # Deploy application
          docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          docker-compose -f docker-compose.prod.yml up -d
```

### Migration Health Checks
```python
async def health_check():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/health")
async def get_health():
    return await health_check()
```

## Integration Checklist

- [ ] Docker multi-stage builds configured
- [ ] Docker Compose for local development
- [ ] .env files properly structured
- [ ] Environment loading in backend (Python/Node)
- [ ] Environment loading in frontend (React)
- [ ] GitHub Actions workflow for tests
- [ ] GitHub Actions workflow for build
- [ ] GitHub Actions workflow for deploy
- [ ] Container registry setup (GHCR/DockerHub)
- [ ] Secrets configured in GitHub
- [ ] JSON logging formatter implemented
- [ ] Prometheus metrics configured
- [ ] Health check endpoints created
- [ ] Alembic migrations initialized
- [ ] Database migration in CI/CD
- [ ] Monitoring dashboard configured (Grafana)
- [ ] Log aggregation setup (ELK/DataDog)
- [ ] Production secrets management
