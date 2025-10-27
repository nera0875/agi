# Architecture LangChain/LangGraph + Docker pour AGI-V2

## Guide Technique Complet - VPS Local + Scaling Cloud

**Objectif:** Architecture AGI complète avec VPS local optimisé et possibilité de scaling cloud via Docker

***

## 🚀 PLAN DE DÉVELOPPEMENT AGI-V2

### Structure Projet Final
```
/home/pilote/projet/agi-v2/
├── docs/                           # Documentation technique
│   ├── .trae/documents/           # Documents Trae
│   └── architecture/              # Diagrammes et specs
├── backend/                       # Backend Python FastAPI
│   ├── agents/                    # Agents LangGraph
│   │   ├── consolidator_agent.py
│   │   ├── validator_agent.py
│   │   ├── pattern_extractor_agent.py
│   │   └── connector_agent.py
│   ├── services/                  # Services métier
│   │   ├── memory_service.py
│   │   ├── graph_service.py
│   │   └── embedding_service.py
│   ├── api/                       # API FastAPI
│   │   ├── routes/
│   │   └── middleware/
│   ├── config/                    # Configuration
│   └── Dockerfile                 # Container backend
├── frontend/                      # Frontend React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── public/
│   └── Dockerfile                 # Container frontend
├── docker-compose.yml             # VPS Local
├── docker-compose.prod.yml        # Cloud Production
└── .env.example                   # Variables d'environnement
```

### 🎯 ROADMAP DE DÉVELOPPEMENT (7 semaines)

#### Phase 1: Infrastructure VPS (Semaine 1)
- [x] **Architecture VPS optimisée définie**
- [ ] **Docker Compose VPS** avec PostgreSQL+pgvector, Neo4j, Redis
- [ ] **Configuration environnement** (.env, secrets, volumes persistants)
- [ ] **Health checks** et monitoring de base
- [ ] **Tests de connectivité** entre services

#### Phase 2: Backend Core (Semaine 2-3)
- [ ] **Structure backend FastAPI** avec agents/, services/, api/
- [ ] **Services de base**: MemoryService, GraphService, EmbeddingService
- [ ] **Intégration services externes**: Voyage AI, Cohere, Claude
- [ ] **Base de données**: Schémas PostgreSQL + Neo4j
- [ ] **API endpoints** de base (health, auth, memory)

#### Phase 3: Agents LangGraph (Semaine 4-5)
- [ ] **ConsolidatorAgent**: Consolidation mémoire L2→L3 avec Claude
- [ ] **ValidatorAgent**: Détection contradictions et validation
- [ ] **PatternExtractorAgent**: Extraction patterns et concepts
- [ ] **ConnectorAgent**: Gestion graphe de connaissances
- [ ] **Tests d'intégration** agents + services

#### Phase 4: Frontend & Intégration (Semaine 6)
- [ ] **Frontend React** propre (Time Blocking interface)
- [ ] **Intégration API** backend ↔ frontend
- [ ] **Interface utilisateur** pour interaction avec agents
- [ ] **Tests end-to-end** complets

#### Phase 5: Production & Scaling (Semaine 7)
- [ ] **Optimisation performances** VPS
- [ ] **Configuration production** (SSL, reverse proxy)
- [ ] **Monitoring avancé** (logs, métriques, alertes)
- [ ] **Préparation scaling cloud**

## 🏗️ ARCHITECTURE TECHNIQUE

### Architecture VPS Locale (Performances Maximales)

```mermaid
graph TD
    A[VPS - Localhost Performance] --> B[Docker Compose Local]
    
    B --> C[PostgreSQL + pgvector<br/>Port: 5432]
    B --> D[Neo4j Knowledge Graph<br/>Port: 7474/7687]
    B --> E[Redis Cache<br/>Port: 6379]
    B --> F[AGI Backend FastAPI<br/>Port: 8000]
    B --> G[React Frontend<br/>Port: 3000]
    
    F --> H[Services Externes]
    H --> I[Voyage AI<br/>Embeddings]
    H --> J[Cohere<br/>Reranking]
    H --> K[Anthropic Claude<br/>LLM Processing]
    
    C --> L[LangGraph Checkpoints]
    C --> M[Vector Embeddings]
    C --> N[Memory L1/L2/L3]
    
    D --> O[Knowledge Graph]
    D --> P[Relations & Concepts]
    
    E --> Q[Session Cache]
    E --> R[Query Cache]
    
    subgraph "Agents LangGraph"
        S[ConsolidatorAgent]
        T[ValidatorAgent]
        U[PatternExtractorAgent]
        V[ConnectorAgent]
    end
    
    F --> S
    F --> T
    F --> U
    F --> V
    
    style A fill:#e1f5fe
    style H fill:#fff3e0
    style B fill:#f3e5f5
```

### Architecture Cloud Scaling (Production)

```mermaid
graph TD
    A[Load Balancer] --> B[AGI Backend Instances]
    B --> B1[Backend Pod 1]
    B --> B2[Backend Pod 2]
    B --> B3[Backend Pod N...]
    
    B1 --> C[Cloud Databases]
    B2 --> C
    B3 --> C
    
    C --> D[AWS RDS PostgreSQL<br/>+ pgvector]
    C --> E[Neo4j Aura<br/>Knowledge Graph]
    C --> F[Redis Cloud<br/>Cache]
    
    B --> G[Services Externes]
    G --> H[Voyage AI]
    G --> I[Cohere]
    G --> J[Anthropic Claude]
    
    K[React Frontend] --> L[CDN/Vercel]
    L --> A
    
    subgraph "Kubernetes/Docker Swarm"
        B1
        B2
        B3
    end
    
    subgraph "Cloud Services"
        D
        E
        F
    end
    
    style A fill:#e8f5e8
    style C fill:#fff3e0
    style G fill:#fce4ec
```

## 🛠️ CONFIGURATIONS DOCKER

### Docker Compose VPS Local (docker-compose.yml)

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: agi_postgres
    environment:
      POSTGRES_DB: agi_db
      POSTGRES_USER: agi_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agi_user -d agi_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  neo4j:
    image: neo4j:5.15
    container_name: agi_neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_security_procedures_unrestricted: "apoc.*,gds.*"
      NEO4J_dbms_memory_heap_initial_size: 1G
      NEO4J_dbms_memory_heap_max_size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
    ports:
      - "7474:7474"
      - "7687:7687"
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: agi_redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "auth", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  agi-backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: agi_backend
    environment:
      # Database Connections
      DATABASE_URL: postgresql://agi_user:${POSTGRES_PASSWORD}@postgres:5432/agi_db
      NEO4J_URL: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: ${NEO4J_PASSWORD}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      
      # External Services
      VOYAGE_API_KEY: ${VOYAGE_API_KEY}
      COHERE_API_KEY: ${COHERE_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      
      # Application Config
      ENVIRONMENT: development
      LOG_LEVEL: INFO
      CORS_ORIGINS: "http://localhost:3000"
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - ./backend/logs:/app/logs

  agi-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: agi_frontend
    environment:
      REACT_APP_API_URL: http://localhost:8000
      REACT_APP_ENVIRONMENT: development
    ports:
      - "3000:3000"
    depends_on:
      - agi-backend
    restart: unless-stopped

volumes:
  postgres_data:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  redis_data:

networks:
  default:
    name: agi_network
```

### Docker Compose Cloud Production (docker-compose.prod.yml)

```yaml
version: '3.8'

services:
  agi-backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      # Cloud Database Connections
      DATABASE_URL: ${CLOUD_DATABASE_URL}  # AWS RDS PostgreSQL
      NEO4J_URL: ${CLOUD_NEO4J_URL}       # Neo4j Aura
      REDIS_URL: ${CLOUD_REDIS_URL}       # Redis Cloud
      
      # External Services
      VOYAGE_API_KEY: ${VOYAGE_API_KEY}
      COHERE_API_KEY: ${COHERE_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      
      # Production Config
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
      CORS_ORIGINS: ${FRONTEND_DOMAIN}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  agi-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      REACT_APP_API_URL: ${API_DOMAIN}
      REACT_APP_ENVIRONMENT: production
    ports:
      - "80:80"
      - "443:443"
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
    volumes:
      - ./ssl:/etc/ssl/certs
    restart: unless-stopped

networks:
  default:
    external: true
    name: agi_prod_network
```

## 📋 TODOS PRIORITAIRES

### 🔥 Immédiat (Cette semaine)
1. **Créer structure AGI-v2** dans `/home/pilote/projet/agi-v2/`
2. **Docker Compose VPS** avec tous les services
3. **Configuration environnement** (.env avec clés API)
4. **Base PostgreSQL + pgvector** avec schémas
5. **Tests de connectivité** services

### ⚡ Court terme (2 semaines)
1. **Backend FastAPI** structure complète
2. **Services de base** (Memory, Graph, Embedding)
3. **Intégration Voyage AI + Cohere + Claude**
4. **ConsolidatorAgent** avec LangGraph
5. **API endpoints** essentiels

### 🎯 Moyen terme (1 mois)
1. **Tous les agents LangGraph** opérationnels
2. **Frontend React** intégré
3. **Tests end-to-end** complets
4. **Optimisation performances VPS**
5. **Préparation configurations cloud**

## 🌐 SCALING & CLOUD DEPLOYMENT

### Stratégies de Scaling

#### 1. Scaling Vertical (VPS)
```bash
# Augmenter ressources VPS
# CPU: 4 → 8 cores
# RAM: 16GB → 32GB
# Storage: SSD NVMe pour performances DB
```

#### 2. Scaling Horizontal (Cloud)
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agi-backend
spec:
  replicas: 5
  selector:
    matchLabels:
      app: agi-backend
  template:
    spec:
      containers:
      - name: agi-backend
        image: agi-backend:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Migration Path VPS → Cloud

#### Étape 1: Préparation
```bash
# 1. Backup données VPS
docker exec agi_postgres pg_dump -U agi_user agi_db > backup.sql
docker exec agi_neo4j cypher-shell -u neo4j -p password "CALL apoc.export.cypher.all('backup.cypher')"

# 2. Test docker-compose.prod.yml localement
docker-compose -f docker-compose.prod.yml up --build
```

#### Étape 2: Cloud Setup
```bash
# AWS RDS PostgreSQL + pgvector
aws rds create-db-instance \
  --db-instance-identifier agi-postgres \
  --db-instance-class db.r6g.xlarge \
  --engine postgres \
  --engine-version 15.4

# Neo4j Aura
# Créer instance via console Neo4j Aura

# Redis Cloud
# Créer instance via console Redis Cloud
```

#### Étape 3: Migration
```bash
# 1. Restore données cloud
psql $CLOUD_DATABASE_URL < backup.sql
cypher-shell -a $CLOUD_NEO4J_URL -u neo4j -p $NEO4J_PASSWORD < backup.cypher

# 2. Deploy backend cloud
docker-compose -f docker-compose.prod.yml up -d

# 3. Update DNS/Load Balancer
# Pointer domaine vers nouvelles instances
```

### Performance Comparison

| Métrique | VPS Local | Cloud Distributed |
|----------|-----------|-------------------|
| **Latency DB** | <1ms | 5-20ms |
| **Throughput** | 10k req/s | 50k req/s |
| **Availability** | 99.5% | 99.99% |
| **Cost/month** | $50-200 | $500-2000 |
| **Scaling** | Manual | Auto |
| **Maintenance** | Manual | Managed |

## 🔧 VARIABLES D'ENVIRONNEMENT

### .env.local (VPS)
```bash
# Database Passwords
POSTGRES_PASSWORD=your_secure_postgres_password
NEO4J_PASSWORD=your_secure_neo4j_password
REDIS_PASSWORD=your_secure_redis_password

# External API Keys
VOYAGE_API_KEY=your_voyage_api_key
COHERE_API_KEY=your_cohere_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Application Config
SECRET_KEY=your_secret_key_for_jwt
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### .env.prod (Cloud)
```bash
# Cloud Database URLs
CLOUD_DATABASE_URL=postgresql://user:pass@aws-rds-endpoint:5432/agi_db
CLOUD_NEO4J_URL=neo4j+s://neo4j-aura-endpoint:7687
CLOUD_REDIS_URL=redis://redis-cloud-endpoint:6379

# External API Keys (same)
VOYAGE_API_KEY=your_voyage_api_key
COHERE_API_KEY=your_cohere_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Production Config
SECRET_KEY=your_production_secret_key
FRONTEND_DOMAIN=https://your-domain.com
API_DOMAIN=https://api.your-domain.com
LOG_LEVEL=WARNING
ENVIRONMENT=production
```

## 🚀 GUIDE DE DÉPLOIEMENT

### Déploiement VPS Local

```bash
# 1. Clone et setup
git clone <repo> /home/pilote/projet/agi-v2
cd /home/pilote/projet/agi-v2

# 2. Configuration environnement
cp .env.example .env.local
# Éditer .env.local avec vos clés API

# 3. Build et démarrage
docker-compose up --build -d

# 4. Vérification santé
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:3000

# 5. Logs monitoring
docker-compose logs -f agi-backend
```

### Déploiement Cloud Production

```bash
# 1. Setup cloud databases
# AWS RDS, Neo4j Aura, Redis Cloud

# 2. Configuration production
cp .env.example .env.prod
# Éditer .env.prod avec URLs cloud

# 3. Build images production
docker build -f backend/Dockerfile.prod -t agi-backend:prod ./backend
docker build -f frontend/Dockerfile.prod -t agi-frontend:prod ./frontend

# 4. Deploy avec orchestrateur
docker-compose -f docker-compose.prod.yml up -d
# ou Kubernetes: kubectl apply -f k8s/

# 5. Setup monitoring
# Prometheus, Grafana, ELK Stack
```

## 📊 MONITORING & OBSERVABILITY

### Health Checks
```python
# backend/api/health.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "postgres": await check_postgres(),
            "neo4j": await check_neo4j(),
            "redis": await check_redis(),
            "voyage_ai": await check_voyage_ai(),
            "cohere": await check_cohere()
        }
    }
```

### Metrics Collection
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

## 🎯 PROCHAINES ÉTAPES IMMÉDIATES

1. **Créer structure AGI-v2** → `/home/pilote/projet/agi-v2/`
2. **Setup Docker Compose VPS** → Tous services locaux
3. **Configuration .env** → Clés API externes
4. **Test connectivité** → PostgreSQL, Neo4j, Redis
5. **Premier agent LangGraph** → ConsolidatorAgent

**Commande de démarrage :**
```bash
mkdir -p /home/pilote/projet/agi-v2
cd /home/pilote/projet/agi-v2
# Puis setup complet selon ce guide
```

---

**Architecture finale :** VPS local optimisé + Docker pour portabilité cloud totale ! 🚀