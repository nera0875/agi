# Optimize Hook - Architecture Analysis & Recommendations

## Purpose

The **optimize hook** analyzes the project architecture and proposes improvements to maintain code quality, prevent technical debt, and optimize organization.

**Triggers:** PostToolUse on critical file modifications (Edit/Write)
**Type:** Passive analysis (read-only, non-blocking)

## What It Analyzes

### 1. Services Layer
- File count and categorization (wrappers, memory services, embeddings)
- Wrapper consolidation opportunities
- Service duplication detection
- Large file detection (>500 lines = refactoring candidate)

### 2. Agents Layer
- Agent count and distribution
- Specialization coverage
- Complexity scoring

### 3. Routes Layer
- API route organization
- Endpoint distribution
- Coverage completeness

### 4. Memory System
- L1 (Redis) tier coverage
- L2 (Storage) tier coverage
- L3 (Graph/Neo4j) tier coverage
- Missing implementations detection

### 5. Naming Conventions
- Python snake_case compliance
- File suffix standardization
- Consistency checking

### 6. Complexity Hotspots
- Files with high complexity scores
- Large files needing refactoring
- Structural issues

## Recommendations Categories

### Priority Levels

- **HIGH** 🔴 - Critical architecture issues requiring immediate attention
- **MEDIUM** 🟡 - Important optimizations for project health
- **LOW** 🟢 - Nice-to-have improvements for code quality

### Recommendation Types

1. **Consolidation** - Merge related services/files
2. **Refactoring** - Split large files into focused modules
3. **Coverage** - Add missing components
4. **Expansion** - Add specialized agents/services
5. **Conventions** - Standardize naming/structure
6. **Architecture** - System-level improvements

## Usage

### Via CLI

```bash
# Run analysis and display results
python3 .claude/hooks/optimize_cli.py run

# List recent reports
python3 .claude/hooks/optimize_cli.py list

# View latest report
python3 .claude/hooks/optimize_cli.py view

# View specific report
python3 .claude/hooks/optimize_cli.py view optimize_20251020_161845
```

### Automatic Trigger

Hook automatically triggers when modifying critical files:

```
backend/api/**
backend/services/**
backend/agents/**
backend/routes/**
.claude/hooks/**
.claude/agents/**
CLAUDE.md
```

## Reports

Reports are saved to: `.claude/meta/optimize_*.json`

### Report Structure

```json
{
  "timestamp": "2025-10-20T16:19:06.123456",
  "statistics": {
    "services": {
      "total": 18,
      "wrappers": 2,
      "memory_services": 5,
      "embeddings_services": 2
    },
    "agents": { "total": 5, "files": {...} },
    "routes": {...},
    "memory_tiers": {
      "L1": ["redis_client.py", "redis_memory.py"],
      "L2": ["store_memory.py", "memory_service.py"],
      "L3": ["graph_service.py", "neo4j_memory.py"]
    }
  },
  "recommendations": [
    {
      "priority": "MEDIUM",
      "category": "consolidation",
      "target": "backend/services/",
      "issue": "Found 5 memory-related services",
      "action": "Review for overlapping responsibilities",
      "impact": "Better separation of concerns"
    }
  ]
}
```

## Example Analysis Output

```
🔧 Services (18 total):
   • Wrappers: 2
   • Memory services: 5
   • Embeddings services: 2

💾 Memory Tiers:
   • L1: 2 services (Redis)
   • L2: 2 services (Storage)
   • L3: 2 services (Graph)

RECOMMENDATIONS (4 found):

🟡 MEDIUM: CONSOLIDATION
   📍 backend/services/
   ❌ Found 5 memory-related services
   ✅ Review for overlapping responsibilities (L1/L2/L3 tiers clear?)

🟡 MEDIUM: REFACTORING
   📍 backend/services/
   ❌ Found 6 large service files (>500 lines)
   ✅ Split into focused modules (single responsibility)
   📄 Files:
      • store_memory.py: 603 lines
      • memory_service.py: 1084 lines
      • hybrid_search.py: 697 lines

🟢 LOW: CONVENTIONS
   📍 backend/services/
   ❌ Found 4 naming convention violations
   ✅ Standardize to: {domain}_{type}.py
```

## Integration with CLAUDE.md

The optimize hook complements CLAUDE.md guidelines by:

1. **Monitoring** - Detects when code deviates from guidelines
2. **Recommending** - Suggests specific improvements
3. **Reporting** - Tracks changes over time

## How to Act on Recommendations

### Example: Large File (>500 lines)

**Issue**: `memory_service.py` is 1084 lines

**Action Steps**:
1. Identify separate concerns in the file
2. Extract each concern to a new service
3. Create proper imports/exports
4. Run tests to validate
5. Delete original or keep as facade

```python
# Before: memory_service.py (1084 lines)
class MemoryService:
    def store_l1(...)
    def retrieve_l1(...)
    def store_l2(...)
    def retrieve_l2(...)
    def search_embeddings(...)
    def consolidate(...)
    # ... 50 more methods

# After: Split into focused modules
# backend/services/memory_l1_service.py (200 lines)
class MemoryL1Service:
    def store(...)
    def retrieve(...)

# backend/services/memory_l2_service.py (250 lines)
class MemoryL2Service:
    def store(...)
    def retrieve(...)

# backend/services/memory_search_service.py (300 lines)
class MemorySearchService:
    def search_embeddings(...)
    def consolidate(...)
```

### Example: Consolidation (Multiple Wrappers)

**Issue**: 2+ wrapper services for similar APIs

**Action Steps**:
1. Analyze each wrapper's interface
2. Create unified interface
3. Implement adapter pattern
4. Migrate code gradually

```python
# Before: Separate wrappers
cohere_wrapper.py  # 200 lines
voyage_wrapper.py  # 180 lines

# After: Unified wrapper with adapters
embeddings/
  ├── __init__.py
  ├── interface.py         # Abstract interface
  ├── cohere_adapter.py    # 100 lines
  ├── voyage_adapter.py    # 100 lines
  └── manager.py           # 80 lines
```

## Metrics Tracked

- **Services**: Total count, by category (wrappers, memory, embeddings)
- **Agents**: Total count, complexity per agent
- **Routes**: File count, endpoint count
- **Memory Tiers**: Coverage (L1, L2, L3)
- **Naming**: Convention violations count
- **Complexity**: Hotspots identified, complexity scores

## Performance

- **Execution Time**: ~2-5 seconds per analysis
- **Trigger Cost**: Non-blocking (runs in background)
- **Report Size**: ~10-50 KB per report
- **Storage**: Reports archived in `.claude/meta/`

## Related

- `auto_trigger_agent.py` - Automatically triggers agents on file changes
- `monitor_triggers.py` - Monitors trigger logs
- `.claude/meta/optimize_latest.json` - Latest analysis report

## Future Enhancements

- [ ] Trend analysis (improvement over time)
- [ ] Dependency graph visualization
- [ ] Test coverage correlation
- [ ] Performance metrics integration
- [ ] Automatic refactoring suggestions
