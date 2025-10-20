# Skill Proposals - How to Review and Activate

## Where Proposals Are Stored

Learn hook generates skill proposals to:
```
/home/pilote/projet/agi/.claude/skills/proposals/
```

File naming: `proposals_YYYYMMDD_HHMMSS.json`

Example:
```
proposals_20251020_161856.json
proposals_20251020_170000.json
proposals_20251021_090000.json
```

## Review Workflow

### Step 1: View Latest Proposals

```bash
# List proposals
ls -lrt .claude/skills/proposals/

# View latest
cat .claude/skills/proposals/proposals_*.json | jq '.' | tail -100

# View specific file
cat .claude/skills/proposals/proposals_20251020_161856.json | jq '.'
```

### Step 2: Analyze Proposal

Each proposal contains:

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

Key fields:
- **priority:** HIGH (10+ occurrences) or MEDIUM (5-9)
- **occurrence_count:** How many times pattern was detected
- **agent_type:** Which agent handles this skill
- **category:** Skill category (quality, backend, frontend, etc.)

### Step 3: Filter by Priority

HIGH priority (most recommended):
```bash
cat .claude/skills/proposals/proposals_*.json | jq '.proposals[] | select(.priority == "HIGH")'
```

MEDIUM priority:
```bash
cat .claude/skills/proposals/proposals_*.json | jq '.proposals[] | select(.priority == "MEDIUM")'
```

### Step 4: Decide to Activate

For HIGH priority skills, create skill directory:

```bash
# Example: activate debug/schema-graphql

mkdir -p .claude/skills/active/02-quality/debug-schema-graphql
cd .claude/skills/active/02-quality/debug-schema-graphql

# Create SKILL.md from proposal
cat > SKILL.md << 'SKILL'
# Schema GraphQL Validation

Optimized workflow for GraphQL schema validation.

## When to Use
- Editing backend/api/schema.py
- Modifying GraphQL queries/mutations
- Adding new schema fields

## Commands
```bash
pytest backend/tests/api/ -q --timeout=10
```

## Generated From
Pattern detected 12 times in 7 days by learn hook.
SKILL
```

## Activation Structure

### New Skill Directory

```
.claude/skills/active/
├── 02-quality/
│   ├── debug-schema-graphql/
│   │   └── SKILL.md
│   ├── security-secrets-check/
│   │   └── SKILL.md
│   └── ...
├── 03-backend/
│   ├── code-memory-optimization/
│   │   └── SKILL.md
│   └── ...
└── ...
```

### SKILL.md Template

```markdown
# Skill Name

Description from proposal.

## When to Use
When you're working on [specific pattern]

## How It Works
[Short explanation]

## Commands
```bash
# Exact command to run
```

## References
- Generated: [timestamp]
- Pattern: [what was detected]
- Occurrences: [count] times
```

## Prioritization Matrix

Use this to decide which proposals to activate:

| Priority | Occurrences | Recommendation | Action |
|----------|-------------|-----------------|--------|
| HIGH | 10+ | Activate immediately | Move to active/ |
| MEDIUM | 5-9 | Review and consider | Keep in proposals/ |
| LOW | <5 | Archive | Delete if not useful |

## Examples

### HIGH Priority Skill
```json
{
  "skill_name": "debug/schema-graphql",
  "priority": "HIGH",
  "occurrence_count": 12
}
```
→ **ACTION:** Activate immediately
→ **Create:** `.claude/skills/active/02-quality/debug-schema-graphql/`

### MEDIUM Priority Skill
```json
{
  "skill_name": "code/memory-optimization",
  "priority": "MEDIUM",
  "occurrence_count": 7
}
```
→ **ACTION:** Review first, then decide
→ **Decision:** Is memory optimization critical? If yes, activate.

## Monitoring

### Track What You've Activated

Keep a log:
```bash
# In .claude/skills/ACTIVATED.log

# Format:
# date | skill_name | category | reason

2025-10-20 | debug/schema-graphql | 02-quality | Frequent edits (12x)
2025-10-20 | code/memory-optimize | 03-backend | High impact (7x)
2025-10-21 | frontend/component-test | 04-frontend | 5 occurrences
```

### Archive Old Proposals

Remove proposals older than 30 days:

```bash
# View file dates
ls -lrt .claude/skills/proposals/

# Remove old (older than 30 days)
find .claude/skills/proposals/ -mtime +30 -delete
```

## Integration

Once activated, skills can be referenced in:

1. **Agent prompts** - Use in task descriptions
2. **Workflow templates** - Build efficient workflows
3. **Documentation** - Link to activated skills
4. **Training** - Learn from what works

## Future Enhancements

Current: Manual activation
Future: 
- Auto-activate HIGH priority (v2)
- Skill deduplication (v2)
- Skill expiration/archival (v2)
- Feedback loop (v2)

## Quick Commands

```bash
# Generate new proposals (manual trigger)
python3 .claude/hooks/learn_hook.py

# View latest proposals
cat .claude/skills/proposals/proposals_*.json | jq '.' | tail -50

# Count patterns
cat .claude/hooks/.trigger_log | jq '.agent' | sort | uniq -c | sort -rn

# Activate a proposal
mkdir -p .claude/skills/active/[category]/[skill-name]
# Then create SKILL.md

# List activated skills
find .claude/skills/active -type d -name "*.md" -o -type f | grep SKILL

# View activated skills
find .claude/skills/active -type f -name "SKILL.md" -exec head -5 {} +
```

---

**Learn Hook Proposals v1.0** - Skill Discovery & Activation Guide
