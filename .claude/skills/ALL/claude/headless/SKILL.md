---
name: claude-headless
description: Claude Code Headless Mode - Automation sans interface graphique
category: claude-integration
---

# Claude Code Headless Mode

Mode d'exécution automatisé de Claude Code sans interface graphique. Permet intégration dans workflows CI/CD, systèmes automatisés, et orchestration complète.

## Modes d'Exécution Headless

### Mode 1: Stdin/Stdout (Texte)

**Usage**: Piping direct dans bash, scripts, ou automation.

```bash
echo "Task description" | claude-code
```

**Comportement**:
- Lit depuis stdin
- Envoie résultat vers stdout
- Mode stateless (pas de session)
- Timeout: 30s défaut, configurable --timeout

**Exemple**:
```bash
echo "Scan backend/*.py - list files" | claude-code --model haiku --timeout 60
```

### Mode 2: File-Based (JSON)

**Usage**: Automation via fichiers, intégration système.

```bash
claude-code --input task.json --output result.json
```

**Format input.json**:
```json
{
  "task": "Read backend/service.py",
  "model": "haiku",
  "tools": ["Read", "Grep"],
  "timeout": 45,
  "context": {
    "cwd": "/project",
    "env": {"DEBUG": "1"}
  }
}
```

**Format output.json**:
```json
{
  "status": "success|error|timeout",
  "result": "...",
  "tokens_used": 1250,
  "execution_time": 12.5,
  "errors": []
}
```

### Mode 3: Server Mode (Long-Running)

**Usage**: Daemon/service continuous, multiple requests.

```bash
claude-code --server --port 8000
```

**HTTP Endpoints**:
- `POST /task` - Submit task
- `GET /task/:id` - Check status
- `GET /tasks` - List running tasks
- `DELETE /task/:id` - Cancel task

**Request**:
```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Your task here",
    "model": "haiku"
  }'
```

**Response**:
```json
{
  "id": "task-uuid",
  "status": "queued|running|completed|failed",
  "result": "...",
  "created_at": "2025-10-26T12:00:00Z"
}
```

## Flags et Options

### Général

| Flag | Description | Défaut |
|------|-------------|--------|
| `--model` | Model à utiliser (haiku, sonnet, opus) | haiku |
| `--timeout` | Timeout en secondes | 30 |
| `--max-tokens` | Limite tokens output | 4096 |
| `--temperature` | Randomness (0-1) | 0.7 |
| `--no-cache` | Désactiver cache | false |

### Input/Output

| Flag | Description |
|------|-------------|
| `--input` | Fichier input JSON |
| `--output` | Fichier output JSON |
| `--format` | Format output (json, text, yaml) |
| `--pretty` | Pretty-print output | false |

### Execution

| Flag | Description |
|------|-------------|
| `--parallel` | Nombre workers parallèles | 1 |
| `--server` | Mode server (daemon) | false |
| `--port` | Port server | 8000 |
| `--workers` | Workers server | 4 |
| `--queue-size` | Max tasks queued | 100 |

### Context

| Flag | Description |
|------|-------------|
| `--cwd` | Working directory | current |
| `--env` | Variables env (JSON) | {} |
| `--secrets` | Fichier secrets (.env) | none |
| `--context-file` | Context custom JSON | none |

### Debugging

| Flag | Description |
|------|-------------|
| `--verbose` | Debug output | false |
| `--log-level` | Level (debug, info, warn, error) | info |
| `--trace` | Full execution trace | false |
| `--dry-run` | Simuler sans exécuter | false |

## Automation Patterns

### Pattern 1: CI/CD Pipeline

**GitHub Actions**:
```yaml
- name: Run Claude Code Task
  run: |
    echo '{"task": "Test backend/*.py", "model": "haiku"}' | \
    claude-code --timeout 120 --format json > results.json

- name: Check Results
  run: |
    jq '.status' results.json | grep -q success
```

### Pattern 2: Scheduled Tasks (Cron)

```bash
#!/bin/bash
# Daily code scan

TASK='{
  "task": "Scan backend/ - find deprecated patterns",
  "model": "haiku",
  "timeout": 300
}'

echo "$TASK" | claude-code --output /var/log/scan-$(date +%Y%m%d).json
```

### Pattern 3: Webhook Integration

```bash
#!/bin/bash
# Déclenché par webhook

PAYLOAD=$(cat)

echo "$PAYLOAD" | \
  claude-code \
    --model haiku \
    --context-file /etc/claude-config.json \
    --timeout 60 \
    --output /tmp/webhook-result.json

# Envoyer résultat
curl -X POST "$WEBHOOK_URL" \
  -d @/tmp/webhook-result.json
```

### Pattern 4: Batch Processing

```bash
#!/bin/bash
# Traiter multiple fichiers en parallèle

for file in backend/*.py; do
  echo "Scan $file" | \
    claude-code \
      --model haiku \
      --parallel 4 \
      --timeout 30 &
done

wait
```

## Configuration File (.claude-headless)

**Localisation**: `~/.claude-headless` ou `./.claude-headless` projet

```yaml
# Default model
model: haiku

# Timeouts
timeout: 30
max_tokens: 4096

# Execution
parallel: 2
cache: true
cache_dir: ~/.cache/claude-code

# Server
server:
  enabled: false
  port: 8000
  workers: 4
  queue_size: 100

# Logging
logging:
  level: info
  file: ~/.cache/claude-code/headless.log
  format: json

# Context
context:
  cwd: .
  env: {}
  # Load from .env
  env_file: .env

# Retry policy
retry:
  enabled: true
  max_attempts: 3
  backoff: exponential
  delay: 1s

# Rate limiting
rate_limit:
  requests_per_minute: 30
  burst: 5
```

## Environment Variables

```bash
# Model
CLAUDE_CODE_MODEL=haiku

# Timeouts
CLAUDE_CODE_TIMEOUT=30
CLAUDE_CODE_MAX_TOKENS=4096

# Server
CLAUDE_CODE_SERVER_PORT=8000
CLAUDE_CODE_SERVER_WORKERS=4

# Logging
CLAUDE_CODE_LOG_LEVEL=info
CLAUDE_CODE_LOG_FILE=~/.cache/claude-code/headless.log

# API
CLAUDE_API_KEY=sk-...  # Auto-loaded from ~/.claude/auth

# Context
CLAUDE_CODE_CWD=/project
CLAUDE_CODE_SECRETS_FILE=.env
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Task failed |
| 2 | Invalid arguments |
| 3 | Timeout |
| 4 | Rate limited |
| 5 | Configuration error |
| 127 | Command not found |

## Error Handling

### Retry Automatique

```bash
# Avec retry (défaut: 3 tentatives)
claude-code --task "..." --retry 3 --backoff exponential
```

### Timeout Handling

```bash
# Timeout personnalisé par type tâche
claude-code \
  --task "Long analysis" \
  --timeout 300 \
  --partial-ok  # Accepter résultats partiels
```

### Error Capture

```bash
if ! result=$(echo "$TASK" | claude-code 2>/tmp/error.log); then
  echo "Error: $(cat /tmp/error.log)"
  exit 1
fi
```

## Performance Optimization

### Caching

```bash
# Activer cache (défaut)
claude-code --cache --cache-dir /tmp/claude-cache

# Désactiver cache
claude-code --no-cache
```

### Parallel Execution

```bash
# 8 workers parallèles
claude-code \
  --task "Process files" \
  --parallel 8 \
  --model haiku  # Cheap + fast
```

### Model Selection

**Recommandations**:
- `haiku`: Tasks <1 min, simple, cheap
- `sonnet`: Tasks <10 min, modérée, coût moyen
- `opus`: Tasks >10 min, complexe, coûteux

## Examples Complets

### Example 1: Scan Code Quality

```bash
#!/bin/bash
TASK=$(cat <<'EOF'
Scan backend/services/*.py:
1. Find large functions (>50 lines)
2. Check imports
3. List classes + methods
4. Return JSON

FORMAT JSON:
{
  "files": [...],
  "large_functions": [...],
  "import_issues": [...],
  "classes": [...]
}
EOF
)

echo "$TASK" | \
  claude-code \
    --model haiku \
    --timeout 60 \
    --format json \
    --output scan-results.json

jq '.large_functions | length' scan-results.json
```

### Example 2: Scheduled Validation

```bash
#!/bin/bash
# Dans crontab: 0 */6 * * * /scripts/validate.sh

claude-code \
  --input validation-task.json \
  --output /var/log/validation-$(date +%Y%m%d-%H%M%S).json \
  --timeout 120 \
  --log-level info

# Alert si erreurs
if jq '.status' /var/log/validation-*.json | grep -q error; then
  echo "Validation failed" | mail -s "Alert" admin@example.com
fi
```

### Example 3: Server Mode

```bash
# Terminal 1: Start server
claude-code --server --port 8000 --workers 4

# Terminal 2: Submit tasks
for i in {1..10}; do
  curl -X POST http://localhost:8000/task \
    -H "Content-Type: application/json" \
    -d "{\"task\": \"Task $i\", \"model\": \"haiku\"}"
done

# Terminal 2: Check status
curl http://localhost:8000/tasks | jq .
```

## Limitations

- Pas d'interface graphique (textuel uniquement)
- Pas de session persistante (stateless par défaut)
- Max 10 tâches parallèles sans server mode
- Rate limiting: 30 req/min (configurable)
- Timeout max: 600s (10 minutes)

## Troubleshooting

**Problem**: "Command not found"
```bash
# Solution: Install or add to PATH
claude-code --version
export PATH="$PATH:$(npm root -g)/claude-code/bin"
```

**Problem**: Timeout
```bash
# Augmenter timeout
--timeout 120
# Ou utiliser partial-ok
--partial-ok
```

**Problem**: Rate limited
```bash
# Attendre ou utiliser retry
--retry 5 --backoff exponential
```

**Problem**: Output tronqué
```bash
# Augmenter max-tokens
--max-tokens 8192
# Ou streamer résultats
--stream
```

## Voir Aussi

- [Claude Code Guide](https://docs.claude.com/claude-code)
- [Automation Patterns](./automation-patterns)
- [Server Mode](./server-mode)
- [API Reference](./api-reference)
