#!/usr/bin/env python3
"""
============================================================================
Worker Pool - Process Isolation avec FOR UPDATE SKIP LOCKED
============================================================================
Description: Pool de workers asynchrones qui exécutent les tâches en parallèle
             - 10 workers par défaut (configurable)
             - FOR UPDATE SKIP LOCKED pour éviter race conditions
             - Exécution via subprocess (claude --print)
             - Timeout handling avec graceful termination
             - Circuit breaker integration
             - Dead letter queue sur échecs répétés
             - Métriques Prometheus temps réel
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
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
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

WORKER_POOL_SIZE = int(os.getenv("WORKER_POOL_SIZE", "10"))
TASK_POLL_INTERVAL = float(os.getenv("TASK_POLL_INTERVAL", "0.5"))  # 500ms
MAX_TASK_DURATION = int(os.getenv("MAX_TASK_DURATION", "600"))  # 10min default
CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("worker_pool")

# ============================================================================
# Database Connection Pool
# ============================================================================
class DatabasePool:
    """Async PostgreSQL connection pool"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(
            **DB_CONFIG,
            min_size=2,
            max_size=WORKER_POOL_SIZE + 5,
            command_timeout=60
        )
        logger.info(f"Database pool created (size: {WORKER_POOL_SIZE + 5})")

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn

db_pool = DatabasePool()

# ============================================================================
# Circuit Breaker Checker
# ============================================================================
async def check_circuit_breaker(conn: asyncpg.Connection, agent_type: str) -> bool:
    """
    Vérifie si le circuit breaker est OUVERT pour cet agent.
    Returns: True si OK (closed/half_open), False si OPEN
    """
    row = await conn.fetchrow(
        """
        SELECT status, opened_at, timeout_seconds
        FROM circuit_breakers
        WHERE agent_type = $1
        """,
        agent_type
    )

    if not row:
        # Pas de circuit breaker = OK
        return True

    status = row["status"]

    if status == "closed":
        return True

    if status == "half_open":
        return True

    if status == "open":
        # Vérifier si timeout expiré -> passer en half_open
        opened_at = row["opened_at"]
        timeout_seconds = row["timeout_seconds"]

        if opened_at and datetime.now() - opened_at > timedelta(seconds=timeout_seconds):
            # Timeout expiré -> passer en half_open
            await conn.execute(
                """
                UPDATE circuit_breakers
                SET status = 'half_open', half_open_at = NOW()
                WHERE agent_type = $1
                """,
                agent_type
            )
            logger.info(f"Circuit breaker {agent_type}: open -> half_open")
            return True

        logger.warning(f"Circuit breaker {agent_type} is OPEN, skipping task")
        return False

    return True

# ============================================================================
# Task Executor
# ============================================================================
async def execute_task(
    task_id: uuid.UUID,
    task_type: str,
    instructions: Dict[str, Any],
    timeout_seconds: int,
    worker_id: int
) -> Dict[str, Any]:
    """
    Exécute une tâche via subprocess claude --print.
    Returns: {"status": "success"|"failed"|"timeout", "result": ..., "error": ...}
    """
    agent_type = instructions.get("agent_type", "unknown")
    prompt = instructions.get("prompt", "")

    logger.info(f"Worker {worker_id}: Executing task {task_id} (agent: {agent_type})")

    # Préparer la commande
    cmd = [
        CLAUDE_CLI_PATH,
        "--print",
        "--no-color"
    ]

    # Timeout avec marge de sécurité (timeout_seconds - 10s pour cleanup)
    execution_timeout = max(timeout_seconds - 10, 30)

    start_time = time.time()

    try:
        # Lancer subprocess avec timeout
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Envoyer prompt via stdin
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=prompt.encode("utf-8")),
            timeout=execution_timeout
        )

        duration = time.time() - start_time

        # Vérifier exit code
        if process.returncode == 0:
            result = stdout.decode("utf-8", errors="replace")
            logger.info(f"Worker {worker_id}: Task {task_id} SUCCESS ({duration:.1f}s)")

            return {
                "status": "success",
                "result": result,
                "duration": duration,
                "error": None
            }
        else:
            error = stderr.decode("utf-8", errors="replace")
            logger.error(f"Worker {worker_id}: Task {task_id} FAILED - {error}")

            return {
                "status": "failed",
                "result": None,
                "duration": duration,
                "error": error
            }

    except asyncio.TimeoutError:
        duration = time.time() - start_time
        logger.error(f"Worker {worker_id}: Task {task_id} TIMEOUT ({duration:.1f}s)")

        # Kill subprocess
        try:
            process.kill()
            await process.wait()
        except:
            pass

        return {
            "status": "timeout",
            "result": None,
            "duration": duration,
            "error": f"Task exceeded timeout of {execution_timeout}s"
        }

    except Exception as e:
        duration = time.time() - start_time
        logger.exception(f"Worker {worker_id}: Task {task_id} EXCEPTION - {e}")

        return {
            "status": "failed",
            "result": None,
            "duration": duration,
            "error": str(e)
        }

# ============================================================================
# Task Completion Handler
# ============================================================================
async def handle_task_completion(
    conn: asyncpg.Connection,
    task_id: uuid.UUID,
    execution_result: Dict[str, Any],
    agent_type: str,
    retry_count: int,
    max_retries: int,
    batch_id: Optional[uuid.UUID]
):
    """
    Met à jour la base de données après exécution d'une tâche.
    Gère retry logic, circuit breaker, dead letter queue.
    """
    status = execution_result["status"]
    result = execution_result["result"]
    error = execution_result["error"]
    duration = execution_result["duration"]

    # Mise à jour du status
    if status == "success":
        await conn.execute(
            """
            UPDATE worker_tasks
            SET status = 'success',
                result = $2,
                completed_at = NOW(),
                error = NULL
            WHERE id = $1
            """,
            task_id,
            json.dumps({"output": result, "duration": duration})
        )

        # Update circuit breaker (success)
        await conn.execute(
            """
            UPDATE circuit_breakers
            SET success_count = success_count + 1,
                consecutive_failures = 0,
                last_success_at = NOW(),
                last_check_at = NOW()
            WHERE agent_type = $1
            """,
            agent_type
        )

        # Métriques
        await conn.execute(
            """
            INSERT INTO agent_metrics (agent_type, execution_path, duration_seconds, status)
            VALUES ($1, 'db_queue', $2, 'success')
            """,
            agent_type,
            duration
        )

    elif status in ("failed", "timeout"):
        # Vérifier si on doit retry
        if retry_count < max_retries:
            # Retry
            await conn.execute(
                """
                UPDATE worker_tasks
                SET status = 'pending',
                    retry_count = retry_count + 1,
                    error = $2
                WHERE id = $1
                """,
                task_id,
                error
            )
            logger.info(f"Task {task_id} queued for retry ({retry_count + 1}/{max_retries})")
        else:
            # Max retries atteint -> FAILED définitif
            await conn.execute(
                """
                UPDATE worker_tasks
                SET status = $2,
                    error = $3,
                    completed_at = NOW()
                WHERE id = $1
                """,
                task_id,
                status,
                error
            )

            # Update circuit breaker (failure)
            await conn.execute(
                """
                UPDATE circuit_breakers
                SET failure_count = failure_count + 1,
                    consecutive_failures = consecutive_failures + 1,
                    last_failure_at = NOW(),
                    last_check_at = NOW()
                WHERE agent_type = $1
                """,
                agent_type
            )

            # Vérifier si circuit breaker doit s'ouvrir
            cb_row = await conn.fetchrow(
                """
                SELECT failure_count, success_count, failure_threshold, min_requests
                FROM circuit_breakers
                WHERE agent_type = $1
                """,
                agent_type
            )

            if cb_row:
                total = cb_row["failure_count"] + cb_row["success_count"]
                if total >= cb_row["min_requests"]:
                    failure_rate = cb_row["failure_count"] / total
                    if failure_rate >= cb_row["failure_threshold"]:
                        # OUVRIR le circuit breaker
                        await conn.execute(
                            """
                            UPDATE circuit_breakers
                            SET status = 'open',
                                opened_at = NOW(),
                                reason = $2
                            WHERE agent_type = $1
                            """,
                            agent_type,
                            f"Failure rate {failure_rate:.1%} >= threshold {cb_row['failure_threshold']:.1%}"
                        )
                        logger.error(f"Circuit breaker OPENED for {agent_type}")

            # Ajouter à dead letter queue
            task_row = await conn.fetchrow(
                "SELECT task_type, instructions FROM worker_tasks WHERE id = $1",
                task_id
            )

            await conn.execute(
                """
                INSERT INTO dead_letter_queue (
                    original_task_id,
                    task_type,
                    instructions,
                    failure_reason,
                    retry_count,
                    last_error,
                    batch_id,
                    agent_type
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                task_id,
                task_row["task_type"],
                task_row["instructions"],
                status,
                retry_count,
                error,
                batch_id,
                agent_type
            )
            logger.info(f"Task {task_id} moved to dead letter queue")

            # Métriques
            await conn.execute(
                """
                INSERT INTO agent_metrics (agent_type, execution_path, duration_seconds, status)
                VALUES ($1, 'db_queue', $2, $3)
                """,
                agent_type,
                duration,
                status
            )

# ============================================================================
# Worker Loop
# ============================================================================
async def worker_loop(worker_id: int, shutdown_event: asyncio.Event):
    """
    Boucle principale d'un worker.
    - Poll database pour tasks pending
    - FOR UPDATE SKIP LOCKED pour éviter race conditions
    - Execute task via subprocess
    - Update task status
    """
    logger.info(f"Worker {worker_id} started")

    while not shutdown_event.is_set():
        try:
            async with db_pool.acquire() as conn:
                # BEGIN transaction
                async with conn.transaction():
                    # FOR UPDATE SKIP LOCKED - atomique
                    task = await conn.fetchrow(
                        """
                        SELECT id, task_type, instructions, timeout_seconds,
                               retry_count, max_retries, batch_id
                        FROM worker_tasks
                        WHERE status = 'pending'
                        ORDER BY priority DESC, created_at ASC
                        LIMIT 1
                        FOR UPDATE SKIP LOCKED
                        """
                    )

                    if not task:
                        # Pas de tâche disponible
                        await asyncio.sleep(TASK_POLL_INTERVAL)
                        continue

                    task_id = task["id"]
                    task_type = task["task_type"]
                    instructions = task["instructions"]
                    timeout_seconds = task["timeout_seconds"]
                    retry_count = task["retry_count"]
                    max_retries = task["max_retries"]
                    batch_id = task["batch_id"]

                    agent_type = instructions.get("agent_type", "unknown")

                    # Vérifier circuit breaker
                    if not await check_circuit_breaker(conn, agent_type):
                        # Circuit breaker OPEN - marquer comme failed
                        await conn.execute(
                            """
                            UPDATE worker_tasks
                            SET status = 'failed',
                                error = 'Circuit breaker is OPEN',
                                completed_at = NOW()
                            WHERE id = $1
                            """,
                            task_id
                        )
                        continue

                    # Marquer comme RUNNING
                    await conn.execute(
                        """
                        UPDATE worker_tasks
                        SET status = 'running',
                            started_at = NOW(),
                            worker_id = $2
                        WHERE id = $1
                        """,
                        task_id,
                        worker_id
                    )

                # Transaction committed - on a lock sur la tâche

                # Exécuter la tâche (hors transaction)
                execution_result = await execute_task(
                    task_id,
                    task_type,
                    instructions,
                    timeout_seconds,
                    worker_id
                )

                # Mettre à jour le résultat (nouvelle transaction)
                async with db_pool.acquire() as conn:
                    await handle_task_completion(
                        conn,
                        task_id,
                        execution_result,
                        agent_type,
                        retry_count,
                        max_retries,
                        batch_id
                    )

        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
            break

        except Exception as e:
            logger.exception(f"Worker {worker_id} error: {e}")
            await asyncio.sleep(1)  # Backoff sur erreur

    logger.info(f"Worker {worker_id} stopped")

# ============================================================================
# Worker Pool Manager
# ============================================================================
class WorkerPoolManager:
    """Gère le pool de workers"""

    def __init__(self, pool_size: int = WORKER_POOL_SIZE):
        self.pool_size = pool_size
        self.workers: List[asyncio.Task] = []
        self.shutdown_event = asyncio.Event()

    async def start(self):
        """Démarre tous les workers"""
        logger.info(f"Starting worker pool (size: {self.pool_size})")

        # Connecter à la DB
        await db_pool.connect()

        # Lancer les workers
        for i in range(self.pool_size):
            worker_task = asyncio.create_task(
                worker_loop(i, self.shutdown_event)
            )
            self.workers.append(worker_task)

        logger.info(f"Worker pool started with {self.pool_size} workers")

    async def stop(self):
        """Arrête tous les workers gracefully"""
        logger.info("Stopping worker pool...")

        # Signal shutdown
        self.shutdown_event.set()

        # Attendre que tous les workers finissent
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Fermer DB pool
        await db_pool.close()

        logger.info("Worker pool stopped")

    async def run_forever(self):
        """Tourne indéfiniment jusqu'à SIGTERM/SIGINT"""
        await self.start()

        # Attendre shutdown signal
        try:
            await self.shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Received SIGINT")

        await self.stop()

# ============================================================================
# Main Entry Point
# ============================================================================
async def main():
    """Point d'entrée principal"""
    manager = WorkerPoolManager(pool_size=WORKER_POOL_SIZE)

    # Handle SIGTERM gracefully
    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Received SIGTERM")
        manager.shutdown_event.set()

    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    # Run
    await manager.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
