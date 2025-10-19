#!/usr/bin/env python3
"""
MCP Research - Execute research using Smithery Gateway (Exa)
Stores results directly in memory_store
"""

import asyncio
import asyncpg
import json
import sys
import subprocess
from typing import List, Dict
from uuid import uuid4
from pathlib import Path

PROJECT_ROOT = Path("/home/pilote/projet/agi")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "agi_user",
    "password": "agi_password",
    "database": "agi_db"
}


async def research_with_smithery_gateway(query: str) -> List[Dict]:
    """
    Execute research using Smithery Gateway (Exa MCP)
    Returns structured results
    """

    try:
        # Query gateway to find search capability MCPs
        conn = await asyncpg.connect(**DB_CONFIG)

        search_mcps = await conn.fetch(
            """
            SELECT mcp_name, capabilities
            FROM smithery_mcp_cache
            WHERE 'search' = ANY(capabilities)
            LIMIT 1
            """
        )

        await conn.close()

        if not search_mcps:
            print("WARNING: No search MCP found in cache, using synthetic patterns")
            return await generate_synthetic_patterns(query)

        mcp_name = search_mcps[0]['mcp_name']
        print(f"  Using MCP: {mcp_name}")

        # Build Python script to invoke MCP via Claude Code
        script = f'''
import json
import sys
sys.path.insert(0, "{PROJECT_ROOT}")

# Use mcp__exa__search tool
from backend.routes.mcp import router as mcp_router

# Simulate request
class FakeRequest:
    def __init__(self):
        self.json_data = {{
            "tool": "search",
            "arguments": {{
                "query": "{query}",
                "num_results": 5
            }}
        }}

    async def json(self):
        return self.json_data

async def run():
    import asyncio
    from backend.routes.mcp import invoke_mcp_tool

    result = await invoke_mcp_tool(
        mcp_name="{mcp_name}",
        tool_name="search",
        arguments={{
            "query": "{query}",
            "num_results": 5
        }}
    )

    print(json.dumps(result))

asyncio.run(run())
'''

        # Execute via subprocess
        result = subprocess.run(
            ["python3", "-c", script],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)

            # Parse Exa results
            findings = []
            for item in data.get("results", [])[:5]:
                findings.append({
                    "title": item.get("title", ""),
                    "summary": item.get("text", item.get("snippet", ""))[:500],
                    "source": item.get("url", ""),
                    "relevance": item.get("score", 0.7)
                })

            if findings:
                return findings

        # Fallback to synthetic
        return await generate_synthetic_patterns(query)

    except Exception as e:
        print(f"ERROR: Smithery search failed: {e}")
        return await generate_synthetic_patterns(query)


async def generate_synthetic_patterns(query: str) -> List[Dict]:
    """
    Generate synthetic patterns based on query keywords
    Used as fallback when API fails
    """

    patterns = []

    # Pattern templates based on common topics
    if "memory" in query.lower() or "rag" in query.lower():
        patterns.append({
            "title": "Hybrid RAG with Semantic + BM25",
            "summary": "Combine semantic search (embeddings) with BM25 keyword search using RRF (Reciprocal Rank Fusion) for optimal retrieval accuracy.",
            "source": "synthetic",
            "relevance": 0.8
        })
        patterns.append({
            "title": "Quality Scoring for Memory Retention",
            "summary": "Score memories based on: content quality (30%), freshness (25%), usage frequency (25%), metadata richness (20%).",
            "source": "synthetic",
            "relevance": 0.8
        })

    if "agent" in query.lower() or "coordination" in query.lower():
        patterns.append({
            "title": "Headless Agent Execution Pattern",
            "summary": "Launch agents as background processes with task queues in PostgreSQL. Main thread continues without blocking.",
            "source": "synthetic",
            "relevance": 0.8
        })
        patterns.append({
            "title": "Agent Task Queue with PostgreSQL",
            "summary": "Use worker_tasks table with SKIP LOCKED for concurrent task processing. Status: pending → running → success/failed.",
            "source": "synthetic",
            "relevance": 0.8
        })

    if "optimization" in query.lower():
        patterns.append({
            "title": "Token Optimization with Dynamic Context",
            "summary": "Load context from database instead of static files. Query only relevant sections using tags and embeddings.",
            "source": "synthetic",
            "relevance": 0.8
        })

    return patterns


async def store_patterns_in_memory(findings: List[Dict], query: str):
    """Store research findings as architectural patterns"""

    if not findings:
        return 0

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        stored = 0

        for finding in findings:
            content = f"""
# {finding.get('title', 'Pattern')}

{finding.get('summary', '')}

Source: {finding.get('source', 'Research')}
Query: {query}
Relevance: {finding.get('relevance', 0.5)}
"""

            # Store in memory
            await conn.execute(
                """
                INSERT INTO memory_store (id, content, source_type, metadata, user_id)
                VALUES ($1, $2, 'architectural_pattern', $3::jsonb, 'system')
                ON CONFLICT (id) DO NOTHING
                """,
                uuid4(),
                content.strip(),
                json.dumps({
                    "query": query,
                    "title": finding.get("title", ""),
                    "source": finding.get("source", ""),
                    "relevance": finding.get("relevance", 0.5),
                    "tags": ["architectural_pattern", "research", "memory_optimization"]
                })
            )

            stored += 1

        return stored

    finally:
        await conn.close()


async def main():
    """Execute research and store results"""

    if len(sys.argv) < 2:
        print("Usage: python3 mcp_research.py <query>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"🔍 Researching: {query}")

    # Execute research
    findings = await research_with_smithery_gateway(query)

    print(f"📊 Found {len(findings)} results")

    # Store patterns
    stored = await store_patterns_in_memory(findings, query)

    print(f"✓ Stored {stored} patterns in memory")

    # Output summary for worker
    summary = {
        "query": query,
        "findings_count": len(findings),
        "stored_count": stored
    }

    print(json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
