# Auto-Trigger Agent Hook - Documentation Index

## Files

| File | Purpose |
|------|---------|
| `auto_trigger_agent.py` | Main hook implementation |
| `monitor_triggers.py` | Monitor and analyze triggers |
| `test_hook.sh` | Test suite |
| `.trigger_log` | Trigger event log (JSON lines) |
| `README.md` | Quick start & overview |
| `USAGE.md` | How to use the hook |
| `TECHNICAL.md` | Deep dive architecture |
| `INDEX.md` | This file |

## Quick Links

**First time?**
→ Read: `USAGE.md`

**How does it work?**
→ Read: `README.md`

**Need technical details?**
→ Read: `TECHNICAL.md`

**Want to customize?**
→ Edit: `auto_trigger_agent.py` → `TRIGGER_RULES` dict

**Monitor triggers?**
→ Run: `python3 monitor_triggers.py`

**Test the hook?**
→ Run: `bash test_hook.sh`

## Summary

**What:** PostToolUse hook that auto-triggers agents on critical file edits

**Where:** `.claude/hooks/auto_trigger_agent.py`

**When:** On Edit/Write operations (matched by settings.json)

**Why:** Automatic validation without manual intervention

**How:** Pattern matching → agent dispatch → background execution

**Status:** ✅ Production Ready

## Trigger Rules (8 total)

```
backend/api/schema.py
  → debug agent (validates GraphQL)

backend/services/memory_service.py
  → performance_optimizer agent (checks performance)

backend/services/graph_service.py
  → debug agent (tests Neo4j)

backend/services/voyage_wrapper.py
  → performance_optimizer agent (checks embeddings cost)

cortex/agi_tools_mcp.py
  → debug agent (validates MCP tools)

backend/agents/**
  → debug agent (tests agent logic)

CLAUDE.md
  → docs agent (verifies documentation)

frontend/src/**
  → frontend agent (validates TypeScript build)
```

## Common Commands

```bash
# Show trigger statistics
python3 monitor_triggers.py

# Follow triggers in real-time
python3 monitor_triggers.py --follow

# Test the hook
bash test_hook.sh

# View trigger log
tail -n 20 .trigger_log

# Clear logs
python3 monitor_triggers.py --clear

# Test manually
export CLAUDE_TOOL_NAME="Edit"
export CLAUDE_FILE_PATH="backend/api/schema.py"
python3 auto_trigger_agent.py
```

## Performance

- Hook execution: <200ms
- Agent execution: 10-60s (background)
- Trigger log: ~200 bytes per entry
- No impact on main workflow

## Configuration

Edit: `.claude/settings.json`

Search for: `"auto-trigger-agents"`

Modify `"matcher"` pattern to add/remove file patterns.

## Adding Rules

Edit: `.claude/hooks/auto_trigger_agent.py`

Add to `TRIGGER_RULES` dict:

```python
'path/to/file.py': {
    'agent': 'agent_name',
    'prompt': 'optional custom prompt',
    'reason': 'why this matters'
}
```

Available agents:
- ask
- research
- architect
- code
- frontend
- debug
- docs
- sre

---

**Version:** 1.0
**Created:** 2025-10-20
**Status:** ✅ Active
