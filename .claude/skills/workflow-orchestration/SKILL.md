---
name: workflow-orchestration
description: Routing intelligent via templates + state.json - détermine phase/agent automatiquement
references:
  - ./.claude/system/rules/RULES.md (Niveau 4, Niveau 6, Niveau 13)
  - ./.claude/system/rules/ORCHESTRATION.md (Plugins project-builder, claude-builder, brain-manager)
---

# Workflow Orchestration

Router intelligent projet long-terme : templates instanciés → .plan/routing.yaml + state.json → détermine agent/action automatiquement.

**JOB ORCHESTRATOR** : Lire .plan/routing.yaml (instancié depuis template) + state.json pour routing automatique.

## Fichiers État (Source Vérité)

1. **routing.yaml** (.plan/) : Créé depuis template, règles routing projet
2. **state.json** (.plan/) : État actuel instantané (current_phase, blockers, next_action)
3. **workflow.yaml** (.plan/) : Phases séquentielles + metadata
4. **tasks.md** (.plan/) : Tracking humain checkboxes

## Routing Logic

**Étape 1 : Détection État Projet**
```
Read .plan/routing.yaml detection_rules:
  - .plan/ absent → NOUVEAU → instructor
  - .plan/ <7j + state.json existe → EN_COURS
  - .plan/ >7j → REPRISE → instructor (audit)
```

**Étape 2 : Routing via state.json + phase_routing**
```
Read .plan/state.json:
  - current_phase → lookup .plan/routing.yaml phase_routing
  - blockers présent ? → return blocked
  - status (in_progress/completed) → determine next_agent
```

**Étape 3 : Retour JSON Décision**
```json
{
  "next_agent": "executor",
  "action": "Implémenter backend models",
  "blockers": [],
  "status": "en_cours",
  "current_phase": "implementation"
}
```

## Invoquer Agents Selon Workflow

```python
# Lire workflow.yaml créé par instructor
workflow = YAML.read(".plan/workflow.yaml")
for phase in workflow.phases:
    if phase.status == "pending":
        Task(phase.agent, "Exécuter {phase.name} - input: {phase.input}, output: {phase.output}")
        break  # 1 phase active à la fois (gate séquentiel)
```

## Règles

- Templates : `@./.claude/system/templates/plugins/*.yaml.template`
- Executor instancie templates → crée .plan/*.yaml (projet-spécifique)
- Phases marquées `completed` → skip, read next status
- Une seule `pending` active à la fois
- Attendre output avant invoquer suivant
- Si blockers présent → AskUserQuestion + investigation parallèle (RULES.md Niveau 13)
