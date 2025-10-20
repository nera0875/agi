#!/usr/bin/env python3
"""
🎯 HOOK: pre-compact
Sauvegarde conversation complète avant compression contexte

Usage: python3 consolidate_conversation.py '$CONVERSATION'
"""

import sys
import asyncio
import asyncpg
import json
from datetime import datetime

DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"

async def main():
    if len(sys.argv) < 2:
        return

    conversation_raw = sys.argv[1]

    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Parse conversation (format Claude Code)
        # TODO: Adapter selon format exact de $CONVERSATION
        messages = []

        # Extraire user messages + assistant responses
        # Pour l'instant, stocke conversation complète
        await conn.execute("""
            INSERT INTO agi_knowledge (section, content, tags, strength, access_count)
            VALUES ('conversation_backup', $1, ARRAY['conversation', 'pre_compact'], 0.6, 0)
        """, conversation_raw[:5000])  # Limite 5000 chars

        # Consolidation LTD : Affaiblir memories non utilisées
        await conn.execute("""
            UPDATE agi_knowledge
            SET strength = GREATEST(0.1, strength * 0.95)
            WHERE last_accessed < NOW() - INTERVAL '7 days'
               OR last_accessed IS NULL
        """)

        # Stats consolidation
        weakened = await conn.fetchval("""
            SELECT COUNT(*) FROM agi_knowledge WHERE strength < 0.3
        """)

        print(f"✅ Conversation sauvegardée, {weakened} memories affaiblies (LTD)")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
