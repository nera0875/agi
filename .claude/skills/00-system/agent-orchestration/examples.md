# Agent Orchestration - Exemples Pratiques

## Exemple 1: Audit Backend Complet (Parallèle Avancée)

**Besoin:** Scanner 67 fichiers backend rapidement

**Approche CEO avec Phases:**

### PHASE 1 - UNDERSTANDING (10 agents × 20s = 20s total):
```python
# Scanner par pattern (diviser le travail)
for pattern in ['services/[a-d]*', 'services/[e-h]*', 'services/[i-l]*', ...]:
    Task(ask, f"""
    Scan backend/{pattern}.py

    DEADLINE: 20s
    SCOPE: List only classes + methods count
    PARTIAL OK: Yes

    Output: {{files: [...], class_count: N, methods: [...]}}
    """)
```

**Résultat:** 20s au lieu de 5min solo

---

## Exemple 2: Refactoring Mémoire (Feature Complex)

**Besoin:** Refactorer système L1/L2/L3

### PHASE 1 - UNDERSTANDING (3 agents):
```python
Task(ask, "backend/services/memory_service.py - Classes L1/L2, dependencies")
Task(ask, "backend/services/embedding_service.py - How used by memory")
Task(ask, "cortex/consolidation.py - Where L2/L3 called")
```

### PHASE 2 - RESEARCH (2 agents):
```python
Task(research, "exa: Redis vs PostgreSQL latency - best practices 2025")
Task(research, "context7: LangChain memory management patterns")
```

### PHASE 3 - ARCHITECTURE (1 agent):
```python
Task(architect, """
Refactor memory system based on:
- Current: L1 Redis, L2 PostgreSQL, L3 Neo4j
- Findings: [result from phase 1&2]

Design new architecture:
1. Split functions per layer
2. Reduce Redis→PG trips
3. Optimize Neo4j queries
Return: ADR + migration plan
""")
```

### PHASE 4 - IMPLEMENTATION (3 agents parallel):
```python
Task(code, "Backend: Refactor MemoryService - Layer separation")
Task(code, "DB: Migrations - Add indexes for L2 queries")
Task(code, "Backend: Update consolidation.py - Use new API")
```

### PHASE 5 - VALIDATION (2 agents):
```python
Task(debug, "Pytest backend/tests/test_memory_service.py")
Task(debug, "Integration tests - L1→L2→L3 flow")
```

### PHASE 6 - DOCUMENTATION:
```python
Task(docs, "Memory refactoring - Architecture + migration guide")
```

---

## Exemple 3: Feature UI Simple (Full-Stack Rapide)

**Besoin:** Ajouter page "MCP Tools Status"

**Skip Phases:** 1 (simple) + 2 (technologie connue)

### PHASE 3 - ARCHITECTURE:
```python
Task(architect, """
New page: MCP Tools Status
Show: Tool name, status (online/offline), latency

Design:
- Frontend: Page composant + TanStack table
- Backend: GraphQL query mcp_tools_status
- No DB changes

Estimated complexity: 2h
""")
```

### PHASE 4 - IMPLEMENTATION (2 agents parallel):
```python
Task(code, "Backend: GraphQL query mcp_tools_status + resolver")
Task(frontend, "Frontend: Page MCPToolsStatus - Table + status badges")
```

### PHASE 5 - VALIDATION:
```python
Task(debug, "Test backend query + frontend rendering")
```

### PHASE 6 - DOCUMENTATION:
```python
Task(docs, "Add MCP Tools Status page to README")
```

**Total:** ~2h vs 3h solo (30% economie)

---

## Exemple 4: Bug Fix Urgent (Minimal Pipeline)

**Besoin:** Fix crash sur query GraphQL users

**Minimal approach:** Skip 1, 2, 3

### PHASE 4 - IMPLEMENTATION:
```python
Task(code, """
Bug: users query crashes with 500 error
Files: backend/api/schema.py

1. Find users query resolver
2. Identify crash cause
3. Add error handling
4. Return fixed code
""")
```

### PHASE 5 - VALIDATION:
```python
Task(debug, "Pytest backend/tests/test_users_query.py")
```

**Total:** 10min vs 30min debug solo

---

## Exemple 5: Performance Optimization (Parallel Investigation)

**Besoin:** Slow GraphQL queries (>1s)

### PHASE 1 - UNDERSTANDING (4 agents):
```python
Task(ask, "backend/api/schema.py - All queries with N+1 potential")
Task(ask, "backend/services/graph_service.py - Neo4j queries structure")
Task(ask, "backend/services/memory_service.py - DB calls per query")
Task(ask, "backend/routes/*.py - API endpoints with DB")
```

### PHASE 2 - RESEARCH:
```python
Task(research, "exa: GraphQL N+1 detection tools")
Task(research, "context7: SQLAlchemy eager loading patterns")
```

### PHASE 3 - ARCHITECTURE:
```python
Task(architect, """
Optimize slow queries based on findings.
Recommend:
1. N+1 eliminations
2. Index additions
3. Query consolidations
""")
```

### PHASE 4 - IMPLEMENTATION (3 agents):
```python
Task(code, "Backend: Add eager loading to slow queries")
Task(code, "DB: Create missing indexes")
Task(code, "Backend: Add query caching layer")
```

### PHASE 5 - VALIDATION:
```python
Task(debug, "Benchmark before/after - queries latency")
```

**Result:** Identify + fix in 1h (vs 4h+ debug solo)

---

## Exemple 6: Problème avec Dépendances (Séquentiel Nécessaire)

**Besoin:** Ajouter authentification JWT

**Not parallel:** PHASE 2 dépend PHASE 1

```python
# PHASE 1 - UNDERSTANDING
Task(ask, "backend/core/security.py - Current auth implementation")
# ← Attendre résultat

# PHASE 2 - RESEARCH (basé sur PHASE 1)
Task(research, f"""
JWT best practices with current stack: {result_phase1}
Strawberry GraphQL authentication patterns
""")
# ← Attendre résultat

# PHASE 3 - ARCHITECTURE (basé sur PHASE 1+2)
Task(architect, f"""
Add JWT auth to current implementation: {result_phase1}
Based on best practices: {result_phase2}
""")
# ← Attendre résultat

# PHASE 4 - IMPLEMENTATION
Task(code, "Backend: Implement JWT middleware")
Task(code, "Backend: Update GraphQL schema - @require_auth")
# Parallèle maintenant (indépendant)

# PHASE 5 - VALIDATION
Task(debug, "Test JWT flow - create/refresh/validate tokens")
```

---

## Checklist Choix Agent

### Je dois faire quoi?
- Lire code existant → **ask**
- Chercher doc externe → **research**
- Designer solution → **architect**
- Coder backend Python → **code**
- Coder frontend React → **frontend**
- Tester + debug → **debug**
- Écrire documentation → **docs**
- Monitoring infrastructure → **sre**

### Qui appelle qui?
- **MOI** appelle agents
- **Agents** retournent JSON
- **MOI** agrège et décide phase suivante
- **Jamais:** Agent1 → Agent2 (uniquement MOI orchestre)

### Combien d'agents en parallèle?
- Read-only tasks: 10-20 agents OK
- Write operations: 1 agent/fichier MAX
- Database: Partitionner rows AVANT

### Deadline sur chaque Task?
- Scan rapide: 10-20s
- Research: 15s
- Plan architecture: 30s
- Code: 30-60s
- Tests: 20-30s

---

## Anti-Patterns à Éviter

❌ **Chaîner agents:**
```python
Task(ask, "Analyse backend")
Task(research, "...")  # Attendre résultat ask
Task(architect, "...")  # Attendre résultat research
# → Séquentiel lent!
```

✅ **Paralléliser indépendants:**
```python
Task(ask, "Analyse backend/services")  # Tous lancés
Task(ask, "Analyse backend/api")       # ensemble
Task(ask, "Analyse backend/routes")    # 3 agents = rapide
```

❌ **Prompts vagues:**
```python
Task(ask, "Regarde le code")
# → Agent ne sait pas quoi faire
```

✅ **Prompts précis:**
```python
Task(ask, """
backend/api/schema.py

1. Find all GraphQL mutations
2. List inputs/outputs
3. Check @require_auth present

Output: [{name, inputs, outputs, auth_required}]
""")
```

---

**Version:** 2025-10-20
