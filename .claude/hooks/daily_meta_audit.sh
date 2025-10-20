#!/bin/bash
# Daily Meta Audit Hook - Runs 9AM via cron
# Automated infrastructure.claude/ manager

cd /home/pilote/projet/agi

# Run MetaOrchestrator audit
python3 .claude/meta/orchestrator.py >> .claude/meta/audit.log 2>&1

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S'): Meta audit complete" >> .claude/meta/audit.log

# Keep only last 100 lines of log
tail -100 .claude/meta/audit.log > .claude/meta/audit.log.tmp && mv .claude/meta/audit.log.tmp .claude/meta/audit.log

exit 0
