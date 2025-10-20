# Memory Strategy - Detailed Instructions

## PART 1: Layer Strategies

### L1 (Redis) - Ephemeral Cache

**Purpose:** Ultra-fast, temporary storage for execution state
**TTL:** 5 minutes maximum
**Retention:** Automatic expiration

#### When to use L1:
- Task status (in progress, queued, completed)
- Intermediate results (<100 lines)
- Recent context for current task
- Notifications/alerts pending delivery
- Session state

#### Never in L1:
- ❌ Important insights
- ❌ Architectural decisions
- ❌ Long-term patterns
- ❌ Historical data

#### Example L1 Storage:
```python
memory(action="store", layer="L1", data={
    "type": "task_status",
    "task_id": "scan_backend_20251019",
    "status": "in_progress",
    "progress": 65,
    "ttl_seconds": 300  # 5 min
})
```

---

### L2 (PostgreSQL) - Persistent Memory

**Purpose:** Long-term storage for important results, insights, analysis
**Retention:** Indefinite (archive strategy separate)
**Queryable:** Via `memory(action="retrieve", query="...")`

#### When to use L2:
- Tâche important complétée (>5 min effort)
- Insight découvert (même seul)
- Erreur résolu (pour future reference)
- Analysis result (code audit, performance)
- Decision prise (mais pas architectural)
- Feedback utilisateur important

#### Never in L2:
- ❌ Sensitive data (API keys, passwords)
- ❌ Duplicate existante (check first)
- ❌ Incomplete/noisy data
- ❌ Cache temporaire

#### Example L2 Storage:
```python
memory(action="store", layer="L2", data={
    "type": "insight",
    "title": "Backend memory_service duplication",
    "content": "memory_service.py et graph_service.py partagent 3 méthodes identiques",
    "source": "debt_hunter_20251019_143022",
    "priority": "high",
    "tags": ["duplication", "backend", "refactoring"],
    "recommendation": "Create abstract service parent class"
})
```

---

### L3 (Neo4j) - Knowledge Graph

**Purpose:** Architectural relationships, patterns, decisions
**Structure:** Nodes (concepts) + Relations (relationships)
**Usage:** Design patterns, dependencies, architecture

#### When to use L3:
- Architectural decision (WebSocket vs GraphQL Subscriptions)
- Design pattern discovered (async wrapper, factory, etc)
- Dependency relationship (ServiceA depends on ServiceB)
- Technology choice rationale
- Trade-off analysis documented

#### Never in L3:
- ❌ Routine execution data
- ❌ Temporary task results
- ❌ Instance-specific data
- ❌ Sensitive information

#### Example L3 Storage:
```python
memory(action="store", layer="L3", data={
    "type": "architecture_decision",
    "title": "Real-time notifications = GraphQL Subscriptions",
    "rationale": "Better for existing GraphQL infrastructure",
    "alternatives": ["WebSocket", "Server-Sent Events"],
    "tradeoffs": "Requires Strawberry upgrade",
    "nodes": {
        "Decision": {"id": "notifications_realtime", "label": "GraphQL Subscriptions"},
        "Pattern": {"id": "graphql_pattern", "label": "GraphQL Patterns"}
    },
    "relations": [
        {"from": "notifications_realtime", "type": "IMPLEMENTS", "to": "graphql_pattern"}
    ]
})
```

---

## PART 2: When to Consolidate

### Consolidation Definition
**Consolidate** = Merge similar memories + extract patterns + create reusable skills

### Automatic Triggers

| Condition | Action | Timing |
|-----------|--------|--------|
| L1 Redis >1000 keys | Expire keys >10 min old | Real-time |
| L2 >20 events since last consolidation | Consolidate + cleanup duplicates | Per session |
| Weekly scheduler | Full consolidation | Monday 00:00 UTC |
| Before `compact()` call | Aggressive cleanup | Manual (user request) |

### Consolidation Process

```
1. IDENTIFY similar memories
   - Same type (all "insights", all "patterns")
   - Same domain (memory_service, graph_service)
   - Created within 24 hours

2. EXTRACT common patterns
   - What's the core insight?
   - What's reusable?
   - What's duplicate?

3. CREATE skill if pattern 5+ times
   - Pattern must appear 5+ times to justify skill
   - Skill goes to `.claude/skills/01-common/` or `.claude/skills/02-patterns/`
   - Link consolidated memories to skill

4. MERGE similar memories
   - Keep newest with references to older
   - Remove exact duplicates
   - Update retrieval index

5. CLEANUP
   - Archive old L2 memories (>3 months)
   - Delete bad data (incomplete, corrupted)
   - Rebuild Neo4j indexes
```

### Example Consolidation

**Before:** 5 separate memories
```
1. debt_hunter: "file A too large"
2. code_guardian: "file A low test coverage"
3. performance_optimizer: "file A slow imports"
4. debt_hunter: "file B too large"
5. code_guardian: "file B low test coverage"
```

**After Consolidation:**
```
Consolidated Memory L2:
- "Large backend files (>500 lines): A, B"
- "Low test coverage in: A, B"
- "Performance bottleneck in: A (imports), B (none)"
- "Recommendation: Refactor A, B into modules"

New Skill Created:
- `01-common/large-file-refactoring/`
- Pattern: How to split large files
- Applies to: A, B, and any future large files
```

---

## PART 3: Memory Event Format

### Required Fields
```json
{
  "type": "insight|decision|pattern|error|analysis",
  "content": "Main content (clear, actionable)",
  "source": "agent_name|manual",
  "timestamp": "2025-10-19T14:30:22Z",
  "layer": "L1|L2|L3",
  "priority": "critical|high|normal|low"
}
```

### Optional but Recommended
```json
{
  "tags": ["tag1", "tag2", "domain"],
  "title": "Brief title",
  "relates_to": ["skill_name", "previous_memory_id"],
  "recommendation": "What to do with this"
}
```

### Only for L3 (Architecture)
```json
{
  "architectural": true,
  "nodes": {
    "NodeType": {"id": "unique_id", "label": "Display label"}
  },
  "relations": [
    {"from": "id1", "type": "DEPENDS_ON|IMPLEMENTS|CONFLICTS_WITH", "to": "id2"}
  ]
}
```

---

## PART 4: Storage Decision Rules

### Rule 1: Check Existence
**Before storing → ALWAYS check duplicate**

```python
# ❌ BAD (possible duplicate):
memory(action="store", layer="L2", data={"content": "Backend has duplicates"})

# ✅ GOOD (check first):
existing = memory(action="retrieve", query="backend duplicates")
if not existing:
    memory(action="store", layer="L2", data={"content": "Backend has duplicates"})
```

### Rule 2: Prioritize Layer
**Use lowest layer that fits**

```
L1 if: Temporary + <5min
L2 if: Important + long-term + not architectural
L3 if: Architectural + affects design + reusable pattern
```

### Rule 3: No Sensitive Data
**Never store secrets**

```python
# ❌ BAD:
memory(action="store", data={"api_key": "sk_live_..."})

# ✅ GOOD:
# Don't store. Use environment variables instead.
# memory(action="store", data={"api_key_configured": true})
```

### Rule 4: Tag Consistently
**Tags for discoverability**

```python
# ✅ GOOD:
memory(action="store", data={
    "type": "insight",
    "content": "...",
    "tags": ["backend", "performance", "database", "optimization"]
})

# Enables future retrieval:
memory(action="retrieve", query="tag:performance")
```

### Rule 5: Relate to Context
**Link related memories**

```python
# ✅ GOOD:
memory(action="store", data={
    "type": "decision",
    "content": "GraphQL Subscriptions for real-time",
    "relates_to": [
        "notifications_feature",
        "performance_optimization_20251019",
        "skill/graphql-patterns"
    ]
})
```

---

## PART 5: Integration Points

### After Task Completion
```python
# Task returns result + memory event
Task(ask, "Scan backend for duplicates")
# Returns: {status: "done", result: [...], memory_event: {...}}

# Store result:
if result["memory_event"]:
    memory(action="store", **result["memory_event"])
```

### Before think() Call
```python
# think() may trigger consolidation
think("bootstrap")
# Internally:
# 1. Consolidate L1 (clean old keys)
# 2. Consolidate L2 (merge similar)
# 3. Update L3 relationships
# 4. Return: {L1: [...], L2: [...], L3: [...]}
```

### Weekly Automation
```python
# Runs automatically Monday 00:00 UTC
# Job: Consolidate everything
# - Merge similar L2 memories
# - Archive old (>3 months)
# - Extract patterns → create skills
# - Rebuild indexes
```

### On compact() Request
```python
# User or system calls: compact()
# Aggressive memory cleanup:
# - DELETE duplicates entirely
# - ARCHIVE non-critical old memories
# - CONSOLIDATE everything into skills
```

---

## PART 6: No-Store Checklist

Before storing, verify:

- [ ] Not a duplicate (checked via retrieve)
- [ ] Not sensitive data (no API keys, passwords)
- [ ] Not temporary execution data (should be L1 only)
- [ ] Complete information (not incomplete/partial)
- [ ] Actionable/useful (not noise)
- [ ] Properly typed (type field valid)
- [ ] Appropriate layer (L1/L2/L3 choice valid)
- [ ] Tagged for discovery (tags added)

---

## PART 7: Common Patterns

### Pattern 1: Insight Discovery
```python
# Agent finds important insight
Task(ask, "Scan X")
# Returns: insight about X

# Store for future reference
memory(action="store", layer="L2", data={
    "type": "insight",
    "content": "Insight content",
    "source": "agent_name",
    "priority": "high",
    "tags": ["domain", "topic"]
})
```

### Pattern 2: Architectural Decision
```python
# Architect makes decision
Task(architect, "Design Y")
# Returns: architecture decision

# Store in knowledge graph
memory(action="store", layer="L3", data={
    "type": "architecture_decision",
    "content": "Decision rationale",
    "architectural": true,
    "nodes": {...},
    "relations": [...]
})
```

### Pattern 3: Reusable Pattern Detection
```python
# Agent detects pattern (5+ occurrences)
if occurrences >= 5:
    # 1. Store as pattern L3
    memory(action="store", layer="L3", data={
        "type": "pattern",
        "content": "Pattern description"
    })

    # 2. Create skill
    create_skill(
        path=".claude/skills/01-common/pattern-name/",
        content=skill_content
    )
```

### Pattern 4: Error Resolution
```python
# Error found and fixed
Task(debug, "Fix bug X")
# Returns: error + solution

# Store for future debugging
memory(action="store", layer="L2", data={
    "type": "error",
    "title": "Error Title",
    "content": "Error description",
    "solution": "How it was fixed",
    "tags": ["error", "bug", "domain"],
    "priority": "high"
})
```

---

## PART 8: Consolidation Scenarios

### Scenario 1: Similar Insights
```
Memory 1: "Backend file A is too large (2000 lines)"
Memory 2: "Backend file B is too large (1800 lines)"
Memory 3: "Backend file C is too large (2100 lines)"

Consolidation:
→ Single memory: "Multiple large backend files (A, B, C)"
→ Create skill: "large-file-refactoring"
→ Link skill to all 3 memories
```

### Scenario 2: Repeated Decision
```
Decision 1: "Use GraphQL for auth"
Decision 2: "Use GraphQL for notifications"
Decision 3: "Use GraphQL for logging"

Consolidation:
→ Pattern: "GraphQL everywhere pattern"
→ Create skill: "graphql-pattern"
→ L3 relationship: All decisions use GraphQL
```

### Scenario 3: Duplicate Error
```
Error 1: "Memory not found (L2)"
Error 2: "Memory not found (L2)" [duplicate]
Error 3: "Memory not found (L2)" [duplicate]

Consolidation:
→ Keep Error 1 only
→ Delete Error 2, 3
→ Reference consolidated error from original task
```

---

## PART 9: Practical Examples

### Example: Store Task Result
```python
# Task completes
result = {
    "status": "done",
    "files_scanned": 47,
    "duplicates_found": 3,
    "memory_event": {
        "type": "insight",
        "content": "Backend has 3 duplicate service classes",
        "source": "debt_hunter",
        "layer": "L2",
        "priority": "high",
        "tags": ["backend", "duplication"]
    }
}

# Store automatically
memory(action="store", **result["memory_event"])
```

### Example: Store Architecture Decision
```python
# Architect makes decision
memory(action="store", layer="L3", data={
    "type": "architecture_decision",
    "title": "Notifications = GraphQL Subscriptions",
    "content": "GraphQL Subscriptions chosen for real-time notifications",
    "source": "architect",
    "priority": "critical",
    "architectural": true,
    "relates_to": ["notifications_feature"],
    "nodes": {
        "Decision": {"id": "notif_realtime", "label": "GraphQL Subscriptions"},
        "Technology": {"id": "graphql", "label": "GraphQL"},
        "Service": {"id": "notification_service", "label": "Notification Service"}
    },
    "relations": [
        {"from": "notif_realtime", "type": "USES", "to": "graphql"},
        {"from": "notification_service", "type": "IMPLEMENTS", "to": "notif_realtime"}
    ]
})
```

### Example: Consolidation Trigger
```python
# After multiple tasks
tasks_done = 5
memories_stored = 7

# Consolidate if enough
if memories_stored >= 5:
    consolidate_result = memory(action="consolidate")
    # Returns: {merged: 2, deleted: 1, skills_created: 1}

    # Create new skill if pattern found
    if consolidate_result["skills_created"] > 0:
        create_skill(name="new_pattern")
```

---

## Summary Checklist

✅ **Before Storing:**
- Type field is valid (insight|decision|pattern|error|analysis)
- Not a duplicate (checked)
- Appropriate layer (L1/L2/L3)
- No sensitive data
- Tags added
- Complete information

✅ **Storage Format:**
- Required fields present
- Source identified
- Timestamp ISO8601
- Priority set
- Layer specified

✅ **After Storing:**
- No duplicates in memory
- Relate to existing skills
- Extract patterns if 5+ occurrences
- Consider consolidation
- Update Neo4j relationships (if L3)

---

**Version:** 1.0.0
**Updated:** 2025-10-19
**Related Skills:** None yet (foundational)
