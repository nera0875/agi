---
name: "Cascade Automation"
description: "Automation patterns: hooks triggering agents, sequential phases automation, learning loops"
categories: ["system", "automation", "cascade"]
tags: ["hooks", "cascade", "automation", "learning", "pipeline"]
version: "1.0.0"
enabled: true
---

## Overview

Automation patterns for cascading actions throughout agent orchestration pipelines. Level 2 hooks that intelligently trigger next phases, detect patterns, manage retries, and create new skills from repeated patterns.

**Key Concept:** Reduce manual orchestration overhead by automating phase transitions, error recovery, and skill generation.

## When to Use

- **After phase completion** → Auto-trigger next phase?
- **Pattern detected** → Create skill or trigger action?
- **Agent timeout** → Retry with reduced scope?
- **Important result** → Auto-store to memory?
- **Repeated patterns** → Auto-generate new skill?

## Core Patterns

### 1. Phase Cascade (Sequential Automation)

Automatically transition between pipeline phases:

```python
# PHASE 1 DONE
results_phase1 = [ask_agent_1, ask_agent_2, ask_agent_3]

# AUTO: Evaluate readiness
if phase_1_quality_check(results_phase1):
    # CASCADE: Auto-launch PHASE 2
    Task(research, "...")  # Parallel research agents
else:
    # FEEDBACK: Retry Phase 1 with adjusted scope
    Task(ask, "...")  # Retry with smaller scope
```

**Rules:**
- Phase gates = quality thresholds (80% data completeness)
- If incomplete → Retry with reduced scope (not full restart)
- Each phase has success criteria before cascading

---

### 2. Smart Retries (Partial Results Handling)

When agents timeout or fail, retry intelligently:

```python
# Agent timeout scenario
agent_result = {
    "status": "partial",
    "timeout": true,
    "completed": "60%",
    "results": [...],
    "failed_items": ["file_20.py", "file_21.py"]
}

# AUTO: Analyze what failed
if len(failed_items) < 30% of total:
    # Accept partial results, continue
    cascade_to_next_phase(results + partial_results)
else:
    # Retry with partitioned scope
    for batch in partition(failed_items, batch_size=5):
        Task(agent, f"Scan only {batch}, 15s deadline")
```

**Rules:**
- Partial results OK if >= 70% complete
- Automatically partition failing items
- Exponential backoff: 1st retry (15s), 2nd retry (10s), 3rd retry (5s top-items)
- Never retry same scope twice

---

### 3. Pattern Detection → Skill Generation

When pattern appears 3+ times, auto-create skill:

```python
# Track repeated patterns
pattern_detector = PatternStore()

# Each time pattern appears:
for event in orchestrator_events:
    pattern = pattern_detector.detect(event)
    pattern.count += 1

    if pattern.count >= 3:  # Magic number: 3
        # AUTO: Generate skill
        new_skill = generate_skill_from_pattern(pattern)
        save_skill_to_repo(new_skill)

        # MEMORY: Store pattern
        memory(action="store", data={
            "type": "pattern_automation",
            "pattern": pattern.name,
            "generated_skill": new_skill.path,
            "timestamp": now()
        })
```

**Example:**
```
Pattern: "scan backend/*/*.py" appears in:
  1. Audit backend (debt_hunter)
  2. Security check (security_sentinel)
  3. Performance analysis (performance_optimizer)

AUTO: Generate skill "backend-scan" with optimized scope/timeout
```

---

### 4. Result Auto-Storage (Memory Integration)

Important results automatically stored:

```python
# Threshold rules for auto-storage
AUTO_STORE_IF = {
    "critical_finding": true,      # Any "CRITICAL" tag
    "cost_saving": "> $100/month",  # Significant cost impact
    "security_issue": true,         # Any security finding
    "performance_improvement": "> 20%",  # Measurable improvement
    "patterns": "patterns_count >= 3",   # Repeated patterns
}

# After agent result received
for result in agent_results:
    if matches_storage_criteria(result):
        memory(action="store", data={
            "type": result.type,
            "content": result,
            "phase": current_phase,
            "agent": result.agent_id,
            "timestamp": now(),
            "importance": calculate_importance(result)
        })
```

---

### 5. Learning Loops (Feedback → Improvement)

Use feedback to improve future orchestrations:

```python
# Feedback collection after each feature completion
feedback_loop = {
    "feature": "notifications-real-time",
    "phases_completed": 6,
    "total_time": "15 minutes",
    "total_agents": 18,
    "agents_per_phase": [3, 3, 1, 5, 3, 1],
    "timeouts": 2,  # 2 agents timed out
    "retries": 1,   # 1 retry executed
    "quality_score": 0.94,
    "lessons": [
        "PHASE 2 needs 25s instead of 20s",
        "PHASE 4 bottleneck: frontend agent was slow",
        "Parallel execution of Phase 1+2 would save 5min"
    ]
}

# AUTO: Update orchestrator config
if feedback_loop.quality_score > 0.90:
    update_phase_config(
        phase=feedback_loop.phases_with_issues,
        new_timeout=feedback_loop.lessons["timeout_needed"],
        new_parallelism=feedback_loop.lessons["parallelism_opportunity"]
    )

    # MEMORY: Store learning
    memory(action="store", data={
        "type": "orchestration_learning",
        "feature": feedback_loop.feature,
        "improvements": feedback_loop.lessons,
        "impact": {
            "time_saved": "5 minutes",
            "quality_maintained": "94%"
        }
    })
```

---

## Automation Triggers

### On Phase Completion
```markdown
TRIGGER: Phase X successfully completed
ACTION: Evaluate Phase X+1 readiness
  - Check result quality (>80% threshold)
  - Calculate aggregate confidence
  - If ready: Auto-cascade to Phase X+1
  - If not ready: Auto-retry Phase X with adjusted scope
```

### On Agent Timeout
```markdown
TRIGGER: Agent deadline exceeded
ACTION: Intelligent retry
  - If partial results viable (>70%): Accept + cascade
  - If results incomplete (<30%): Partition and retry
  - Track retry history (max 3 retries per scope)
```

### On Pattern Detection
```markdown
TRIGGER: Same pattern appears 3+ times
ACTION: Generate automation skill
  - Extract pattern rules
  - Create .md skill file
  - Save to /skills/00-system/cascade-automation/patterns/
  - Store in memory with timestamp
```

### On Critical Finding
```markdown
TRIGGER: Result tagged as CRITICAL/HIGH priority
ACTION: Auto-store + alert
  - Store to memory immediately
  - Tag with importance score
  - Calculate potential impact
  - Flag for orchestrator dashboard
```

---

## Implementation Rules

**✅ DO:**
- Cascade only after quality gates pass
- Accept partial results pragmatically (70% = good enough)
- Retry with reduced scope, not full restart
- Store learning for continuous improvement
- Generate skills from repeated patterns

**❌ DON'T:**
- Cascade to next phase if quality < 80%
- Retry same failing task identically (will fail again)
- Ignore timeouts (they signal scope too large)
- Create skill after just 1-2 patterns (need 3+ signals)
- Auto-store low-priority results (only critical/high)

---

## Files in This Skill

- **README.md** - Overview + patterns (this file)
- **instructions.md** - Detailed implementation guide + code examples
- **hooks-cascade.json** - Automation trigger definitions
- **phase-gates.json** - Quality thresholds per phase
- **pattern-detector.json** - Pattern templates for auto-skill generation

---

## Related Skills

- `00-system/agent-orchestration` - Master orchestrator patterns
- `00-system/agent-pool` - Agent management + allocation
- `06-workflow/phase-pipeline` - Phase definitions + structure

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Author:** AGI Auto-Apprentice
**Status:** Ready for implementation
