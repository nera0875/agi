#!/bin/bash
set -euo pipefail

# Memory Daemon - Consolidation via Claude Code headless
CLAUDE_DIR="$HOME/.claude"
PROJECT_DIR="/home/pilote/projet/primaire/AGI"
SCRIPT_DIR="$PROJECT_DIR/.claude/scripts/python"
LOG_FILE="$SCRIPT_DIR/daemon.log"

# Logging
exec >> "$LOG_FILE" 2>&1
echo "[$(date -Iseconds)] === Memory Daemon Started ==="

# Task prompt (inline, pas besoin YAML parsing)
TASK=$(cat <<'TASK_EOF'
MISSION: Consolidation mémoire intelligente long-terme

CONTEXTE USAGE:
- Mémoire chargée via /data-load par orchestrator
- Projets long-terme (>1 session, plusieurs semaines)
- Crucial pour continuité décisions/patterns

ÉTAPES:
1. Check si ~/.claude/context.json existe
2. Check si ~/.claude/context-full.json existe (créer si absent: {})
3. Grep conversations ~/.claude/projects/-home-pilote-projet-primaire-AGI/*.jsonl
   - Parse messages type:"user" et type:"assistant"
   - Skip patterns: "Bash output", "Read tool", "✓ Terminé", "File list"
   - Keep patterns: "Agent", "Décision", "Convention", "Structure", "RÈGLES", "créé", "finalisé"
   - Extraire timestamp + content seulement

4. Append raw events → ~/.claude/context-full.json (format JSONL, append-only)

5. Consolide intelligemment pour ~/.claude/context.json:
   - Phrases courtes (10-20 mots max)
   - Renforce importance (patterns répétés mention_count++)
   - Créer connexions (supersedes/continues/caused_by/related_to)
   - Calculer importance = freq*0.3 + recency*0.4 + connections*0.3
   - Marquer obsolètes (status: obsolete) - JAMAIS delete physique
   - Fusionner doublons sémantiques

6. Write ~/.claude/context.json
   Format JSON strict:
   {
     "version": "2.0.0",
     "last_processed_timestamp": "ISO8601_NOW",
     "entries": [
       {
         "id": "ctx-XXX",
         "timestamp": "ISO8601",
         "type": "pattern|decision|action",
         "theme": "architecture|memory|agents|workflow",
         "content": "phrase courte 10-20 mots",
         "importance": 0.0-1.0,
         "status": "active|obsolete",
         "frequency": {"mention_count": N, "contexts": ["x", "y"]},
         "connections": {"supersedes": [], "continues": [], "caused_by": [], "related_to": []},
         "tags": ["tag1", "tag2"]
       }
     ],
     "metadata": {
       "total_entries": N,
       "active_entries": N,
       "obsolete_entries": N,
       "themes": [],
       "top_patterns": []
     }
   }

RÈGLES STRICTES:
- Garder TOUTES entries (actives + obsolètes marquées)
- Phrases ultra-courtes, denses, keywords explicites
- Validation JSON avant Write
- Timeline ISO 8601
- Importance composite obligatoire
TASK_EOF
)

# Execute consolidation
echo "[$(date -Iseconds)] Running consolidation..."

if echo "$TASK" | claude-code --model haiku --timeout 180 2>&1; then
  echo "[$(date -Iseconds)] Consolidation completed"

  # Validation
  if [ -f "$CLAUDE_DIR/context.json" ]; then
    if jq empty "$CLAUDE_DIR/context.json" 2>/dev/null; then
      ENTRIES=$(jq '.entries | length' "$CLAUDE_DIR/context.json")
      echo "[$(date -Iseconds)] context.json validated - $ENTRIES entries"
    else
      echo "[$(date -Iseconds)] ERROR: context.json invalid JSON"
      exit 1
    fi
  else
    echo "[$(date -Iseconds)] WARNING: context.json not created"
  fi
else
  echo "[$(date -Iseconds)] ERROR: Consolidation failed"
  exit 1
fi

echo "[$(date -Iseconds)] === Memory Daemon Finished ==="
