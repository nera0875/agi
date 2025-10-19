#!/usr/bin/env python3
"""
============================================================================
AGI Client - Python API for Sonnet to interact with AGI system
============================================================================
Description: High-level API Python que Sonnet 4.5 utilise pour:
             - Lancer des agents (non-blocking)
             - Créer/gérer des sessions
             - Vérifier le status de batches
             - Récupérer les résultats
             - Smart routing automatique

             Simple, pythonic, type-safe.
Author: AGI System
Date: 2025-10-18
============================================================================
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

import asyncpg

from smart_router import ExecutionPath, TaskComplexity, route_task
from resilience import RetryConfig, execute_with_resilience

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

# ============================================================================
# Enums
# ============================================================================
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# Data Classes
# ============================================================================
@dataclass
class AgentTask:
    """Représente une tâche agent"""
    task_id: uuid.UUID
    agent_type: str
    prompt: str
    priority: int = 50
    timeout_seconds: int = 300
    max_retries: int = 3
    batch_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TaskResult:
    """Résultat d'une tâche"""
    task_id: uuid.UUID
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class BatchStatus:
    """Status d'un batch de tâches"""
    batch_id: uuid.UUID
    total_tasks: int
    pending_count: int
    running_count: int
    success_count: int
    failed_count: int
    is_complete: bool
    results: List[TaskResult]

@dataclass
class Session:
    """Session AGI (état de Sonnet)"""
    session_id: uuid.UUID
    session_name: str
    current_phase: str
    status: SessionStatus
    context: Dict[str, Any]
    launched_tasks: List[uuid.UUID]
    next_action: Optional[str] = None
    created_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None

# ============================================================================
# AGI Client
# ============================================================================
class AGIClient:
    """
    Client Python pour interagir avec le système AGI.

    Usage:
        async with AGIClient() as client:
            # Lancer des agents
            batch_id = await client.launch_agents([
                ("research-agent", "Research RAG optimization patterns"),
                ("code-agent", "Implement vector store")
            ])

            # Vérifier le status
            status = await client.get_batch_status(batch_id)

            # Récupérer les résultats
            results = await client.get_batch_results(batch_id)
    """

    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.conn = await asyncpg.connect(**DB_CONFIG)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.conn:
            await self.conn.close()

    # ========================================================================
    # Session Management
    # ========================================================================
    async def create_session(
        self,
        session_name: str,
        phase: str,
        context: Dict[str, Any]
    ) -> uuid.UUID:
        """
        Crée une nouvelle session AGI.

        Returns:
            session_id (UUID)
        """
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

    async def get_session(self, session_id: uuid.UUID) -> Optional[Session]:
        """Récupère une session par ID"""
        row = await self.conn.fetchrow(
            """
            SELECT id, session_name, current_phase, status, context,
                   launched_tasks, next_action, created_at, resumed_at
            FROM agi_sessions
            WHERE id = $1
            """,
            session_id
        )

        if not row:
            return None

        return Session(
            session_id=row["id"],
            session_name=row["session_name"],
            current_phase=row["current_phase"],
            status=SessionStatus(row["status"]),
            context=row["context"],
            launched_tasks=row["launched_tasks"] or [],
            next_action=row["next_action"],
            created_at=row["created_at"],
            resumed_at=row["resumed_at"]
        )

    async def update_session(
        self,
        session_id: uuid.UUID,
        phase: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        next_action: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ):
        """Met à jour une session"""
        updates = []
        params = [session_id]
        param_idx = 2

        if phase is not None:
            updates.append(f"current_phase = ${param_idx}")
            params.append(phase)
            param_idx += 1

        if context is not None:
            updates.append(f"context = ${param_idx}")
            params.append(json.dumps(context))
            param_idx += 1

        if next_action is not None:
            updates.append(f"next_action = ${param_idx}")
            params.append(next_action)
            param_idx += 1

        if status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1

        if updates:
            query = f"""
                UPDATE agi_sessions
                SET {', '.join(updates)}, resumed_at = NOW()
                WHERE id = $1
            """
            await self.conn.execute(query, *params)

    # ========================================================================
    # Agent Task Management
    # ========================================================================
    async def launch_agent(
        self,
        agent_type: str,
        prompt: str,
        priority: int = 50,
        timeout_seconds: Optional[int] = None,
        complexity: Optional[TaskComplexity] = None,
        batch_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Lance un agent unique (non-blocking).

        Args:
            agent_type: Type d'agent (ex: "research-agent")
            prompt: Prompt pour l'agent
            priority: Priorité 0-100 (default: 50)
            timeout_seconds: Timeout custom (None = smart routing)
            complexity: Complexité de la tâche (pour smart routing)
            batch_id: ID du batch (None = créer nouveau)
            session_id: ID de session (optional)
            metadata: Métadonnées custom (optional)

        Returns:
            task_id (UUID)
        """
        # Smart routing si pas de timeout spécifié
        if timeout_seconds is None:
            decision = await route_task(agent_type, complexity, priority)
            timeout_seconds = decision.estimated_timeout

        # Créer la tâche
        task_id = await self.conn.fetchval(
            """
            INSERT INTO worker_tasks (
                task_type,
                instructions,
                priority,
                timeout_seconds,
                batch_id,
                metadata,
                status
            ) VALUES ($1, $2, $3, $4, $5, $6, 'pending')
            RETURNING id
            """,
            agent_type,
            json.dumps({
                "agent_type": agent_type,
                "prompt": prompt,
                "session_id": str(session_id) if session_id else None
            }),
            priority,
            timeout_seconds,
            batch_id,
            json.dumps(metadata) if metadata else None
        )

        # Ajouter à la session si spécifié
        if session_id:
            await self.conn.execute(
                """
                UPDATE agi_sessions
                SET launched_tasks = array_append(launched_tasks, $2)
                WHERE id = $1
                """,
                session_id,
                task_id
            )

        return task_id

    async def launch_agents_batch(
        self,
        tasks: List[tuple[str, str]],  # [(agent_type, prompt), ...]
        priority: int = 50,
        session_id: Optional[uuid.UUID] = None,
        wait_for_completion: bool = False
    ) -> uuid.UUID:
        """
        Lance plusieurs agents en parallèle (batch).

        Args:
            tasks: Liste de (agent_type, prompt)
            priority: Priorité commune
            session_id: ID de session (optional)
            wait_for_completion: Si True, bloque jusqu'à completion (default: False)

        Returns:
            batch_id (UUID)
        """
        batch_id = uuid.uuid4()

        task_ids = []
        for agent_type, prompt in tasks:
            task_id = await self.launch_agent(
                agent_type,
                prompt,
                priority=priority,
                batch_id=batch_id,
                session_id=session_id
            )
            task_ids.append(task_id)

        # Si wait_for_completion, attendre
        if wait_for_completion:
            await self.wait_for_batch(batch_id)

        return batch_id

    async def wait_for_batch(
        self,
        batch_id: uuid.UUID,
        poll_interval: float = 1.0,
        timeout: Optional[float] = None
    ) -> BatchStatus:
        """
        Attend la completion d'un batch (blocking).

        Args:
            batch_id: ID du batch
            poll_interval: Intervalle de polling (seconds)
            timeout: Timeout max (seconds, None = infini)

        Returns:
            BatchStatus final
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            status = await self.get_batch_status(batch_id)

            if status.is_complete:
                return status

            # Check timeout
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Batch {batch_id} did not complete within {timeout}s")

            await asyncio.sleep(poll_interval)

    async def get_batch_status(self, batch_id: uuid.UUID) -> BatchStatus:
        """
        Récupère le status d'un batch.

        Returns:
            BatchStatus avec compteurs et résultats
        """
        rows = await self.conn.fetch(
            """
            SELECT id, task_type, status, result, error,
                   started_at, completed_at, created_at,
                   EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
            FROM worker_tasks
            WHERE batch_id = $1
            ORDER BY created_at ASC
            """,
            batch_id
        )

        total = len(rows)
        pending = sum(1 for r in rows if r["status"] == "pending")
        running = sum(1 for r in rows if r["status"] == "running")
        success = sum(1 for r in rows if r["status"] == "success")
        failed = sum(1 for r in rows if r["status"] in ("failed", "timeout"))

        results = []
        for row in rows:
            results.append(TaskResult(
                task_id=row["id"],
                status=TaskStatus(row["status"]),
                result=row["result"],
                error=row["error"],
                duration_seconds=row["duration_seconds"],
                started_at=row["started_at"],
                completed_at=row["completed_at"]
            ))

        return BatchStatus(
            batch_id=batch_id,
            total_tasks=total,
            pending_count=pending,
            running_count=running,
            success_count=success,
            failed_count=failed,
            is_complete=(pending + running == 0),
            results=results
        )

    async def get_batch_results(self, batch_id: uuid.UUID) -> List[TaskResult]:
        """
        Récupère les résultats d'un batch.
        Alias pour get_batch_status().results
        """
        status = await self.get_batch_status(batch_id)
        return status.results

    async def get_task_result(self, task_id: uuid.UUID) -> Optional[TaskResult]:
        """Récupère le résultat d'une tâche unique"""
        row = await self.conn.fetchrow(
            """
            SELECT id, task_type, status, result, error,
                   started_at, completed_at,
                   EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
            FROM worker_tasks
            WHERE id = $1
            """,
            task_id
        )

        if not row:
            return None

        return TaskResult(
            task_id=row["id"],
            status=TaskStatus(row["status"]),
            result=row["result"],
            error=row["error"],
            duration_seconds=row["duration_seconds"],
            started_at=row["started_at"],
            completed_at=row["completed_at"]
        )

    # ========================================================================
    # Helpers
    # ========================================================================
    async def get_circuit_breaker_status(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Récupère le status du circuit breaker pour un agent"""
        row = await self.conn.fetchrow(
            """
            SELECT status, failure_count, success_count,
                   consecutive_failures, last_failure_at, reason
            FROM circuit_breakers
            WHERE agent_type = $1
            """,
            agent_type
        )

        if not row:
            return None

        total = row["failure_count"] + row["success_count"]
        failure_rate = row["failure_count"] / total if total > 0 else 0.0

        return {
            "agent_type": agent_type,
            "status": row["status"],
            "failure_count": row["failure_count"],
            "success_count": row["success_count"],
            "consecutive_failures": row["consecutive_failures"],
            "failure_rate": failure_rate,
            "last_failure_at": row["last_failure_at"],
            "reason": row["reason"]
        }

    async def get_system_health(self) -> Dict[str, Any]:
        """Récupère la santé globale du système"""
        # Task queue
        task_stats = await self.conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'running') as running,
                COUNT(*) FILTER (WHERE status = 'success') as success,
                COUNT(*) FILTER (WHERE status IN ('failed', 'timeout')) as failed
            FROM worker_tasks
            WHERE created_at >= NOW() - INTERVAL '1 hour'
            """
        )

        # Circuit breakers
        cb_stats = await self.conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'open') as open_count,
                COUNT(*) FILTER (WHERE status = 'closed') as closed_count
            FROM circuit_breakers
            """
        )

        # Dead letter queue
        dlq_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM dead_letter_queue WHERE status = 'pending'"
        )

        return {
            "task_queue": {
                "pending": task_stats["pending"],
                "running": task_stats["running"],
                "success_1h": task_stats["success"],
                "failed_1h": task_stats["failed"]
            },
            "circuit_breakers": {
                "open": cb_stats["open_count"],
                "closed": cb_stats["closed_count"]
            },
            "dead_letter_queue": {
                "pending_items": dlq_count
            },
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# Convenience Functions
# ============================================================================
async def quick_launch(
    agent_type: str,
    prompt: str,
    wait: bool = False
) -> uuid.UUID:
    """
    Quick helper pour lancer un agent unique.

    Usage:
        task_id = await quick_launch("research-agent", "Research RAG patterns")
    """
    async with AGIClient() as client:
        task_id = await client.launch_agent(agent_type, prompt)
        if wait:
            result = await client.get_task_result(task_id)
            return result
        return task_id

# ============================================================================
# CLI for testing
# ============================================================================
async def main():
    """Test CLI"""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python agi_client.py <agent_type> <prompt>")
        print("Example: python agi_client.py research-agent 'Research RAG patterns'")
        return

    agent_type = sys.argv[1]
    prompt = sys.argv[2]

    print(f"Launching {agent_type}...")

    async with AGIClient() as client:
        # Lancer l'agent
        task_id = await client.launch_agent(agent_type, prompt, priority=70)
        print(f"Task launched: {task_id}")

        # Attendre le résultat
        print("Waiting for completion...")
        while True:
            result = await client.get_task_result(task_id)
            print(f"Status: {result.status}")

            if result.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.TIMEOUT):
                break

            await asyncio.sleep(2)

        # Afficher le résultat
        if result.status == TaskStatus.SUCCESS:
            print(f"\nSUCCESS ({result.duration_seconds:.1f}s):")
            print(result.result)
        else:
            print(f"\nFAILED:")
            print(result.error)

if __name__ == "__main__":
    asyncio.run(main())
