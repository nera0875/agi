#!/usr/bin/env python3
"""
Smithery Intelligent Gateway - ZÉRO EXPOSITION CONTEXTE
System intelligent avec découverte basée sur capabilities

Architecture:
1. Agent demande capability ("search", "browser", "database")
2. Gateway check cache PostgreSQL (24h TTL)
3. Si cache miss → Registry API → cache
4. Agent utilise MCP via use_mcp()
5. OAuth géré par Claude Code (HTTP config)

Avantages:
- Zéro liste MCPs dans prompts agents
- Cache intelligent (pas de spam Registry)
- Accès 4000+ MCPs Smithery on-demand
- Réutilisation automatique via cache
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

import httpx
import asyncpg

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smithery-intelligent")

# Config
SMITHERY_API_KEY = "0cccee52-3826-4658-8e05-b35aaf2627f1"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
DATABASE_URL = "postgresql://agi_user:mysecretpassword@localhost:5433/agi_db"

# MCP Server
app = Server("smithery-intelligent-gateway")
db_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database pool"""
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

    # Ensure capabilities column exists
    async with db_pool.acquire() as conn:
        await conn.execute("""
            ALTER TABLE known_mcps
            ADD COLUMN IF NOT EXISTS capabilities TEXT[] DEFAULT '{}';
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_capabilities
            ON known_mcps USING GIN(capabilities);
        """)

    logger.info("✅ Database initialized")


async def close_db():
    """Close database pool"""
    if db_pool:
        await db_pool.close()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Expose 1 tool: discover_mcp (discovery only)"""

    return [
        Tool(
            name="discover_mcp",
            description="""Discover MCPs by capability and make them available.

CRITICAL: This is DISCOVERY only. After discovery, call the MCP tools DIRECTLY.

How it works:
1. You call discover_mcp("search")
2. Gateway finds matching MCPs (exa, dockfork, etc.)
3. Gateway adds them to Claude Code config automatically
4. You can now call mcp__exa__search() DIRECTLY

DO NOT use this gateway to execute MCPs. Execute them directly.

Capabilities examples:
- "search" → AI search engines (exa, perplexity, dockfork)
- "web" → Web fetching/scraping (@smithery-ai/fetch, browserbase)
- "browser" → Browser automation (playwright, puppeteer)
- "database" → Database access (postgres, supabase, mongodb)
- "vector" → Vector databases (pinecone, qdrant, weaviate)
- "communication" → Messaging (slack, discord, telegram)
- "cloud" → Cloud services (aws, vercel, cloudflare, netlify)
- "ai" → AI services (openai, anthropic, huggingface)

Workflow:
  discover_mcp("search") → returns ["exa", "dockfork"]
  → MCPs auto-added to config
  → Call mcp__exa__search({"query": "RAG 2025"}) DIRECTLY

Cache: 24h TTL in PostgreSQL
Registry: Smithery API (4000+ MCPs)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "capability": {
                        "type": "string",
                        "description": "Capability needed (e.g. 'search', 'browser', 'database')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 3)",
                        "default": 3
                    },
                    "auto_add": {
                        "type": "boolean",
                        "description": "Auto-add to Claude Code config (default: true)",
                        "default": True
                    }
                },
                "required": ["capability"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "discover_mcp":
            results = await discover_mcp(
                arguments["capability"],
                arguments.get("limit", 3),
                arguments.get("auto_add", True)
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def discover_mcp(capability: str, limit: int = 3, auto_add: bool = True) -> dict:
    """
    Discover MCPs by capability

    1. Check PostgreSQL cache (capability-based search)
    2. If cache miss → Smithery Registry API
    3. Store in cache with capabilities tags
    4. Auto-add to Claude Code config (if auto_add=True)
    5. Return list of mcp_ids with usage instructions
    """

    # 1. Check cache
    async with db_pool.acquire() as conn:
        cached = await conn.fetch(
            """
            SELECT mcp_id, display_name, description, tools, smithery_url
            FROM known_mcps
            WHERE $1 = ANY(capabilities)
            AND (last_used > NOW() - INTERVAL '24 hours'
                 OR created_at > NOW() - INTERVAL '24 hours')
            ORDER BY usage_count DESC
            LIMIT $2
            """,
            capability,
            limit
        )

    if cached:
        logger.info(f"✅ Cache HIT for capability '{capability}' ({len(cached)} MCPs)")

        results = []
        for row in cached:
            mcp_id = row["mcp_id"]
            tool_prefix = f"mcp__{mcp_id.replace('/', '_').replace('@', '').replace('-', '_')}"

            results.append({
                "mcp_id": mcp_id,
                "display_name": row["display_name"],
                "description": row["description"],
                "available_tools": json.loads(row["tools"]) if row["tools"] else [],
                "how_to_use": f"Call tools directly: {tool_prefix}__<tool_name>",
                "example": f"{tool_prefix}__search" if json.loads(row["tools"] or "[]") else f"{tool_prefix}__<tool>",
                "source": "cache"
            })

        return {
            "capability": capability,
            "count": len(results),
            "mcps": results,
            "instructions": "MCPs are ready. Call tools directly using the pattern shown in 'how_to_use'."
        }

    # 2. Cache MISS → Registry API
    logger.info(f"🔍 Cache MISS for '{capability}', searching Smithery registry...")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                "https://registry.smithery.ai/servers",
                params={"q": capability, "is:deployed": True},
                headers={"Authorization": f"Bearer {SMITHERY_API_KEY}"}
            )
            response.raise_for_status()

            servers = response.json().get("servers", [])

            if not servers:
                return {
                    "capability": capability,
                    "count": 0,
                    "mcps": [],
                    "message": f"No MCPs found for capability '{capability}'"
                }

            # 3. Cache discovered MCPs
            results = []

            for server in servers[:limit]:
                mcp_id = server.get("qualifiedName")
                smithery_url = f"https://server.smithery.ai/{mcp_id}/mcp?profile={SMITHERY_PROFILE}"

                # Infer capabilities from description/category
                capabilities = infer_capabilities(
                    server.get("description", ""),
                    server.get("category", ""),
                    [capability]  # Include search query
                )

                async with db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO known_mcps
                        (mcp_id, display_name, description, tools, category, smithery_url, capabilities, verified)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, false)
                        ON CONFLICT (mcp_id) DO UPDATE
                        SET capabilities = $7, last_used = NOW(), smithery_url = $6
                        """,
                        mcp_id,
                        server.get("displayName"),
                        server.get("description"),
                        json.dumps(server.get("tools", [])),
                        server.get("category", "unknown"),
                        smithery_url,
                        capabilities
                    )

                tool_prefix = f"mcp__{mcp_id.replace('/', '_').replace('@', '').replace('-', '_')}"

                result_data = {
                    "mcp_id": mcp_id,
                    "display_name": server.get("displayName"),
                    "description": server.get("description"),
                    "available_tools": server.get("tools", []),
                    "how_to_use": f"Call tools directly: {tool_prefix}__<tool_name>",
                    "example": f"{tool_prefix}__search" if server.get("tools") else f"{tool_prefix}__<tool>",
                    "source": "registry"
                }

                results.append(result_data)

                logger.info(f"📦 Cached {mcp_id} with capabilities: {capabilities}")

                # Auto-add to Claude Code config if requested
                if auto_add:
                    await add_to_claude_config(mcp_id, smithery_url)

            return {
                "capability": capability,
                "count": len(results),
                "mcps": results,
                "instructions": "MCPs discovered and added to config. Restart Claude Code, then call tools directly.",
                "restart_required": auto_add
            }

        except Exception as e:
            logger.error(f"Registry API error: {e}")
            return {
                "capability": capability,
                "count": 0,
                "mcps": [],
                "error": str(e)
            }


def infer_capabilities(description: str, category: str, hints: list) -> list:
    """
    Infer capabilities from MCP metadata

    Smart tagging based on description/category
    """

    capabilities = set(hints)  # Start with search query

    text = f"{description} {category}".lower()

    # Capability mapping
    mappings = {
        "search": ["search", "find", "query", "lookup"],
        "web": ["web", "fetch", "http", "scrape", "crawl"],
        "browser": ["browser", "puppeteer", "playwright", "selenium"],
        "database": ["database", "sql", "postgres", "mongo", "redis"],
        "vector": ["vector", "embedding", "pinecone", "qdrant", "weaviate"],
        "communication": ["slack", "discord", "telegram", "email", "message"],
        "cloud": ["aws", "gcp", "azure", "vercel", "cloudflare"],
        "ai": ["ai", "llm", "gpt", "claude", "openai", "anthropic"],
        "file": ["file", "storage", "s3", "bucket"],
        "auth": ["auth", "oauth", "login", "user"]
    }

    for capability, keywords in mappings.items():
        if any(keyword in text for keyword in keywords):
            capabilities.add(capability)

    return list(capabilities)


async def add_to_claude_config(mcp_id: str, smithery_url: str):
    """
    Add MCP to Claude Code config automatically

    IMPORTANT: Requires Claude Code restart to take effect
    """
    from pathlib import Path

    claude_config_path = Path.home() / ".config/claude/claude_desktop_config.json"

    if not claude_config_path.exists():
        logger.warning(f"Claude Code config not found at {claude_config_path}")
        return False

    try:
        config = json.loads(claude_config_path.read_text())

        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Check if already exists
        if mcp_id in config["mcpServers"]:
            logger.info(f"✅ {mcp_id} already in Claude Code config")
            return True

        # Add as HTTP config (OAuth handled by Claude Code)
        config["mcpServers"][mcp_id] = {
            "type": "http",
            "url": smithery_url
        }

        # Write back
        claude_config_path.write_text(json.dumps(config, indent=2))

        logger.info(f"✅ Added {mcp_id} to Claude Code config")
        logger.info(f"⚠️  RESTART Claude Code to load new MCP")

        return True

    except Exception as e:
        logger.error(f"Failed to update Claude Code config: {e}")
        return False


async def main():
    """Run MCP server"""

    logger.info("🚀 Starting Smithery Intelligent Gateway...")

    await init_db()

    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
