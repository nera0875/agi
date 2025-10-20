---
title: Infrastructure Health Monitoring
category: workflow
priority: high
updated: 2025-10-20
version: 1.0
agent: sre
---

# Infrastructure Health Monitoring

## Overview
Real-time monitoring of PostgreSQL, Neo4j, Redis, and API costs without creating operational chaos.

## Database Health Checks

### PostgreSQL Monitoring
```sql
-- Connection status
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

-- Slow queries (>100ms)
SELECT query, mean_time FROM pg_stat_statements
WHERE mean_time > 100 ORDER BY mean_time DESC;

-- Table bloat
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables ORDER BY pg_total_relation_size DESC;

-- Missing indexes
SELECT * FROM pg_stat_user_tables
WHERE seq_scan > idx_scan AND seq_scan > 100;

-- Cache hit ratio (should be >90%)
SELECT
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

### Neo4j Monitoring
```cypher
-- Database size
CALL db.stats.usedDbhitCount() YIELD hitCount;

-- Query performance
PROFILE MATCH (n) RETURN count(n);

-- Index status
CALL db.indexes();

-- Constraint check
CALL db.constraints();

-- Connection pool
:diagnostics
```

### Redis Monitoring
```bash
# Memory usage
INFO memory

# Key count
DBSIZE

# Eviction policy
CONFIG GET maxmemory-policy

# Replication status
INFO replication

# Slow log
SLOWLOG GET 10

# Memory fragmentation
INFO stats → mem_fragmentation_ratio
```

## Cost Tracking

### API Costs (24h window)
```python
# Anthropic API calls
- Model: claude-haiku-4-5
- Calls count: X
- Input tokens: Y
- Output tokens: Z
- Cost: $(Y + Z*1.5) / 1M * pricing

# Voyage AI embeddings
- Embeddings calls: X
- Tokens: Y
- Cost: $Y / 1M * pricing

# External MCPs (if billed)
- exa-mcp-server
- fetch-mcp
- context7
```

### Cost Alerts
- [ ] Daily API spend > $50
- [ ] Embedding calls > 1M tokens/day
- [ ] PostgreSQL connection pool > 80%
- [ ] Redis memory > 80% of limit
- [ ] Neo4j database > 50GB

## Performance Baselines

### API Latency
```markdown
🟢 Healthy:
- GraphQL query: <100ms
- REST endpoint: <50ms
- Memory lookup: <20ms

🟡 Warning:
- GraphQL query: 100-500ms
- REST endpoint: 50-200ms
- Memory lookup: 20-100ms

🔴 Critical:
- GraphQL query: >500ms
- REST endpoint: >200ms
- Memory lookup: >100ms
```

### Database Performance
```markdown
PostgreSQL:
- Query: <100ms (p95)
- Connection time: <10ms
- Cache hit: >90%

Neo4j:
- Traversal: <200ms
- Write: <150ms
- Index lookup: <50ms

Redis:
- Get: <5ms
- Set: <5ms
- Memory fragmentation: <1.5
```

## Alert Rules

### Critical (Immediate Action)
- [ ] Database connection refused
- [ ] Redis out of memory
- [ ] Neo4j unreachable
- [ ] API error rate > 5%
- [ ] Slow query (>1s)
- [ ] Daily cost > $100

### Warning (Investigate)
- [ ] Connection pool > 70%
- [ ] Memory bloat > 20%
- [ ] Query p95 > 200ms
- [ ] Missing indexes on hot tables
- [ ] Replication lag > 10s

### Info (Monitor)
- [ ] Cache hit ratio changes
- [ ] New slow queries
- [ ] Index size growth
- [ ] Backup status

## Log Analysis Locations

```
/tmp/postgresql.log      → Database queries, errors
/tmp/redis.log           → Cache hits/misses
/tmp/neo4j.log           → Graph queries
/tmp/api.log             → API requests/responses
/tmp/agents.log          → Agent execution traces
/tmp/errors.log          → Application errors
```

## Monitoring Dashboard Layout

```markdown
REAL-TIME METRICS:

┌─────────────────────────────────────────┐
│ PostgreSQL                              │
│ Connections: 15/100  Cache Hit: 94%    │
│ Slow Query p95: 45ms   Bloat: 2.3GB   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Neo4j                                   │
│ Connections: 8/50     DB Size: 2.1GB   │
│ Write Speed: 150ms    Query p95: 120ms │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Redis                                   │
│ Memory: 234MB / 1GB (23%)   Keys: 15K  │
│ Hits: 9,823   Misses: 217   HitRate: 98% │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ API Performance                         │
│ Requests/min: 45    Error Rate: 0.1%   │
│ p50 latency: 45ms   p95 latency: 120ms │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Cost (24h)                              │
│ Anthropic: $12.34    Voyage: $2.15     │
│ Storage: $0.50       Total: $15.00     │
└─────────────────────────────────────────┘
```

## Health Check Procedures

### Daily Morning Check (5 min)
1. [ ] All 3 databases responding
2. [ ] Error rate < 1%
3. [ ] No slow queries (p95 < 200ms)
4. [ ] API costs normal
5. [ ] Agent logs clean

### Weekly Deep Dive (30 min)
1. [ ] Index efficiency analysis
2. [ ] Table bloat check
3. [ ] Query optimization review
4. [ ] Cache performance analysis
5. [ ] Cost trends

### Monthly Review (1h)
1. [ ] Capacity planning
2. [ ] Upgrade recommendations
3. [ ] Cost optimization
4. [ ] Backup verification
5. [ ] Documentation update

## Escalation Procedures

### If PostgreSQL Down
1. Check network connectivity
2. Review logs in `/tmp/postgresql.log`
3. SSH to VPS and restart if needed
4. Verify data integrity
5. Check backup status

### If Neo4j Down
1. Check disk space
2. Review Neo4j logs
3. Force database check
4. Restart if needed
5. Verify no data corruption

### If Redis Down
1. Check memory limits
2. Review eviction policy
3. Check disk space (persistence)
4. Restart Redis
5. Verify cache repopulation

## Metrics to Track Long-term

```python
# Weekly snapshots
- API latency trends
- Query count patterns
- Cache hit ratio progression
- Database size growth
- Cost trends

# Monthly analysis
- Performance degradation detection
- Scaling needs
- Cost optimization opportunities
- Index effectiveness
- Cache efficiency
```

## Tools & Commands

```bash
# PostgreSQL
psql -h localhost -U agi_user -d agi_db -c "SELECT version();"

# Neo4j
cypher-shell -a neo4j://localhost:7687 "CALL dbms.components()"

# Redis
redis-cli PING

# Check logs
tail -f /tmp/*.log

# Monitor processes
ps aux | grep postgres|redis|neo4j
```

---

**Goal:** Proactive monitoring, not reactive firefighting.
