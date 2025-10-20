#!/usr/bin/env python3
"""
🎯 HOOK: user-prompt-submit
Capture + stocke message user + charge mémoire pertinente

Usage: python3 capture_user_message.py "message user"
"""

import sys
import asyncio
import asyncpg
import json

DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"

async def main():
    if len(sys.argv) < 2:
        return

    user_message = sys.argv[1]

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # 1. Stocke question user immédiatement (LTP)
        await conn.execute("""
            INSERT INTO agi_knowledge (section, content, tags, strength, access_count)
            VALUES ('user_question', $1, ARRAY['conversation', 'user'], 0.5, 0)
        """, user_message)

        # 2. Charge mémoire pertinente (optionnel - si stdout visible par Claude)
        results = await conn.fetch("""
            SELECT section, content, strength
            FROM agi_knowledge
            WHERE content ILIKE $1
            ORDER BY strength DESC, access_count DESC
            LIMIT 3
        """, f"%{user_message[:50]}%")

        if results:
            context = {
                "type": "memory_context",
                "relevant_memories": [
                    {"section": r["section"], "content": r["content"][:200], "strength": r["strength"]}
                    for r in results
                ]
            }
            # Output JSON (test si Claude le voit)
            print(json.dumps(context, ensure_ascii=False))

        await conn.close()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
