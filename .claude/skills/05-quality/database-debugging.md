---
name: database-debugging
category: quality
type: methodology
tags: [database, postgresql, debugging, performance, queries]
complexity: intermediate
---

# Database Debugging Guide

Debugging PostgreSQL queries, performance, connections, and data issues.

## Connection Issues

### Connection Refused / Can't Connect

```bash
# 1. Check PostgreSQL running
sudo systemctl status postgresql

# Start if down
sudo systemctl start postgresql

# 2. Test basic connection
psql -U postgres -c "SELECT 1"

# 3. Test application connection
psql -U agi_user -d agi_db -c "SELECT 1"

# 4. Check credentials
echo "Host: localhost, Port: 5432"
echo "User: agi_user"
echo "Database: agi_db"

# 5. Check pg_hba.conf permissions
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Must have line like:
# local   all             agi_user                                md5
# host    all             agi_user    127.0.0.1/32                md5

# 6. Restart PostgreSQL after config change
sudo systemctl restart postgresql
```

### Connection Pool Exhausted

```bash
# Check active connections
psql -U agi_user -d agi_db -c "SELECT * FROM pg_stat_activity;"

# Output should show:
# - datname (database)
# - usename (user)
# - state (active, idle)
# - query (what's running)

# Kill idle connections (if needed)
psql -U agi_user -d agi_db -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'agi_db' AND state = 'idle' AND query_start < now() - interval '10 minutes';"

# Increase pool size in FastAPI
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Default 5
    max_overflow=40,        # Default 10
    pool_recycle=3600       # Recycle connections hourly
)
```

### Timeout Issues

```bash
# Check long-running queries
psql -U agi_user -d agi_db -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

# Increase timeout in application
# FastAPI:
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout TO 30000")  # 30s

# Or in psql
psql -U agi_user -d agi_db -c "SET statement_timeout TO 30000;"
```

## Slow Queries

### Find Slow Queries

```bash
# Enable query logging (if not already)
sudo nano /etc/postgresql/*/main/postgresql.conf

# Set these:
# log_min_duration_statement = 1000  (log queries > 1s)
# log_statement = 'all'              (log all statements)

sudo systemctl restart postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log | grep duration
```

### Analyze Query Performance

```bash
# EXPLAIN PLAN - shows how query executes
psql -U agi_user -d agi_db << EOF
EXPLAIN ANALYZE
SELECT * FROM memories
WHERE type = 'short_term' AND created_at > now() - interval '1 hour'
ORDER BY created_at DESC
LIMIT 100;
EOF

# Read output:
# - Seq Scan = full table scan (slow)
# - Index Scan = using index (fast)
# - Planning Time vs Execution Time
# - Rows returned vs Rows estimated
```

### Index Optimization

```bash
# Check existing indexes
psql -U agi_user -d agi_db -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';"

# Check which indexes are used
psql -U agi_user -d agi_db -c "
SELECT * FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;"

# Create missing index (on filtering columns)
psql -U agi_user -d agi_db -c "
CREATE INDEX idx_memories_type_created
ON memories(type, created_at DESC);"

# Drop unused index
psql -U agi_user -d agi_db -c "
DROP INDEX idx_memories_unused;"

# Analyze query again to verify improvement
EXPLAIN ANALYZE SELECT ...;
```

### Common Slow Query Patterns

```sql
-- ❌ SLOW - Full table scan
SELECT * FROM memories WHERE content LIKE '%neurotransmitter%';

-- ✅ FAST - Full text search
CREATE INDEX idx_memories_content_fts ON memories USING GIN(to_tsvector('english', content));
SELECT * FROM memories WHERE to_tsvector('english', content) @@ to_tsquery('english', 'neurotransmitter');

-- ❌ SLOW - N+1 query (in application)
SELECT * FROM users;  -- 1 query
-- Then for each user:
SELECT * FROM memories WHERE user_id = ?;  -- N queries

-- ✅ FAST - JOIN
SELECT u.*, m.* FROM users u
LEFT JOIN memories m ON u.id = m.user_id;

-- ❌ SLOW - Subquery in WHERE
SELECT * FROM memories WHERE id IN (
  SELECT memory_id FROM memory_tags WHERE tag_id IN (1,2,3)
);

-- ✅ FAST - JOIN instead
SELECT m.* FROM memories m
JOIN memory_tags mt ON m.id = mt.memory_id
WHERE mt.tag_id IN (1,2,3)
GROUP BY m.id;
```

## Data Issues

### Find Duplicate Data

```bash
# Check for duplicates in unique field
psql -U agi_user -d agi_db -c "
SELECT content, COUNT(*)
FROM memories
GROUP BY content
HAVING COUNT(*) > 1;"

# Remove duplicates (keep first)
psql -U agi_user -d agi_db -c "
DELETE FROM memories
WHERE ctid NOT IN (
  SELECT MIN(ctid)
  FROM memories
  GROUP BY content
);"
```

### Find Missing Data

```bash
# Check for NULL in required field
psql -U agi_user -d agi_db -c "
SELECT COUNT(*) FROM memories WHERE content IS NULL;"

# Check for orphaned records (FK violation)
psql -U agi_user -d agi_db -c "
SELECT * FROM memories
WHERE user_id NOT IN (SELECT id FROM users);"

# Remove orphaned records
psql -U agi_user -d agi_db -c "
DELETE FROM memories
WHERE user_id NOT IN (SELECT id FROM users);"
```

### Validate Data Consistency

```bash
# Check constraints
psql -U agi_user -d agi_db -c "\d memories"

# Verify NOT NULL constraints
psql -U agi_user -d agi_db -c "
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_name = 'memories';"

# Verify UNIQUE constraints
psql -U agi_user -d agi_db -c "
SELECT constraint_name, column_name
FROM information_schema.key_column_usage
WHERE table_name = 'memories';"

# Check foreign keys
psql -U agi_user -d agi_db -c "
SELECT constraint_name, table_name, column_name, referenced_table_name
FROM information_schema.referential_constraints
WHERE table_name = 'memories';"
```

## Deadlocks

### Detect Deadlocks

```bash
# Check for blocking queries
psql -U agi_user -d agi_db -c "
SELECT blocked_locks.pid, blocked_locks.usename,
       blocking_locks.pid, blocking_locks.usename
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;"

# Kill blocking query (if safe)
psql -U agi_user -d agi_db -c "SELECT pg_terminate_backend(<pid>);"
```

### Prevent Deadlocks

```python
# Python: Use transaction isolation
from sqlalchemy import event
from sqlalchemy.orm import Session

# Set isolation level
session = Session(bind=engine)
session.connection().connection.set_isolation_level(3)  # SERIALIZABLE

# Or use context manager
with engine.begin() as connection:
    # Transaction auto-committed on success, rolled back on error
    result = connection.execute("UPDATE memories SET ...")

# Lock order consistency (important!)
# Always lock tables in same order to prevent deadlocks
```

## Table Management

### Check Table Sizes

```bash
# Size of each table
psql -U agi_user -d agi_db -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size DESC;"

# Size of specific table
psql -U agi_user -d agi_db -c "
SELECT pg_size_pretty(pg_total_relation_size('memories'));"

# Size of indexes
psql -U agi_user -d agi_db -c "
SELECT schemaname, indexname,
  pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size DESC;"
```

### Maintenance

```bash
# VACUUM - removes dead tuples
psql -U agi_user -d agi_db -c "VACUUM memories;"

# ANALYZE - updates statistics
psql -U agi_user -d agi_db -c "ANALYZE memories;"

# REINDEX - rebuilds indexes
psql -U agi_user -d agi_db -c "REINDEX TABLE memories;"

# Auto-maintenance (recommended)
# In postgresql.conf:
# autovacuum = on
# autovacuum_naptime = '1min'
```

### Backup & Recovery

```bash
# Full backup
pg_dump -U agi_user -d agi_db > backup.sql

# Backup with compression
pg_dump -U agi_user -d agi_db | gzip > backup.sql.gz

# Restore from backup
psql -U agi_user -d agi_db < backup.sql

# Point-in-time recovery
# Requires WAL archiving configured
```

## SQLAlchemy Debugging

### Enable SQL Logging

```python
import logging
from sqlalchemy import create_engine

# Setup logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or programmatically
engine = create_engine(DATABASE_URL, echo=True)

# In code
session.execute(text("SELECT * FROM memories")).fetchall()
# Will print executed SQL to console
```

### Check Connection String

```python
# Test connection
from sqlalchemy import create_engine, text

engine = create_engine(DATABASE_URL)
with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print(result.fetchone())
```

### Query Building

```python
# Build query step by step
from sqlalchemy import select

# Simple
query = select(Memory)

# With filter
query = select(Memory).where(Memory.type == 'short_term')

# With order and limit
query = query.order_by(Memory.created_at.desc()).limit(10)

# Execute
result = session.execute(query).scalars().all()

# Print SQL
print(str(query))
```

## Migrations (Alembic)

### Check Migration Status

```bash
# Current revision
alembic current

# History
alembic history

# Pending migrations
alembic heads
```

### Run Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add memory table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Specific version
alembic upgrade 123abc
```

## Performance Monitoring

### Monitor Query Performance Over Time

```bash
# Query statistics extension (must be installed)
CREATE EXTENSION pg_stat_statements;

# View top queries by time
psql -U agi_user -d agi_db -c "
SELECT calls, mean_time, query
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;"

# Reset stats
psql -U agi_user -d agi_db -c "SELECT pg_stat_statements_reset();"
```

## Debugging Checklist

```markdown
### Connection Issues
- [ ] PostgreSQL running: `systemctl status postgresql`
- [ ] Credentials correct: Check .env DATABASE_URL
- [ ] User exists: `psql -U agi_user -c "SELECT 1"`
- [ ] Database exists: `psql -c "\l"`

### Performance Issues
- [ ] Query plan analyzed: `EXPLAIN ANALYZE`
- [ ] Indexes present: `\d table_name`
- [ ] Statistics up to date: `ANALYZE table_name`
- [ ] No deadlocks: `SELECT * FROM pg_locks`

### Data Issues
- [ ] No duplicates: `GROUP BY ... HAVING COUNT > 1`
- [ ] No orphaned records: Join to parent tables
- [ ] Constraints valid: `\d table_name`

### Slow Queries
- [ ] Using indexes: Not Seq Scan
- [ ] Row estimates match: Not huge discrepancy
- [ ] No unnecessary JOINs
- [ ] No N+1 queries
```
