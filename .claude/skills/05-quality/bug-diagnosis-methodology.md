---
name: bug-diagnosis-methodology
category: quality
type: methodology
tags: [debugging, diagnosis, troubleshooting]
complexity: intermediate
---

# Bug Diagnosis Methodology

Méthodologie systématique pour diagnostiquer et résoudre bugs dans tout type de problème.

## 6-Step Diagnostic Framework

### Phase 1: REPRODUIRE

**Objectif:** Confirmer bug et obtenir stacktrace/logs détaillés.

```bash
# 1. Chercher logs
tail -100 /tmp/backend.log
journalctl -xe
tail -50 ~/.pm2/logs/app-error.log

# 2. Obtenir stacktrace complète
pytest tests/test_failing.py -v -s --tb=long

# 3. Conditions exactes
- Navigateur ? (Chrome, Firefox, Safari)
- Version Node/Python ?
- Version OS ?
- Données reproduisant bug ?
```

**Checklist Reproducibilité:**
```markdown
- [ ] Bug reproductible 100% ?
- [ ] Logs capturés ?
- [ ] Stacktrace complète obtenue ?
- [ ] Étapes exactes documentées ?
- [ ] Environnement identifié (dev/prod) ?
```

### Phase 2: ISOLER

**Objectif:** Localiser fichier/fonction exacte.

```bash
# 1. Grep pour trouver erreur
Grep: "ConnectionError" --type py -n
# Résultat: services/memory_service.py:145

# 2. Lire contexte
Read: backend/services/memory_service.py (lignes 140-150)

# 3. Vérifier imports
Grep: "from.*import\|import" dans memory_service.py

# 4. Dépendances directes
Grep: "MemoryService" pour voir où appelé
```

**Checklist Isolation:**
```markdown
- [ ] Fichier problématique identifié ?
- [ ] Ligne exacte localisée ?
- [ ] Contexte compris (before/after) ?
- [ ] Imports correctement résolus ?
- [ ] Dépendances circulaires ? (Grep imports)
```

### Phase 3: FORMULER HYPOTHÈSES

**Objectif:** Lister causes probables par probabilité.

**Format Standard:**
```markdown
## Hypothèses (analysées en ordre de probabilité)

### H1: X est null/undefined [PROBABILITÉ: 70%]
Raison: Ligne 145 fait response.data['key'] sans vérifier null
Indicateurs:
  - TypeError: 'NoneType' object is not subscriptable
  - Pas de check if response.data

### H2: Import manquant [PROBABILITÉ: 15%]
Raison: 'ConnectionError' pas importé
Indicateurs:
  - NameError: name 'ConnectionError' not defined
  - Grep montre pas d'import ConnectionError

### H3: Race condition async [PROBABILITÉ: 10%]
Raison: fetch() and process() pas synchronisés
Indicateurs:
  - Bug intermittent
  - Logs montrent timing issues

### H4: Database connection timeout [PROBABILITÉ: 5%]
Raison: Pool connexions limité
```

### Phase 4: VÉRIFIER HYPOTHÈSES

**Objectif:** Tester chaque hypothèse de façon isolée.

```python
# Test H1: response.data est null?
# Code test isolé
def test_hypothesis_1():
    """Vérifier si response.data peut être None"""
    response = fetch_from_api()
    print(f"response: {response}")
    print(f"response.data: {response.data}")
    # → Si None, H1 confirmée

# Exécution
python -c "exec(open('test_hypothesis_1.py').read())"
```

**Vérifications Systématiques:**
```bash
# Type checking
mypy backend/services/memory_service.py

# Linting
pylint backend/services/memory_service.py

# Syntax errors
python -m py_compile backend/services/memory_service.py

# Import resolution
python -c "from backend.services.memory_service import *"
```

### Phase 5: CORRIGER

**Objectif:** Implémenter fix pour cause racine confirmée.

**Format de correction:**
```python
# AVANT (code problématique)
def fetch_data():
    response = api.call()
    return response.data['key']  # ❌ Can crash if data is None

# APRÈS (code corrigé)
def fetch_data():
    response = api.call()
    if response is None or response.data is None:
        logger.warning("API returned None")
        return None

    return response.data.get('key')  # ✅ Safe access
```

**Checklist Fix:**
```markdown
- [ ] Root cause corrigée (pas symptôme) ?
- [ ] Pas de side effects non intentionnés ?
- [ ] Types sont corrects ?
- [ ] Logs ajoutés pour debug futur ?
- [ ] Documentation inline sur fix ?
```

### Phase 6: VALIDER

**Objectif:** Vérifier fix et prévenir régressions.

```bash
# 1. Test précis
pytest tests/test_memory_service.py::test_fetch_data -v

# 2. Tests connexes
pytest tests/test_memory_service.py -v

# 3. Couverture complète
pytest tests/ --cov=backend --cov-fail-under=85

# 4. Intégration
pytest tests/integration/ -v

# 5. Vérification manuelle
curl http://localhost:8000/api/endpoint
```

**Checklist Validation:**
```markdown
- [ ] Test unitaire spécifique passe ?
- [ ] Tests connexes toujours passent ?
- [ ] Couverture >= 85% ?
- [ ] Pas de nouvelles warnings ?
- [ ] Regession test créé (pour prévenir) ?
```

## Matrices de Diagnostic Rapides

### Backend Python Errors

| Erreur | Cause Probable | Vérification |
|--------|---|---|
| `TypeError: 'NoneType' object...` | Variable None non vérifiée | `if var is None:` |
| `ModuleNotFoundError: No module...` | Import manquant/path incorrect | `python -c "from module import *"` |
| `ConnectionError: Network...` | DB/API down ou credentials wrong | `psql` / `curl` test |
| `RuntimeError: Event loop...` | Async/await mismatch | Chercher `.run()` vs `await` |
| `ValueError: invalid literal...` | String->int conversion échouée | Check input types, cast correctly |

### Frontend React Errors

| Erreur | Cause Probable | Vérification |
|--------|---|---|
| `Cannot read property X of undefined` | State pas initialisé | Check useState default |
| `Missing dependency X in useEffect` | Hook dépendance oubliée | Add to dependency array |
| `Hooks called outside FC` | Hook dans condition/loop | Move hook to top level |
| `CORS error` | Backend CORS policy | Check `Access-Control-Allow-*` |
| `Blank screen / white page` | Error boundary hit | F12 console errors |

### GraphQL Errors

| Erreur | Cause Probable | Vérification |
|--------|---|---|
| `Field does not exist` | Typo schema ou pas implémenté | Vérifier schema.py |
| `Cannot return null for non-null field` | Resolver retourne None | Add non-null check |
| `Variable type mismatch` | Query variable type incorrect | Check fragment/query |
| `Unauthorized` | JWT/auth token invalid | Verify token headers |

### Database Errors

| Erreur | Cause Probable | Vérification |
|--------|---|---|
| `Connection timeout` | Pool exhausted / DB slow | `SELECT * FROM pg_stat_activity;` |
| `Deadlock detected` | Transaction conflict | Check transaction isolation |
| `Constraint violation` | Unique/FK constraint | Verify data schema |
| `Disk full` | Database storage full | `df -h` / `du -sh /var/lib/postgresql` |

## Tools & Commands Quick Reference

### Logging & Tailing

```bash
# Real-time logs with grep
tail -f /tmp/backend.log | grep ERROR

# Last 100 lines
tail -100 /tmp/backend.log

# Search in logs
grep "ConnectionError" /tmp/backend.log | head -20

# Timestamp filter
grep "2025-10-20 15:" /tmp/backend.log
```

### Python Debugging

```bash
# Direct code execution
python -c "print(variable_test)"

# Import verification
python -c "from module import func; print(func)"

# Type checking
mypy file.py --strict

# Profiling slow function
python -m cProfile -s cumtime script.py | head -30
```

### Database Queries

```bash
# Active connections
psql -U agi_user -d agi_db -c "SELECT * FROM pg_stat_activity;"

# Slow queries
psql -U agi_user -d agi_db -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Table size
psql -U agi_user -d agi_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### API Testing

```bash
# GraphQL test
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ healthCheck { service status } }"}'

# REST test
curl -v http://localhost:8000/api/memory/1

# Headers debug
curl -i -H "Authorization: Bearer TOKEN" http://localhost:8000/api/endpoint
```

## Communication Format

**Rapport de diagnostic standard:**
```markdown
## Bug Description
[Symptôme observé]

## Reproduction Steps
1. [Étape 1]
2. [Étape 2]
3. [Erreur occurs here]

## Root Cause Analysis
[Explication technique avec hypothèses testées]

## Affected Code
File: path/to/file.py:123
Function: function_name()

## Fix Applied
[Explication du fix]

## Validation
- [ ] Test case created
- [ ] Manual verification done
- [ ] No regressions detected

## Prevention
[Suggestions pour éviter futur]
```

## Anti-Patterns to Avoid

```markdown
❌ "It works on my machine" (pas reproductible?)
❌ "Let me add logging everywhere" (scattered debugging)
❌ "I'll rewrite this module" (premature refactoring)
❌ "Probably a typo" (guess-based fixing)
❌ "Works now, let's ship" (no regression tests)
```

## Checklist: Complete Diagnosis

```markdown
- [ ] Bug reproductible 100% ?
- [ ] Exact file/line identified ?
- [ ] Root cause (not symptom) found ?
- [ ] 3+ hypotheses tested ?
- [ ] Fix deployed to isolated test ?
- [ ] Regression test created ?
- [ ] Full test suite still passing ?
- [ ] Documentation updated ?
- [ ] Team notified of fix ?
```
