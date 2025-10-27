---
description: Create new project with strict YAML structure and schema validation
allowed-tools: Task, Read, Write, Bash
argument-hint: <project-name> [type]
---

# Project Creation - Strict Workflow

**Project Name**: $1
**Project Type**: ${2:-web-app}

## Pre-Flight Validation

1. **Check project name format** (kebab-case required):
   - Pattern: lowercase + hyphens only
   - Examples valid: "e-commerce", "todo-app", "api-gateway"
   - Examples invalid: "ECommerce", "todo_app", "api.gateway"

2. **Check project type** (must be one of):
   - web-app (default)
   - api
   - mobile
   - cli

## Workflow Execution

**Step 1: Create .plan/ structure**
```bash
mkdir -p $1/.plan/
mkdir -p $1/.plan/diagrams/
```

**Step 2: Invoke instructor**

Task("project-builder:instructor") with STRICT prompt:

```
TASK: Initialize project "$1" (Mode: NOUVEAU)

CONTEXT:
- Project name: $1
- Project type: ${2:-web-app}
- Mode: NOUVEAU (.plan/ structure created)

ACTION:
1. Read .claude/schemas/project.yaml.schema.json
2. Read .claude/schemas/roadmap.yaml.schema.json
3. Generate $1/.plan/project.yaml (STRICT YAML format)
4. Generate $1/.plan/roadmap.yaml (STRICT YAML format)
5. Generate $1/.plan/requirements.yaml (structured specs)
6. Validate all outputs against JSON schemas

OBLIGATION FIN ACTION:
- Update $1/.plan/state.json (current_phase: Discovery, progress: 17%)
- All files MUST validate against JSON schemas
- Format: YAML strict (NO markdown, NO freestyle)

DEADLINE: 60 seconds
PARTIAL OK: No

CONTRAINTES STRICTES:
- Format YAML uniquement (strict schema validation)
- kebab-case naming obligatoire
- Aucun fichier parasite (.backup, .tmp)
```

**Step 3: Post-Validation**

After instructor completes:
```bash
# Validate directory structure
ls -la $1/.plan/

# Validate YAML files exist
test -f $1/.plan/project.yaml || error "project.yaml missing"
test -f $1/.plan/roadmap.yaml || error "roadmap.yaml missing"

# Validate YAML syntax (basic)
python3 -c "import yaml; yaml.safe_load(open('$1/.plan/project.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('$1/.plan/roadmap.yaml'))"
```

**Step 4: Display Summary**

```yaml
project_created:
  name: "$1"
  type: "${2:-web-app}"
  location: "$1/"
  files_generated:
    - .plan/project.yaml (✓ YAML validated)
    - .plan/roadmap.yaml (✓ YAML validated)
    - .plan/requirements.yaml (✓)
    - .plan/state.json (✓)
    - .plan/diagrams/
  next_phase:
    agent: "architect"
    action: "Design architecture per project.yaml"
    estimated_duration: "4 hours"
  status: "READY"
```

## Validation Rules

- Project name MUST be kebab-case (no spaces, underscores, capitals)
- Type MUST be in allowed list: web-app | api | mobile | cli
- All YAML files MUST be valid YAML syntax
- state.json MUST be valid JSON with required fields
- NO duplicate projects (check if $1/ already exists)
