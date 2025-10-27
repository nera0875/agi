#!/usr/bin/env python3
"""Context Optimizer - Clustering Sémantique + Gemini Consolidation

MISSION: Optimiser context.json via clustering + LLM pour Grep ultra-efficace

Workflow:
1. Load context.json entries
2. Embedding via sentence-transformers
3. Clustering DBSCAN (eps adaptatif selon densité)
4. Gemini consolidation par cluster
5. Graph relations automatiques
6. Output context-optimized.json
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
CONTEXT_OPTIMIZED = PROJECT_DIR / ".claude/context-optimized.json"
BACKUP_DIR = PROJECT_DIR / ".claude/scripts/python/backups"

# Load models
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Config OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"

def load_context():
    """Load context.json entries"""
    if not CONTEXT_FILE.exists():
        print("ERROR: context.json not found")
        return []

    with open(CONTEXT_FILE) as f:
        data = json.load(f)

    entries = data.get("entries", [])
    print(f"Loaded {len(entries)} entries")
    return entries

def backup_context():
    """Backup context.json before optimization"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"context_{timestamp}.json"

    if CONTEXT_FILE.exists():
        with open(CONTEXT_FILE) as f:
            data = json.load(f)
        with open(backup_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backup created: {backup_file}")

def cluster_entries(entries):
    """Clustering sémantique avec DBSCAN adaptatif

    Stratégie eps adaptatif:
    - <100 entries: eps=0.3 (strict)
    - 100-500: eps=0.4 (medium)
    - >500: eps=0.5 (loose)
    """

    if len(entries) < 3:
        print("Too few entries for clustering, keeping all")
        return [{-1: entries}]  # All outliers

    # Embeddings
    print(f"Embedding {len(entries)} entries...")
    texts = [e["content"] for e in entries]
    embeddings = embedding_model.encode(texts, batch_size=32, show_progress_bar=False)

    # Eps adaptatif
    if len(entries) < 100:
        eps = 0.3
    elif len(entries) < 500:
        eps = 0.4
    else:
        eps = 0.5

    print(f"Clustering with eps={eps}...")
    clusters = DBSCAN(eps=eps, min_samples=2).fit_predict(embeddings)

    # Group by cluster
    cluster_map = {}
    for i, cluster_id in enumerate(clusters):
        if cluster_id not in cluster_map:
            cluster_map[cluster_id] = []
        cluster_map[cluster_id].append(entries[i])

    print(f"Found {len(cluster_map)} clusters (including outliers)")
    for cid, centries in cluster_map.items():
        status = "outliers" if cid == -1 else f"cluster {cid}"
        print(f"  {status}: {len(centries)} entries")

    return cluster_map

def gemini_consolidate_cluster(cluster_entries, cluster_id):
    """Consolidate cluster via Gemini

    Returns optimized entry representing the cluster
    """

    if cluster_id == -1:
        # Outliers = keep all (important unique events)
        return cluster_entries

    # Build prompt
    cluster_json = json.dumps(cluster_entries, indent=2)

    prompt = f"""TU ES EXPERT OPTIMISATION MÉMOIRE AGI - CONSOLIDATION CLUSTER

MISSION: Fusionner {len(cluster_entries)} entries similaires en 1-3 entries ULTRA-OPTIMISÉES.

CLUSTER DATA:
{cluster_json}

RÈGLES STRICTES:
1. Fusionner doublons sémantiques → 1 entry représentative
2. Si vraiment distincts (même cluster mais concepts différents) → max 3 entries
3. Phrases 10-20 mots (grep-friendly)
4. Keywords explicites (techniques directs)
5. Type précis (pattern/decision/action/discovery/error)
6. Theme clair (agents/python-dev/react-dev/memory/architecture/debugging)
7. Status (active/obsolete/deprecated)
8. Connections: supersedes/caused_by/related_to (IDs entries liées)

OUTPUT JSON STRICT:
{{
  "consolidated": [
    {{
      "id": "cluster_{cluster_id}_001",
      "content": "phrase 10-20 mots représentant cluster",
      "type": "pattern|decision|action|discovery|error",
      "theme": "agents|python-dev|react-dev|memory|architecture|debugging|autre",
      "keywords": ["mot1", "mot2", "mot3"],
      "status": "active|obsolete|deprecated",
      "frequency": {len(cluster_entries)},
      "connections": {{
        "supersedes": ["id1", "id2"],
        "caused_by": [],
        "related_to": []
      }},
      "timestamp": "ISO plus récent du cluster"
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON, no markdown, no explanation."""

    try:
        # OpenRouter API call
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/pilote/AGI-memory",
                "X-Title": "AGI Memory Optimizer"
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
            raise Exception(f"OpenRouter error {response.status_code}: {response.json()}")

        result_text = response.json()["choices"][0]["message"]["content"]

        # Clean markdown if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]

        result = json.loads(result_text)
        consolidated = result.get("consolidated", [])

        print(f"  Cluster {cluster_id}: {len(cluster_entries)} → {len(consolidated)} entries")
        return consolidated

    except Exception as e:
        print(f"  ERROR Gemini cluster {cluster_id}: {e}")
        # Fallback: keep first entry with frequency metadata
        fallback = cluster_entries[0].copy()
        fallback["frequency"] = len(cluster_entries)
        fallback["cluster_id"] = cluster_id
        return [fallback]

def optimize_context():
    """Main optimization workflow"""

    print("=== Context Optimizer Started ===\n")

    # 1. Backup
    backup_context()

    # 2. Load
    entries = load_context()
    if not entries:
        print("No entries to optimize")
        return

    # 3. Cluster
    cluster_map = cluster_entries(entries)

    # 4. Gemini consolidation par cluster
    optimized_entries = []

    for cluster_id, centries in cluster_map.items():
        consolidated = gemini_consolidate_cluster(centries, cluster_id)
        optimized_entries.extend(consolidated)

    # 5. Build graph relations
    print(f"\nBuilding graph relations...")
    # TODO: Intelligent graph building based on keywords/themes similarity

    # 6. Save optimized
    output = {
        "entries": optimized_entries,
        "metadata": {
            "total_entries": len(optimized_entries),
            "original_count": len(entries),
            "compression_ratio": f"{len(entries) / len(optimized_entries):.2f}x",
            "last_optimized": datetime.now().isoformat(),
            "clusters_found": len(cluster_map)
        }
    }

    with open(CONTEXT_OPTIMIZED, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Optimization Complete ===")
    print(f"Original: {len(entries)} entries")
    print(f"Optimized: {len(optimized_entries)} entries")
    print(f"Compression: {output['metadata']['compression_ratio']}")
    print(f"Output: {CONTEXT_OPTIMIZED}")

if __name__ == "__main__":
    optimize_context()
