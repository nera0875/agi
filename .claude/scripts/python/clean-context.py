#!/usr/bin/env python3
"""Clean Context - Parse + Filter + Consolidate context.json brut

MISSION: Transform raw conversation events → ultra-optimized memory entries

Workflow:
1. Load context.json raw entries
2. Filter noise (tool outputs, system messages, short content)
3. Extract meaningful events (decisions, patterns, discoveries)
4. Clustering DBSCAN
5. Gemini consolidation
6. Output clean context.json
"""

import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
import requests
from datetime import datetime

# Config
PROJECT_DIR = Path("/home/pilote/projet/primaire/AGI")
CONTEXT_FILE = PROJECT_DIR / ".claude/context.json"
CONTEXT_CLEAN = PROJECT_DIR / ".claude/context-clean.json"
BACKUP_DIR = PROJECT_DIR / ".claude/scripts/python/backups"

# Load models
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Config OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"

def load_context():
    """Load context.json raw entries"""
    if not CONTEXT_FILE.exists():
        print("ERROR: context.json not found")
        return []

    with open(CONTEXT_FILE) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    print(f"Loaded {len(entries)} raw entries")
    return entries

def filter_noise(entries):
    """Filter noise from raw conversation events

    Keep ONLY:
    - User messages >50 chars (meaningful requests)
    - Assistant text responses >100 chars (explanations, not tool outputs)

    Skip:
    - Tool outputs (Read, Edit, Bash results)
    - System reminders
    - Short messages (<50 chars)
    - Tool use definitions
    """

    meaningful = []

    for entry in entries:
        content = str(entry.get("content", ""))
        msg_type = entry.get("type", "")

        # Skip noise patterns
        if any(skip in content for skip in [
            "tool_use", "tool_result", "system-reminder",
            "Bash output", "Read tool", "Edit tool",
            "function_calls", "antml:invoke",
            "cat -n", "wc -l", "ls -la"
        ]):
            continue

        # Skip short messages
        if len(content) < 50:
            continue

        # Keep meaningful content
        if msg_type == "user" and len(content) >= 50:
            meaningful.append({
                "content": content[:500],  # Max 500 chars
                "type": msg_type,
                "timestamp": entry.get("timestamp", 0)
            })
        elif msg_type == "assistant" and len(content) >= 100:
            # Parse assistant text responses (not tool outputs)
            if content.startswith("[{"):  # JSON tool output
                continue
            meaningful.append({
                "content": content[:500],
                "type": msg_type,
                "timestamp": entry.get("timestamp", 0)
            })

    print(f"Filtered: {len(entries)} → {len(meaningful)} meaningful entries")
    return meaningful

def cluster_entries(entries):
    """Clustering DBSCAN avec eps adaptatif"""

    if len(entries) < 3:
        print("Too few entries for clustering")
        return {-1: entries}

    # Embeddings
    print(f"Embedding {len(entries)} entries...")
    texts = [e["content"] for e in entries]
    embeddings = embedding_model.encode(texts, batch_size=32, show_progress_bar=False)

    # Eps adaptatif
    if len(entries) < 100:
        eps = 0.4
    elif len(entries) < 500:
        eps = 0.5
    else:
        eps = 0.6

    print(f"Clustering with eps={eps}...")
    clusters = DBSCAN(eps=eps, min_samples=3).fit_predict(embeddings)

    # Group by cluster
    cluster_map = {}
    for i, cluster_id in enumerate(clusters):
        if cluster_id not in cluster_map:
            cluster_map[cluster_id] = []
        cluster_map[cluster_id].append(entries[i])

    print(f"Found {len(cluster_map)} clusters")
    for cid, centries in cluster_map.items():
        status = "outliers" if cid == -1 else f"cluster {cid}"
        print(f"  {status}: {len(centries)} entries")

    return cluster_map

def gemini_consolidate_cluster(centries, cluster_id):
    """Consolidate cluster via Gemini

    Returns 1-3 optimized entries per cluster
    """

    if cluster_id == -1:
        # Outliers = important unique events, keep all
        return centries

    # Build prompt
    cluster_json = json.dumps(centries, indent=2)

    prompt = f"""TU ES EXPERT CONSOLIDATION MÉMOIRE AGI

MISSION: Fusionner {len(centries)} entries similaires en 1-3 entries ULTRA-OPTIMISÉES pour Grep.

CLUSTER DATA:
{cluster_json}

RÈGLES STRICTES:
1. Fusionner doublons sémantiques → 1 entry représentative
2. Si concepts distincts dans cluster → max 3 entries
3. Phrases 10-20 mots (grep-friendly, pas de code/JSON)
4. Keywords explicites (agents, python, memory, workflow, etc)
5. Type précis: pattern|decision|action|discovery|error|preference
6. Theme: agents|python-dev|react-dev|memory|architecture|debugging|autre
7. Status: active|obsolete|deprecated

OUTPUT JSON STRICT:
{{
  "consolidated": [
    {{
      "id": "mem_{cluster_id}_001",
      "content": "phrase 10-20 mots claire et grep-friendly",
      "type": "pattern|decision|action|discovery|error|preference",
      "theme": "agents|python-dev|memory|architecture|debugging|autre",
      "keywords": ["mot1", "mot2", "mot3"],
      "status": "active",
      "frequency": {len(centries)},
      "timestamp": "ISO plus récent"
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON, no markdown."""

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/pilote/AGI-memory",
                "X-Title": "AGI Memory Cleaner"
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 4000
            },
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter error {response.status_code}")

        result_text = response.json()["choices"][0]["message"]["content"]

        # Clean markdown
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]

        result = json.loads(result_text)
        consolidated = result.get("consolidated", [])

        print(f"  Cluster {cluster_id}: {len(centries)} → {len(consolidated)} entries")
        return consolidated

    except Exception as e:
        print(f"  ERROR Gemini cluster {cluster_id}: {e}")
        # Fallback
        fallback = centries[0].copy()
        fallback["frequency"] = len(centries)
        fallback["cluster_id"] = cluster_id
        return [fallback]

def backup_context():
    """Backup context.json"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"context_raw_{timestamp}.json"

    if CONTEXT_FILE.exists():
        with open(CONTEXT_FILE) as f:
            data = json.load(f)
        with open(backup_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backup: {backup_file}")

def clean_context():
    """Main cleaning workflow"""

    print("=== Context Cleaner Started ===\n")

    # 1. Backup
    backup_context()

    # 2. Load raw
    entries = load_context()
    if not entries:
        print("No entries")
        return

    # 3. Filter noise
    meaningful = filter_noise(entries)
    if len(meaningful) < 10:
        print("Too few meaningful entries after filtering")
        return

    # 4. Cluster
    cluster_map = cluster_entries(meaningful)

    # 5. Gemini consolidation par cluster
    clean_entries = []

    for cluster_id, centries in cluster_map.items():
        consolidated = gemini_consolidate_cluster(centries, cluster_id)
        clean_entries.extend(consolidated)

    # 6. Save clean
    output = {
        "entries": clean_entries,
        "metadata": {
            "total_entries": len(clean_entries),
            "original_count": len(entries),
            "meaningful_count": len(meaningful),
            "compression_ratio": f"{len(entries) / len(clean_entries):.2f}x",
            "last_cleaned": datetime.now().isoformat(),
            "clusters_found": len(cluster_map)
        }
    }

    with open(CONTEXT_CLEAN, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Cleaning Complete ===")
    print(f"Raw: {len(entries)} entries")
    print(f"Meaningful: {len(meaningful)} entries")
    print(f"Clean: {len(clean_entries)} entries")
    print(f"Compression: {output['metadata']['compression_ratio']}")
    print(f"Output: {CONTEXT_CLEAN}")

if __name__ == "__main__":
    clean_context()
