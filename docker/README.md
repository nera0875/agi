# Docker Infrastructure

## Quick Start

```bash
# Copy environment template
cp ../.env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Services

### PostgreSQL 16 + pgvector
- **Port**: 5432
- **User**: agi_user (configurable via .env)
- **Database**: agi_db
- **Extensions**: vector, pg_trgm, btree_gin
- **Health check**: Automatic readiness probe

### Redis Stack
- **Port**: 6379 (Redis)
- **Port**: 8001 (RedisInsight web UI)
- **Features**: Cache, pub/sub, RedisJSON, RediSearch

### Backend (FastAPI)
- **Port**: 8000
- **Auto-reload**: Enabled in development
- **Dependencies**: Waits for PostgreSQL + Redis health checks

## Database Schema

See `init-db.sql` for complete schema. Key tables:

- `checkpoints`: LangGraph agent state persistence
- `memory_store`: Vector + full-text hybrid search
- `relations`: Graph relations (replaces Neo4j)
- `sessions`: User conversation management

## Helper Functions

### hybrid_search()
RRF fusion search (70% semantic + 30% BM25):
```sql
SELECT * FROM hybrid_search(
    query_embedding := '[...]'::vector(1024),
    query_text := 'user question',
    match_count := 10
);
```

### get_related_memories()
Graph traversal up to 3 levels:
```sql
SELECT * FROM get_related_memories(
    start_id := 'uuid-here',
    max_depth := 3,
    relation_filter := 'RELATES_TO'
);
```

## Production Checklist

- [ ] Change `POSTGRES_PASSWORD` in .env
- [ ] Generate strong `JWT_SECRET`
- [ ] Configure Sentry DSN
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable PostgreSQL SSL
- [ ] Configure backup strategy
- [ ] Set up monitoring (Prometheus)
- [ ] Review rate limits
- [ ] Enable Row-Level Security policies (if multi-tenant)

## Troubleshooting

### PostgreSQL connection refused
```bash
# Check health
docker-compose ps
docker-compose logs postgres
```

### Redis not responding
```bash
# Test connection
docker exec -it agi-redis redis-cli ping
```

### Backend crashes on startup
```bash
# Check dependencies
docker-compose logs backend
# Verify .env has all required keys
```

## Development vs Production

**Development**:
- Volumes mounted for hot-reload
- Debug logging enabled
- RedisInsight exposed

**Production**:
- Remove volume mounts
- Set `LOG_LEVEL=warning`
- Use secrets manager (not .env)
- Enable SSL/TLS
- Configure firewall rules
