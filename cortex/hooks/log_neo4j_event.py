#!/usr/bin/env python3
"""
🎯 HOOK: post-tool-use
Log tous events/tools dans Neo4j pour analysis patterns et traceabilité

Usage: python3 log_neo4j_event.py "tool_name" "file_path" "session_id"
"""

import sys
import asyncio
import os
from datetime import datetime

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "Voiture789")


async def log_event_to_neo4j(tool_name: str, file_path: str, session_id: str):
    """
    Log tool usage event dans Neo4j
    Crée node ToolEvent et relie à session si existe
    """
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

        async with driver.session() as session:

            # Créer event node
            timestamp = datetime.utcnow().isoformat()
            query = """
            CREATE (e:ToolEvent {
                tool: $tool,
                file: $file,
                session_id: $session_id,
                timestamp: $timestamp,
                created_at: timestamp()
            })
            RETURN e.session_id AS session_id
            """

            result = await session.run(
                query,
                {
                    "tool": tool_name,
                    "file": file_path or "unknown",
                    "session_id": session_id,
                    "timestamp": timestamp,
                },
            )

            await result.consume()

            # Lier à session si existe
            if session_id and session_id != "unknown":
                link_query = """
                MATCH (s:Session {id: $session_id})
                MATCH (e:ToolEvent {session_id: $session_id, timestamp: $timestamp})
                WHERE NOT (s)-[:USED_TOOL]->(e)
                CREATE (s)-[:USED_TOOL {at: timestamp()}]->(e)
                RETURN COUNT(*)
                """

                link_result = await session.run(
                    link_query,
                    {"session_id": session_id, "timestamp": timestamp},
                )
                await link_result.consume()

        await driver.close()
        print(f"✅ Neo4j: Event logged [{tool_name}]", file=sys.stderr)

    except Exception as e:
        # Silent fail - don't block tool execution
        print(f"⚠️ Neo4j error: {e}", file=sys.stderr)


async def main():
    """Parse args et log event"""
    if len(sys.argv) < 3:
        return

    tool_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    file_path = sys.argv[2] if len(sys.argv) > 2 else ""
    session_id = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("CLAUDE_SESSION_ID", "unknown")

    try:
        await log_event_to_neo4j(tool_name, file_path, session_id)
    except Exception as e:
        print(f"⚠️ Hook error: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
