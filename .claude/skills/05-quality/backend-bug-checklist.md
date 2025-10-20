---
name: backend-bug-checklist
category: quality
type: checklist
tags: [backend, python, fastapi, debugging, errors]
complexity: beginner
---

# Backend Bug Checklist - Python/FastAPI

Checklist rapide pour diagnostiquer bugs backend.

## Exception/500 Errors

```markdown
### When: Exception or HTTP 500 error

- [ ] **Logs**
  - [ ] Read full stacktrace in /tmp/backend.log
  - [ ] Check last 50 lines: `tail -50 /tmp/backend.log`
  - [ ] Grep error message: `grep "ExceptionName" /tmp/backend.log`

- [ ] **Imports**
  - [ ] Module exists: `python -c "from module import *"`
  - [ ] No circular imports: `grep -n "from.*import" file.py`
  - [ ] All deps installed: `pip list | grep package`

- [ ] **Types**
  - [ ] Type hints correct: `mypy file.py`
  - [ ] None checks: `if var is None: ...`
  - [ ] List index bounds: Check range(len(list))

- [ ] **Async/Await**
  - [ ] Function decorated @app.route / @app.post: Check
  - [ ] Async function called with await: `await func()`
  - [ ] No missing await keywords
  - [ ] Event loop running: `pytest -v tests/`

- [ ] **Database**
  - [ ] Connection active: `psql -c "SELECT 1"`
  - [ ] Credentials correct: Check .env DATABASE_URL
  - [ ] Session committed: `session.commit()`
  - [ ] No transaction lock: `SELECT * FROM pg_locks`

- [ ] **External APIs**
  - [ ] API endpoint reachable: `curl http://api.example.com`
  - [ ] Credentials passed: Check headers/params
  - [ ] Response parsing: Check response.json()
```

---

## Database Connection Errors

```markdown
### When: "ConnectionError", "Database connection refused"

- [ ] **PostgreSQL Running**
  - [ ] Check status: `sudo systemctl status postgresql`
  - [ ] Start if down: `sudo systemctl start postgresql`
  - [ ] Connect test: `psql -U agi_user -d agi_db -c "SELECT 1"`

- [ ] **Connection String**
  - [ ] URL format: `postgresql://user:pass@host:5432/db`
  - [ ] Check .env file: `echo $DATABASE_URL`
  - [ ] User exists: `psql -c "\du"` (list users)
  - [ ] Database exists: `psql -c "\l"` (list databases)

- [ ] **Permissions**
  - [ ] User has permissions: `psql -c "GRANT ALL ON DATABASE agi_db TO agi_user"`
  - [ ] pg_hba.conf allows: Check `/etc/postgresql/*/main/pg_hba.conf`

- [ ] **Connection Pool**
  - [ ] Pool exhausted: Check active connections
  - [ ] Connections not closed: Look for missing `session.close()`
  - [ ] Max pool size: Increase if needed: `pool_size=20`

- [ ] **Network**
  - [ ] Host reachable: `ping hostname`
  - [ ] Port open: `nc -zv hostname 5432`
  - [ ] Firewall rules: `sudo ufw status`
```

---

## Async/Concurrency Issues

```markdown
### When: Intermittent failures, "Event loop" errors, race conditions

- [ ] **Event Loop**
  - [ ] Running in async context: Check @app.on_event("startup")
  - [ ] Not calling sync blocking code: Use threadpool if needed
  - [ ] No nested loops: `asyncio.run()` only once

- [ ] **Race Conditions**
  - [ ] Use locks for shared state: `async with self.lock: ...`
  - [ ] Database unique constraints: Check schema
  - [ ] Test with pytest-asyncio

- [ ] **Timeouts**
  - [ ] Set reasonable timeouts: `asyncio.wait_for(coro, timeout=30)`
  - [ ] Check external API timeouts: `httpx.AsyncClient(timeout=30)`

- [ ] **Task Management**
  - [ ] Tasks properly awaited: `await asyncio.gather(*tasks)`
  - [ ] No dangling tasks: Check no unawaited futures
```

---

## Memory/Performance Issues

```markdown
### When: Slow API, high memory, OOM crashes

- [ ] **Memory Leaks**
  - [ ] Cache has TTL: `TTLCache(maxsize=1000, ttl=3600)`
  - [ ] No infinite lists growing: Check loops
  - [ ] Circular references broken: Use weak refs if needed
  - [ ] Profile: `python -m memory_profiler script.py`

- [ ] **Slow Queries**
  - [ ] Query logged: Check query in logs
  - [ ] Analyze query plan: `EXPLAIN ANALYZE SELECT ...`
  - [ ] Missing index: Check indexed columns in WHERE
  - [ ] N+1 queries: Use joinedload() or batch queries
  - [ ] Profile: `python -m cProfile -s cumulative script.py`

- [ ] **Large Data Processing**
  - [ ] Streaming instead of loading all: Use generators
  - [ ] Batch operations: Process 1000 at a time not 1M
  - [ ] Database pagination: LIMIT 1000 OFFSET
  - [ ] Lazy loading: Use SQLAlchemy .all() sparingly

- [ ] **Resource Cleanup**
  - [ ] Files closed: `with open(...) as f:`
  - [ ] Connections returned: `session.close()`
  - [ ] Threads joined: `thread.join()`
```

---

## Request/Response Issues

```markdown
### When: "Bad Request", "400", "422 Unprocessable Entity"

- [ ] **Input Validation**
  - [ ] Schema defined: Check Pydantic model
  - [ ] Required fields present: Check in request body
  - [ ] Types correct: `mypy` check models
  - [ ] Example: `curl -d '{"field":"value"}' ...`

- [ ] **Content Type**
  - [ ] Header set: `-H "Content-Type: application/json"`
  - [ ] Request body valid JSON: Try `python -m json.tool`

- [ ] **Route Path**
  - [ ] URL correct: Check @app.post("/path")
  - [ ] Path params: If `/api/memory/{id}` check in URL
  - [ ] Query params: If `?type=short` check parsing

- [ ] **Authentication**
  - [ ] Token provided: Check Authorization header
  - [ ] Token valid: Check token creation and expiry
  - [ ] Token format: "Bearer TOKEN" not just TOKEN
  - [ ] Route protected: Check @app.post security parameter
```

---

## GraphQL Issues

```markdown
### When: GraphQL query fails, null response, type errors

- [ ] **Schema Definition**
  - [ ] Field defined in schema: Check schema.py
  - [ ] Type correct: scalar vs object vs enum
  - [ ] Non-null: `field: String!` vs `field: String`

- [ ] **Resolver Implementation**
  - [ ] Resolver exists: `@strawberry.field` decorator
  - [ ] Function returns correct type
  - [ ] No exceptions in resolver: Add try-catch if needed
  - [ ] Database query correct: Manually test

- [ ] **Query Syntax**
  - [ ] Query valid: Try in GraphQL playground
  - [ ] Fields exist: Match schema exactly
  - [ ] Variables types: Must match schema

- [ ] **Data Flow**
  - [ ] DB returns data: Test with psql directly
  - [ ] Resolver receives data: Add logging
  - [ ] Response type matches: Check serialization
```

---

## Dependency/Import Issues

```markdown
### When: "ImportError", "ModuleNotFoundError", "No module named"

- [ ] **Module Installed**
  - [ ] Listed in requirements.txt: Check file
  - [ ] Installed: `pip list | grep package`
  - [ ] Version correct: `pip show package`

- [ ] **Python Path**
  - [ ] Project root in path: Check sys.path
  - [ ] __init__.py exists: In each package folder
  - [ ] Relative imports: Use `from ..package import`

- [ ] **Circular Imports**
  - [ ] Import chain: `grep -r "from X import Y"`
  - [ ] Late import: Import in function, not module
  - [ ] Refactor: Move to common module

- [ ] **Version Conflicts**
  - [ ] Dep versions: `pip freeze | grep package`
  - [ ] Lock file: requirements.lock up to date
  - [ ] Compatibility: Check package changelog
```

---

## Authentication/Authorization

```markdown
### When: "Unauthorized", "403 Forbidden", auth fails

- [ ] **Token Generation**
  - [ ] Token created correctly: Check JWT creation
  - [ ] Secret key used: Check SECRET_KEY in config
  - [ ] Expiry set: Not permanent tokens

- [ ] **Token Validation**
  - [ ] Token present in request: Check Authorization header
  - [ ] Token not expired: Check exp claim
  - [ ] Signature valid: Check secret used matches

- [ ] **Permissions**
  - [ ] User role checked: Check authorize() function
  - [ ] Database role stored: Check user.role column
  - [ ] Endpoint protected: Check @app.post(security=...)

- [ ] **CORS/CSP**
  - [ ] Origin allowed: Check CORS headers
  - [ ] Credentials sent: Check withCredentials: true
  - [ ] Headers allowed: Check Access-Control-Allow-Headers
```

---

## Error Handling Pattern

### Template for Debugging Any Backend Error

```markdown
### SYMPTOM
[What user sees/error message]

### 1. LOCATE
- Grep error in logs
- Identify file and line number
- Read code context (10 lines before/after)

### 2. CLASSIFY
Type of error:
- [ ] Import/Syntax
- [ ] Type/Runtime
- [ ] Database/Connection
- [ ] Async/Concurrency
- [ ] External API
- [ ] Authentication
- [ ] Input validation

### 3. GATHER INFO
- [ ] Full stacktrace
- [ ] Input values
- [ ] Database state
- [ ] Log timestamps
- [ ] Environment (dev/prod)

### 4. HYPOTHESIZE
Most likely causes:
1. [H1] - Probability 60%
2. [H2] - Probability 25%
3. [H3] - Probability 15%

### 5. TEST
```bash
# For H1
python -c "code to test hypothesis 1"

# For H2
mypy module.py

# For H3
pytest tests/test_feature.py -v
```

### 6. FIX
Edit file, apply fix, document

### 7. VALIDATE
```bash
pytest tests/ --cov=backend -v
curl http://localhost:8000/api/endpoint
```
```

---

## Checklist Before Deploying

```markdown
- [ ] No "TODO" comments left
- [ ] No hardcoded values (use .env)
- [ ] All tests pass: `pytest --cov=backend`
- [ ] Type check passes: `mypy backend/`
- [ ] Linting passes: `pylint backend/`
- [ ] Logs don't expose secrets
- [ ] Error messages user-friendly (no stack traces)
- [ ] Database migrations applied
- [ ] Secrets not in git (check .gitignore)
- [ ] API docs updated (if applicable)
```
