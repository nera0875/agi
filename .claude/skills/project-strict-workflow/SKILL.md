---
name: project-strict-workflow
description: Workflow création projet avec validation stricte + CEO fix automatique
references:
  - ./.claude/system/rules/ORCHESTRATION.md (project-builder phases)
  - ./.claude/system/rules/RULES.md (Niveau 1-14 CEO proactif)
---

# Project Strict Workflow

Workflow création projet avec validation schemas obligatoire. Orchestrator CEO proactif : agents fix automatiquement sans attendre user si validation échoue.

## Phases Séquentielles (5)

1. **Schemas** → .plan/project.yaml + roadmap.yaml (instructor)
2. **Architecture** → .plan/architecture.md selon constraints (architect)
3. **Implementation** → Code selon architecture (executor + auto-fix tests)
4. **Validation** → state.json + tasks.md qualité (writor)
5. **State Update** → Tous agents update progression (PostToolUse hook)

## CEO Proactif

```
Validation échoue → Task(executor, "Fix + re-validate")
→ Boucle validation-fix jusqu'à success
→ User informé résultat final SEULEMENT
```

Jamais bloquer sur validation : executor fix automatiquement (RULES.md Niveau 13).

## Agents Obligations

Tous agents update (PostToolUse trigger) :
- `.plan/state.json` : current_phase, progress %, last_action
- `.plan/tasks.md` : checkboxes [x] + timestamp
- `.plan/workflow.yaml` : phase.status si changement

## State Files

```
.plan/
├── project.yaml         # Schema projet (goals, constraints)
├── roadmap.yaml         # Timeline phases
├── architecture.md      # Design technique
├── state.json           # État actuel (source vérité)
├── tasks.md             # Tracking checkboxes
└── workflow.yaml        # Phases status
```

## Validation Hooks

- Schema validation (JSON schema vs project.yaml)
- Architecture validation (constraints check)
- Code validation (tests + lint auto)
- State validation (files synchronized)
