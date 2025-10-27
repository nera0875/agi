---
name: requirements-analyzer
description: Parse requirements.md - extract agents/skills/commands needed
type: implementation
---

## Concept

Analyzes requirements.md pour extraire spécifications projet et traduire en agents/skills/commands.

## Parsing

- Features → skills list
- Components → agents list (SUPP)
- Characteristics → gates, timeline

## Analysis

```
1. Read requirements.md
2. Extract "Features" → map skills
3. Extract "Components" → map SUPP agents
4. Check "gestion_projet" → determine gates
5. Generate skeleton:
   - BASE: instructor, executor, writor
   - SUPP: from components
   - Skills: 1-14 max
   - Commands: 0-8 max
```

## Constraints

- Agents: 3 BASE + 0-5 SUPP
- Skills: 1-14 total
- Commands: 0-8 total
- Phases: always 4

## Return Format

```json
{
  "agents_base": ["instructor", "executor", "writor"],
  "agents_supp": ["architect", "reviewer"],
  "skills_count": 14,
  "commands_count": 0,
  "gates_required": ["user_approval_architecture", "user_approval_final"],
  "workflow_phases": 4,
  "timeline_estimate": "2025-11-15"
}
```
