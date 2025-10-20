# ADR-0003: Système Décision Automatique Rollback + Skills Évolution

**Date:** 2025-10-20
**Statut:** Accepted
**Architecture Mode:** Senior System Architect
**Priority:** CRITICAL (git safety, auto-recovery, autonomous improvement)

---

## Contexte

**Problème identifié:**
1. Rollback manual = lent et inefficace (nécessite intervention user)
2. Skills Claude Code = accumulent sans stratégie (30+ sans métrique d'utilité)
3. Pas de décision automatisée "qui rollback?" → chaos
4. Mémoire L1/L2/L3 = pas intégrée avec Skills Management
5. Agents parallèles = risque de conflits sans stratégie coordination

**Objectifs non-fonctionnels:**
- Auto-recovery en <5s (erreur critique)
- Zero-downtime para agent failures
- Skills évolution autonome (quotidien)
- Traçabilité complète (audit trail L3)
- Pas de data loss (L2 backup before rollback)

---

## Décision Architecturale

### 1. MODÈLE DÉCISION ROLLBACK (Hiérarchique)

```
┌─────────────────────────────────────────────┐
│          ERROR EVENT DETECTED               │
│  (pytest fail, syntax error, agent timeout) │
└──────────────────┬──────────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ CLASSIFY ERROR       │
        │ Severity: LOW/MED/HI │
        └──────────┬───────────┘
                   ↓
    ┌──────────────────────────────────┐
    │                                  │
    ↓ SEVERITY_LOW                     ↓ SEVERITY_MED/HIGH
┌─────────────────┐         ┌──────────────────────┐
│ HOOK            │         │ DECISION ENGINE      │
│ (auto-trigger)  │         │ (MetaOrchestrator)   │
│                 │         │                      │
│ <2s decision    │         │ 3-5s analysis:       │
│ Simple rules    │         │ - Error scope        │
│                 │         │ - Test impact        │
│                 │         │ - Agent affected     │
│                 │         │ - Memory consistency │
│                 │         │                      │
│ Action:         │         │ Consulte:            │
│ - Store backup  │         │ - L1 (Redis)         │
│ - Tag commit    │         │ - L2 (PostgreSQL)    │
│ - Monitor       │         │ - L3 (Neo4j)         │
└────────┬────────┘         └──────────┬───────────┘
         │                             │
         ↓ No action                   ↓ Decision: ROLLBACK
    Continue                     ┌──────────────────┐
                                │ EXECUTE ROLLBACK │
                                │ Mode selector:   │
                                │ - SOFT (undo)    │
                                │ - HARD (discard) │
                                │ - BRANCH (v-src) │
                                └──────────┬───────┘
                                           ↓
                                    ┌──────────────┐
                                    │ VERIFY STATE │
                                    │ - Tests pass?│
                                    │ - DBs ok?    │
                                    └──────────────┘
```

### 2. QUI DÉCIDE ROLLBACK?

**Hiérarchie décision:**

| Erreur | Décideur | Timing | Scope | Mode |
|--------|----------|--------|-------|------|
| **Syntax Error** | Hook (regex) | <2s | File | SOFT |
| **Pytest Fail** | Hook (pytest parser) | <2s | Test module | SOFT |
| **Agent Timeout** | MetaOrchestrator | 5s | Agent task | SOFT |
| **Test Suite Fail** | Hook (CI runner) | <2s | All tests | BRANCH |
| **Critical Error** | MetaOrchestrator | 5s | Commit | HARD |
| **Data Corruption** | Manual (safety) | N/A | Full DB | BRANCH |

**Règles décision:**

```python
# Pseudo-code decision tree
def decide_rollback(error_event):
    # SEVERITY CLASSIFICATION
    if error_type == "syntax_error":
        return (HOOK, SOFT, 2)      # < 2s, simple fix
    
    elif error_type == "test_fail":
        if test_scope == "single_file":
            return (HOOK, SOFT, 2)  # Quick fix
        else:
            return (META, BRANCH, 5) # Safer, analysis needed
    
    elif error_type == "agent_fail":
        if error_context == "timeout":
            return (META, SOFT, 5)  # Restart agent
        else:
            return (META, BRANCH, 5) # Unknown = safer
    
    elif error_type == "critical":
        return (META, HARD, 5)      # Full rollback
    
    else:
        return (NONE, NONE, 0)      # Unknown error, log + alert
```

### 3. HOOKS vs AGENTS (Decision Tree)

**Critères:**
- **Speed (<5s)?** → Hook (synchronous)
- **Complexity (>3 rules)?** → Agent (async)
- **Criticality (data-affecting)?** → Agent (safer analysis)
- **Frequency (>10/day)?** → Hook (optimization)

**Allocation:**

| Task | Type | Tool | Reason |
|------|------|------|--------|
| **Syntax check** | Fast | Hook | Regex only, <100ms |
| **Pytest runner** | Fast | Hook | Direct pytest call, <2s |
| **Git checkpoint** | Fast | Hook | Git commands only, <1s |
| **Error classification** | Complex | Agent | NLP analysis needed |
| **Rollback decision** | Complex | Agent | Multi-factor analysis |
| **Skills archival** | Complex | Agent | Metrics + heuristics |
| **Memory consolidation** | Critical | Agent | Must preserve data |
| **Neo4j migration** | Critical | Agent | Distributed transaction |

**Hook Implementations (synchronous):**

```bash
# .claude/hooks/pre-commit-validate.sh
# <1s: Syntax validation (Python/TypeScript)

# .claude/hooks/pytest-runner.sh
# <2s: Run fast tests, fail if any error

# .claude/hooks/git-checkpoint.sh
# <1s: Create atomic git checkpoint

# .claude/hooks/memory-backup.sh
# <5s: Backup L1/L2 before any write operation
```

**Agent Implementations (async):**

```python
# Task(meta, "Analyze error + decide rollback")
# 5s: Full analysis with L1/L2/L3 context

# Task(architect, "Plan Skills evolution")
# 30s: Design archival/merge/split strategy

# Task(sre, "Audit infrastructure metrics")
# 20s: Database health + performance
```

---

## 4. SKILLS ÉVOLUTION (Quotidien + Mensuel)

### Métriques Tracking (L2 PostgreSQL)

**Schema additions:**

```sql
-- Skills usage metrics
CREATE TABLE skills_metrics (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255),
    category VARCHAR(50),           -- 00-system, 01-languages, etc.
    usage_count INT DEFAULT 0,      -- Number of invocations
    last_used TIMESTAMP,
    avg_token_cost FLOAT,           -- Tokens per invocation
    success_rate FLOAT,             -- 0-1 score
    overlap_keywords TEXT[],        -- Potential duplicates
    quality_score FLOAT,            -- Manual/auto-assessed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Skills history (for trend analysis)
CREATE TABLE skills_changelog (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255),
    action VARCHAR(20),             -- archived, merged, split, updated
    reason TEXT,
    old_size_lines INT,
    new_size_lines INT,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- L3 Graph integration
-- Neo4j: SKILL nodes with properties
-- (:Skill {name, category, usage_count, strength, last_accessed})
-- Relations: SUPERSEDES, SIMILAR_TO, DEPENDS_ON
```

### Workflow Quotidien (MetaOrchestrator)

**Chaque matin (9AM cron):**

```python
def daily_skills_evolution():
    # PHASE 1: ANALYSIS (5 min)
    metrics = analyze_skills_usage()
    overlaps = detect_duplicates()
    dead_skills = find_unused_30days()
    
    # PHASE 2: DECISION ENGINE (2 min)
    actions = []
    
    # Rule: Archive if unused 30 days
    for skill in dead_skills:
        if skill.access_count == 0:
            actions.append({
                "action": "archive",
                "skill": skill.name,
                "reason": f"Unused 30 days (last: {skill.last_used})"
            })
    
    # Rule: Merge if >80% semantic similarity
    for overlap in overlaps:
        if overlap.similarity > 0.8:
            actions.append({
                "action": "merge",
                "skill1": overlap.skill1,
                "skill2": overlap.skill2,
                "reason": f"Similarity {overlap.similarity:.0%}"
            })
    
    # Rule: Split if >1000 lines AND >3 distinct topics
    for skill in large_skills:
        if len(skill) > 1000 and num_topics(skill) > 3:
            topics = extract_topics(skill)
            actions.append({
                "action": "split",
                "skill": skill.name,
                "new_skills": topics,
                "reason": f"{len(skill)} lines, {len(topics)} topics"
            })
    
    # PHASE 3: EXECUTION (10 min)
    for action in actions:
        if action["action"] == "archive":
            archive_skill(action["skill"], action["reason"])
        elif action["action"] == "merge":
            merge_skills(action["skill1"], action["skill2"])
        elif action["action"] == "split":
            split_skill(action["skill"], action["new_skills"])
        
        # Log to L2 + L3
        log_to_postgres(action)
        log_to_neo4j(action)
    
    # PHASE 4: REPORT (1 min)
    report = {
        "timestamp": now(),
        "skills_total": len(all_skills()),
        "actions_taken": len(actions),
        "archived": count_by_action("archive"),
        "merged": count_by_action("merge"),
        "split": count_by_action("split"),
        "token_saved": estimate_token_savings(actions)
    }
    
    save_report(report)
    notify_user(report)
```

### Règles Archival (Heuristiques)

```python
class SkillsArchivalStrategy:
    
    def should_archive(skill):
        """Score 0-1: archival likelihood"""
        score = 0
        
        # Factor 1: Usage frequency (weight 40%)
        if skill.usage_count == 0:
            score += 0.4
        elif skill.usage_count < 5:
            score += 0.2
        
        # Factor 2: Recency (weight 30%)
        days_since_last = (now() - skill.last_used).days
        if days_since_last > 30:
            score += 0.3
        elif days_since_last > 14:
            score += 0.15
        
        # Factor 3: Overlap (weight 20%)
        if has_similar_skill(skill):
            score += 0.2
        
        # Factor 4: Documentation (weight 10%)
        if is_poorly_documented(skill):
            score += 0.1
        
        return score > 0.6  # Archive if score > 60%
    
    def should_merge(skill1, skill2):
        """Merge if high semantic similarity + low combined usage"""
        similarity = calculate_similarity(skill1, skill2)
        combined_usage = skill1.usage_count + skill2.usage_count
        
        if similarity > 0.8 and combined_usage < 20:
            return True
        return False
    
    def should_split(skill):
        """Split if large + multiple distinct topics"""
        if len(skill) < 800:
            return False
        
        topics = extract_topics(skill)
        if len(topics) > 3:
            return True
        return False
```

### Intégration L1/L2/L3

**L1 (Redis):** Current skill context
```python
redis.hset(f"skill:{skill_name}", {
    "usage_count": count,
    "last_used": timestamp,
    "quality_score": score
})
```

**L2 (PostgreSQL):** 7 days metrics + changelog
```sql
SELECT skill_name, usage_count, success_rate 
FROM skills_metrics 
WHERE updated_at > NOW() - INTERVAL 7 DAYS;
```

**L3 (Neo4j):** Long-term trends + ADR
```cypher
MATCH (s1:Skill)-[r:SIMILAR_TO]-(s2:Skill)
WHERE r.similarity > 0.8
RETURN s1.name, s2.name, r.similarity
```

---

## 5. MONITORING & MÉTRIQUES (Dashboard)

### Metrics Collectés

```json
{
  "timestamp": "2025-10-20T09:00:00Z",
  
  "rollback_metrics": {
    "total_rollbacks": 42,
    "last_7_days": 3,
    "auto_vs_manual": {"auto": 25, "manual": 17},
    "success_rate": 0.95,
    "avg_recovery_time_seconds": 4.2,
    "by_error_type": {
      "syntax_error": 12,
      "test_fail": 15,
      "agent_fail": 8,
      "critical_error": 7
    }
  },
  
  "skills_metrics": {
    "total_skills": 42,
    "active_skills": 38,
    "archived_30d": 4,
    "avg_usage_per_skill": 18,
    "median_skill_size_lines": 180,
    "overlap_detected": 5,
    "suggested_splits": 2,
    "token_economy": {
      "total_tokens_saved_monthly": 45000,
      "estimated_cost_saved": "$2.25"
    }
  },
  
  "memory_integration": {
    "l1_redis": {"status": "ok", "keys": 127, "bytes": 45000},
    "l2_postgres": {"status": "ok", "rows_metrics": 1240, "size_mb": 34},
    "l3_neo4j": {"status": "ok", "nodes": 450, "relations": 1200}
  },
  
  "agent_health": {
    "parallel_tasks": 8,
    "conflicts_detected": 0,
    "checkpoint_commits": 85,
    "error_rate": 0.02
  }
}
```

### Alertes (Thresholds)

```python
ALERTS = {
    "rollback_spike": {
        "threshold": 5,              # 5+ rollbacks in 1h
        "action": "notify_user + pause_agents"
    },
    "skills_bloat": {
        "threshold": 50,             # 50+ total skills
        "action": "trigger_cleanup"
    },
    "memory_l2_full": {
        "threshold": "80%",          # PostgreSQL 80% capacity
        "action": "archive_old_metrics"
    },
    "agent_conflicts": {
        "threshold": ">0",           # Any conflict detected
        "action": "serialize_writes"
    },
    "recovery_timeout": {
        "threshold": ">30s",         # Rollback taking too long
        "action": "manual_intervention"
    }
}
```

---

## 6. PLAN IMPLÉMENTATION (6 Phases)

### Phase 1: Foundation (Week 1)
**Déléguer à: `code`, `architect`**

1. Create ADR-0003 (THIS FILE)
2. Implement `RollbackDecisionEngine` class
   - Error classification
   - L1/L2/L3 lookup
   - Decision tree logic
3. Extend `MetaOrchestrator` with metrics collection
4. Create PostgreSQL schema for skills_metrics

**Acceptance:**
- Unit tests for decision logic
- Decision tree 90%+ accuracy (vs manual review)

### Phase 2: Hooks Integration (Week 1-2)
**Déléguer à: `code`**

1. Implement 4 core hooks:
   - `pre-commit-validate.sh` (syntax + types)
   - `pytest-runner.sh` (run tests, parse output)
   - `git-checkpoint.sh` (atomic commits)
   - `memory-backup.sh` (L1/L2 backup before writes)

2. Integrate with `RollbackManager`
   - On hook failure → trigger RollbackDecisionEngine
   - Store error context (severity, scope, timestamp)

3. Add hook metrics to L2

**Acceptance:**
- All hooks execute <5s
- 100% uptime (no false errors)
- Rollback triggered correctly 95%+

### Phase 3: Skills Evolution Engine (Week 2)
**Déléguer à: `code`, `architect`**

1. Implement `SkillsEvolutionEngine`:
   - Daily metrics analysis
   - Archive/merge/split decision logic
   - Neo4j graph updates

2. CLI: `python daily_skills_evolution.py`
   - Runs daily via cron (9AM)
   - Generates report + recommendations

3. Auto-execute approved actions:
   - Archive unused skills
   - Merge duplicates
   - Split large files

**Acceptance:**
- 20% reduction in skills bloat (test run)
- Zero data loss on archive
- Reports match manual audit 90%+

### Phase 4: L1/L2/L3 Integration (Week 3)
**Déléguer à: `code`, `debug`**

1. L1 (Redis):
   - Cache skill metadata (usage, score)
   - LRU eviction policy (max 1000 entries)

2. L2 (PostgreSQL):
   - Metrics table with 7-day retention
   - Changelog table for audit trail
   - Queries for trend analysis

3. L3 (Neo4j):
   - SKILL nodes + properties
   - SIMILAR_TO, SUPERSEDES relations
   - Community detection (topic clusters)

4. Tests:
   - Query performance <100ms
   - Data consistency checks
   - Failover scenarios

**Acceptance:**
- All queries run <100ms
- Perfect data consistency L1↔L2↔L3
- 99.9% uptime

### Phase 5: Monitoring Dashboard (Week 3-4)
**Déléguer à: `frontend`, `code`**

1. Metrics endpoint (GraphQL):
   ```graphql
   query MetricsSnapshot {
     rollbackMetrics { ... }
     skillsMetrics { ... }
     memoryHealth { ... }
     alertsList { ... }
   }
   ```

2. React dashboard:
   - Real-time metrics
   - Alert visualization
   - Rollback history graph
   - Skills evolution trends

3. CLI reports:
   - `python show_metrics.py --last-7d`
   - `python check_health.py`

**Acceptance:**
- Dashboard loads <2s
- Metrics update <5s interval
- All charts display correctly

### Phase 6: Full Integration Testing (Week 4)
**Déléguer to: `debug`**

1. End-to-end scenarios:
   - Error inject → Hook catch → Rollback execute → Verify state
   - Skills analysis → Actions → L2 update → L3 sync
   - Agent parallel execution → Conflict detection → Serialize

2. Stress tests:
   - 100 parallel agent tasks
   - 50 rapid error events
   - 1M Neo4j nodes
   - 1GB PostgreSQL dataset

3. Production readiness:
   - Disaster recovery (restore from backup)
   - Failover scenarios
   - Security audit

**Acceptance:**
- 100% success rate on E2E tests
- Stress tests pass within SLA
- Security audit clean

---

## 7. TRADE-OFFS

### Performance vs Safety

**Decision:** Safety-first
- Rollback mode selection: BRANCH > HARD > SOFT
- Slower recovery acceptable if prevents data loss
- Test suite always runs before production commit

### Automation vs Control

**Decision:** Progressive automation
- Week 1-2: Manual approval required
- Week 3+: Auto-execute low-risk actions (archive)
- Never auto-execute high-risk (merge, split)

### Centralized vs Distributed Decisions

**Decision:** Centralized with fallback
- MetaOrchestrator = single source of truth
- Hooks = fast path for simple errors
- Agent failures → automatic escalation to MetaOrchestrator

---

## 8. RISQUES & MITIGATIONS

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| **Rollback cascade** | Data loss | Backup L1/L2 before each write |
| **Skills over-archival** | Loss of useful skills | Manual review before archive, 7d grace period |
| **Merge conflicts** | Code chaos | Test suite must pass after merge |
| **Agent conflicts** | Race conditions | Serialize writes to same file (advisory lock) |
| **Decision engine bug** | Wrong rollback | Unit tests 95%+ coverage + manual audit |
| **Memory corruption** | Inconsistent state | L1/L2/L3 checksums + periodic repair job |

---

## 9. SUCCÈS CRITERIA

| Métrique | Target | Timeline |
|---------|--------|----------|
| **Auto-recovery time** | <5s for 95% errors | Week 2 |
| **Rollback success rate** | 98%+ | Week 2 |
| **Skills consolidation** | 15% reduction in files | Week 3 |
| **Token savings** | 30% reduction in skill tokens | Month 1 |
| **Memory consistency** | 100% L1/L2/L3 sync | Week 3 |
| **Dashboard uptime** | 99.9% | Week 4 |
| **Zero data loss** | 100% zero events | Ongoing |

---

## 10. ALTERNATIVES REJETÉES

### Option A: Manual rollback only
**Rejectée:** Trop lent (5-30 min), ne scale pas avec 50+ agents

### Option B: Simple hook-based (no agent decision)
**Rejectée:** Trop simpliste pour erreurs complexes, pas d'analyse contexte

### Option C: Distributed rollback (each agent decides)
**Rejectée:** Risque de conflits, pas de coordination, audit trail complexe

### Option D: Rollback à la main via CLI
**Rejectée:** User dépendence = bottleneck, AGI pas vraiment autonome

---

## 11. RÉFÉRENCES

- `RollbackManager`: `/home/pilote/projet/agi/.claude/hooks/rollback_manager.py`
- `MetaOrchestrator`: `/home/pilote/projet/agi/.claude/meta/orchestrator.py`
- `GitCheckpointManager`: `/home/pilote/projet/agi/.claude/hooks/git_checkpoint_wrapper.py`
- Memory System: Backend `/backend/services/{redis,neo4j,graph}_memory.py`
- Skills directory: `/.claude/skills/` (30+ active)
- Redis L1 service: `/backend/services/redis_memory.py`
- PostgreSQL L2: `backend/config/agi_config.py`
- Neo4j L3: `backend/services/neo4j_memory.py`

---

**Version:** 1.0
**Architecture:** Senior System (Haiku 4.5)
**Next Review:** 2025-11-20
