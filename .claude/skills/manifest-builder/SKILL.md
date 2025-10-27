---
name: manifest-builder
description: Génère plugin.json - manifest complet avec tous composants
type: implementation
---

## Concept

Builds plugin.json manifest listing all agents, skills, commands with descriptions.

## Structure

```json
{
  "name": "project-builder-v2",
  "version": "1.0.0",
  "agents": [{name, description, tools, model}],
  "skills": [{name, description, type}],
  "commands": []
}
```

## Generation

Scan agents/ → frontmatter, scan skills/ → frontmatter, scan commands/, merge to JSON.

## Validation

```bash
jq . plugin.json > /dev/null  # Valid JSON
wc -l agents/*.md             # Agent counts
ls skills/*/SKILL.md | wc -l  # Skill counts
```

## Return Format

```json
{
  "status": "created|updated",
  "agents_count": 5,
  "skills_count": 14,
  "commands_count": 0,
  "file": "plugin.json",
  "valid_json": true,
  "checksum": "sha256:..."
}
```
