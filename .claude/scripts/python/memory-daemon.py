#!/usr/bin/env python3
"""Memory Daemon - Clustering Sémantique + Gemini Consolidation"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import numpy as np
from dateutil import parser as dateparser
import requests

# Config
CLAUDE_DIR = Path.home() / ".claude"
PROJECT_DIR = Path("/home/pilote/projet/primaire/AGI")
CONTEXT_DIR = PROJECT_DIR / ".claude"
SCRIPT_DIR = PROJECT_DIR / ".claude/scripts/python"
LOG_FILE = SCRIPT_DIR / "daemon.log"

# Load models (1x au startup)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Config OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# Gemini 2.5 Flash Lite = ultra cheap + rapide + excellent pour consolidation
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"

def log(msg):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def parse_conversation_file(jsonl_file):
    """Parse UN fichier conversation → events"""
    events = []

    try:
        with open(jsonl_file) as f:
            for line in f:
                try:
                    msg = json.loads(line)

                    # Parse timestamp
                    msg_ts_str = msg.get("timestamp", msg.get("snapshot", {}).get("timestamp", ""))
                    if not msg_ts_str:
                        continue

                    try:
                        if isinstance(msg_ts_str, str):
                            msg_ts = dateparser.parse(msg_ts_str).timestamp()
                        else:
                            msg_ts = float(msg_ts_str)
                    except:
                        continue

                    # Garde messages importants
                    msg_type = msg.get("type", "")
                    if msg_type in ["user", "assistant"]:
                        content = str(msg.get("message", {}).get("content", ""))

                        # Filter noise
                        if any(skip in content for skip in ["Bash output", "Read tool", "✓ Terminé", "system-reminder"]):
                            continue

                        # Garde importants
                        if len(content) > 50:  # Ignore messages trop courts
                            events.append({
                                "timestamp": msg_ts,
                                "type": msg_type,
                                "content": content[:500]  # Limite 500 chars
                            })
                except:
                    continue
    except Exception as e:
        log(f"Error parsing {jsonl_file.name}: {e}")

    return events

def cluster_events(events):
    """Clustering sémantique DBSCAN"""

    if len(events) < 5:
        log("Too few events for clustering, keeping all")
        return events

    # Embeddings
    log(f"Embedding {len(events)} events...")
    texts = [e["content"] for e in events]
    embeddings = embedding_model.encode(texts, batch_size=32, show_progress_bar=False)

    # Clustering
    log("Clustering...")
    clusters = DBSCAN(eps=0.6, min_samples=2).fit_predict(embeddings)

    # Consolidation
    consolidated = []
    cluster_ids = set(clusters)

    log(f"Found {len(cluster_ids)} clusters (including outliers)")

    for cluster_id in cluster_ids:
        cluster_events = [events[i] for i, c in enumerate(clusters) if c == cluster_id]
        cluster_embeds = embeddings[clusters == cluster_id]

        if cluster_id == -1:
            # Outliers = tous importants
            consolidated.extend(cluster_events)
            log(f"  Outliers: {len(cluster_events)} events (kept all)")
        else:
            # Garde centroïde + metadata
            centroid = np.mean(cluster_embeds, axis=0)
            distances = [np.linalg.norm(e - centroid) for e in cluster_embeds]
            closest_idx = np.argmin(distances)

            entry = cluster_events[closest_idx].copy()
            entry["frequency"] = len(cluster_events)
            entry["cluster_size"] = len(cluster_events)
            entry["cluster_id"] = int(cluster_id)

            consolidated.append(entry)
            log(f"  Cluster {cluster_id}: {len(cluster_events)} events → 1 representative")

    log(f"Consolidated: {len(events)} → {len(consolidated)} entries")
    return consolidated

def gemini_format_with_retry(consolidated_entries, max_retries=5):
    """Format final via Gemini avec retry sur rate limit"""

    log(f"Formatting {len(consolidated_entries)} entries via Gemini...")

    # Si trop peu d'entries, pas besoin Gemini
    if len(consolidated_entries) < 10:
        log("Too few entries for Gemini, keeping as-is")
        return {
            "entries": consolidated_entries,
            "last_processed_timestamp": max(e["timestamp"] for e in consolidated_entries),
            "metadata": {"total_entries": len(consolidated_entries)}
        }

    for attempt in range(max_retries):
        try:
            prompt = f"""CONSOLIDE {len(consolidated_entries)} ENTRIES EN MÉMOIRE OPTIMISÉE:

{json.dumps(consolidated_entries, indent=2)}

OBJECTIF: Context.json = RAG via Grep (recherche rapide)

RÈGLES STRICTES:
1. Phrases 10-20 mots UNIQUEMENT (grep-friendly)
2. Keywords explicites (pas métaphores)
3. Fusion doublons sémantiques → 1 entry
4. Connexions claires (supersedes/caused_by/related_to)
5. Importance = frequency*0.3 + recency*0.4 + connections*0.3
6. Type précis (pattern/decision/action/discovery/error)
7. Status (active/obsolete/deprecated)

ANTI-PATTERNS:
- Phrases vagues ("système fonctionne bien")
- Doublons ("créer agent" + "agent créé")
- Détails inutiles (tool outputs, logs)

OUTPUT JSON STRICT:
{{
  "entries": [
    {{"id": "action_001", "content": "Agent writor créé tools Read Write Edit",
      "type": "pattern|decision|action|discovery|error", "frequency": N, "importance": 0-1,
      "connections": {{"supersedes": [], "caused_by": [], "related_to": []}},
      "timestamp": "ISO8601", "status": "active", "keywords": ["agent", "writor"]}}
  ],
  "last_processed_timestamp": {max(e["timestamp"] for e in consolidated_entries)},
  "metadata": {{"total_entries": N, "last_run": "{datetime.now().isoformat()}"}}
}}"""

            # OpenRouter API call
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/pilote/AGI-memory",
                    "X-Title": "AGI Memory Daemon"
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

            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]

            result = json.loads(result_text)
            log(f"✓ Gemini returned {len(result.get('entries', []))} entries")
            return result

        except Exception as e:
            error_str = str(e)

            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries - 1:
                    delay = 6 * (2 ** attempt)
                    log(f"Rate limit hit, retry {attempt+1}/{max_retries} in {delay}s...")
                    time.sleep(delay)
                    continue

            log(f"ERROR Gemini: {e}")
            return {
                "entries": consolidated_entries,
                "last_processed_timestamp": max(e["timestamp"] for e in consolidated_entries),
                "metadata": {"total_entries": len(consolidated_entries), "error": str(e)}
            }

    log("Max retries reached, using fallback")
    return {
        "entries": consolidated_entries,
        "last_processed_timestamp": max(e["timestamp"] for e in consolidated_entries),
        "metadata": {"total_entries": len(consolidated_entries), "error": "max_retries"}
    }

def process_file(jsonl_file):
    """Traite UN fichier 29MB → entries consolidées"""

    log(f"Processing {jsonl_file.name}...")

    # 1. Parse
    events = parse_conversation_file(jsonl_file)
    if not events:
        log("  No events found")
        return []

    log(f"  Parsed {len(events)} events")

    # 2. Clustering
    consolidated = cluster_events(events)

    # 3. Gemini format (avec retry rate limit)
    formatted = gemini_format_with_retry(consolidated)

    return formatted["entries"]

def main():
    log("=== Memory Daemon Started ===")

    try:
        convs_dir = CLAUDE_DIR / "projects" / "-home-pilote-projet-primaire-AGI"

        # Load context
        context_file = CONTEXT_DIR / "context.json"
        if context_file.exists():
            with open(context_file) as f:
                context = json.load(f)
        else:
            context = {"entries": [], "processed_files": []}

        processed_files = context.get("processed_files", [])
        all_entries = context.get("entries", [])

        # Trouver fichiers conversations par modification time
        all_jsonl = sorted(convs_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime)

        if len(all_jsonl) == 0:
            log("No conversations found")
            return

        # SKIP le plus récent (conversation actuelle)
        if len(all_jsonl) > 1:
            current_conversation = all_jsonl[-1]
            files_to_process = all_jsonl[:-1]  # Tous sauf le dernier
            log(f"Current conversation (skipped): {current_conversation.name}")
        else:
            log("Only 1 conversation found (current), nothing to process")
            return

        # Process anciennes conversations SEULEMENT
        new_files = 0
        for jsonl_file in files_to_process:
            file_id = jsonl_file.stem

            # Skip si déjà traité
            if file_id in processed_files:
                continue

            # Process fichier
            entries = process_file(jsonl_file)

            if entries:
                # Merge dans context.json
                all_entries.extend(entries)
                processed_files.append(file_id)
                new_files += 1

                # Delete source JSONL (cleanup)
                try:
                    jsonl_file.unlink()
                    log(f"  Deleted source {jsonl_file.name} (processed)")
                except Exception as e:
                    log(f"  Warning: Could not delete {jsonl_file.name}: {e}")

        if new_files == 0:
            log("No new files to process")
            return

        # Save context.json
        final_context = {
            "entries": all_entries,
            "processed_files": processed_files,
            "last_run": datetime.now().isoformat(),
            "metadata": {
                "total_entries": len(all_entries),
                "total_files": len(processed_files)
            }
        }

        with open(context_file, "w") as f:
            json.dump(final_context, f, indent=2)

        log(f"=== Success: Processed {new_files} files, {len(all_entries)} total entries ===")

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
