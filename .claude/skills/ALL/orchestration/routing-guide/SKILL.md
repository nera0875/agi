---
name: routing-guide
description: How intelligent routing works - state-based agent selection
type: documentation
---

# Routing Guide - project-builder-v2

## Overview

Routing system automatically determines next agent and action based on project state, phase status, and blockers.

## Routing Rules

### Detection: Project State

**Mode: NOUVEAU** (no .plan/ directory)
- Trigger: First run of project-builder on new project
- Next Agent: instructor
- Action: Ask discovery questions

**Mode: EN_COURS** (recent .plan/, modified <7 days)
- Trigger: Resuming active project
- Next Agent: Determined by state.json.current_phase + status
- Action: Continue from where left off

**Mode: REPRISE** (old .plan/, modified >7 days)
- Trigger: Resuming abandoned project
- Next Agent: instructor
- Action: Audit architecture, check for obsolescence

### Routing: Phase Transitions

```
discovery (completed) → architecture phase
  Next Agent: architect

architecture (completed) → check gate
  Gate: user_approval_architecture
  ✓ Approved → implementation phase
           → executor
  ✗ Pending → blocked (awaiting user)

implementation (completed) → validation phase
  Next Agent: writor

validation (completed) → check gate
  Gate: user_approval_final
  ✓ Approved → project complete
  ✗ Pending → blocked (awaiting user)
```

## Implementation

Routing logic lives in:
- **routing.yaml**: Static rules + phase transitions
- **state.json**: Dynamic state (current_phase, blockers, gates)
- **workflow-orchestration skill**: Executes routing decision

Query: `Task("project-builder-v2:workflow-orchestration", "Determine next agent")`

## Blockers

If project has active blockers (gates), routing returns:
```json
{
  "status": "blocked",
  "blockers": [...],
  "message": "Awaiting user approval on architecture"
}
```

Workflow cannot progress until blockers resolved.
