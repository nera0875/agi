#!/usr/bin/env python3
"""
============================================================================
Sonnet Workflow Helper - SOLUTION FIABLE pour workflow non-bloquant
============================================================================
Description: Helper qui résout le problème du timeout 2min de Claude Code

             STRATÉGIE HYBRID:
             1. Tâches rapides (<2min) → Attendre directement
             2. Tâches longues (>2min) → Session + Check-on-Restart
             3. Auto-detect du meilleur pattern

             Sonnet appelle UNE fonction: workflow_manager()
============================================================================
"""

import asyncio
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable

sys.path.insert(0, '/home/pilote/projet/agi/cortex')

from agi_client import AGIClient, TaskStatus, SessionStatus
import uuid

# ============================================================================
# Configuration
# ============================================================================
QUICK_TASK_THRESHOLD = 90  # 90s = considéré "rapide"
POLL_INTERVAL = 10  # Check every 10s
MAX_WAIT_TIME = 110  # Max 110s wait (reste 10s de marge sur 2min)

# ============================================================================
# Workflow Manager
# ============================================================================

@dataclass
class WorkflowTask:
    """Définition d'une tâche"""
    agent_type: str
    prompt: str
    estimated_duration: int = 60  # secondes

class SonnetWorkflow:
    """
    Manager de workflow pour Sonnet.

    Usage simple:
        wf = SonnetWorkflow()

        # 1. Check si workflow en attente
        if wf.has_pending_work():
            wf.resume_pending_work()
        else:
            # 2. Lancer nouveau workflow
            wf.start_workflow("my_feature", [
                WorkflowTask("research-agent", "Research X"),
                WorkflowTask("code-agent", "Implement Y")
            ])
    """

    def __init__(self):
        self.client: Optional[AGIClient] = None
        self.session_id: Optional[uuid.UUID] = None

    async def __aenter__(self):
        self.client = await AGIClient().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def has_pending_work(self) -> bool:
        """Check si des sessions actives avec batches terminés existent"""
        conn = self.client.conn

        count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM agi_sessions s
            WHERE s.status = 'active'
              AND EXISTS (
                  SELECT 1
                  FROM unnest(s.launched_tasks) task_id
                  JOIN worker_tasks t ON t.id = task_id
                  GROUP BY s.id
                  HAVING COUNT(*) FILTER (WHERE t.status IN ('pending', 'running')) = 0
              )
            """
        )

        return count > 0

    async def get_pending_sessions(self):
        """Récupère sessions avec batches terminés"""
        conn = self.client.conn

        sessions = await conn.fetch(
            """
            SELECT
                s.id,
                s.session_name,
                s.current_phase,
                s.next_action,
                s.context,
                s.launched_tasks,
                (
                    SELECT COUNT(*)
                    FROM unnest(s.launched_tasks) task_id
                    JOIN worker_tasks t ON t.id = task_id
                    WHERE t.status = 'success'
                ) as success_count,
                (
                    SELECT COUNT(*)
                    FROM unnest(s.launched_tasks) task_id
                    JOIN worker_tasks t ON t.id = task_id
                    WHERE t.status IN ('failed', 'timeout')
                ) as failed_count
            FROM agi_sessions s
            WHERE s.status = 'active'
              AND EXISTS (
                  SELECT 1
                  FROM unnest(s.launched_tasks) task_id
                  JOIN worker_tasks t ON t.id = task_id
                  GROUP BY s.id
                  HAVING COUNT(*) FILTER (WHERE t.status IN ('pending', 'running')) = 0
              )
            ORDER BY s.created_at ASC
            LIMIT 1
            """
        )

        return sessions

    async def resume_pending_work(self):
        """Reprend une session en attente"""
        sessions = await self.get_pending_sessions()

        if not sessions:
            print("ℹ️  Aucune session en attente")
            return False

        sess = sessions[0]

        print(f"\n{'=' * 70}")
        print(f"📋 REPRISE SESSION: {sess['session_name']}")
        print(f"{'=' * 70}")
        print(f"Phase: {sess['current_phase']}")
        print(f"Next action: {sess['next_action']}")
        print(f"Success: {sess['success_count']}, Failed: {sess['failed_count']}")
        print()

        # Récupérer résultats
        conn = self.client.conn
        results = await conn.fetch(
            """
            SELECT id, task_type, status, result, error
            FROM worker_tasks
            WHERE id = ANY($1)
            ORDER BY created_at ASC
            """,
            sess['launched_tasks']
        )

        print("📊 Résultats des agents:")
        for i, r in enumerate(results, 1):
            status_emoji = "✅" if r['status'] == 'success' else "❌"
            print(f"  {i}. {status_emoji} {r['task_type']} - {r['status']}")

            if r['result']:
                # Afficher preview du résultat
                result_str = str(r['result'])[:200]
                print(f"      → {result_str}...")

        print()
        print(f"👉 SONNET: Continue avec '{sess['next_action']}'")
        print(f"{'=' * 70}\n")

        return True

    async def start_workflow(
        self,
        workflow_name: str,
        tasks: List[WorkflowTask],
        on_complete: Optional[Callable] = None,
        next_action_description: str = "analyze_results_and_continue"
    ):
        """
        Lance un workflow avec stratégie automatique.

        STRATÉGIE:
        - Si total_duration < 90s → Attendre directement
        - Sinon → Session + return pour continuation
        """
        print(f"\n{'=' * 70}")
        print(f"🚀 DÉMARRAGE WORKFLOW: {workflow_name}")
        print(f"{'=' * 70}")
        print(f"Tasks: {len(tasks)}")

        # Calculer durée totale estimée
        total_duration = sum(t.estimated_duration for t in tasks)
        print(f"Durée estimée: {total_duration}s")

        # Créer session
        session_id = await self.client.create_session(
            workflow_name,
            "execution_phase",
            context={
                "workflow_name": workflow_name,
                "task_count": len(tasks),
                "estimated_duration": total_duration
            }
        )
        self.session_id = session_id

        print(f"Session créée: {session_id}")

        # Lancer batch
        batch_tasks = [(t.agent_type, t.prompt) for t in tasks]
        batch_id = await self.client.launch_agents_batch(
            batch_tasks,
            priority=70,
            session_id=session_id,
            wait_for_completion=False
        )

        print(f"Batch lancé: {batch_id}")
        print()

        # Stratégie: Rapide ou Long?
        if total_duration < QUICK_TASK_THRESHOLD:
            # STRATÉGIE 1: Attendre (tâches rapides)
            print("⚡ Tâches rapides → Attente directe")
            return await self._wait_and_complete(batch_id, on_complete)
        else:
            # STRATÉGIE 2: Session + Return (tâches longues)
            print("⏳ Tâches longues → Session sauvegardée")
            await self.client.update_session(
                session_id,
                next_action=next_action_description,
                context={
                    "batch_id": str(batch_id),
                    "workflow_name": workflow_name
                }
            )

            print(f"\n{'=' * 70}")
            print("💾 SESSION SAUVEGARDÉE")
            print(f"{'=' * 70}")
            print(f"Session ID: {session_id}")
            print(f"Batch ID: {batch_id}")
            print(f"Next action: {next_action_description}")
            print()
            print("👉 SONNET: Relance cette conversation pour continuer")
            print(f"{'=' * 70}\n")

            return None

    async def _wait_and_complete(self, batch_id, on_complete):
        """Attendre completion avec timeout"""
        print("⏳ Attente des résultats...")

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > MAX_WAIT_TIME:
                print(f"\n⚠️  Timeout {MAX_WAIT_TIME}s atteint")
                print("💾 Session sauvegardée, relance pour continuer")
                return None

            # Check status
            status = await self.client.get_batch_status(batch_id)

            done = status.success_count + status.failed_count
            total = status.total_tasks
            pct = (done / total * 100) if total > 0 else 0

            print(f"  Progress: {done}/{total} ({pct:.0f}%) - {elapsed:.0f}s elapsed", end='\r')

            if status.is_complete:
                print(f"\n✅ Batch terminé en {elapsed:.1f}s!")

                # Afficher résultats
                print("\n📊 Résultats:")
                for i, r in enumerate(status.results, 1):
                    status_emoji = "✅" if r.status == TaskStatus.SUCCESS else "❌"
                    print(f"  {i}. {status_emoji} {r.status}")

                # Callback si fourni
                if on_complete:
                    print("\n🔄 Exécution callback...")
                    await on_complete(status.results)

                # Marquer session comme completed
                await self.client.update_session(
                    self.session_id,
                    status=SessionStatus.COMPLETED
                )

                return status.results

            await asyncio.sleep(POLL_INTERVAL)

# ============================================================================
# Helper Functions (API simple pour Sonnet)
# ============================================================================

async def quick_start_workflow(
    workflow_name: str,
    tasks: List[Tuple[str, str]],  # [(agent_type, prompt), ...]
    estimated_durations: Optional[List[int]] = None
):
    """
    API ultra-simple pour Sonnet.

    Usage:
        results = await quick_start_workflow(
            "deploy_oauth",
            [
                ("research-agent", "Research OAuth2"),
                ("code-agent", "Implement OAuth2")
            ],
            estimated_durations=[60, 120]  # secondes
        )
    """
    # Convert to WorkflowTask
    workflow_tasks = []
    for i, (agent_type, prompt) in enumerate(tasks):
        duration = estimated_durations[i] if estimated_durations else 60
        workflow_tasks.append(WorkflowTask(agent_type, prompt, duration))

    async with SonnetWorkflow() as wf:
        # Check pending first
        if await wf.has_pending_work():
            print("📋 Session en attente détectée!")
            await wf.resume_pending_work()
            return None

        # Start new
        return await wf.start_workflow(workflow_name, workflow_tasks)

# ============================================================================
# CLI pour testing
# ============================================================================

async def demo():
    """Demo du workflow"""

    # Test 1: Tâches rapides (attente directe)
    print("\n=== TEST 1: Tâches rapides ===")

    async with SonnetWorkflow() as wf:
        results = await wf.start_workflow(
            "quick_test",
            [
                WorkflowTask("research-agent", "Quick research", 30),
                WorkflowTask("code-agent", "Quick code", 30)
            ]
        )

        if results:
            print(f"✅ Résultats reçus: {len(results)} tasks")
        else:
            print("⏳ Session sauvegardée")

if __name__ == "__main__":
    asyncio.run(demo())
