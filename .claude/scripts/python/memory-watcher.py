#!/usr/bin/env python3
"""Memory Watcher - Déclenche daemon quand nouvelle conversation créée

TRIGGER: Nouveau fichier .jsonl créé dans ~/.claude/projects/
ACTION: Lance memory-daemon.py immédiatement
"""

import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

WATCH_DIR = Path.home() / ".claude/projects/-home-pilote-projet-primaire-AGI"
DAEMON_SCRIPT = Path("/home/pilote/projet/primaire/AGI/.claude/scripts/python/memory-daemon.py")
LOG_FILE = Path("/home/pilote/projet/primaire/AGI/.claude/scripts/python/watcher.log")

def log(msg):
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

class ConversationHandler(FileSystemEventHandler):
    def __init__(self):
        self.processing = False
        self.last_trigger = 0

    def on_created(self, event):
        """Déclenché quand nouveau fichier .jsonl créé = ancienne conversation terminée"""

        if event.is_directory:
            return

        if not event.src_path.endswith('.jsonl'):
            return

        # Debounce: éviter triggers multiples (5s min entre déclenchements)
        now = time.time()
        if now - self.last_trigger < 5:
            log(f"Debounce: skip {Path(event.src_path).name}")
            return

        self.last_trigger = now

        # Attendre que nouveau fichier soit stable
        time.sleep(2)

        new_file = Path(event.src_path)
        log(f"Nouvelle conversation créée: {new_file.name}")
        log("→ Ancienne conversation terminée, lancement daemon...")

        # Lancer daemon
        if not self.processing:
            self.processing = True
            try:
                log("Lancement memory-daemon.py...")
                result = subprocess.run(
                    ["python3", str(DAEMON_SCRIPT)],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 min max
                )

                if result.returncode == 0:
                    log("✓ Daemon complété")
                else:
                    log(f"✗ Daemon erreur: {result.stderr[:200]}")

            except subprocess.TimeoutExpired:
                log("✗ Daemon timeout (>10min)")
            except Exception as e:
                log(f"✗ Daemon exception: {e}")
            finally:
                self.processing = False
        else:
            log("Daemon déjà en cours, skip")

def main():
    log("=== Memory Watcher Started ===")
    log(f"Watching: {WATCH_DIR}")

    if not WATCH_DIR.exists():
        log(f"ERROR: Directory not found: {WATCH_DIR}")
        return

    event_handler = ConversationHandler()
    observer = Observer()
    observer.schedule(event_handler, str(WATCH_DIR), recursive=False)
    observer.start()

    log("Watcher active, waiting for new conversations...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Stopping watcher...")
        observer.stop()
        observer.join()
        log("=== Memory Watcher Stopped ===")

if __name__ == "__main__":
    main()
