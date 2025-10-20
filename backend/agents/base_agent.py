from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime


class BaseAgent(ABC):
    """Abstract base class for all autonomous agents"""

    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type  # event-driven, scheduled, on-demand
        self.is_running = False
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_runtime_seconds": 0,
            "last_run": None
        }
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Main execution logic - must be implemented"""
        pass

    async def run(self, *args, **kwargs):
        """Wrapper with error handling and metrics"""
        self.is_running = True
        start = datetime.now()

        try:
            result = await self.execute(*args, **kwargs)
            self.metrics["tasks_completed"] += 1
            self.logger.info(f"{self.name} completed successfully")
            return result
        except Exception as e:
            self.metrics["tasks_failed"] += 1
            self.logger.error(f"{self.name} failed: {e}")
            raise
        finally:
            duration = (datetime.now() - start).total_seconds()
            self.metrics["total_runtime_seconds"] += duration
            self.metrics["last_run"] = datetime.now().isoformat()
            self.is_running = False

    def get_metrics(self) -> Dict[str, Any]:
        """Return agent metrics"""
        return {
            "name": self.name,
            "type": self.agent_type,
            "is_running": self.is_running,
            **self.metrics
        }

    def health_check(self) -> bool:
        """Check if agent is healthy"""
        error_rate = self.metrics["tasks_failed"] / max(1, self.metrics["tasks_completed"])
        return error_rate < 0.1  # < 10% error rate
