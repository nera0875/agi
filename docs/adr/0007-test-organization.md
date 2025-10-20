# ADR-0007: Test Organization Structure

**Date:** 2025-10-20
**Statut:** Proposed
**Author:** Architect

## Contexte

Le projet a **tests éparpillés** dans plusieurs locations:

**Problème actuel:**
```
backend/
├── test_graphql.py          (Script debug, pas pytest)
├── test_schema.py           (Script debug, pas pytest)
├── test_memory_optimization.py  (Script de simulation)
├── tests/
│   └── test_semantic_cache.py   (Pytest fixture)
└── agents/l1_observer/nodes/tests/
    ├── test_store_memory.py     (Pytest fixture)
    └── test_store_memory_simple.py

cortex/
├── test_mcp_detector.py     (Pytest fixture)
├── test_full_workflow.py    (Pytest fixture)
├── test_http_mcp_server.py  (Pytest fixture)
└── test_parser_mock.py      (Pytest fixture)

backend/scripts/
├── test_bootstrap_neurotransmitters.py  (Pytest fixture)
└── test_neurotransmitters.py            (Pytest fixture)
```

**Résultats de pytest:**
- 76 tests découverts (réussissent collecte)
- Tests à `backend/` ne sont PAS pytest (0 tests collectés)
- Cortex tests découverts mais tests à la racine `backend/` ignorés

**Incohérences:**
1. Scripts debug nommés `test_*.py` mais PAS fonctions de test
2. Vrais fixtures pytest dispersés
3. Imports relatifs cassés (`from services.x` nécessite sys.path)
4. Pas de `pytest.ini` pour configurer discovery

## Décision

**Restructurer tests en organisation cohérente:**

```
/home/pilote/projet/agi/
├── tests/                          # Root tests directory
│   ├── __init__.py
│   ├── conftest.py                 # Pytest global configuration
│   ├── pytest.ini                  # Pytest settings
│   │
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── test_memory_service.py  # Déplacé depuis backend/tests/
│   │   └── integration/
│   │       ├── test_graphql_integration.py  (ancien test_graphql.py)
│   │       └── test_memory_optimization.py  (ancien backend/test_*.py)
│   │
│   ├── cortex/
│   │   ├── __init__.py
│   │   ├── test_mcp_detector.py
│   │   ├── test_parser_mock.py
│   │   └── integration/
│   │       ├── test_full_workflow.py
│   │       └── test_http_mcp_server.py
│   │
│   └── agents/
│       ├── __init__.py
│       └── test_store_memory.py

backend/
├── scripts/
│   ├── test_bootstrap_neurotransmitters.py  (RENAMED → debug_bootstrap.py)
│   └── test_neurotransmitters.py            (RENAMED → debug_neurotransmitters.py)
└── (pas de test_*.py à la racine)

cortex/
└── (pas de test_*.py à la racine)
```

## Conséquences

### Positives
- **Cohérence pytest:** Tous tests vrais = fixtures pytest avec `assert`
- **Single source of truth:** Tests au 1 seul endroit (`/tests/`)
- **Import simplification:** `from backend.services.memory_service import X`
- **Pytest discovery automatique:** `pytest tests/` = collecte 100% tests
- **Scripts debug clarifiés:** Renommés `debug_*.py` (pas `test_`)
- **Organisation scalable:** Facile ajouter module + tests
- **Intégration CI/CD:** `pytest tests/ -v --cov` fonctionne directement

### Négatives
- **Migration non-triviale:** Move ~167 lignes de code
- **Imports relatifs à fixer:** `from services.X` → `from backend.services.X`
- **Documentation à mettre à jour:** README, .github/workflows/
- **Backups temporaires:** Besoin vérifier rien cassé

## Alternatives Considérées

### Option 1: Laisser comme c'est (Status Quo)
**Rejetée car:**
- Pytest découvre que 50% tests réels
- Scripts debug confondus avec vrais tests
- Import chaos (sys.path partout)
- Pas scalable (chaque nouveau test = configuration)

### Option 2: Créer `tests/` uniquement pour nouveaux tests
**Rejetée car:**
- Duplication (tests dans 2 locations)
- Confusion continue
- Maintenance difficile

### Option 3: Monter scripts debug à racine AGI
**Rejetée car:**
- Root directory pollué
- Pas standard Python

## Plan d'Implémentation

### Phase 1: Préparation (Code Agent)
```bash
# 1. Créer structure tests/
mkdir -p tests/backend/integration
mkdir -p tests/cortex/integration
mkdir -p tests/agents
touch tests/__init__.py tests/conftest.py
touch tests/backend/__init__.py
touch tests/cortex/__init__.py
touch tests/agents/__init__.py

# 2. Créer pytest.ini
cat > tests/pytest.ini << 'PYTEST'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --strict-markers --tb=short
PYTEST

# 3. Créer conftest.py pour fixtures communes
touch tests/conftest.py
```

### Phase 2: Move tests véritables (Code Agent)
```bash
# Tests avec fixtures pytest = move vers tests/
mv backend/tests/test_semantic_cache.py tests/backend/
mv backend/agents/l1_observer/nodes/tests/* tests/agents/
mv cortex/test_mcp_detector.py tests/cortex/
mv cortex/test_parser_mock.py tests/cortex/
mv cortex/test_full_workflow.py tests/cortex/integration/
mv cortex/test_http_mcp_server.py tests/cortex/integration/
mv backend/scripts/test_bootstrap_neurotransmitters.py tests/backend/integration/
mv backend/scripts/test_neurotransmitters.py tests/backend/integration/
```

### Phase 3: Rename scripts debug (Code Agent)
```bash
# Scripts debug = rename + move à scripts/
mv backend/test_graphql.py backend/scripts/debug_graphql.py
mv backend/test_schema.py backend/scripts/debug_schema.py
mv backend/test_memory_optimization.py backend/scripts/debug_memory_optimization.py
```

### Phase 4: Fix imports (Code Agent)
**Avant:**
```python
# backend/tests/test_semantic_cache.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.memory_service import cosine_similarity
```

**Après:**
```python
# tests/backend/test_semantic_cache.py
from backend.services.memory_service import cosine_similarity
```

**Patterns à chercher & fixer:**
- `from services.X` → `from backend.services.X`
- `from cortex.X` → `from cortex.X` (reste inchangé)
- `sys.path.insert()` → SUPPRIMER
- `Path(__file__).parent.parent` → Pas besoin

### Phase 5: Cleanup ancien structure (Code Agent)
```bash
# Supprimer dossiers vides
rmdir backend/tests/
rmdir backend/agents/l1_observer/nodes/tests/
```

### Phase 6: Vérifier pytest discover (Debug Agent)
```bash
cd /home/pilote/projet/agi
python3 -m pytest --collect-only
# Résultat attendu: 76+ items collected (pas 0)
```

### Phase 7: Documenter (Docs Agent)
- Update README.md → Section "Running Tests"
- Update .github/workflows/test.yml (si existe)
- Créer TESTING.md → Guide testing

## Imports Impactés

**Fichiers à fixer:**

1. `tests/backend/test_semantic_cache.py`
   - Avant: `from services.memory_service import cosine_similarity`
   - Après: `from backend.services.memory_service import cosine_similarity`

2. `tests/backend/integration/test_neurotransmitters.py`
   - Avant: Import système ad-hoc via scripts
   - Après: Imports classiques relatifs

3. `tests/cortex/test_parser_mock.py`
   - Avant: `sys.path.insert(0, '/home/pilote/projet/agi')`
   - Après: Imports directs

## Pytest Discovery Validation

**Avant migration:**
```bash
$ python3 -m pytest --collect-only
collected 76 items (1 error)
backend/test_graphql.py ... collected 0 items  # ❌ Scripts, pas tests
```

**Après migration:**
```bash
$ python3 -m pytest --collect-only
collected 76 items
tests/backend/test_semantic_cache.py ... 10 items
tests/backend/integration/ ... 3 items
tests/cortex/ ... 20+ items
tests/agents/ ... 40+ items
# ✅ 76 items = 100% discovered
```

## Configuration pytest.ini

```ini
[pytest]
# Chemin où pytest cherche
testpaths = tests

# Patterns pour découvrir tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Async support
asyncio_mode = auto

# Output verbeux + short traceback
addopts = -v --strict-markers --tb=short

# Markers custom (optionnel)
markers =
    integration: Integration tests
    unit: Unit tests
    slow: Slow tests
```

## Références

- pytest discovery: https://docs.pytest.org/en/stable/example/pythonpath.html
- pytest.ini: https://docs.pytest.org/en/stable/reference.html#ini-options-ref
- Test organization: https://docs.pytest.org/en/stable/goodpractices.html

