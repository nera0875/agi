#!/usr/bin/env python3
"""
============================================================================
Prometheus Exporter - Real-time observability
============================================================================
Description: Expose métriques Prometheus pour monitoring temps réel
             - Task queue metrics (pending, running, success, failed)
             - Agent performance (duration, success rate, p50/p95/p99)
             - Circuit breaker states
             - Dead letter queue size
             - Worker pool health
             - System resources
Author: AGI System
Date: 2025-10-18
============================================================================
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import asyncpg
from aiohttp import web

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

METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
METRICS_UPDATE_INTERVAL = int(os.getenv("METRICS_UPDATE_INTERVAL", "10"))  # 10s

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prometheus_exporter")

# ============================================================================
# Metrics Storage (in-memory cache)
# ============================================================================
class MetricsCache:
    """Cache in-memory des métriques pour éviter trop de queries DB"""

    def __init__(self):
        self.data: Dict[str, any] = {}
        self.last_update: Optional[datetime] = None

    def set(self, key: str, value: any):
        self.data[key] = value
        self.last_update = datetime.now()

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def is_stale(self, max_age_seconds: int = 30) -> bool:
        if not self.last_update:
            return True
        return (datetime.now() - self.last_update).total_seconds() > max_age_seconds

metrics_cache = MetricsCache()

# ============================================================================
# Metrics Collectors
# ============================================================================
class MetricsCollector:
    """Collecte les métriques depuis PostgreSQL"""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def collect_task_queue_metrics(self) -> Dict[str, int]:
        """Métriques de la task queue"""
        result = await self.conn.fetch(
            """
            SELECT status, COUNT(*) as count
            FROM worker_tasks
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY status
            """
        )

        metrics = {
            "pending": 0,
            "running": 0,
            "success": 0,
            "failed": 0,
            "timeout": 0,
            "cancelled": 0
        }

        for row in result:
            metrics[row["status"]] = row["count"]

        # Total tasks in queue (pending + running)
        metrics["queue_length"] = metrics["pending"] + metrics["running"]

        # Success rate
        total_completed = metrics["success"] + metrics["failed"] + metrics["timeout"]
        if total_completed > 0:
            metrics["success_rate"] = metrics["success"] / total_completed
        else:
            metrics["success_rate"] = 0.0

        return metrics

    async def collect_agent_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Métriques de performance par agent"""
        result = await self.conn.fetch(
            """
            SELECT
                agent_type,
                COUNT(*) as total_executions,
                AVG(duration_seconds) as avg_duration,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) as p50_duration,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95_duration,
                PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_seconds) as p99_duration,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)::float / COUNT(*) as success_rate
            FROM agent_metrics
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            GROUP BY agent_type
            """
        )

        metrics = {}
        for row in result:
            metrics[row["agent_type"]] = {
                "total_executions": row["total_executions"],
                "avg_duration": float(row["avg_duration"] or 0),
                "p50_duration": float(row["p50_duration"] or 0),
                "p95_duration": float(row["p95_duration"] or 0),
                "p99_duration": float(row["p99_duration"] or 0),
                "success_rate": float(row["success_rate"] or 0)
            }

        return metrics

    async def collect_circuit_breaker_metrics(self) -> Dict[str, Dict[str, any]]:
        """Métriques des circuit breakers"""
        result = await self.conn.fetch(
            """
            SELECT
                agent_type,
                status,
                failure_count,
                success_count,
                consecutive_failures,
                failure_threshold
            FROM circuit_breakers
            """
        )

        metrics = {}
        for row in result:
            total = row["failure_count"] + row["success_count"]
            failure_rate = row["failure_count"] / total if total > 0 else 0.0

            metrics[row["agent_type"]] = {
                "status": row["status"],
                "failure_count": row["failure_count"],
                "success_count": row["success_count"],
                "consecutive_failures": row["consecutive_failures"],
                "failure_rate": failure_rate,
                "is_open": 1 if row["status"] == "open" else 0
            }

        return metrics

    async def collect_dlq_metrics(self) -> Dict[str, int]:
        """Métriques de dead letter queue"""
        result = await self.conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_items,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'investigating' THEN 1 ELSE 0 END) as investigating,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'ignored' THEN 1 ELSE 0 END) as ignored
            FROM dead_letter_queue
            """
        )

        return {
            "total_items": result["total_items"],
            "pending": result["pending"] or 0,
            "investigating": result["investigating"] or 0,
            "resolved": result["resolved"] or 0,
            "ignored": result["ignored"] or 0
        }

    async def collect_session_metrics(self) -> Dict[str, int]:
        """Métriques des sessions AGI"""
        result = await self.conn.fetch(
            """
            SELECT status, COUNT(*) as count
            FROM agi_sessions
            GROUP BY status
            """
        )

        metrics = {
            "active": 0,
            "paused": 0,
            "completed": 0,
            "failed": 0
        }

        for row in result:
            metrics[row["status"]] = row["count"]

        return metrics

    async def collect_all_metrics(self) -> Dict[str, any]:
        """Collecte toutes les métriques"""
        return {
            "task_queue": await self.collect_task_queue_metrics(),
            "agent_performance": await self.collect_agent_performance_metrics(),
            "circuit_breakers": await self.collect_circuit_breaker_metrics(),
            "dead_letter_queue": await self.collect_dlq_metrics(),
            "sessions": await self.collect_session_metrics(),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# Prometheus Formatter
# ============================================================================
class PrometheusFormatter:
    """Formate les métriques au format Prometheus"""

    @staticmethod
    def format_gauge(name: str, value: float, labels: Dict[str, str] = None, help_text: str = "") -> str:
        """Formate une métrique gauge"""
        lines = []

        if help_text:
            lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} gauge")

        if labels:
            label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
            lines.append(f"{name}{{{label_str}}} {value}")
        else:
            lines.append(f"{name} {value}")

        return "\n".join(lines)

    @staticmethod
    def format_counter(name: str, value: float, labels: Dict[str, str] = None, help_text: str = "") -> str:
        """Formate une métrique counter"""
        lines = []

        if help_text:
            lines.append(f"# HELP {name} {help_text}")
        lines.append(f"# TYPE {name} counter")

        if labels:
            label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
            lines.append(f"{name}{{{label_str}}} {value}")
        else:
            lines.append(f"{name} {value}")

        return "\n".join(lines)

    @staticmethod
    def format_all_metrics(metrics: Dict[str, any]) -> str:
        """Formate toutes les métriques collectées"""
        lines = []

        # Task Queue Metrics
        tq = metrics.get("task_queue", {})
        lines.append(PrometheusFormatter.format_gauge(
            "agi_task_queue_length",
            tq.get("queue_length", 0),
            help_text="Number of tasks in queue (pending + running)"
        ))
        lines.append(PrometheusFormatter.format_gauge(
            "agi_task_queue_pending",
            tq.get("pending", 0),
            help_text="Number of pending tasks"
        ))
        lines.append(PrometheusFormatter.format_gauge(
            "agi_task_queue_running",
            tq.get("running", 0),
            help_text="Number of running tasks"
        ))
        lines.append(PrometheusFormatter.format_counter(
            "agi_tasks_success_total",
            tq.get("success", 0),
            help_text="Total successful tasks (24h)"
        ))
        lines.append(PrometheusFormatter.format_counter(
            "agi_tasks_failed_total",
            tq.get("failed", 0),
            help_text="Total failed tasks (24h)"
        ))
        lines.append(PrometheusFormatter.format_gauge(
            "agi_task_success_rate",
            tq.get("success_rate", 0),
            help_text="Task success rate (24h)"
        ))

        # Agent Performance Metrics
        for agent_type, perf in metrics.get("agent_performance", {}).items():
            labels = {"agent_type": agent_type}

            lines.append(PrometheusFormatter.format_counter(
                "agi_agent_executions_total",
                perf["total_executions"],
                labels,
                "Total executions per agent (24h)"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_agent_duration_seconds_avg",
                perf["avg_duration"],
                labels,
                "Average execution duration"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_agent_duration_seconds_p50",
                perf["p50_duration"],
                labels,
                "P50 execution duration"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_agent_duration_seconds_p95",
                perf["p95_duration"],
                labels,
                "P95 execution duration"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_agent_duration_seconds_p99",
                perf["p99_duration"],
                labels,
                "P99 execution duration"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_agent_success_rate",
                perf["success_rate"],
                labels,
                "Agent success rate"
            ))

        # Circuit Breaker Metrics
        for agent_type, cb in metrics.get("circuit_breakers", {}).items():
            labels = {"agent_type": agent_type}

            lines.append(PrometheusFormatter.format_gauge(
                "agi_circuit_breaker_is_open",
                cb["is_open"],
                labels,
                "Circuit breaker status (1=open, 0=closed)"
            ))
            lines.append(PrometheusFormatter.format_counter(
                "agi_circuit_breaker_failures_total",
                cb["failure_count"],
                labels,
                "Total failures for agent"
            ))
            lines.append(PrometheusFormatter.format_gauge(
                "agi_circuit_breaker_failure_rate",
                cb["failure_rate"],
                labels,
                "Failure rate for agent"
            ))

        # Dead Letter Queue Metrics
        dlq = metrics.get("dead_letter_queue", {})
        lines.append(PrometheusFormatter.format_gauge(
            "agi_dlq_items_total",
            dlq.get("total_items", 0),
            help_text="Total items in dead letter queue"
        ))
        lines.append(PrometheusFormatter.format_gauge(
            "agi_dlq_items_pending",
            dlq.get("pending", 0),
            help_text="Pending items in DLQ"
        ))

        # Session Metrics
        sess = metrics.get("sessions", {})
        lines.append(PrometheusFormatter.format_gauge(
            "agi_sessions_active",
            sess.get("active", 0),
            help_text="Number of active sessions"
        ))
        lines.append(PrometheusFormatter.format_gauge(
            "agi_sessions_paused",
            sess.get("paused", 0),
            help_text="Number of paused sessions"
        ))

        return "\n".join(lines) + "\n"

# ============================================================================
# HTTP Server
# ============================================================================
async def metrics_handler(request):
    """Handler pour /metrics endpoint"""
    # Vérifier si cache est frais
    if not metrics_cache.is_stale(max_age_seconds=METRICS_UPDATE_INTERVAL):
        metrics_text = metrics_cache.get("prometheus_text", "")
        return web.Response(text=metrics_text, content_type="text/plain")

    # Cache stale → recalculer
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        try:
            collector = MetricsCollector(conn)
            metrics = await collector.collect_all_metrics()

            # Formater pour Prometheus
            prometheus_text = PrometheusFormatter.format_all_metrics(metrics)

            # Cache
            metrics_cache.set("prometheus_text", prometheus_text)
            metrics_cache.set("metrics", metrics)

            return web.Response(text=prometheus_text, content_type="text/plain")

        finally:
            await conn.close()

    except Exception as e:
        logger.exception(f"Error collecting metrics: {e}")
        return web.Response(text=f"# ERROR: {e}\n", status=500, content_type="text/plain")

async def health_handler(request):
    """Handler pour /health endpoint"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        await conn.fetchval("SELECT 1")
        await conn.close()

        return web.Response(text="OK\n", content_type="text/plain")
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return web.Response(text=f"ERROR: {e}\n", status=503, content_type="text/plain")

async def root_handler(request):
    """Handler pour / endpoint"""
    html = """
    <html>
    <head><title>AGI Prometheus Exporter</title></head>
    <body>
        <h1>AGI Prometheus Exporter</h1>
        <p>Endpoints:</p>
        <ul>
            <li><a href="/metrics">/metrics</a> - Prometheus metrics</li>
            <li><a href="/health">/health</a> - Health check</li>
        </ul>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

# ============================================================================
# Main
# ============================================================================
async def main():
    """Démarre le serveur HTTP"""
    app = web.Application()
    app.router.add_get("/", root_handler)
    app.router.add_get("/metrics", metrics_handler)
    app.router.add_get("/health", health_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", METRICS_PORT)
    await site.start()

    logger.info(f"Prometheus exporter listening on http://0.0.0.0:{METRICS_PORT}")
    logger.info(f"Metrics endpoint: http://0.0.0.0:{METRICS_PORT}/metrics")

    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
