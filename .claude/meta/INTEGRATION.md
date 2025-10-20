# MetaOrchestrator Integration Guide

## Quick Start

```bash
# Manual audit
python3 .claude/meta/orchestrator.py

# View latest report
cat .claude/meta/reports/meta_audit_$(date +%Y%m%d).json

# Check execution log
tail .claude/meta/audit.log
```

## Automatic Scheduling

Daily audit scheduled at 9AM via cron:

```bash
# View cron job
crontab -l | grep daily_meta_audit

# Output:
# 0 9 * * * /home/pilote/projet/agi/.claude/hooks/daily_meta_audit.sh
```

## Report Structure

Each daily report includes:

### Skills Analysis
- Total skills files
- Categorization
- Total storage size

### Commands Audit
- Available commands
- Count by category

### Hooks Monitoring
- Active hooks
- Performance baseline (future)

### Agents Inventory
- Configured agents
- Agent types

### CLAUDE.md Health
- Line count
- Bloat detection (>850 lines)
- Extraction recommendations

### Recommendations Engine
Generates actionable insights:
- **OPTIMIZE**: File size/complexity issues
- **CONSOLIDATE**: Duplicate or scattered functionality
- **CLEANUP**: Archive/remove aged artifacts

## Integration Points

### With CI/CD
```bash
# Run audit as pre-commit check
.claude/hooks/daily_meta_audit.sh

# Fail if recommendations count > threshold
python3 -c "
import json
with open('.claude/meta/reports/meta_audit_$(date +%Y%m%d).json') as f:
    recs = json.load(f)['recommendations']
    exit(1 if len(recs) > 3 else 0)
"
```

### With Agent Health Check
```bash
# Include meta audit in daily health check
python run_agents.py health && python3 .claude/meta/orchestrator.py
```

### With Monitoring
```bash
# Alert if infrastructure issues detected
if [ -s .claude/meta/audit.log ]; then
    tail .claude/meta/audit.log | mail -s "Meta Audit Alert" admin@example.com
fi
```

## Performance Baseline

Typical execution metrics:

| Operation | Time | Memory |
|-----------|------|--------|
| Full audit | <5s | <50MB |
| Report generation | <1s | <20MB |
| File I/O | <1s | <10MB |
| Report parsing | <100ms | <5MB |

## Report Location

```
.claude/meta/reports/
├── meta_audit_20251020.json
├── meta_audit_20251019.json
├── meta_audit_20251018.json
└── ... (daily)
```

Auto-cleanup: Keep last 15 days, archive older reports

## Extending MetaOrchestrator

### Add New Metric

```python
# In orchestrator.py
def analyze_custom(self) -> dict:
    """Custom metric"""
    return {
        "metric_name": value
    }

# Update audit_daily()
report["custom"] = self.analyze_custom()
```

### Add New Recommendation

```python
# In generate_recommendations()
if some_condition:
    recs.append({
        "type": "category",
        "target": "resource",
        "reason": "explanation",
        "action": "recommended action"
    })
```

## Troubleshooting

### Cron not running
```bash
# Check cron status
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog | tail
```

### Report not generating
```bash
# Run manually with output
python3 .claude/meta/orchestrator.py

# Check directory permissions
ls -ld .claude/meta/reports/
chmod 755 .claude/meta/reports/
```

### Missing data in report
```bash
# Verify file paths exist
ls -d .claude/skills .claude/commands .claude/hooks .claude/agents

# Check CLAUDE.md location
ls -l CLAUDE.md
```

## Next Steps

1. Monitor recommendations daily
2. Implement high-priority optimizations
3. Track infrastructure health over time
4. Auto-execute cleanup recommendations (future)
5. Generate trend reports (week/month)
