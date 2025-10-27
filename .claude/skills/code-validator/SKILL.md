---
name: code-validator
description: Valide agents/skills/commands - tailles et structure
type: implementation
---

## Concept

Code quality validator - ensures agents/skills/commands meet size limits.

## Validation Rules

**Agents (BASE ≤30 lignes, AJOUT ≤30 lignes justifiés)**:
```bash
for agent in agents/*.md:
  lines=$(wc -l < "$agent")

  # Si ≤30 lignes → OK direct
  [ $lines -le 30 ] && continue

  # Si >30 lignes → vérifier marqueurs AJOUT
  ajouts=$(grep -c "<!-- AJOUT" "$agent")
  [ $ajouts -eq 0 ] && error "Agent >30 lignes sans marqueur AJOUT"

  # Vérifier chaque AJOUT justifié (date + raison + count)
  grep "<!-- AJOUT [0-9-]*:.*([0-9]* lignes)" "$agent" || error "AJOUT format invalide"

  grep -q "^---$" "$agent" || error "Missing frontmatter"
```

**Skills (≤50 if implementation, unlimited if documentation)**:
```bash
for skill in skills/*/SKILL.md:
  type=$(grep "^type:" "$skill" | grep "implementation" && echo "impl" || echo "doc")
  [ "$type" = "doc" ] && continue
  [ $(wc -l < "$skill") -le 50 ] || error "Skill exceeds 50"
```

**Naming (kebab-case)**:
```bash
find . -name "*.md" | grep -E '[A-Z_]|[^a-z0-9-]' && error "Invalid naming"
```

**No Parasites**:
```bash
find . -type f \( -name "*.backup" -o -name "*.old" -o -name "*.tmp" \)
```

## Return Format

```json
{
  "status": "valid",
  "agents": 5,
  "skills": 14,
  "commands": 0,
  "errors": []
}
```
