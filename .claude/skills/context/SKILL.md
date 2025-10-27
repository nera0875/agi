---
name: context
description: Patterns contextualisation - quelles infos stocker, format, quand mettre à jour
---

# Context - Patterns Contextualisation

Patterns mémorisation système pour orchestrator (RULES.md Niveau 11).

## Quand Stocker

Stocker si :
- Agent/skill créé ou modifié
- Décision architecture prise
- Workflow validé
- Pattern découvert
- Milestone atteint
- Info oubliable coûte >30min réexpliquer

## Implémentation

**Format générique** (définition) : `[Date Heure] Sujet - Description concise → Impact: fichiers`

**Context core skill** (implémentation) : Orchestrator utilise `Task("writor", "MODE: WRITE ...")` pour charger/écrire `.claude/data/brain/context.json` (structure JSON avec entries[], date, event, details, impact, links)

Fichier mémoire : `.claude/data/brain/context.json`

## Règles

- [Date] pour timeline
- → Impact/Lien pour connexions
- [OBSOLÈTE] marquer sans supprimer
- Phrases complètes, pas compression
- **Accès mémoire** : Via agent `writor` avec Skill("context") (pas lecture manuelle)
