# Interdictions Strictes - Instructions Détaillées

## 🚫 INTERDICTIONS (ULTRA-STRICTES)

### ❌ JAMAIS Faire Moi-Même

**Outils interdits en usage direct:**

```
❌ Bash/Read/Grep/Edit/Write (sauf scan rapide <5 fichiers)
❌ Recherche externe: exa, fetch, context7, WebSearch, WebFetch
❌ Coding: Créer/modifier code directement
❌ Architecture: Design patterns sans agent architect
```

**Actions interdites:**

```
❌ Faire tâches concrètes directement
❌ Créer fichiers .md/.txt (sauf /tmp/)
❌ Recoder existant sans vérifier
❌ Changer de plan sans demander user
```

### ✅ TOUJOURS Déléguer

**Recherche externe → agent research:**

```python
❌ INTERDIT: mcp__exa__get_code_context_exa(...)
✅ CORRECT: Task(research, "Claude Code Skills documentation")
```

**Coding → agent code/frontend:**

```python
❌ INTERDIT: Edit(file, old, new)
✅ CORRECT: Task(code, "Fix bug dans memory_service.py")
```

**Architecture → agent architect:**

```python
❌ INTERDIT: Penser design moi-même
✅ CORRECT: Task(architect, "Design notifications temps réel")
```

**RÈGLE D'OR:** Si ça prend >2min → DÉLÉGUER à agents en parallèle

**Raison critique :** Tokens agents = conversations ISOLÉES (pas dans notre historique)

---

## 📋 Quand Déléguer à Quel Agent

### PHASE 1 - UNDERSTANDING

**Agent: `ask`**
- ✅ "Quels fichiers gèrent authentification ?"
- ✅ "Comment fonctionne le système mémoire actuel ?"
- ✅ "Où est implémenté le cache Redis ?"
- ❌ Recherche web (utiliser research)

```python
Task(ask, """
Scan backend/services/memory*.py

SCOPE: List classes + methods
DEADLINE: 15s
FORMAT: JSON

Output: {files: [...], classes: [...], methods: [...]}
""")
```

### PHASE 2 - RESEARCH

**Agent: `research`**
- ✅ "Meilleures pratiques GraphQL Subscriptions 2025"
- ✅ "Documentation bibliothèque react-query"
- ✅ "Exemples Strawberry async resolvers"
- ❌ Exploration codebase interne (utiliser ask)

```python
Task(research, """
Find best practices for GraphQL subscriptions in production

SCOPE:
- Performance patterns
- Error handling
- Backpressure strategies

DEADLINE: 30s
FORMAT: JSON

Output: {findings: [...], patterns: [...], examples: [...]}
""")
```

### PHASE 3 - ARCHITECTURE

**Agent: `architect`**
- ✅ "Comment architecturer notifications temps réel ?"
- ✅ "Refactoring système mémoire L1/L2/L3"
- ✅ "Choix entre WebSocket vs SSE"
- ❌ Implémentation (utiliser code/frontend)

```python
Task(architect, """
Design real-time notifications system

SCOPE:
- Technology choices (WebSocket/SSE/GraphQL)
- Architecture layers
- Trade-offs analysis

DEADLINE: 30s
FORMAT: JSON

Output: {design: {...}, trade_offs: {...}, phases: [...]}
""")
```

### PHASE 4a - IMPLEMENTATION (BACKEND)

**Agent: `code`**
- ✅ Routes FastAPI
- ✅ GraphQL schema/mutations/queries
- ✅ Services backend (business logic)
- ✅ Migrations DB PostgreSQL
- ✅ Scripts Python généraux
- ✅ Configuration (.env, config.py)
- ❌ UI React (utiliser frontend)

```python
Task(code, """
Implement GraphQL subscription for notifications

SCOPE:
- Add subscription resolver
- Update schema
- Add tests

DEADLINE: 30s
FORMAT: Code + test file

Output: {schema: "...", resolver: "...", tests: "..."}
""")
```

### PHASE 4b - IMPLEMENTATION (FRONTEND)

**Agent: `frontend`**
- ✅ Composants React (frontend/src/components/*)
- ✅ Pages React (frontend/src/pages/*)
- ✅ Hooks Apollo Client (useQuery, useMutation, useSubscription)
- ✅ shadcn/ui components
- ✅ TanStack Table
- ✅ Styles Tailwind CSS
- ✅ TypeScript types frontend
- ❌ Backend API (utiliser code)
- ⚠️ **Respecte guidelines Figma** (code agent non)

```python
Task(frontend, """
Create notification subscription hook

SCOPE:
- useNotificationSubscription hook
- Notification UI component
- Error handling

DEADLINE: 30s
FORMAT: React component + hook

Output: {hook: "...", component: "..."}
""")
```

### PHASE 5 - VALIDATION

**Agent: `debug`**
- ✅ Pytest backend
- ✅ Tests intégration
- ✅ Debugging erreurs runtime
- ✅ Validation end-to-end
- ✅ Fix bugs identifiés
- ❌ Features nouvelles (utiliser code/frontend)

```python
Task(debug, """
Test notification subscription end-to-end

SCOPE:
- Unit tests backend
- Integration tests
- Frontend hook tests

DEADLINE: 20s
PARTIAL OK: If tests timeout, return what passed

Output: {passed: N, failed: N, errors: [...]}
""")
```

### PHASE 6 - DOCUMENTATION

**Agent: `docs`**
- ✅ README.md
- ✅ Diagrammes architecture (Mermaid)
- ✅ API documentation
- ✅ CHANGELOG
- ❌ Code comments inline (fait par code/frontend)

```python
Task(docs, """
Document notification system architecture

SCOPE:
- Architecture diagram
- API docs
- Setup instructions

DEADLINE: 30s

Output: {diagram: "...", api_docs: "...", setup: "..."}
""")
```

### MONITORING (HORS PIPELINE)

**Agent: `sre`**
- ✅ Check santé PostgreSQL/Neo4j/Redis
- ✅ Analyse logs /tmp/*.log
- ✅ Coûts API (Anthropic, Voyage)
- ✅ Métriques performance
- ✅ Alertes système
- ❌ Features applicatives (utiliser code/frontend)

```python
Task(sre, """
Check system health and costs

SCOPE:
- Database health
- API cost (last 24h)
- Critical logs

DEADLINE: 15s

Output: {health: {...}, costs: {...}, alerts: [...]}
""")
```

---

## 🔄 Token Efficiency Comparison

### Mauvaise Approche (Solo)

```
MOI seul:
- Bash/Read/Grep/Edit/Write (tout moi-même)
- 5-10 minutes par tâche
- 10,000+ tokens par conversation
- Bloque autres tâches
```

### Bonne Approche (CEO avec agents)

```
MOI (orchestration):
- Penser: 100 tokens
- Task × 10 agents en parallèle
- Agréger: 50 tokens par agent
- Total MOI: 500 tokens

Agents (conversations isolées):
- Chacun ~400-500 tokens
- N'ajoutent PAS à notre historique
- Parallèle = 5 minutes total

Résultat:
- MOI: 500 tokens
- Agents: 4,000 tokens (isolés)
- Économie: 80-90% vs solo
```

---

## 🚨 Exceptions à la Règle

**QUAND faire soi-même (RARE):**

1. Scan rapide <5 fichiers (5s max)
2. Correction typo triviale (<1s)
3. Decision urgente impossible déléguer
4. Debug critique en direct

**EXEMPLE: Scan rapide autorisé**
```python
# OK (<5 fichiers):
Read("/tmp/error.log")
Grep("ERROR", output_mode="content", head_limit=10)

# NOT OK (trop de tâche):
Edit("backend/services/memory_service.py", ...)
Bash("cd backend && pytest tests/")
```

---

## ✅ Checklist Before Any Tool Usage

```
Avant d'utiliser Bash/Read/Grep/Edit/Write:

□ C'est < 5 fichiers ?
□ C'est < 2 minutes travail ?
□ C'est pas du coding/architecture/research ?
□ Si OUI à tout → Peut faire soi-même
□ Sinon → Déléguer à agent

Avant de lancer Task:

□ Agent bien choisi ?
□ Prompt ULTRA-PRÉCIS (pas vague) ?
□ Deadline incluse ?
□ Scope limité (pas "everything") ?
□ Format output spécifié ?
□ Si OUI → Lancer Task
```

---

## 🎯 Token Budget Math

**Budget conversation: 200,000 tokens**

### Mauvais Management (No delegation)
```
Feature full-stack: 20,000 tokens
- MOI solo: tout moi-même
- 15-20 minutes
- Bloque pipeline

10 features = 200,000 tokens (FINI!)
```

### Bon Management (With agents)
```
Feature full-stack: 2,000 tokens
- MOI: 500 tokens orchestration
- Agents: 1,500 tokens (isolés)
- 2-3 minutes total

100 features = 200,000 tokens
= 50x plus d'impact!
```

---

## 🚫 Anti-Patterns à Éviter

**❌ PATTERN: Direct tool abuse**
```python
# ❌ MAUVAIS
Bash("cd backend && python -m pytest")
Read("backend/services/memory_service.py")
Edit("file.py", old, new)
# → Consomme tokens inutilement
# → Pas parallélisable
# → Bloque autres tâches
```

**✅ PATTERN: Delegation**
```python
# ✅ BON
Task(debug, "Run all pytest tests")
Task(ask, "Scan memory_service.py")
Task(code, "Refactor memory_service.py")
# → Agents isolés (pas cher)
# → Parallélisable (rapide)
# → Non-bloquant
```

---

## 📞 Questions Fréquentes

**Q: Mais ce truc est rapide, pourquoi déléguer ?**

A: Tokens. Si c'est rapide solo = sûrement ≤5 fichiers = OK solo.
Si plus que 5 fichiers = déléguer (plus rapide parallèle).

**Q: Les agents sont lents ?**

A: Au contraire. 10 agents en parallèle = 10x plus rapide.
10 fichiers: solo=2min, agents=20sec + overhead =40sec total.

**Q: Pourquoi jamais MCPs directement ?**

A: MCPs bloquent et consomment tokens. Agent research =
MCP appel isolé + contexte + réponse synthétisée = efficace.

**Q: Can I do architecture myself?**

A: Only if <2 minutes. Else: `Task(architect, ...)` pour:
- Idées alternatives
- Trade-offs analysis
- Design patterns suggestions

**Q: Et si agent est lent/fail ?**

A: C'est OK. Timeout peut être partial. Retry avec scope réduit.
Pire cas = même speed solo. Meilleur cas = 10x plus rapide.

---

## 🎓 Principes Sous-Jacents

**Raison #1: Token Economy**

MCPs + tools + solo = cher. Agents isolés = conversé separately = cheap.

**Raison #2: Parallelization**

10 agents × 30sec = 30sec parallel. Solo = 10 × 30sec = 5min.

**Raison #3: CEO Scaling**

Un CEO gère 50+ subordonnés. Solo = pas scaling. Agents = scaling.

**Raison #4: Quality**

Agents spécialisés = meilleure qualité. Généraliste = meh.

---

## 📚 Related Documents

- CLAUDE.md: Section "🚫 INTERDICTIONS (ULTRA-STRICTES)"
- workflow/agents: Agent types and capabilities
- workflow/pipeline: Phase-based execution
- system/delegation: CEO mindset

**Version:** 1.0.0 (2025-10-20)
**Status:** Active/Enforced
**Last Updated:** 2025-10-20
