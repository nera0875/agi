# Hooks System Guide

## Overview

The **hooks system** is a set of Python scripts that automatically monitor and improve project health.

**Hooks Directory**: `.claude/hooks/`

## Available Hooks

### 1. `optimize_hook.py` - Architecture Analysis (NEW)

**Purpose**: Analyzes project architecture and proposes optimizations

**How It Works**:
- Scans backend services, agents, routes
- Analyzes memory tier (L1/L2/L3) coverage
- Detects naming violations
- Identifies complexity hotspots
- Generates actionable recommendations

**Trigger**: Automatically on Edit/Write to critical files
- `backend/api/**`
- `backend/services/**`
- `backend/agents/**`
- `backend/routes/**`
- `.claude/**`
- `CLAUDE.md`

**Usage**:
```bash
# CLI analysis
python3 .claude/hooks/optimize_cli.py run
python3 .claude/hooks/optimize_cli.py list
python3 .claude/hooks/optimize_cli.py view

# Health check
python3 .claude/hooks/health_check.py
```

**Output**: `.claude/meta/optimize_*.json`

**Documentation**: `.claude/hooks/README_OPTIMIZE.md`

---

### 2. `auto_trigger_agent.py` - Automatic Agent Triggers

**Purpose**: Automatically triggers appropriate agents when critical files change

**Mapping**:
- `backend/api/schema.py` → debug agent (tests)
- `backend/services/memory_service.py` → performance_optimizer
- `backend/services/graph_service.py` → debug agent
- `backend/services/voyage_wrapper.py` → performance_optimizer
- `cortex/agi_tools_mcp.py` → debug agent
- `backend/agents/` → debug agent
- `CLAUDE.md` → docs agent
- `frontend/src/` → frontend agent

**Trigger**: PostToolUse on file modification

**How It Works**:
- Detects file change
- Matches against trigger rules
- Spawns agent in background (non-blocking)
- Logs trigger event to `.trigger_log`

**Usage**:
```bash
# Monitor triggers
python3 .claude/hooks/monitor_triggers.py --stats
python3 .claude/hooks/monitor_triggers.py --timeline 24
python3 .claude/hooks/monitor_triggers.py --follow
```

**Output**: `.claude/hooks/.trigger_log` (JSON lines)

---

### 3. `monitor_triggers.py` - Trigger Analysis

**Purpose**: Analyzes auto_trigger logs and provides statistics

**Features**:
- Trigger frequency by file
- Trigger frequency by agent
- Recent trigger timeline
- Statistics dashboard

**Usage**:
```bash
python3 .claude/hooks/monitor_triggers.py --stats       # Statistics
python3 .claude/hooks/monitor_triggers.py --timeline 24 # Last 24h
python3 .claude/hooks/monitor_triggers.py --follow      # Live monitoring
python3 .claude/hooks/monitor_triggers.py --clear       # Clear logs
```

---

### 4. `health_check.py` - Architecture Health Validation (NEW)

**Purpose**: Quick validation that architecture meets health thresholds

**Checks**:
- Service count (<25)
- Memory services (<6)
- Memory tiers coverage (L1/L2/L3 present)
- Agent count (>2)
- Complexity hotspots (<10)
- Naming conventions (<5 violations)

**Exit Codes**:
- `0` = HEALTHY ✅
- `1` = WARNING ⚠️
- `2` = CRITICAL 🔴

**Usage**:
```bash
# Display results
python3 .claude/hooks/health_check.py

# JSON output
python3 .claude/hooks/health_check.py --json

# Custom threshold
python3 .claude/hooks/health_check.py --threshold max_services 30
```

---

## Quick Reference

| Hook | Purpose | Trigger | Output |
|------|---------|---------|--------|
| **optimize_hook.py** | Architecture analysis | PostToolUse | `.claude/meta/optimize_*.json` |
| **auto_trigger_agent.py** | Auto-trigger agents | PostToolUse | `.claude/hooks/.trigger_log` |
| **monitor_triggers.py** | Analyze triggers | Manual | Console output |
| **health_check.py** | Validate health | Manual | Console or JSON |

---

## Workflow: Using All Hooks Together

### Scenario 1: You Modify backend/services/memory_service.py

**What Happens Automatically**:

1. **optimize_hook.py** triggers
   - Analyzes architecture changes
   - Detects if service size increased
   - Saves recommendation

2. **auto_trigger_agent.py** triggers
   - Detects memory_service.py change
   - Spawns performance_optimizer agent
   - Agent analyzes performance implications

3. **Result**: Report + Agent background task

### Scenario 2: Morning Health Check

**Command**:
```bash
python3 .claude/hooks/health_check.py
```

**Output**:
```
✅ Status: HEALTHY
  ✅ service_count        : 18
  ✅ memory_services      : 5
  ✅ memory_tiers         : {L1: 2, L2: 2, L3: 2}
  ✅ agents               : 5
  ✅ complexity           : 7
  ✅ naming               : 4
OPTIMIZATION OPPORTUNITIES: 4
```

### Scenario 3: Weekly Optimization Review

**Commands**:
```bash
# 1. View latest recommendations
python3 .claude/hooks/optimize_cli.py view

# 2. Check trigger statistics
python3 .claude/hooks/monitor_triggers.py --stats

# 3. Health check
python3 .claude/hooks/health_check.py
```

---

## Reports & Logs

### Locations

| Item | Path | Format |
|------|------|--------|
| Optimization reports | `.claude/meta/optimize_*.json` | JSON |
| Trigger logs | `.claude/hooks/.trigger_log` | JSON Lines |
| Latest optimization | `.claude/meta/optimize_latest.json` | JSON |

### Reading Reports

```python
import json

# Read latest optimization report
with open('.claude/meta/optimize_latest.json') as f:
    analysis = json.load(f)

# Access data
stats = analysis['statistics']
recommendations = analysis['recommendations']

print(f"Services: {stats['services']['total']}")
print(f"Recommendations: {len(recommendations)}")
```

---

## Integration with Other Tools

### With Agent System
- Hooks → Trigger agents → Agents provide results
- Optimize hook provides context for agent analysis

### With CLAUDE.md
- Hooks validate CLAUDE.md guidelines
- Recommendations align with architecture standards

### With Version Control
- Hooks detect changes via tool invocations
- Could integrate with git hooks in future

---

## Performance

| Hook | Time | Blocking | Frequency |
|------|------|----------|-----------|
| optimize_hook.py | 2-5s | No | Per critical file change |
| auto_trigger_agent.py | <1s | No | Per file change |
| monitor_triggers.py | <1s | Manual | On demand |
| health_check.py | 2-5s | Manual | On demand |

**Total Overhead**: Negligible (background, non-blocking)

---

## Maintenance

### Clearing Logs

```bash
python3 .claude/hooks/monitor_triggers.py --clear
```

### Viewing Recent Analysis

```bash
python3 .claude/hooks/optimize_cli.py list
```

### Checking Specific Report

```bash
python3 .claude/hooks/optimize_cli.py view optimize_20251020_161845
```

---

## Troubleshooting

### Hook Not Triggering

**Check**:
- File matches critical patterns? (backend/services/*, etc.)
- Environment variables set? (CLAUDE_TOOL_NAME, CLAUDE_FILE_PATH)
- Permissions? (chmod +x optimize_hook.py)

### No Recommendations

**Means**:
- Architecture is healthy ✅
- No issues detected within thresholds

### Reports Not Saving

**Check**:
- `.claude/meta/` directory exists?
- Write permissions on `.claude/`?

---

## Contributing

To add new hooks:

1. Create `{name}_hook.py` in `.claude/hooks/`
2. Implement main() entry point
3. Add error handling (non-blocking)
4. Add to trigger rules if needed
5. Create README_{name}.md documentation
6. Test with `CLAUDE_TOOL_NAME=Edit CLAUDE_FILE_PATH=backend/... python3 ...`

---

## See Also

- `.claude/hooks/README_OPTIMIZE.md` - Detailed optimize hook guide
- `.claude/meta/` - Reports directory
- `CLAUDE.md` - Project architecture guidelines
