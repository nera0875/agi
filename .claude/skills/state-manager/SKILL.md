---
name: state-manager
description: Update .plan/state.json avec état courant
type: implementation
---

## Concept

Central state management - tracks current phase, actions, blockers, history pour context-aware routing.

## Fields

**Current**: phase, agent, last_action, timestamp
**Blockers**: [{type: "gate", name, status}]
**History**: [{agent, phase, timestamp, action, files, status}]
**Metadata**: {progress, phases_done, total_phases}

## Update Pattern

```javascript
state.current_phase = "implementation";
state.last_action = "Executor: created agents";
state.last_action_timestamp = now();
state.agents_history.push({
  agent: "executor", phase: "impl",
  timestamp: now(), action: "Create agents",
  output_files: [...], status: "completed"
});
state.metadata.progress = 50;
writeFile('.plan/state.json', JSON.stringify(state, null, 2));
```

## Return Format

```json
{
  "status": "updated",
  "phase": "implementation",
  "progress": 50,
  "timestamp": "2025-10-25T10:30:00Z"
}
```
