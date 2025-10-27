---
name: plan-create
description: Crée structure .plan/ complète selon convention/project-structure.json
allowed-tools: Task
argument-hint: "<project-name>"
---

Task("constructor", """
TASK: Créer structure projet .plan/

PROJECT: $ARGUMENTS

ACTIONS:
1. Read .claude/convention/project-structure.json
2. Créer .plan/ directory
3. Générer tous fichiers selon default_structure
4. Initialiser state.json avec projet $ARGUMENTS
5. Créer requirements.md, architecture.md, tasks.md avec sections

DEADLINE: 30 seconds
PARTIAL OK: No

CONTRAINTES STRICTES :
- Respecter project-structure.json strict
- Valider state.json contre schema inline
- kebab-case uniquement
- Aucun fichier parasite
""")
