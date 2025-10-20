---
title: "ADR - Architecture Decision Records"
description: "Document architectural decisions with context, rationale, and consequences for future maintainers"
category: "Architecture"
level: "Advanced"
tags: ["adr", "documentation", "decisions", "trade-offs", "process"]
---

# Architecture Decision Records (ADR)

## Overview
Architecture Decision Records (ADRs) are lightweight documents that capture important decisions, their context, and consequences. They prevent repeating past discussions and help future developers understand "why" the system works this way.

## ADR Format Template

```markdown
# ADR-XXXX: [Short, imperative title]

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-YYYY
**Author:** Name or Agent

## Context
[Explain the problem/situation that prompted this decision]
- What's the background?
- Why does this matter?
- What constraints exist?
- What alternatives were considered?

## Decision
[State the chosen solution clearly and concisely]
- What are we doing?
- How will we do it?
- When does this take effect?

## Consequences
[Describe what happens after this decision]

### Positive Consequences
- Benefit 1: [Explanation]
- Benefit 2: [Explanation]

### Negative Consequences
- Drawback 1: [Explanation]
- Drawback 2: [Explanation]

### Mitigations
[How we'll handle the negative consequences]

## Alternatives Considered
1. **Alternative A** - [Brief description]
   - Rejected because: [Rationale]

2. **Alternative B** - [Brief description]
   - Rejected because: [Rationale]

3. **Option We Chose** ✅ [This decision]
   - Selected because: [Why this is best]

## Related ADRs
- ADR-001: [Title of related decision]
- ADR-002: [Title of related decision]

## References
- [Link to documentation]
- [Link to issue/PR]
- [Link to relevant code]
```

## When to Create an ADR

### YES - Create ADR For:

✅ **Major Technology Choices**
- Switching database (PostgreSQL → MongoDB)
- Adopting new framework (FastAPI chosen for backend)
- Infrastructure decision (Redis for caching)
- Language/Runtime choice (Python 3.10+)

✅ **Architectural Changes**
- Splitting monolithe into services
- Introducing new layer (GraphQL added)
- New communication pattern (pub/sub vs REST)
- Deployment strategy change

✅ **Significant Pattern Introductions**
- First use of Event Sourcing
- Introducing CQRS pattern
- GraphQL schema design philosophy
- API versioning strategy

✅ **Infrastructure Decisions**
- Database sharding strategy
- Caching architecture
- Message queue adoption
- Monitoring/logging approach

### NO - Don't Create ADR For:

❌ **Bug Fixes**
- Not architectural
- Fix is temporary
- No strategic impact

❌ **Feature Implementation**
- Covered by user stories
- Not system-level decision
- Reverse easily

❌ **Minor Refactoring**
- Code reorganization
- Performance tweaks
- Small optimizations

❌ **Development Process**
- Code review guidelines
- Pull request workflow
- Testing procedures
- (These go in CONTRIBUTING.md)

## ADR Lifecycle

```
     ┌────────────┐
     │ Proposed   │  New decision under discussion
     └──────┬─────┘
            │ Discussion complete
     ┌──────v─────┐
     │ Accepted   │  Decision made, implementation starts
     └──────┬─────┘
            │
       ┌────┴────────────┐
       │                 │
       v                 v
  ┌────────────┐   ┌─────────────────┐
  │ Deprecated │   │ Superseded by   │
  │            │   │ ADR-YYYY        │
  └────────────┘   └─────────────────┘
  Still valid but   Replaced by newer
  no new use        decision
```

## Real-World Examples

### Example 1: GraphQL Adoption

```markdown
# ADR-0001: Use GraphQL for API Layer

**Date:** 2025-01-15
**Status:** Accepted
**Author:** Architecture Team

## Context
Current REST API requires 3-4 requests to get related data. Frontend developers
report over-fetching (unnecessary fields) and under-fetching (missing data).
Mobile clients suffer from data bloat.

Investigated two approaches:
- Extend REST with HAL/HATEOAS (standardized but verbose)
- Adopt GraphQL (newer, powerful, learning curve)

## Decision
Adopt GraphQL (via Strawberry) for all new endpoints. Legacy REST endpoints
remain but are deprecated. Migration: 1 endpoint/sprint.

## Consequences

### Positive
- Clients request exactly what they need (no over-fetching)
- Complex queries solved in one request (no under-fetching)
- Strong schema enables IDE autocompletion
- Backend dataloader prevents N+1 queries
- Introspection enables API exploration

### Negative
- Team learning curve on GraphQL concepts
- Complexity: mutations, subscriptions, schema design
- Caching more complex (HTTP caching doesn't work)
- Query cost risks (unbounded queries)

### Mitigations
- Team GraphQL training sprint (1 week)
- Query depth/complexity limits enforced
- GraphQL monitoring dashboard
- Clear mutation patterns in style guide

## Alternatives Considered

1. **REST with HAL** - Rejected
   - Addresses some issues but still verbose
   - No IDE support

2. **gRPC** - Rejected
   - Overkill for browser clients
   - Requires code generation
   - Harder debugging

3. **GraphQL** ✅ Selected
   - Solves over/under-fetching
   - Strong ecosystem (Strawberry, Apollo)
   - Future-proof design

## References
- Strawberry GraphQL docs: https://strawberry.rocks/
- Apollo Client docs: https://www.apollographql.com/docs/react/
- PR #456: Initial GraphQL schema
```

### Example 2: Memory Layer Architecture

```markdown
# ADR-0002: L0-L5 Memory Layering System

**Date:** 2025-02-01
**Status:** Accepted
**Author:** AGI Team

## Context
Need to scale memory from 10K to 10M+ memories. Monolithic PostgreSQL
becomes bottleneck. Flat memory access is too slow for working context.

Trade-off: Access speed vs Storage cost vs Query flexibility.

Analyzed three models:
- Single PostgreSQL (current): Simple, doesn't scale
- Flat Redis cache: Fast but tiny, expensive
- Layered L0-L5: Complex but scalable to billions

## Decision
Implement 5-layer memory system:
- L0: In-process cache (current thinking only)
- L1: Redis (session working memory, TTL)
- L2: PostgreSQL (conversation history)
- L3-L5: Neo4j + embeddings (semantic graph, long-term)

## Consequences

### Positive
- Scales from 10K to billions of memories
- Working memory ultra-fast (in-process)
- Semantic search via Neo4j embeddings
- Separate concerns by layer
- Can optimize each layer independently

### Negative
- Complexity: Synchronization between layers
- Consistency: Data might diverge (L0 vs L2 vs L3)
- Maintenance: Monitor 3 databases
- Cost: 3 database services vs 1
- Development time: Implementation complex

### Mitigations
- Consolidation async job: L2→L3 moves
- TTLs prevent stale data (L1 expires, L0 clears)
- Event sourcing: All changes logged
- Integration tests verify consistency

## Alternatives Considered

1. **Single PostgreSQL** - Rejected
   - Works now but hits wall at 1M memories
   - Queries slow at scale
   - Can't semantic search

2. **Flat Redis** - Rejected
   - Fast but expensive (RAM costs)
   - Loses memory on restart
   - No semantic search

3. **L0-L5 Layers** ✅ Selected
   - Scales indefinitely
   - Each layer optimized for use case
   - Best of all worlds

## References
- System design: /docs/memory-architecture.md
- L0 implementation: /backend/core/l0_cache.py
- L1 (Redis) implementation: /backend/services/redis_client.py
- L2 (PostgreSQL) implementation: /backend/models/memory_model.py
- L3 (Neo4j) implementation: /backend/agents/consolidation_agent.py
- Tests: /backend/tests/test_memory_layers.py
```

## ADR Best Practices

### Writing Guidelines

1. **Be Concise**
   - Short title (5-7 words)
   - Context in <100 words
   - Decision in 1-2 sentences

2. **Be Specific**
   - Exact technology name, version
   - Concrete consequences, not vague
   - Real metrics, not "probably faster"

3. **Be Honest**
   - Include real drawbacks, not just benefits
   - Acknowledge limitations
   - State uncertainty where it exists

4. **Be Future-Focused**
   - How will maintainers understand this?
   - What assumptions might change?
   - When should this be revisited?

### Review Process

Before marking as "Accepted":

- [ ] Problem clearly stated (context)
- [ ] Decision unambiguous
- [ ] Consequences realistic
- [ ] Trade-offs acknowledged
- [ ] Alternatives genuinely considered
- [ ] References valid
- [ ] 2+ team members agree

### Maintenance

**Update ADR When:**
- Decision implementation changes
- New consequences discovered
- Better alternative found
- Decision becomes obsolete

**Mark Superseded When:**
- New ADR replaces this one
- Technology changes fundamentally
- Constraints no longer apply

## ADR Repository Organization

```
docs/adr/
├── 0001-graphql-adoption.md
├── 0002-memory-layering.md
├── 0003-authentication-strategy.md
├── README.md                    # ADR index and process
└── TEMPLATE.md                  # Copy for new ADRs
```

**README tracks:**
- All ADR titles and status
- Quick reference (which ADR for what)
- Process for proposing new ADRs

## Common ADR Mistakes

❌ **Decision already made before ADR**
- ADR should inform decision, not justify it
- Fix: Write ADR before implementation

❌ **Vague consequences**
- "Performance will improve" (by how much?)
- Fix: Quantify or describe specifically

❌ **Ignoring alternatives**
- "Best option available" (why?)
- Fix: Compare options explicitly

❌ **Too long**
- Should be 1-2 pages, not 10
- Fix: Move details to separate docs

❌ **Never reviewed or revisited**
- ADR becomes stale
- Fix: Annual ADR audit, mark superseded

## References
- ADR format by Michael Nygard
- Y Combinator architecture decisions
- Example ADRs: Apache, Kubernetes
- Tool: adr-tools GitHub repo
