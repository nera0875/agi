import asyncio
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.frontend_manager import FrontendManagerAgent
from backend.agents.consolidator import ConsolidatorAgent  # To be created
from backend.agents.validator import ValidatorAgent  # To be created

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

class AgentOrchestrator:
    def __init__(self):
        self.agents = {}
        self.running = False

    async def register_agent(self, agent, schedule=None):
        """Register agent with optional schedule"""
        self.agents[agent.name] = {
            "agent": agent,
            "schedule": schedule,  # "1h", "6h", "daily", None (event-driven)
            "task": None
        }

    async def start_scheduled_agent(self, name: str):
        """Start scheduled agent in background"""
        config = self.agents[name]
        agent = config["agent"]
        schedule = config["schedule"]

        async def run_loop():
            while self.running:
                try:
                    await agent.run()

                    # Wait based on schedule
                    if schedule == "1h":
                        await asyncio.sleep(3600)
                    elif schedule == "6h":
                        await asyncio.sleep(21600)
                    elif schedule == "daily":
                        await asyncio.sleep(86400)
                except Exception as e:
                    logger.error(f"{name} failed: {e}")
                    await asyncio.sleep(60)  # Retry after 1min

        config["task"] = asyncio.create_task(run_loop())
        logger.info(f"Started {name} with schedule {schedule}")

    async def health_monitor(self):
        """Monitor agent health every 30s"""
        while self.running:
            for name, config in self.agents.items():
                agent = config["agent"]
                if not agent.health_check():
                    logger.warning(f"{name} unhealthy - error rate high")
                    # Could auto-restart here

            await asyncio.sleep(30)

    async def start(self):
        """Start all agents"""
        self.running = True

        # Start scheduled agents
        for name, config in self.agents.items():
            if config["schedule"]:
                await self.start_scheduled_agent(name)

        # Start health monitor
        asyncio.create_task(self.health_monitor())

        logger.info(f"Orchestrator started with {len(self.agents)} agents")

        # Keep alive
        while self.running:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop all agents"""
        self.running = False

        for name, config in self.agents.items():
            if config["task"]:
                config["task"].cancel()

        logger.info("Orchestrator stopped")

    def get_metrics(self):
        """Get all agent metrics"""
        return {
            name: config["agent"].get_metrics()
            for name, config in self.agents.items()
        }

async def main():
    orchestrator = AgentOrchestrator()

    # Register agents
    frontend_agent = FrontendManagerAgent()
    await orchestrator.register_agent(frontend_agent, schedule=None)  # Event-driven

    # Future agents:
    # consolidator = ConsolidatorAgent()
    # await orchestrator.register_agent(consolidator, schedule="1h")

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
