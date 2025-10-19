# Architecture 3 Couches avec Smithery - AGI System

## 🎯 Objectif: ZÉRO pollution de tokens dans le prompt de base

Au lieu d'avoir 60+ MCPs exposés dans Claude Code (coût tokens énorme), on utilise un système à 3 couches intelligent.

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUCHE 1: Claude Code Base                   │
│                                                                  │
│  - Outils essentiels SEULEMENT (Read, Write, Edit, Bash...)    │
│  - 1 seul MCP exposé: agi-tools (memory + smithery gateway)    │
│  - Token count: ~15K (minimal)                                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ mcp__agi_tools__discover_mcp("search")
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│           COUCHE 2: Smithery Intelligent Gateway                │
│                    (smithery_intelligent_gateway.py)            │
│                                                                  │
│  1. Query: capability (ex: "search", "browser", "database")    │
│  2. Cache check: PostgreSQL (known_mcps table, 24h TTL)        │
│  3. Cache MISS → Smithery Registry API (4000+ MCPs)            │
│  4. Store in DB avec capabilities tags                          │
│  5. Return: liste de MCPs matchant la capability               │
│                                                                  │
│  Cache intelligent:                                             │
│  - Évite spam Registry API                                      │
│  - Réutilisation automatique                                    │
│  - Hot reload (file watcher)                                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ MCPs découverts: ["exa", "dockfork"]
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              COUCHE 3: MCP Router + Agent Isolation             │
│                        (mcp_router.py)                          │
│                                                                  │
│  Option A: Router direct (use_mcp)                              │
│  ─────────────────────────────────                              │
│  - use_mcp("exa", "search", {"query": "RAG 2025"})             │
│  - Spawn subprocess à la demande                                │
│  - Execute outil                                                │
│  - Kill subprocess                                              │
│  - Cache connections (5min TTL)                                 │
│                                                                  │
│  Option B: Agent isolé dynamique                                │
│  ──────────────────────────────────                             │
│  - Agent lancé UNIQUEMENT avec MCPs nécessaires                 │
│  - Agent voit SEULEMENT ["exa"] dans son contexte               │
│  - Execute tâche                                                │
│  - Retourne résultats                                           │
│  - Agent terminé (libère contexte)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔥 Exemple de workflow complet

### Scénario: User demande "Cherche les derniers articles sur RAG"

```python
# COUCHE 1: Claude Code détecte besoin de search
# → Appelle discover_mcp
mcp__agi_tools__discover_mcp({
    "capability": "search",
    "limit": 3,
    "auto_add": false  # Ne pas polluer config
})

# COUCHE 2: Gateway cherche dans cache → MISS
# → Query Smithery Registry API
# → Trouve: exa, dockfork, perplexity
# → Cache dans PostgreSQL
# → Return:
{
    "capability": "search",
    "count": 3,
    "mcps": [
        {
            "mcp_id": "exa",
            "tools": ["search", "find_similar"],
            "how_to_use": "mcp__exa__search"
        },
        {
            "mcp_id": "dockfork",
            "tools": ["search_docs"],
            "how_to_use": "mcp__dockfork__search_docs"
        }
    ]
}

# COUCHE 3A: Router execute directement
use_mcp("exa", "search", {
    "query": "RAG optimization 2025",
    "num_results": 10
})

# OU COUCHE 3B: Agent isolé
agent = launch_agent("search-task", mcps=["exa"])
agent.execute("Search RAG optimization 2025")
# → Agent a SEULEMENT exa dans son prompt
# → Pas de pollution avec les 60+ autres MCPs
```

---

## 💾 Base de données: Cache intelligent

### Table `known_mcps`
```sql
CREATE TABLE known_mcps (
    mcp_id TEXT PRIMARY KEY,           -- "exa", "@smithery-ai/fetch"
    display_name TEXT,                 -- "Exa AI Search"
    description TEXT,                  -- "AI-powered search engine"
    tools JSONB,                       -- ["search", "find_similar"]
    category TEXT,                     -- "search"
    smithery_url TEXT,                 -- URL Smithery hosted
    capabilities TEXT[],               -- ["search", "ai", "web"]
    verified BOOLEAN DEFAULT false,    -- Manuellement vérifié
    usage_count INTEGER DEFAULT 0,     -- Popularité
    last_used TIMESTAMP,               -- Pour TTL
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_capabilities ON known_mcps USING GIN(capabilities);
CREATE INDEX idx_mcp_category ON known_mcps(category);
```

### Logique cache (24h TTL)
```python
# Cache HIT si:
# - capability match (GIN index)
# - last_used < 24h OU created_at < 24h
# - Trié par usage_count DESC

# Cache MISS:
# → Smithery Registry API
# → Store avec capabilities auto-détectées
# → Infer capabilities depuis description/category
```

---

## 🎨 Implémentation: 3 fichiers clés

### 1. `smithery_intelligent_gateway.py` (COUCHE 2)
**Rôle:** Découverte MCPs par capability

```python
# Expose 1 tool: discover_mcp
discover_mcp("search")  # → ["exa", "dockfork", "perplexity"]
discover_mcp("browser")  # → ["playwright", "puppeteer", "browserbase"]
discover_mcp("database")  # → ["postgres", "supabase", "mongodb"]
```

**Avantages:**
- Cache PostgreSQL (fast)
- Fallback Smithery Registry (4000+ MCPs)
- Inférence capabilities intelligente
- ZÉRO exposition dans prompt de base

### 2. `mcp_router.py` (COUCHE 3A)
**Rôle:** Execution MCPs à la demande

```python
# Expose 1 tool: use_mcp
use_mcp("exa", "search", {"query": "..."})

# Features:
# - Hot-reload registry (file watcher)
# - Connection cache (5min TTL)
# - Multi-transport (stdio, HTTP, SSE, WebSocket)
# - Thread pool (évite event loop conflicts)
```

### 3. `mcp_dynamic_agent.md` (COUCHE 3B) - À CRÉER
**Rôle:** Agent isolé avec MCP spécifique

```python
# Agent dynamique
agent = Task(
    subagent_type="mcp-executor",
    prompt=f"""
    Execute search using ONLY exa MCP.
    Query: "RAG optimization 2025"

    Available tools:
    - mcp__exa__search
    - mcp__exa__find_similar
    """,
    mcps_enabled=["exa"]  # SEULEMENT exa exposé
)

# Agent termine → libère contexte
```

---

## 🚀 Avantages système 3 couches

### ✅ AVANT (problème actuel)
```
Prompt Claude Code:
- 60+ MCPs exposés = ~300 outils
- Token count: ~50K tokens
- Pollution constante
- Lent à charger
```

### ✅ APRÈS (3 couches)
```
Prompt Claude Code:
- 1 MCP exposé: agi-tools
- 3 outils: discover_mcp, use_mcp, memory_*
- Token count: ~15K tokens
- MCPs chargés à la demande
- Agents isolés (zéro pollution)
```

### 📊 Économies
- **Tokens:** 50K → 15K (-70%)
- **Latency:** Chargement initial 5x plus rapide
- **Scalabilité:** 4000+ MCPs Smithery accessibles
- **Isolation:** Agents voient UNIQUEMENT MCPs nécessaires

---

## 🔧 Configuration requise

### 1. Nettoyer `mcp-registry.json`
**Garder SEULEMENT:**
```json
{
  "agi-memory": {...},  // Essentiel (memory system)
}
```

**Retirer:**
- Tous les autres MCPs (60+)
- Seront accessibles via discovery on-demand

### 2. Activer gateway dans `settings.local.json`
```json
{
  "enabledMcpjsonServers": [
    "agi-tools"  // Contient memory + smithery gateway
  ]
}
```

### 3. Créer `agi-tools` MCP combiné
**Fusion de:**
- `memory_search/store/stats` (déjà existant)
- `discover_mcp` (smithery gateway)
- `use_mcp` (router)

---

## 🎯 Workflow recommandé

### Découverte + Execution
```python
# 1. Découvrir MCPs par capability
mcps = discover_mcp("search", limit=3)
# → Cache intelligent, pas de spam Registry

# 2. Choisir MCP
chosen = mcps["mcps"][0]["mcp_id"]  # "exa"

# 3. Executer
result = use_mcp(chosen, "search", {"query": "..."})
```

### Agent isolé (option avancée)
```python
# 1. Découvrir
mcps = discover_mcp("browser")

# 2. Lancer agent AVEC MCPs spécifiques
agent = Task(
    subagent_type="browser-automation",
    mcps_enabled=["playwright"],  # Isolation
    prompt="Prendre screenshot de example.com"
)
```

---

## 📈 Roadmap

### Phase 1: Cleanup ✅
- [x] Analyser architecture actuelle
- [ ] Nettoyer `mcp-registry.json` (garder essentiels)
- [ ] Tester gateway isolation

### Phase 2: Gateway activation
- [ ] Fusionner memory + smithery gateway → `agi-tools`
- [ ] Update `settings.local.json`
- [ ] Tester `discover_mcp` + cache

### Phase 3: Agent isolation
- [ ] Créer agent `mcp-executor`
- [ ] Support `mcps_enabled` parameter
- [ ] Tester isolation contexte

### Phase 4: Production
- [ ] Seed common MCPs dans cache
- [ ] Monitoring usage (PostgreSQL)
- [ ] Documentation

---

## 🧪 Tests

### Test gateway
```bash
# Découverte
python3 cortex/smithery_intelligent_gateway.py <<EOF
{"capability": "search", "limit": 3}
EOF

# Check cache
psql -d agi_db -c "SELECT mcp_id, capabilities, usage_count FROM known_mcps;"
```

### Test router
```bash
# Execution
python3 cortex/mcp_router.py --test exa

# Check registry hot-reload
echo '{"test": {...}}' >> cortex/mcp-registry.json
# → Auto-reload dans 2s
```

---

## 🎓 Concepts clés

### Capability-based discovery
Au lieu de lister tous les MCPs, on demande une **capability**:
- `"search"` → MCPs de recherche
- `"browser"` → MCPs d'automation navigateur
- `"database"` → MCPs de bases de données

### Cache intelligent (PostgreSQL)
- Évite spam Smithery Registry API
- Réutilisation automatique (24h TTL)
- Inférence capabilities (smart tagging)
- Popularité tracking (usage_count)

### Agent isolation
- Agent voit UNIQUEMENT MCPs nécessaires
- Pas de pollution contexte principal
- Libération automatique après exécution
- Scalable (N agents en parallèle)

---

## 🔐 Sécurité

### Credentials isolation
- Jamais exposer API keys dans prompts
- Stockage sécurisé (env vars)
- Masking dans logs

### Rate limiting
- Cache évite spam Registry
- Connection pool (max 5 concurrent)
- Timeout protection (30s default)

---

## 💡 Use cases

### 1. Recherche AI
```python
discover_mcp("search")  # → exa, dockfork
use_mcp("exa", "search", {"query": "..."})
```

### 2. Automation navigateur
```python
discover_mcp("browser")  # → playwright, puppeteer
use_mcp("playwright", "screenshot", {"url": "..."})
```

### 3. Base de données
```python
discover_mcp("database")  # → postgres, supabase
use_mcp("supabase", "query", {"table": "..."})
```

### 4. Agent avec MCP spécifique
```python
agent = Task(
    subagent_type="mcp-executor",
    mcps_enabled=["exa"],
    prompt="Search and summarize RAG articles"
)
```

---

## 📝 Notes

- **Smithery Registry:** 4000+ MCPs disponibles
- **Cache TTL:** 24h (configurable)
- **Connection cache:** 5min (configurable)
- **Hot-reload:** File watcher (2s latency)
- **Transports supportés:** stdio, HTTP, SSE, WebSocket

---

## 🎉 Résultat final

**Avant:** 60+ MCPs exposés, 50K tokens, pollution constante
**Après:** 1 MCP exposé, 15K tokens, discovery on-demand, agents isolés

**= Architecture scalable, économe en tokens, intelligent**
