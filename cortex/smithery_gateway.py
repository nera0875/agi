#!/usr/bin/env python3
"""
Smithery Gateway - Universal MCP Access
Expose 2 tools: use_mcp + search_mcps
Hybrid: known MCPs cached in PostgreSQL, fallback to Smithery registry
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import httpx
import asyncpg

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smithery-gateway")

# Configuration
SMITHERY_API_KEY = "0cccee52-3826-4658-8e05-b35aaf2627f1"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
DATABASE_URL = "postgresql://agi_user:mysecretpassword@localhost:5433/agi_db"

# MCP Server
app = Server("smithery-gateway")

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool"""
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    logger.info("Database pool initialized")


async def close_db():
    """Close database pool"""
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Expose 2 tools: use_mcp + search_mcps"""

    return [
        Tool(
            name="use_mcp",
            description="""Execute any Smithery MCP directly by name.

Known MCPs (fast, cached in DB):
- exa: AI search engine for tech/AI content
- @smithery-ai/fetch: Fetch and parse webpages
- browserbase: Cloud browser automation
- playwright: Browser automation framework
- postgres: PostgreSQL database queries
- supabase: Supabase database/APIs
- slack: Slack messaging
- discord: Discord bot

Unknown MCPs will search Smithery registry automatically and cache for next time.

Examples:
  use_mcp("exa", "search", {"query": "RAG optimization 2025"})
  use_mcp("@smithery-ai/fetch", "fetch_url", {"url": "https://example.com"})
  use_mcp("browserbase", "screenshot", {"url": "https://site.com"})
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "mcp_id": {
                        "type": "string",
                        "description": "MCP identifier (e.g. 'exa', '@smithery-ai/fetch')"
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
                "required": ["mcp_id", "tool", "args"]
            }
        ),

        Tool(
            name="search_mcps",
            description="""Search Smithery registry for available MCPs.

Use ONLY if you need to discover new capabilities not in known MCPs.
Most common MCPs are already known - prefer use_mcp directly.

Examples:
  search_mcps("weather forecast")
  search_mcps("vector database")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if name == "use_mcp":
            result = await use_mcp(
                arguments["mcp_id"],
                arguments["tool"],
                arguments.get("args", {})
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_mcps":
            results = await search_mcps(arguments["query"])
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]


async def use_mcp(mcp_id: str, tool: str, args: dict) -> dict:
    """
    Execute MCP tool - check cache first, fallback to discovery
    """

    # 1. Try known MCPs cache (fast path)
    mcp = await get_known_mcp(mcp_id)

    if mcp:
        logger.info(f"Using KNOWN MCP: {mcp_id}.{tool}")

        # Execute
        result = await execute_smithery(mcp_id, tool, args)

        # Update usage stats
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE known_mcps SET usage_count = usage_count + 1, last_used = NOW() WHERE mcp_id = $1",
                mcp_id
            )

        return result

    else:
        # 2. Unknown MCP - search Smithery registry (slow path)
        logger.warning(f"Unknown MCP: {mcp_id}, searching Smithery registry...")

        search_results = await search_smithery_registry(mcp_id)

        if not search_results:
            raise Exception(f"MCP not found in Smithery registry: {mcp_id}")

        # Use first result
        found_mcp = search_results[0]
        logger.info(f"Found MCP: {found_mcp.get('displayName', mcp_id)}")

        # Cache for next time
        await cache_mcp(found_mcp)

        # Execute
        return await execute_smithery(
            found_mcp["qualifiedName"],
            tool,
            args
        )


async def get_known_mcp(mcp_id: str) -> Optional[dict]:
    """Get MCP from cache"""

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM known_mcps WHERE mcp_id = $1",
            mcp_id
        )

        if row:
            return dict(row)
        return None


async def search_smithery_registry(query: str) -> list:
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
            return data.get("servers", [])

        except Exception as e:
            logger.error(f"Smithery registry search failed: {e}")
            return []


async def cache_mcp(mcp_data: dict):
    """Cache discovered MCP in database"""

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO known_mcps (mcp_id, display_name, description, tools, category, verified)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (mcp_id) DO UPDATE
            SET display_name = $2, description = $3, tools = $4, category = $5
            """,
            mcp_data.get("qualifiedName"),
            mcp_data.get("displayName"),
            mcp_data.get("description"),
            json.dumps(mcp_data.get("tools", [])),
            mcp_data.get("category", "unknown"),
            False  # Not verified yet
        )

    logger.info(f"Cached MCP: {mcp_data.get('qualifiedName')}")


async def execute_smithery(mcp_id: str, tool: str, args: dict) -> dict:
    """Execute tool on Smithery-hosted MCP via CLI"""

    import subprocess
    import tempfile

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
        # Use Smithery CLI (handles OAuth automatically)
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
            raise Exception(f"Smithery CLI error: {stderr}")

        # Parse response
        stdout = process.stdout.decode().strip()

        # Find JSON-RPC response (skip CLI logs)
        for line in stdout.split('\n'):
            try:
                result = json.loads(line)
                if "jsonrpc" in result:
                    if "error" in result:
                        raise Exception(f"MCP error: {result['error']}")
                    return result.get("result", result)
            except json.JSONDecodeError:
                continue

        raise Exception(f"No valid JSON-RPC response from {mcp_id}")

    except subprocess.TimeoutExpired:
        raise Exception(f"Timeout executing {mcp_id}.{tool}")
    except Exception as e:
        logger.error(f"Smithery execution error: {e}")
        raise


async def search_mcps(query: str) -> dict:
    """Search Smithery registry (explicit discovery)"""

    results = await search_smithery_registry(query)

    return {
        "query": query,
        "count": len(results),
        "mcps": [
            {
                "mcp_id": mcp.get("qualifiedName"),
                "display_name": mcp.get("displayName"),
                "description": mcp.get("description"),
                "category": mcp.get("category"),
                "tools": mcp.get("tools", [])
            }
            for mcp in results
        ]
    }


async def main():
    """Run MCP server"""

    logger.info("Starting Smithery Gateway...")

    # Initialize database
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
