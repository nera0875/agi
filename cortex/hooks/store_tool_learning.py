#!/usr/bin/env python3
"""
🎯 HOOK: post-tool-use
Stocke apprentissages de chaque tool automatiquement (LTP)

Usage: python3 store_tool_learning.py "tool_name" '{"result": "..."}'
"""

import sys
import asyncio
import asyncpg
import json

DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"

async def main():
    if len(sys.argv) < 3:
        return

    tool_name = sys.argv[1]
    try:
        tool_result = json.loads(sys.argv[2])
    except:
        tool_result = sys.argv[2]

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Extraire learning selon type de tool
        learning = f"Tool {tool_name} utilisé"
        tags = ["tool_use", tool_name]

        if "exa" in tool_name.lower():
            learning = f"Recherche Exa: {str(tool_result)[:300]}"
            tags.append("search")
        elif "context7" in tool_name.lower():
            learning = f"Docs Context7: {str(tool_result)[:300]}"
            tags.append("documentation")
        elif "database" in tool_name.lower():
            learning = f"Query DB: {str(tool_result)[:300]}"
            tags.append("database")

        # Stocke learning automatiquement
        await conn.execute("""
            INSERT INTO agi_knowledge (section, content, tags, strength, access_count)
            VALUES ('tool_learning', $1, $2, 0.5, 0)
        """, learning, tags)

        await conn.close()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
