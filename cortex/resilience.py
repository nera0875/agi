#!/usr/bin/env python3
"""
============================================================================
Resilience Layer - Retry, Circuit Breaker, DLQ, Graceful Degradation
============================================================================
Description: Couche de résilience complète pour garantir fiabilité du système
             - Exponential backoff retry avec jitter
             - Circuit breaker integration
             - Dead letter queue automatique
             - Graceful degradation (fallback strategies)
             - Timeout adaptatif
             - Bulkhead pattern (resource isolation)
Author: AGI System
Date: 2025-10-18
============================================================================
"""

import asyncio
import logging
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional, Any, TypeVar, Generic

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

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_EXPONENTIAL_BASE = 2.0
JITTER_FACTOR = 0.1  # 10% jitter

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resilience")

# ============================================================================
# Type Vars
# ============================================================================
T = TypeVar("T")

# ============================================================================
# Enums
# ============================================================================
class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class RetryStrategy(str, Enum):
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"

# ============================================================================
# Exceptions
# ============================================================================
class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is OPEN"""
    pass

class MaxRetriesExceededError(Exception):
    """Raised when max retries exceeded"""
    pass

class TaskTimeoutError(Exception):
    """Raised when task exceeds timeout"""
    pass

# ============================================================================
# Data Classes
# ============================================================================
@dataclass
class RetryConfig:
    """Configuration pour retry logic"""
    max_retries: int = DEFAULT_MAX_RETRIES
    base_delay: float = DEFAULT_BASE_DELAY
    max_delay: float = DEFAULT_MAX_DELAY
    exponential_base: float = DEFAULT_EXPONENTIAL_BASE
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True

@dataclass
class RetryAttempt:
    """Informations sur une tentative de retry"""
    attempt_number: int
    error: Exception
    delay_before_retry: float
    timestamp: datetime

# ============================================================================
# Circuit Breaker
# ============================================================================
class CircuitBreaker:
    """
    Circuit breaker avec PostgreSQL backend.
    Patterns: closed -> open -> half_open -> closed
    """

    def __init__(self, agent_type: str, conn: asyncpg.Connection):
        self.agent_type = agent_type
        self.conn = conn

    async def check_state(self) -> CircuitBreakerState:
        """Vérifie l'état actuel du circuit breaker"""
        row = await self.conn.fetchrow(
            """
            SELECT status, opened_at, timeout_seconds
            FROM circuit_breakers
            WHERE agent_type = $1
            """,
            self.agent_type
        )

        if not row:
            # Créer circuit breaker si n'existe pas
            await self.conn.execute(
                """
                INSERT INTO circuit_breakers (agent_type, status)
                VALUES ($1, 'closed')
                ON CONFLICT (agent_type) DO NOTHING
                """,
                self.agent_type
            )
            return CircuitBreakerState.CLOSED

        state = CircuitBreakerState(row["status"])

        # Si OPEN, vérifier si timeout expiré
        if state == CircuitBreakerState.OPEN:
            opened_at = row["opened_at"]
            timeout_seconds = row["timeout_seconds"]

            if opened_at and datetime.now() - opened_at > timedelta(seconds=timeout_seconds):
                # Passer en HALF_OPEN
                await self.conn.execute(
                    """
                    UPDATE circuit_breakers
                    SET status = 'half_open', half_open_at = NOW()
                    WHERE agent_type = $1
                    """,
                    self.agent_type
                )
                logger.info(f"Circuit breaker {self.agent_type}: OPEN -> HALF_OPEN")
                return CircuitBreakerState.HALF_OPEN

        return state

    async def record_success(self):
        """Enregistre un succès"""
        await self.conn.execute(
            """
            UPDATE circuit_breakers
            SET success_count = success_count + 1,
                consecutive_failures = 0,
                last_success_at = NOW(),
                last_check_at = NOW(),
                status = CASE
                    WHEN status = 'half_open' THEN 'closed'
                    ELSE status
                END,
                closed_at = CASE
                    WHEN status = 'half_open' THEN NOW()
                    ELSE closed_at
                END
            WHERE agent_type = $1
            """,
            self.agent_type
        )

    async def record_failure(self):
        """Enregistre un échec"""
        await self.conn.execute(
            """
            UPDATE circuit_breakers
            SET failure_count = failure_count + 1,
                consecutive_failures = consecutive_failures + 1,
                last_failure_at = NOW(),
                last_check_at = NOW()
            WHERE agent_type = $1
            """,
            self.agent_type
        )

        # Vérifier si on doit ouvrir le circuit breaker
        row = await self.conn.fetchrow(
            """
            SELECT failure_count, success_count, consecutive_failures,
                   failure_threshold, min_requests, status
            FROM circuit_breakers
            WHERE agent_type = $1
            """,
            self.agent_type
        )

        if row:
            total = row["failure_count"] + row["success_count"]

            # Condition 1: Failure rate > threshold (avec min requests)
            if total >= row["min_requests"]:
                failure_rate = row["failure_count"] / total
                if failure_rate >= row["failure_threshold"]:
                    await self._open_circuit(
                        f"Failure rate {failure_rate:.1%} >= threshold {row['failure_threshold']:.1%}"
                    )
                    return

            # Condition 2: Consecutive failures (plus agressif)
            if row["consecutive_failures"] >= 5:
                await self._open_circuit(
                    f"Consecutive failures: {row['consecutive_failures']}"
                )

    async def _open_circuit(self, reason: str):
        """Ouvre le circuit breaker"""
        await self.conn.execute(
            """
            UPDATE circuit_breakers
            SET status = 'open',
                opened_at = NOW(),
                reason = $2,
                alert_sent = FALSE
            WHERE agent_type = $1
              AND status != 'open'
            """,
            self.agent_type,
            reason
        )
        logger.error(f"Circuit breaker OPENED for {self.agent_type}: {reason}")

# ============================================================================
# Retry Logic
# ============================================================================
class RetryExecutor:
    """Exécute une fonction avec retry logic"""

    def __init__(self, config: RetryConfig = RetryConfig()):
        self.config = config
        self.attempts: List[RetryAttempt] = []

    def calculate_delay(self, attempt: int) -> float:
        """Calcule le délai avant le prochain retry"""
        if self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * (attempt + 1)
        elif self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        else:  # IMMEDIATE
            delay = 0.0

        # Clamp to max_delay
        delay = min(delay, self.config.max_delay)

        # Add jitter
        if self.config.jitter and delay > 0:
            jitter = delay * JITTER_FACTOR * random.uniform(-1, 1)
            delay = max(0, delay + jitter)

        return delay

    async def execute(
        self,
        func: Callable[[], Any],
        on_retry: Optional[Callable[[RetryAttempt], None]] = None
    ) -> Any:
        """
        Exécute une fonction avec retry.

        Args:
            func: Fonction async à exécuter
            on_retry: Callback appelé avant chaque retry (optional)

        Returns:
            Résultat de func()

        Raises:
            MaxRetriesExceededError: Si max retries atteint
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func()
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {e}")

                if attempt < self.config.max_retries:
                    delay = self.calculate_delay(attempt)

                    retry_attempt = RetryAttempt(
                        attempt_number=attempt + 1,
                        error=e,
                        delay_before_retry=delay,
                        timestamp=datetime.now()
                    )
                    self.attempts.append(retry_attempt)

                    if on_retry:
                        on_retry(retry_attempt)

                    if delay > 0:
                        logger.info(f"Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                else:
                    # Max retries atteint
                    raise MaxRetriesExceededError(
                        f"Max retries ({self.config.max_retries}) exceeded. Last error: {last_error}"
                    ) from last_error

        # Should not reach here
        raise MaxRetriesExceededError(f"Max retries exceeded") from last_error

# ============================================================================
# Resilient Task Executor
# ============================================================================
class ResilientTaskExecutor:
    """
    Exécuteur de tâches avec résilience complète:
    - Retry logic
    - Circuit breaker
    - Timeout adaptatif
    - Dead letter queue
    """

    def __init__(
        self,
        agent_type: str,
        conn: asyncpg.Connection,
        retry_config: RetryConfig = RetryConfig(),
        timeout: Optional[int] = None
    ):
        self.agent_type = agent_type
        self.conn = conn
        self.retry_config = retry_config
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker(agent_type, conn)

    async def execute(
        self,
        task_func: Callable[[], Any],
        task_id: Optional[uuid.UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Exécute une tâche avec résilience complète.

        Flow:
        1. Check circuit breaker
        2. Execute with retry
        3. Record success/failure
        4. Handle DLQ on final failure
        """
        # 1. Check circuit breaker
        state = await self.circuit_breaker.check_state()
        if state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit breaker is OPEN for {self.agent_type}")

        # 2. Execute with retry
        retry_executor = RetryExecutor(self.retry_config)

        try:
            # Wrap avec timeout si spécifié
            if self.timeout:
                result = await asyncio.wait_for(
                    retry_executor.execute(task_func),
                    timeout=self.timeout
                )
            else:
                result = await retry_executor.execute(task_func)

            # Success!
            await self.circuit_breaker.record_success()
            return result

        except asyncio.TimeoutError:
            await self.circuit_breaker.record_failure()
            await self._send_to_dlq(
                task_id,
                "timeout",
                f"Task exceeded timeout of {self.timeout}s",
                retry_executor.attempts,
                context
            )
            raise TaskTimeoutError(f"Task exceeded timeout of {self.timeout}s")

        except MaxRetriesExceededError as e:
            await self.circuit_breaker.record_failure()
            await self._send_to_dlq(
                task_id,
                "max_retries_exceeded",
                str(e),
                retry_executor.attempts,
                context
            )
            raise

        except Exception as e:
            await self.circuit_breaker.record_failure()
            await self._send_to_dlq(
                task_id,
                "unknown_error",
                str(e),
                retry_executor.attempts,
                context
            )
            raise

    async def _send_to_dlq(
        self,
        task_id: Optional[uuid.UUID],
        failure_reason: str,
        error_message: str,
        attempts: List[RetryAttempt],
        context: Optional[Dict[str, Any]]
    ):
        """Envoie une tâche échouée vers dead letter queue"""
        all_errors = [
            {
                "attempt": a.attempt_number,
                "error": str(a.error),
                "timestamp": a.timestamp.isoformat()
            }
            for a in attempts
        ]

        await self.conn.execute(
            """
            INSERT INTO dead_letter_queue (
                original_task_id,
                task_type,
                instructions,
                failure_reason,
                retry_count,
                last_error,
                all_errors,
                agent_type,
                status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
            """,
            task_id or uuid.uuid4(),
            self.agent_type,
            context or {},
            failure_reason,
            len(attempts),
            error_message,
            all_errors,
            self.agent_type
        )

        logger.error(f"Task {task_id} sent to dead letter queue: {failure_reason}")

# ============================================================================
# High-Level API
# ============================================================================
async def execute_with_resilience(
    agent_type: str,
    task_func: Callable[[], Any],
    task_id: Optional[uuid.UUID] = None,
    retry_config: RetryConfig = RetryConfig(),
    timeout: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """
    API simple pour exécuter une tâche avec résilience complète.

    Usage:
        async def my_task():
            # Do work
            return result

        result = await execute_with_resilience(
            "research-agent",
            my_task,
            retry_config=RetryConfig(max_retries=5),
            timeout=300
        )
    """
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        executor = ResilientTaskExecutor(
            agent_type,
            conn,
            retry_config,
            timeout
        )
        return await executor.execute(task_func, task_id, context)
    finally:
        await conn.close()

# ============================================================================
# Graceful Degradation
# ============================================================================
class FallbackStrategy:
    """
    Stratégie de fallback pour graceful degradation.
    Si une opération échoue, essayer une alternative moins optimale.
    """

    @staticmethod
    async def with_fallback(
        primary: Callable[[], T],
        fallback: Callable[[], T],
        fallback_on: Optional[List[type]] = None
    ) -> T:
        """
        Exécute primary, si échec → fallback.

        Args:
            primary: Fonction principale
            fallback: Fonction de secours
            fallback_on: Liste d'exceptions qui déclenchent fallback (None = toutes)

        Returns:
            Résultat de primary ou fallback
        """
        try:
            return await primary()
        except Exception as e:
            if fallback_on is None or type(e) in fallback_on:
                logger.warning(f"Primary failed ({e}), using fallback")
                return await fallback()
            else:
                raise

# ============================================================================
# CLI for testing
# ============================================================================
async def test_retry():
    """Test retry logic"""
    attempt_count = 0

    async def flaky_task():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")

        if attempt_count < 3:
            raise Exception(f"Simulated failure #{attempt_count}")

        return "Success!"

    config = RetryConfig(max_retries=5, base_delay=0.5)
    executor = RetryExecutor(config)

    result = await executor.execute(flaky_task)
    print(f"Result: {result}")
    print(f"Total attempts: {len(executor.attempts) + 1}")

async def main():
    """Test CLI"""
    print("=== Testing Retry Logic ===")
    await test_retry()

if __name__ == "__main__":
    asyncio.run(main())
