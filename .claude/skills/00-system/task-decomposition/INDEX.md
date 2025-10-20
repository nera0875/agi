# Task Decomposition Skill - Complete Navigation Index

## Overview

This skill teaches **CEO-level task orchestration**: breaking complex work into micro-tasks, parallelizing with strict deadlines, and aggregating results.

**Core formula:** Decompose → Partition → Parallelize (N agents) → Aggregate = **5-20x speedup**

**Key insight:** 70% useful in 30s beats 100% useful in 5 minutes

---

## Files in This Skill

### 1. **README.md** - The Main Guide (START HERE)

**What it covers:**
- Overview + core principles
- When to use task decomposition
- Key principles (Independence, Scope Isolation, Deadline Discipline, Ultra-Precise Prompts)
- Decomposition strategy (5-step process)
- Timeout management (6 rules)
- Aggregation strategy
- Anti-patterns to avoid
- Full working examples

**When to read:**
- First time learning decomposition
- Need deep understanding
- Understanding theory + practice

**Key sections:**
- Principle 1: Independence = Parallelizable
- Principle 2: Scope Isolation
- Principle 3: Deadline Discipline (CRITICAL)
- Principle 4: Ultra-Precise Prompts
- Decomposition Patterns (Pattern 1-4)
- Timeout Management (Rule 1-6)

---

### 2. **instructions.md** - Deep Technical Reference

**What it covers:**
- Part 1: When to decompose (decision tree)
- Part 2: Decomposition rules (STRICT)
- Part 3: Prompt engineering (6-part template)
- Part 3b: Scope ultra-précis (anti-dérive)
- Part 4: Timeout & partial results (STRICT DEADLINES)
- Part 5: Decomposition heuristics
- Part 6: Aggregation patterns
- Part 7: Common scenarios
- Part 8: Anti-patterns & pitfalls
- Part 9: Complete checklist
- Part 10: Real-world examples (DEADLINE DISCIPLINE)

**When to read:**
- Deep dive on specific topic
- Need comprehensive technical reference
- Building production decompositions

**Key sections:**
- Part 3b: Scope ULTRA-PRÉCIS (most critical for quality)
- Part 4: Timeout & Partial Results (MANDATORY deadlines)
- Part 10: DEADLINE DISCIPLINE (real-world examples)

---

### 3. **DEADLINE-REFERENCE.md** - Quick Copy-Paste Cheatsheet

**What it covers:**
- CRITICAL RULE (every task needs deadline)
- Timeout by task type (production-tested table)
- Mandatory prompt template
- 70% rule (accept partial)
- Anti-patterns (avoid these)
- CEO success formula
- 3 full examples (copy-paste ready)
- Key takeaways

**When to use:**
- Need timeout for specific task
- Writing agent prompts
- Quick reference when in a hurry
- Copy-paste templates

**Best for:**
- New tasks (1-2 min lookup)
- Remembering deadline for "scan 20 files" (20s)
- Template for agent prompts

---

### 4. **CHECKLISTS.md** - Validation & Quality Assurance

**What it covers:**
- Checklist 1: Before decomposing (is it worth it?)
- Checklist 2: Planning decomposition
- Checklist 3: Prompt writing (MOST CRITICAL)
- Checklist 4: Execution setup
- Checklist 5: After execution
- DEADLINE checklist (MANDATORY)
- Common mistakes (5 scenarios)
- Quick validation script
- Timeline expectations
- Success indicators
- Template cheatsheet

**When to use:**
- Before launching agents
- Quality assurance
- Debugging why decomposition failed
- Learning from mistakes

**Best for:**
- Validation before execution
- Post-mortem analysis
- Teaching others

---

### 5. **This file: INDEX.md** - Navigation

Quick reference to all files and what they contain.

---

## Quick Start (5 minutes)

### For the Impatient

1. **Read this section** (2 min)
2. **Read DEADLINE-REFERENCE.md** (2 min)
3. **Run Checklist 3: Prompt Writing** (1 min)
4. **Launch your first decomposed task**

### For the Thorough

1. Read README.md (10 min)
2. Skim instructions.md Part 1-3 (10 min)
3. Study DEADLINE-REFERENCE.md (5 min)
4. Run through CHECKLISTS.md before execution (5 min)
5. Execute and learn

---

## Navigation by Topic

### Topic: "I need to decompose my first task"

1. Start: README.md → **Decomposition Strategy** section
2. Deep dive: instructions.md → **Part 2: Decomposition Rules**
3. Quick ref: DEADLINE-REFERENCE.md → **Example 1/2/3**
4. Validate: CHECKLISTS.md → **Checklist 1 + 2**

### Topic: "How do I set deadlines?"

1. Quick: DEADLINE-REFERENCE.md → **Timeout by Task Type**
2. Why: README.md → **Principle 3: Deadline Discipline**
3. Examples: DEADLINE-REFERENCE.md → **Real-World Examples**
4. Validate: CHECKLISTS.md → **DEADLINE Checklist**

### Topic: "Why is my decomposition failing?"

1. Common errors: CHECKLISTS.md → **Common Mistakes**
2. Anti-patterns: README.md → **Anti-Patterns to Avoid**
3. Deep dive: instructions.md → **Part 8: Anti-patterns & Pitfalls**
4. Replan: CHECKLISTS.md → **Checklist 1-2**

### Topic: "How do I write better prompts?"

1. Template: DEADLINE-REFERENCE.md → **Mandatory Prompt Template**
2. Deep dive: instructions.md → **Part 3: Prompt Engineering**
3. Examples: instructions.md → **Part 3b: Scope Ultra-Précis**
4. Validate: CHECKLISTS.md → **Checklist 3: Prompt Writing**

### Topic: "How do I combine agent results?"

1. Overview: README.md → **Aggregation Strategy**
2. Code: instructions.md → **Part 6: Aggregation Patterns**
3. Real examples: README.md → **Examples**
4. Validate: CHECKLISTS.md → **Checklist 5: After Execution**

### Topic: "I'm confused about scope"

1. Principle: README.md → **Principle 2: Scope Isolation**
2. Strategies: instructions.md → **Part 3b: Strategies for Ultra-Precise Scopes**
3. Example: instructions.md → **Example: Dividing Gros Travaux (67 files)**
4. Checklist: CHECKLISTS.md → **Mistake 1: Overlapping Scopes**

---

## Key Concepts (Understand These)

### Concept 1: DEADLINE is Mandatory

**Rule:** Every task to agents MUST have `DEADLINE: X seconds MAX`

**Why:** Agents without deadlines perfectionism themselves into 5-10 minute tasks.

**Files:**
- See: DEADLINE-REFERENCE.md → **CRITICAL RULE**
- Why: README.md → **Principle 3: Deadline Discipline**
- Examples: instructions.md → **Part 10: DEADLINE DISCIPLINE**

### Concept 2: 70% Rule (Pragmatism)

**Rule:** 70% complete in 30s > 100% complete in 5 min

**Why:** CEO pragmatism beats perfectionism. 70% is actionable.

**Files:**
- See: DEADLINE-REFERENCE.md → **The 70% Rule**
- Why: instructions.md → **Part 4: Handling Timeouts**
- Examples: CHECKLISTS.md → **Timeline Expectations**

### Concept 3: Parallelization

**Rule:** If task > 30s and splittable → decompose into N agents in parallel

**Why:** 5 agents × 20s = 20s total (vs 1 agent × 5 min = 5 min solo)

**Files:**
- See: README.md → **Decomposition Strategy**
- Deep: instructions.md → **Part 2: Decomposition Rules**
- Heuristic: instructions.md → **Part 5: Task Size Heuristics**

### Concept 4: Scope Isolation (No Overlap)

**Rule:** Each agent gets exclusive, non-overlapping scope

**Why:** Overlapping scopes = wasted work + inconsistent results

**Files:**
- See: README.md → **Principle 2: Scope Isolation**
- Deep: instructions.md → **Part 3b: Scope Ultra-Précis**
- Examples: CHECKLISTS.md → **Mistake 1: Overlapping Scopes**

### Concept 5: Independence (No Dependencies)

**Rule:** Independent tasks parallelizable, dependent tasks sequential

**Why:** Agent A's output is input for Agent B = sequential requirement

**Files:**
- See: README.md → **Principle 1: Independence**
- Decision tree: instructions.md → **Part 5: When to Parallelize**
- Mistakes: CHECKLISTS.md → **Mistake 2: Dependent Tasks**

---

## Common Questions

### Q: "How many agents should I launch?"

**A:** See instructions.md → Part 5: **Task Size Heuristics**

Heuristic:
- Read-only scans: 5-10 agents
- Data processing: 3-5 agents
- Implementation: 2-3 agents
- Architecture: 1 agent

### Q: "What's the right deadline?"

**A:** See DEADLINE-REFERENCE.md → **Timeout by Task Type**

Formula: `Deadline = (Expected_Duration × 1.5) + 5s buffer`

### Q: "Is partial results OK?"

**A:** Yes! See DEADLINE-REFERENCE.md → **The 70% Rule**

70%+ completion is acceptable and saves 4.5 min waiting.

### Q: "My task has dependencies - can I parallelize?"

**A:** Partially. See instructions.md → Part 1 (decision tree) + Part 2 (Rule 1)

Decompose into phases:
- Phase 1: Independent tasks (parallel)
- Phase 2: Dependent on Phase 1 (wait, then parallel)
- Phase 3: Dependent on Phase 2 (wait, then parallel)

### Q: "Why did my decomposition fail?"

**A:** See CHECKLISTS.md → **Common Mistakes**

Top 5 reasons:
1. Overlapping scopes
2. Dependent tasks parallelized
3. No deadline
4. Vague scope
5. Perfectionism language

---

## Recommended Reading Order

### Path 1: Quick Start (10 min)
1. This INDEX.md
2. DEADLINE-REFERENCE.md
3. Go decompose!

### Path 2: Thorough Learning (30 min)
1. README.md (main guide)
2. DEADLINE-REFERENCE.md (quick ref)
3. instructions.md Part 1-3 (understanding)
4. CHECKLISTS.md (validation)
5. Go decompose!

### Path 3: Deep Mastery (60 min)
1. README.md (cover to cover)
2. instructions.md (cover to cover)
3. DEADLINE-REFERENCE.md (internalize patterns)
4. CHECKLISTS.md (memorize checklists)
5. Experiment with real decompositions

---

## Files Quick Reference

| File | Length | Purpose | When to Use |
|------|--------|---------|------------|
| README.md | ~600 lines | Main guide + theory | Learning |
| instructions.md | ~850 lines | Technical deep dive | Reference + patterns |
| DEADLINE-REFERENCE.md | ~300 lines | Quick copy-paste | During decomposition |
| CHECKLISTS.md | ~400 lines | Validation | Before/after execution |
| INDEX.md (this) | ~400 lines | Navigation | Getting oriented |

---

## Key Takeaways

1. **DEADLINE is mandatory** - Every task needs `DEADLINE: X seconds MAX`
2. **Parallelize ruthlessly** - If can split → split (5-20x speedup)
3. **Accept 70%** - Partial results are OK, embrace pragmatism
4. **Scope ultra-precise** - "backend" is vague, "backend/services/[a-e]*.py" is precise
5. **Aggregate quickly** - Your job is CEO, not executor

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10-20 | Initial release + DEADLINE DISCIPLINE from CLAUDE.md |

---

**Skill:** Task Decomposition (System - Orchestration)
**Audience:** CEO/Director Mode (Advanced)
**Status:** Complete + Production Ready
**Next:** Execute your first decomposed task and learn!
