# Learn Hook - Quick Start

## TL;DR

Learn hook automatically detects repeated patterns in agent executions and proposes new skills.

**Runs:** Automatically post-session (no action needed)
**Time:** ~5 seconds
**Output:** Skill proposals saved to `.claude/skills/proposals/`

## 5-Minute Setup

### Already Done For You

1. ✅ Hook installed: `.claude/hooks/learn_hook.py`
2. ✅ Tests passing: Run `python3 .claude/hooks/test_learn_hook.py`
3. ✅ Integrated: Added to `.claude/settings.json`
4. ✅ Ready: No configuration needed

### What It Does

```
Your editing → auto_trigger_agent logs → learn_hook analyzes → proposes skills
```

When you frequently edit same file with same agent, learn hook detects the pattern:

- Pattern detected 12 times in 7 days? → Proposes "debug/schema-graphql" skill
- Pattern detected 7 times? → Proposes "code/memory-optimize" skill
- Pattern detected 3 times? → Too rare, ignored (threshold: 5+)

## How to Use

### Automatic (Default)

Hook runs automatically after each session. No action needed.

Output: `.claude/skills/proposals/proposals_YYYYMMDD_HHMMSS.json`

### Manual (Optional)

```bash
python3 .claude/hooks/learn_hook.py
```

### View Proposals

```bash
# Latest proposals
cat .claude/skills/proposals/proposals_*.json | jq '.'

# High priority only
cat .claude/skills/proposals/proposals_*.json | jq '.proposals[] | select(.priority == "HIGH")'

# Count patterns
cat .claude/hooks/.trigger_log | jq '.agent' | sort | uniq -c
```

## Proposal Structure

```json
{
  "skill_name": "debug/schema-graphql",
  "category": "02-quality",
  "agent": "debug",
  "priority": "HIGH",
  "occurrence_count": 12,
  "reason": "Pattern detected 12 times in 7 days",
  "timestamp": "2025-10-20T16:35:00"
}
```

Key fields:
- **priority:** HIGH (10+) = activate soon, MEDIUM (5-9) = review first
- **occurrence_count:** How many times this pattern appeared
- **agent:** Which agent handles this workflow

## Next Steps

### Review Proposals

```bash
ls -lrt .claude/skills/proposals/
cat .claude/skills/proposals/proposals_*.json | jq '.proposals[] | .skill_name'
```

### Activate Skills

For HIGH priority skills:

```bash
# Example: activate debug/schema-graphql

mkdir -p .claude/skills/active/02-quality/debug-schema-graphql

cat > .claude/skills/active/02-quality/debug-schema-graphql/SKILL.md << 'SKILL'
# Schema GraphQL Validation

Detects patterns in GraphQL schema editing.

## When to Use
- Editing backend/api/schema.py
- Modifying GraphQL mutations/queries

## Command
```bash
pytest backend/tests/api/ -q --timeout=10
```
SKILL
```

## Priority Guide

| Priority | Count | Action |
|----------|-------|--------|
| HIGH | 10+ | Activate immediately |
| MEDIUM | 5-9 | Review and consider |

## Commands Quick Reference

```bash
# Run tests
python3 .claude/hooks/test_learn_hook.py

# Generate proposals (manual)
python3 .claude/hooks/learn_hook.py

# View latest
cat .claude/skills/proposals/proposals_*.json | jq '.' | tail -50

# Debug triggers
cat .claude/hooks/.trigger_log | tail -20

# Activate skill
mkdir -p .claude/skills/active/[category]/[skill-name]
# then create SKILL.md
```

## FAQ

### Will it slow down my session?

No. Hook runs post-session (after you're done), 5-second timeout.

### What if it breaks?

Failures are silent (non-blocking). Session continues normally.

### How often does it run?

After each session ends. Once per day minimum = 1+ proposals.

### Can I disable it?

Yes. Remove from `.claude/settings.json` `pre-compact` section.

### How do I see what patterns were detected?

```bash
cat .claude/hooks/.trigger_log | jq '.' | grep -E "agent|file|timestamp"
```

## Learn More

- Full guide: `.claude/hooks/LEARN_HOOK.md`
- Activation: `.claude/skills/PROPOSALS_GUIDE.md`
- System overview: `.claude/skills/README.md`

## Examples

### Example 1: Frequent Schema Edits

You edit `backend/api/schema.py` 12 times with debug agent:

→ Learn hook detects pattern
→ Generates: "debug/schema-graphql" (HIGH priority)
→ You activate it
→ Next time you edit schema, you can use the skill

### Example 2: Repeated Memory Optimization

You optimize `backend/services/memory_service.py` 7 times with performance_optimizer:

→ Learn hook detects pattern
→ Generates: "code/memory-optimize" (MEDIUM priority)
→ You review it and decide if critical
→ If yes, activate as skill

## Status

```
✅ Hook working
✅ Tests passing
✅ Integrated in settings
✅ Ready to use
```

Run `python3 .claude/hooks/test_learn_hook.py` to verify.

---

**Next:** Review proposals in `.claude/skills/proposals/` and activate HIGH priority skills!
