"""
MCP Memory System - Integrated with AGI PostgreSQL backend
Direct connection to our memory_store table for persistent context
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from services.memory_service import MemoryService
from services.database import db
from services.redis_client import redis_client
from config.settings import Settings

# Initialize settings
settings = Settings()

class MemorySystemMCP:
    """MCP server integrated with AGI memory system"""

    def __init__(self):
        self.server = Server("agi-memory-system")
        self.memory_service = None
        self._setup_handlers()

    async def initialize(self):
        """Initialise les connexions et le service mémoire (idempotent)"""
        if self.memory_service:
            return

        # Connexion base de données (pool global)
        db_pool = await db.connect()

        # Connexion Redis
        redis = await redis_client.get_client()

        # Instancie le service mémoire avec les connexions partagées
        self.memory_service = MemoryService(
            db_pool=db_pool,
            redis_client=redis
        )

    def _setup_handlers(self):
        """Setup MCP tool handlers"""
        self.tool_handlers = {
            "memory_search": self._handle_memory_search,
            "memory_store": self._handle_memory_store,
            "memory_stats": self._handle_memory_stats,
            "memory_checkpoint": self._handle_memory_checkpoint,
            "memory_restore": self._handle_memory_restore,
        }

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="memory_search",
                    description="Search AGI memories using hybrid RAG (semantic + BM25)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "number", "default": 5},
                            "project": {"type": "string", "description": "Filter by project"},
                            "type": {"type": "string", "description": "Memory type filter"},
                            "include_relations": {"type": "boolean", "default": True}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="memory_store",
                    description="Store memory in AGI system with auto-embedding and indexing",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Memory content"},
                            "type": {"type": "string", "default": "general"},
                            "project": {"type": "string", "description": "Associated project"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "relations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "target_text": {"type": "string"},
                                        "relation_type": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="memory_stats",
                    description="Get AGI memory system statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="memory_checkpoint",
                    description="Create context checkpoint for session continuity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session identifier"},
                            "context": {"type": "string", "description": "Current context to save"}
                        },
                        "required": ["context"]
                    }
                ),
                Tool(
                    name="memory_restore",
                    description="Restore context from checkpoint",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session to restore"}
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if not self.memory_service:
                await self.initialize()

            handler = self.tool_handlers.get(name)
            if handler:
                return await handler(arguments)
            
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    async def _handle_memory_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        results = await self._search_memory(arguments)
        return [TextContent(
            type="text",
            text=json.dumps(results, indent=2, default=str)
        )]

    async def _handle_memory_store(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = await self._store_memory(arguments)
        return [TextContent(
            type="text",
            text=f"Memory stored with ID: {result}"
        )]

    async def _handle_memory_stats(self, arguments: Dict[str, Any]) -> List[TextContent]:
        stats = await self._get_stats()
        return [TextContent(
            type="text",
            text=json.dumps(stats, indent=2)
        )]

    async def _handle_memory_checkpoint(self, arguments: Dict[str, Any]) -> List[TextContent]:
        result = await self._create_checkpoint(arguments)
        return [TextContent(
            type="text",
            text=f"Checkpoint created: {result}"
        )]

    async def _handle_memory_restore(self, arguments: Dict[str, Any]) -> List[TextContent]:
        context = await self._restore_checkpoint(arguments)
        return [TextContent(
            type="text",
            text=context or "No checkpoint found"
        )]

    async def _search_memory(self, args: Dict[str, Any]) -> List[Dict]:
        """Search memories using hybrid RAG"""
        query = args["query"]
        limit = args.get("limit", 5)
        project = args.get("project")
        memory_type = args.get("type")
        include_relations = args.get("include_relations", True)

        # Use hybrid search
        results = await self.memory_service.hybrid_search(
            query=query,
            top_k=limit,
            user_id=project  # Use project as user_id filter
        )

        formatted_results = []
        for doc in results:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("rrf_score", 0.0),
                "id": doc.metadata.get("id")
            }

            # Add relations if requested
            if include_relations and result["id"]:
                relations = await self._get_relations(result["id"])
                if relations:
                    result["relations"] = relations

            # Filter by type if specified
            if memory_type and doc.metadata.get("source_type") != memory_type:
                continue

            formatted_results.append(result)

        return formatted_results

    async def _store_memory(self, args: Dict[str, Any]) -> str:
        """Store new memory with embeddings"""
        text = args["text"]
        memory_type = args.get("type", "general")
        project = args.get("project", "agi")
        tags = args.get("tags", [])
        relations = args.get("relations", [])

        # Prepare metadata
        metadata = {
            "source_type": memory_type,
            "project": project,
            "tags": tags
        }

        # Store memory
        memory_id = await self.memory_service.add_memory(
            content=text,
            metadata=metadata,
            source_type=memory_type,
            user_id=project
        )

        # Add relations
        for relation in relations:
            # Find target memory by text
            target_results = await self.memory_service.semantic_search(
                query=relation["target_text"],
                top_k=1,
                threshold=0.95
            )

            if target_results:
                target_id = target_results[0].metadata.get("id")
                if target_id:
                    await self.memory_service.add_relation(
                        source_id=memory_id,
                        target_id=target_id,
                        relation_type=relation.get("relation_type", "RELATES_TO")
                    )

        return str(memory_id)

    async def _get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        pool = await db.connect()

        async with pool.acquire() as conn:
            # Count memories
            total_memories = await conn.fetchval(
                "SELECT COUNT(*) FROM memory_store"
            )

            # Count by type
            type_counts = await conn.fetch(
                "SELECT source_type, COUNT(*) as count FROM memory_store GROUP BY source_type"
            )

            # Count relations
            total_relations = await conn.fetchval(
                "SELECT COUNT(*) FROM relations"
            )

            # Count checkpoints
            total_checkpoints = await conn.fetchval(
                "SELECT COUNT(*) FROM checkpoints"
            )

        # Check health
        health = await self.memory_service.health_check()

        return {
            "total_memories": total_memories,
            "memory_types": {row["source_type"]: row["count"] for row in type_counts},
            "total_relations": total_relations,
            "total_checkpoints": total_checkpoints,
            "health": health,
            "backend": "PostgreSQL + pgvector",
            "cache": "Redis Stack"
        }

    async def _create_checkpoint(self, args: Dict[str, Any]) -> str:
        """Create context checkpoint"""
        session_id = args.get("session_id", "default")
        context = args["context"]

        # Store as special memory type
        checkpoint_id = await self.memory_service.add_memory(
            content=context,
            metadata={
                "session_id": session_id,
                "checkpoint": True
            },
            source_type="checkpoint",
            user_id=session_id
        )

        # Also store in checkpoints table for LangGraph
        pool = await db.connect()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO checkpoints (thread_id, checkpoint, metadata)
                VALUES ($1, $2, $3)
                """,
                session_id,
                {"context": context},
                {"checkpoint_id": str(checkpoint_id)}
            )

        return f"{session_id}:{checkpoint_id}"

    async def _restore_checkpoint(self, args: Dict[str, Any]) -> Optional[str]:
        """Restore context from checkpoint"""
        session_id = args.get("session_id", "default")

        # Get latest checkpoint
        pool = await db.connect()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT checkpoint, metadata
                FROM checkpoints
                WHERE thread_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                session_id
            )

        if row:
            return row["checkpoint"].get("context", "")

        # Fallback to memory_store
        results = await self.memory_service.semantic_search(
            query=f"checkpoint session {session_id}",
            top_k=1,
            threshold=0.9
        )

        if results:
            return results[0].page_content

        return None

    async def _get_relations(self, memory_id: str) -> List[Dict]:
        """Get memory relations"""
        pool = await db.connect()

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT r.*, m.content as target_content
                FROM relations r
                JOIN memory_store m ON r.target_id = m.id
                WHERE r.source_id = $1
                """,
                memory_id
            )

        return [
            {
                "target_id": str(row["target_id"]),
                "relation_type": row["relation_type"],
                "target_content": row["target_content"][:100]
            }
            for row in rows
        ]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.initialize,
                {}
            )

if __name__ == "__main__":
    mcp = MemorySystemMCP()
    asyncio.run(mcp.run())
