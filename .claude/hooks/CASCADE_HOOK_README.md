# Cascade Hook - Automatic Phase Sequencing

## Overview

The cascade hook automatically triggers the next phase in a workflow sequence after the current phase completes.

**Phase Sequence:**
```
understanding → research → architecture → implementation → validation → documentation
```

## Files

- `cascade_hook.py` - Main hook (auto-triggered by Claude Code)
- `cascade_monitor.py` - Monitor script for analyzing cascade events
- `.cascade_log` - Event log (auto-created)

## How It Works

### 1. Phase Completion

When Claude Code completes a phase:
```python
# Claude Code sets environment variable
os.environ['CLAUDE_COMPLETED_PHASE'] = 'understanding'
os.environ['CLAUDE_AUTO_CASCADE'] = 'true'
```

### 2. Cascade Trigger

Hook automatically:
1. Detects completed phase
2. Maps to next phase
3. Finds appropriate agent
4. Launches agent in background

### 3. Agent Launch

Next phase agent runs with `--auto-cascade` flag:
```bash
python3 run_agents.py agent research --auto-cascade
```

## Usage

### Enable Cascade in Claude Code

```python
# In your agent orchestrator
from pathlib import Path
import os

def complete_phase(phase_name: str):
    """Signal phase completion for cascade"""
    os.environ['CLAUDE_COMPLETED_PHASE'] = phase_name
    os.environ['CLAUDE_AUTO_CASCADE'] = 'true'

    # Trigger cascade hook
    subprocess.run(['python3', '.claude/hooks/cascade_hook.py'])
```

### Manual Test

```bash
# Test understanding → research cascade
CLAUDE_COMPLETED_PHASE="understanding" \
CLAUDE_AUTO_CASCADE="true" \
python3 .claude/hooks/cascade_hook.py

# View cascade log
tail .claude/hooks/.cascade_log
```

### Monitor Cascades

```bash
# Show cascade statistics
python3 .claude/hooks/cascade_monitor.py --stats

# Show phase transition chains
python3 .claude/hooks/cascade_monitor.py --chains

# Follow cascade log in real-time
python3 .claude/hooks/cascade_monitor.py --follow

# Clear cascade log
python3 .claude/hooks/cascade_monitor.py --clear
```

## Phase Mapping

| Current Phase | Next Phase | Agent |
|---|---|---|
| understanding | research | research |
| research | architecture | architect |
| architecture | implementation | code |
| implementation | validation | debug |
| validation | documentation | docs |

## Event Types

| Action | Meaning |
|---|---|
| `triggered` | ✅ Successfully triggered next phase |
| `skipped_disabled` | ⏸️ Cascade is disabled |
| `trigger_failed` | ❌ Failed to trigger agent |
| `final_phase` | ✨ Phase is final (no next phase) |
| `no_agent_found` | ⚠️ No agent mapped for next phase |

## Log Format

Each event logged as JSON:
```json
{
  "timestamp": "2025-10-20T16:18:21.014044",
  "phase": "understanding",
  "next_phase": "research",
  "action": "triggered"
}
```

## Features

### Non-Blocking Execution

- Agents run in background via `subprocess.Popen(start_new_session=True)`
- Does not interrupt main workflow
- Runs in isolated process group

### Configurable Cascade

- Set `CLAUDE_AUTO_CASCADE=false` to disable
- Set `CLAUDE_AUTO_CASCADE=true` to enable
- Can cascade chain multiple phases

### Event Logging

- All cascade events logged to `.cascade_log`
- JSON format for easy parsing
- Timestamped for timeline analysis

## Example: Complete Cascade Chain

```
Start: User asks "Implement feature X"

understanding phase:
  └─ Ask × 3 (explore backend/frontend/DB)
  └─ Cascade triggered → research

research phase:
  └─ Research × 3 (exa, context7, fetch)
  └─ Cascade triggered → architecture

architecture phase:
  └─ Architect × 1 (design solution)
  └─ Cascade triggered → implementation

implementation phase:
  └─ Code × 3 (backend/frontend/migrations)
  └─ Cascade triggered → validation

validation phase:
  └─ Debug × 3 (unit/integration/e2e tests)
  └─ Cascade triggered → documentation

documentation phase:
  └─ Docs × 1 (README/API)
  └─ COMPLETE!

Total time: ~3-5 minutes (parallel execution)
```

## Monitoring Example

```bash
$ python3 .claude/hooks/cascade_monitor.py --stats
======================================================================
CASCADE HOOK STATISTICS
======================================================================

Total Events: 6
  ✅ Triggered: 6
  ⏸️  Skipped (disabled): 0
  ❌ Failed: 0
  ✨ Final phase: 0

✅ Success Rate: 100.0%

Phase Transitions:
  understanding → research        2x
  research → architecture         2x
  architecture → implementation   1x
  implementation → validation     1x

Recent Events (last 10):
  [2025-10-20T16:22:15.123456] ✅ validation      → documentation   (triggered)
  [2025-10-20T16:21:42.456789] ✅ implementation  → validation      (triggered)
  ...
```

## Integration Points

### In run_agents.py

```python
def execute_phase(phase: str, agents: list):
    """Execute phase and trigger cascade on completion"""
    # Run all agents in phase
    results = parallel_execute(agents)

    # Signal phase completion for cascade
    os.environ['CLAUDE_COMPLETED_PHASE'] = phase
    os.environ['CLAUDE_AUTO_CASCADE'] = 'true'

    # Trigger cascade hook
    subprocess.run([
        'python3',
        '.claude/hooks/cascade_hook.py'
    ])

    return results
```

### In orchestrator.py

```python
def orchestrate_workflow():
    """Full workflow with automatic cascading"""
    # Phase 1: Understanding
    ask_results = execute_phase('understanding', [
        Task(ask, "scan backend"),
        Task(ask, "scan frontend"),
        Task(ask, "scan database")
    ])
    # → Cascade hook auto-triggers research

    # Phases 2-6 auto-cascade...
```

## Performance

- **Hook Execution:** <100ms
- **Phase Trigger:** Async (non-blocking)
- **Log Write:** <10ms
- **Full Cascade Chain:** 3-5 minutes (6 phases, parallel agents)

## Troubleshooting

### Cascade Not Triggering

```bash
# Check environment variables
echo $CLAUDE_COMPLETED_PHASE
echo $CLAUDE_AUTO_CASCADE

# Must be:
# CLAUDE_COMPLETED_PHASE=understanding
# CLAUDE_AUTO_CASCADE=true
```

### Agent Not Starting

```bash
# Check if run_agents.py exists and is executable
ls -l /home/pilote/projet/agi/run_agents.py

# Test manually
cd /home/pilote/projet/agi
python3 run_agents.py agent research
```

### Events Not Logged

```bash
# Check cascade log permissions
ls -la .claude/hooks/.cascade_log

# Should be readable/writable by current user
chmod 644 .claude/hooks/.cascade_log
```

## Advanced

### Disable Cascade Globally

```bash
export CLAUDE_AUTO_CASCADE=false
```

### View All Cascade Events

```bash
cat .claude/hooks/.cascade_log | jq '.action' | sort | uniq -c
```

### Parse Cascade Times

```bash
python3 -c "
import json
with open('.claude/hooks/.cascade_log') as f:
    logs = [json.loads(l) for l in f if l.strip()]

for log in logs:
    if log['action'] == 'triggered':
        print(f\"{log['phase']} → {log['next_phase']}\")
"
```
