---
name: common-bug-patterns
category: quality
type: patterns
tags: [debugging, patterns, anti-patterns, common-mistakes]
complexity: intermediate
---

# Common Bug Patterns & Solutions

Patterns de bugs les plus fréquents avec solutions et prévention.

## 1. Race Conditions (Async)

### Pattern
```python
# ❌ PROBLÈME
async def update_memory():
    data = await fetch_from_db()     # Point A
    # Autre coroutine peut modifier 'data' ici
    await process_and_save(data)     # Point B - data peut être stale
```

### Solution: Locking
```python
from asyncio import Lock

class MemoryService:
    def __init__(self):
        self.lock = Lock()

    async def update_memory(self):
        async with self.lock:
            data = await fetch_from_db()
            await process_and_save(data)
```

### Prévention
- Utiliser locks/semaphores pour état partagé
- Tests avec `pytest-asyncio`
- Éviter mutations partagées

---

## 2. Memory Leaks

### Pattern: Uncapped Cache
```python
# ❌ PROBLÈME - Cache grandit indéfiniment
class MemoryService:
    def __init__(self):
        self.cache = {}  # Pas de limit!

    def cache_memory(self, key, value):
        self.cache[key] = value  # Grandit jusqu'à crash

# Après 1M mémorizations → OUT OF MEMORY
```

### Solution: TTL Cache
```python
from cachetools import TTLCache
import time

class MemoryService:
    def __init__(self):
        self.cache = TTLCache(maxsize=10000, ttl=3600)

    def cache_memory(self, key, value):
        self.cache[key] = value  # Auto-eviction après 1h
```

### Prévention
- Toujours limiter cache size
- TTL pour dépendances temporaires
- Profile memory: `memory_profiler`
- Monitor: `psutil.Process().memory_info()`

---

## 3. N+1 Query Problem

### Pattern
```python
# ❌ PROBLÈME - 1 query + N queries (N+1 total)
def get_users_with_posts():
    users = db.query(User).all()          # 1 query
    result = []
    for user in users:
        posts = db.query(Post).filter_by(user_id=user.id).all()  # N queries
        result.append({"user": user, "posts": posts})
    return result

# 10 users = 11 queries ❌
```

### Solution: Join/Batch
```python
# ✅ OPTION 1 - Join
def get_users_with_posts():
    users = db.query(User).options(
        joinedload(User.posts)  # SQLAlchemy eager loading
    ).all()
    return users
    # 1 query with join

# ✅ OPTION 2 - Batch load
async def get_users_with_posts():
    user_ids = [u.id for u in users]
    posts = await db.query(Post).filter(Post.user_id.in_(user_ids)).all()
    # 2 queries total (batch)
```

### Prévention
- Profile query count: `django-debug-toolbar` / `sqlalchemy echo`
- Unit tests vérifier query count
- Use `Select.options(joinedload())` for relationships

---

## 4. Type Mismatches (Python)

### Pattern
```python
# ❌ PROBLÈME
def process_age(age):
    return age + 10  # Assume age est int

# Mais appelé avec string:
result = process_age("25")  # TypeError: can only concatenate str...
```

### Solution: Type Hints + Checking
```python
# ✅ Solution 1 - Type hints (static)
def process_age(age: int) -> int:
    return age + 10

# Type checker: mypy process_age("25")  # ❌ Error!

# ✅ Solution 2 - Runtime validation
from typing import Union

def process_age(age: Union[int, str]) -> int:
    if isinstance(age, str):
        age = int(age)
    elif not isinstance(age, int):
        raise TypeError(f"age must be int/str, got {type(age)}")
    return age + 10
```

### Prévention
- `mypy --strict` dans CI/CD
- Validation au boundary (API input)
- Pydantic models pour data validation

---

## 5. Null Pointer Exceptions

### Pattern
```python
# ❌ PROBLÈME
def get_user_email(user):
    return user.profile.email  # None si profile is None

response = api_call()
email = get_user_email(response)  # AttributeError: 'NoneType'...
```

### Solution: Safe Navigation
```python
# ✅ Solution 1 - Explicit checks
def get_user_email(user):
    if user is None or user.profile is None:
        return None
    return user.profile.email

# ✅ Solution 2 - Try-except
def get_user_email(user):
    try:
        return user.profile.email
    except AttributeError:
        logger.warning(f"User profile missing: {user}")
        return None

# ✅ Solution 3 - Optional type hints
from typing import Optional

def get_user_email(user: Optional[User]) -> Optional[str]:
    return user.profile.email if user else None
```

### Prévention
- Use `Optional[T]` type hints
- Defensive programming at API boundaries
- Tests with None values

---

## 6. Off-by-One Errors

### Pattern
```python
# ❌ PROBLÈME - Index boundary
memories = get_memories()  # List[Memory]
for i in range(len(memories)):
    process(memories[i+1])  # IndexError on last item!

# ❌ PROBLÈME - Range off-by-one
for i in range(0, 10):  # 0-9 (10 items)
    if i == 10:  # Never true!
        print("Should never print")
```

### Solution
```python
# ✅ Solution 1 - Pythonic iteration
for memory in memories:
    process(memory)  # No index needed

# ✅ Solution 2 - Correct boundaries
for i in range(len(memories) - 1):  # Stop at len-1
    process(memories[i], memories[i+1])

# ✅ Solution 3 - zip
for current, next_item in zip(memories, memories[1:]):
    process(current, next_item)
```

### Prévention
- Prefer direct iteration over indexing
- Unit test boundary cases (i=0, i=len-1)
- Code review for loops

---

## 7. Concurrent Modifications (Collections)

### Pattern
```python
# ❌ PROBLÈME - Modifying list during iteration
memories = [mem1, mem2, mem3]
for memory in memories:
    if memory.is_old():
        memories.remove(memory)  # RuntimeError or skips items!
```

### Solution
```python
# ✅ Solution 1 - Copy list
memories = [mem1, mem2, mem3]
for memory in memories[:]:  # Iterate over copy
    if memory.is_old():
        memories.remove(memory)

# ✅ Solution 2 - List comprehension
memories = [m for m in memories if not m.is_old()]

# ✅ Solution 3 - Filter
memories = list(filter(lambda m: not m.is_old(), memories))
```

### Prévention
- Avoid mutations during iteration
- Use list comprehensions
- Unit test modification patterns

---

## 8. Infinite Loops

### Pattern
```python
# ❌ PROBLÈME
while True:
    data = fetch_data()
    process(data)
    # No break condition!

# ❌ PROBLÈME - Condition never false
counter = 0
while counter < 10:
    process()
    # counter never incremented!
```

### Solution
```python
# ✅ Solution 1 - Clear exit condition
while True:
    data = fetch_data()
    if not data:
        break
    process(data)

# ✅ Solution 2 - For loop with max
for i in range(10):
    process()  # Auto-exits after 10

# ✅ Solution 3 - Timeout
import time
start = time.time()
while time.time() - start < 30:  # Max 30s
    if process():
        break
```

### Prévention
- Always define exit condition
- Code review loops for increment
- Set timeouts for background tasks
- Use `for` instead of `while` when possible

---

## 9. String Formatting/Injection

### Pattern
```python
# ❌ PROBLÈME - SQL Injection
user_input = "admin' OR '1'='1"
query = f"SELECT * FROM users WHERE name = '{user_input}'"
db.execute(query)  # Security breach!

# ❌ PROBLÈME - Format string vulnerability
log_message = user_input  # Could be "%x" for memory leak
print(f"User input: {log_message}")
```

### Solution
```python
# ✅ Solution 1 - Parameterized queries
query = "SELECT * FROM users WHERE name = ?"
db.execute(query, (user_input,))

# ✅ Solution 2 - Proper logging
print(f"User input: {user_input!r}")  # Always quote

# ✅ Solution 3 - Validation
if not re.match(r"^[a-zA-Z0-9]+$", user_input):
    raise ValueError("Invalid input")
```

### Prévention
- Always use parameterized queries
- Validate/sanitize user input
- Use logging libraries (not print)
- Security testing

---

## 10. Import Cycles

### Pattern
```python
# ❌ PROBLÈME - Circular imports
# module_a.py
from module_b import func_b

def func_a():
    func_b()

# module_b.py
from module_a import func_a  # Circular!

def func_b():
    func_a()

# Result: ImportError or None attributes
```

### Solution
```python
# ✅ Solution 1 - Restructure (Best)
# common.py - shared utilities
def shared_func():
    pass

# module_a.py
from common import shared_func

# module_b.py
from common import shared_func

# ✅ Solution 2 - Late import
# module_a.py
def func_a():
    from module_b import func_b  # Import when needed
    func_b()

# ✅ Solution 3 - Type hints only
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_b import FuncB  # For type checker only
```

### Prévention
- Keep imports at module top level (detect cycles)
- Use `python -c "import module"` to test
- Circular dependency visualizer
- Code review import structure

---

## 11. Exception Swallowing

### Pattern
```python
# ❌ PROBLÈME - Silent failures
def process_memory():
    try:
        dangerous_operation()
    except Exception:
        pass  # Swallowed! Silent failure

# Result: Bug manifests later, hard to debug
```

### Solution
```python
# ✅ Solution 1 - Log exceptions
import logging

def process_memory():
    try:
        dangerous_operation()
    except ValueError as e:
        logging.exception(f"Failed to process: {e}")
        raise  # Re-raise or handle explicitly

# ✅ Solution 2 - Specific exceptions only
def process_memory():
    try:
        dangerous_operation()
    except ValueError:
        logger.error("Invalid value provided")
        return None  # Explicit handling
    except Exception:
        logger.exception("Unexpected error")  # Re-raise context

# ✅ Solution 3 - Context manager
from contextlib import suppress

def process_memory():
    with suppress(ValueError):  # Intentional, documented
        dangerous_operation()
```

### Prévention
- Never bare `except:` without logging
- Specific exception types
- Always log context
- Code review exception handling

---

## Quick Pattern Matcher

```markdown
## When you see... → Suspect...

-> NoneType error
   └─ Null pointer exception

-> TypeError: NoneType
   └─ Optional type not handled

-> IndexError: list index out of range
   └─ Off-by-one error

-> RuntimeError: dictionary changed during iteration
   └─ Concurrent modification

-> ConnectionError/TimeoutError
   └─ Resource exhaustion (pool) or upstream down

-> AttributeError after time
   └─ Memory leak (object not GC'd)

-> Intermittent failures
   └─ Race condition

-> Works locally, fails prod
   └─ Env variable / config issue
```
