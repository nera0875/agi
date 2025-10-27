---
name: progress-tracker
description: Calcule progress % et détecte blocages stagnation
type: implementation
---

## Concept

Tracks completion percentage across phases, détecte quand projet stagne (status unchanged >3 jours).

## Calculation

```javascript
// Simple: completed / total * 100
completed = workflow.phases.filter(p => p.status == "completed").length;
progress = (completed / workflow.phases.length) * 100;

// Weighted (optional): discovery:25%, architecture:25%, implementation:35%, validation:15%
weights = {discovery: 0.25, architecture: 0.25, implementation: 0.35, validation: 0.15};
weighted = sum(weights[p.name] for p in completed_phases);
```

## Stagnation Detection

```javascript
// If in progress >3 days with no updates = stagnant
days_stagnant = now - state.last_action_timestamp;
if (days_stagnant > 3 && state.current_phase_status == "in_progress") {
  return {status: "stagnant", days: days_stagnant, blocker: true};
}
```

## Return Format

```json
{
  "progress_percentage": 50,
  "phases_completed": 2,
  "total_phases": 4,
  "stagnant": false,
  "days_last_action": 0,
  "eta_completion": "2025-11-15T18:00:00Z"
}
```
