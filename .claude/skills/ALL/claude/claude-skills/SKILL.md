---
name: claude-skills-system
description: Complete reference for Claude Code skills - creation, usage patterns, and best practices
category: claude
version: 2.0.0
---

# Claude Skills System

Skills are reusable knowledge modules that extend Claude Code's capabilities. They provide structured guidance, patterns, and best practices for specific domains or workflows.

## Concept

Skills are markdown documents stored in `.claude/skills/` directory that act as:
- **Knowledge bases**: Comprehensive references for specific domains
- **Pattern libraries**: Reusable solutions and conventions
- **Workflow guides**: Step-by-step instructions for complex processes
- **Best practices**: Standards and recommendations for consistent development

Skills are:
- **Loaded automatically** when matching skill name references
- **Composable**: Can reference other skills via cross-links
- **Versionable**: Updated as patterns evolve
- **Namespaced**: Organized by category (core, patterns, orchestration, validation, guides, etc.)

## Skill Types

### Type 1: Implementation Skills (≤50 lines)
Short, actionable guides for specific implementations.

**Usage**: Executor agents read these for quick how-to instructions.

**Example structure**:
```markdown
---
name: python-fastapi-setup
description: Setup FastAPI project with async patterns
---

## Quick Start
1. Create venv: `python -m venv venv`
2. Install: `pip install fastapi uvicorn`
3. Create main.py with basic app

## Patterns
- Use async/await for I/O operations
- Dependency injection via Depends()
- Pydantic models for validation

## Example
[minimal code snippet]
```

### Type 2: Documentation Skills (>50 lines OK)
Complete reference documentation for systems, patterns, or workflows.

**Usage**: Agents read via explicit Read() calls for comprehensive reference.

**Example structure**:
```markdown
---
name: orchestration-guide
description: Complete guide to workflow orchestration patterns
---

## Overview
[Comprehensive introduction]

## Core Concepts
[Detailed explanations]

## Patterns
[Multiple pattern examples]

## Best Practices
[Guidelines and recommendations]

## Reference
[Complete specification]
```

### Type 3: Pattern Library Skills
Collections of reusable patterns for specific tech stacks or domains.

**Structure**:
```
.claude/skills/patterns/
├── react-typescript-conventions/SKILL.md
├── python-fastapi-conventions/SKILL.md
└── backend-config-patterns/SKILL.md
```

Each contains:
- Pattern overview
- Usage scenarios
- Example implementations
- Common pitfalls to avoid

## Directory Structure

```
.claude/skills/
├── core/                          # Core AGI patterns
│   ├── workflow-orchestration/    # Workflow automation
│   ├── yaml-conventions/          # YAML standards
│   ├── strict-validation/         # Validation rules
│   ├── manifest-builder/          # Manifest generation
│   ├── context/                   # Context management
│   └── project-strict-workflow/   # Project workflows
├── patterns/                       # Tech stack patterns
│   ├── react-typescript-conventions/
│   ├── python-fastapi-conventions/
│   ├── backend-config-patterns/
│   └── frontend-testing-patterns/
├── orchestration/                 # Workflow orchestration
│   ├── routing-guide/
│   ├── state-manager/
│   ├── phase-router/
│   ├── workflow-guide/
│   ├── git-tracker/
│   └── deployment-orchestration/
├── validation/                    # Quality validation
│   ├── code-validator/
│   ├── architecture-validator/
│   └── progress-tracker/
├── guides/                        # Guides and standards
│   ├── conventions-guide/
│   ├── code-standards/
│   ├── requirements-analyzer/
│   └── requirements-analysis/
├── productivity/                  # TSA/HPI optimization
│   ├── time-optimizer/
│   ├── energy-mapper/
│   ├── goal-tracker/
│   └── goals-planning/
└── claude/                        # Claude Code specific
    └── claude-skills/            # This skill
```

## Creating a Skill

### Step 1: Choose Skill Type
- **Implementation** (<50 lines): How-to guides, quick starts
- **Documentation** (>50 lines OK): Complete references, specifications
- **Patterns**: Reusable solutions for specific domains

### Step 2: Define Frontmatter
```yaml
---
name: skill-name-kebab-case
description: Clear description of skill purpose
category: core|patterns|orchestration|validation|guides|productivity|claude
version: 1.0.0
---
```

**Naming rules**:
- Use kebab-case (no underscores, no camelCase)
- Descriptive but concise (max 50 chars)
- Avoid redundant prefixes (not `skill-my-skill`)

**Categories**:
- `core`: AGI core patterns
- `patterns`: Tech stack patterns
- `orchestration`: Workflow orchestration
- `validation`: Quality assurance
- `guides`: How-to guides and standards
- `productivity`: Time/energy management
- `claude`: Claude Code specific

### Step 3: Structure Content

**For Implementation Skills**:
```markdown
## Quick Start
[Steps to get started]

## Patterns
[Key patterns to follow]

## Common Pitfalls
[What to avoid]

## Example
[Minimal code example]
```

**For Documentation Skills**:
```markdown
## Overview
[Comprehensive introduction]

## Core Concepts
[Detailed concept explanations]

## Patterns
[Pattern descriptions and examples]

## Best Practices
[Guidelines and recommendations]

## Reference
[Complete specification or API]

## Examples
[Code examples]
```

### Step 4: Directory Creation
```bash
mkdir -p .claude/skills/CATEGORY/skill-name-kebab-case/
touch .claude/skills/CATEGORY/skill-name-kebab-case/SKILL.md
```

### Step 5: Write Content
- Keep implementation skills concise and actionable
- Document skills can be comprehensive (>50 lines OK for documentation)
- Use markdown formatting for readability
- Include practical examples
- Reference other skills when appropriate

## Usage Patterns

### Pattern 1: Direct Reference in Instructions
Agent instructions can reference skills:

```markdown
Follow patterns in .claude/skills/patterns/react-typescript-conventions/SKILL.md
```

### Pattern 2: Explicit Read by Agents
Agents explicitly read skills when needed:

```bash
Read .claude/skills/core/workflow-orchestration/SKILL.md
Extract: Phase router implementation pattern
```

### Pattern 3: Auto-Discovery (Skills Referenced)
When skill name appears in context, framework auto-loads matching skill:

```python
# In agent instructions or task
"Follow python-fastapi-conventions patterns"
# → Auto-loads .claude/skills/patterns/python-fastapi-conventions/SKILL.md
```

### Pattern 4: Cross-Linking
Skills can reference other skills:

```markdown
See also: .claude/skills/guides/code-standards/SKILL.md
For detailed patterns, refer: .claude/skills/patterns/react-typescript-conventions/SKILL.md
```

## Best Practices

### 1. Clarity Over Completeness
- Implementation skills should be immediately actionable
- Documentation skills should be logically organized
- Use examples for clarification

### 2. Naming Consistency
- Always use kebab-case
- Match directory name to skill name
- Keep names descriptive but concise

### 3. Single Responsibility
Each skill should focus on one domain or workflow:
- ✅ `python-fastapi-conventions` - FastAPI specific patterns
- ❌ `python-and-javascript-patterns` - Too broad

### 4. Version Management
- Update version in frontmatter when skill changes significantly
- Keep SKILL.md as single source of truth
- Never create duplicate skills with different names

### 5. Structure for Scanning
Agents scan skills efficiently:
- Clear headings with consistent hierarchy
- Bullet points for lists
- Code blocks for examples
- Summary sections for quick reference

### 6. No Parasitic Files
Skills directory contains ONLY:
- `SKILL.md` (required)
- Optional supporting files (referenced explicitly)
- NO: `.backup`, `.tmp`, `README`, `NOTES`, auto-generated files

## Integration with Agents

### How Agents Use Skills

**Executor agents** (Haiku fast):
- Read specific skills when instructed
- Apply patterns from implementation skills
- Reference documentation skills for complete guidance

**Architect agents** (design phase):
- Review architecture-validator skill
- Reference pattern skills for tech stack choices
- Consult orchestration skills for workflow design

**Writor agents** (validation phase):
- Use code-validator skill for quality checks
- Reference architecture-validator for design validation
- Consult progress-tracker for completion validation

### Skill Loading in Instructions

```markdown
Skills to use:
- .claude/skills/patterns/python-fastapi-conventions/SKILL.md
- .claude/skills/core/yaml-conventions/SKILL.md
- .claude/skills/validation/code-validator/SKILL.md
```

Agents explicitly load and reference when needed.

## Advanced Patterns

### Pattern: Skill Composition
Complex workflows compose multiple skills:

```markdown
1. Follow .claude/skills/guides/requirements-analyzer/SKILL.md
2. Apply .claude/skills/patterns/python-fastapi-conventions/SKILL.md
3. Validate with .claude/skills/validation/code-validator/SKILL.md
4. Track progress via .claude/skills/validation/progress-tracker/SKILL.md
```

### Pattern: Conditional Skills
Workflows reference different skills based on context:

```markdown
IF tech stack is React:
  → Use .claude/skills/patterns/react-typescript-conventions/SKILL.md
  → Use .claude/skills/patterns/react-testing-patterns/SKILL.md

IF tech stack is Python:
  → Use .claude/skills/patterns/python-fastapi-conventions/SKILL.md
  → Use .claude/skills/patterns/backend-config-patterns/SKILL.md
```

### Pattern: Skill Versioning
When updating skills for new patterns:

```yaml
---
name: python-fastapi-conventions
version: 2.0.0  # Major version bump for breaking changes
changelog: Added async context manager patterns (v2.0)
---
```

## Maintenance

### When to Update Skills
- New patterns discovered and validated
- Best practices change or improve
- Tech stack updates (new major versions)
- Agent feedback indicates gaps or errors

### When to Create New Skills
- New domain or category emerges
- Existing skill exceeds 100 lines (split into 2)
- New tech stack or framework adopted
- Workflow pattern becomes standard

### Deprecation
Mark skills as deprecated when superseded:

```markdown
---
name: old-pattern-name
status: DEPRECATED
replacement: new-pattern-name
version: 1.0.0
---

⚠️ This skill is deprecated. Use `.claude/skills/guides/new-pattern-name/SKILL.md` instead.
```

## Examples

### Example 1: Implementation Skill
See `.claude/skills/core/yaml-conventions/SKILL.md` for concise implementation patterns.

### Example 2: Documentation Skill
See `.claude/skills/guides/code-standards/SKILL.md` for comprehensive documentation patterns.

### Example 3: Pattern Library
See `.claude/skills/patterns/python-fastapi-conventions/SKILL.md` for tech-specific patterns.

## References

- RULES.md Level 12: Patterns création - mandatory for agent/skill creation
- BUILDER.md: Skill pattern specification (≤50 lines implementation, >50 OK for documentation)
- Skills loading: Automatic when skill name referenced in context

---

**Last Updated**: 2025-10-26
**Maintainer**: AGI Project - Skills System
**Status**: Active
