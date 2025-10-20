# Architecture Skills Collection

Professional architecture framework for AGI system design, decision-making, and documentation.

## Skills Overview

### 1. **Project Structure & Organization** (`project-structure.md`)
- Scanning for duplicates (Glob/Grep patterns)
- File organization standards
- Naming conventions (backend Python, frontend TypeScript)
- Common issues and fixes
- Implementation checklist

**Use when:**
- Creating new files or modules
- Refactoring codebase structure
- Onboarding new developers
- Detecting duplicate code

---

### 2. **Architecture Thinking Framework** (`architecture-thinking.md`)
- Layered architecture patterns (backend routes → services → data)
- System design patterns (memory L0-L5, agent system)
- Design patterns (repository, factory, singleton, strategy, observer)
- Anti-patterns to avoid (God objects, circular dependencies, N+1 queries)
- Complex system example (memory consolidation)

**Use when:**
- Designing new features
- Thinking about system structure
- Evaluating design patterns
- Understanding existing architecture

---

### 3. **ADR - Architecture Decision Records** (`adr-decisions.md`)
- ADR template and format
- When to create ADRs (yes) and when not to (no)
- ADR lifecycle (Proposed → Accepted → Deprecated)
- Real-world examples (GraphQL adoption, memory layering)
- Best practices for writing ADRs
- Review process and maintenance

**Use when:**
- Making significant architectural decisions
- Documenting technology choices
- Recording trade-off analysis
- Preserving knowledge for future developers

---

### 4. **Trade-Offs Analysis Framework** (`trade-offs-analysis.md`)
- Performance vs Maintainability (when to choose each)
- Normalization vs Denormalization (database design)
- Monolith vs Microservices (scaling decisions)
- Consistency vs Availability (CAP theorem)
- Trade-off decision matrix
- Analysis process (identify → measure → evaluate → choose)

**Use when:**
- Choosing between architectural options
- Evaluating performance needs
- Analyzing scaling requirements
- Making informed trade-off decisions

---

## Quick Reference: Which Skill?

| Situation | Skill |
|-----------|-------|
| "Should I create a new file?" | Project Structure |
| "Where does this code go?" | Project Structure |
| "Why does the system work this way?" | Architecture Thinking |
| "How should we design this feature?" | Architecture Thinking |
| "Should we use GraphQL or REST?" | ADR + Trade-Offs |
| "Why was this decision made?" | ADR |
| "Speed vs Simplicity - which matters?" | Trade-Offs Analysis |
| "Monolith or Microservices?" | Trade-Offs Analysis |

---

## Architecture Principles

### Core Values
1. **Clarity** - Code should be understandable
2. **Scalability** - System should grow without collapse
3. **Maintainability** - Changes should be safe and easy
4. **Performance** - Critical paths should be fast

### Decision Framework
```
New Decision?
├─ Is it major? (YES) → Create ADR
├─ Any trade-offs? (YES) → Analyze trade-offs
├─ Need new files? (YES) → Follow structure guide
└─ Done? → Document in ADR + implement
```

---

## Related Documentation

- Backend Code Skills: `/skills/01-backend/`
- Frontend Code Skills: `/skills/02-frameworks/`
- Database Design: `/skills/03-databases/` (if exists)
- AGI System Architecture: `/docs/architecture/`
- Memory System: `/docs/memory-architecture.md`

---

## Implementation Examples

### Example: Adding Authentication Feature

1. **Project Structure**: Where should auth code go?
   - Routes: `backend/api/rest/auth.py`
   - Service: `backend/services/auth_service.py`
   - Model: `backend/models/user_model.py`
   - Tests: `backend/tests/services/test_auth_service.py`

2. **Architecture Thinking**: How should layers interact?
   - API layer: Handle requests, call service
   - Service layer: Orchestrate auth logic
   - Data layer: Query/update user
   - Utils: Hashing, token generation

3. **ADR**: Document the decision
   - Why JWT instead of sessions?
   - Trade-offs analyzed?
   - Alternatives considered?

4. **Trade-Offs**: Evaluate options
   - JWT vs Sessions: Stateless scalability vs simplicity?
   - Database vs cache: Consistency vs speed?

---

## Maintenance

**Review quarterly:**
- [ ] ADRs still valid?
- [ ] Project structure followed?
- [ ] New patterns emerged?
- [ ] Anti-patterns detected?

**Update when:**
- [ ] Architecture changes significantly
- [ ] New patterns introduced
- [ ] Trade-off evaluation shows different choice
- [ ] Team learns new insight

---

## Learning Path

**Beginner:**
1. Start with Project Structure (understand where things go)
2. Read Architecture Thinking (understand why)

**Intermediate:**
3. Learn ADR format (document decisions)
4. Study trade-offs (make informed choices)

**Advanced:**
5. Write ADRs for your decisions
6. Analyze new features through trade-off lens
7. Mentor others on architecture

---

**Version:** 1.0
**Last Updated:** 2025-10-20
**Maintained By:** Architecture Team
