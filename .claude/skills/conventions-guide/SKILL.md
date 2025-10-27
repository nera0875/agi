---
name: conventions-guide
description: Plugin conventions - naming, structure, size limits
type: documentation
---

# Conventions Guide - project-builder-v2

## Naming Conventions

**All files must be kebab-case**:
- agents: `instructor.md`, `executor.md`, `my-custom-agent.md` ✓
- skills: `workflow-orchestration/SKILL.md`, `my-skill-name/SKILL.md` ✓
- commands: `deploy.md`, `my-command.md` ✓

**Invalid**:
- `instructor_v2.md` ✗ (underscore)
- `MyAgent.md` ✗ (PascalCase)
- `my skill.md` ✗ (spaces)

## Size Limits

**Agents**: ≤30 lines total
- Frontmatter (5 lines)
- Job description (1 line)
- Instructions (5-10 lines)
- Obligation end action (5 lines)
- Total: 15-25 lines typical

**Skills Implementation**: ≤50 lines
- Frontmatter (3 lines)
- Concept (2-3 lines)
- Implementation section (30-40 lines)
- Return format (5 lines)

**Skills Documentation**: No limit
- Reference materials can be longer

**Commands**: ≤20 lines
- Brief command implementations

## Structure Requirements

**Agent frontmatter** (mandatory):
```yaml
---
name: agent-name
description: One line description
tools: Read, Write, Bash
model: haiku
---
```

**Skill frontmatter** (mandatory):
```yaml
---
name: skill-name
description: One line description
type: implementation|documentation
---
```

**No Parasite Files**:
- ✗ `.backup`, `.bak`, `*.backup`
- ✗ `.tmp`, `*~`
- ✗ `.old`, `-old`
- ✗ `README.md`, `DOCS.md` (except memory)

## BASE Agents (3 Always Required)

1. **instructor**: Discovery phase
2. **executor**: Implementation phase
3. **writor**: Tracking/validation phase

**Cannot remove or rename these.**

## Supplementary Agents (0-5 recommended)

Additional agents for specific roles:
- architect: Design architecture
- reviewer: Code/quality review
- deployer: Deployment automation
- etc.

Naming pattern: `{role}.md`

## Skills Organization

Skills are organized in folders:
```
skills/
  skill-name-1/
    SKILL.md
  skill-name-2/
    SKILL.md
```

Each skill has exactly ONE file: `SKILL.md`
