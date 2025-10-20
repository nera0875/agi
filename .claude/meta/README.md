# MetaOrchestrator - Infrastructure Manager

Auto-audit quotidien de l'infrastructure `.claude/` avec recommendations.

## Architecture

```
.claude/meta/
├── orchestrator.py          # Main audit engine
├── reports/                 # Daily JSON reports
├── audit.log                # Execution log
└── README.md                # This file
```

## Daily Audit (automatique via cron)

```bash
# Lancé automatiquement à 9AM
bash .claude/hooks/daily_meta_audit.sh

# Ou manuel:
python3 .claude/meta/orchestrator.py
```

## Audit Report Structure

Chaque rapport JSON contient:

```json
{
  "audit_date": "ISO timestamp",
  "skills": {
    "total": 12,
    "categories": {...},
    "size_kb": 75
  },
  "commands": {...},
  "hooks": {...},
  "agents": {...},
  "claude_md": {
    "lines": 850,
    "bloated": false
  },
  "recommendations": [
    {
      "type": "optimize|consolidate|cleanup",
      "target": "file/dir path",
      "action": "Recommended action"
    }
  ]
}
```

## Recommendations

### OPTIMIZE
- CLAUDE.md > 850 lignes → Extract to Skills
- Duplicate code → Consolidate

### CONSOLIDATE
- Hooks > 5 → Group by domain
- Skills > 20 → Organize by category

### CLEANUP
- Reports > 30 → Archive old (>15 days)
- Logs > 1MB → Compress

## Reports Storage

- Location: `.claude/meta/reports/`
- Naming: `meta_audit_YYYYMMDD.json`
- Retention: Auto-cleanup (keep last 15 days)

## Integration

Hook in `.claude/hooks/daily_meta_audit.sh`:
- Runs daily at 9AM
- Appends to `.claude/meta/audit.log`
- Keeps last 100 lines of log

## Usage Examples

### Programmatic

```python
from orchestrator import MetaOrchestrator

orch = MetaOrchestrator()
report = orch.audit_daily()
print(report['recommendations'])
```

### Command Line

```bash
# Full audit with pretty print
python3 .claude/meta/orchestrator.py

# Check specific component
python3 -c "from orchestrator import *; o=MetaOrchestrator(); print(o.analyze_skills())"
```

## Metrics Tracked

- Skills: Count + Categories + Size
- Commands: List available
- Hooks: List active
- Agents: List configured
- CLAUDE.md: Line count + bloat detection
- Reports: Archive size + retention

## Performance

- Audit execution: <5 seconds
- Memory usage: <50MB
- Storage: ~1KB per report/day = 365KB/year

## Future Enhancements

- [ ] Unused skills detection
- [ ] Hook performance metrics
- [ ] Agent usage statistics
- [ ] CLAUDE.md change tracking
- [ ] Auto-cleanup aged reports
