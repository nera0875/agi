#!/usr/bin/env python3
"""
Query AGI Knowledge from PostgreSQL
Fast access to context instead of reading CLAUDE.md
"""

import asyncio
import asyncpg
from typing import List, Optional

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def query_knowledge(
    section: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10
) -> List[dict]:
    """
    Query AGI knowledge

    Args:
        section: Specific section name
        tags: Filter by tags (any match)
        limit: Max results

    Returns:
        List of knowledge entries
    """

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        if section:
            # Get specific section
            results = await conn.fetch(
                "SELECT * FROM agi_knowledge WHERE section = $1",
                section
            )

        elif tags:
            # Get by tags (any match)
            results = await conn.fetch(
                """
                SELECT * FROM agi_knowledge
                WHERE tags && $1
                ORDER BY priority DESC
                LIMIT $2
                """,
                tags,
                limit
            )

        else:
            # Get all, ordered by priority
            results = await conn.fetch(
                """
                SELECT * FROM agi_knowledge
                ORDER BY priority DESC
                LIMIT $1
                """,
                limit
            )

        return [
            {
                "section": r["section"],
                "tags": list(r["tags"]),
                "content": r["content"],
                "priority": r["priority"]
            }
            for r in results
        ]

    finally:
        await conn.close()


async def get_session_context() -> str:
    """
    Get essential context for session start

    Returns:
        Combined context string
    """

    # Load critical sections
    core = await query_knowledge(tags=["agi-core"], limit=5)
    workflow = await query_knowledge(tags=["workflow-optimization"], limit=2)

    context = "=== AGI SESSION CONTEXT ===\n\n"

    for entry in core + workflow:
        context += f"## {entry['section'].upper()}\n"
        context += f"{entry['content']}\n\n"

    return context


async def main():
    """Example usage"""

    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 query_knowledge.py --section <name>")
        print("  python3 query_knowledge.py --tags tag1,tag2")
        print("  python3 query_knowledge.py --context")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "--section":
        section = sys.argv[2]
        results = await query_knowledge(section=section)

    elif mode == "--tags":
        tags = sys.argv[2].split(",")
        results = await query_knowledge(tags=tags)

    elif mode == "--context":
        context = await get_session_context()
        print(context)
        return

    else:
        print("Invalid mode")
        sys.exit(1)

    for r in results:
        print(f"\n=== {r['section']} ({r['priority']}) ===")
        print(f"Tags: {', '.join(r['tags'])}")
        print(f"\n{r['content']}\n")


if __name__ == "__main__":
    asyncio.run(main())
