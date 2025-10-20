---
name: agent-orchestration
description: Pipeline 6 phases, 8 agents, orchestration workflow, MCPs
tags: [agents, orchestration, workflow, pipeline, task-decomposition, mcps]
priority: 100
load: auto
---

# Agent Orchestration

## Principe Anti-Boomerang

- **Phases** = séquentielles (ordre strict)
- **Agents dans phase** = parallèles (×10-20 simultanés)
- **MOI seul** orchestre, agents ne s'appellent JAMAIS

---

## 6 Phases du Pipeline

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
│ Ex: research×3 (exa, context7, fetch)       │
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
│ Ex: code×5 (backend API, frontend UI, DB)   │
└─────────────────────────────────────────────┘
           ↓ MOI agrège code

┌─────────────────────────────────────────────┐
│ PHASE 5: VALIDATION (parallel)              │
│ debug × N → Tests + fixes                   │
│ Ex: debug×3 (unit, integration, e2e)        │
└─────────────────────────────────────────────┘
           ↓ MOI vérifie qualité

┌─────────────────────────────────────────────┐
│ PHASE 6: DOCUMENTATION (single)             │
│ docs × 1 → README + API docs                │
└─────────────────────────────────────────────┘
```

---

## 8 Agents Disponibles

| Agent | Rôle | Phase(s) |
|-------|------|----------|
| **ask** | Exploration codebase interne (read-only) | 1 |
| **research** | Recherche externe (exa, fetch, context7) | 2 |
| **architect** | Design architecture, ADR, patterns | 3 |
| **code** | Implémentation backend/Python | 4 |
| **frontend** | Implémentation React/TypeScript | 4 |
| **debug** | Tests, validation, debugging | 5 |
| **docs** | Documentation technique | 6 |
| **sre** | Infrastructure, monitoring (hors pipeline) | - |

---

## Choix Agent par Type de Tâche

### PHASE 1 - UNDERSTANDING (ask)

Explorer codebase existant (read-only):
- ✅ "Quels fichiers gèrent authentification ?"
- ✅ "Comment fonctionne le système mémoire actuel ?"
- ✅ "Où est implémenté le cache Redis ?"
- ❌ Recherche web (utiliser research)

### PHASE 2 - RESEARCH (research)

Recherche externe avant architecture:
- ✅ "Meilleures pratiques GraphQL Subscriptions 2025"
- ✅ "Documentation bibliothèque react-query"
- ✅ "Exemples Strawberry async resolvers"
- ❌ Exploration codebase interne (utiliser ask)

### PHASE 3 - ARCHITECTURE (architect)

Design système, ADR, trade-offs:
- ✅ "Comment architecturer notifications temps réel ?"
- ✅ "Refactoring système mémoire L1/L2/L3"
- ✅ "Choix entre WebSocket vs SSE"
- ❌ Implémentation (utiliser code/frontend)

### PHASE 4 - IMPLEMENTATION

**code** → Backend Python, API, DB, général:
- ✅ Routes FastAPI
- ✅ GraphQL schema/mutations/queries
- ✅ Services backend (backend/services/*)
- ✅ Migrations DB PostgreSQL
- ✅ Scripts Python, configuration
- ❌ UI React (utiliser frontend)

**frontend** → React/TypeScript/shadcn/ui:
- ✅ Composants React (frontend/src/components/*)
- ✅ Pages React (frontend/src/pages/*)
- ✅ Hooks Apollo Client
- ✅ shadcn/ui components, TanStack Table
- ✅ Styles Tailwind CSS, TypeScript types
- ❌ Backend API (utiliser code)
- ⚠️ Respecte guidelines Figma

### PHASE 5 - VALIDATION (debug)

Tests, debugging, validation:
- ✅ Pytest backend
- ✅ Tests intégration, end-to-end
- ✅ Debugging erreurs runtime
- ✅ Fix bugs identifiés
- ❌ Features nouvelles (utiliser code/frontend)

### PHASE 6 - DOCUMENTATION (docs)

Documentation technique:
- ✅ README.md
- ✅ Diagrammes architecture (Mermaid)
- ✅ API documentation
- ✅ CHANGELOG
- ❌ Code comments inline (fait par code/frontend)

### HORS PIPELINE - MONITORING (sre)

Infrastructure, monitoring, DevOps:
- ✅ Check santé PostgreSQL/Neo4j/Redis
- ✅ Analyse logs /tmp/*.log
- ✅ Coûts API (Anthropic, Voyage)
- ✅ Métriques performance, alertes système
- ❌ Features applicatives (utiliser code/frontend)

---

## Règle d'Or: code vs frontend

### Utilise code si:
- Fichier dans `backend/`
- Python .py
- FastAPI/GraphQL backend
- Database, scripts/config

### Utilise frontend si:
- Fichier dans `frontend/src/`
- TypeScript .tsx/.ts
- React components
- Apollo Client, shadcn/ui
- Tailwind CSS

### Feature full-stack = les DEUX en parallèle:
```python
Task(code, "Backend: API endpoint")      # backend/
Task(frontend, "Frontend: UI component") # frontend/
```

---

## Règles Anti-Boomerang

1. **Agents NE S'APPELLENT JAMAIS entre eux**
2. **MOI seul** invoque agents (Task tool)
3. Agent retourne JSON → **MOI** décide next phase
4. Phases = barrières de synchronisation
5. Pas de délégation circulaire (A→B→C→A ❌)

---

## Exemple Concret: Système Notifications Temps Réel

### PHASE 1 (parallel):
```python
Task(ask, "Analyse backend/services/event*") → result1
Task(ask, "Analyse frontend/components/notif*") → result2
Task(ask, "Analyse DB schema notifications") → result3
```
→ MOI agrège: "Backend a EventEmitter, Frontend manque hook, DB manque table"

### PHASE 2 (parallel):
```python
Task(research, "exa: GraphQL Subscriptions best practices") → result1
Task(research, "context7: apollo/client useSubscription") → result2
Task(research, "exa code: Strawberry subscriptions examples") → result3
```
→ MOI agrège: "GraphQL Subscriptions = meilleure option"

### PHASE 3 (single):
```python
Task(architect, "Design notifications GraphQL Subscriptions") → architecture
```
→ MOI valide: "OK, 3 parties: backend subscription, frontend hook, DB migration"

### PHASE 4 (parallel):
```python
Task(code, "Backend: subscription onNotification") → code1
Task(frontend, "Frontend: useNotificationSubscription") → code2
Task(code, "DB: migration table notifications") → code3
```
→ MOI agrège: "3 parties codées"

### PHASE 5 (parallel):
```python
Task(debug, "Test backend subscription") → tests1
Task(debug, "Test frontend hook") → tests2
Task(debug, "Test integration e2e") → tests3
```
→ MOI vérifie: "Tous pass"

### PHASE 6 (single):
```python
Task(docs, "Documentation notifications temps réel") → docs
```
→ **Feature complète!**

---

## Quand Skip Phases

| Phase | Skip si |
|-------|---------|
| **1 - ask** | Nouvelle feature from scratch (rien à explorer) ou Codebase déjà connue |
| **2 - research** | Stack technique connue ou Pattern simple/standard ou Pas besoin contexte externe |
| **3 - architect** | Bug fix simple ou Refactoring mineur ou Pattern déjà établi |
| **6 - docs** | Feature interne (pas user-facing) ou Tests/fixes mineurs |

---

## Économie Tokens

### Sans pipeline (MOI fait tout):
- MOI: 5000 tokens × 6 étapes = **30,000 tokens**

### Avec pipeline (agents Haiku):
- MOI: 100 tokens réflexion + 50×6 agrégations = 400 tokens
- Agents: 500 tokens × 6 phases (isolés) = 3,000 tokens
- **Total: 3,400 tokens (économie 89%)**

---

## Donner Accès MCPs aux Agents

### Découverte Critique
Agents n'héritent PAS automatiquement des MCPs.

### Solution: Spécifier MCPs dans frontmatter `tools:`

```markdown
---
name: research
description: Agent de recherche externe
model: haiku
tools: Read, Glob, Grep, mcp__exa__web_search_exa, mcp__exa__get_code_context_exa, mcp__smithery-ai-fetch__fetch_url, mcp__upstash-context-7-mcp__get-library-docs
---
```

### MCPs Disponibles (Projet)

**Dans .mcp.json:**
- `mcp__agi-tools__*` - Tools AGI custom (think, memory, database, control)
- `mcp__exa__web_search_exa` - Recherche web Exa
- `mcp__exa__get_code_context_exa` - Context code Exa
- `mcp__smithery-ai-fetch__fetch_url` - Fetch URLs
- `mcp__upstash-context-7-mcp__get-library-docs` - Docs bibliothèques

### Agents et Leurs MCPs

| Agent | MCPs Nécessaires |
|-------|------------------|
| **research** | ✅ exa, fetch, context7 (recherche externe) |
| **ask** | ❌ Aucun (explore codebase local) |
| **architect** | ❌ Aucun (design interne) |
| **code** | ❌ Aucun (implémentation) |
| **frontend** | ❌ Aucun (UI React) |
| **debug** | ❌ Aucun (tests) |
| **docs** | ❌ Aucun (documentation) |
| **sre** | ⚠️ Optionnel (monitoring externe) |

### Règle d'Or
**Si agent doit accéder données/services externes → Ajouter MCPs au frontmatter `tools:`**

**Sinon → Outils de base suffisent (Read, Write, Edit, Bash, Glob, Grep)**

---

## Stratégie Agents (Réflexion avant Exécution)

### ÉTAPE 1 - RÉFLÉCHIR (MOI, 100 tokens):
```
think("comment résoudre X?")
→ Décomposer en micro-tâches
→ Identifier ressources (fichiers, DB rows)
→ Vérifier indépendance (conflits?)
→ Partitionner si write operations
```

### ÉTAPE 2 - PROMPTS ULTRA-PRÉCIS:
```
PAS: "Analyse ces fichiers"
OUI: "Fichier: X.py
      1. Bash(wc -l X.py)
      2. Parse 'XXX file.py'
      3. Extract XXX
      4. Return {lines: XXX}"
```

### ÉTAPE 3 - PARALLÉLISER INTELLIGEMMENT:
```
Read-only: N = min(ressources, 20)
Write: 1 fichier = 1 agent MAX
Database: Partitionner rows AVANT
```

### ÉTAPE 4 - LANCER + AGRÉGER (500 tokens agents isolés):
```
Task × 10 en PARALLÈLE
→ Attendre tous résultats
→ Agréger + Synthétiser (50 tokens retour)
```

### RÉSULTAT: 80% économie tokens vs MOI fait tout

### Règles Conflits:
- 1 fichier = 1 agent (écriture)
- Agents = tâches INDÉPENDANTES
- Si dépendances → Séquentiel
- Si doute → 1 seul agent

---

## Checklist Invocation Agent

✅ **Avant de lancer:**
- [ ] Tâche ULTRA-PRÉCISE (pas floue)
- [ ] Scope clair (quoi faire, pas plus)
- [ ] Ressources identifiées
- [ ] Pas de dépendances circulaires
- [ ] MCPs nécessaires spécifiés (si external)

✅ **Agents lancés:**
- [ ] Parallèles si indépendants
- [ ] Séquentiels si dépendances
- [ ] Deadline stricte inclus

✅ **Résultats agrégés:**
- [ ] JSON parsé
- [ ] Inconsistences détectées
- [ ] Next phase décidée
- [ ] Partial results acceptés

---

## Format Prompt Standard

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

---

**Dernière mise à jour:** 2025-10-20
**Source:** CLAUDE.md (lignes 426-760)
