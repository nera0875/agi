---
description: Full codebase audit (quality, debt, security)
---

Launch 3 agents in parallel:
1. code_guardian (tests, quality)
2. debt_hunter (tech debt, large files)
3. security_sentinel (secrets, vulnerabilities)

```bash
python /home/pilote/projet/agi/run_agents.py agent code_guardian &
python /home/pilote/projet/agi/run_agents.py agent debt_hunter &
python /home/pilote/projet/agi/run_agents.py agent security_sentinel &
wait
```

Aggregate reports from agents/team/reports/.
