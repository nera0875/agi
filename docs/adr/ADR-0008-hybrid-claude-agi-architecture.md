# ADR-0008: Architecture Hybride Claude Code + AGI System

**Status:** Accepted
**Date:** 2025-10-20
**Deciders:** AGI Team, Claude Code
**Context:** Critical path reliability vs analytics intelligence

---

## Problem Statement

Nous gérons deux systèmes en parallèle:
1. **Claude Code** (local, fiable, synchrone)
2. **AGI System** (cloud, intelligent, asynchrone)

Tension architecturale critique:
- Claude Code: 100% reliable mais limité (local logs, pas d'analytics)
- AGI System: Intelligent mais fragile (Neo4j DOWN, complexity haute)

**Question:** Où placer git rollback, metrics, skills evolution?

**Services Status (2025-10-20):**
- PostgreSQL: UP (L2 memory)
- Redis: UP (L1 cache)
- Neo4j: DOWN (auth error)

---

## Decision

**HYBRID ARCHITECTURE: Critical path = Claude Code, Analytics = AGI**

### Principe de Base

```
"Use the right tool for the job"
```

- **Critical operations** (rollback, backup, agents orchestration)
  → Claude Code (100% reliable, local, synchrone)
- **Analytics operations** (metrics, trends, skills evolution)
  → AGI System (best-effort, cloud, asynchrone)

### Architecture Globale

```
┌─────────────────────────────────────────────────────────┐
│ CLAUDE CODE (Local, Synchrone, Fiable)                 │
│                                                         │
│  LAYER 1 - CRITICAL PATH                               │
│  ├─ Git hooks (backup, checkpoint, rollback)           │
│  ├─ Agents orchestration (Task calls)                  │
│  ├─ Test orchestration (pytest validation)             │
│  ├─ Local meta logs (.claude/meta/*.json)              │
│  └─ Must be 100% reliable - NO FAILURES TOLERATED      │
│                                                         │
│  Fallback: Revert everything, alert user               │
└─────────────────────────────────────────────────────────┘
           ↓ Async replication
┌─────────────────────────────────────────────────────────┐
│ AGI SYSTEM (Cloud, Best-Effort, Intelligent)            │
│                                                         │
│  LAYER 2 - ANALYTICS (PostgreSQL + Redis)              │
│  ├─ Metrics storage (cost, tokens, skills usage)       │
│  ├─ Trend analysis (over weeks/months)                 │
│  ├─ Skills performance tracking                        │
│  ├─ Conversation patterns                              │
│  └─ Best-effort (fail = skip, continue working)        │
│                                                         │
│  LAYER 3 - ADVANCED (Neo4j - CURRENTLY DISABLED)       │
│  ├─ Graph queries (dependencies, patterns)             │
│  ├─ Machine learning (predict best agents)             │
│  ├─ Knowledge graph (concepts, relationships)          │
│  └─ DISABLED (fix auth issues in Phase 4)              │
└─────────────────────────────────────────────────────────┘
```

### Decision Matrix

| Operation | System | Layer | Critical? | SLA | Fallback |
|-----------|--------|-------|-----------|-----|----------|
| Git rollback | Claude | Local | **YES** | 99.99% | None (fail=halt) |
| Backup | Claude | Local | **YES** | 99.99% | None (fail=halt) |
| Agents Task() | Claude | Local | **YES** | 99.99% | None (fail=halt) |
| Test orchestration | Claude | Local | **YES** | 99.99% | None (fail=halt) |
| Store metrics | AGI-PG | L2 | NO | 95% | Log files |
| Store trends | AGI-PG | L2 | NO | 95% | Skip this period |
| Skills tracking | AGI-PG | L2 | NO | 95% | Lose data, continue |
| Graph patterns | AGI-Neo4j | L3 | NO | 90% | Disabled |

---

## Consequences

### Positive (+)

✅ **Reliability**: Critical path JAMAIS bloqué par system failures
✅ **Graceful Degradation**: Neo4j down? Continue. PostgreSQL down? Continue.
✅ **Local Independence**: Claude Code works offline entirely
✅ **Progressive Evolution**: Start simple (Layer 1), add complexity (Layers 2/3)
✅ **Best of Both Worlds**: Local safety + cloud intelligence
✅ **Clear Boundaries**: Developers know what's critical vs optional

### Negative (-)

⚠️ **Complexity**: Two systems à maintenir
⚠️ **Data Sync**: Potential inconsistency (local vs cloud)
⚠️ **Learning Curve**: Developers need understand both stacks
⚠️ **Partial Failures**: Handle gracefully (non-trivial)

### Mitigations

- Document ULTRA-clear boundaries (voir Decision Matrix)
- Fallbacks pour TOUTES opérations AGI
- Health checks réguliers (PHASE 2)
- Monitoring dual-system
- Evolve gradually avec phases

---

## Implementation Roadmap

### PHASE 1 (DONE - 2025-10-20) - Claude Code Critical Path

**Status: Complete**

- ✅ Git safety hooks active (backup, checkpoint, rollback)
- ✅ Auto-rollback on test failure
- ✅ Agents orchestration (Task calls working)
- ✅ Local meta logs (.claude/meta/*)
- ✅ Clear error handling (fail = revert + alert)

**Code locations:**
- `.claude/hooks/pre-commit` - Backup strategy
- `.claude/hooks/post-test-fail` - Auto-rollback
- `agents/orchestrator.py` - Task invocation
- `.claude/meta/` - Local logs

---

### PHASE 2 (Week 1-2) - PostgreSQL Analytics Layer

**Target: 2025-10-27**

**Tasks:**
1. Create metrics schema (PostgreSQL L2)
   - Table: `metrics_tokens` (tokens/session)
   - Table: `metrics_costs` (API costs hourly)
   - Table: `metrics_agents` (agent performance)

2. Implement MetaOrchestrator writer
   - Async write to PostgreSQL (fire-and-forget)
   - Fallback: If fails → log locally, continue
   - No retry (best-effort philosophy)

3. Implement fallback for PostgreSQL down
   - Write to `/tmp/metrics_fallback.jsonl`
   - Async recovery when DB back UP

4. Dashboard read (read-only analytics)
   - Query metrics via GraphQL
   - Display trends, costs, agent efficiency

**Code to create:**
- `backend/services/metrics_service.py` - Write metrics
- `backend/api/queries/metrics.py` - Read metrics
- `migrations/0008_create_metrics_tables.sql` - Schema

---

### PHASE 3 (Week 3-4) - Skills Evolution Tracking

**Target: 2025-11-03**

**Tasks:**
1. Track skill usage per agent
   - Table: `agent_skills` (what each agent can do)
   - Table: `agent_usage` (each invocation)
   - Table: `skill_performance` (success rate per skill)

2. Detect skill overlap
   - Query: Find multiple agents doing similar things
   - Alert: Consolidate redundant skills

3. Predict best agent for task
   - ML: Based on historical performance
   - Use PostgreSQL data only (neo4j not ready)

**Code to create:**
- `backend/services/skill_service.py` - Usage tracking
- `backend/api/queries/skills.py` - Read analytics
- `migrations/0009_create_skills_tables.sql` - Schema

---

### PHASE 4 (Month 1-2) - Neo4j Graph Layer

**Target: 2025-11-17**

**Pre-requisites:**
- Fix Neo4j auth issues
- Verify connection reliability
- Test failover strategy

**Tasks:**
1. Solve Neo4j authentication
   - Debug current error
   - Test connectivity
   - Verify Cypher queries work

2. Implement graph operations
   - Store relationships (agent→skill→outcome)
   - Query patterns (which combinations work well?)
   - Pattern detection (common execution flows)

3. Enable ML capabilities
   - Graph embeddings for pattern matching
   - Predict agent combinations
   - Anomaly detection

**Conditional:** Only proceed if Neo4j proves reliable

---

## Alternatives Considered

### Option A: Pure Claude Code (Local-Only)

**Pros:**
- ✅ 100% reliable
- ✅ No external dependencies
- ✅ Fast (local I/O)

**Cons:**
- ❌ No historical analytics
- ❌ No trend detection
- ❌ No ML predictions
- ❌ Limited learning capability

**Verdict: REJECTED** - Too limiting long-term

---

### Option B: Pure AGI System (Cloud-First)

**Pros:**
- ✅ Advanced analytics
- ✅ Machine learning possible
- ✅ Scalable

**Cons:**
- ❌ Single point of failure
- ❌ Neo4j currently broken
- ❌ Data loss risk
- ❌ Network dependency
- ❌ Slower (cloud latency)

**Verdict: REJECTED** - Not mature enough, too risky

---

### Option C: Hybrid (SELECTED)

**Pros:**
- ✅ Reliable critical path (Claude Code)
- ✅ Intelligent analytics (AGI Layer 2/3)
- ✅ Graceful degradation (fail AGI = continue)
- ✅ Progressive evolution (Phases 1→2→3→4)
- ✅ Best balance of reliability + capability

**Cons:**
- ⚠️ More complex
- ⚠️ Sync issues possible
- ⚠️ Two systems to maintain

**Mitigations:** Clear boundaries, good fallbacks, gradual rollout

**Verdict: SELECTED** - Best risk/reward profile

---

## Evolution Strategy

### Short-term (Weeks 1-2): PostgreSQL Analytics
- Get metrics flowing
- Build dashboards
- Monitor trends

### Medium-term (Weeks 3-4): Skills Evolution
- Understand agent performance
- Optimize agent selection
- Reduce redundancy

### Long-term (Month 1-2): Neo4j Intelligence
- Graph-based pattern detection
- ML-driven optimization
- Advanced knowledge graph

### Future: Full AGI Autonomy
- Self-improving agent team
- Autonomous skill refinement
- Feedback loops active

**Key principle:** Each phase must work WITHOUT next phase

---

## Communication

### For Developers

- **Critical path (Layer 1):** Local, reliable, must work
- **Analytics (Layer 2/3):** Cloud-based, best-effort, nice-to-have
- **Boundaries:** See Decision Matrix above
- **Fallbacks:** All AGI operations must have fallbacks

### For Operations

- Monitor both systems independently
- Critical alerts: Layer 1 only
- Analytics alerts: Layer 2/3 (best-effort)
- Neo4j issues: Don't block Claude Code

### For Users (AGI)

- Critical path is 100% reliable
- Analytics may be partial (no big deal)
- System learns over time (Phases 2-4)
- Neo4j enables advanced learning later

---

## Success Criteria

✅ **Phase 1 Done:**
- Git hooks working (backup, rollback)
- No test failures = no unexpected rollbacks
- Agents run reliably

✅ **Phase 2 Done:**
- Metrics flowing to PostgreSQL
- Dashboard shows trends
- No impact if PostgreSQL down

✅ **Phase 3 Done:**
- Agent skills tracked
- Overlap detected
- Performance per agent visible

✅ **Phase 4 Done:**
- Neo4j queries working
- Pattern detection active
- ML predictions functional

---

## References

- **Previous ADR:** ADR-0003 (Auto-rollback strategy)
- **Memory ID:** 94cfffb4-84f0-487a-bc48-e4eea77d866d
- **Git commit:** a1ce3ec (initial safety net)
- **Services test:** 2025-10-20 (PG UP, Redis UP, Neo4j DOWN)
- **Tech Stack:** FastAPI + PostgreSQL + Redis + Neo4j + Claude Code

---

## Notes

**Evolution Philosophy:**

This architecture evolves WITH system maturity. As AGI components stabilize (especially Neo4j), more functionality can shift from Claude Code → AGI system. However:

**CRITICAL INVARIANT:** Critical path (rollback, backup, agents) should remain local for reliability.

Ne jamais sacrifier reliability (SLA 99.99%) pour features (SLA 95%).

**Next Review:** 2025-11-17 (after Phase 4 milestone)
