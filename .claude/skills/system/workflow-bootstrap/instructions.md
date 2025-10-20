# Workflow Bootstrap Instructions

## WORKFLOW ABSOLU (NON-NÉGOCIABLE)

**AVANT toute réponse :**
1. `think("bootstrap")` OU `think("contexte [sujet]")`
2. Analyser L1/L2/L3 retourné

**POUR toute tâche :**
3. `Task(subagent_type="task-executor", ...)` × N en PARALLÈLE
   - ❌ JAMAIS faire tâches MOI-MÊME (Bash/Read/Grep/Edit/Write)
   - ✅ TOUJOURS via agents (économie 90% tokens - conversations isolées)
4. Agréger résultats JSON
5. `memory(action="store", ...)` si important

**APRÈS conversation :**
6. Hooks capturent automatiquement (background)

## PHASE BREAKDOWN

### PHASE 0: BOOTSTRAP (MOI seul, <5s)

```python
# Charger contexte depuis DB
think("bootstrap")
```

**Retour:**
```json
{
  "memory": {
    "L1": {...},  // Redis hot cache
    "L2": {...},  // PostgreSQL memories
    "L3": {...}   // Neo4j graph
  }
}
```

**Analyse:**
- Quels contextes chargés ?
- Quoi manque ?
- Besoin recherche/exploration ?

### PHASE 1: EXPLORATION (ask × N, 10-20s)

**Si manque contexte codebase:**
```python
Task(ask, "Scan backend/services/memory*.py, return: list classes")
Task(ask, "Find tests related to memory")
Task(ask, "Grep imports for dependencies")
```

**Timeout:** 15-20s per agent
**Output:** JSON list files/classes

### PHASE 2: RESEARCH (research × N, 20-30s)

**Si besoin patterns/docs externes:**
```python
Task(research, "Best practices GraphQL subscriptions")
Task(research, "React hooks performance optimization")
Task(research, "PostgreSQL query optimization")
```

**Timeout:** 20-30s per agent
**Output:** JSON summaries

### PHASE 3: ARCHITECTURE (architect × 1-3, 30s)

**Design solution:**
```python
Task(architect, "Design memory L1/L2/L3 cascade with context")
```

**Timeout:** 30s
**Output:** JSON architecture + ADR

### PHASE 4: IMPLEMENTATION (code/frontend × N, 30-60s)

**Implement features:**
```python
Task(code, "Backend: memory consolidation service")
Task(frontend, "Frontend: memory visualization")
```

**Timeout:** 30-60s per agent
**Output:** Code (created/modified files)

### PHASE 5: VALIDATION (debug × N, 20-40s)

**Test & verify:**
```python
Task(debug, "Test memory service endpoint")
Task(debug, "Test frontend component renders")
```

**Timeout:** 20-40s per agent
**Output:** Test results, bug reports

### PHASE 6: DOCUMENTATION (docs × 1, 20-30s)

**Document:**
```python
Task(docs, "Update README memory system section")
```

**Timeout:** 20-30s
**Output:** Documentation

### PHASE 7: MEMORY STORAGE (MOI seul, <5s)

**Persist important findings:**
```python
memory(action="store", data={
    "feature": "memory_consolidation",
    "status": "complete",
    "findings": {...}
})
```

## TOOLS REFERENCE

### think() - Bootstrap & Context Loading

**Syntax:**
```python
think("bootstrap")              # Full cascade L1→L2→L3
think("contexte [subject]")     # Load specific topic
```

**Returns:**
```json
{
  "memory": {
    "L1": {
      "recent": [...],          // Redis hot cache
      "session": {...}
    },
    "L2": {
      "memories": [...],        // PostgreSQL
      "metadata": {}
    },
    "L3": {
      "entities": [...],        // Neo4j
      "relationships": [...]
    }
  }
}
```

**Usage:**
- Start of every conversation
- When need historical context
- Before major decisions

### memory() - Persistent Storage

**Syntax:**
```python
memory(action="store", data={
    "key": "value",
    "timestamp": datetime.now(),
    "tags": ["tag1", "tag2"]
})

memory(action="retrieve", query="memory_consolidation")

memory(action="consolidate")  # Trigger consolidation
```

**Actions:**
- **store** - Save to L1 (Redis) + L2 (PostgreSQL)
- **retrieve** - Query L2 with full-text search
- **consolidate** - Trigger L2→L3 consolidation

**Returns:**
```json
{
  "status": "stored",
  "id": "memory_uuid",
  "location": "L1,L2"
}
```

### database() - Direct Data Access

**Syntax:**
```python
database(query="SELECT * FROM memories WHERE created_at > ?", params=[timestamp])

database(action="update", table="memories", data={...}, where={...})

database(action="execute", sql="INSERT INTO ...")
```

**Usage:**
- Direct PostgreSQL queries
- Bulk operations
- Administrative tasks

**Returns:**
```json
{
  "status": "success",
  "rows": [...],
  "affected": 5
}
```

### Task() - Agent Orchestration

**Syntax:**
```python
Task(agent_type="ask", prompt="""
Scan backend/services/memory*.py

DEADLINE: 20s
SCOPE: List classes + methods
PARTIAL OK: If timeout

Output: {files: [], classes: []}
""")
```

**Agent Types:**
- ask - Codebase exploration
- research - External research
- architect - Design patterns
- code - Backend implementation
- frontend - UI implementation
- debug - Testing & debugging
- docs - Documentation
- sre - Infrastructure

**Key Parameters:**
- `agent_type` - Which agent to invoke
- `prompt` - Ultra-precise task description
- **DEADLINE** - Timeout in seconds
- **SCOPE** - Exactly what to do
- **Output** - Expected JSON format

**Returns:**
```json
{
  "status": "complete|partial|error",
  "timeout": false,
  "result": {...}
}
```

## DEADLINES AGENTS (EFFICIENCY MAXIMALE)

**RÈGLE ABSOLUE: Agents ont DEADLINES strictes comme employés**

### Timeouts Recommandés

| Type Tâche | Timeout | Exemple |
|------------|---------|---------|
| Scan 1-5 fichiers | 10s | Glob + Read rapide |
| Scan 10-20 fichiers | 20s | Sample premiers si trop |
| Grep pattern | 15s | Ripgrep = rapide |
| Plan phase | 30s | Architecture courte |
| Code micro-feature | 30s | 1 fonction/classe |
| Tests run | 20s | pytest fichier unique |
| Documentation | 30s | Readme section |

### Format Prompt Standard

**TOUJOURS inclure:**
```python
Task(agent, """
[Tâche ULTRA-PRÉCISE]

DEADLINE: [X] secondes MAX
SCOPE: [Exactement quoi faire - pas plus]
PARTIAL OK: Si timeout, return ce que tu as
FORMAT: JSON compact

Output attendu: {...}
""")
```

### Partial Results Handling

**Si dépasse → PARTIAL RESULTS:**
```json
{
  "status": "partial",
  "timeout": true,
  "completed": "70%",
  "results": [...],
  "message": "Timeout 20s, traité 7/10 fichiers"
}
```

**MOI (CEO) agrège intelligemment:**
```python
results = [agent1, agent2, agent3, ...]

complete = [r for r in results if not r.get('timeout')]
partial = [r for r in results if r.get('timeout')]

if len(complete) >= 70%:
    # Assez de données, continue
    aggregate(complete + partial)
else:
    # Relancer agents timeout avec scope réduit
    retry_with_smaller_scope(partial)
```

## SCOPE ULTRA-PRÉCIS (Pas de Dérive)

**❌ FLOU (agent se perd):**
```
"Analyse le backend"
→ Agent scanne TOUT (5 min)
→ Bloque les 9 autres
```

**✅ PRÉCIS (agent focus):**
```
"Scan backend/services/memory*.py
- List classes + leurs méthodes publiques
- Max 10 fichiers (sample si plus)
- 15s deadline
- Return: {files: [], classes: []}"

→ Agent fait JUSTE ça (15s)
```

## DIVISER GROS TRAVAUX

**Exemple: Scan 50 fichiers backend**

❌ **1 agent lent:**
```python
Task(ask, "Scan tout backend")
→ 5 minutes
```

✅ **5 agents rapides:**
```python
Task(ask, "Scan services/[a-e]*.py, 20s max")
Task(ask, "Scan services/[f-j]*.py, 20s max")
Task(ask, "Scan services/[k-o]*.py, 20s max")
Task(ask, "Scan services/[p-t]*.py, 20s max")
Task(ask, "Scan services/[u-z]*.py, 20s max")

→ 20 secondes total (parallèle)
→ Si 1 timeout: 80% résultats = OK
```

## STRATÉGIE AGENTS (MOI intelligent/lent → EUX rapides/bêtes)

**AVANT de lancer agents:**

**ÉTAPE 1 - RÉFLÉCHIR (MOI, 100 tokens):**
```
think("comment résoudre X?")
→ Décomposer en micro-tâches
→ Identifier ressources (fichiers, DB rows)
→ Vérifier indépendance (conflits?)
→ Partitionner si write operations
```

**ÉTAPE 2 - PROMPTS ULTRA-PRÉCIS:**
```
PAS: "Analyse ces fichiers"
OUI: "Fichier: X.py
      1. Bash(wc -l X.py)
      2. Parse 'XXX file.py'
      3. Extract XXX
      4. Return {lines: XXX}"
```

**ÉTAPE 3 - PARALLÉLISER INTELLIGEMMENT:**
```
Read-only: N = min(ressources, 20)
Write: 1 fichier = 1 agent MAX
Database: Partitionner rows AVANT
```

**ÉTAPE 4 - LANCER + AGRÉGER (500 tokens agents isolés):**
```
Task × 10 en PARALLÈLE
→ Attendre tous résultats
→ Agréger + Synthétiser (50 tokens retour)
```

**RÉSULTAT:** 80% économie tokens vs MOI fait tout

### RÈGLES CONFLITS:
- 1 fichier = 1 agent (écriture)
- Agents = tâches INDÉPENDANTES
- Si dépendances → Séquentiel
- Si doute → 1 seul agent

## L1/L2/L3 CASCADE

**L1 (Redis) - Hot Cache:**
- Recent interactions (session)
- Quick retrieval
- TTL-based expiry

**L2 (PostgreSQL) - Persistent Storage:**
- Structured memories with metadata
- Full-text search enabled
- Relationships (foreign keys)
- Source tracking

**L3 (Neo4j) - Knowledge Graph:**
- Entity relationships
- Semantic connections
- Pattern detection
- Graph algorithms

**Cascade Logic:**
```
Query: think("contexte [subject]")
  ↓
1. Check L1 (Redis) - Hit? Return fast
2. If miss → Query L2 (PostgreSQL)
3. If miss → Query L3 (Neo4j) + consolidate
4. Store result in L1 for next access
```

## ANTI-PATTERNS À ÉVITER

❌ **Pas de deadline:**
```
"Fais de ton mieux"
→ Agent prend son temps (3-10 min)
```

❌ **Scope vague:**
```
"Regarde le projet"
→ Agent ne sait pas quoi chercher
```

❌ **Perfectionnisme:**
```
"Analyse complète 100% obligatoire"
→ Bloque si gros projet
```

❌ **Faire moi-même:**
```
Edit(file, old, new)  # MOI-MÊME (interdit)
→ Tokens wasted, agents idle
```

✅ **Pragmatique CEO:**
```
Task(code, "Fix this bug - 30s max, partial OK")
→ Rapide + utile
```

## ÉCONOMIE TOKENS

**Sans pipeline** (MOI fait tout):
- MOI: 5000 tokens × 6 étapes = 30,000 tokens

**Avec pipeline** (agents Haiku):
- MOI: 100 tokens réflexion + 50×6 agrégations = 400 tokens
- Agents: 500 tokens × 6 phases (isolés) = 3,000 tokens
- **Total: 3,400 tokens (économie 89%)**
