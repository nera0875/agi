#!/usr/bin/env python3
"""
Seed Common MCPs - Pre-populate cache with most useful MCPs

Run this ONCE to bootstrap your system with essential MCPs.
After this, discovery_mcp() will be instant for common capabilities.
"""

import asyncio
import json
import asyncpg

DATABASE_URL = "postgresql://agi_user:mysecretpassword@localhost:5433/agi_db"
PROFILE = "rolling-ladybug-4DEfPv"

# Essential MCPs to seed
SEED_MCPS = [
    {
        "mcp_id": "exa",
        "display_name": "Exa",
        "description": "AI-powered search engine for technical and AI content",
        "capabilities": ["search", "ai", "research"],
        "tools": ["search", "find_similar", "get_contents"],
        "category": "search"
    },
    {
        "mcp_id": "@smithery-ai/fetch",
        "display_name": "Smithery Fetch",
        "description": "Fetch and parse web pages",
        "capabilities": ["web", "fetch", "scrape"],
        "tools": ["fetch_url", "extract_elements", "get_page_metadata"],
        "category": "web"
    },
    {
        "mcp_id": "browserbase",
        "display_name": "Browserbase",
        "description": "Cloud browser automation",
        "capabilities": ["browser", "automation", "screenshot"],
        "tools": ["screenshot", "navigate", "extract"],
        "category": "browser"
    },
    {
        "mcp_id": "playwright",
        "display_name": "Playwright",
        "description": "Browser automation framework",
        "capabilities": ["browser", "automation", "testing"],
        "tools": ["navigate", "screenshot", "click", "type"],
        "category": "browser"
    },
    {
        "mcp_id": "postgres",
        "display_name": "PostgreSQL",
        "description": "PostgreSQL database queries",
        "capabilities": ["database", "sql", "data"],
        "tools": ["query", "execute"],
        "category": "database"
    },
    {
        "mcp_id": "supabase",
        "display_name": "Supabase",
        "description": "Supabase database and APIs",
        "capabilities": ["database", "sql", "api", "data"],
        "tools": ["query", "insert", "update", "delete"],
        "category": "database"
    },
    {
        "mcp_id": "redis",
        "display_name": "Redis",
        "description": "Redis key-value store",
        "capabilities": ["database", "cache", "data"],
        "tools": ["get", "set", "delete", "keys"],
        "category": "database"
    },
    {
        "mcp_id": "slack",
        "display_name": "Slack",
        "description": "Slack messaging",
        "capabilities": ["communication", "messaging", "collaboration"],
        "tools": ["send_message", "list_channels", "get_history"],
        "category": "communication"
    },
    {
        "mcp_id": "discord",
        "display_name": "Discord",
        "description": "Discord bot interactions",
        "capabilities": ["communication", "messaging", "bot"],
        "tools": ["send_message", "list_channels"],
        "category": "communication"
    }
]


async def seed_mcps():
    """Seed common MCPs into cache"""

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

    try:
        async with pool.acquire() as conn:
            for mcp in SEED_MCPS:
                smithery_url = f"https://server.smithery.ai/{mcp['mcp_id']}/mcp?profile={PROFILE}"

                await conn.execute(
                    """
                    INSERT INTO known_mcps
                    (mcp_id, display_name, description, tools, category, smithery_url, capabilities, verified)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, true)
                    ON CONFLICT (mcp_id) DO UPDATE
                    SET capabilities = $7, verified = true, last_used = NOW()
                    """,
                    mcp["mcp_id"],
                    mcp["display_name"],
                    mcp["description"],
                    json.dumps(mcp["tools"]),  # Convert list to JSON string
                    mcp["category"],
                    smithery_url,
                    mcp["capabilities"]
                )

                print(f"✅ Seeded {mcp['mcp_id']} with capabilities: {mcp['capabilities']}")

        print(f"\n🎉 Seeded {len(SEED_MCPS)} essential MCPs!")
        print("\nNow you can use:")
        print("  discover_mcp('search') → instant (exa cached)")
        print("  discover_mcp('browser') → instant (browserbase, playwright cached)")
        print("  discover_mcp('database') → instant (postgres, supabase, redis cached)")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(seed_mcps())
