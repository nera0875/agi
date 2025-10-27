# ORCHESTRATION - Skills Workflow Guide

Orchestration via skills + executor. Pas de plugins agents - tout passe par Skill() + Task(executor).

---

## Skills Disponibles

**Localisation** : `.claude/skills/`

| Skill | Type | Usage |
|-------|------|-------|
| `memory` | Implementation | Charge/synch mémoire CONTEXT.md |
| `workflow-orchestration` | Implementation | Route action → phase suivante (projet/plugin) |
| `project-strict-workflow` | Implementation | Workflow création projet (phases + validation) |
| `plugin-creation` | Implementation | Création plugin structure conforme |
| `plugin-validation` | Implementation | Valide agents/skills/commands/plugin.json |
| `strict-validation` | Implementation | Validation générique (syntax, lint, tests) |
| `yaml-conventions` | Implementation | Valide/formate YAML (workflow, routing, state) |

---

## Workflow Création Projet

**Pattern** : Skill() → Décision → Task(executor) → Skill() → Loop

### Phase 1 : Analyse Requirements

```python
# 1. Charger mémoire
Skill("memory").load_context()

# 2. Analyser requirements
Skill("project-strict-workflow").analyze_project(type="NOUVEAU|EN_COURS|REPRISE")
# Retourne : {status, phases, blockers, next_action}

# 3. Si blockers
if blockers:
    AskUserQuestion(f"Blockers: {blockers}")
    # User répond
```

### Phase 2 : Exécution via Executor

```python
# Task(executor) exécute selon Skill décision
Task(executor, """
TASK: Créer projet structure
ACTION:
  1. Créer .plan/requirements.md (from Skill result)
  2. Créer .plan/workflow.yaml (template: system/templates/projects/)
  3. Créer .plan/tasks.md
DEADLINE: 30 seconds
FORMAT: Fichiers YAML/Markdown conformes
CONTRAINTES:
  - kebab-case uniquement
  - Aucun fichier parasite
""")
```

### Phase 3 : Routing vers Phase Suivante

```python
# Après executor complété
state = Skill("workflow-orchestration").next_phase()
# Retourne : {next_phase: "IMPLEMENTATION|VALIDATION", agent_next: "executor", blockers}

if state.next_phase == "IMPLEMENTATION":
    Task(executor, "Implémenter selon .plan/architecture.md")
elif state.next_phase == "VALIDATION":
    Skill("strict-validation").validate(scope=".plan/")
```

---

## Workflow Création Plugin

**Pattern** : Same as Project - Skill() route → Task(executor)

### Phase 1 : Plugin Discovery

```python
Skill("plugin-creation").analyze(questions=[
    "Type plugin? (dev/pentest/doc/custom)",
    "Agents domain? (count 1-5)",
    "Skills? (count 1-10)",
    "Commands? (yes/no)"
])
# Retourne : {architecture.md, constraints, count_agents/skills}

# Valider limits
if count_agents > 5:
    AskUserQuestion("Warning: >5 agents. Confirm?")
```

### Phase 2 : Architecture File

```python
Task(executor, """
TASK: Créer architecture plugin
ACTION:
  1. Générer .plan/architecture.md (from Skill decision)
  2. List agents + skills + commands détaillés
DEADLINE: 20 seconds
""")
```

### Phase 3 : Create Agents (Parallèle)

```python
# Skill retourne list agents à créer
agents_list = Skill("plugin-creation").agents_to_create()  # [{name, description, tools, lines_max: 30}]

for agent in agents_list:
    Task(executor, f"""
    TASK: Créer agent {agent['name']}
    TEMPLATE: .claude/system/templates/agents/BASE.md
    VALIDATE: wc -l ≤ 30 lignes
    """)
```

### Phase 4 : Create Skills (Parallèle)

```python
skills_list = Skill("plugin-creation").skills_to_create()  # [{name, type: "implementation|documentation", lines_max: 50}]

for skill in skills_list:
    Task(executor, f"""
    TASK: Créer skill {skill['name']}
    TYPE: {skill['type']}
    LINES MAX: {skill['lines_max']}
    """)
```

### Phase 5 : Validation

```python
Skill("plugin-validation").validate(scope=".claude-plugin/")
# Checks:
# - agents/*.md ≤30 lignes
# - skills/*/*.md ≤50 lignes
# - plugin.json valid JSON
# - Aucun fichier parasite
# Retourne : {errors: [], warnings: [], status: "OK|FAIL"}

if not validation.ok:
    AskUserQuestion(f"Errors: {validation.errors}")
```

---

## Workflow Brain (Productivité TSA/HPI)

**Pattern** : Skill() memory + MCP sync + executor optimization

### Setup Initial

```python
# Load memory
Skill("memory").load_context()

# Questions TSA/HPI
from AskUserQuestion import ask

profile = {
    "objective": ask("Objectif? (milliardaire/productivité/santé)"),
    "constraints_tsa": ask("Constraints TSA? (switching cost, overload, etc)"),
    "patterns_hpi": ask("HPI patterns? (pics énergie, hyperfocus)"),
    "ticktick_usage": ask("TickTick count? (projets, tasks/jour)"),
}

# Créer .plan/requirements.md profil
Task(executor, """
TASK: Créer brain requirements
ACTION: Write .plan/brain-requirements.md
CONTENT: {profile converted to markdown}
""")
```

### Sync TickTick Continu

```python
# Writor → Skill memory → MCP sync
Task("brain-manager:writor", """
TASK: Sync TickTick bidirectionnel
ACTION:
  1. Fetch TickTick via mcp__ticktick__get_all_tasks
  2. Compare avec .claude/brain-manager/data/tasks.json
  3. Merge changes (last-modified wins)
  4. Update context.json historique
TRIGGER: Quotidien ou /brain:sync command
""")
```

### Optimization Temps (Hebdomadaire)

```python
# Executor analyse energy patterns
Task(executor, """
TASK: Optimize time blocks
ACTION:
  1. Read .claude/brain-manager/data/energy-log.json
  2. Detect pics/creux HPI
  3. Generate optimal schedule
  4. Write time-blocks.json updated
DEADLINE: 45 seconds
""")
```

### Goals Tracking (Mensuel)

```python
Task(executor, """
TASK: Track roadmap progress
ACTION:
  1. Read .claude/brain-manager/data/goals.json
  2. Calculate % completion
  3. Identify blockers
  4. Propose next milestones
DEADLINE: 30 seconds
""")
```

---

## Templates Disponibles

**Localisation** : `.claude/system/templates/`

**Projets** :
- `project.yaml.template` - Workflow projet standard
- `architecture.md.template` - Architecture template
- `roadmap.yaml.template` - Roadmap milestones
- `state.json.template` - État projet (phases, progress)

**Plugins** :
- `plugins/workflow.yaml.template` - Workflow plugin
- `plugins/architecture.md.template` - Architecture plugin
- `plugins/requirements.md.template` - Requirements
- `plugins/tasks.md.template` - Tracking tasks
- `plugins/state.json.template` - État plugin

**Agents/Skills** :
- Templates chargés via Skill("plugin-creation")

---

## Validation Workflow

**Après CHAQUE phase executor complétée** :

```python
# 1. Vérifier résultat
result = Skill("strict-validation").validate(scope="output_files")
# Checks: syntax, structure, kebab-case, no parasites

if not result.ok:
    # 2. Diagnostiquer + corriger
    Task(executor, f"""
    TASK: Fix validation errors
    ERRORS: {result.errors}
    """)

# 3. Update workflow state
Skill("workflow-orchestration").update_state(phase="COMPLETED", next="PHASE_NAME")
Skill("memory").update_context(action="Phase X completed")
```

---

## Rules Générales

1. **Skill() charge logique** - Routage, décisions, planning
2. **Task(executor) exécute** - Read/Write/Edit/Bash concrets
3. **Workflow séquentiel** - Phase N → Phase N+1 (attendre output)
4. **Parallélisation** - Agents/skills indépendants en parallèle
5. **Validation obligatoire** - Jamais skip validation (strict-validation skill)
6. **Memory persistent** - Skill("memory") start + update après actions clés
7. **Templates = sources vérité** - Toujours utiliser templates/.claude/system/

---

## Commands Disponibles

```bash
/memory:load       # Charge mémoire CONTEXT.md + brain data
/workflow:next     # Skill workflow-orchestration → next phase
/validate:project  # Skill strict-validation → project scope
/validate:plugin   # Skill plugin-validation → plugin scope
/brain:sync        # Writor sync TickTick
/brain:optimize    # Executor optimize time blocks
```

