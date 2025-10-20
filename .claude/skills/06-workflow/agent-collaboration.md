---
title: Agent Collaboration & Role Clarity
category: workflow
priority: high
updated: 2025-10-20
version: 1.0
agent: ask
---

# Agent Collaboration & Role Clarity

## Core Principle: Clear Boundaries

Each agent has **ONE clear responsibility**. Agents do NOT cross boundaries.

```markdown
❌ CHAOS: Agents stepping on each other
Agent1 scans backend
Agent2 also scans backend (duplicate work)
Agent3 tries to refactor (conflict with Agent1)
= Confusion, waste, conflicts

✅ CLARITY: Each agent has exclusive zone
Agent1: Scan backend/services/
Agent2: Scan backend/api/
Agent3: Scan backend/models/
= No overlap, efficient, parallel
```

## The 8 Specialist Agents

### 1. ask (Code Exploration)

**Exclusive Responsibility:**
- Explore internal codebase only
- Find where logic lives
- Identify duplicates
- Map architecture

**Input Examples:**
- "Find all memory-related classes"
- "Scan backend/services/ for patterns"
- "Where is authentication implemented?"

**Output:**
- Structured list of findings
- File locations
- Code structure analysis

**NOT their job:**
- External research (use research)
- Deciding architecture (use architect)
- Implementing code (use code)
- Testing (use debug)

**Tool Constraints:**
```python
✅ Can use: Glob, Grep, Read
❌ Cannot use: Write, Edit, Bash (execute)
```

### 2. research (External Context)

**Exclusive Responsibility:**
- Research external libraries
- Find best practices
- Fetch documentation
- Explore patterns

**Input Examples:**
- "Find GraphQL Subscription best practices"
- "Document how exa-mcp-server works"
- "What's the latest in React 19?"

**Output:**
- Recommended patterns
- Code examples
- Best practices
- Framework documentation

**NOT their job:**
- Exploring internal codebase (use ask)
- Deciding design (use architect)
- Implementation (use code)

**Tool Constraints:**
```python
✅ Can use: research MCPs (exa, fetch, context7)
❌ Cannot use: Glob, Write, Edit, Bash
```

### 3. architect (System Design)

**Exclusive Responsibility:**
- Design new features
- Create architecture diagrams
- Write ADRs (Architecture Decision Records)
- Plan refactoring phases
- Compare options and tradeoffs

**Input Examples:**
- "Design real-time notification system"
- "Plan refactoring of memory service"
- "Should we use WebSocket or SSE?"

**Output:**
- Architecture diagrams
- Design patterns
- Phase breakdown
- Recommendations

**NOT their job:**
- Small bug fixes (skip directly to code)
- Implementation details (use code)
- Research (use research)

**Tool Constraints:**
```python
✅ Can use: Think deeply, design, propose
❌ Cannot use: Glob, Grep, Write, Edit
```

### 4. code (Backend Implementation)

**Exclusive Responsibility:**
- Implement backend features
- Create FastAPI endpoints
- Write GraphQL mutations/queries
- Database migrations
- Service business logic
- Python configuration/scripts

**Input Examples:**
- "Implement memory consolidation endpoint"
- "Create GraphQL mutation for storing embeddings"
- "Write migration for neurotransmitter table"

**Output:**
- Python code
- Database schemas
- Configuration
- Integration points

**NOT their job:**
- React components (use frontend)
- Infrastructure setup (use sre)
- Testing only (use debug for testing, use code for implementation)

**Tool Constraints:**
```python
✅ Can use: Write, Edit, Bash (limited)
❌ Cannot use: Modify React/TS files, infra config
```

**File Scope:**
```python
✅ backend/
✅ cortex/ (Python scripts)
✅ backend/migrations/
✅ backend/tests/ (own implementation)

❌ frontend/ (use frontend agent)
❌ Infrastructure files
```

### 5. frontend (React Implementation)

**Exclusive Responsibility:**
- Create React components
- Implement TypeScript
- Build with shadcn/ui
- Apollo Client integration
- Styling with Tailwind
- Custom React hooks

**Input Examples:**
- "Create NotificationCenter component"
- "Implement useMemoryQuery hook"
- "Build settings page with form"

**Output:**
- TSX components
- Custom hooks
- Styled layouts
- Apollo integrations

**NOT their job:**
- Backend API (use code)
- Infrastructure (use sre)
- Database (use code)

**Tool Constraints:**
```python
✅ Can use: Write, Edit, Bash (npm commands only)
❌ Cannot use: Backend Python, Database operations
```

**File Scope:**
```python
✅ frontend/src/components/
✅ frontend/src/pages/
✅ frontend/src/hooks/
✅ frontend/src/lib/

❌ backend/ (use code)
❌ Migration files
❌ Infrastructure
```

### 6. debug (Testing & Validation)

**Exclusive Responsibility:**
- Write tests (pytest, integration)
- Find bugs
- Validate implementations
- E2E testing
- Bug fixing
- Performance testing

**Input Examples:**
- "Write tests for memory consolidation"
- "Debug why notification isn't firing"
- "Validate end-to-end flow"

**Output:**
- Test code
- Bug reports
- Test results
- Validation results

**NOT their job:**
- Creating new features (use code/frontend)
- Architecture (use architect)
- Documentation (use docs)

**Tool Constraints:**
```python
✅ Can use: Write (tests), Bash (pytest, npm test)
❌ Cannot use: Edit production code without asking
```

### 7. docs (Documentation)

**Exclusive Responsibility:**
- README documentation
- API documentation
- Architecture diagrams
- CHANGELOG
- Deployment guides
- User guides

**Input Examples:**
- "Document notification system"
- "Create API documentation"
- "Generate architecture diagram"

**Output:**
- Markdown documentation
- Mermaid diagrams
- API specs
- Guides

**NOT their job:**
- Code comments (done by developers)
- Inline documentation (done by code agent)
- Implementation (use code/frontend)

**Tool Constraints:**
```python
✅ Can use: Write (markdown/docs only)
❌ Cannot use: Modify code files
```

### 8. sre (Infrastructure & Monitoring)

**Exclusive Responsibility:**
- Health checks (PostgreSQL, Neo4j, Redis)
- Monitoring setup
- Cost analysis
- Performance optimization
- Infrastructure troubleshooting
- Scaling recommendations

**Input Examples:**
- "Check system health"
- "Analyze slow queries"
- "Optimize Redis memory usage"

**Output:**
- Health reports
- Performance analysis
- Recommendations
- Cost reports

**NOT their job:**
- Application features (use code/frontend)
- Architectural design (use architect)
- Code implementation (use code)

**Tool Constraints:**
```python
✅ Can use: Limited Bash (health checks, logs)
❌ Cannot use: Change critical infrastructure
```

## Collaboration Rules (Non-Negotiable)

### Rule 1: Never Cross Domains

```python
❌ WRONG: ask agent researches external libraries
Task(ask, "Find best GraphQL library")
→ That's research agent's job

✅ RIGHT: Use correct agent
Task(research, "Find best GraphQL library")
```

### Rule 2: Never Call Other Agents

```python
❌ WRONG: Agent calls another agent
Agent1: Task(ask, "Explore backend")
  # Inside agent1 response:
  Task(research, "Research patterns")  # CIRCULAR!

✅ RIGHT: Orchestrator (ME) calls all agents
ME: Task(ask, "Explore backend")
ME: Task(research, "Research patterns")
ME: Aggregate results
```

### Rule 3: Sequential Phases, Parallel Agents

```python
❌ WRONG: Run all phases simultaneously
Task(code, "Implement feature")  # Needs design first!
Task(architect, "Design feature")
Task(debug, "Test feature")
→ Code without design = wasted work

✅ RIGHT: Phases in order, agents within phase parallel
Phase 1 (ask): Task(ask, X), Task(ask, Y), Task(ask, Z) [parallel]
Phase 2 (architect): Task(architect, ...) [waits for phase 1]
Phase 3 (code): Task(code, X), Task(code, Y) [parallel, waits for phase 2]
Phase 4 (debug): Task(debug, X), Task(debug, Y) [parallel, waits for phase 3]
```

### Rule 4: Output Formats Must Be Structured

```python
❌ WRONG: Free-form text output
Agent: "I found some stuff and here's what..."

✅ RIGHT: Structured output (JSON, lists)
Agent: {findings: [{file, type, detail}], status: "complete"}
```

### Rule 5: Deadlines Enforce Discipline

```python
❌ WRONG: No deadline
Task(ask, "Analyze backend")
→ Agent takes unlimited time

✅ RIGHT: Strict deadline
Task(ask, "Analyze backend\nDEADLINE: 20s\nPARTIAL OK")
→ Agent works efficiently, returns what they have
```

## Coordination Pattern: Feature Implementation

### Example: Build Notification System

```
PHASE 1 - UNDERSTANDING (Parallel)
│
├─ Agent ask:
│  "Find notification-related code"
│  Scope: backend/
│
├─ Agent ask:
│  "Find real-time patterns"
│  Scope: frontend/
│
└─ Agent ask:
   "Check database schema"
   Scope: migrations/

↓ [ME: Aggregate findings]

PHASE 2 - RESEARCH (Parallel)
│
├─ Agent research:
│  "GraphQL Subscriptions patterns"
│
├─ Agent research:
│  "Apollo Client real-time hooks"
│
└─ Agent research:
   "PostgreSQL LISTEN/NOTIFY"

↓ [ME: Aggregate research]

PHASE 3 - ARCHITECTURE (Single)
│
└─ Agent architect:
   "Design notification system"
   Input: All phase 1 & 2 findings

↓ [ME: Validate design]

PHASE 4 - IMPLEMENTATION (Parallel)
│
├─ Agent code:
│  "Backend: GraphQL subscription"
│  Scope: backend/api/schema.py
│
├─ Agent code:
│  "Backend: Notification service"
│  Scope: backend/services/
│
├─ Agent code:
│  "Database: Migration"
│  Scope: migrations/
│
└─ Agent frontend:
   "Frontend: Notification UI"
   Scope: frontend/src/components/

↓ [ME: Aggregate code]

PHASE 5 - VALIDATION (Parallel)
│
├─ Agent debug:
│  "Test backend subscription"
│
├─ Agent debug:
│  "Test frontend hook"
│
└─ Agent debug:
   "E2E test notification flow"

↓ [ME: Verify all pass]

PHASE 6 - DOCUMENTATION (Single)
│
└─ Agent docs:
   "Document notification system"

✅ COMPLETE: Feature shipped end-to-end
```

## When Agents Need to Wait

### Dependency Chain
```
ask (explore) → research (context) → architect (design)
                                        ↓
                                      code (implement)
                                        ↓
                                      debug (validate)
                                        ↓
                                      docs (document)
```

### Independence Within Phase
```
PHASE 4: code (backend implementation)
  ├─ code agent 1: API endpoint
  ├─ code agent 2: Service logic  } Can run parallel
  ├─ code agent 3: Database migration
  └─ code agent 4: Config update
```

## Handling Conflicts

### Conflict: Code Agent vs Frontend Agent (Same Feature)

**Solution: Split file ownership**
```python
✅ CORRECT:
- code agent: backend/api/schema.py (GraphQL mutation)
- frontend agent: frontend/src/components/notif.tsx (component)

❌ WRONG:
- Both agents editing same file simultaneously
→ Conflicts, overwrites, chaos
```

### Conflict: Ask Agent Finds Duplicate Code

**Solution: Ask reports, Code agent refactors**
```python
ask: "Found duplicate consolidation logic in X.py and Y.py"
↓
ME: "OK, let's consolidate"
↓
code: Refactor into shared service, delete duplicates
↓
debug: Verify tests still pass
```

### Conflict: Architect Suggests Design, Code Can't Implement

**Solution: Async feedback loop**
```python
architect: "Recommends WebSocket + Redis Pub/Sub"
↓
ME: "Check if feasible"
↓
code: "Redis add requires infrastructure setup"
↓
ME: "Need to adjust design or add infrastructure work"
↓
architect: "Redesign without Redis if simpler"
```

## Preventing Coordination Disasters

### Anti-Pattern 1: Call Agent Multiple Times Without Coordination

```python
❌ WRONG: Redundant work
Task(ask, "Explore backend")
Task(ask, "Explore backend again")  # Duplicate!
→ Wasted API calls, duplicate results

✅ RIGHT: Strategic batching
Task(ask, [
  "Scan services/",
  "Scan api/",
  "Scan models/"
])
→ One agent, comprehensive results
```

### Anti-Pattern 2: Agent Bottleneck

```python
❌ WRONG: Single agent doing everything
Task(ask, "Do everything for feature X")
→ Takes 10 min, blocks other work

✅ RIGHT: Parallelize specialization
Task(ask, "Explore")
Task(research, "Research")
Task(architect, "Design")
Task(code, "Backend")
Task(frontend, "Frontend")
Task(debug, "Test")
→ Run in phases, agents work simultaneously within phase
```

### Anti-Pattern 3: No Clear Output Format

```python
❌ WRONG: Free-form response
Agent: "I found some stuff related to memory in several places"

✅ RIGHT: Structured output
Agent: {
  memory_files: [...],
  classes: [...],
  methods: [...],
  coverage: "80%"
}
```

## Best Practices Checklist

**Before Assigning Tasks:**
- [ ] Agent has clear, exclusive responsibility?
- [ ] Task is within agent's domain?
- [ ] Deadline is realistic?
- [ ] Output format is specified?
- [ ] No circular dependencies with other agents?
- [ ] Parallel tasks don't conflict (same files)?
- [ ] Agent has access to required tools?

**During Execution:**
- [ ] Agents running in correct phase order?
- [ ] Multiple agents NOT working on same file?
- [ ] Deadlines being monitored?
- [ ] Partial results acceptable if timeout?

**After Execution:**
- [ ] Results aggregated correctly?
- [ ] No conflicting outputs?
- [ ] Ready for next phase?
- [ ] Documentation of coordination captured?

---

**Remember:** Clear roles + No overlap = Smooth collaboration.
