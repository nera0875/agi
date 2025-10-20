# Claude Code Hooks

Automated hooks que se déclenchent lors d'opérations de fichiers.

## Auto-Trigger Agent Hook

**File:** `auto_trigger_agent.py`

Déclenche automatiquement les agents appropriés sur fichiers critiques.

### Trigger Rules

| File Pattern | Agent | Action |
|---|---|---|
| `backend/api/schema.py` | `debug` | Valide GraphQL schema + tests |
| `backend/services/memory_service.py` | `performance_optimizer` | Analyse performance mémoire |
| `backend/services/graph_service.py` | `debug` | Teste Neo4j operations |
| `backend/services/voyage_wrapper.py` | `performance_optimizer` | Analyse coûts embeddings |
| `cortex/agi_tools_mcp.py` | `debug` | Valide MCP tools |
| `backend/agents/**` | `debug` | Teste agent logic |
| `CLAUDE.md` | `docs` | Vérifie documentation |
| `frontend/src/**` | `frontend` | Valide build TypeScript |

### Comment ça marche

1. À chaque Edit/Write d'un fichier critique
2. Hook se déclenche en arrière-plan (non-bloquant)
3. Agent approprié est lancé via `run_agents.py`
4. Tests/validation tournent en parallèle

### Non-Bloquant

- Timeout hook = 2s (très court)
- Agents tournent en background
- Zéro impact sur ton workflow
- Logs disponibles dans `.trigger_log`

### Logs

```bash
# Voir triggers récents
tail -f /home/pilote/projet/agi/.claude/hooks/.trigger_log

# Exemple log:
{"timestamp": "2025-10-20T16:00:45", "file": "backend/api/schema.py", "agent": "debug", "reason": "GraphQL schema modified"}
```

### Test

```bash
bash /home/pilote/projet/agi/.claude/hooks/test_hook.sh
```

## Architecture

```
.claude/hooks/
├── auto_trigger_agent.py    # Hook principal
├── .trigger_log             # Logs des triggers
├── test_hook.sh            # Script test
└── README.md               # Cette doc
```

## Configuration

Hook activé via `.claude/settings.json`:

```json
{
  "name": "auto-trigger-agents",
  "matcher": "Edit:backend/**/*|Write:backend/**/*|...",
  "hooks": [
    {
      "type": "command",
      "command": "python3 /home/pilote/projet/agi/.claude/hooks/auto_trigger_agent.py",
      "timeout": 2
    }
  ]
}
```

## Ajouter Règles Supplémentaires

Edit `auto_trigger_agent.py`:

```python
TRIGGER_RULES = {
    'path/to/file.py': {
        'agent': 'agent_name',
        'prompt': 'Your custom prompt here',
        'reason': 'Why this file matters'
    },
    # ...
}
```

Agents disponibles:
- `ask` - Exploration codebase
- `research` - Recherche externe
- `architect` - Design système
- `code` - Implémentation backend
- `frontend` - Implémentation React
- `debug` - Tests & debugging
- `docs` - Documentation
- `sre` - Infrastructure

---

**Created:** 2025-10-20
**Version:** 1.0
**Status:** ✅ Operational
