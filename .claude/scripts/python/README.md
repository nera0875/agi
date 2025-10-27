# Memory Daemon - Système Consolidation Automatique

## Architecture

**Daemon** : `memory-daemon.py`
- Parsing conversations JSONL
- Embeddings locaux (all-MiniLM-L6-v2)
- Clustering sémantique DBSCAN (eps=0.6)
- Consolidation Gemini 2.0 Flash (gratuit)
- Retry rate limit automatique

**Fichiers** :
- `~/.claude/context.json` : Mémoire optimisée (chargée /data-load)
- `~/.claude/context-full.json` : Backup append-only
- `daemon.log` : Logs exécution

**Automation** :
- Cron : */10 * * * * (toutes les 10 minutes)
- Wrapper : `run-daemon.sh`

## Performance

- **Vitesse** : 442 embeddings/sec
- **Consolidation** : 2457 events → ~650 entries (-21.8%)
- **Coût** : $0 (embeddings local + Gemini free tier)

## Usage

### Forcer run immédiat
```bash
bash run-daemon.sh
```

### Voir logs temps réel
```bash
tail -f daemon.log
```

### Compter entries
```bash
python3 -c "import json; print(len(json.load(open('/home/pilote/.claude/context.json'))['entries']))"
```

### Reset mémoire (DEBUG)
```bash
echo '{"entries": [], "processed_files": []}' > ~/.claude/context.json
```

## Configuration

**Paramètres clustering** :
- eps=0.6 (distance sémantique max)
- min_samples=2 (min events par cluster)

**Retry rate limit** :
- Max 5 tentatives
- Backoff : 6s, 12s, 24s, 48s, 96s

**API Keys** :
- Gemini : Dans run-daemon.sh (GOOGLE_API_KEY)

## Troubleshooting

**Rate limit 429** :
- Normal : retry automatique 6s → 12s
- Si persist : attendre 1 minute

**Context.json vide** :
- Vérifier daemon.log erreurs Gemini
- Vérifier context-full.json (backup)

**Cron pas lancé** :
```bash
crontab -l | grep memory-daemon
systemctl status cron
```

## Stack Technique

- Python 3.10+
- sentence-transformers (all-MiniLM-L6-v2)
- scikit-learn (DBSCAN clustering)
- google-generativeai (Gemini API)
- dateutil (ISO timestamp parsing)
