# Cascade Automation - Implementation Guide

## WORKFLOW ABSOLU (From CLAUDE.md)

This skill implements the core automation patterns from the absolute workflow:

```
1. think("bootstrap") OR think("contexte [sujet]")  → Analyze L1/L2/L3
2. Task(subagent_type="task-executor", ...) × N     → Parallel execution
3. Aggregate results JSON                            → CEO synthesizes
4. memory(action="store", ...)                       → Store important data
5. Hooks capture automatically (background)          → Cascade automation
```

**Section 5 is where cascade-automation applies:** After phase completion, hooks automatically evaluate next state and trigger cascades.

---

## PHASE PIPELINE (Sequential + Parallel)

From CLAUDE.md - 6-phase architecture:

```
Phase 1: UNDERSTANDING (parallel ask × N)
         ↓ MOI agrège résultats
Phase 2: RESEARCH (parallel research × N)
         ↓ MOI agrège résultats
Phase 3: ARCHITECTURE (architect × 1-3)
         ↓ MOI valide architecture
Phase 4: IMPLEMENTATION (parallel code/frontend × N)
         ↓ MOI agrège code
Phase 5: VALIDATION (parallel debug × N)
         ↓ MOI vérifie qualité
Phase 6: DOCUMENTATION (docs × 1)
```

**Cascade rules:**
- Phase gates = automatic quality checks
- If phase incomplete → Retry with reduced scope
- If phase complete → Auto-cascade to next

---

## HOOKS AUTOMATION (4 Built-in Hooks)

From CLAUDE.md - Hooks are level 2 automation:

### Hook 1: Phase Completion → Phase Cascade

**When:** All agents in phase X finish

**Check:**
```python
def evaluate_phase_complete(phase_results):
    """Quality gate for phase completion"""

    # Minimum data completeness
    if len(phase_results) < MIN_AGENTS_COMPLETE:
        return False

    # Result quality threshold
    complete = [r for r in phase_results if not r.get('timeout')]
    if len(complete) / len(phase_results) < 0.80:  # 80% pass rate
        return False

    # Aggregate confidence
    confidence = sum(r.get('confidence', 0) for r in complete) / len(complete)
    if confidence < 0.75:
        return False

    return True

# If passes: Cascade to next phase
if evaluate_phase_complete(phase_results):
    Task(next_phase_agent, prompt)  # AUTO: Launch next phase
else:
    # Retry with reduced scope
    Task(phase_agent, reduced_scope_prompt)
```

**Implementation:**
- File: `hooks-cascade.json`
- Trigger: After all agents in phase complete or timeout
- Action: Run quality gate → Decide cascade vs retry

---

### Hook 2: Agent Timeout → Smart Retry

**When:** Agent exceeds deadline

**Logic:**
```python
def handle_agent_timeout(agent_result):
    """Intelligent retry on timeout"""

    # Check if partial results usable
    if agent_result.get('completed', 0) >= 0.70:
        # 70%+ complete = accept and cascade
        return {
            'action': 'accept_partial',
            'continue': True
        }

    # If <70% complete: Try again with reduced scope
    failed_items = agent_result.get('failed_items', [])

    # Check retry history
    if agent_result.get('retry_count', 0) >= 3:
        return {
            'action': 'abort',
            'reason': 'Max retries exceeded',
            'continue': False
        }

    # Partition: Split failed items across multiple agents
    partitions = partition(failed_items, batch_size=5)
    return {
        'action': 'partition_retry',
        'batches': len(partitions),
        'timeout_reduced': True,  # 5s shorter deadline
        'continue': True
    }

# Apply retry logic
retry_decision = handle_agent_timeout(agent_result)
if retry_decision['action'] == 'partition_retry':
    for batch in retry_decision['batches']:
        Task(agent, f"Scan batch: {batch}", deadline=15)  # Reduced deadline
```

**Implementation:**
- File: `hooks-cascade.json`
- Trigger: Agent result has `timeout: true`
- Action:
  - If 70%+ complete → accept + cascade
  - If <70% complete → partition and retry
  - If 3+ retries → give up + continue with partial

---

### Hook 3: Pattern Detection → Skill Generation

**When:** Same pattern appears 3+ times

**Pattern tracking:**
```python
class PatternDetector:
    def __init__(self):
        self.patterns = {}  # pattern_name -> count

    def detect(self, event):
        """Detect automation opportunity"""

        # Pattern examples:
        # "scan backend/services/*.py" appears in:
        #   - debt_hunter audit
        #   - security_sentinel check
        #   - performance_optimizer analysis

        pattern_signature = extract_pattern_signature(event)

        if pattern_signature in self.patterns:
            self.patterns[pattern_signature]['count'] += 1
        else:
            self.patterns[pattern_signature] = {
                'count': 1,
                'first_seen': now(),
                'contexts': [event.context]
            }

        return self.patterns[pattern_signature]

    def check_skill_generation(self, pattern):
        """Should we generate a skill from this pattern?"""

        if pattern['count'] >= 3:  # Magic number: 3
            return True
        return False

# Skill generation
pattern = pattern_detector.detect(current_event)
if pattern_detector.check_skill_generation(pattern):
    skill = generate_skill_from_pattern(pattern)
    save_skill_to_repo(skill)

    memory(action="store", data={
        "type": "pattern_automation",
        "pattern_name": pattern['name'],
        "skill_path": skill['path'],
        "created_at": now(),
        "contexts": pattern['contexts']
    })
```

**Implementation:**
- File: `pattern-detector.json`
- Trigger: Pattern event counter reaches 3
- Action: Generate skill + store in memory + save to repo

**Skill generation output example:**
```
/home/pilote/projet/agi/.claude/skills/00-system/cascade-automation/patterns/
  └── backend-services-scan.md

---
name: "Backend Services Scan"
description: "Fast scan of backend services directory - optimized from repeated pattern"
tags: ["backend", "scan", "performance"]
pattern_count: 3
contexts: ["debt_hunter", "security_sentinel", "performance_optimizer"]
timeout: 20s
scope: "backend/services/*.py"
---

This skill was auto-generated after pattern appeared 3 times...
```

---

### Hook 4: Critical Result → Auto-Storage

**When:** Result contains important finding

**Storage criteria:**
```python
AUTO_STORE_THRESHOLDS = {
    "CRITICAL": True,           # Any CRITICAL tag
    "HIGH": True,               # Any HIGH priority
    "cost_saving": 100,         # >$100/month savings
    "security_issue": True,     # Any security finding
    "performance_improvement": 0.20,  # >20% improvement
    "pattern_count": 3,         # Pattern appears 3+ times
}

def should_auto_store(result):
    """Determine if result worth storing in memory"""

    # Check priority tags
    if result.get('priority') in ['CRITICAL', 'HIGH']:
        return True

    # Check cost impact
    if result.get('cost_impact', 0) > AUTO_STORE_THRESHOLDS['cost_saving']:
        return True

    # Check security findings
    if result.get('security_issues', 0) > 0:
        return True

    # Check performance improvements
    if result.get('performance_improvement', 0) > AUTO_STORE_THRESHOLDS['performance_improvement']:
        return True

    return False

# Auto-store if important
if should_auto_store(agent_result):
    memory(action="store", data={
        "type": agent_result['type'],
        "content": agent_result,
        "phase": current_phase,
        "agent_id": agent_result['agent_id'],
        "priority": calculate_priority(agent_result),
        "timestamp": now(),
        "auto_stored": True
    })
```

**Implementation:**
- File: `hooks-cascade.json`
- Trigger: Agent returns result with `priority` or `impact` metrics
- Action: Auto-store to PostgreSQL + Neo4j + Redis

---

## AGENT DEADLINES (From CLAUDE.md)

Timeout strategy for efficient cascading:

```markdown
| Type Tâche | Timeout | Cascade Rule |
|------------|---------|--------------|
| Scan 1-5 files | 10s | If fail: skip, continue |
| Scan 10-20 files | 20s | If <70%: retry partitioned |
| Grep pattern | 15s | If fail: accept partial |
| Plan phase | 30s | If fail: redesign + retry |
| Code feature | 30s | If fail: split into smaller |
| Run tests | 20s | If fail: run subset + mark |
| Documentation | 30s | If fail: generate skeleton |
```

**Cascade logic:**
- **10s timeout** → Super strict, accept 50%+ results
- **20s timeout** → Moderate, accept 70%+ results
- **30s timeout** → Generous, accept 80%+ results

```python
def accept_partial_threshold(deadline_seconds):
    """What % completeness triggers 'good enough'?"""

    mapping = {
        10: 0.50,   # 10s deadline: 50%+ = accept
        15: 0.60,   # 15s deadline: 60%+ = accept
        20: 0.70,   # 20s deadline: 70%+ = accept
        30: 0.80,   # 30s deadline: 80%+ = accept
    }
    return mapping.get(deadline_seconds, 0.70)  # Default 70%
```

---

## LEARNING LOOPS (Feedback → Improvement)

From CLAUDE.md section - use orchestration feedback to improve:

```python
class OrchestrationLearning:
    def __init__(self):
        self.feature_history = []

    def capture_feedback(self, feature_result):
        """After feature completion, capture learning"""

        feedback = {
            "feature_name": feature_result['name'],
            "phases_completed": len(feature_result['phases']),
            "total_time_seconds": feature_result['duration'],
            "total_agents_used": sum(len(p) for p in feature_result['phases']),
            "agents_per_phase": [len(p) for p in feature_result['phases']],
            "timeouts_count": feature_result.get('timeout_count', 0),
            "retries_count": feature_result.get('retry_count', 0),
            "quality_score": feature_result.get('quality', 0.95),
            "lessons_learned": []
        }

        # Extract lessons
        if feature_result.get('timeout_count', 0) > 0:
            feedback['lessons_learned'].append({
                'type': 'timeout_pattern',
                'phases': feature_result['phases_with_timeouts'],
                'suggestion': 'Increase deadline by 5-10 seconds'
            })

        if feature_result.get('phase_4_slow'):
            feedback['lessons_learned'].append({
                'type': 'bottleneck',
                'phase': 4,
                'suggestion': 'Parallelize code/frontend agents better'
            })

        # Store learning
        if feedback['quality_score'] > 0.90:
            memory(action="store", data={
                "type": "orchestration_learning",
                "feedback": feedback,
                "timestamp": now()
            })

        self.feature_history.append(feedback)
        return feedback

    def improve_orchestrator(self):
        """Update orchestrator config based on learnings"""

        if len(self.feature_history) < 3:
            return  # Need at least 3 data points

        # Aggregate patterns
        avg_time = mean([f['total_time_seconds'] for f in self.feature_history])
        avg_agents = mean([f['total_agents_used'] for f in self.feature_history])
        timeout_rate = mean([f['timeouts_count'] for f in self.feature_history])

        # Suggestions
        improvements = {
            "avg_duration": f"{avg_time}s",
            "expected_agents": int(avg_agents),
            "timeout_rate": f"{timeout_rate:.1%}",
        }

        # Update config if patterns clear
        if timeout_rate > 0.05:  # >5% timeout rate
            improvements['action'] = 'increase_deadlines_by_10s'

        if avg_agents > 20:  # Using too many agents
            improvements['action'] = 'consolidate_phases'

        return improvements
```

**Implementation:**
- File: Orchestrator logs (background)
- Trigger: Feature completion
- Action: Analyze patterns + suggest config updates

---

## CONFIG FILES (Included)

### 1. hooks-cascade.json

```json
{
  "hooks": [
    {
      "id": "phase_complete_cascade",
      "trigger": "phase_complete",
      "condition": "quality_score >= 0.80",
      "action": "cascade_to_next_phase",
      "otherwise": "retry_with_reduced_scope"
    },
    {
      "id": "agent_timeout_retry",
      "trigger": "agent_timeout",
      "condition": "completed >= 0.70",
      "action": "accept_partial_and_continue",
      "otherwise": {
        "action": "partition_and_retry",
        "max_retries": 3
      }
    },
    {
      "id": "pattern_detection_skill",
      "trigger": "pattern_count >= 3",
      "action": "generate_skill_from_pattern",
      "save_location": "/skills/00-system/cascade-automation/patterns/"
    },
    {
      "id": "critical_result_storage",
      "trigger": "result_priority in [CRITICAL, HIGH]",
      "action": "memory_store",
      "store_to": ["postgresql", "neo4j", "redis"]
    }
  ]
}
```

### 2. phase-gates.json

```json
{
  "phase_gates": {
    "phase_1_understanding": {
      "min_agents_complete": 2,
      "pass_rate_threshold": 0.80,
      "confidence_threshold": 0.75,
      "cascade_on_pass": "phase_2",
      "retry_on_fail": true,
      "reduced_scope": "top_5_files"
    },
    "phase_2_research": {
      "min_agents_complete": 2,
      "pass_rate_threshold": 0.70,
      "confidence_threshold": 0.70,
      "cascade_on_pass": "phase_3",
      "accept_partial": true
    },
    "phase_3_architecture": {
      "min_agents_complete": 1,
      "pass_rate_threshold": 0.90,
      "confidence_threshold": 0.85,
      "cascade_on_pass": "phase_4",
      "mandatory": true
    },
    "phase_4_implementation": {
      "min_agents_complete": 3,
      "pass_rate_threshold": 0.80,
      "confidence_threshold": 0.75,
      "cascade_on_pass": "phase_5",
      "parallel_agents_allowed": true
    },
    "phase_5_validation": {
      "min_agents_complete": 2,
      "pass_rate_threshold": 0.90,
      "confidence_threshold": 0.85,
      "cascade_on_pass": "phase_6",
      "mandatory": true
    },
    "phase_6_documentation": {
      "min_agents_complete": 1,
      "pass_rate_threshold": 0.95,
      "confidence_threshold": 0.90,
      "final_phase": true
    }
  }
}
```

### 3. pattern-detector.json

```json
{
  "pattern_templates": [
    {
      "name": "backend_services_scan",
      "pattern": "Scan backend/services/*.py - list classes",
      "contexts": ["debt_hunter", "security_sentinel", "performance_optimizer"],
      "threshold": 3,
      "skill_template": "scan_pattern.md"
    },
    {
      "name": "frontend_components_audit",
      "pattern": "Scan frontend/src/components/*.tsx - list exports",
      "contexts": ["code_guardian", "frontend", "docs_keeper"],
      "threshold": 3,
      "skill_template": "scan_pattern.md"
    },
    {
      "name": "database_migration_check",
      "pattern": "Check PostgreSQL migrations status",
      "contexts": ["infra_watch", "security_sentinel", "performance_optimizer"],
      "threshold": 3,
      "skill_template": "db_check_pattern.md"
    }
  ],
  "generation_rules": {
    "min_pattern_count": 3,
    "skill_location": "/skills/00-system/cascade-automation/patterns/",
    "auto_commit": false,
    "require_manual_review": true
  }
}
```

---

## INTEGRATION CHECKLIST

To implement cascade-automation:

- [ ] Create orchestrator event listener (listens for phase completion)
- [ ] Implement phase gates (quality score calculation)
- [ ] Add smart retry logic (partition on timeout)
- [ ] Build pattern detector (count repeated patterns)
- [ ] Implement skill generator (create .md from patterns)
- [ ] Connect memory storage hooks (auto-store CRITICAL/HIGH)
- [ ] Add learning loop (capture orchestration feedback)
- [ ] Test cascade behavior (dry-run 1 feature)
- [ ] Monitor effectiveness (track metric improvements)

---

**Implementation Status:** Ready for coding
**Related Files:**
- `/home/pilote/projet/agi/.claude/skills/00-system/agent-orchestration/`
- `/home/pilote/projet/agi/.claude/skills/00-system/agent-pool/`
- `/home/pilote/projet/agi/.claude/skills/06-workflow/phase-pipeline/`

**Next Steps:**
1. Create event listener in orchestrator
2. Implement phase gates + cascade logic
3. Test with real feature (recommend: small feature first)
4. Iterate based on logs + learning feedback
