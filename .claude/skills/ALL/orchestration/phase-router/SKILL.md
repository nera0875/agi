---
name: phase-router
description: Routing phases - mapping phase status to next agent
type: implementation
---

## Concept

Maps phase status → next phase and agent.

## Transitions

```
discovery → architecture (architect)
architecture → implementation (executor) [gate: user_approval]
implementation → validation (writor)
validation → complete [gate: user_approval_final]
```

## Logic

```javascript
switch(phase) {
  case "discovery": return {next_agent: "architect"};
  case "architecture":
    if (gate.pending) return {status: "blocked"};
    return {next_agent: "executor"};
  case "implementation": return {next_agent: "writor"};
  case "validation":
    if (gate.pending) return {status: "blocked"};
    return {status: "complete"};
}
```

## Return

```json
{"next_agent": "architect|executor|writor", "blocked": bool}
```
