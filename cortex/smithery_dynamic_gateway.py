#!/usr/bin/env python3
"""
Smithery Dynamic Gateway - ZERO Config Files
100% discovery via Smithery Registry API
Cache in PostgreSQL (24h TTL)
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

import httpx
import asyncpg

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smithery-dynamic")

SMITHERY_API_KEY = "0cccee52-3826-4658-8e05-b35aaf2627f1"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
DATABASE_URL = "postgresql://agi_user:mysecretpassword@localhost:5433/agi_db"

db_pool: Optional[asyncpg.Pool] = None
app = Server("smithery-dynamic")


async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    logger.info("Database pool initialized")


async def close_db():
    if db_pool:
        await db_pool.close()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="use_mcp",
            description="""Execute any Smithery MCP dynamically.

System automatically discovers MCPs from Smithery registry as needed.
No config files. No hardcoded MCPs.

Usage:
  1. Specify MCP by name or category
  2. Gateway discovers if unknown (searches registry)
  3. Caches for 24h
  4. Executes tool

Examples:
  use_mcp("exa", "search", {"query": "RAG techniques"})
  use_mcp("@smithery-ai/fetch", "fetch_url", {"url": "https://..."})
  use_mcp("browserbase", "screenshot", {"url": "..."})

Agent prompts specify recommended MCPs per use case.
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "mcp_name": {
                        "type": "string",
                        "description": "MCP name (e.g. 'exa', '@smithery-ai/fetch') or category (e.g. 'search', 'browser')"
                    },
                    "tool": {
                        "type": "string",
                        "description": "Tool name to execute"
                    },
                    "args": {
                        "type": "object",
                        "description": "Tool arguments"
                    }
                },
                "required": ["mcp_name", "tool", "args"]
            }
        ),

        Tool(
            name="discover_mcps",
            description="""Discover available MCPs from Smithery registry.

Use when you need to find MCPs for a specific capability.

Examples:
  discover_mcps("weather forecast")
  discover_mcps("vector database")
  discover_mcps("email sending")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or capability description"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    try:
        if name == "use_mcp":
            result = await use_mcp(
                arguments["mcp_name"],
                arguments["tool"],
                arguments.get("args", {})
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "discover_mcps":
            results = await discover_mcps(
                arguments["query"],
                arguments.get("limit", 5)
            )
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def use_mcp(mcp_name: str, tool: str, args: dict) -> dict:
    """
    Execute MCP tool - auto-discover if unknown
    """

    # 1. Try cache first
    cached = await get_cached_mcp(mcp_name)

    if cached:
        logger.info(f"Using CACHED MCP: {mcp_name}")
        mcp_config = cached
    else:
        # 2. Discover via registry
        logger.info(f"Unknown MCP: {mcp_name}, discovering...")

        discovered = await search_registry(mcp_name)

        if not discovered:
            raise Exception(f"MCP not found in Smithery registry: {mcp_name}")

        # Use first result
        mcp_config = discovered[0]
        logger.info(f"Discovered: {mcp_config['display_name']}")

        # 3. Cache for next time
        await cache_mcp(mcp_config)

    # 4. Execute via Smithery CLI
    result = await execute_smithery_cli(
        mcp_config["mcp_id"],
        tool,
        args
    )

    # 5. Update usage stats
    await update_usage(mcp_config["mcp_id"])

    return result


async def get_cached_mcp(mcp_name: str) -> Optional[dict]:
    """Get MCP from PostgreSQL cache (24h TTL)"""

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM known_mcps
            WHERE mcp_id = $1
            AND (last_used > NOW() - INTERVAL '24 hours' OR created_at > NOW() - INTERVAL '24 hours')
            """,
            mcp_name
        )

        if row:
            return {
                "mcp_id": row["mcp_id"],
                "display_name": row["display_name"],
                "description": row["description"],
                "tools": json.loads(row["tools"]) if row["tools"] else [],
                "category": row["category"]
            }
        return None


async def search_registry(query: str) -> List[dict]:
    """Search Smithery registry"""

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                "https://registry.smithery.ai/servers",
                params={"q": query, "is:deployed": True},
                headers={"Authorization": f"Bearer {SMITHERY_API_KEY}"}
            )
            response.raise_for_status()

            data = response.json()
            servers = data.get("servers", [])

            # Transform to our format
            return [
                {
                    "mcp_id": s.get("qualifiedName"),
                    "display_name": s.get("displayName"),
                    "description": s.get("description"),
                    "category": s.get("category", "unknown"),
                    "tools": s.get("tools", [])
                }
                for s in servers
            ]

        except Exception as e:
            logger.error(f"Registry search failed: {e}")
            return []


async def cache_mcp(mcp_data: dict):
    """Cache discovered MCP in PostgreSQL"""

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO known_mcps (mcp_id, display_name, description, tools, category, verified)
            VALUES ($1, $2, $3, $4, $5, false)
            ON CONFLICT (mcp_id) DO UPDATE
            SET display_name = $2, description = $3, tools = $4, category = $5, last_used = NOW()
            """,
            mcp_data["mcp_id"],
            mcp_data["display_name"],
            mcp_data["description"],
            json.dumps(mcp_data["tools"]),
            mcp_data["category"]
        )

    logger.info(f"Cached MCP: {mcp_data['mcp_id']}")


async def update_usage(mcp_id: str):
    """Update usage stats"""

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE known_mcps SET usage_count = usage_count + 1, last_used = NOW() WHERE mcp_id = $1",
            mcp_id
        )


async def execute_smithery_cli(mcp_id: str, tool: str, args: dict) -> dict:
    """Execute via Smithery CLI"""

    # Prepare JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": args
        }
    }

    try:
        # Run Smithery CLI
        process = subprocess.run(
            [
                "npx", "-y", "@smithery/cli@latest", "run", mcp_id,
                "--key", SMITHERY_API_KEY,
                "--profile", SMITHERY_PROFILE
            ],
            input=json.dumps(request).encode(),
            capture_output=True,
            timeout=30
        )

        if process.returncode != 0:
            stderr = process.stderr.decode()
            raise Exception(f"CLI error: {stderr}")

        # Parse response (find JSON-RPC in output)
        stdout = process.stdout.decode()

        for line in stdout.split('\n'):
            try:
                result = json.loads(line)
                if "jsonrpc" in result:
                    if "error" in result:
                        raise Exception(f"MCP error: {result['error']}")
                    return result.get("result", result)
            except json.JSONDecodeError:
                continue

        raise Exception(f"No valid response from {mcp_id}")

    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout executing {mcp_id}.{tool}")
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise


async def discover_mcps(query: str, limit: int = 5) -> dict:
    """Explicit discovery (rare usage)"""

    results = await search_registry(query)

    # Cache all discovered MCPs
    for mcp in results[:limit]:
        await cache_mcp(mcp)

    return {
        "query": query,
        "count": len(results),
        "results": results[:limit]
    }


async def main():
    logger.info("Starting Smithery Dynamic Gateway...")

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
