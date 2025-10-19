#!/usr/bin/env python3
"""
Agent Manager - High-level interface for launching agents
Manages multiple headless agents in parallel
"""

import asyncio
import asyncpg
from typing import List, Dict, Any
from launch_agent_headless import launch_agent_headless, check_agent_output

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


class AgentManager:
    """Manages multiple headless agents"""

    def __init__(self):
        self.running_agents = {}

    async def launch(self, agent_type: str, task_prompt: str) -> str:
        """
        Launch agent and track it

        Returns:
            agent_id for tracking
        """
        result = await launch_agent_headless(agent_type, task_prompt)

        agent_id = result['process_id']
        self.running_agents[agent_id] = result

        return agent_id

    async def launch_parallel(self, tasks: List[Dict[str, str]]) -> List[str]:
        """
        Launch multiple agents in parallel

        Args:
            tasks: List of {"agent_type": "...", "task_prompt": "..."}

        Returns:
            List of agent_ids
        """
        coros = [
            self.launch(task["agent_type"], task["task_prompt"])
            for task in tasks
        ]

        return await asyncio.gather(*coros)

    async def check(self, agent_id: str) -> Dict[str, Any]:
        """Check agent status"""

        if agent_id not in self.running_agents:
            return {"error": "Agent not found"}

        agent_info = self.running_agents[agent_id]
        status = await check_agent_output(agent_info['output_file'])

        return {
            "agent_id": agent_id,
            "agent_type": agent_info['agent_type'],
            "model": agent_info['model'],
            "status": status['status'],
            "result": status.get('result')
        }

    async def check_all(self) -> Dict[str, Dict]:
        """Check status of all running agents"""

        results = {}
        for agent_id in list(self.running_agents.keys()):
            results[agent_id] = await self.check(agent_id)

        return results

    async def wait_for(self, agent_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Wait for agent to complete (with timeout)

        Args:
            agent_id: Agent to wait for
            timeout: Max wait time in seconds

        Returns:
            Agent result
        """
        start = asyncio.get_event_loop().time()

        while True:
            status = await self.check(agent_id)

            if status['status'] in ['completed', 'error']:
                return status

            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > timeout:
                return {"error": "Timeout", "agent_id": agent_id}

            await asyncio.sleep(1)

    async def wait_for_all(self, timeout: int = 120) -> Dict[str, Dict]:
        """Wait for all agents to complete"""

        tasks = [
            self.wait_for(agent_id, timeout)
            for agent_id in self.running_agents.keys()
        ]

        results = await asyncio.gather(*tasks)

        return {
            agent_id: result
            for agent_id, result in zip(self.running_agents.keys(), results)
        }


# Example usage patterns
async def example_parallel_research():
    """Example: Launch 3 research agents in parallel"""

    manager = AgentManager()

    # Launch 3 research tasks simultaneously
    agent_ids = await manager.launch_parallel([
        {
            "agent_type": "research-agent",
            "task_prompt": "Research latest vector database optimizations 2025"
        },
        {
            "agent_type": "research-agent",
            "task_prompt": "Research RAG techniques for long-term memory"
        },
        {
            "agent_type": "research-agent",
            "task_prompt": "Research Claude Code API advanced features"
        }
    ])

    print(f"Launched {len(agent_ids)} research agents")

    # Continue working on other things...
    # ... (non-blocking) ...

    # Check results after 30s
    await asyncio.sleep(30)
    results = await manager.check_all()

    for agent_id, status in results.items():
        print(f"{status['agent_type']}: {status['status']}")


async def example_mixed_workflow():
    """Example: Research → Context → Execute"""

    manager = AgentManager()

    # Step 1: Research in background
    research_id = await manager.launch(
        "research-agent",
        "Research best practices for deduplication in vector databases"
    )

    # Step 2: Build context while research runs
    context_id = await manager.launch(
        "context-builder",
        "Build context for implementing deduplication in memory_service.py"
    )

    # Continue other work...

    # Step 3: Wait for both, then execute
    research_result = await manager.wait_for(research_id, timeout=60)
    context_result = await manager.wait_for(context_id, timeout=30)

    if research_result['status'] == 'completed' and context_result['status'] == 'completed':
        # Launch implementation
        exec_id = await manager.launch(
            "task-executor",
            f"Implement deduplication using:\nResearch: {research_result['result']}\nContext: {context_result['result']}"
        )

        print("Implementation launched in background")


if __name__ == "__main__":
    # Run examples
    asyncio.run(example_parallel_research())
