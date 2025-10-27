---
name: architecture-validator
description: Valide structure architecture.md - agents/skills/commands définition
type: implementation
---

## Concept

Validates architecture.md structure - ensures all components properly defined and limits respected.

## Validation Checks

```javascript
// Agents: 3 BASE, ≤5 SUPP
if (agents.BASE.count != 3) error("BASE must be 3");
if (agents.SUPP.count > 5) error("SUPP max 5");

// Skills: ≤10 implem, ≤14 total
if (skills.implementation.count > 10) error("Implem max 10");
if (skills.total > 14) error("Total max 14");

// Commands: ≤8
if (commands.count > 8) error("Commands max 8");

// plugin.json counts match
if (plugin.agents.length != agents.total) error("Count mismatch");
```

## Return Format

```json
{
  "status": "valid|invalid",
  "agents_valid": true,
  "skills_valid": true,
  "commands_valid": true,
  "plugin_json_valid": true,
  "errors": [],
  "warnings": [],
  "ready_implementation": true
}
```
