# Skills & Pattern Learning System

Auto-learning system that detects repeated patterns in agent executions and proposes new optimized skills.

## Overview

The **Learn Hook** runs post-session and analyzes patterns to propose new reusable skills for the AGI system.

### Architecture

```
post-session
   ↓
learn_hook.py runs
   ↓
Parse .claude/hooks/.trigger_log (agent executions)
   ↓
Analyze patterns (count occurrences)
   ↓
If pattern >= 5 times in 7 days
   ↓
Generate skill proposal
   ↓
Save to .claude/skills/proposals/
```

## How It Works

### 1. Pattern Detection

The hook monitors `.claude/hooks/.trigger_log` which contains all agent triggers:

```json
{
  "timestamp": "2025-10-20T16:30:00",
  "file": "backend/api/schema.py",
  "agent": "debug",
  "reason": "GraphQL schema modified - validate queries/mutations"
}
```

### 2. Threshold Analysis

Patterns detected when:
- **File + Agent pair** appears >= 5 times in last 7 days
- **Reason + Agent pair** appears >= 5 times in last 7 days

Example:
- `(backend/api/schema.py, debug)` appears 12 times → **PATTERN DETECTED**
- Priority: `HIGH` if count >= 10, else `MEDIUM`

### 3. Skill Proposal

When pattern detected, generates:

```json
{
  "skill_name": "debug/schema-graphql",
  "category": "02-quality",
  "agent": "debug",
  "reason": "Pattern detected 12 times in 7 days",
  "priority": "HIGH",
  "detected_pattern": "backend/api/schema.py",
  "occurrence_count": 12,
  "proposed_template": {
    "name": "debug/schema-graphql",
    "category": "02-quality",
    "description": "Optimized workflow for repeated task on backend/api/schema.py",
    "agent_type": "debug"
  }
}
```

## Skill Categories

| Category | Code | Agent Type |
|----------|------|-----------|
| Quality & Testing | `02-quality` | debug, security_sentinel |
| Backend Development | `03-backend` | code |
| Frontend Development | `04-frontend` | frontend |
| Architecture | `05-architecture` | architect |
| Workflow & DevOps | `06-workflow` | performance_optimizer, infra_watch |
| Documentation | `07-docs` | docs |
| Custom | `08-custom` | - |

## File Structure

```
.claude/
├── skills/
│   ├── README.md (this file)
│   ├── proposals/               # Generated proposals
│   │   ├── proposals_20251020_163000.json
│   │   ├── proposals_20251020_170000.json
│   │   └── ...
│   └── active/                  # Activated skills (future)
│       └── (manual management)
└── hooks/
    ├── learn_hook.py            # Main pattern detection
    └── .trigger_log             # Execution log (auto-generated)
```

## Proposal Files

Each proposal file includes:

```json
{
  "generated_at": "2025-10-20T16:35:00",
  "patterns_analyzed": 156,
  "proposals_count": 3,
  "proposals": [
    { ... skill proposal ... },
    { ... skill proposal ... }
  ]
}
```

## Example Scenario

### Day 1-7: Repeated Triggers

```
Edit backend/api/schema.py
  → Trigger auto_trigger_agent → debug agent runs → Log entry

Edit backend/api/schema.py (again)
  → Trigger auto_trigger_agent → debug agent runs → Log entry

... (12 total times in 7 days)
```

### Day 7: Learn Hook Runs

```
Analysis:
- (backend/api/schema.py, debug) = 12 occurrences
- >= threshold (5) → PATTERN DETECTED
- Generate proposal: "debug/schema-graphql"
- Priority: HIGH (count >= 10)
- Save to proposals_20251020_170000.json
```

### Proposal Output

```json
{
  "skill_name": "debug/schema-graphql",
  "category": "02-quality",
  "agent": "debug",
  "priority": "HIGH",
  "occurrence_count": 12,
  "reason": "Pattern detected 12 times in 7 days",
  "proposed_template": {
    "name": "debug/schema-graphql",
    "description": "Optimized workflow for GraphQL schema validation",
    "agent_type": "debug"
  }
}
```

## Manual Usage

Run learn hook directly:

```bash
python3 /home/pilote/projet/agi/.claude/hooks/learn_hook.py
```

Check proposals:

```bash
ls -lrt /home/pilote/projet/agi/.claude/skills/proposals/
cat /home/pilote/projet/agi/.claude/skills/proposals/proposals_latest.json
```

## Integration with Workflow

### Automatic (Default)

Learn hook runs automatically:
- Trigger: `pre-compact` (post-session)
- Timeout: 5 seconds
- Frequency: After each session completes

### Manual (Optional)

Can be invoked manually:
```bash
python3 .claude/hooks/learn_hook.py
```

## Future Enhancements

1. **Skill Activation**: Move HIGH priority proposals to `active/`
2. **Skill Merging**: Combine similar proposals
3. **Skill Expiration**: Remove old proposals (>30 days)
4. **Skill Metrics**: Track which proposals were useful
5. **Feedback Loop**: Learn from activated skills

## Configuration

In `.claude/settings.json`:

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

## Debug

Check execution logs:

```bash
# View trigger log
cat /home/pilote/projet/agi/.claude/hooks/.trigger_log | tail -20

# View latest proposals
cat /home/pilote/projet/agi/.claude/skills/proposals/proposals_*.json | jq '.' | tail -50
```

---

**Learn Hook v1.0** - AGI Auto-Learning System
