#!/usr/bin/env python3
"""
============================================================================
Check and Continue - Helper pour workflow Sonnet
============================================================================
Description: Script que Sonnet appelle AU DÉBUT de chaque invocation
             pour vérifier si des agents ont terminé et continuer le workflow

Usage:
    1. Sonnet lance: python3 cortex/check_and_continue.py
    2. Script check si batches terminés
    3. Si oui → affiche résultats + prochaine action
    4. Si non → affiche status + "attendre"
============================================================================
"""

import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, '/home/pilote/projet/agi/cortex')

from agi_client import AGIClient, TaskStatus, SessionStatus

async def check_active_sessions():
    """Check les sessions actives et affiche leur status"""
    async with AGIClient() as client:
        # Récupérer sessions actives
        conn = client.conn
        sessions = await conn.fetch(
            """
            SELECT id, session_name, current_phase, next_action,
                   context, launched_tasks, created_at
            FROM agi_sessions
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT 5
            """
        )

        if not sessions:
            print("✅ Aucune session active. Sonnet peut démarrer nouveau workflow.")
            return

        print(f"📋 {len(sessions)} session(s) active(s) trouvée(s):\n")

        for sess in sessions:
            print(f"{'=' * 70}")
            print(f"Session: {sess['session_name']}")
            print(f"ID: {sess['id']}")
            print(f"Phase: {sess['current_phase']}")
            print(f"Créée: {sess['created_at']}")
            print()

            # Check les tasks de cette session
            launched_tasks = sess['launched_tasks'] or []
            if not launched_tasks:
                print("   ⚠️  Aucune task lancée dans cette session")
                continue

            print(f"   📊 {len(launched_tasks)} task(s) lancée(s)")

            # Récupérer status des tasks
            tasks_status = await conn.fetch(
                """
                SELECT status, COUNT(*) as count
                FROM worker_tasks
                WHERE id = ANY($1)
                GROUP BY status
                """,
                launched_tasks
            )

            pending = 0
            running = 0
            success = 0
            failed = 0

            for row in tasks_status:
                count = row['count']
                status = row['status']
                if status == 'pending':
                    pending = count
                elif status == 'running':
                    running = count
                elif status == 'success':
                    success = count
                elif status in ('failed', 'timeout'):
                    failed = count

            print(f"   • Pending: {pending}")
            print(f"   • Running: {running}")
            print(f"   • Success: {success}")
            print(f"   • Failed: {failed}")
            print()

            # Déterminer action
            if pending + running == 0:
                # Tous terminés!
                print("   ✅ BATCH TERMINÉ!")
                print(f"   📝 Prochaine action: {sess['next_action']}")
                print()

                # Afficher résultats
                results = await conn.fetch(
                    """
                    SELECT id, task_type, status, result, error
                    FROM worker_tasks
                    WHERE id = ANY($1)
                    ORDER BY created_at ASC
                    """,
                    launched_tasks
                )

                print("   📊 Résultats détaillés:")
                for i, task in enumerate(results, 1):
                    status_emoji = "✅" if task['status'] == 'success' else "❌"
                    print(f"      {i}. {status_emoji} {task['task_type']} - {task['status']}")
                    if task['status'] == 'success' and task['result']:
                        result_preview = str(task['result'])[:100]
                        print(f"         → {result_preview}...")
                    elif task['error']:
                        print(f"         ⚠️  {task['error'][:100]}...")

                print()
                print(f"   👉 SONNET: Continue avec '{sess['next_action']}'")

            else:
                # Encore en cours
                total = pending + running + success + failed
                done = success + failed
                pct = (done / total * 100) if total > 0 else 0
                print(f"   ⏳ En cours... {done}/{total} ({pct:.0f}%)")
                print(f"   👉 SONNET: Attendre ou faire autre chose")

            print()

async def main():
    """Point d'entrée"""
    print("\n" + "=" * 70)
    print("🔍 CHECK AND CONTINUE - Vérification sessions actives")
    print("=" * 70 + "\n")

    await check_active_sessions()

    print("=" * 70)
    print()

if __name__ == "__main__":
    asyncio.run(main())
