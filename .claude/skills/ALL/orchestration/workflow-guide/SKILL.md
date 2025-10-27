---
name: workflow-guide
description: How to use project workflow - phases and progression
type: documentation
---

# Workflow Guide - project-builder-v2

## Overview

project-builder-v2 manages projects through 4 sequential phases, each with dedicated agents and gates.

## Phases

### 1. Discovery (5-10 min)
**Agent**: instructor
**Output**: .plan/requirements.md, .plan/architecture.md, .plan/workflow.yaml
**Tasks**:
- Answer 5 questions (type, stack, timeline, team, constraints)
- Generate requirements document
- Propose architecture structure
- Create initial workflow

### 2. Architecture (5 min)
**Agent**: architect
**Output**: .plan/architecture.md (updated)
**Tasks**:
- Design component structure
- Define agents, skills, commands
- Update workflow with implementation timeline
- Gate check: user_approval_architecture

### 3. Implementation (15-30 min)
**Agent**: executor
**Output**: agents/*.md, skills/*/SKILL.md, commands/*.md, plugin.json
**Tasks**:
- Create agents (≤30 lines each)
- Create skills (≤50 lines implementation)
- Create commands (≤20 lines each)
- Generate plugin.json manifest

### 4. Validation (2 min)
**Agent**: writor + reviewer
**Output**: .plan/validation-report.md
**Tasks**:
- Validate file sizes
- Check naming conventions
- Verify no parasite files
- Gate check: user_approval_final

## Progress Tracking

- View progress: `cat .plan/tasks.md`
- Check state: `cat .plan/state.json | jq .metadata`
- Next action: Read state.json.next_action field

## Gates

See gates-guide for blocking checkpoints during workflow.
