# Agent Orchestration Skill

Orchestration framework pour diriger 8 agents Haiku en pipeline 6 phases.

## Fichiers

- **agent-orchestration.md** - Guide complet (phases, agents, MCPs)
- **examples.md** - Exemples concrets (audit, refactoring, features)
- **quick-reference.txt** - Cheat sheet d'invocation

## Concept Clé

**Pipeline 6 Phases:**
1. Understanding (explore)
2. Research (learn)
3. Architecture (design)
4. Implementation (code)
5. Validation (test)
6. Documentation (doc)

**Parallélisation Maximale:**
- Phases = séquentielles
- Agents dans phase = parallèles (×10-20)
- MOI orchestre, agents ne s'appellent jamais

## Agents Disponibles

| Agent | Rôle |
|-------|------|
| ask | Explore codebase interne |
| research | Recherche externe (exa, fetch, context7) |
| architect | Design système, ADR |
| code | Backend Python/FastAPI |
| frontend | React/TypeScript |
| debug | Tests, validation |
| docs | Documentation |
| sre | Infrastructure, monitoring |

## Cas d'Usage Rapide

### Audit backend
```python
Task(ask, "backend/services/* - List classes")
Task(ask, "backend/api/* - List endpoints")
Task(ask, "backend/routes/* - List routes")
```
→ 20s parallèle vs 5min solo

### Feature full-stack
```python
# Phase 1: explore
Task(ask, "current auth system")

# Phase 2: research
Task(research, "JWT best practices")

# Phase 3: design
Task(architect, "JWT auth design")

# Phase 4: code (parallèle!)
Task(code, "Backend: JWT middleware")
Task(frontend, "Frontend: Login component")

# Phase 5: test
Task(debug, "Test JWT flow")

# Phase 6: doc
Task(docs, "Auth documentation")
```

### Bug fix urgent
```python
# Skip phases 1-3, go direct
Task(code, "Fix users query crash")
Task(debug, "Test users query")
```

## MCPs Configuration

**Pour agent research:**
```markdown
---
name: research
tools: Read, Glob, Grep, mcp__exa__web_search_exa, mcp__exa__get_code_context_exa, mcp__smithery-ai-fetch__fetch_url, mcp__upstash-context-7-mcp__get-library-docs
---
```

**Pour autres agents:**
```markdown
---
name: code
tools: Read, Write, Edit, Bash, Glob, Grep
---
```

## Règles d'Or

1. **MOI seul** invoque agents
2. **Agents** retournent JSON
3. **MOI** orchestre phases
4. **Jamais** Agent→Agent (seulement MOI)
5. **Parallèle** si indépendant
6. **Séquentiel** si dépendance
7. **Prompt** ultra-précis, pas vague
8. **Deadline** stricte sur chaque task

## Économie Tokens

- Solo approach: 30,000 tokens
- Agent pipeline: 3,400 tokens
- **Économie: 89%**

Raison: Agents = conversations isolées (pas dans historique)

## Quick Decision Tree

```
Besoin → Skip phases? → Quelle phase? → Quel(s) agent(s)?

1. Lire code → ask
2. Chercher doc → research
3. Designer → architect
4. Coder backend → code
5. Coder frontend → frontend
6. Tester → debug
7. Écrire docs → docs
```

## Links

- **Full Guide:** agent-orchestration.md
- **Examples:** examples.md
- **CLAUDE.md Reference:** Lines 426-760

---

**Load:** auto (chargé automatiquement)
**Priority:** 100 (système critique)
**Tags:** agents, orchestration, workflow, pipeline, mcps
