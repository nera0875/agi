---
name: git-tracker
description: Track fichiers créés/modifiés pour state.json
type: implementation
---

## Concept

Tracker quels fichiers ont été créés/modifiés dans session courante pour documenter dans state.json.

## Implementation Steps

```bash
# 1. Get last state timestamp
last_time=$(jq '.last_action_timestamp' .plan/state.json)

# 2. Find files modified today
find . -type f -newermt "$(date -d '24 hours ago' '+%Y-%m-%d')" > /tmp/modified.txt

# 3. Filter to .plan/ and project files only
grep -E "^\./agents/|^\./skills/|^\./\.plan/" /tmp/modified.txt

# 4. Format for state.json
cat /tmp/modified.txt | sed 's|^./||'
```

## Tracked Patterns

- agents/*.md (nouvea agents)
- skills/*/SKILL.md (nouveaux skills)
- commands/*.md (nouveaux commands)
- .plan/state.json (updates)
- .plan/tasks.md (updates)
- .plan/workflow.yaml (updates)
- plugin.json (créé/modifié)

## Return Format

```json
{
  "files_modified_today": [
    "agents/executor.md",
    "skills/workflow-orchestration/SKILL.md",
    ".plan/state.json"
  ],
  "count": 15,
  "timestamp": "2025-10-25T10:30:00Z"
}
```
