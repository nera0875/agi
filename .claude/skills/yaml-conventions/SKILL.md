---
name: yaml-conventions
description: Format YAML strict - ISO 8601, kebab-case, null handling
---

# YAML Strict Format

YAML parsing breaks with loose formatting. Use strict conventions: ISO 8601 dates, kebab-case identifiers, explicit null handling, pure YAML (no markdown/Python mix).

## Conventions Obligatoires

**Dates: ISO 8601 format (strings, no Python datetime)**
- ✅ `created-at: "2025-10-26T14:30:00Z"` (UTC explicit)
- ✅ `deadline: "2025-11-15"` (dates only, no time)
- ❌ `created: 2025-10-26 14:30:00` (unquoted, ambiguous)
- ❌ `created: !!python/object:datetime.datetime {...}` (Python serialization breaks)

**Naming: kebab-case strict (no underscores, no camelCase)**
- ✅ `project-name`, `user-id`, `created-at`, `test-app`
- ❌ `project_name`, `projectName`, `ProjectName`

**Null Handling: omit vs explicit**
- ✅ `status: "pending"` + omit `description:` (implicit null)
- ✅ `status: "pending"` + `description: null` (explicit null, clearer)
- ❌ `description: None` (Python syntax, breaks YAML)
- ❌ `description: "null"` (string, not null type)

**Pure YAML: no markdown/code blocks**
- ✅ Multiline strings: `|` (literal) or `>` (folded)
- ❌ ```markdown code blocks```
- ❌ Embedded Python/bash syntax

**Enum strict values (no free strings)**
- ✅ `status: "in-progress"` (declared enum)
- ❌ `status: "In Progress"` (different capitalization)

## Line-by-Line Checklist

- [ ] All dates: ISO 8601, quoted strings
- [ ] All identifiers: kebab-case lowercase
- [ ] Nulls: omitted OR explicit `null` (no None/empty)
- [ ] Enums: exact values from spec
- [ ] No markdown/Python/bash embedded
- [ ] Valid YAML: `python -m yaml` parse test

