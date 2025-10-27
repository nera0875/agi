---
name: git-tracker
description: Smart git tracking - auto-commit milestones, push alerts, intelligent messages
type: implementation
---

## Concept

Auto-commit on phase completion, track dirty state, generate smart commit messages from diffs.

## Automatic Triggers

- Phase VALIDATION complete → Auto-commit changes
- 5+ commits since push → Alert user
- Session end detected → Propose push
- Feature milestone → Commit + push

## State Tracking (`.plan/state.json` git section)

```json
{
  "git": {
    "last_commit": "2025-10-27T12:00:00Z",
    "commits_since_push": 3,
    "dirty": true,
    "branch": "main"
  }
}
```

## Smart Commit Messages

Analyze `git diff --stat`:
- Backend files only → "backend: [summary]"
- Frontend files only → "frontend: [summary]"
- Tests added → "test: [summary]"
- Mixed → "feat: [summary]"

Format:
```
<type>: <summary>

- Change 1
- Change 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Methods

- `track_files()` - Update state.json git section
- `should_commit()` - Check VALIDATION done + dirty files
- `should_push()` - Check commits_since_push > 5
- `generate_message()` - Create message from diff --stat
- `auto_save(phase)` - Full workflow: commit + push

## Rules

- NEVER commit if tests fail
- NEVER push without commit
- ALWAYS update state.json after git operation
- ALWAYS use conventional format
