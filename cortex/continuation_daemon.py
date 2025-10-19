#!/usr/bin/env python3
"""
============================================================================
Continuation Daemon - Auto-reinvoke Sonnet via LISTEN/NOTIFY
============================================================================
Description: Daemon qui écoute les événements PostgreSQL NOTIFY et
             réinvoque automatiquement Sonnet 4.5 pour continuer le workflow
             - LISTEN sur batch_complete, task_completed, critical_error
             - <50ms latency (vs 2000ms polling)
             - Auto-reinvoke claude code avec session context
             - State persistence via agi_sessions
             - Graceful shutdown avec cleanup
Author: AGI System
Date: 2025-10-18
============================================================================
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import asyncpg

# ============================================================================
# Configuration
# ============================================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "agi_db",
    "user": "agi_user",
    "password": "agi_password"
}

CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")
CLAUDE_PROJECT_PATH = "/home/pilote/projet/agi"
CONTINUATION_ENABLED = os.getenv("CONTINUATION_ENABLED", "true").lower() == "true"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("continuation_daemon")

# ============================================================================
# Session Manager
# ============================================================================
class SessionManager:
    """Gère les sessions AGI (état de Sonnet)"""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_session(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Récupère une session par ID"""
        row = await self.conn.fetchrow(
            """
            SELECT session_name, current_phase, context, launched_tasks,
                   next_action, status, created_at, resumed_at
            FROM agi_sessions
            WHERE id = $1
            """,
            session_id
        )

        if not row:
            return None

        return {
            "id": session_id,
            "session_name": row["session_name"],
            "current_phase": row["current_phase"],
            "context": row["context"],
            "launched_tasks": row["launched_tasks"],
            "next_action": row["next_action"],
            "status": row["status"],
            "created_at": row["created_at"],
            "resumed_at": row["resumed_at"]
        }

    async def update_session_status(
        self,
        session_id: uuid.UUID,
        status: str,
        phase: Optional[str] = None
    ):
        """Met à jour le status d'une session"""
        if phase:
            await self.conn.execute(
                """
                UPDATE agi_sessions
                SET status = $2, current_phase = $3, resumed_at = NOW()
                WHERE id = $1
                """,
                session_id,
                status,
                phase
            )
        else:
            await self.conn.execute(
                """
                UPDATE agi_sessions
                SET status = $2, resumed_at = NOW()
                WHERE id = $1
                """,
                session_id,
                status
            )

    async def create_session(
        self,
        session_name: str,
        phase: str,
        context: Dict[str, Any]
    ) -> uuid.UUID:
        """Crée une nouvelle session"""
        session_id = await self.conn.fetchval(
            """
            INSERT INTO agi_sessions (session_name, current_phase, context, status)
            VALUES ($1, $2, $3, 'active')
            RETURNING id
            """,
            session_name,
            phase,
            json.dumps(context)
        )
        return session_id

# ============================================================================
# Batch Result Aggregator
# ============================================================================
async def aggregate_batch_results(
    conn: asyncpg.Connection,
    batch_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Agrège les résultats de toutes les tâches d'un batch.
    Returns: {"tasks": [...], "success_count": N, "failed_count": M, ...}
    """
    tasks = await conn.fetch(
        """
        SELECT id, task_type, status, result, error,
               started_at, completed_at,
               EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
        FROM worker_tasks
        WHERE batch_id = $1
        ORDER BY created_at ASC
        """,
        batch_id
    )

    results = []
    success_count = 0
    failed_count = 0

    for task in tasks:
        task_result = {
            "task_id": str(task["id"]),
            "task_type": task["task_type"],
            "status": task["status"],
            "duration_seconds": task["duration_seconds"]
        }

        if task["status"] == "success":
            success_count += 1
            task_result["result"] = task["result"]
        elif task["status"] in ("failed", "timeout"):
            failed_count += 1
            task_result["error"] = task["error"]

        results.append(task_result)

    return {
        "batch_id": str(batch_id),
        "total_tasks": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "tasks": results
    }

# ============================================================================
# Continuation Executor
# ============================================================================
async def execute_continuation(
    session_id: uuid.UUID,
    batch_id: uuid.UUID,
    context: Dict[str, Any],
    batch_results: Dict[str, Any]
):
    """
    Réinvoque Claude Code avec le contexte de session + résultats du batch.
    Crée un prompt intelligent qui dit à Sonnet:
    - Quelle était sa mission
    - Quels agents ont terminé
    - Quels résultats ils ont produit
    - Quelle est la prochaine étape
    """
    logger.info(f"Executing continuation for session {session_id}, batch {batch_id}")

    # Construire le prompt de continuation
    prompt = f"""# CONTINUATION AUTOMATIQUE - Session {session_id}

## Contexte de la session
{json.dumps(context, indent=2)}

## Batch terminé: {batch_id}
- Total tâches: {batch_results['total_tasks']}
- Succès: {batch_results['success_count']}
- Échecs: {batch_results['failed_count']}

## Résultats détaillés
"""

    for task in batch_results["tasks"]:
        prompt += f"\n### Tâche {task['task_id']} ({task['task_type']}) - {task['status'].upper()}\n"
        if task["status"] == "success":
            result_preview = str(task.get("result", ""))[:500]
            prompt += f"**Résultat:** {result_preview}\n"
        else:
            prompt += f"**Erreur:** {task.get('error', 'Unknown error')}\n"

    prompt += """
## Ta mission maintenant
Tu es Sonnet 4.5, l'orchestrateur principal du système AGI. Les agents que tu avais lancés ont terminé leur travail.

**Analyse les résultats ci-dessus et décide de la prochaine étape:**
1. Si tous les agents ont réussi → passe à la phase suivante
2. Si certains ont échoué → analyse les erreurs et décide si retry ou pivot
3. Si le workflow est terminé → marque la session comme complétée

**IMPORTANT:**
- Utilise `mcp__agi_tools__pg_query` pour lire l'état actuel
- Utilise `mcp__agi_tools__pg_execute` pour mettre à jour la session
- Lance de nouveaux agents via `mcp__agi_tools__launch_agent` si nécessaire
- Stocke les patterns découverts via `mcp__agi_tools__memory_store`

Continue le workflow là où tu l'avais laissé.
"""

    # Exécuter Claude Code
    cmd = [
        CLAUDE_CLI_PATH,
        "--print",
        "--no-color"
    ]

    try:
        logger.info(f"Invoking Claude Code for continuation...")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=CLAUDE_PROJECT_PATH
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=prompt.encode("utf-8")),
            timeout=600  # 10min max
        )

        if process.returncode == 0:
            output = stdout.decode("utf-8", errors="replace")
            logger.info(f"Continuation SUCCESS:\n{output[:500]}...")

            # Stocker le résultat de continuation dans la session
            async with await asyncpg.connect(**DB_CONFIG) as conn:
                await conn.execute(
                    """
                    UPDATE agi_sessions
                    SET metadata = metadata || jsonb_build_object(
                        'last_continuation', NOW(),
                        'continuation_output', $2
                    )
                    WHERE id = $1
                    """,
                    session_id,
                    output[:5000]  # Truncate si trop long
                )

        else:
            error = stderr.decode("utf-8", errors="replace")
            logger.error(f"Continuation FAILED: {error}")

    except asyncio.TimeoutError:
        logger.error(f"Continuation TIMEOUT after 10 minutes")

    except Exception as e:
        logger.exception(f"Continuation ERROR: {e}")

# ============================================================================
# Event Handlers
# ============================================================================
async def handle_batch_complete(payload: Dict[str, Any]):
    """
    Handler pour l'événement batch_complete.
    Triggered par le trigger PostgreSQL quand toutes les tâches d'un batch sont terminées.
    """
    batch_id = uuid.UUID(payload["batch_id"])
    session_id_str = payload.get("session_id")

    if not session_id_str:
        logger.warning(f"Batch {batch_id} has no session_id, skipping continuation")
        return

    session_id = uuid.UUID(session_id_str.strip('"'))  # Remove quotes si présentes
    context = payload.get("context", {})

    logger.info(f"Batch {batch_id} completed (session: {session_id})")

    if not CONTINUATION_ENABLED:
        logger.info("Continuation disabled, skipping auto-reinvoke")
        return

    # Récupérer les résultats du batch
    async with await asyncpg.connect(**DB_CONFIG) as conn:
        batch_results = await aggregate_batch_results(conn, batch_id)

        # Vérifier si la session existe et est active
        session_mgr = SessionManager(conn)
        session = await session_mgr.get_session(session_id)

        if not session:
            logger.warning(f"Session {session_id} not found, skipping continuation")
            return

        if session["status"] != "active":
            logger.info(f"Session {session_id} status is {session['status']}, skipping continuation")
            return

        # Marquer la session comme "resuming"
        await session_mgr.update_session_status(session_id, "resuming")

    # Exécuter la continuation (réinvoquer Sonnet)
    await execute_continuation(session_id, batch_id, context, batch_results)

async def handle_task_completed(payload: Dict[str, Any]):
    """Handler pour task_completed (informational, pas de continuation)"""
    task_id = payload["task_id"]
    status = payload["status"]
    duration = payload.get("duration_seconds", 0)

    logger.info(f"Task {task_id} completed: {status} ({duration:.1f}s)")

async def handle_critical_error(payload: Dict[str, Any]):
    """Handler pour critical_error (alerting)"""
    task_id = payload["task_id"]
    agent_type = payload["agent_type"]
    error = payload["error"]

    logger.error(f"CRITICAL ERROR - Task {task_id} (agent: {agent_type}): {error}")

    # TODO: Envoyer une alerte (email, Slack, etc.)

async def handle_circuit_breaker_changed(payload: Dict[str, Any]):
    """Handler pour circuit_breaker_changed (alerting)"""
    agent_type = payload["agent_type"]
    old_status = payload["old_status"]
    new_status = payload["new_status"]
    reason = payload.get("reason", "")

    logger.warning(f"Circuit breaker {agent_type}: {old_status} -> {new_status} ({reason})")

    # TODO: Envoyer une alerte si status = 'open'

# ============================================================================
# LISTEN Loop
# ============================================================================
async def listen_loop(shutdown_event: asyncio.Event):
    """
    Boucle principale qui LISTEN sur les channels PostgreSQL.
    Dispatche les événements aux handlers appropriés.
    """
    logger.info("Starting LISTEN loop...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # LISTEN sur tous les channels
        await conn.add_listener("batch_complete", lambda conn, pid, channel, payload: asyncio.create_task(handle_batch_complete(json.loads(payload))))
        await conn.add_listener("task_completed", lambda conn, pid, channel, payload: asyncio.create_task(handle_task_completed(json.loads(payload))))
        await conn.add_listener("critical_error", lambda conn, pid, channel, payload: asyncio.create_task(handle_critical_error(json.loads(payload))))
        await conn.add_listener("circuit_breaker_changed", lambda conn, pid, channel, payload: asyncio.create_task(handle_circuit_breaker_changed(json.loads(payload))))

        logger.info("LISTEN active on: batch_complete, task_completed, critical_error, circuit_breaker_changed")

        # Attendre shutdown
        await shutdown_event.wait()

    finally:
        # Cleanup
        await conn.remove_listener("batch_complete", lambda conn, pid, channel, payload: None)
        await conn.remove_listener("task_completed", lambda conn, pid, channel, payload: None)
        await conn.remove_listener("critical_error", lambda conn, pid, channel, payload: None)
        await conn.remove_listener("circuit_breaker_changed", lambda conn, pid, channel, payload: None)
        await conn.close()

        logger.info("LISTEN loop stopped")

# ============================================================================
# Main Entry Point
# ============================================================================
async def main():
    """Point d'entrée principal"""
    logger.info("Continuation daemon starting...")

    shutdown_event = asyncio.Event()

    # Handle signals
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received shutdown signal")
        shutdown_event.set()

    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    # Run LISTEN loop
    await listen_loop(shutdown_event)

    logger.info("Continuation daemon stopped")

if __name__ == "__main__":
    asyncio.run(main())
