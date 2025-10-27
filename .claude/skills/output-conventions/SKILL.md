---
name: output-conventions
description: Output structure - fichiers artifacts organisés par scope
---

## Output Convention - Fichiers Structurés

**Principe** : Outputs organisés par scope (projet, plugin, memory) avec validation stricte.

### Structure Obligatoire

**Projet/Plugin (.plan/)** :
```
.plan/
├── requirements.md      # Besoins listés
├── workflow.yaml        # Phases séquentielles
├── architecture.md      # Design decisions
├── tasks.md            # Tracking checkboxes + timestamps
├── state.json          # État dynamique (current_phase, agents_history)
└── roadmap.yaml        # Milestones (optionnel)
```

**Memory (Persistant)** :
```
.claude/
├── context.json        # Consolidated memory (writor + daemon update)
└── data/brain/         # Brain-specific data (TickTick sync, energy logs)
```

**Plugins Structure** :
```
.claude-plugin/
├── plugin.json         # Manifest (name, version, agents, skills, commands)
├── agents/*.md         # Agents (≤30 lignes chacun)
├── skills/*/*.md       # Skills (≤50 lignes implémentation)
└── commands/*.yaml     # Commands metadata
```

### Règles Sorties

**CRÉER TOUJOURS** :
- `.plan/state.json` (source vérité workflow)
- `.plan/tasks.md` (tracking human-readable)
- Architecture si >3 agents ou décisions clés

**JAMAIS CRÉER** :
- README.md (documentation = context.json)
- REPORT.md, SUMMARY.md (artifacts parasites)
- `.backup`, `.tmp`, `.old` (Git = historique)
- Fichiers temporaires hors scope défini

### Validation Output

**Avant finaliser** :
1. Grep context.json (vérifier pas doublon)
2. Glob scope (vérifier pas fichier parasite)
3. Validate JSON/YAML (strict-validation skill)
4. Update state.json (final step)

### Format Agents History (state.json)

```json
{
  "agents_history": [
    {"agent": "writor", "action": "LOAD context", "timestamp": "2025-10-27T14:30:00Z"},
    {"agent": "executor", "action": "Created skill X", "timestamp": "2025-10-27T14:35:00Z"}
  ]
}
```

**Orchestrator responsabilité** : Update state.json après CHAQUE agent complété.

### Intégration Workflows

**Phase Architect** → Outputs : `.plan/architecture.md` + `state.json`
**Phase Executor** → Outputs : Agents/skills créés + `state.json` update
**Phase Validation** → Outputs : Zero artifacts (validation inline)
