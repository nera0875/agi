# Auto-Trigger Agent Hook - Usage Guide

## Overview

The auto-trigger agent hook automatically runs validation agents when you edit critical project files.

**Key benefit:** Zero configuration needed. Just edit files, agents validate automatically in background.

## Quick Start

### 1. The Hook is Already Active

No setup needed! It's configured in `.claude/settings.json`:

```json
"auto-trigger-agents": {
  "matcher": "Edit:backend/**/*|Write:backend/**/*|...",
  "hooks": [{"type": "command", "command": "python3 .claude/hooks/auto_trigger_agent.py"}]
}
```

### 2. Edit a Critical File

When you edit/create a file in:
- `backend/api/schema.py` → `debug` agent validates GraphQL
- `backend/services/memory_service.py` → `performance_optimizer` checks performance
- `backend/services/graph_service.py` → `debug` tests Neo4j
- `backend/services/voyage_wrapper.py` → `performance_optimizer` checks embeddings cost
- `cortex/agi_tools_mcp.py` → `debug` validates MCP tools
- `backend/agents/**` → `debug` tests agent logic
- `CLAUDE.md` → `docs` verifies documentation
- `frontend/src/**` → `frontend` validates TypeScript build

### 3. Agent Runs in Background

- Hook executes in <200ms (non-blocking)
- Agent runs in background process
- No impact on your workflow
- Results logged to `.claude/hooks/.trigger_log`

## Monitoring

### View Recent Triggers

```bash
# Show statistics
python3 .claude/hooks/monitor_triggers.py

# Follow triggers in real-time
python3 .claude/hooks/monitor_triggers.py --follow

# View timeline (last 24h)
python3 .claude/hooks/monitor_triggers.py --timeline 24
```

### Check Log File

```bash
# See all triggers
cat .claude/hooks/.trigger_log

# Last 10 triggers
tail -n 10 .claude/hooks/.trigger_log

# Pretty print
tail -n 5 .claude/hooks/.trigger_log | python3 -m json.tool
```

## Behavior

### When Hook Triggers

1. **Detection:** File Edit/Write detected
2. **Pattern Matching:** File path checked against rules
3. **Agent Dispatch:** If match, agent triggered in background
4. **Logging:** Trigger event logged
5. **Continuation:** Hook exits, main workflow continues

### Non-Blocking

```
Your action: Edit backend/api/schema.py
    ↓
Hook detects (instant)
    ↓
Hook matches rule (agent=debug)
    ↓
Hook triggers debug agent (background process)
    ↓
Hook exits immediately ✅ (<200ms)
    ↓
You continue working (no delay)
    ↓
Debug agent runs tests in parallel (doesn't block)
```

## Examples

### Example 1: Edit GraphQL Schema

```
Action: Edit backend/api/schema.py
  ↓
Hook detects
  ↓
Triggers: debug agent
  ↓
Agent runs: pytest backend/tests/api/ -q
  ↓
Log entry: {"timestamp": "...", "agent": "debug", "reason": "GraphQL schema modified"}
  ↓
You keep working (no delay)
```

### Example 2: Improve Memory Service

```
Action: Edit backend/services/memory_service.py
  ↓
Hook detects
  ↓
Triggers: performance_optimizer agent
  ↓
Agent analyzes: Memory queries, indexes, caching
  ↓
Agent reports: Query performance, optimization suggestions
  ↓
You check reports later: agents/team/reports/
```

### Example 3: Multiple Edits

```
Action 1: Edit backend/api/schema.py
  ↓ Trigger: debug agent ✅

Action 2: Edit backend/services/memory_service.py
  ↓ Trigger: performance_optimizer agent ✅

Action 3: Edit frontend/src/components/brain.tsx
  ↓ Trigger: frontend agent ✅

All 3 agents run in parallel (your workflow continues instantly)
```

## Customization

### Add New Trigger Rule

Edit `.claude/hooks/auto_trigger_agent.py`:

```python
TRIGGER_RULES = {
    # Existing rules...

    'path/to/critical/file.py': {
        'agent': 'debug',  # or: performance_optimizer, docs, frontend, etc.
        'prompt': 'Your custom instruction',
        'reason': 'Why this file matters'
    }
}
```

Then test:

```bash
bash .claude/hooks/test_hook.sh
```

### Modify Existing Rule

```python
TRIGGER_RULES = {
    'backend/api/schema.py': {
        'agent': 'code',  # Changed from 'debug'
        'prompt': 'Validate schema design and performance',  # New prompt
        'reason': 'GraphQL schema is critical'
    }
}
```

### Disable a Rule

Comment out or remove from `TRIGGER_RULES`:

```python
# TRIGGER_RULES = {
#     'backend/api/schema.py': {...},  # Disabled
# }
```

## Advanced Usage

### View Agent Reports

```bash
# List all agent reports
ls -la agents/team/reports/

# View latest debug report
cat agents/team/reports/debug_latest.json | python3 -m json.tool
```

### Clear Trigger Log

```bash
# Clear all history
python3 .claude/hooks/monitor_triggers.py --clear

# Or manually
rm .claude/hooks/.trigger_log
```

### Test Hook Manually

```bash
# Simulate Edit event
export CLAUDE_TOOL_NAME="Edit"
export CLAUDE_FILE_PATH="backend/api/schema.py"
python3 .claude/hooks/auto_trigger_agent.py

# Check trigger was logged
tail .claude/hooks/.trigger_log
```

### Run Full Test Suite

```bash
bash .claude/hooks/test_hook.sh
```

Expected output:
```
✅ PASS: Hook is executable
✅ PASS: Python syntax valid
✅ PASS: Hook executed without errors
✅ PASS: Hook executed without errors
✅ All tests passed!
```

## FAQ

### Q: Does the hook slow down my edits?

**A:** No. Hook timeout is 2s, but executes in <200ms. Non-blocking.

### Q: Can agents conflict with each other?

**A:** No. Agents run in separate processes with their own locks. Safe for parallel execution.

### Q: What if an agent fails?

**A:** Hook catches all exceptions. Main workflow continues. Agent output logged to reports.

### Q: Can I disable specific triggers?

**A:** Yes. Comment out rules in `TRIGGER_RULES` dict.

### Q: How do I see agent results?

**A:** Check `agents/team/reports/` directory. Each agent creates JSON report.

### Q: Can I add my own custom rules?

**A:** Yes. Edit `TRIGGER_RULES` in `auto_trigger_agent.py` and restart Claude Code.

### Q: Is the hook secure?

**A:** Yes. Runs with Claude Code permissions, no shell injection, no privilege escalation.

## Troubleshooting

### Hook Not Triggering

1. Check file matches pattern:
   ```bash
   grep "matcher" .claude/settings.json
   ```

2. Verify hook is executable:
   ```bash
   ls -la .claude/hooks/auto_trigger_agent.py
   # Should show: -rwxrwxr-x
   ```

3. Test manually:
   ```bash
   export CLAUDE_TOOL_NAME="Edit"
   export CLAUDE_FILE_PATH="backend/api/schema.py"
   python3 .claude/hooks/auto_trigger_agent.py
   echo $?  # Should be 0
   ```

### Agent Not Running

1. Check trigger was logged:
   ```bash
   tail .claude/hooks/.trigger_log
   ```

2. Verify agent exists:
   ```bash
   python3 run_agents.py agent debug --help
   ```

3. Check agent reports:
   ```bash
   ls agents/team/reports/
   ```

### Log File Growing Too Large

Logs are small (JSON lines, ~200 bytes each). 1000 triggers = ~200KB. Safe to accumulate 5000+ triggers (~1MB).

To clean up old logs:
```bash
tail -n 1000 .claude/hooks/.trigger_log > .tmp
mv .tmp .claude/hooks/.trigger_log
```

## Performance

| Operation | Time | Impact |
|-----------|------|--------|
| Hook execution | <200ms | None |
| Pattern matching | <10ms | None |
| Subprocess spawn | <100ms | None |
| **Total** | **<200ms** | **None** |
| Agent execution | 10-60s | Background only |

**Main workflow impact: Zero.** All timing is background.

## Summary

The auto-trigger hook:
- ✅ Runs automatically (no setup)
- ✅ Non-blocking (<200ms)
- ✅ Agents run in parallel
- ✅ Results logged automatically
- ✅ Easy to customize
- ✅ Safe and secure

Just edit critical files, agents validate automatically.

---

**Version:** 1.0
**Created:** 2025-10-20
**Status:** ✅ Operational
