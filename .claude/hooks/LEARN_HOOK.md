# Learn Hook - Auto-Skill Proposal System

## Overview

The **Learn Hook** automatically detects repeated patterns in agent executions and proposes optimized reusable skills.

**Purpose:** Enable continuous improvement by identifying common workflows that could be automated as dedicated skills.

## How It Works

### 1. Pattern Detection

Learn hook monitors `.claude/hooks/.trigger_log` which records all agent triggers:

```json
{
  "timestamp": "2025-10-20T16:30:00",
  "file": "backend/api/schema.py",
  "agent": "debug",
  "reason": "GraphQL schema modified - validate queries/mutations"
}
```

Each entry represents:
- **timestamp**: When agent was triggered
- **file**: Which file caused the trigger
- **agent**: Which agent was invoked
- **reason**: Why the agent was triggered

### 2. Pattern Analysis

Counts occurrences of:
- **(file, agent)** pairs
- **(reason, agent)** pairs

Over last 7 days.

### 3. Threshold & Prioritization

- **Threshold:** >= 5 occurrences
- **Priority:**
  - `HIGH` if count >= 10
  - `MEDIUM` if count 5-9

Example:
```
(backend/api/schema.py, debug) appears 12 times
→ PATTERN DETECTED
→ Priority: HIGH (12 >= 10)
```

### 4. Skill Proposal Generation

Generates proposal JSON:

```json
{
  "skill_name": "debug/schema-graphql",
  "category": "02-quality",
  "agent": "debug",
  "priority": "HIGH",
  "reason": "Pattern detected 12 times in 7 days",
  "detected_pattern": "backend/api/schema.py",
  "occurrence_count": 12,
  "proposed_template": {
    "name": "debug/schema-graphql",
    "category": "02-quality",
    "description": "Optimized workflow for GraphQL schema validation",
    "agent_type": "debug"
  },
  "timestamp": "2025-10-20T16:35:00"
}
```

## Execution

### Automatic (Post-Session)

Hook runs automatically after every session:

**Trigger:** `pre-compact` phase in settings.json
**Timeout:** 5 seconds
**Frequency:** Per session

### Manual

Run directly:

```bash
python3 /home/pilote/projet/agi/.claude/hooks/learn_hook.py
```

## Output

Proposals saved to:
```
/home/pilote/projet/agi/.claude/skills/proposals/proposals_YYYYMMDD_HHMMSS.json
```

Each file contains:
```json
{
  "generated_at": "ISO timestamp",
  "patterns_analyzed": 42,
  "proposals_count": 3,
  "proposals": [...]
}
```

## Skill Categories

Proposals auto-categorized:

| Agent | Category | Code |
|-------|----------|------|
| debug | Quality & Testing | 02-quality |
| code | Backend Development | 03-backend |
| frontend | Frontend Development | 04-frontend |
| architect | Architecture | 05-architecture |
| performance_optimizer | Workflow & DevOps | 06-workflow |
| infra_watch | Workflow & DevOps | 06-workflow |
| security_sentinel | Quality & Testing | 02-quality |
| docs | Documentation | 07-docs |

## Example Workflow

### Day 1-7: Repeated Edits

```
Edit backend/api/schema.py
→ Hook auto_trigger_agent triggered
→ debug agent runs
→ Log: (backend/api/schema.py, debug, reason)

... repeat 11 more times ...

Total: 12 occurrences in 7 days
```

### Day 7: Learn Hook Runs

```
Analyze .trigger_log
→ Count (backend/api/schema.py, debug) = 12
→ >= 5 threshold ✓
→ Priority = HIGH (12 >= 10) ✓
→ Generate proposal: "debug/schema-graphql"
→ Save to proposals_20251020_170000.json
```

### Next Phase: Skill Activation (Manual)

```json
// proposals_20251020_170000.json
{
  "skill_name": "debug/schema-graphql",
  "priority": "HIGH",
  "reason": "Pattern detected 12 times"
}

// Move to active skills if approved
// .claude/skills/active/debug/schema-graphql/
```

## Integration with Auto-Trigger

**Trigger Log Integration:**

```python
# auto_trigger_agent.py logs each trigger:
log_trigger(file_path, agent, reason)

# Writes to .claude/hooks/.trigger_log:
{"timestamp": "...", "file": "...", "agent": "...", "reason": "..."}

# Learn hook reads and analyzes:
parse_trigger_log()
analyze_patterns()
propose_skill()
```

**Data Flow:**

```
Edit file
  ↓
auto_trigger_agent.py
  ↓
log_trigger() → .trigger_log
  ↓
(next session post-compact)
  ↓
learn_hook.py runs
  ↓
Analyze .trigger_log
  ↓
Generate proposals → .claude/skills/proposals/
```

## Testing

Run test suite:

```bash
python3 /home/pilote/projet/agi/.claude/hooks/test_learn_hook.py
```

Tests validate:
- Pattern detection logic
- Threshold filtering
- Priority calculation
- Category mapping
- Proposal generation

## Debug & Monitoring

### View Trigger Log

```bash
tail -20 /home/pilote/projet/agi/.claude/hooks/.trigger_log
cat /home/pilote/projet/agi/.claude/hooks/.trigger_log | jq '.'
```

### View Latest Proposals

```bash
ls -lrt /home/pilote/projet/agi/.claude/skills/proposals/
cat /home/pilote/projet/agi/.claude/skills/proposals/proposals_*.json | jq '.'
```

### Count Patterns

```bash
cat /home/pilote/projet/agi/.claude/hooks/.trigger_log | jq -r '.agent' | sort | uniq -c
```

## Configuration

Edit in `.claude/settings.json`:

```json
"pre-compact": [
  {
    "type": "command",
    "command": "python3 /home/pilote/projet/agi/.claude/hooks/learn_hook.py",
    "timeout": 5,
    "name": "learn-patterns"
  }
]
```

Parameters:
- **timeout**: 5 seconds (safe upper bound)
- **name**: Identifier for logging
- **command**: Full path to script

## Performance

- **Log Parse:** O(n) entries in last 7 days
- **Pattern Count:** O(n) with Counter
- **Proposal Gen:** O(m) patterns
- **Typical Runtime:** 100-500ms for 100+ entries
- **Timeout Buffer:** 5s (plenty of headroom)

## Future Enhancements

1. **Skill Activation:** Auto-move HIGH priority to active/
2. **Deduplication:** Merge similar proposals
3. **Feedback:** Track which proposed skills were useful
4. **Expiration:** Remove old proposals (>30 days)
5. **Metrics:** Skill adoption rate
6. **Clustering:** Group similar patterns automatically

## Troubleshooting

### No proposals generated

Check:
1. `.trigger_log` has entries: `wc -l .claude/hooks/.trigger_log`
2. Recent entries: `tail .claude/hooks/.trigger_log`
3. Count >= 5: `cat .trigger_log | jq -r '.agent' | sort | uniq -c`

### Proposals in wrong category

Check mapping in `learn_hook.py` > `extract_skill_category()`

### Hook timeout

- Increase timeout in settings.json if needed
- Hook is non-blocking (won't interrupt session)

## Architecture Notes

**Non-Blocking Design:**
- Hook runs post-session (no impact on user interaction)
- Timeout kills stalled hook (5s max)
- Failures silently ignored (don't crash session)

**Memory Efficient:**
- Parses log sequentially (no full load into memory)
- Counter-based analysis (O(1) lookups)
- JSON output only when proposals generated

**Modular Design:**
- Each function testable independently
- Clear separation: parse → analyze → propose
- Easy to extend with new analysis types

---

**Learn Hook v1.0** - Continuous Skill Discovery System
