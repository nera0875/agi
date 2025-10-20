---
name: diagnostic-tools
category: quality
type: tools-reference
tags: [debugging, tools, profiling, monitoring]
complexity: intermediate
---

# Diagnostic Tools & Commands

Ensemble complet d'outils pour diagnostic, profiling et monitoring du projet.

## Python Debugging Tools

### pdb - Python Debugger

```bash
# Breakpoint dans code
import pdb; pdb.set_trace()

# Ou (Python 3.7+)
breakpoint()

# Commands
(Pdb) n       # Next line
(Pdb) s       # Step into
(Pdb) c       # Continue
(Pdb) l       # List current code
(Pdb) w       # Where (stack trace)
(Pdb) p var   # Print variable
(Pdb) pp dict # Pretty print dict
(Pdb) j 10    # Jump to line 10
```

### ipdb - IPython Debugger (Better)

```bash
pip install ipdb

# In code
import ipdb; ipdb.set_trace()

# Terminal usage
ipython --pdb script.py  # Auto-debug on error
```

### logging - Structured Logging

```python
import logging

# Setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Usage
logger.debug("Variable x = %s", x)
logger.error("Error occurred", exc_info=True)  # With traceback
```

### traceback - Stack Traces

```python
import traceback

try:
    risky_operation()
except Exception as e:
    traceback.print_exc()  # Full stack trace
    print(traceback.format_exc())  # As string
```

### sys.settrace() - Function Tracing

```python
import sys

def tracer(frame, event, arg):
    if event == 'call':
        print(f"Calling {frame.f_code.co_name}")
    return tracer

# Trace all function calls
sys.settrace(tracer)
my_function()
sys.settrace(None)  # Stop tracing
```

---

## Performance Profiling

### cProfile - CPU Profiling

```bash
# Profile script
python -m cProfile -o profile.stats myscript.py

# View results
python -m pstats profile.stats
(pstats) sort cumulative
(pstats) stats 20  # Top 20

# Command line output
python -m cProfile -s cumulative myscript.py | head -30
```

### memory_profiler - Memory Profiling

```bash
pip install memory_profiler

# Mark function
from memory_profiler import profile

@profile
def my_function():
    large_list = [x for x in range(1000000)]

# Run
python -m memory_profiler script.py

# Output shows memory usage per line
```

### line_profiler - Line-by-Line Profiling

```bash
pip install line_profiler

# Mark function
@profile
def slow_function():
    for i in range(1000000):
        x = i ** 2

# Run
kernprof -l -v script.py
```

### tracemalloc - Memory Tracking

```python
import tracemalloc

tracemalloc.start()

# Your code here
data = [i for i in range(1000000)]

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.1f} MB")
print(f"Peak: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

---

## Type Checking

### mypy - Static Type Checker

```bash
pip install mypy

# Check file
mypy script.py

# Strict mode
mypy --strict script.py

# Configuration (mypy.ini)
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

# Run with config
mypy --config-file=mypy.ini backend/
```

### pydantic - Runtime Validation

```python
from pydantic import BaseModel, ValidationError

class Memory(BaseModel):
    content: str
    priority: int  # Must be int
    tags: list[str] = []

# Validation
try:
    mem = Memory(content="test", priority="high")  # Type error
except ValidationError as e:
    print(e.json())
```

---

## Testing & Quality

### pytest - Testing Framework

```bash
# Run all tests
pytest

# Specific file/function
pytest tests/test_memory.py::test_store -v

# With coverage
pytest --cov=backend --cov-report=html

# Verbose output
pytest -vv -s --tb=long

# Parallel execution
pytest -n auto

# Last failures
pytest --lf

# Profile tests
pytest --durations=20
```

### pylint - Code Quality

```bash
pip install pylint

# Analyze
pylint backend/services/memory.py

# Show only errors
pylint backend/services/memory.py --disable=all --enable=E

# Configuration (.pylintrc)
[MESSAGES CONTROL]
disable=
    missing-docstring,
    too-many-arguments

# Run with config
pylint --rcfile=.pylintrc backend/
```

### black - Code Formatter

```bash
pip install black

# Format file
black script.py

# Check without modifying
black --check script.py

# In CI/CD
black --check backend/
```

### flake8 - Linting

```bash
pip install flake8

# Lint
flake8 backend/

# Ignore rules
flake8 backend/ --ignore=E501,W503

# Configuration (.flake8)
[flake8]
max-line-length = 100
ignore = E501, W503
```

---

## Database Tools

### PostgreSQL Query Analysis

```bash
# Connect
psql -U agi_user -d agi_db

# Active connections
SELECT * FROM pg_stat_activity;

# Slow queries
SELECT * FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;

# Query plan
EXPLAIN ANALYZE SELECT * FROM memories WHERE type='short_term';

# Index usage
SELECT * FROM pg_stat_user_indexes;

# Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables ORDER BY pg_total_relation_size DESC;
```

### SQLAlchemy Echo

```python
# Enable SQL logging
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@host/db",
    echo=True  # Print all SQL
)

# Or for specific session
Session = sessionmaker(bind=engine)
session = Session()
session.echo = True
```

---

## API/Network Tools

### curl - HTTP Testing

```bash
# GET request
curl http://localhost:8000/api/memory/1

# POST with JSON
curl -X POST http://localhost:8000/api/memory \
  -H "Content-Type: application/json" \
  -d '{"content":"test","type":"short"}'

# Headers
curl -i http://localhost:8000/api  # Show headers

# Authentication
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/protected

# Verbose
curl -v http://localhost:8000/api/memory/1
```

### GraphQL Debugging

```bash
# Using curl
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ getMemory(id: 1) { id content } }"
  }'

# Using Apollo DevTools
# Install browser extension, check Network tab

# Apollo Client logging
import { ApolloClient, InMemoryCache } from '@apollo/client';

const client = new ApolloClient({
  cache: new InMemoryCache(),
  logger: console,  // Log all operations
});
```

### tcpdump - Network Packet Analysis

```bash
# Capture traffic
sudo tcpdump -i eth0 -w traffic.pcap

# Filter by port
sudo tcpdump -i eth0 -n port 5432

# View in Wireshark
# Open .pcap file in Wireshark GUI
```

---

## System Monitoring

### System Resources

```bash
# CPU/Memory/Disk
htop

# Process specific
ps aux | grep python

# Real-time disk I/O
iotop

# Memory details
free -h
cat /proc/meminfo

# Disk space
df -h
du -sh *
```

### Python Process Monitoring

```python
import psutil
import os

proc = psutil.Process(os.getpid())

# Memory
print(f"Memory: {proc.memory_info().rss / 1024 / 1024:.1f} MB")

# CPU
print(f"CPU%: {proc.cpu_percent(interval=1)}")

# Open files
print(f"Open files: {len(proc.open_files())}")

# Network connections
print(f"Connections: {len(proc.net_connections())}")
```

### Logging Aggregation

```bash
# Tail backend logs with filtering
tail -f /tmp/backend.log | grep -i error

# Real-time error rate
tail -f /tmp/backend.log | grep ERROR | wc -l

# Parse JSON logs (if structured)
tail -f /tmp/backend.log | jq '.level, .message'

# Time-series analysis
grep "2025-10-20" /tmp/backend.log | grep ERROR | wc -l
```

---

## Docker Debugging

```bash
# Logs
docker logs -f container_name
docker logs --tail 100 container_name

# Exec into container
docker exec -it container_name /bin/bash

# Resource usage
docker stats

# Inspect container
docker inspect container_name | jq '.[0].State'

# Network
docker network ls
docker inspect container_name | jq '.[0].NetworkSettings'
```

---

## IDE/Editor Debugging

### VS Code Python Debugging

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm Debugging

```bash
# Start debug from CLI
/Applications/PyCharm.app/Contents/bin/pycharm.sh --debug path/to/script.py

# Remote debugging
# Configure Python Debugger in PyCharm IDE
```

---

## Quickstart Debugging Checklists

### "It's slow" Diagnosis

```bash
1. Profile CPU
   python -m cProfile -s cumulative script.py | head -20

2. Check queries
   psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5"

3. Memory usage
   python -m memory_profiler script.py

4. Network latency
   curl -w "@curl-format.txt" http://localhost:8000/api/endpoint
```

### "It crashes" Diagnosis

```bash
1. Get full stacktrace
   python script.py 2>&1 | tail -50

2. Identify exact line
   grep -n "line from error" backend/services/file.py

3. Type check
   mypy backend/services/file.py

4. Test with ipdb
   import ipdb; ipdb.set_trace()
```

### "It leaks memory" Diagnosis

```bash
1. Get baseline
   psutil.Process().memory_info().rss

2. Run operation
   # 1000x iterations of operation

3. Check memory again
   psutil.Process().memory_info().rss

4. If grown significantly
   python -m memory_profiler decorated_function.py
```
