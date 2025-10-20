#!/usr/bin/env python3
"""
AGI Tools MCP Server - UNIFIED INTERFACE

UN SEUL MCP pour TOUS les outils AGI:
- Memory: search, store, stats
- PostgreSQL: query, execute, schema
- Smithery: discover, use MCPs on-demand
- Agents: launch, get results

Architecture 3 couches:
COUCHE 1: Claude Code → agi-tools (ce fichier)
COUCHE 2: Smithery Gateway (discovery + cache PostgreSQL)
COUCHE 3: MCP Router (execution + isolation)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import asyncpg
import httpx
import redis

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add backend services to path for Voyage AI and Cohere
backend_services_path = str(Path(__file__).parent.parent / 'backend' / 'services')
if backend_services_path not in sys.path:
    sys.path.insert(0, backend_services_path)

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agi-tools")

# Database config
DATABASE_URL = "postgresql://agi_user:agi_password@localhost:5432/agi_db"

# Import Voyage AI and Cohere wrappers
try:
    from voyage_wrapper import set_db_pool as set_voyage_pool, semantic_search, embed_single
    from cohere_wrapper import set_db_pool as set_cohere_pool, rerank, hybrid_search_and_rerank
    VOYAGE_COHERE_AVAILABLE = True
    logger.info("✅ Voyage AI and Cohere wrappers loaded")
except ImportError as e:
    logger.warning(f"⚠️  Voyage AI / Cohere wrappers not available: {e}")
    VOYAGE_COHERE_AVAILABLE = False

# Import Local Fetch MCP (remplacement Smithery)
try:
    from local_fetch_mcp import fetch_url as local_fetch, extract_elements as local_extract, get_page_metadata as local_metadata
    LOCAL_FETCH_AVAILABLE = True
    logger.info("✅ Local Fetch MCP loaded (remplacement Smithery)")
except ImportError as e:
    logger.warning(f"⚠️  Local Fetch not available: {e}")
    LOCAL_FETCH_AVAILABLE = False

# Import Local Search MCPs (Exa, Docfork, Context7 fallbacks)
try:
    from local_search_mcps import exa_search, docfork_search, context7_resolve_library, context7_get_docs
    LOCAL_SEARCH_AVAILABLE = True
    logger.info("✅ Local Search MCPs loaded (Exa/Docfork/Context7 fallbacks)")
except ImportError as e:
    logger.warning(f"⚠️  Local Search MCPs not available: {e}")
    LOCAL_SEARCH_AVAILABLE = False

# Import Local MCP Router (MCPs hébergés localement)
try:
    from local_mcp_router import route_mcp_call, list_local_mcps, get_mcp_client
    LOCAL_MCP_ROUTER_AVAILABLE = True
    logger.info("✅ Local MCP Router loaded (Exa/Context7/Fetch hébergés localement)")
except ImportError as e:
    logger.warning(f"⚠️  Local MCP Router not available: {e}")
    LOCAL_MCP_ROUTER_AVAILABLE = False

# Smithery config
SMITHERY_API_KEY = "15d7d8e1-61c3-4dba-a91f-63751eec8b08"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
SMITHERY_REGISTRY_URL = "https://registry.smithery.ai/servers"

# ═══════════════════════════════════════════════════════════
# AUTO-MEMORY WRAPPER CLASSES
# ═══════════════════════════════════════════════════════════

class PertinenceDetector:
    """Détecte automatiquement si contenu vaut la peine d'être sauvegardé"""

    KEYWORDS = {
        "high_value": [
            "decision", "strategy", "important", "critical",
            "bug", "error", "fix", "improvement", "optimization",
            "architecture", "design", "pattern", "insight",
            "milestone", "breakthrough", "solution"
        ],
        "low_value": [
            "todo", "remind me", "search for", "help with",
            "what is", "how do", "temporary", "test", "debug"
        ]
    }

    @staticmethod
    def estimate_importance(content: str, type_hint: str = None) -> float:
        """Score rapide sans LLM (0-1 scale)"""
        score = 0.5  # Baseline
        content_lower = content.lower()
        high_count = sum(1 for kw in PertinenceDetector.KEYWORDS["high_value"]
                        if kw in content_lower)
        low_count = sum(1 for kw in PertinenceDetector.KEYWORDS["low_value"]
                       if kw in content_lower)
        score += high_count * 0.1
        score -= low_count * 0.15
        if type_hint == "error":
            score += 0.2
        elif type_hint == "decision":
            score += 0.15
        elif type_hint == "insight":
            score += 0.15
        if len(content) < 50:
            score -= 0.2
        elif len(content) > 5000:
            score -= 0.1
        return max(0.0, min(1.0, score))


class EmbeddingService:
    """Génère embeddings via Voyage AI"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.voyageai.com/v1/embeddings"
        self.model = "voyage-2"

    async def embed(self, text: str) -> Optional[list]:
        """Genère embedding (1024-dimensional vector)"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "input": text,
                        "model": self.model
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    embedding = data["data"][0]["embedding"]
                    return embedding
                else:
                    logger.warning(f"Embedding API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            return None

    async def embed_batch(self, texts: list) -> list:
        """Batch embedding for efficiency"""
        return await asyncio.gather(
            *[self.embed(text) for text in texts]
        )


class MCPAutoMemoryWrapper:
    """Wrapper qui intercepte MCP tool calls et sauvegarde automatiquement"""

    def __init__(self, db_pool, redis_client, embedding_service: EmbeddingService):
        self.db_pool = db_pool
        self.redis = redis_client
        self.embeddings = embedding_service
        self.context = {
            "current_user_message": None,
            "tool_calls": [],
            "tool_results": []
        }

    async def wrap_user_input(self, message: str):
        """Sauvegarde input utilisateur"""
        self.context["current_user_message"] = message
        importance = PertinenceDetector.estimate_importance(
            message,
            type_hint="conversation"
        )
        if importance >= 0.3:
            await self._save_to_all_layers(
                content=message,
                type_="conversation",
                importance=importance,
                metadata={"role": "user"}
            )

    async def wrap_tool_call(self, tool_name: str, arguments: dict):
        """Wrapper autour d'un tool call"""
        call_record = {
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.context["tool_calls"].append(call_record)

    async def wrap_assistant_response(self, response: str):
        """Sauvegarde réponse assistant"""
        self._detect_decisions(response)
        importance = PertinenceDetector.estimate_importance(
            response,
            type_hint="decision"
        )
        if importance >= 0.4:
            await self._save_to_all_layers(
                content=response,
                type_=self._detect_type(response),
                importance=importance,
                metadata={"role": "assistant"}
            )

    async def _save_to_all_layers(self, content: str, type_: str,
                                  importance: float, metadata: dict):
        """Orchestration complète de sauvegarde"""
        entry_hash = hashlib.sha256(content.encode()).hexdigest()[:12]
        await self._save_l1(entry_hash, content, type_, importance)
        entry_id = await self._save_l2(entry_hash, content, type_, importance, metadata)
        await self._save_l3(entry_id, entry_hash, content, type_)
        await self._queue_neo4j_sync(entry_id, entry_hash, content, type_, importance)

    async def _save_l1(self, entry_hash: str, content: str, type_: str, importance: float):
        """Save to Redis cache"""
        ttl = {
            "conversation": 7200,
            "decision": 86400,
            "technical": 259200,
            "error": 1296000,
            "insight": 2592000
        }.get(type_, 3600)
        try:
            self.redis.hset(f"agi:cache:{entry_hash}", mapping={
                "content": content[:500],
                "type": type_,
                "importance": importance,
                "accessed": datetime.utcnow().isoformat()
            })
            self.redis.expire(f"agi:cache:{entry_hash}", ttl)
            self.redis.sadd(f"agi:cache:idx:type:{type_}", entry_hash)
            self.redis.zadd("agi:cache:idx:importance", {entry_hash: importance})
        except Exception as e:
            logger.warning(f"L1 save failed: {e}")

    async def _save_l2(self, entry_hash: str, content: str, type_: str,
                       importance: float, metadata: dict):
        """Save to PostgreSQL buffer"""
        try:
            async with self.db_pool.acquire() as conn:
                entry_id = await conn.fetchval("""
                    INSERT INTO memory_working_buffer
                    (entry_hash, content, type, importance, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, entry_hash, content, type_, importance, json.dumps(metadata))
            return entry_id
        except Exception as e:
            logger.warning(f"L2 save failed: {e}")
            return None

    async def _save_l3(self, entry_id, entry_hash: str, content: str, type_: str):
        """Save embeddings to pgvector"""
        if not entry_id:
            return
        try:
            embedding = await self.embeddings.embed(content)
            if embedding:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO memory_embeddings
                        (entry_hash, content, embedding, type)
                        VALUES ($1, $2, $3, $4)
                    """, entry_hash, content, embedding, type_)
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE memory_working_buffer
                        SET embeddings_generated = TRUE
                        WHERE id = $1
                    """, entry_id)
        except Exception as e:
            logger.warning(f"L3 save failed: {e}")

    async def _queue_neo4j_sync(self, entry_id, entry_hash: str, content: str,
                               type_: str, importance: float):
        """Queue entry for Neo4j sync"""
        if not entry_id:
            return
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO memory_neo4j_sync_log
                    (entry_id, entry_hash, node_label, status)
                    VALUES ($1, $2, $3, 'pending')
                """, entry_id, entry_hash, type_.upper())
        except Exception as e:
            logger.warning(f"Neo4j sync queue failed: {e}")

    def _detect_type(self, content: str) -> str:
        """Détecte type de contenu"""
        content_lower = content.lower()
        if "error" in content_lower or "bug" in content_lower:
            return "error"
        elif "decision" in content_lower or "decided" in content_lower:
            return "decision"
        elif "discovered" in content_lower or "realized" in content_lower:
            return "insight"
        elif "strategy" in content_lower or "plan" in content_lower:
            return "strategic"
        else:
            return "technical"

    def _detect_decisions(self, response: str):
        """Détecte décisions importantes"""
        keywords = ["i decided", "i will", "let's", "decision", "plan"]
        if any(kw in response.lower() for kw in keywords):
            logger.info("[DECISION DETECTED] Marked for high importance")


# MCP Server
app = Server("agi-tools")
db_pool: Optional[asyncpg.Pool] = None
auto_memory: Optional[MCPAutoMemoryWrapper] = None


async def init_db():
    """Initialize database connection pool + create tables"""
    global db_pool, auto_memory
    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30
    )
    logger.info("✅ Database pool initialized")

    # Create Smithery MCP cache table if not exists
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS smithery_mcp_cache (
                    mcp_id TEXT PRIMARY KEY,
                    call_count INT DEFAULT 1,
                    tools TEXT[] DEFAULT '{}',
                    last_used TIMESTAMPTZ DEFAULT NOW(),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_smithery_mcp_call_count ON smithery_mcp_cache(call_count DESC);
                CREATE INDEX IF NOT EXISTS idx_smithery_mcp_last_used ON smithery_mcp_cache(last_used DESC);
            """)
            logger.info("✅ Smithery cache table ready")
    except Exception as e:
        logger.warning(f"Could not create cache table: {e}")

    # Initialize MCPAutoMemoryWrapper
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        embedding_service = EmbeddingService(api_key=os.getenv("VOYAGE_API_KEY", ""))
        auto_memory = MCPAutoMemoryWrapper(
            db_pool=db_pool,
            redis_client=redis_client,
            embedding_service=embedding_service
        )
        logger.info("✅ MCPAutoMemoryWrapper initialized")
    except Exception as e:
        logger.warning(f"⚠️  MCPAutoMemoryWrapper initialization failed: {e}")
        auto_memory = None


async def close_db():
    """Close database pool"""
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all AGI tools - UNIFIED VERSION (4 tools)"""

    return [
        # ═══════════════════════════════════════════════════════
        # 1. THINK - Outil PRINCIPAL (Cerveau, 95% des cas)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="think",
            description="""🧠 THINK - Outil SURPUISSANT (CASCADE AUTOMATIQUE)

Comme cerveau humain: tu PENSES, tout se déclenche en cascade.

Cascade L1/L2/L3:
- L1 (working memory): Rules renforcées + contexte immédiat
- L2 (short-term): Session + fichiers récents
- L3 (long-term): Memories + codebase

Utilise ceci pour 95% des requêtes!

Examples:
  think("async workers")
  think("what did I work on today")
  think("find memory about reinforcement learning")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ta pensée/question/intention"},
                    "context": {"type": "object", "description": "Contexte optionnel"}
                },
                "required": ["query"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # 2. MEMORY - Mémoire unifié (search/store/stats)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="memory",
            description="""💾 MEMORY - Gestion mémoire unifiée

Actions:
- search: Chercher dans memories (semantic + BM25)
- store: Stocker nouvelle memory
- stats: Statistiques mémoire

Examples:
  memory(action="search", query="async workers", limit=5)
  memory(action="store", text="Decision...", type="architectural_pattern", tags=["agi"])
  memory(action="stats")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "store", "stats"]},
                    "query": {"type": "string"},
                    "text": {"type": "string"},
                    "type": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "number", "default": 5}
                },
                "required": ["action"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # 3. DATABASE - PostgreSQL unifié (query/execute/schema)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="database",
            description="""🗄️ DATABASE - PostgreSQL unifié

Actions:
- query: SELECT queries
- execute: INSERT/UPDATE/DELETE
- tables: Liste tables
- schema: Schema d'une table
- stats: Database stats

Examples:
  database(action="query", sql="SELECT * FROM agi_ideas")
  database(action="execute", sql="INSERT INTO...", params=[...])
  database(action="tables")
  database(action="schema", table_name="agi_ideas")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["query", "execute", "tables", "schema", "stats"]},
                    "sql": {"type": "string"},
                    "params": {"type": "array"},
                    "table_name": {"type": "string"}
                },
                "required": ["action"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # 4. CONTROL - Control système (agents/mcp/bootstrap)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="control",
            description="""⚙️ CONTROL - Control système unifié

Actions:
- bootstrap: Bootstrap AGI (démarrage)
- agent: Execute agent direct (non-blocking)
- discover_mcp: Cherche MCP Smithery
- use_mcp: Utilise MCP Smithery
- list_mcps: Liste MCPs utilisés
- consolidate: LTD rules (weekly)

Examples:
  control(action="bootstrap")
  control(action="agent", prompt="Research RAG patterns")
  control(action="discover_mcp", capability="search", limit=3)
  control(action="use_mcp", mcp_id="exa", tool="web_search_exa", args={...})
  control(action="consolidate")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["bootstrap", "agent", "discover_mcp", "use_mcp", "list_mcps", "consolidate"]},
                    "prompt": {"type": "string"},
                    "capability": {"type": "string"},
                    "mcp_id": {"type": "string"},
                    "tool": {"type": "string"},
                    "args": {"type": "object"},
                    "limit": {"type": "number", "default": 3}
                },
                "required": ["action"]
            }
        )
    ]


# OLD TOOLS DEFINITIONS (keeping for reference, not exposed)
# These will be removed after migration complete
_OLD_TOOLS = [
        Tool(
            name="memory_search",
            description="""Search AGI memory using hybrid RAG (semantic + BM25).

Query stored knowledge, patterns, decisions, learnings.

Returns: Ranked results with relevance scores and metadata.

Example:
  memory_search("Smithery integration architecture")
  memory_search("neurotransmitters system", limit=10)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 5)",
                        "default": 5
                    },
                    "tags": {
                        "type": "array",
                        "description": "Filter by tags",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="memory_store",
            description="""Store new memory with auto-embeddings.

Store knowledge, patterns, decisions, architectures in AGI memory.

Type categories:
- architectural_pattern
- workflow-optimization
- learning
- decision
- error-solution

Returns: memory_id

Example:
  memory_store("System uses neurotransmitters for dynamic resource allocation", "architectural_pattern", ["agi-core", "optimization"])
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Content to store"
                    },
                    "type": {
                        "type": "string",
                        "description": "Memory type (architectural_pattern, workflow-optimization, learning, etc.)"
                    },
                    "tags": {
                        "type": "array",
                        "description": "Tags for filtering",
                        "items": {"type": "string"}
                    },
                    "project": {
                        "type": "string",
                        "description": "Project ID (default: 'default')",
                        "default": "default"
                    }
                },
                "required": ["text", "type"]
            }
        ),

        Tool(
            name="memory_stats",
            description="""Get AGI memory system statistics.

Returns:
- Total memories
- By type breakdown
- By project
- Storage size

Example:
  memory_stats()
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),

        # ═══════════════════════════════════════════════════════
        # POSTGRESQL TOOLS
        # ═══════════════════════════════════════════════════════

        Tool(
            name="pg_query",
            description="""Execute SELECT query on AGI database.

Tables:
- known_mcps: Smithery cache
- agi_ideas: Innovation ideas
- agi_knowledge: Knowledge base
- agi_roadmap: Roadmap items

Returns: JSON array of rows

Example:
  pg_query("SELECT * FROM agi_ideas WHERE priority > 7")
  pg_query("SELECT mcp_id, capabilities FROM known_mcps WHERE 'search' = ANY(capabilities)")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT query"
                    },
                    "params": {
                        "type": "array",
                        "description": "Query parameters ($1, $2, etc.)",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["sql"]
            }
        ),

        Tool(
            name="pg_execute",
            description="""Execute INSERT/UPDATE/DELETE/DDL statement.

Returns: Number of rows affected

Example:
  pg_execute("INSERT INTO agi_ideas (title, priority) VALUES ($1, $2)", ["Idea", 9])
  pg_execute("UPDATE known_mcps SET usage_count = usage_count + 1 WHERE mcp_id = $1", ["exa"])
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL statement"
                    },
                    "params": {
                        "type": "array",
                        "description": "Parameters",
                        "items": {"type": ["string", "number", "boolean", "null"]}
                    }
                },
                "required": ["sql"]
            }
        ),

        Tool(
            name="pg_tables",
            description="""List all tables with row counts and sizes.

Returns: [{table_name, row_count, size_bytes, column_count}]

Example:
  pg_tables()
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),

        Tool(
            name="pg_schema",
            description="""Get table schema (columns, types, constraints).

Returns: {table_name, columns[], constraints[]}

Example:
  pg_schema("agi_ideas")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Table name"
                    }
                },
                "required": ["table_name"]
            }
        ),

        Tool(
            name="pg_stats",
            description="""Get database statistics.

Returns: size, table count, total rows, active connections

Example:
  pg_stats()
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),

        # ═══════════════════════════════════════════════════════
        # AGENT TOOLS (Headless Agent Management)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="launch_agent",
            description="""Launch headless agent for background task execution.

Creates task in worker_tasks queue. Agent executes asynchronously.

Available agents:
- research-agent: Fast research with pattern extraction
- code-agent: Code generation and refactoring
- task-executor: Generic task execution

Returns: {task_id, status: "pending"}

Example:
  launch_agent("research-agent", "RAG optimization patterns")
  launch_agent("code-agent", "Refactor authentication system")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "description": "Agent type (research-agent, code-agent, task-executor)"
                    },
                    "task": {
                        "type": "string",
                        "description": "Task description/query"
                    },
                    "wait": {
                        "type": "boolean",
                        "description": "Wait for completion (default: false, non-blocking)",
                        "default": False
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Max wait time in seconds (if wait=true)",
                        "default": 60
                    }
                },
                "required": ["agent_type", "task"]
            }
        ),

        Tool(
            name="get_agent_result",
            description="""Get result of launched agent task.

Query worker_tasks by task_id to check status and retrieve results.

Status values:
- pending: Task queued, not started
- running: Agent currently executing
- success: Completed successfully
- failed: Error occurred

Returns: {status, result, error, patterns_stored}

Example:
  get_agent_result("abc-123-def")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID from launch_agent"
                    }
                },
                "required": ["task_id"]
            }
        ),

        Tool(
            name="list_agents",
            description="""List available headless agents with configs.

Returns all agents from agent_prompts table with model and capabilities.

Returns: [{agent_type, model, description, speed_estimate}]

Example:
  list_agents()
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),

        Tool(
            name="execute_agent_direct",
            description="""Execute agent directly with claude --print (NO worker daemon).

Pattern from Claude Code docs: claude --print + stream-json for direct execution.

Alternative décentralisée au worker daemon:
- Exécution immédiate avec --print
- Output JSON parseable
- Pas de polling database
- Compatible CI/CD/hooks

Returns: {stdout, stderr, returncode, output_json}

Example:
  execute_agent_direct("Analyze codebase for security issues", output_format="stream-json")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Task/prompt for Claude Code"
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format: text or stream-json (default: stream-json)",
                        "default": "stream-json"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds (default: 120)",
                        "default": 120
                    }
                },
                "required": ["prompt"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # WEB FETCH TOOLS (Local, no Smithery needed)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="fetch_url",
            description="""Fetch content from any URL (docs, articles, APIs).

DIRECT Python httpx + BeautifulSoup, NO Smithery dependency.
Parses HTML and extracts clean text.

Example:
  fetch_url("https://docs.claude.com/hooks-guide", max_length=50000)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch"
                    },
                    "max_length": {
                        "type": "number",
                        "description": "Max content length (default: 50000)",
                        "default": 50000
                    }
                },
                "required": ["url"]
            }
        ),

        Tool(
            name="extract_elements",
            description="""Extract specific HTML elements using CSS selectors.

Example:
  extract_elements("https://example.com", "h2")  # All h2 headers
  extract_elements("https://example.com", ".main-content")  # Class selector
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to extract from"
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector (e.g. 'h2', '.content', '#main')"
                    }
                },
                "required": ["url", "selector"]
            }
        ),

        Tool(
            name="get_page_metadata",
            description="""Get page metadata (title, description, OpenGraph tags).

Useful for understanding page content before fetching.

Example:
  get_page_metadata("https://docs.claude.com/hooks-guide")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to get metadata from"
                    }
                },
                "required": ["url"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # SEARCH TOOLS (Local Exa/Docfork/Context7 fallbacks)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="exa_search",
            description="""Intelligent web search (Exa fallback local).

Uses DuckDuckGo + metadata extraction if no Exa API key.
Set EXA_API_KEY env for official Exa API.

Example:
  exa_search("FastAPI async best practices 2025", num_results=5)
  exa_search("Claude Code hooks", num_results=3, include_domains=["docs.claude.com"])
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "number",
                        "description": "Number of results (default: 5)",
                        "default": 5
                    },
                    "include_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter results to specific domains"
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="docfork_search",
            description="""Search GitHub documentation (Docfork local fallback).

Searches markdown docs in GitHub repositories.
Set GITHUB_TOKEN env for better rate limits.

Example:
  docfork_search("FastAPI lifespan events", limit=5)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),

        Tool(
            name="context7_resolve",
            description="""Resolve library ID (Context7 local fallback).

Searches npm + PyPI for library info.

Example:
  context7_resolve("fastapi")  # Returns library metadata
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "library_name": {
                        "type": "string",
                        "description": "Library name (e.g. 'fastapi', 'react')"
                    }
                },
                "required": ["library_name"]
            }
        ),

        Tool(
            name="context7_docs",
            description="""Get library documentation (Context7 local fallback).

Fetches README + docs from GitHub.

Example:
  context7_docs("/npm/fastapi", query="async")
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "library_id": {
                        "type": "string",
                        "description": "Library ID (from context7_resolve)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional filter query",
                        "default": ""
                    }
                },
                "required": ["library_id"]
            }
        ),

        # ═══════════════════════════════════════════════════════
        # SMITHERY TOOLS (MCP Discovery + Execution)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="discover_mcp",
            description="""Discover MCPs by capability from Smithery registry (4000+ MCPs).

ZERO pollution: MCPs discovered on-demand, cached in PostgreSQL (24h TTL).

Returns: List of matching MCPs with tools and usage instructions.

Example:
  discover_mcp("search", limit=3)
""",
            inputSchema={
                "type": "object",
                "properties": {
                    "capability": {
                        "type": "string",
                        "description": "Capability needed (search, browser, database, web, ai, vector, etc.)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max results (default: 3)",
                        "default": 3
                    }
                },
                "required": ["capability"]
            }
        ),

        Tool(
            name="use_mcp",
            description="""Execute tool on any MCP via Smithery HTTP API (4000+ MCPs available).

ZERO installation: Direct HTTP calls to https://server.smithery.ai/{mcp_id}/mcp
NO subprocess, NO npx, NO process management.
Smithery handles everything server-side (caching, scaling, etc.)

Example:
  use_mcp("exa", "web_search_exa", {"query": "RAG 2025", "num_results": 5})
  use_mcp("@upstash/context7-mcp", "resolve-library-id", {"libraryName": "react"})
  use_mcp("@smithery-ai/fetch", "fetch_url", {"url": "https://example.com"})

Note: Tool names vary per MCP (use discover_mcp or check CLAUDE.md)
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
                        "description": "Tool arguments (JSON object)"
                    }
                },
                "required": ["mcp_id", "tool", "args"]
            }
        ),

        Tool(
            name="list_my_mcps",
            description="""Liste TOUS les MCPs Smithery déjà utilisés avec leurs tools disponibles.

Cette "bibliothèque personnelle" montre:
- Les MCPs que tu as déjà utilisés
- Les noms EXACTS des tools disponibles (plus besoin de deviner!)
- Le nombre d'utilisations de chaque MCP
- La dernière fois qu'ils ont été utilisés

Utilise ceci AVANT use_mcp pour connaître le nom exact du tool!

Returns: Liste de {mcp_id, tools: [...], call_count, last_used}

Example:
  list_my_mcps()
  → [{
      "mcp_id": "@smithery-ai/fetch",
      "tools": ["fetch_url", "extract_elements"],
      "call_count": 5,
      "last_used": "2025-10-18"
    }]
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # ═══════════════════════════════════════════════════════
        # BOOTSTRAP TOOL (Auto-load context on startup)
        # ═══════════════════════════════════════════════════════

        Tool(
            name="bootstrap_agi",
            description="""🧠 BOOTSTRAP AUTOMATIQUE DU SYSTÈME AGI

EXÉCUTER EN PREMIER au démarrage de chaque conversation.

Charge automatiquement depuis PostgreSQL:
1. Instructions de bootstrap (system_bootstrap)
2. Contexte de session actif (active_context)
3. Règles système (system_rules)
4. Tâches en cours (worker_tasks)
5. Instructions en attente (pending_instructions)

Retourne un contexte formaté prêt à utiliser avec TOUTES les informations
nécessaires pour continuer le travail là où il était.

AUCUN fichier .md requis - tout vient de la database.

Returns: {
  session_id: UUID de la session,
  bootstrap_instructions: [...],
  active_rules: [...],
  running_tasks: [...],
  pending_actions: [...],
  context_variables: {...},
  ready: true
}

Example:
  bootstrap_agi()
  → Retourne tout le contexte système formaté
""",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    ]


async def _create_tool_response(result: Any, text_content: str = None) -> list[TextContent]:
    """Helper to create and auto-save tool response"""
    response_text = text_content or json.dumps(result, indent=2, default=str)
    response = [TextContent(type="text", text=response_text)]

    # Auto-memory: Wrap response AFTER execution
    if auto_memory:
        try:
            await auto_memory.wrap_assistant_response(response_text)
        except Exception as e:
            logger.warning(f"Failed to wrap assistant response: {e}")

    return response


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls - UNIFIED VERSION (4 tools) + Auto-memory wrapper"""

    # Auto-memory: Wrap tool call BEFORE execution
    if auto_memory:
        try:
            await auto_memory.wrap_tool_call(name, arguments)
        except Exception as e:
            logger.warning(f"Failed to wrap tool call: {e}")

    try:
        # ═══════════════════════════════════════════════════════
        # 1. THINK - Outil principal (cascade automatique)
        # ═══════════════════════════════════════════════════════

        if name == "think":
            result = await think(
                arguments["query"],
                arguments.get("context")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # 2. MEMORY - Unifié (search/store/stats)
        # ═══════════════════════════════════════════════════════

        elif name == "memory":
            action = arguments["action"]

            if action == "search":
                result = await memory_search(
                    arguments["query"],
                    arguments.get("limit", 5),
                    arguments.get("tags", [])
                )
            elif action == "store":
                result = await memory_store(
                    arguments["text"],
                    arguments["type"],
                    arguments.get("tags", []),
                    arguments.get("project", "default")
                )
            elif action == "stats":
                result = await memory_stats()
            else:
                raise ValueError(f"Unknown memory action: {action}")

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # 3. DATABASE - Unifié (query/execute/tables/schema/stats)
        # ═══════════════════════════════════════════════════════

        elif name == "database":
            action = arguments["action"]

            if action == "query":
                result = await pg_query(
                    arguments["sql"],
                    arguments.get("params", [])
                )
            elif action == "execute":
                rows_affected = await pg_execute(
                    arguments["sql"],
                    arguments.get("params", [])
                )
                result = {"rows_affected": rows_affected, "success": True}
            elif action == "tables":
                result = await pg_tables()
            elif action == "schema":
                result = await pg_schema(arguments["table_name"])
            elif action == "stats":
                result = await pg_stats()
            else:
                raise ValueError(f"Unknown database action: {action}")

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        # ═══════════════════════════════════════════════════════
        # 4. CONTROL - Unifié (bootstrap/agent/mcp/consolidate)
        # ═══════════════════════════════════════════════════════

        elif name == "control":
            action = arguments["action"]

            if action == "bootstrap":
                result = await bootstrap_agi()
            elif action == "agent":
                result = await execute_agent_direct(
                    arguments["prompt"],
                    arguments.get("output_format", "stream-json"),
                    arguments.get("timeout", 120)
                )
            elif action == "discover_mcp":
                result = await discover_mcp(
                    arguments["capability"],
                    arguments.get("limit", 3)
                )
            elif action == "use_mcp":
                result = await use_mcp(
                    arguments["mcp_id"],
                    arguments["tool"],
                    arguments["args"]
                )
            elif action == "list_mcps":
                result = await list_my_mcps()
            elif action == "consolidate":
                result = await consolidate_rules()
            else:
                raise ValueError(f"Unknown control action: {action}")

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        # ═══════════════════════════════════════════════════════
        # SEARCH TOOLS (Local)
        # ═══════════════════════════════════════════════════════

        elif name == "exa_search":
            if not LOCAL_SEARCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local search not available"
                }, indent=2))]

            result = await exa_search(
                arguments["query"],
                arguments.get("num_results", 5),
                arguments.get("include_domains")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "docfork_search":
            if not LOCAL_SEARCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local search not available"
                }, indent=2))]

            result = await docfork_search(
                arguments["query"],
                arguments.get("limit", 5)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "context7_resolve":
            if not LOCAL_SEARCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local search not available"
                }, indent=2))]

            result = await context7_resolve_library(arguments["library_name"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "context7_docs":
            if not LOCAL_SEARCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local search not available"
                }, indent=2))]

            result = await context7_get_docs(
                arguments["library_id"],
                arguments.get("query", "")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        # ═══════════════════════════════════════════════════════
        # OLD TOOLS (backwards compatibility, will be removed)
        # ═══════════════════════════════════════════════════════

        elif name == "memory_search":
            result = await memory_search(
                arguments["query"],
                arguments.get("limit", 5),
                arguments.get("tags", [])
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "memory_store":
            result = await memory_store(
                arguments["text"],
                arguments["type"],
                arguments.get("tags", []),
                arguments.get("project", "default")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "memory_stats":
            result = await memory_stats()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # POSTGRESQL TOOLS
        # ═══════════════════════════════════════════════════════

        elif name == "pg_query":
            result = await pg_query(
                arguments["sql"],
                arguments.get("params", [])
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "pg_execute":
            rows_affected = await pg_execute(
                arguments["sql"],
                arguments.get("params", [])
            )
            return [TextContent(
                type="text",
                text=json.dumps({"rows_affected": rows_affected, "success": True}, indent=2)
            )]

        elif name == "pg_tables":
            result = await pg_tables()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pg_schema":
            result = await pg_schema(arguments["table_name"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "pg_stats":
            result = await pg_stats()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # AGENT TOOLS
        # ═══════════════════════════════════════════════════════

        elif name == "launch_agent":
            result = await launch_agent(
                arguments["agent_type"],
                arguments["task"],
                arguments.get("wait", False),
                arguments.get("timeout", 60)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_agent_result":
            result = await get_agent_result(arguments["task_id"])
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "list_agents":
            result = await list_agents()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "execute_agent_direct":
            result = await execute_agent_direct(
                arguments["prompt"],
                arguments.get("output_format", "stream-json"),
                arguments.get("timeout", 120)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # WEB FETCH TOOLS (Local)
        # ═══════════════════════════════════════════════════════

        elif name == "fetch_url":
            if not LOCAL_FETCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local fetch not available",
                    "install": "pip install httpx beautifulsoup4"
                }, indent=2))]

            result = await local_fetch(
                arguments["url"],
                arguments.get("max_length", 50000)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "extract_elements":
            if not LOCAL_FETCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local fetch not available"
                }, indent=2))]

            result = await local_extract(
                arguments["url"],
                arguments["selector"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "get_page_metadata":
            if not LOCAL_FETCH_AVAILABLE:
                return [TextContent(type="text", text=json.dumps({
                    "error": "Local fetch not available"
                }, indent=2))]

            result = await local_metadata(arguments["url"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # SMITHERY TOOLS
        # ═══════════════════════════════════════════════════════

        elif name == "discover_mcp":
            result = await discover_mcp(
                arguments["capability"],
                arguments.get("limit", 3)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "use_mcp":
            result = await use_mcp(
                arguments["mcp_id"],
                arguments["tool"],
                arguments["args"]
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        elif name == "list_my_mcps":
            result = await list_my_mcps()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ═══════════════════════════════════════════════════════
        # BOOTSTRAP TOOL
        # ═══════════════════════════════════════════════════════

        elif name == "bootstrap_agi":
            result = await bootstrap_agi()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        error_response = [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "tool": name}, indent=2)
        )]
        # Auto-memory: Wrap error response AFTER execution
        if auto_memory:
            try:
                await auto_memory.wrap_assistant_response(str(e))
            except Exception as wrap_err:
                logger.warning(f"Failed to wrap error response: {wrap_err}")
        return error_response


# ═══════════════════════════════════════════════════════
# MEMORY IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════

async def memory_search(query: str, limit: int = 5, tags: list = None) -> dict:
    """Search memory using hybrid RAG with auto-reinforcement (LTP)"""

    async with db_pool.acquire() as conn:
        # Simple text search for now (can upgrade to pgvector later)
        sql = """
            SELECT id, section, content, tags, priority, created_at, strength, access_count
            FROM agi_knowledge
            WHERE content ILIKE $1
        """

        if tags:
            sql += " AND tags && $2"
            rows = await conn.fetch(sql + " LIMIT $3", f"%{query}%", tags, limit)
        else:
            rows = await conn.fetch(sql + " LIMIT $2", f"%{query}%", limit)

        # 🧠 AUTO-REINFORCEMENT (LTP - Long Term Potentiation)
        # Renforcer patterns utilisés, comme Neo4j le fait déjà pour Files/Rules
        for row in rows:
            await conn.execute("""
                UPDATE agi_knowledge
                SET access_count = access_count + 1,
                    last_accessed = NOW(),
                    strength = LEAST(1.0, COALESCE(strength, 0.5) + 0.05)
                WHERE id = $1
            """, row['id'])

        return {
            "results": [
                {
                    "section": row["section"],
                    "content": row["content"],
                    "tags": row["tags"],
                    "priority": row["priority"],
                    "created_at": str(row["created_at"]),
                    "strength": row["strength"],
                    "access_count": row["access_count"]
                }
                for row in rows
            ],
            "count": len(rows)
        }


async def memory_store(text: str, type: str, tags: list = None, project: str = "default", sync_neo4j: bool = True) -> dict:
    """Store memory with auto-embeddings, LTP initialization, and Neo4j sync"""

    async with db_pool.acquire() as conn:
        # 🧠 Générer embedding Voyage AI si disponible
        embedding = None
        if VOYAGE_COHERE_AVAILABLE:
            try:
                embedding = await embed_single(text)
                logger.info(f"✅ Embedding generated for memory: {len(embedding)} dimensions")
            except Exception as e:
                logger.warning(f"⚠️  Failed to generate embedding: {e}")

        # 🧠 Initialiser strength=0.5, access_count=0 (comme Neo4j Files)
        result = await conn.fetchrow("""
            INSERT INTO agi_knowledge (section, content, tags, priority, strength, access_count, embedding)
            VALUES ($1, $2, $3, 5, 0.5, 0, $4)
            RETURNING id, strength, access_count
        """, type, text, tags or [], embedding)

        memory_id = str(result["id"])

        # 🔄 Sync vers Neo4j automatiquement (optionnel)
        neo4j_synced = False
        if sync_neo4j:
            try:
                sync_result = await sync_memory_to_neo4j(memory_id)
                neo4j_synced = sync_result.get("synced", 0) > 0
                logger.info(f"✅ Memory synced to Neo4j: {neo4j_synced}")
            except Exception as e:
                logger.warning(f"⚠️  Neo4j sync failed: {e}")

        return {
            "memory_id": memory_id,
            "status": "stored",
            "strength": result["strength"],
            "access_count": result["access_count"],
            "has_embedding": embedding is not None,
            "neo4j_synced": neo4j_synced,
            "layer": "L2"  # Short-term memory (nouvellement créé)
        }


async def memory_stats() -> dict:
    """Get memory statistics"""

    async with db_pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM agi_knowledge")

        by_section = await conn.fetch("""
            SELECT section, COUNT(*) as count
            FROM agi_knowledge
            GROUP BY section
            ORDER BY count DESC
        """)

        return {
            "total_memories": total,
            "by_section": {row["section"]: row["count"] for row in by_section}
        }


async def sync_memory_to_neo4j(memory_id: str = None) -> dict:
    """
    🔄 SYNC PostgreSQL agi_knowledge ↔ Neo4j

    Synchronise mémoires PostgreSQL vers Neo4j pour spreading activation
    - Crée node Knowledge dans Neo4j
    - Link concepts automatiquement
    - Bidirectionnel: Neo4j strength ↔ PostgreSQL strength

    Args:
        memory_id: Si fourni, sync seulement cette mémoire. Sinon sync toutes.
    """
    if not db_pool:
        return {"error": "Database pool not initialized"}

    async with db_pool.acquire() as conn:
        # Récupérer mémoires à synchroniser
        if memory_id:
            memories = await conn.fetch("""
                SELECT id, section, content, tags, strength, access_count
                FROM agi_knowledge WHERE id = $1
            """, memory_id)
        else:
            # Sync seulement celles pas encore synced ou strength changée
            memories = await conn.fetch("""
                SELECT id, section, content, tags, strength, access_count
                FROM agi_knowledge
                LIMIT 100
            """)

    if not memories:
        return {"synced": 0, "message": "No memories to sync"}

    # Connect Neo4j
    from neo4j import AsyncGraphDatabase
    neo4j_driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Voiture789")
    )

    synced_count = 0

    try:
        async with neo4j_driver.session() as session:
            for mem in memories:
                # Créer node Knowledge dans Neo4j
                await session.run("""
                    MERGE (k:Knowledge {id: $id})
                    ON CREATE SET
                        k.section = $section,
                        k.content = $content,
                        k.tags = $tags,
                        k.strength = $strength,
                        k.access_count = $access_count,
                        k.created_at = datetime()
                    ON MATCH SET
                        k.strength = $strength,
                        k.access_count = $access_count,
                        k.last_synced = datetime()
                """,
                    id=str(mem['id']),
                    section=mem['section'],
                    content=mem['content'][:500],  # Limite pour Neo4j
                    tags=mem['tags'] or [],
                    strength=mem['strength'] or 0.5,
                    access_count=mem['access_count'] or 0
                )

                # Link concepts (simple pour l'instant: même section = lien)
                await session.run("""
                    MATCH (k1:Knowledge {id: $id})
                    MATCH (k2:Knowledge {section: $section})
                    WHERE k1.id <> k2.id
                    MERGE (k1)-[r:RELATED_TO]->(k2)
                    ON CREATE SET r.strength = 0.3, r.created = datetime()
                """, id=str(mem['id']), section=mem['section'])

                synced_count += 1

        await neo4j_driver.close()

        return {
            "synced": synced_count,
            "message": f"Synchronized {synced_count} memories to Neo4j"
        }

    except Exception as e:
        logger.error(f"Neo4j sync error: {e}")
        return {"error": str(e), "synced": synced_count}


# ═══════════════════════════════════════════════════════
# POSTGRESQL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════

async def pg_query(sql: str, params: list = None) -> list[dict]:
    """Execute SELECT query"""

    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries allowed. Use pg_execute for modifications.")

    async with db_pool.acquire() as conn:
        if params:
            rows = await conn.fetch(sql, *params)
        else:
            rows = await conn.fetch(sql)

        return [dict(row) for row in rows]


async def pg_execute(sql: str, params: list = None) -> int:
    """Execute INSERT/UPDATE/DELETE"""

    async with db_pool.acquire() as conn:
        if params:
            result = await conn.execute(sql, *params)
        else:
            result = await conn.execute(sql)

        if result:
            parts = result.split()
            if len(parts) >= 2:
                return int(parts[-1])

        return 0


async def pg_tables() -> list[dict]:
    """List all tables"""

    async with db_pool.acquire() as conn:
        tables = await conn.fetch("""
            SELECT
                tablename as table_name,
                pg_total_relation_size('public.'||tablename)::bigint as size_bytes,
                (SELECT COUNT(*) FROM information_schema.columns
                 WHERE table_schema = 'public' AND table_name = tablename) as column_count
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        result = []
        for table in tables:
            table_dict = dict(table)
            row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            table_dict['row_count'] = row_count
            result.append(table_dict)

        return result


async def pg_schema(table_name: str) -> dict:
    """Get table schema"""

    async with db_pool.acquire() as conn:
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """, table_name)

        constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'public' AND table_name = $1
        """, table_name)

        return {
            "table_name": table_name,
            "columns": [dict(col) for col in columns],
            "constraints": [dict(c) for c in constraints]
        }


async def pg_stats() -> dict:
    """Get database statistics"""

    async with db_pool.acquire() as conn:
        db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'
        """)

        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        total_rows = 0
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
            total_rows += count

        active_conn = await conn.fetchval("""
            SELECT COUNT(*) FROM pg_stat_activity
            WHERE datname = current_database() AND state = 'active'
        """)

        return {
            "database": "agi_db",
            "size_bytes": db_size,
            "size_mb": round(db_size / 1024 / 1024, 2),
            "table_count": table_count,
            "total_rows": total_rows,
            "active_connections": active_conn
        }


# ═══════════════════════════════════════════════════════
# AGENT IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════

async def launch_agent(agent_type: str, task: str, wait: bool = False, timeout: int = 60) -> dict:
    """Launch headless agent"""

    import subprocess
    from uuid import uuid4

    # Insert task in worker_tasks
    task_id = uuid4()

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO worker_tasks (id, task_type, instructions, status)
            VALUES ($1, 'research', $2::jsonb, 'pending')
        """, task_id, json.dumps({"query": task, "agent": agent_type}))

    logger.info(f"✅ Agent launched: {agent_type} - Task: {task_id}")

    # If wait=False, return immediately
    if not wait:
        return {
            "task_id": str(task_id),
            "status": "pending",
            "agent_type": agent_type,
            "non_blocking": True
        }

    # If wait=True, poll for result
    import asyncio

    for _ in range(timeout // 2):
        await asyncio.sleep(2)

        async with db_pool.acquire() as conn:
            task = await conn.fetchrow("""
                SELECT status, result, error
                FROM worker_tasks
                WHERE id = $1
            """, task_id)

            if task["status"] in ("success", "failed"):
                result = task["result"]
                if isinstance(result, str):
                    result = json.loads(result)

                return {
                    "task_id": str(task_id),
                    "status": task["status"],
                    "result": result,
                    "error": task["error"]
                }

    # Timeout reached
    return {
        "task_id": str(task_id),
        "status": "timeout",
        "message": f"Agent did not complete within {timeout}s. Check later with get_agent_result()"
    }


async def get_agent_result(task_id: str) -> dict:
    """Get agent task result"""

    from uuid import UUID

    try:
        task_uuid = UUID(task_id)
    except:
        return {"error": "Invalid task_id format"}

    async with db_pool.acquire() as conn:
        task = await conn.fetchrow("""
            SELECT status, result, error, created_at, completed_at
            FROM worker_tasks
            WHERE id = $1
        """, task_uuid)

        if not task:
            return {"error": "Task not found", "task_id": task_id}

        result = task["result"]
        if result and isinstance(result, str):
            result = json.loads(result)

        return {
            "task_id": task_id,
            "status": task["status"],
            "result": result,
            "error": task["error"],
            "created_at": str(task["created_at"]),
            "completed_at": str(task["completed_at"]) if task["completed_at"] else None
        }


async def list_agents() -> list[dict]:
    """List available agents"""

    async with db_pool.acquire() as conn:
        agents = await conn.fetch("""
            SELECT agent_type, model, LEFT(system_prompt, 100) as description
            FROM agent_prompts
            ORDER BY agent_type
        """)

        return [
            {
                "agent_type": agent["agent_type"],
                "model": agent["model"],
                "description": agent["description"],
                "speed_estimate": "20-40s"
            }
            for agent in agents
        ]


async def execute_agent_direct(prompt: str, output_format: str = "stream-json", timeout: int = 120) -> dict:
    """
    Execute agent directly with claude --print (Alternative to worker daemon)

    Pattern from Claude Code docs: claude --print for direct execution.
    NO database polling, NO worker daemon - pure subprocess execution.
    """

    import subprocess
    import asyncio

    # Build command
    cmd = ["claude", "--print", prompt]

    if output_format == "stream-json":
        cmd.extend(["--output-format", "stream-json"])

    logger.info(f"📡 Executing direct: {' '.join(cmd[:3])}... (timeout: {timeout}s)")

    try:
        # Run claude --print
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        stdout_str = stdout.decode('utf-8') if stdout else ""
        stderr_str = stderr.decode('utf-8') if stderr else ""

        # Parse JSON output if stream-json
        output_json = None
        if output_format == "stream-json" and stdout_str:
            try:
                # Try to parse each line as JSON
                json_results = []
                for line in stdout_str.strip().split('\n'):
                    if line.strip():
                        try:
                            json_results.append(json.loads(line))
                        except:
                            pass
                output_json = json_results if json_results else None
            except Exception as e:
                logger.warning(f"JSON parse error: {e}")

        return {
            "status": "success" if process.returncode == 0 else "failed",
            "returncode": process.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "output_json": output_json,
            "pattern": "claude-print-direct"
        }

    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout}s")
        return {
            "status": "timeout",
            "error": f"Execution exceeded {timeout}s",
            "pattern": "claude-print-direct"
        }
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "pattern": "claude-print-direct"
        }


# ═══════════════════════════════════════════════════════════
# SMITHERY IMPLEMENTATIONS (Discovery + Execution)
# ═══════════════════════════════════════════════════════════

async def discover_mcp(capability: str, limit: int = 3) -> dict:
    """
    Discover MCPs by capability (COUCHE 2: Smithery Gateway)

    1. Check PostgreSQL cache (24h TTL)
    2. If cache MISS → Smithery Registry API
    3. Store in cache with capabilities
    4. Return matching MCPs
    """

    # 1. Check cache
    async with db_pool.acquire() as conn:
        cached = await conn.fetch("""
            SELECT mcp_id, display_name, description, tools, smithery_url
            FROM known_mcps
            WHERE $1 = ANY(capabilities)
            AND (last_used > NOW() - INTERVAL '24 hours'
                 OR created_at > NOW() - INTERVAL '24 hours')
            ORDER BY usage_count DESC
            LIMIT $2
        """, capability, limit)

    if cached:
        logger.info(f"✅ Cache HIT for '{capability}' ({len(cached)} MCPs)")

        results = []
        for row in cached:
            tools_data = row["tools"]
            if isinstance(tools_data, str):
                tools_data = json.loads(tools_data)

            results.append({
                "mcp_id": row["mcp_id"],
                "display_name": row["display_name"],
                "description": row["description"],
                "available_tools": tools_data,
                "how_to_use": f"use_mcp('{row['mcp_id']}', 'tool_name', {{}})",
                "source": "cache"
            })

        return {
            "capability": capability,
            "count": len(results),
            "mcps": results,
            "instructions": "Use use_mcp(mcp_id, tool, args) to execute."
        }

    # 2. Cache MISS → Smithery Registry API
    logger.info(f"🔍 Cache MISS for '{capability}', searching Smithery...")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                SMITHERY_REGISTRY_URL,
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
                    "message": f"No MCPs found for '{capability}'"
                }

            # 3. Cache discovered MCPs
            results = []

            for server in servers[:limit]:
                mcp_id = server.get("qualifiedName")
                smithery_url = f"https://server.smithery.ai/{mcp_id}/mcp?profile={SMITHERY_PROFILE}"

                # Infer capabilities
                capabilities = infer_capabilities(
                    server.get("description", ""),
                    server.get("category", ""),
                    [capability]
                )

                async with db_pool.acquire() as conn:
                    await conn.execute("""
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

                results.append({
                    "mcp_id": mcp_id,
                    "display_name": server.get("displayName"),
                    "description": server.get("description"),
                    "available_tools": server.get("tools", []),
                    "how_to_use": f"use_mcp('{mcp_id}', 'tool_name', {{}})",
                    "source": "registry"
                })

                logger.info(f"📦 Cached {mcp_id} with capabilities: {capabilities}")

            return {
                "capability": capability,
                "count": len(results),
                "mcps": results,
                "instructions": "MCPs discovered and cached. Use use_mcp() to execute."
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
    """Infer capabilities from MCP metadata"""

    capabilities = set(hints)
    text = f"{description} {category}".lower()

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


async def use_mcp(mcp_id: str, tool: str, args: dict) -> dict:
    """
    Execute MCP tool - HYBRID: Local first, Smithery fallback

    PRIORITÉ 1: MCPs locaux hébergés (exa, context7, fetch)
    PRIORITÉ 2: Smithery HTTP API (4000+ MCPs)

    Avantages MCPs locaux:
    - Pas de token API nécessaire
    - Latence ultra-faible (<50ms)
    - Contrôle total
    - Pas de rate limits

    Avantages Smithery:
    - 4000+ MCPs disponibles
    - Pas d'installation locale
    - Scaling automatique
    """
    # PRIORITÉ 1: Essayer MCP local d'abord
    if LOCAL_MCP_ROUTER_AVAILABLE and mcp_id in ["exa", "context7", "fetch"]:
        logger.info(f"🏠 Local MCP call to {mcp_id}.{tool}({args})")
        try:
            result = await route_mcp_call(mcp_id, tool, args)
            logger.info(f"✅ {mcp_id}.{tool} executed locally")
            return {"content": result, "source": "local"}
        except Exception as e:
            logger.warning(f"⚠️  Local MCP failed, trying Smithery fallback: {e}")
            # Continue to Smithery fallback

    # PRIORITÉ 2: Smithery HTTP
    logger.info(f"🌐 Smithery HTTP call to {mcp_id}.{tool}({args})")

    try:
        # Smithery HTTP endpoint
        url = f"https://server.smithery.ai/{mcp_id}/mcp"

        # JSON-RPC 2.0 request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": args
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                json=request_data,
                params={"profile": SMITHERY_PROFILE},
                headers={
                    "Authorization": f"Bearer {SMITHERY_API_KEY}",
                    "Content-Type": "application/json"
                }
            )

            response.raise_for_status()
            result = response.json()

            # Check for JSON-RPC error
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                raise Exception(f"MCP error: {error_msg}")

            # Update usage stats
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO smithery_mcp_cache (mcp_id, call_count, last_used)
                    VALUES ($1, 1, NOW())
                    ON CONFLICT (mcp_id) DO UPDATE
                    SET call_count = smithery_mcp_cache.call_count + 1,
                        last_used = NOW()
                """, mcp_id)

            logger.info(f"✅ {mcp_id}.{tool} executed via HTTP")

            return result.get("result", result)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"Smithery HTTP error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"use_mcp error: {e}")
        raise


async def list_my_mcps() -> dict:
    """
    Liste tous les MCPs Smithery déjà utilisés avec leurs tools disponibles

    Retourne la "bibliothèque personnelle" de MCPs avec les noms exacts des tools
    """

    async with db_pool.acquire() as conn:
        mcps = await conn.fetch("""
            SELECT mcp_id, tools, call_count, last_used, created_at
            FROM smithery_mcp_cache
            ORDER BY call_count DESC, last_used DESC
        """)

    results = []
    for row in mcps:
        results.append({
            "mcp_id": row['mcp_id'],
            "tools": row['tools'] if row['tools'] else [],
            "call_count": row['call_count'],
            "last_used": row['last_used'].isoformat() if row['last_used'] else None,
            "first_used": row['created_at'].isoformat() if row['created_at'] else None
        })

    return {
        "my_mcps": results,
        "total_count": len(results),
        "instructions": "Use use_mcp(mcp_id, tool_name, args) with exact tool names from 'tools' list"
    }


# ═══════════════════════════════════════════════════════════
# SUPER-TOOL: think() - UN SEUL outil surpuissant qui gère TOUT
# ═══════════════════════════════════════════════════════════

async def think(query: str, context: dict = None) -> dict:
    """
    🧠 THINK - L'outil SURPUISSANT qui gère tout en CASCADE

    Comme cerveau humain: tu PENSES, tout le reste se déclenche automatiquement

    Cascade automatique:
    1. Bootstrap (L1 rules + session)
    2. Memory search (L2 spreading activation)
    3. Code awareness (L3 codebase)
    4. Store new learnings
    5. Reinforce patterns utilisés (LTP)
    6. Return contexte complet

    Args:
        query: Ta pensée/question/intention
        context: Contexte optionnel {file, action, data}

    Returns:
        {
            "understanding": "Ce que j'ai compris",
            "L1": {...},  # Working memory (rules + current context)
            "L2": {...},  # Short-term (session + recent files)
            "L3": {...},  # Long-term (knowledge + codebase)
            "actions": []  # Actions suggérées
        }
    """
    if not db_pool:
        await init_db()

    result = {
        "query": query,
        "understanding": "",
        "L1": {},
        "L2": {},
        "L3": {},
        "actions": []
    }

    try:
        # CASCADE 1: Bootstrap L1 (working memory)
        bootstrap_result = await bootstrap_agi()
        result["L1"] = {
            "rules": bootstrap_result.get("reinforced_rules", [])[:3],  # Top-3
            "session_id": bootstrap_result.get("session", {}).get("session_id"),
            "phase": bootstrap_result.get("session", {}).get("phase")
        }

        # CASCADE 2: Memory search L2/L3 (spreading activation)
        from neo4j import AsyncGraphDatabase
        neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Voiture789")
        )

        async with neo4j_driver.session() as session:
            # L2: Recent files (today's edits)
            recent_files = await session.run("""
                MATCH (s:Session {id: "current"})-[:EDITED_TODAY]->(f:File)
                RETURN f.name as name, f.path as path, f.strength as strength
                ORDER BY f.strength DESC
                LIMIT 5
            """)

            l2_files = []
            async for record in recent_files:
                l2_files.append({
                    "name": record["name"],
                    "path": record["path"],
                    "strength": record["strength"]
                })

            result["L2"]["recent_files"] = l2_files

            # L3: Memory search (spreading activation)
            memories = await memory_search(query, limit=3)
            result["L3"]["memories"] = memories.get("results", [])

        await neo4j_driver.close()

        # CASCADE 3: Understanding (analyze query)
        context = context or {}

        # Special case: bootstrap query
        if query.lower() in ["bootstrap", "start", "init", "démarrage"]:
            result["understanding"] = "Bootstrap request → returning full brain context"
            result["actions"].append("bootstrapped")
            result["bootstrap_mode"] = True
            return result

        if "file" in context or "code" in query.lower():
            result["understanding"] = "Code-related query → activating codebase knowledge"
            result["actions"].append("search_codebase")
        elif "memory" in query.lower() or "remember" in query.lower():
            result["understanding"] = "Memory query → spreading activation in L3"
            result["actions"].append("deep_search")
        else:
            result["understanding"] = "General query → using L1 rules + L2 context"
            result["actions"].append("use_working_memory")

        # CASCADE 4: Auto-reinforce (LTP)
        # Patterns utilisés dans cette pensée → strength +0.05
        if l2_files:
            async with neo4j_driver.session() as session:
                for file in l2_files[:2]:  # Top-2 files
                    await session.run("""
                        MATCH (f:File {path: $path})
                        SET f.strength = CASE
                            WHEN f.strength + 0.05 > 1.0 THEN 1.0
                            ELSE f.strength + 0.05
                        END
                    """, path=file["path"])

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"think() cascade failed: {e}")
        result["error"] = str(e)
        result["success"] = False
        return result


# ═══════════════════════════════════════════════════════════
# CODE AWARENESS - Auto-track edits in Neo4j (L1/L2/L3)
# ═══════════════════════════════════════════════════════════

async def track_code_edit(file_path: str, content: str, edit_type: str = "modified") -> dict:
    """
    🧠 AUTO-AWARENESS: Track code edits dans Neo4j avec cascade

    Comme cerveau humain:
    - L1: Current file/function → working memory
    - L2: Today's edits → short-term session
    - L3: All code → long-term structure
    - Spreading activation → cascade automatique

    Args:
        file_path: Path du fichier édité
        content: Contenu (pour parser functions/classes)
        edit_type: "created", "modified", "deleted"

    Returns:
        {
            "stored": True,
            "layer": "L2",  # L1 si très utilisé, L2 si récent, L3 si ancien
            "cascaded": [list of related concepts activated],
            "strength": 0.5  # Reinforcement strength
        }
    """
    if not db_pool:
        await init_db()

    try:
        from neo4j import AsyncGraphDatabase

        neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Voiture789")
        )

        # Extract file info
        file_name = file_path.split('/')[-1]
        extension = file_name.split('.')[-1] if '.' in file_name else ''

        # Create or update File concept in Neo4j
        async with neo4j_driver.session() as session:
            # 1. Store/update file concept
            result = await session.run("""
                MERGE (f:File {path: $path})
                ON CREATE SET
                    f.name = $name,
                    f.extension = $ext,
                    f.strength = 0.5,
                    f.access_count = 1,
                    f.created_at = datetime(),
                    f.last_modified = datetime()
                ON MATCH SET
                    f.access_count = f.access_count + 1,
                    f.last_modified = datetime(),
                    f.strength = CASE
                        WHEN f.strength + 0.1 > 1.0 THEN 1.0
                        ELSE f.strength + 0.1
                    END
                RETURN f.strength as strength, f.access_count as accesses
            """, path=file_path, name=file_name, ext=extension)

            file_record = await result.single()

            # 2. Add to session (L2 - today's work)
            await session.run("""
                MERGE (s:Session {id: "current"})
                ON CREATE SET s.created_at = datetime()
                WITH s

                MATCH (f:File {path: $path})
                MERGE (s)-[r:EDITED_TODAY]->(f)
                ON CREATE SET r.count = 1, r.last_edit = datetime()
                ON MATCH SET r.count = r.count + 1, r.last_edit = datetime()
            """, path=file_path)

            # 3. Spreading activation cascade (find related)
            cascade_result = await session.run("""
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[:IMPORTS|CALLS|USES*1..2]-(related)
                WHERE related:File OR related:Function
                RETURN DISTINCT related.name as name, related.path as path
                LIMIT 5
            """, path=file_path)

            cascaded = []
            async for record in cascade_result:
                if record["name"]:
                    cascaded.append(record["name"])

        await neo4j_driver.close()

        # Determine layer based on strength
        strength = file_record["strength"]
        if strength >= 0.7:
            layer = "L1"  # Working memory (hot)
        elif strength >= 0.3:
            layer = "L2"  # Short-term (warm)
        else:
            layer = "L3"  # Long-term (cold)

        return {
            "stored": True,
            "file": file_name,
            "layer": layer,
            "strength": strength,
            "accesses": file_record["accesses"],
            "cascaded": cascaded,
            "message": f"File tracked in {layer}, activated {len(cascaded)} related concepts"
        }

    except Exception as e:
        logger.error(f"track_code_edit failed: {e}")
        return {
            "stored": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════
# BOOTSTRAP IMPLEMENTATION
# ═══════════════════════════════════════════════════════════

async def consolidate_rules() -> dict:
    """
    🧠 LTD - Long-Term Depression: Weaken unused rules

    Comme cerveau humain pendant le sommeil:
    - Rules non utilisées récemment → strength ↓ (décroissance exponentielle)
    - Libère "working memory" pour rules importantes
    - Exécuter pendant idle time (nuit, weekends)

    Returns:
        {
            "weakened_count": int,
            "avg_strength_before": float,
            "avg_strength_after": float,
            "rules_below_threshold": int  # strength < 0.2
        }
    """
    if not db_pool:
        await init_db()

    try:
        from neo4j import AsyncGraphDatabase
        from datetime import datetime, timedelta

        neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Voiture789")
        )

        # LTD: Weaken rules not accessed in last 7 days
        async with neo4j_driver.session() as session:
            # Get stats before
            before = await session.run("""
                MATCH (r:Rule)
                RETURN avg(r.strength) as avg_strength, count(r) as total
            """)
            before_record = await before.single()

            # Apply LTD (decay factor = 0.95 for unused rules)
            result = await session.run("""
                MATCH (r:Rule)
                WHERE r.last_accessed IS NULL
                   OR r.last_accessed < datetime() - duration('P7D')

                // LTD: Exponential decay (0.95 = 5% reduction)
                SET r.strength = CASE
                    WHEN r.strength * 0.95 < 0.1 THEN 0.1  // Floor at 0.1
                    ELSE r.strength * 0.95
                END

                RETURN count(r) as weakened
            """)
            weakened_record = await result.single()

            # Get stats after
            after = await session.run("""
                MATCH (r:Rule)
                RETURN
                    avg(r.strength) as avg_strength,
                    count(CASE WHEN r.strength < 0.2 THEN 1 END) as low_strength
            """)
            after_record = await after.single()

        await neo4j_driver.close()

        return {
            "success": True,
            "weakened_count": weakened_record["weakened"],
            "avg_strength_before": before_record["avg_strength"],
            "avg_strength_after": after_record["avg_strength"],
            "rules_below_threshold": after_record["low_strength"],
            "message": f"LTD applied: {weakened_record['weakened']} rules weakened (unused >7 days)"
        }

    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def bootstrap_agi() -> dict:
    """
    🧠 BOOTSTRAP AUTOMATIQUE DU SYSTÈME AGI

    NOUVELLE APPROCHE - Mémoire associative comme cerveau humain:
    - Utilise memory_search() avec Neo4j graph traversal
    - Voyage AI + Cohere reranking (infra existante)
    - Retourne contexte MINIMAL (~300 tokens) au lieu de tout charger (5000 tokens)
    - Déclencheurs activent fragments pertinents via relations

    Comme un humain: tu te souviens pas de TOUT, mais tu SAIS de quoi tu parles.
    """

    logger.info("🧠 Bootstrapping AGI with memory search + graph traversal...")

    async with db_pool.acquire() as conn:
        # 1. Restaurer session active (critique)
        active_session = await conn.fetchrow("""
            SELECT *
            FROM active_context
            WHERE session_active = true
            ORDER BY updated_at DESC
            LIMIT 1
        """)

        # 2. Check tâches en cours (critique)
        running_tasks = await conn.fetch("""
            SELECT id, task_type, status, created_at, metadata
            FROM worker_tasks
            WHERE status IN ('pending', 'running')
            ORDER BY priority DESC, created_at ASC
            LIMIT 5
        """)

    # 3. 🧠 NEUROTRANSMITTER MODULATION + NEURAL ACTIVATION
    # Comme cerveau humain: activation locale avec décroissance
    # Bootstrap = background task → GABA high, économie maximale
    try:
        from neo4j import AsyncGraphDatabase

        # 🧠 Get neurotransmitter parameters for BACKGROUND query type
        import sys
        from pathlib import Path
        backend_path = str(Path(__file__).parent.parent / 'backend' / 'services')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        from neurotransmitter_system import NeurotransmitterSystem

        neuro = NeurotransmitterSystem(db_pool)
        params = await neuro.modulate(
            query_type='background',  # Bootstrap = économie maximale
            context={'bootstrap': True}
        )

        logger.info(
            f"🧠 Bootstrap neurotransmitters: depth={params['max_depth']}, "
            f"threshold={params['activation_threshold']:.2f}, "
            f"top_k={params['top_k']} (GABA={params['gaba']:.2f})"
        )

        neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Voiture789")
        )

        async with neo4j_driver.session() as session:
            # Spreading activation avec paramètres ADAPTATIFS (neurotransmetteurs!)
            result = await session.run(f"""
                // 1. Chercher concepts de départ
                MATCH (start:Concept)
                WHERE start.content CONTAINS 'system'
                   OR start.content CONTAINS 'rules'
                   OR start.content CONTAINS 'workflow'
                   OR 'system-rule' IN start.tags
                   OR 'bootstrap' IN start.tags
                   OR 'agi-core' IN start.tags

                // 2. Spreading depth ADAPTATIF (neurotransmetteurs!)
                MATCH path = (start)-[:SYNAPSE*0..{params['max_depth']}]-(target:Concept)

                WITH
                    target,
                    length(path) as depth,
                    1.0 / (length(path) + 1) as activation,
                    relationships(path) as synapses

                WHERE activation >= $threshold  // Seuil ADAPTATIF (GABA → seuil haut)

                // 3. LTP - Renforcement ADAPTATIF (dopamine boost!)
                FOREACH (syn in synapses |
                    SET syn.strength = CASE
                        WHEN syn.strength + $ltp_boost > 1.0 THEN 1.0
                        ELSE syn.strength + $ltp_boost
                    END,
                    syn.use_count = syn.use_count + 1,
                    syn.last_used = datetime()
                )

                RETURN DISTINCT
                    target.content as content,
                    target.tags as tags,
                    activation,
                    depth
                ORDER BY activation DESC, depth ASC
                LIMIT $top_k
            """,
                threshold=params['activation_threshold'],
                ltp_boost=params['ltp_strength'],
                top_k=params['top_k']
            )

            neural_fragments = []
            async for record in result:
                neural_fragments.append({
                    "content": record["content"],
                    "tags": record["tags"] or [],
                    "activation": record["activation"],
                    "depth": record["depth"]
                })

        logger.info(f"🧠 Neural activation: {len(neural_fragments)} concepts activated")

        # 🧠 RULES RENFORCÉES (Top-K par strength, adaptatif!)
        # Comme cerveau humain: Charger rules LES PLUS UTILISÉES, pas toutes!
        # IMPORTANT: Faire ça AVANT de fermer le driver!
        reinforced_rules = []
        async with neo4j_driver.session() as session:
            rules_result = await session.run("""
                MATCH (r:Rule)
                // LTP: Renforcer règles accédées
                SET r.last_accessed = datetime(),
                    r.access_count = r.access_count + 1

                RETURN
                    r.essence as essence,
                    r.category as category,
                    r.strength as strength,
                    r.access_count as access_count,
                    r.priority as priority
                ORDER BY r.strength DESC, r.priority DESC
                LIMIT 5
            """)

            async for record in rules_result:
                reinforced_rules.append({
                    "category": record["category"],
                    "essence": record["essence"],
                    "strength": record["strength"],
                    "access_count": record["access_count"],
                    "priority": record["priority"]
                })

        logger.info(f"🧠 Reinforced rules: {len(reinforced_rules)} (top-K by strength)")

        # Maintenant on peut fermer le driver
        await neo4j_driver.close()

    except Exception as e:
        logger.warning(f"Neural activation failed: {e}, using empty context")
        neural_fragments = []

        # Fallback vers system_principles si Neo4j échoue complètement
        reinforced_rules = []
        async with db_pool.acquire() as conn:
            fallback = await conn.fetch("""
                SELECT category, essence, concepts, priority
                FROM system_principles
                WHERE active = true
                ORDER BY priority DESC
            """)
            reinforced_rules = [
                {"category": r["category"], "essence": r["essence"],
                 "strength": 0.5, "access_count": 0, "priority": r["priority"]}
                for r in fallback
            ]

    # Format session info
    session_id = active_session['session_id'] if active_session else None
    context_variables = active_session['context_variables'] if active_session else {}
    conversation_phase = active_session['conversation_phase'] if active_session else 'initialization'

    # Use neural fragments (déclencheurs activés via Neo4j)
    memory_fragments = neural_fragments[:3]  # Top 3 seulement

    result = {
        "ready": True,
        "bootstrap_complete": True,
        "approach": "memory_associative",  # Comme cerveau humain
        "session": {
            "session_id": str(session_id) if session_id else "NEW_SESSION",
            "phase": conversation_phase,
            "context_variables": context_variables,
            "last_updated": str(active_session['updated_at']) if active_session else None
        },
        "memory_fragments": memory_fragments,  # Fragments pertinents (déclencheurs)
        "reinforced_rules": reinforced_rules,  # 🧠 NOUVEAU: Rules adaptatives par usage!
        "running_tasks": [
            {
                "id": str(row["id"]),
                "type": row["task_type"],
                "status": row["status"],
                "created_at": str(row["created_at"]),
                "metadata": row["metadata"]
            }
            for row in running_tasks
        ],
        "instructions": """
🧠 SYSTÈME DE MÉMOIRE ASSOCIATIVE ACTIVÉ

Comme un cerveau humain:
- 4 PRINCIPES généraux chargés (essence, pas 8 rules détaillées!)
- Fragments pertinents via déclencheurs (memory_search + Neo4j)
- Relations traversées automatiquement (graph_depth)
- Cache Redis (instantané)

Pour rules DÉTAILLÉES si besoin:
  → memory_search("critical thinking validation") → trouve rule exacte
  → memory_search("async workers headless") → trouve rule exacte

Tu retiens l'ESSENCE, pas les phrases exactes.
Si besoin détail → Spreading activation trouve.
        """.strip(),
        "summary": f"""
🧠 AGI BOOTSTRAPPED (Reinforcement Learning)

SESSION: {str(session_id) if session_id else 'NEW SESSION'}
PHASE: {conversation_phase}

🎯 RULES RENFORCÉES: {len(reinforced_rules)} (top-K par strength, adaptatif!)
💾 MEMORY FRAGMENTS: {len(memory_fragments)} (top-k pertinents)
🔄 RUNNING TASKS: {len(running_tasks)}

Tokens: ~{len(reinforced_rules) * 15} rules + ~200 fragments = ~{len(reinforced_rules) * 15 + 200} total
Approche: Renforcement naturel comme cerveau humain
- Rules utilisées → Strength ↑ (LTP)
- Rules non utilisées → Strength ↓ (LTD)
- Personnalisation selon TON usage!

READY TO WORK.
        """.strip()
    }

    logger.info(f"✅ Bootstrap complete (memory associative) - Session: {session_id}, Fragments: {len(memory_fragments)}, Tasks: {len(running_tasks)}")

    return result


async def main():
    """Run MCP server"""

    logger.info("🚀 Starting AGI Tools MCP Server...")

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
