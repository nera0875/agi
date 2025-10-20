# Agent Orchestration Instructions

## Pipeline Phases (WORKFLOW AGENTS)

### ORDRE DES PHASES

```
┌─────────────────────────────────────────────┐
│ PHASE 1: UNDERSTANDING (parallel)           │
│ ask × N → Explorer codebase existant        │
│ Ex: ask×3 (backend, frontend, DB)           │
└─────────────────────────────────────────────┘
           ↓ MOI agrège résultats
┌─────────────────────────────────────────────┐
│ PHASE 2: RESEARCH (parallel)                │
│ research × N → Recherche externe            │
│ Ex: research×3 (exa patterns, context7      │
│     libs, fetch best practices)             │
└─────────────────────────────────────────────┘
           ↓ MOI agrège résultats
┌─────────────────────────────────────────────┐
│ PHASE 3: ARCHITECTURE (1-3 agents)          │
│ architect × 1-3 → Design solution           │
│ Ex: architect (plan général + ADR)          │
└─────────────────────────────────────────────┘
           ↓ MOI valide architecture
┌─────────────────────────────────────────────┐
│ PHASE 4: IMPLEMENTATION (parallel)          │
│ code/frontend × N → Coder features          │
│ Ex: code×5 (backend API, frontend UI,       │
│     DB migrations, tests, config)           │
└─────────────────────────────────────────────┘
           ↓ MOI agrège code
┌─────────────────────────────────────────────┐
│ PHASE 5: VALIDATION (parallel)              │
│ debug × N → Tests + fixes                   │
│ Ex: debug×3 (unit tests, integration, e2e)  │
└─────────────────────────────────────────────┘
           ↓ MOI vérifie qualité
┌─────────────────────────────────────────────┐
│ PHASE 6: DOCUMENTATION (single)             │
│ docs × 1 → README + API docs                │
└─────────────────────────────────────────────┘
```

## 8 Agents Disponibles

**Tous Haiku (cost-effective):**

1. **ask** - Exploration codebase interne (read-only)
2. **research** - Recherche externe (exa, fetch, context7)
3. **architect** - Design architecture, ADR, patterns
4. **code** - Implémentation backend/générale
5. **frontend** - Implémentation React/TypeScript
6. **debug** - Tests, validation, debugging
7. **docs** - Documentation technique
8. **sre** - Infrastructure, monitoring

## CHOIX AGENT PAR TYPE DE TÂCHE

### PHASE 1 - UNDERSTANDING

**ask** → Explorer codebase existant
- ✅ "Quels fichiers gèrent authentification ?"
- ✅ "Comment fonctionne le système mémoire actuel ?"
- ✅ "Où est implémenté le cache Redis ?"
- ❌ Recherche web (utiliser research)

### PHASE 2 - RESEARCH

**research** → Recherche externe avant architecture
- ✅ "Meilleures pratiques GraphQL Subscriptions 2025"
- ✅ "Documentation bibliothèque react-query"
- ✅ "Exemples Strawberry async resolvers"
- ❌ Exploration codebase interne (utiliser ask)

### PHASE 3 - ARCHITECTURE

**architect** → Design système, ADR, trade-offs
- ✅ "Comment architecturer notifications temps réel ?"
- ✅ "Refactoring système mémoire L1/L2/L3"
- ✅ "Choix entre WebSocket vs SSE"
- ❌ Implémentation (utiliser code/frontend)

### PHASE 4 - IMPLEMENTATION

**code** → Backend Python, API, DB, général
- ✅ Routes FastAPI
- ✅ GraphQL schema/mutations/queries (backend/api/schema.py)
- ✅ Services backend (backend/services/*)
- ✅ Migrations DB PostgreSQL
- ✅ Scripts Python généraux
- ✅ Configuration (.env, config.py)
- ❌ UI React (utiliser frontend)

**frontend** → React/TypeScript/shadcn/ui
- ✅ Composants React (frontend/src/components/*)
- ✅ Pages React (frontend/src/pages/*)
- ✅ Hooks Apollo Client (useQuery, useMutation, useSubscription)
- ✅ shadcn/ui components
- ✅ TanStack Table
- ✅ Styles Tailwind CSS
- ✅ TypeScript types frontend
- ❌ Backend API (utiliser code)
- ⚠️ **Respecte guidelines Figma** (code agent non)

### PHASE 5 - VALIDATION

**debug** → Tests, debugging, validation
- ✅ Pytest backend
- ✅ Tests intégration
- ✅ Debugging erreurs runtime
- ✅ Validation end-to-end
- ✅ Fix bugs identifiés
- ❌ Features nouvelles (utiliser code/frontend)

### PHASE 6 - DOCUMENTATION

**docs** → Documentation technique
- ✅ README.md
- ✅ Diagrammes architecture (Mermaid)
- ✅ API documentation
- ✅ CHANGELOG
- ❌ Code comments inline (fait par code/frontend)

### HORS PIPELINE - MONITORING

**sre** → Infrastructure, monitoring, DevOps
- ✅ Check santé PostgreSQL/Neo4j/Redis
- ✅ Analyse logs /tmp/*.log
- ✅ Coûts API (Anthropic, Voyage)
- ✅ Métriques performance
- ✅ Alertes système
- ❌ Features applicatives (utiliser code/frontend)

## RÈGLE D'OR: code vs frontend

**Utilise code si:**
- Fichier dans `backend/`
- Python .py
- FastAPI/GraphQL backend
- Database
- Scripts/config

**Utilise frontend si:**
- Fichier dans `frontend/src/`
- TypeScript .tsx/.ts
- React components
- Apollo Client
- shadcn/ui
- Tailwind CSS

**Feature full-stack = les DEUX en parallèle:**
```python
Task(code, "Backend: API endpoint")      # backend/
Task(frontend, "Frontend: UI component") # frontend/
```

## RÈGLES ANTI-BOOMERANG

1. **Agents NE S'APPELLENT JAMAIS entre eux**
2. **MOI seul** invoque agents (Task tool)
3. Agent retourne JSON → **MOI** décide next phase
4. Phases = barrières de synchronisation
5. Pas de délégation circulaire (A→B→C→A ❌)

## EXEMPLE CONCRET

**Feature: "Système notifications temps réel"**

**PHASE 1** (parallel):
```python
Task(ask, "Analyse backend/services/event*") → result1
Task(ask, "Analyse frontend/components/notif*") → result2
Task(ask, "Analyse DB schema notifications") → result3
```
→ MOI agrège: "Backend a EventEmitter, Frontend manque hook, DB manque table"

**PHASE 2** (parallel):
```python
Task(research, "exa: GraphQL Subscriptions best practices") → result1
Task(research, "context7: apollo/client useSubscription") → result2
Task(research, "exa code: Strawberry subscriptions examples") → result3
```
→ MOI agrège: "GraphQL Subscriptions = meilleure option"

**PHASE 3** (single):
```python
Task(architect, "Design notifications GraphQL Subscriptions + contexte") → architecture
```
→ MOI valide: "OK, 3 parties: backend subscription, frontend hook, DB migration"

**PHASE 4** (parallel):
```python
Task(code, "Backend: subscription onNotification") → code1
Task(frontend, "Frontend: useNotificationSubscription") → code2
Task(code, "DB: migration table notifications") → code3
```
→ MOI agrège: "3 parties codées"

**PHASE 5** (parallel):
```python
Task(debug, "Test backend subscription") → tests1
Task(debug, "Test frontend hook") → tests2
Task(debug, "Test integration e2e") → tests3
```
→ MOI vérifie: "Tous pass"

**PHASE 6** (single):
```python
Task(docs, "Documentation notifications temps réel") → docs
```
→ **Feature complète!**

## QUAND SKIP PHASES

**Phase 1 (ask)** - Skip si:
- Nouvelle feature from scratch (rien à explorer)
- Codebase déjà connue

**Phase 2 (research)** - Skip si:
- Stack technique connue
- Pattern simple/standard
- Pas besoin contexte externe

**Phase 3 (architect)** - Skip si:
- Bug fix simple
- Refactoring mineur
- Pattern déjà établi

**Phase 6 (docs)** - Skip si:
- Feature interne (pas user-facing)
- Tests/fixes mineurs

## ÉCONOMIE TOKENS

**Sans pipeline** (MOI fait tout):
- MOI: 5000 tokens × 6 étapes = 30,000 tokens

**Avec pipeline** (agents Haiku):
- MOI: 100 tokens réflexion + 50×6 agrégations = 400 tokens
- Agents: 500 tokens × 6 phases (isolés) = 3,000 tokens
- **Total: 3,400 tokens (économie 89%)**
