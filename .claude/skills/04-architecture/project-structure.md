---
title: "Project Structure & Organization"
description: "Prevent duplicates and maintain clean architecture through systematic scanning and structure enforcement"
category: "Architecture"
level: "Advanced"
tags: ["structure", "organization", "scanning", "naming", "patterns"]
---

# Project Structure & Organization

## Overview
Clean project structure prevents duplicates, improves maintainability, and enables developers to find code quickly. This skill covers systematic approaches to scanning, organizing, and enforcing structure conventions.

## Core Principles

### 1. Scan Before Creating
**Always verify existence before creating new files:**

```bash
# Step 1: Check existence with broad patterns
Glob: "**/*memory*"
Glob: "**/*service*"

# Step 2: Search similar code logic
Grep: "class.*Memory|def.*memory" --type py

# Step 3: Make creation decision
if file_exists:
    Edit existing  # NEVER create duplicate
elif similar_code_exists:
    Extend existing  # Reuse over recreate
else:
    Create new_file  # At correct location
```

### 2. Prevent Duplicates
**Duplicate detection workflow:**

```python
# Duplicate patterns to watch
❌ memory_service.py + memory.py  (different names, same logic)
❌ utils.py + helpers.py + misc.py  (vague names, scattered)
❌ service_v2.py (versioned files = bad practice)
❌ temp_migration.sql + migrations/001.sql  (scattered migrations)

# How to detect duplicates
1. Scan filenames: memory*.py, *_service.py, *_wrapper.py
2. Grep class names: class Memory, class MemoryService
3. Check imports: Who imports from where?
4. Consolidate: Keep 1 source of truth
```

### 3. File Organization Structure

**Backend Python:**
```
backend/
├── api/              # GraphQL/REST endpoints
│   ├── graphql/
│   │   └── schema.py
│   └── rest/
│       ├── memory.py
│       └── graph.py
├── services/         # Business logic (ALWAYS here)
│   ├── memory_service.py
│   ├── graph_service.py
│   └── embedding_service.py
├── models/           # SQLAlchemy DB models
│   ├── memory_model.py
│   └── neurotransmitter_model.py
├── schemas/          # Pydantic validation
│   └── memory_schema.py
├── agents/           # LangGraph agents
│   ├── observer_agent.py
│   └── consolidation_agent.py
├── utils/            # ORGANIZED utilities
│   ├── date_formatter.py
│   ├── string_utils.py
│   └── __init__.py
├── migrations/       # Database migrations
│   ├── versions/
│   └── env.py
├── tests/            # MIRROR source structure
│   ├── services/
│   │   └── test_memory_service.py
│   ├── agents/
│   │   └── test_observer_agent.py
│   └── api/
│       └── test_memory_routes.py
└── main.py
```

**Frontend React:**
```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui only (DO NOT CREATE)
│   │   ├── button.tsx
│   │   └── card.tsx
│   ├── memory/          # Feature: Memory
│   │   ├── memory-board.tsx
│   │   ├── memory-card.tsx
│   │   └── use-memory.ts
│   └── features/        # Other features
│       └── dashboard.tsx
├── pages/               # Page components
│   ├── home.tsx
│   └── dashboard.tsx
├── hooks/               # Custom hooks
│   ├── use-memory.ts
│   └── use-graph.ts
├── lib/                 # Utilities
│   ├── utils.ts
│   └── constants.ts
└── __tests__/           # Tests
    └── components/
        └── memory-card.test.tsx
```

## Naming Conventions

### Backend Python
```python
# Filenames (snake_case)
memory_service.py       ✅ Clear domain + type
graph_embeddings.py     ✅ Descriptive
config.py               ✅ Standard
utils.py                ❌ Too vague

# Classes (PascalCase)
class MemoryService         ✅
class GraphEmbeddingEngine  ✅
class S                     ❌ Too short

# Functions (snake_case)
def get_memories()          ✅
def calculate_embeddings()  ✅
def x()                     ❌ Too short

# Constants (UPPER_SNAKE_CASE)
MAX_MEMORY_SIZE = 10000     ✅
EMBEDDING_MODEL = "voyage"  ✅
```

### Frontend TypeScript/React
```typescript
// Files (kebab-case)
memory-card.tsx         ✅ Component
use-memory.ts           ✅ Hook
memory.constants.ts     ✅ Constants
utils.ts                ⚠️ Only if truly generic

// Components (PascalCase)
function MemoryCard()           ✅
function MemoryProvider()       ✅
function mc()                   ❌ Too short

// Hooks (use* prefix)
function useMemory()            ✅
function useMemoryStore()       ✅
function useFetch()             ⚠️ Too generic

// Constants (UPPER_SNAKE_CASE)
const MAX_CARDS = 100           ✅
const API_BASE_URL = "..."      ✅
```

## Scanning Patterns

### Quick Scan Checklist
```bash
# 1. Duplicate services
Glob "**/*service*.py" | grep -E "(memory|graph|embedding)"

# 2. Vague utility files
Glob "**/(utils|helpers|misc).py"

# 3. Test file organization
Glob "tests/**" | grep -v "__pycache__"

# 4. Scattered migrations
Glob "**/*.sql" | grep -v "migrations/"

# 5. Relative imports (anti-pattern)
Grep "from \.\." --type py
```

### What Each Pattern Detects
| Pattern | Finds | Action |
|---------|-------|--------|
| `**/*_service.py` | All services | Check for duplicates |
| `**/*_model.py` | All DB models | Verify normalization |
| `**/*_schema.py` | All validation | Find scattered schemas |
| `**/*.sql` | All SQL | Ensure in migrations/ |
| `src/**/*.tsx` | All components | Check naming, organization |

## Common Issues & Fixes

### Issue 1: Scattered Utilities
**Problem:**
```
backend/
├── utils.py              (date formatting)
├── helpers.py            (string utils)
├── misc.py               (random helpers)
├── services/utils.py     (more utilities)
```

**Solution:**
```
backend/utils/           # Organized directory
├── __init__.py
├── date_formatter.py    # Specific purpose
├── string_utils.py      # Specific purpose
└── validators.py        # Specific purpose
```

### Issue 2: Duplicate Business Logic
**Problem:**
```python
# File 1: backend/services/memory_service.py
class MemoryService:
    def get_memories(self): ...

# File 2: backend/memory.py (duplicate!)
class Memory:
    def get_memories(self): ...
```

**Solution:**
```python
# Keep ONE source of truth
# Edit backend/services/memory_service.py
class MemoryService:
    def get_memories(self): ...  # Enhanced version
    def add_filter_option(self): ...  # New capability

# Delete backend/memory.py
# Update imports everywhere to use MemoryService
```

### Issue 3: Wrong File Location
**Problem:**
```
backend/
├── api/
│   └── memory_logic.py  # ❌ Business logic in API layer
└── database.py          # ❌ DB logic at root
```

**Solution - Correct Layering:**
```
backend/
├── api/
│   └── memory.py        # ✅ Only routing
├── services/
│   └── memory_service.py  # ✅ Business logic
├── models/
│   └── memory_model.py    # ✅ DB models
```

## Implementation Checklist

Before creating any new file:

- [ ] Run `Glob "**/*{keyword}*"` to check existence
- [ ] Run `Grep "class.*{Name}"` to find similar code
- [ ] Verify correct folder location matches structure
- [ ] Check naming follows conventions
- [ ] If edit existing: Read full file first
- [ ] If create new: Place in correct folder, correct name
- [ ] Create corresponding test file (mirror structure)
- [ ] Update imports if consolidating duplicates

## Quick Reference

**File Creation Decision Tree:**
```
┌─────────────────────────┐
│ Need new file?          │
└───────────┬─────────────┘
            │
    ┌───────v─────────┐
    │ File exists?    │
    └───┬─────────┬───┘
        │ YES     │ NO
        v         │
      EDIT        │
                  v
         ┌────────────────┐
         │ Similar code?  │
         └──┬──────────┬──┘
            │ YES      │ NO
            v          │
          EXTEND       v
                    ┌──────────────┐
                    │ Right folder?│
                    └──┬────────┬──┘
                       │ YES    │ NO
                       v        v
                     CREATE  FIX LOCATION
```

## References
- Backend service layer pattern
- Database schema normalization
- React component composition
