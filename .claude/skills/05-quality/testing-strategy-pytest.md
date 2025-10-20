---
name: testing-strategy-pytest
category: quality
type: methodology
tags: [testing, pytest, quality-assurance]
complexity: intermediate
---

# Testing Strategy - Pytest Framework

Stratégie complète de testing pour projet Python/FastAPI utilisant pytest.

## Principes Fondamentaux

### Couverture de Tests Hiérarchique

```markdown
100% ❌ (coûteux, slow)
└─ 85% ✅ (target idéal)
   ├─ Critical paths (100%)
   ├─ Edge cases (90%)
   └─ Nice-to-have (70%)
```

### Types de Tests

**Unit Tests** (60% couverture)
- 1 fonction = 1 test
- Mocks dépendances externes
- Rapide (<1s par test)
- Exécution: `pytest tests/unit/ -v`

**Integration Tests** (25% couverture)
- APIs + Database
- Workflows réalistes
- Moyen (<5s par test)
- Exécution: `pytest tests/integration/ -v`

**End-to-End Tests** (15% couverture)
- Scénarios utilisateur complets
- Lent (<30s par test)
- Exécution: `pytest tests/e2e/ -v`

## Structure Pytest

### Arborescence Recommended

```python
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures partagées
│   ├── unit/
│   │   ├── test_memory_service.py
│   │   ├── test_graph_service.py
│   │   └── test_auth.py
│   ├── integration/
│   │   ├── test_memory_api.py
│   │   └── test_graph_api.py
│   └── e2e/
│       └── test_user_workflows.py
```

### conftest.py - Fixtures Centralisées

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_db():
    """Database test unique pour session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(test_db):
    """Session DB fraîche par test"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_memory_service(db_session):
    """Mock MemoryService"""
    return MemoryService(db_session)

@pytest.fixture
async def client():
    """FastAPI test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Patterns de Testing

### 1. Unit Tests - Service Layer

```python
class TestMemoryService:
    """Suite de tests pour MemoryService"""

    def test_store_memory_creates_entry(self, mock_memory_service):
        """Store memory crée entrée en DB"""
        # Arrange
        memory_data = {"content": "test", "type": "short_term"}

        # Act
        result = mock_memory_service.store_memory(memory_data)

        # Assert
        assert result.id is not None
        assert result.content == "test"

    def test_retrieve_memory_not_found(self, mock_memory_service):
        """Retrieve non-existent memory retourne None"""
        result = mock_memory_service.retrieve_memory(999)
        assert result is None

    def test_consolidate_memory_threshold(self, mock_memory_service):
        """Consolidation respecte threshold"""
        memories = [{"content": f"mem{i}"} for i in range(100)]
        results = mock_memory_service.consolidate(memories, threshold=0.5)
        assert len(results) <= 50
```

### 2. Integration Tests - API Layer

```python
@pytest.mark.asyncio
class TestMemoryAPI:
    """Tests API GraphQL/REST"""

    async def test_memory_post_endpoint(self, client, db_session):
        """POST /api/memory crée mémoire"""
        response = await client.post(
            "/api/memory",
            json={"content": "test", "type": "short_term"}
        )

        assert response.status_code == 201
        assert response.json()["id"] is not None

        # Vérifier DB
        memory = db_session.query(Memory).first()
        assert memory is not None

    async def test_memory_graphql_query(self, client):
        """GraphQL query retourne memory"""
        response = await client.post(
            "/graphql",
            json={
                "query": "{ getMemory(id: 1) { id content } }"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
```

### 3. Parametrized Tests

```python
@pytest.mark.parametrize("input_type,expected", [
    ("short_term", "L1"),
    ("medium_term", "L2"),
    ("long_term", "L3"),
])
def test_memory_type_routing(input_type, expected):
    """Memory correctement routée selon type"""
    router = MemoryRouter()
    assert router.get_layer(input_type) == expected
```

## Commandes Pytest Essentielles

### Exécution

```bash
# Tous les tests
pytest

# Fichier spécifique
pytest tests/test_memory.py

# Test spécifique
pytest tests/test_memory.py::TestMemory::test_store

# Avec output (-v: verbose, -s: show prints)
pytest -v -s

# Failfast (stop au premier failure)
pytest -x

# Derniers N failures seulement
pytest --lf (last-failed)
pytest --ff (failed-first)
```

### Couverture

```bash
# Rapport couverture
pytest --cov=backend --cov-report=html

# Couverture minimale
pytest --cov=backend --cov-fail-under=85

# Par fichier
pytest --cov=backend --cov-report=term-missing
```

### Performance

```bash
# Top 10 tests lents
pytest --durations=10

# Parallèle (pytest-xdist)
pytest -n auto

# Profiling
pytest --profile
```

## Bonnes Pratiques

### 1. Naming Convention

```python
# ✅ BON
def test_store_memory_with_valid_data():
    pass

def test_retrieve_memory_returns_none_when_not_found():
    pass

# ❌ MAUVAIS
def test_memory():
    pass

def test_it_works():
    pass
```

### 2. AAA Pattern (Arrange-Act-Assert)

```python
def test_example():
    # Arrange - Setup
    input_data = {"content": "test"}
    service = MemoryService()

    # Act - Exécute
    result = service.store(input_data)

    # Assert - Vérifie
    assert result is not None
    assert result.content == "test"
```

### 3. Avoid Common Mistakes

```python
# ❌ Test trop général
def test_memory_service(mock_service):
    mock_service.store({"content": "x"})
    mock_service.retrieve(1)
    # Pas clair ce qu'on teste

# ✅ Test focused
def test_store_increments_memory_count():
    service = MemoryService()
    initial_count = service.count()
    service.store({"content": "x"})
    assert service.count() == initial_count + 1
```

## Mock & Patch

### Mocking External Services

```python
from unittest.mock import Mock, patch

def test_memory_with_external_api(monkeypatch):
    # Mock external API call
    mock_response = {"status": "ok"}
    monkeypatch.setattr(
        "app.services.external_api.call",
        Mock(return_value=mock_response)
    )

    result = some_function_calling_api()
    assert result["status"] == "ok"

# Alternative avec context manager
def test_with_patch():
    with patch('module.function') as mock_func:
        mock_func.return_value = "mocked"
        assert function_using_module() == "mocked"
```

## Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test fonction async"""
    result = await async_memory_service.fetch()
    assert result is not None

# Multiple async tests
@pytest.mark.asyncio
@pytest.mark.parametrize("delay", [0.1, 0.5, 1.0])
async def test_async_performance(delay):
    start = time.time()
    await asyncio.sleep(delay)
    elapsed = time.time() - start
    assert elapsed >= delay
```

## Reporting & CI Integration

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --strict-markers
    --tb=short
    --color=yes

markers =
    slow: marks tests as slow
    integration: integration tests
    unit: unit tests
```

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install deps
        run: pip install -r requirements.txt pytest pytest-cov
      - name: Run tests
        run: pytest --cov=backend --cov-fail-under=85
```

## Checklist Testing

```markdown
- [ ] Unit tests pour chaque fonction nouvelle (>85% coverage)
- [ ] Integration tests pour APIs
- [ ] Parametrized tests pour edge cases
- [ ] Async tests si code async
- [ ] Mocks pour dépendances externes
- [ ] Fixtures conftest.py partagées
- [ ] Naming convention respect
- [ ] AAA pattern appliqué
- [ ] No hardcoded test data
- [ ] CI/CD configuré
```
