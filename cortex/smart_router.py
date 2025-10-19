#!/usr/bin/env python3
"""
============================================================================
Smart Router - ML-based execution path selection
============================================================================
Description: Décide intelligemment quelle méthode d'exécution utiliser:
             - db_queue: Worker pool async (parallel, non-blocking)
             - cli_direct: claude --print direct (sync, simple tasks)
             - cli_streaming: claude stream-json (sync, streaming output)

             Utilise les métriques historiques pour optimiser le choix.
             Adaptive timeout basé sur l'historique de performance.
Author: AGI System
Date: 2025-10-18
============================================================================
"""

import asyncio
import json
import logging
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

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

# Thresholds for routing decision
MIN_SAMPLES_FOR_ML = 10  # Minimum samples avant d'utiliser ML
DEFAULT_TIMEOUT = 300  # 5min par défaut
FAST_TASK_THRESHOLD = 30  # <30s = fast task
SLOW_TASK_THRESHOLD = 180  # >3min = slow task

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_router")

# ============================================================================
# Enums
# ============================================================================
class ExecutionPath(str, Enum):
    DB_QUEUE = "db_queue"
    CLI_DIRECT = "cli_direct"
    CLI_STREAMING = "cli_streaming"

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

# ============================================================================
# Data Classes
# ============================================================================
@dataclass
class RoutingDecision:
    """Résultat d'une décision de routing"""
    execution_path: ExecutionPath
    estimated_timeout: int
    confidence: float  # 0.0 - 1.0
    reason: str
    metrics_used: Dict[str, Any]

@dataclass
class AgentMetrics:
    """Métriques agrégées pour un agent"""
    agent_type: str
    total_executions: int
    avg_duration: float
    median_duration: float
    p95_duration: float
    success_rate: float
    path_performance: Dict[ExecutionPath, Dict[str, float]]

# ============================================================================
# Metrics Analyzer
# ============================================================================
class MetricsAnalyzer:
    """Analyse les métriques historiques pour prendre des décisions"""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_agent_metrics(
        self,
        agent_type: str,
        lookback_days: int = 7
    ) -> Optional[AgentMetrics]:
        """
        Récupère et agrège les métriques d'un agent.
        """
        since = datetime.now() - timedelta(days=lookback_days)

        rows = await self.conn.fetch(
            """
            SELECT execution_path, duration_seconds, status, task_complexity
            FROM agent_metrics
            WHERE agent_type = $1
              AND timestamp >= $2
            ORDER BY timestamp DESC
            LIMIT 1000
            """,
            agent_type,
            since
        )

        if not rows:
            return None

        # Calculs globaux
        durations = [r["duration_seconds"] for r in rows]
        total = len(rows)
        success_count = sum(1 for r in rows if r["status"] == "success")

        # Performance par path
        path_perf = {}
        for path in ExecutionPath:
            path_rows = [r for r in rows if r["execution_path"] == path.value]
            if path_rows:
                path_durations = [r["duration_seconds"] for r in path_rows]
                path_success = sum(1 for r in path_rows if r["status"] == "success")

                path_perf[path] = {
                    "count": len(path_rows),
                    "avg_duration": statistics.mean(path_durations),
                    "success_rate": path_success / len(path_rows) if path_rows else 0.0
                }

        return AgentMetrics(
            agent_type=agent_type,
            total_executions=total,
            avg_duration=statistics.mean(durations),
            median_duration=statistics.median(durations),
            p95_duration=self._percentile(durations, 0.95),
            success_rate=success_count / total if total > 0 else 0.0,
            path_performance=path_perf
        )

    def _percentile(self, data: List[float], p: float) -> float:
        """Calcule le percentile p (0.0 - 1.0)"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p)
        return sorted_data[min(index, len(sorted_data) - 1)]

# ============================================================================
# Smart Router
# ============================================================================
class SmartRouter:
    """Router intelligent basé sur ML et métriques historiques"""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        self.analyzer = MetricsAnalyzer(conn)

    async def decide_execution_path(
        self,
        agent_type: str,
        task_complexity: Optional[TaskComplexity] = None,
        priority: int = 50,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Décide du meilleur execution path pour cette tâche.

        Stratégie:
        1. Si pas assez de métriques → fallback heuristique
        2. Si métriques disponibles → ML-based decision
        3. Considère: complexity, priority, historical performance
        """
        # Récupérer métriques historiques
        metrics = await self.analyzer.get_agent_metrics(agent_type)

        if not metrics or metrics.total_executions < MIN_SAMPLES_FOR_ML:
            # Pas assez de données → heuristique
            return self._heuristic_decision(agent_type, task_complexity, priority)

        # Décision ML-based
        return self._ml_decision(agent_type, metrics, task_complexity, priority)

    def _heuristic_decision(
        self,
        agent_type: str,
        task_complexity: Optional[TaskComplexity],
        priority: int
    ) -> RoutingDecision:
        """
        Décision heuristique (fallback quand pas assez de métriques).

        Règles simples:
        - simple + high priority → cli_direct (rapide, sync)
        - complex → db_queue (async, non-blocking)
        - medium → db_queue par défaut
        """
        if task_complexity == TaskComplexity.SIMPLE and priority >= 80:
            return RoutingDecision(
                execution_path=ExecutionPath.CLI_DIRECT,
                estimated_timeout=DEFAULT_TIMEOUT,
                confidence=0.6,
                reason="Heuristic: simple task + high priority → cli_direct",
                metrics_used={"fallback": True}
            )

        # Par défaut: db_queue (le plus robuste)
        return RoutingDecision(
            execution_path=ExecutionPath.DB_QUEUE,
            estimated_timeout=DEFAULT_TIMEOUT,
            confidence=0.7,
            reason="Heuristic: default to db_queue (most robust)",
            metrics_used={"fallback": True}
        )

    def _ml_decision(
        self,
        agent_type: str,
        metrics: AgentMetrics,
        task_complexity: Optional[TaskComplexity],
        priority: int
    ) -> RoutingDecision:
        """
        Décision ML-based (quand métriques disponibles).

        Stratégie:
        1. Calculer score pour chaque path
        2. Sélectionner le meilleur
        3. Adaptive timeout basé sur p95
        """
        scores = {}

        for path, perf in metrics.path_performance.items():
            score = 0.0

            # Factor 1: Success rate (40% du score)
            score += perf["success_rate"] * 0.4

            # Factor 2: Speed (30% du score) - inverse de avg_duration
            max_duration = max(p["avg_duration"] for p in metrics.path_performance.values())
            if max_duration > 0:
                speed_score = 1.0 - (perf["avg_duration"] / max_duration)
                score += speed_score * 0.3

            # Factor 3: Sample size (20% du score) - confiance
            sample_score = min(perf["count"] / 100, 1.0)
            score += sample_score * 0.2

            # Factor 4: Priority boost (10% du score)
            if path == ExecutionPath.CLI_DIRECT and priority >= 80:
                score += 0.1  # Boost pour high priority

            scores[path] = score

        # Sélectionner le meilleur path
        best_path = max(scores, key=scores.get)
        best_score = scores[best_path]

        # Adaptive timeout basé sur p95
        estimated_timeout = int(metrics.p95_duration * 1.5)  # 50% marge
        estimated_timeout = max(estimated_timeout, 60)  # Min 1min
        estimated_timeout = min(estimated_timeout, 600)  # Max 10min

        return RoutingDecision(
            execution_path=best_path,
            estimated_timeout=estimated_timeout,
            confidence=best_score,
            reason=f"ML-based: best path={best_path.value} (score={best_score:.2f})",
            metrics_used={
                "total_executions": metrics.total_executions,
                "avg_duration": metrics.avg_duration,
                "success_rate": metrics.success_rate,
                "scores": {p.value: s for p, s in scores.items()}
            }
        )

    async def record_execution(
        self,
        agent_type: str,
        execution_path: ExecutionPath,
        duration_seconds: float,
        status: str,
        task_complexity: Optional[TaskComplexity] = None
    ):
        """
        Enregistre une exécution dans agent_metrics pour ML futur.
        """
        await self.conn.execute(
            """
            INSERT INTO agent_metrics (
                agent_type,
                execution_path,
                duration_seconds,
                status,
                task_complexity
            ) VALUES ($1, $2, $3, $4, $5)
            """,
            agent_type,
            execution_path.value,
            duration_seconds,
            status,
            task_complexity.value if task_complexity else None
        )

# ============================================================================
# High-Level API
# ============================================================================
async def route_task(
    agent_type: str,
    task_complexity: Optional[TaskComplexity] = None,
    priority: int = 50
) -> RoutingDecision:
    """
    API simple pour router une tâche.

    Usage:
        decision = await route_task("research-agent", TaskComplexity.MEDIUM, priority=70)
        print(f"Use {decision.execution_path} with timeout {decision.estimated_timeout}s")
    """
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        router = SmartRouter(conn)
        decision = await router.decide_execution_path(
            agent_type,
            task_complexity,
            priority
        )
        return decision
    finally:
        await conn.close()

async def record_task_execution(
    agent_type: str,
    execution_path: ExecutionPath,
    duration_seconds: float,
    status: str,
    task_complexity: Optional[TaskComplexity] = None
):
    """
    API simple pour enregistrer une exécution.

    Usage:
        await record_task_execution(
            "research-agent",
            ExecutionPath.DB_QUEUE,
            45.2,
            "success",
            TaskComplexity.MEDIUM
        )
    """
    conn = await asyncpg.connect(**DB_CONFIG)
    try:
        router = SmartRouter(conn)
        await router.record_execution(
            agent_type,
            execution_path,
            duration_seconds,
            status,
            task_complexity
        )
    finally:
        await conn.close()

# ============================================================================
# CLI for testing
# ============================================================================
async def main():
    """Test CLI"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python smart_router.py <agent_type> [complexity] [priority]")
        print("Example: python smart_router.py research-agent medium 80")
        return

    agent_type = sys.argv[1]
    complexity = TaskComplexity(sys.argv[2]) if len(sys.argv) > 2 else None
    priority = int(sys.argv[3]) if len(sys.argv) > 3 else 50

    decision = await route_task(agent_type, complexity, priority)

    print(f"\n=== Routing Decision for {agent_type} ===")
    print(f"Execution Path: {decision.execution_path.value}")
    print(f"Estimated Timeout: {decision.estimated_timeout}s")
    print(f"Confidence: {decision.confidence:.1%}")
    print(f"Reason: {decision.reason}")
    print(f"Metrics: {json.dumps(decision.metrics_used, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
