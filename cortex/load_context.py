#!/usr/bin/env python3
"""
Load Full Context from PostgreSQL
Replaces reading CLAUDE.md - everything from DB
"""

import asyncio
import asyncpg

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def load_full_context() -> str:
    """
    Load complete AGI context from PostgreSQL
    This replaces reading CLAUDE.md entirely
    """

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        context = "="*60 + "\n"
        context += "AGI SYSTEM CONTEXT (FROM POSTGRESQL)\n"
        context += "="*60 + "\n\n"

        # 1. System Rules (Core Behavior)
        context += "## SYSTEM RULES\n\n"
        rules = await conn.fetch(
            """
            SELECT rule_type, rule_content, priority
            FROM system_rules
            WHERE active = true
            ORDER BY priority DESC, rule_type
            """
        )

        current_type = None
        for rule in rules:
            if rule["rule_type"] != current_type:
                context += f"\n### {rule['rule_type'].upper()}\n"
                current_type = rule["rule_type"]
            context += f"- {rule['rule_content']}\n"

        # 2. Current Roadmap (What to do next)
        context += "\n## CURRENT ROADMAP\n\n"
        roadmap = await conn.fetchrow(
            """
            SELECT phase, predicted_next, priority, next_actions
            FROM agi_roadmap
            WHERE status = 'active'
            ORDER BY priority DESC
            LIMIT 1
            """
        )

        if roadmap:
            context += f"**Phase:** {roadmap['phase']}\n"
            context += f"**Next Action:** {roadmap['predicted_next']}\n"
            context += f"**Priority:** {roadmap['priority']}\n"
        else:
            context += "*No active roadmap - run self_improve_memory.py*\n"

        # 3. Memory Metrics (Current State)
        context += "\n## MEMORY METRICS (Latest)\n\n"
        metrics = await conn.fetch(
            """
            SELECT DISTINCT ON (metric_name) metric_name, value, target_value, status
            FROM memory_metrics
            ORDER BY metric_name, measured_at DESC
            """
        )

        for metric in metrics:
            status_icon = "✓" if metric["status"] == "excellent" else "⚠️" if metric["status"] == "at_target" else "❌"
            context += f"{status_icon} {metric['metric_name']}: {metric['value']:.1%} (target: {metric['target_value']:.1%})\n"

        # 4. Improvement Goals (Active)
        context += "\n## ACTIVE IMPROVEMENT GOALS\n\n"
        goals = await conn.fetch(
            """
            SELECT goal_name, current_metric, target_metric, priority
            FROM improvement_goals
            WHERE status = 'active'
            ORDER BY priority DESC
            LIMIT 5
            """
        )

        for goal in goals:
            context += f"- [{goal['priority']}] {goal['goal_name']}: {goal['current_metric']:.1%} → {goal['target_metric']:.1%}\n"

        # 5. Agent Configs with MCPs
        context += "\n## AGENTS & MCP ACCESS\n\n"
        agents = await conn.fetch(
            """
            SELECT agent_type, model, tools FROM agent_prompts
            ORDER BY agent_type
            """
        )

        for agent in agents:
            context += f"- **{agent['agent_type']}** ({agent['model']})\n"

            # Get MCP configs
            mcp_config = await conn.fetchrow(
                "SELECT available_mcps FROM agent_mcp_configs WHERE agent_type = $1",
                agent['agent_type']
            )

            if mcp_config and mcp_config['available_mcps']:
                mcps = ", ".join(mcp_config['available_mcps'])
                context += f"  MCPs: {mcps}\n"

        context += "\n" + "="*60 + "\n"
        context += "Context loaded from PostgreSQL ✓\n"
        context += "="*60 + "\n"

        return context

    finally:
        await conn.close()


async def main():
    """Display full context"""
    context = await load_full_context()
    print(context)


if __name__ == "__main__":
    asyncio.run(main())
