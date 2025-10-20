---
name: "Interdictions Strictes"
description: "Ultra-strict rules: NEVER use Bash/Read/Grep/Edit/Write directly. NEVER use MCPs directly. ALWAYS delegate to agents."
categories: ["rules", "interdictions", "delegation"]
tags: ["interdictions", "delegation", "agents", "MCPs", "research", "coding"]
version: "1.0.0"
enabled: true
---

## Overview

Ultra-strict operational rules enforcing:
- **NEVER execute tasks directly** (delegate to agents via Task tool)
- **NEVER use tools directly** (Bash, Read, Grep, Edit, Write)
- **NEVER use MCPs directly** (exa, fetch, context7 - use research agent)
- **ALWAYS delegate** external research, coding, architecture

This Skill prevents chaotic behavior and ensures proper agent orchestration.

## When to Use This Skill

- Before using ANY tool directly (Bash, Read, Grep, Edit, Write)
- Before calling MCP tools (exa, fetch, context7, etc.)
- Before coding features directly
- Before designing architecture alone
- To verify proper delegation patterns
- When unsure about task assignment

## Key Principles

**JAMAIS DIRECTEMENT:**
- ❌ Bash/Read/Grep/Edit/Write (sauf scan rapide <5 fichiers)
- ❌ Recherche externe (exa, fetch, context7)
- ❌ Coding features directement
- ❌ Architecture design sans agent architect

**TOUJOURS DÉLÉGUER VIA TASK:**
- ✅ External research → `Task(research, ...)`
- ✅ Backend coding → `Task(code, ...)`
- ✅ Frontend coding → `Task(frontend, ...)`
- ✅ Architecture → `Task(architect, ...)`
- ✅ Testing → `Task(debug, ...)`
- ✅ Documentation → `Task(docs, ...)`
- ✅ Infrastructure → `Task(sre, ...)`

## Agent Assignment Rules

| Task Type | Agent | MCPs |
|-----------|-------|------|
| Explore codebase | `ask` | None |
| External research | `research` | exa, fetch, context7 |
| Architecture design | `architect` | None |
| Backend coding | `code` | None |
| Frontend coding | `frontend` | None |
| Testing/validation | `debug` | None |
| Documentation | `docs` | None |
| Infrastructure | `sre` | Optional |

## Examples

### WRONG - Direct tool usage
```python
# ❌ WRONG: Using MCP directly
mcp__exa__get_code_context_exa("pattern")

# ❌ WRONG: Coding directly
Edit("backend/services/memory_service.py", old, new)

# ❌ WRONG: Grepping directly
Grep("class MemoryService")
```

### CORRECT - Delegated to agents
```python
# ✅ CORRECT: Research via agent
Task(research, "Best practices for memory systems")

# ✅ CORRECT: Coding via agent
Task(code, "Refactor memory_service.py for performance")

# ✅ CORRECT: Ask agent to explore
Task(ask, "Scan backend/services/memory*.py, list classes")
```

## Timeout Guidelines

**Always include deadlines in Task prompts:**

| Task Type | Timeout |
|-----------|---------|
| Explore 1-5 files | 10s |
| Explore 10-20 files | 20s |
| Grep pattern | 15s |
| Design phase | 30s |
| Code micro-feature | 30s |
| Run tests | 20s |
| Documentation | 30s |

## Related Skills

- `workflow/agents` - Agent orchestration patterns
- `workflow/pipeline` - Phase-based execution pipeline
- `system/delegation` - CEO delegation mindset
- `rules/naming-conventions` - Code naming standards

## Enforcement

This Skill is **NON-NEGOTIABLE**. Violations:
- Consume tokens inefficiently (solo vs parallel agents)
- Create hidden failures (no test coverage)
- Violate CEO delegation patterns
- Risk token budget waste

**Token savings: 80-90% when delegating properly**
