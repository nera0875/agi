# AGI Memory Management - Detailed Instructions

## Memory Architecture Overview

### Three-Tier System

**L1 (Redis) - Working Memory (0-10 minutes)**
- Current conversation context
- Active task state
- Short-lived variables
- Auto-expires: TTL-based eviction
- Speed: <1ms read/write

**L2 (PostgreSQL) - Short-Term Memory (1 hour - 1 week)**
- Recent decisions and context
- Embeddings for semantic search
- Conversation history with metadata
- Consolidation source from L1
- Speed: 1-10ms read/write

**L3 (Neo4j) - Long-Term Memory (permanent)**
- Learned patterns and relationships
- Conceptual knowledge graph
- Connection between past decisions
- Neurotransmitter-weighted edges
- Speed: 100-1000ms (rarely queried directly)

---

## Consolidation Workflow

### Automatic Consolidation (Background Job)

**Every 5 minutes:**
1. Scan L1 for items aged > 5 minutes
2. Move aged items to L2 with timestamp
3. Scan L2 for items aged > 1 hour
4. Calculate relevance score using LTP/LTD
5. If relevance > threshold: move to L3 as graph nodes
6. Delete from L2 if LTD applied

**Pseudo-code:**
```python
# L1 → L2 (age-based)
for item in redis_scan():
    if item.age > 5 minutes:
        postgres_insert(item, timestamp=now)
        redis_delete(item)

# L2 → L3 (relevance-based)
for item in postgres_query("age > 1 hour"):
    relevance = calculate_ltp_lts(item)
    if relevance > 0.7:
        neo4j_create_node(item, weight=relevance)
        postgres_delete(item)
```

### Manual Consolidation

Call when needed (user request, anomaly detection):
```python
from cortex.consolidation import ConsolidationOrchestrator

orchestrator = ConsolidationOrchestrator()
result = await orchestrator.consolidate_all()
# Returns: {l1_moved: N, l2_moved: M, l3_created: K}
```

---

## Neurotransmitter System (LTP/LTD)

### Long-Term Potentiation (LTP) - Strengthen

**Triggers LTP:**
- Memory accessed N times in last hour
- Marked as "important" by user/system
- Validated as correct prediction
- Part of recurring pattern

**Effect:**
- Increase weight in L3 graph edges
- Move to L3 earlier (lower consolidation threshold)
- Prevent automatic deletion (LTD blocking)

**Implementation:**
```python
from backend.services.neurotransmitter_system import NeurotransmitterSystem

nts = NeurotransmitterSystem()

# Strengthen memory (LTP)
await nts.apply_ltp(
    memory_id="conv_2025_10_20_xyz",
    strength=0.8,  # 0-1 scale
    reason="accessed_3_times"
)
```

### Long-Term Depression (LTD) - Weaken

**Triggers LTD:**
- Memory not accessed for N days
- Marked as incorrect/irrelevant
- Conflicted with newer memory
- Low relevance decay over time

**Effect:**
- Decrease weight in L3 graph edges
- Move to deletion queue (automatic cleanup)
- Mark for garbage collection

**Implementation:**
```python
# Weaken memory (LTD)
await nts.apply_ltd(
    memory_id="old_conversation_2025_01_01",
    strength=0.2,  # 0-1 scale
    reason="age_>_90_days"
)
```

### Neurotransmitter Scoring

**Calculate Memory Weight:**
```
weight = (access_count / 100) * ltp_bonus - ltd_penalty - age_decay

where:
- access_count = times accessed in last 30 days
- ltp_bonus = 0 to 2.0 (LTP multiplier)
- ltd_penalty = 0 to 1.0 (LTD reduction)
- age_decay = days_old * 0.01 (small decay per day)
```

**Thresholds:**
- weight >= 0.7 → Consolidate to L3
- weight < 0.3 → Mark for LTD (delete)
- weight 0.3-0.7 → Keep in L2

---

## Memory Service API

### Store Memory

```python
from backend.services.memory_service import MemoryService

service = MemoryService()

# Store item
await service.store(
    key="conversation_xyz",
    value={"content": "...", "metadata": {...}},
    metadata={
        "type": "conversation",
        "priority": "high",
        "ttl": 300  # 5 minutes in L1
    }
)
```

### Query Memory

```python
# Query by key (L1 → L2)
result = await service.get(
    key="conversation_xyz"
)

# Search semantic (L1 + L2)
results = await service.search(
    query="topic about memory consolidation",
    limit=10,
    include_l3=False  # Don't query slow L3
)

# Query L3 (slow but comprehensive)
results = await service.query_graph(
    pattern="(memory)-[RELATES_TO]->(?)",
    limit=5
)
```

### Consolidate

```python
# Trigger consolidation
consolidated = await service.consolidate(
    source="L1",
    target="L2"
)
# Returns: {"moved": 42, "deleted": 3}
```

---

## Practical Examples

### Example 1: Store Decision

**Scenario:** Agent makes a decision, should be remembered

```python
decision = {
    "timestamp": "2025-10-20T10:30:00",
    "decision": "Use GraphQL Subscriptions for notifications",
    "context": "Real-time feature discussion",
    "reasoning": "Lower latency, better UX"
}

await memory_service.store(
    key=f"decision_{uuid()}",
    value=decision,
    metadata={
        "type": "decision",
        "priority": "high",  # Goes to L3 faster
        "tags": ["architecture", "notifications"]
    }
)
```

**Consolidation:**
- L1 (0-5min): Active in Redis, accessible
- L2 (5min-1h): Moved to PostgreSQL with metadata
- L3 (1h+): If referenced again (LTP), moved to Neo4j as graph node

### Example 2: Mark Memory as Important

**Scenario:** Decision validated as correct, strengthen it

```python
# Query from L2
decision = await memory_service.get("decision_xyz")

# Mark as validated (LTP)
await neurotransmitter_system.apply_ltp(
    memory_id="decision_xyz",
    strength=1.0,  # Full strength
    reason="validated_in_production"
)

# Effect: Will be consolidated to L3, weighted heavily
```

### Example 3: Handle Deprecated Memory

**Scenario:** Old decision becomes obsolete, weaken it

```python
# Mark as obsolete (LTD)
await neurotransmitter_system.apply_ltd(
    memory_id="old_decision_from_2025_01_01",
    strength=0.1,  # Minimal weight
    reason="superseded_by_newer_decision"
)

# Effect: Will be deleted next consolidation cycle
```

### Example 4: Query Recent Pattern

**Scenario:** Find similar past decisions quickly

```python
# Search L1+L2 (fast, ignoring L3)
similar = await memory_service.search(
    query="GraphQL implementation decisions",
    limit=5,
    include_l3=False  # Fast query (<100ms)
)

# Returns: Recent decisions with similarity scores
```

### Example 5: Semantic Knowledge Query

**Scenario:** Need deep conceptual knowledge (slow but comprehensive)

```python
# Query L3 for relationships
knowledge = await memory_service.query_graph(
    pattern="(Database)-[PERFORMS_BETTER_THAN]->(OtherDB)",
    limit=20
)

# Returns: All known database comparisons from L3
# This is slow (1-2s) but comprehensive
```

---

## Neurotransmitter Rules (Built-in)

### Default LTP Rules

| Condition | Strength | When |
|-----------|----------|------|
| Accessed 1x in 24h | 0.3 | Useful |
| Accessed 3x in 24h | 0.6 | Frequently used |
| Accessed 5x in 24h | 0.9 | Critical pattern |
| Explicitly marked important | 1.0 | User/system decision |

### Default LTD Rules

| Condition | Strength | When |
|-----------|----------|------|
| Not accessed for 7 days | 0.2 | Getting old |
| Not accessed for 30 days | 0.05 | Very old |
| Explicitly marked irrelevant | 0.0 | Delete immediately |
| Conflicts with newer memory | 0.1 | Superseded |

---

## Performance Considerations

### L1 Query (Redis)
- Speed: <1ms per key
- When: Always first choice
- Limitation: Only 5-10min of data

### L2 Query (PostgreSQL)
- Speed: 1-10ms per query
- When: Need recent history
- Limitation: Only 1 hour - 1 week of data

### L3 Query (Neo4j)
- Speed: 100-1000ms per query
- When: Need deep knowledge
- Limitation: SLOW, use timeouts

### Strategy
```python
# FAST: Query L1 only (async, timeout 100ms)
try:
    result = await memory_service.get(key, timeout=0.1)
except TimeoutError:
    # Fallback: recent history from L2
    result = await memory_service.search(key, timeout=1.0)
    # Cache in L1 for next time
    await memory_service.store(key, result, ttl=300)

# SLOW: Only query L3 when necessary
if need_deep_knowledge:
    result = await memory_service.query_graph(pattern, timeout=2.0)
```

---

## Debugging Memory Issues

### Memory Stuck in L1

**Symptom:** Old data still in Redis, not moving to L2

**Diagnosis:**
```python
# Check L1 age
from cortex.consolidation import ConsolidationOrchestrator
orch = ConsolidationOrchestrator()
old_items = await orch.find_old_l1_items(min_age="5min")
print(f"Items in L1: {len(old_items)}")
```

**Fix:**
```python
# Trigger consolidation manually
result = await orch.consolidate_l1_to_l2()
print(f"Moved {result['moved']} items to L2")
```

### Memory Not Consolidating to L3

**Symptom:** Recent data stuck in L2, not moving to L3

**Diagnosis:**
```python
# Check neurotransmitter scores
nts = NeurotransmitterSystem()
l2_scores = await nts.calculate_l2_scores()
high_relevance = [s for s in l2_scores if s['weight'] > 0.7]
print(f"Ready for L3: {len(high_relevance)} items")
```

**Fix:**
```python
# Check LTP/LTD rules
await nts.apply_ltp(
    memory_id="important_decision",
    strength=1.0,
    reason="manual_boost"
)
# Re-run consolidation
await orch.consolidate_l2_to_l3()
```

### Query Too Slow

**Symptom:** Memory queries taking >1s

**Diagnosis:**
```python
# Check which layer queried
import time
start = time.time()
result = await memory_service.search(query="...", include_l3=True)
elapsed = time.time() - start
print(f"Query took {elapsed}s - probably queried L3")
```

**Fix:**
```python
# Force L1+L2 only (fast)
result = await memory_service.search(
    query="...",
    include_l3=False,  # Avoid slow L3
    timeout=0.5  # 500ms max
)
```

---

## Integration Points

### With Think Tool
```python
# Before thinking, load recent context from L2
memory = await memory_service.search("current_task")
think("context " + json.dumps(memory))
```

### With Database Tool
```python
# Raw database access (advanced)
db_query = await database(
    action="query",
    sql="SELECT * FROM l2_memory WHERE priority='high' LIMIT 10"
)
```

### With Memory Tool
```python
# Store thinking results
await memory(
    action="store",
    data={"thought_result": "..."},
    metadata={"type": "thinking"}
)
```

---

## Best Practices

1. **Always store with metadata** - Helps consolidation decisions
2. **Use timeouts for L3 queries** - Avoid hanging on slow graph
3. **Mark important memories explicitly** - Trigger LTP manually
4. **Monitor consolidation jobs** - Ensure L1→L2→L3 flow
5. **Apply LTD to old data** - Prevent memory bloat
6. **Cache frequently accessed items** - In L1 Redis
7. **Don't query L3 in hot paths** - Too slow for real-time

---

**Version:** 1.0.0
**Last Updated:** 2025-10-20
**Maintenance:** Quarterly review of consolidation efficiency
