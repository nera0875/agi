"""
GraphQL Schema - Strawberry with WebSocket subscriptions
Implements JWT authentication, rate limiting, and streaming
"""

from __future__ import annotations
import logging
from typing import Optional, List, AsyncGenerator, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

import strawberry
from strawberry.types import Info
from strawberry.permission import BasePermission
from strawberry.extensions import Extension
from strawberry.scalars import JSON
import jwt
from passlib.context import CryptContext

from config import settings
from services.memory_service import MemoryService
from services.agent_service import AgentService
from services.graph_service import GraphService
from services.database import db
from services.redis_client import redis_client
from core import trace_llm_call, performance_monitor

logger = logging.getLogger(__name__)

# ============================================================================
# AUTHENTICATION
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class IsAuthenticated(BasePermission):
    """
    Permission class for authenticated users
    """
    message = "User is not authenticated"

    async def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        request = info.context.request
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if not token:
            return False

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            info.context.user_id = payload.get("sub")
            return True
        except jwt.JWTError:
            return False


class RateLimitExtension(Extension):
    """
    Rate limiting extension for GraphQL
    """

    async def on_request_start(self):
        request = self.execution_context.context.request
        client_ip = request.client.host

        # Check rate limit
        redis = await redis_client.get_client()
        key = f"rate_limit:{client_ip}"

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)  # 1 minute window

        if count > settings.rate_limit_per_minute:
            raise Exception(f"Rate limit exceeded: {settings.rate_limit_per_minute}/min")


# ============================================================================
# SCALAR TYPES
# ============================================================================

@strawberry.scalar
class UUID:
    """UUID scalar type"""
    serialize = str
    parse_value = str


# ============================================================================
# OBJECT TYPES
# ============================================================================

@strawberry.type
class Memory:
    """Memory object type"""
    id: str
    content: str
    metadata: JSON
    source_type: str
    created_at: datetime
    similarity_score: Optional[float] = None


@strawberry.type
class Relation:
    """Graph relation type"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: float
    metadata: JSON


@strawberry.type
class Session:
    """Conversation session type"""
    id: str
    thread_id: str
    user_id: Optional[str]
    created_at: datetime
    last_active_at: datetime


@strawberry.type
class ChatMessage:
    """Chat message type"""
    role: str  # human, assistant, system
    content: str
    timestamp: datetime
    metadata: Optional[JSON] = None


@strawberry.type
class SearchResult:
    """Search result with highlights"""
    memory: Memory
    highlights: List[str]
    score: float


@strawberry.type
class AuthToken:
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@strawberry.type
class HealthStatus:
    """Service health status"""
    service: str
    status: bool
    message: Optional[str] = None


# AGI Types
@strawberry.type
class KnowledgeEntry:
    """AGI Knowledge Base entry"""
    id: str  # UUID converted to string for JSON serialization
    section: str
    content: str
    tags: List[str]
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class RoadmapItem:
    """AGI Roadmap item"""
    id: str
    phase: str
    status: str
    next_actions: List[str]
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class WorkerTask:
    """Worker task from task queue"""
    id: str
    task_type: str
    status: str
    result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


@strawberry.type
class KnownMCP:
    """Known MCP (Model Context Protocol)"""
    id: str
    mcp_id: str
    display_name: str
    capabilities: List[str]
    description: Optional[str] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None


@strawberry.type
class DatabaseTable:
    """Database table information"""
    name: str
    schema: str
    row_count: int = strawberry.field(name="rowCount", default=0)


@strawberry.type
class TableColumn:
    """Table column information"""
    name: str
    type: str
    nullable: bool = True


@strawberry.type
class NeurotransmitterMetrics:
    """🧠 Neurotransmitter system metrics"""
    glutamate: float
    dopamine: float
    gaba: float
    serotonin: float
    arousal_level: float
    learning_rate: float
    avg_response_time: int
    last_query_type: Optional[str] = None
    last_success: Optional[bool] = None
    updated_at: Optional[str] = None


@strawberry.type
class NeuralMetrics:
    """🧠 Complete neural memory system metrics"""
    graph_total_nodes: int
    graph_total_synapses: int
    graph_density: float
    synapse_avg_strength: float
    synapse_avg_use_count: float
    activation_count: int
    neurotransmitters: NeurotransmitterMetrics


@strawberry.type
class TableDataResult:
    """Complete table data with metadata"""
    columns: List[TableColumn]
    rows: List[JSON]
    total: int


@strawberry.type
class TableRow:
    """Table row data (legacy)"""
    data: JSON


@strawberry.type
class GraphNode:
    """Graph node from knowledge graph"""
    id: str
    label: str
    type: str  # Memory, Knowledge, Task
    properties: JSON


@strawberry.type
class GraphRelation:
    """Graph relation/edge"""
    id: str
    source: str
    target: str
    type: str
    weight: float = 1.0


@strawberry.type
class GraphData:
    """Complete graph data"""
    nodes: List[GraphNode]
    relations: List[GraphRelation]


# ============================================================================
# INPUT TYPES
# ============================================================================

@strawberry.input
class MemoryInput:
    """Input for creating memory"""
    content: str
    metadata: Optional[JSON] = None
    source_type: str = "user"


@strawberry.input
class RelationInput:
    """Input for creating relation"""
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    metadata: Optional[JSON] = None


@strawberry.input
class SearchInput:
    """Input for search queries"""
    query: str
    top_k: int = 10
    search_type: str = "hybrid"  # hybrid, semantic, bm25
    threshold: Optional[float] = 0.7


# ============================================================================
# CONTAINER/BLOCK/TASK TYPES (must be defined before Query/Mutation)
# ============================================================================

@strawberry.type
class Task:
    id: str
    title: str
    description: Optional[str]
    completed: bool
    block_id: str
    created_at: datetime
    completed_at: Optional[datetime]


@strawberry.type
class Block:
    id: str
    name: str
    duration: int
    position: int
    color: Optional[str]
    tasks: List[Task]


@strawberry.type
class Container:
    id: str
    name: str
    total_duration: int
    pause_after: int
    status: str
    locked: bool
    progress: int
    current_block_index: int
    color: Optional[str]
    is_template: bool
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    blocks: List[Block]


# ============================================================================
# QUERIES
# ============================================================================

@strawberry.type
class Query:
    """GraphQL Query root"""

    @strawberry.field
    @performance_monitor.track_latency("search_memories")
    async def search_memories(
        self,
        info: Info,
        search: SearchInput
    ) -> List[SearchResult]:
        """
        Search memories using hybrid RAG

        Args:
            info: GraphQL context
            search: Search parameters

        Returns:
            List of search results
        """
        # Get services from context
        memory_service: MemoryService = info.context.memory_service
        user_id = getattr(info.context, "user_id", None)

        # Execute search
        if search.search_type == "hybrid":
            docs = await memory_service.hybrid_search(
                query=search.query,
                top_k=search.top_k,
                user_id=user_id
            )
        else:
            docs = await memory_service.semantic_search(
                query=search.query,
                top_k=search.top_k,
                threshold=search.threshold
            )

        # Format results
        results = []
        for doc in docs:
            memory = Memory(
                id=doc.metadata.get("id"),
                content=doc.page_content,
                metadata=doc.metadata,
                source_type=doc.metadata.get("source_type", "unknown"),
                created_at=datetime.utcnow(),
                similarity_score=doc.metadata.get("similarity") or doc.metadata.get("rrf_score")
            )

            results.append(SearchResult(
                memory=memory,
                highlights=[doc.page_content[:100]] if doc.page_content else [],  # Highlight excerpt
                score=doc.metadata.get("similarity", 0.0)
            ))

        return results

    @strawberry.field
    async def get_memory(
        self,
        info: Info,
        memory_id: str
    ) -> Optional[Memory]:
        """
        Get single memory by ID

        Args:
            info: GraphQL context
            memory_id: Memory UUID

        Returns:
            Memory object or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM memory_store WHERE id = $1",
                memory_id
            )

        if not row:
            return None

        return Memory(
            id=row["id"],
            content=row["content"],
            metadata=row["metadata"],
            source_type=row["source_type"],
            created_at=row["created_at"]
        )

    @strawberry.field
    async def get_related_memories(
        self,
        info: Info,
        memory_id: str,
        max_depth: int = 3
    ) -> List[Memory]:
        """
        Get related memories through graph traversal

        Args:
            info: GraphQL context
            memory_id: Starting memory
            max_depth: Maximum traversal depth

        Returns:
            List of related memories
        """
        memory_service: MemoryService = info.context.memory_service

        docs = await memory_service.get_related_memories(
            memory_id=memory_id,
            max_depth=max_depth
        )

        return [
            Memory(
                id=doc.metadata["id"],
                content=doc.page_content,
                metadata=doc.metadata,
                source_type="related",
                created_at=datetime.utcnow()
            )
            for doc in docs
        ]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def get_session(
        self,
        info: Info,
        thread_id: str
    ) -> Optional[Session]:
        """
        Get conversation session

        Args:
            info: GraphQL context
            thread_id: Thread ID

        Returns:
            Session object or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM sessions WHERE thread_id = $1",
                thread_id
            )

        if not row:
            return None

        return Session(
            id=row["id"],
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            last_active_at=row["last_active_at"]
        )

    @strawberry.field
    async def health_check(self, info: Info) -> List[HealthStatus]:
        """
        Check system health

        Args:
            info: GraphQL context

        Returns:
            List of health statuses
        """
        statuses = []

        # Check database
        try:
            pool = await db.connect()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            statuses.append(HealthStatus(
                service="database",
                status=True
            ))
        except Exception as e:
            statuses.append(HealthStatus(
                service="database",
                status=False,
                message=str(e)
            ))

        # Check Redis
        try:
            redis = await redis_client.get_client()
            await redis.ping()
            statuses.append(HealthStatus(
                service="redis",
                status=True
            ))
        except Exception as e:
            statuses.append(HealthStatus(
                service="redis",
                status=False,
                message=str(e)
            ))

        # Check memory service
        memory_service: MemoryService = info.context.memory_service
        memory_health = await memory_service.health_check()

        for service, status in memory_health.items():
            statuses.append(HealthStatus(
                service=f"memory_{service}",
                status=status
            ))

        return statuses

    @strawberry.field
    async def get_neural_metrics(self, info: Info) -> NeuralMetrics:
        """
        🧠 Get neural memory system metrics

        Returns complete metrics including:
        - Graph stats (nodes, synapses, density)
        - Synapse stats (strength, use count)
        - Neurotransmitter levels (glutamate, dopamine, GABA, serotonin)
        - Activation count
        """
        ctx = info.context
        graph_service = ctx.get("graph_service")

        if not graph_service or not hasattr(graph_service, 'neural_memory'):
            raise Exception("Neural memory service not available")

        metrics = await graph_service.neural_memory.get_neural_metrics()

        return NeuralMetrics(
            graph_total_nodes=metrics['graph']['total_nodes'],
            graph_total_synapses=metrics['graph']['total_synapses'],
            graph_density=metrics['graph']['density'],
            synapse_avg_strength=metrics['synapses']['avg_strength'],
            synapse_avg_use_count=metrics['synapses']['avg_use_count'],
            activation_count=metrics['activation_count'],
            neurotransmitters=NeurotransmitterMetrics(
                glutamate=metrics['neurotransmitters']['glutamate'],
                dopamine=metrics['neurotransmitters']['dopamine'],
                gaba=metrics['neurotransmitters']['gaba'],
                serotonin=metrics['neurotransmitters']['serotonin'],
                arousal_level=metrics['neurotransmitters']['arousal_level'],
                learning_rate=metrics['neurotransmitters']['learning_rate'],
                avg_response_time=metrics['neurotransmitters']['avg_response_time'],
                last_query_type=metrics['neurotransmitters']['last_query_type'],
                last_success=metrics['neurotransmitters']['last_success'],
                updated_at=metrics['neurotransmitters']['updated_at']
            )
        )

    # ========== AGI QUERIES ==========
    @strawberry.field
    async def get_all_knowledge(
        self,
        info: Info,
        section: Optional[str] = None,
        priority_min: Optional[int] = None
    ) -> List["KnowledgeEntry"]:
        """Get all knowledge entries from AGI database"""
        pool = await db.connect()
        query = "SELECT id, section, content, tags, priority, created_at, updated_at FROM agi_knowledge WHERE 1=1"
        params = []

        if section:
            query += " AND section = $" + str(len(params) + 1)
            params.append(section)
        if priority_min is not None:
            query += " AND priority >= $" + str(len(params) + 1)
            params.append(priority_min)

        query += " ORDER BY priority DESC, created_at DESC"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            KnowledgeEntry(
                id=str(row["id"]),
                section=row["section"],
                content=row["content"],
                tags=list(row["tags"]) if row["tags"] else [],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    @strawberry.field
    async def get_all_roadmap(
        self,
        info: Info,
        status: Optional[str] = None,
        priority_min: Optional[int] = None
    ) -> List["RoadmapItem"]:
        """Get all roadmap items from AGI database"""
        pool = await db.connect()
        query = "SELECT id, phase, status, next_actions, priority, created_at, updated_at FROM agi_roadmap WHERE 1=1"
        params = []

        if status:
            query += " AND status = $" + str(len(params) + 1)
            params.append(status)
        if priority_min is not None:
            query += " AND priority >= $" + str(len(params) + 1)
            params.append(priority_min)

        query += " ORDER BY priority DESC, created_at DESC"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            RoadmapItem(
                id=str(row["id"]),
                phase=row["phase"],
                status=row["status"],
                next_actions=list(row["next_actions"]) if row["next_actions"] else [],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    @strawberry.field
    async def get_all_tasks(
        self,
        info: Info,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List["WorkerTask"]:
        """Get all worker tasks from AGI database"""
        pool = await db.connect()
        query = "SELECT id, task_type, status, result, created_at, updated_at, error_message FROM worker_tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = $" + str(len(params) + 1)
            params.append(status)
        if task_type:
            query += " AND task_type = $" + str(len(params) + 1)
            params.append(task_type)

        query += " ORDER BY created_at DESC"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            WorkerTask(
                id=str(row["id"]),
                task_type=row["task_type"],
                status=row["status"],
                result=row["result"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error_message=row["error_message"]
            )
            for row in rows
        ]

    @strawberry.field
    async def get_all_mcps(
        self,
        info: Info,
        capability: Optional[str] = None
    ) -> List["KnownMCP"]:
        """Get all known MCPs from AGI database"""
        pool = await db.connect()

        if capability:
            query = "SELECT id, mcp_id, display_name, capabilities, description, usage_count, last_used_at FROM known_mcps WHERE capabilities @> ARRAY[$1] ORDER BY usage_count DESC"
            params = [capability]
        else:
            query = "SELECT id, mcp_id, display_name, capabilities, description, usage_count, last_used_at FROM known_mcps ORDER BY usage_count DESC"
            params = []

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            KnownMCP(
                id=str(row["id"]),
                mcp_id=row["mcp_id"],
                display_name=row["display_name"],
                capabilities=list(row["capabilities"]) if row["capabilities"] else [],
                description=row["description"],
                usage_count=row["usage_count"],
                last_used_at=row["last_used_at"]
            )
            for row in rows
        ]

    @strawberry.field
    async def get_database_tables(self, info: Info) -> List["DatabaseTable"]:
        """Get all tables in the database"""
        pool = await db.connect()

        query = """
            SELECT
                table_schema as schema,
                table_name as name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """

        async with pool.acquire() as conn:
            rows = await conn.fetch(query)

            # Get row counts
            tables = []
            for row in rows:
                count_query = f"SELECT COUNT(*) FROM {row['schema']}.{row['name']}"
                count = await conn.fetchval(count_query)
                tables.append(DatabaseTable(
                    name=row["name"],
                    schema=row["schema"],
                    row_count=count or 0
                ))

        return tables

    @strawberry.field
    async def get_database_table_data(
        self,
        info: Info,
        table: str,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[JSON] = None
    ) -> "TableDataResult":
        """Get table data with columns and total count"""
        pool = await db.connect()

        # Sanitize table name
        if not table.replace("_", "").isalnum():
            raise Exception("Invalid table name")

        async with pool.acquire() as conn:
            # Get columns
            columns_query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """
            columns_rows = await conn.fetch(columns_query, table)

            columns = [
                TableColumn(
                    name=row["column_name"],
                    type=row["data_type"],
                    nullable=row["is_nullable"] == "YES"
                )
                for row in columns_rows
            ]

            # Get total count
            count_query = f"SELECT COUNT(*) FROM {table}"
            total = await conn.fetchval(count_query)

            # Get data rows
            data_query = f"SELECT * FROM {table} LIMIT $1 OFFSET $2"
            data_rows = await conn.fetch(data_query, limit, offset)

            # Serialize data
            def serialize_value(val):
                from uuid import UUID
                from datetime import datetime, date
                from decimal import Decimal

                if isinstance(val, UUID):
                    return str(val)
                elif isinstance(val, (datetime, date)):
                    return val.isoformat()
                elif isinstance(val, Decimal):
                    return float(val)
                else:
                    return val

            rows = [
                {k: serialize_value(v) for k, v in dict(row).items()}
                for row in data_rows
            ]

        return TableDataResult(
            columns=columns,
            rows=rows,
            total=total or 0
        )

    @strawberry.field
    async def get_table_data(
        self,
        info: Info,
        table_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List["TableRow"]:
        """Get data from a specific table"""
        pool = await db.connect()

        # Sanitize table name (basic protection)
        if not table_name.replace("_", "").isalnum():
            raise Exception("Invalid table name")

        query = f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, limit, offset)

        # Convert all values to JSON-serializable types
        def serialize_value(val):
            """Convert PostgreSQL types to JSON-serializable types"""
            from uuid import UUID
            from datetime import datetime, date
            from decimal import Decimal

            if isinstance(val, UUID):
                return str(val)
            elif isinstance(val, (datetime, date)):
                return val.isoformat()
            elif isinstance(val, Decimal):
                return float(val)
            elif isinstance(val, (list, dict)):
                return val  # Already JSON-serializable
            else:
                return val

        return [
            TableRow(data={k: serialize_value(v) for k, v in dict(row).items()})
            for row in rows
        ]

    @strawberry.field
    async def get_graph_data(
        self,
        info: Info,
        node_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> "GraphData":
        """
        Get graph nodes and relations

        Args:
            info: GraphQL context
            node_types: Filter by node types (Memory, Knowledge, Task)
            limit: Max number of nodes

        Returns:
            Graph data with nodes and relations
        """
        graph_service: GraphService = getattr(info.context, "graph_service", None)
        if not graph_service:
            # Fallback: create temporary service
            pool = await db.connect()
            redis = await redis_client.get_client()
            graph_service = GraphService(pool, redis)

        nodes = await graph_service.get_graph_nodes(node_types=node_types, limit=limit)
        relations = await graph_service.get_graph_relations(limit=limit * 2)

        return GraphData(
            nodes=[GraphNode(**n) for n in nodes],
            relations=[GraphRelation(**r) for r in relations]
        )

    @strawberry.field
    async def search_graph_nodes(
        self,
        info: Info,
        query: str,
        limit: int = 10
    ) -> List["GraphNode"]:
        """
        Search graph nodes by text

        Args:
            info: GraphQL context
            query: Search query
            limit: Max results

        Returns:
            List of matching nodes
        """
        graph_service: GraphService = getattr(info.context, "graph_service", None)
        if not graph_service:
            pool = await db.connect()
            redis = await redis_client.get_client()
            graph_service = GraphService(pool, redis)

        nodes = await graph_service.search_nodes(query=query, limit=limit)

        return [GraphNode(**n) for n in nodes]

    @strawberry.field
    async def get_node_neighbors(
        self,
        info: Info,
        node_id: str,
        depth: int = 1
    ) -> "GraphData":
        """
        Get neighbors of a node

        Args:
            info: GraphQL context
            node_id: Node ID
            depth: Search depth

        Returns:
            Subgraph with node and its neighbors
        """
        graph_service: GraphService = getattr(info.context, "graph_service", None)
        if not graph_service:
            pool = await db.connect()
            redis = await redis_client.get_client()
            graph_service = GraphService(pool, redis)

        result = await graph_service.get_node_neighbors(node_id=node_id, depth=depth)

        return GraphData(
            nodes=[GraphNode(**n) for n in result["nodes"]],
            relations=[GraphRelation(**r) for r in result["relations"]]
        )

    @strawberry.field
    async def get_all_containers(self, info: Info) -> List["Container"]:
        """Get all containers (without blocks/tasks)"""
        from services.container_service import ContainerService

        containers_data = await ContainerService.get_all_containers()

        # Convert to Container objects
        containers = []
        for data in containers_data:
            containers.append(Container(
                id=data['id'],
                name=data['name'],
                total_duration=data['total_duration'],
                pause_after=data['pause_after'],
                status=data['status'],
                locked=data['locked'],
                progress=data['progress'],
                current_block_index=data['current_block_index'],
                color=data.get('color'),
                is_template=data['is_template'],
                created_at=data['created_at'],
                started_at=data.get('started_at'),
                completed_at=data.get('completed_at'),
                blocks=[]  # Empty for lightweight query
            ))

        return containers

    @strawberry.field
    async def get_container(self, info: Info, id: str) -> Optional["Container"]:
        """Get single container with all blocks and tasks"""
        from services.container_service import ContainerService

        data = await ContainerService.get_container(id)
        if not data:
            return None

        # Parse nested JSON from get_container_full function
        return Container(
            id=data['id'],
            name=data['name'],
            total_duration=data['totalDuration'],
            pause_after=data['pauseAfter'],
            status=data['status'],
            locked=data['locked'],
            progress=data['progress'],
            current_block_index=data['currentBlockIndex'],
            color=data.get('color'),
            is_template=data['isTemplate'],
            created_at=datetime.fromisoformat(data['createdAt']) if isinstance(data['createdAt'], str) else data['createdAt'],
            started_at=datetime.fromisoformat(data['startedAt']) if data.get('startedAt') and isinstance(data['startedAt'], str) else data.get('startedAt'),
            completed_at=datetime.fromisoformat(data['completedAt']) if data.get('completedAt') and isinstance(data['completedAt'], str) else data.get('completedAt'),
            blocks=[
                Block(
                    id=b['id'],
                    name=b['name'],
                    duration=b['duration'],
                    position=b['position'],
                    color=b.get('color'),
                    tasks=[
                        Task(
                            id=t['id'],
                            title=t['title'],
                            description=t.get('description'),
                            completed=t['completed'],
                            block_id=t['blockId'],
                            created_at=datetime.fromisoformat(t['createdAt']) if isinstance(t['createdAt'], str) else t['createdAt'],
                            completed_at=datetime.fromisoformat(t['completedAt']) if t.get('completedAt') and isinstance(t['completedAt'], str) else t.get('completedAt')
                        )
                        for t in b.get('tasks', [])
                    ]
                )
                for b in data.get('blocks', [])
            ]
        )


# ============================================================================
# INPUT TYPES (must be defined before Mutation)
# ============================================================================

@strawberry.input
class CreateContainerInput:
    name: str
    total_duration: int
    pause_after: int = 10
    color: Optional[str] = None


@strawberry.input
class UpdateContainerInput:
    name: Optional[str] = None
    total_duration: Optional[str] = None
    pause_after: Optional[int] = None
    status: Optional[str] = None
    locked: Optional[bool] = None
    progress: Optional[int] = None
    current_block_index: Optional[int] = None
    color: Optional[str] = None


@strawberry.input
class BlockInput:
    name: str
    duration: int
    position: int
    color: Optional[str] = None


# ============================================================================
# MUTATIONS
# ============================================================================

@strawberry.type
class Mutation:
    """GraphQL Mutation root"""

    @strawberry.mutation
    async def create_memory(
        self,
        info: Info,
        memory: MemoryInput
    ) -> Memory:
        """
        Create new memory

        Args:
            info: GraphQL context
            memory: Memory input data

        Returns:
            Created memory
        """
        memory_service: MemoryService = info.context.memory_service
        user_id = getattr(info.context, "user_id", None)

        memory_id = await memory_service.add_memory(
            content=memory.content,
            metadata=memory.metadata,
            source_type=memory.source_type,
            user_id=user_id
        )

        return Memory(
            id=memory_id,
            content=memory.content,
            metadata=memory.metadata or {},
            source_type=memory.source_type,
            created_at=datetime.utcnow()
        )

    @strawberry.mutation
    async def create_relation(
        self,
        info: Info,
        relation: RelationInput
    ) -> Relation:
        """
        Create relation between memories

        Args:
            info: GraphQL context
            relation: Relation input data

        Returns:
            Created relation
        """
        memory_service: MemoryService = info.context.memory_service

        relation_id = await memory_service.add_relation(
            source_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation.relation_type,
            metadata=relation.metadata,
            weight=relation.weight
        )

        return Relation(
            id=relation_id,
            source_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation.relation_type,
            weight=relation.weight,
            metadata=relation.metadata or {}
        )

    @strawberry.mutation
    @performance_monitor.track_latency("chat_message")
    # Note: LangSmith decorator omitted due to Strawberry compatibility
    # Use performance_monitor instead for tracing
    async def send_message(
        self,
        info: Info,
        thread_id: str,
        message: str
    ) -> ChatMessage:
        """
        Send chat message and get response

        Args:
            info: GraphQL context
            thread_id: Conversation thread ID
            message: User message

        Returns:
            Assistant response
        """
        agent_service: AgentService = info.context.agent_service
        user_id = getattr(info.context, "user_id", None)

        # Get response
        response = await agent_service.chat(
            message=message,
            thread_id=thread_id,
            user_id=user_id,
            stream=False
        )

        return ChatMessage(
            role="assistant",
            content=response,
            timestamp=datetime.utcnow()
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_session(
        self,
        info: Info,
        metadata: Optional[JSON] = None
    ) -> Session:
        """
        Create new conversation session

        Args:
            info: GraphQL context
            metadata: Optional metadata

        Returns:
            Created session
        """
        agent_service: AgentService = info.context.agent_service
        user_id = getattr(info.context, "user_id", None)

        thread_id = await agent_service.create_session(
            user_id=user_id,
            metadata=metadata
        )

        return Session(
            id=thread_id,
            thread_id=thread_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            last_active_at=datetime.utcnow()
        )

    @strawberry.mutation
    async def login(
        self,
        info: Info,
        username: str,
        password: str
    ) -> AuthToken:
        """
        User login

        Args:
            info: GraphQL context
            username: Username
            password: Password

        Returns:
            JWT token
        """
        # Authentifie l’utilisateur via le couple username/hash configuré
        if username != settings.admin_username:
            raise Exception("Invalid credentials")

        password_valid = False
        try:
            password_valid = pwd_context.verify(password, settings.admin_password_hash)
        except Exception:
            password_valid = False

        if not password_valid:
            raise Exception("Invalid credentials")

        # Création du JWT une fois l’utilisateur vérifié
        payload = {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(
                minutes=settings.jwt_expiration_minutes
            )
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )

        return AuthToken(
            access_token=token,
            expires_in=settings.jwt_expiration_minutes * 60
        )

    @strawberry.mutation
    async def create_container(
        self,
        info: Info,
        input: CreateContainerInput
    ) -> "Container":
        """Create new container"""
        from services.container_service import ContainerService

        data = await ContainerService.create_container(
            name=input.name,
            total_duration=input.total_duration,
            pause_after=input.pause_after,
            color=input.color
        )

        # Parse and return (same logic as get_container query)
        return Container(
            id=data['id'],
            name=data['name'],
            total_duration=data['totalDuration'],
            pause_after=data['pauseAfter'],
            status=data['status'],
            locked=data['locked'],
            progress=data['progress'],
            current_block_index=data['currentBlockIndex'],
            color=data.get('color'),
            is_template=data['isTemplate'],
            created_at=datetime.fromisoformat(data['createdAt']) if isinstance(data['createdAt'], str) else data['createdAt'],
            started_at=None,
            completed_at=None,
            blocks=[]
        )

    @strawberry.mutation
    async def update_container(
        self,
        info: Info,
        id: str,
        input: UpdateContainerInput
    ) -> Optional["Container"]:
        """Update container"""
        from services.container_service import ContainerService

        updates = {
            k: v for k, v in {
                'name': input.name,
                'total_duration': input.total_duration,
                'pause_after': input.pause_after,
                'status': input.status,
                'locked': input.locked,
                'progress': input.progress,
                'current_block_index': input.current_block_index,
                'color': input.color
            }.items() if v is not None
        }

        data = await ContainerService.update_container(id, **updates)
        if not data:
            return None

        # Parse and return
        return Container(
            id=data['id'],
            name=data['name'],
            total_duration=data['totalDuration'],
            pause_after=data['pauseAfter'],
            status=data['status'],
            locked=data['locked'],
            progress=data['progress'],
            current_block_index=data['currentBlockIndex'],
            color=data.get('color'),
            is_template=data['isTemplate'],
            created_at=datetime.fromisoformat(data['createdAt']) if isinstance(data['createdAt'], str) else data['createdAt'],
            started_at=datetime.fromisoformat(data['startedAt']) if data.get('startedAt') and isinstance(data['startedAt'], str) else data.get('startedAt'),
            completed_at=datetime.fromisoformat(data['completedAt']) if data.get('completedAt') and isinstance(data['completedAt'], str) else data.get('completedAt'),
            blocks=[
                Block(
                    id=b['id'],
                    name=b['name'],
                    duration=b['duration'],
                    position=b['position'],
                    color=b.get('color'),
                    tasks=[
                        Task(
                            id=t['id'],
                            title=t['title'],
                            description=t.get('description'),
                            completed=t['completed'],
                            block_id=t['blockId'],
                            created_at=datetime.fromisoformat(t['createdAt']) if isinstance(t['createdAt'], str) else t['createdAt'],
                            completed_at=datetime.fromisoformat(t['completedAt']) if t.get('completedAt') and isinstance(t['completedAt'], str) else t.get('completedAt')
                        )
                        for t in b.get('tasks', [])
                    ]
                )
                for b in data.get('blocks', [])
            ]
        )

    @strawberry.mutation
    async def delete_container(self, info: Info, id: str) -> bool:
        """Delete container"""
        from services.container_service import ContainerService
        return await ContainerService.delete_container(id)

    @strawberry.mutation
    async def update_blocks(
        self,
        info: Info,
        container_id: str,
        blocks: List[BlockInput]
    ) -> "Container":
        """Replace all blocks in container"""
        from services.container_service import ContainerService

        blocks_data = [
            {
                'name': b.name,
                'duration': b.duration,
                'position': b.position,
                'color': b.color
            }
            for b in blocks
        ]

        data = await ContainerService.update_blocks(container_id, blocks_data)

        # Parse and return (same as update_container)
        return Container(
            id=data['id'],
            name=data['name'],
            total_duration=data['totalDuration'],
            pause_after=data['pauseAfter'],
            status=data['status'],
            locked=data['locked'],
            progress=data['progress'],
            current_block_index=data['currentBlockIndex'],
            color=data.get('color'),
            is_template=data['isTemplate'],
            created_at=datetime.fromisoformat(data['createdAt']) if isinstance(data['createdAt'], str) else data['createdAt'],
            started_at=datetime.fromisoformat(data['startedAt']) if data.get('startedAt') and isinstance(data['startedAt'], str) else data.get('startedAt'),
            completed_at=datetime.fromisoformat(data['completedAt']) if data.get('completedAt') and isinstance(data['completedAt'], str) else data.get('completedAt'),
            blocks=[
                Block(
                    id=b['id'],
                    name=b['name'],
                    duration=b['duration'],
                    position=b['position'],
                    color=b.get('color'),
                    tasks=[
                        Task(
                            id=t['id'],
                            title=t['title'],
                            description=t.get('description'),
                            completed=t['completed'],
                            block_id=t['blockId'],
                            created_at=datetime.fromisoformat(t['createdAt']) if isinstance(t['createdAt'], str) else t['createdAt'],
                            completed_at=datetime.fromisoformat(t['completedAt']) if t.get('completedAt') and isinstance(t['completedAt'], str) else t.get('completedAt')
                        )
                        for t in b.get('tasks', [])
                    ]
                )
                for b in data.get('blocks', [])
            ]
        )

    @strawberry.mutation
    async def add_task(
        self,
        info: Info,
        block_id: str,
        title: str,
        description: Optional[str] = None
    ) -> Task:
        """Add task to block"""
        from services.container_service import ContainerService

        data = await ContainerService.add_task(block_id, title, description)

        return Task(
            id=data['id'],
            title=data['title'],
            description=data.get('description'),
            completed=data['completed'],
            block_id=data['block_id'],
            created_at=data['created_at'],
            completed_at=data.get('completed_at')
        )

    @strawberry.mutation
    async def toggle_task(
        self,
        info: Info,
        task_id: str,
        completed: bool
    ) -> Task:
        """Toggle task completion"""
        from services.container_service import ContainerService

        data = await ContainerService.toggle_task(task_id, completed)

        return Task(
            id=data['id'],
            title=data['title'],
            description=data.get('description'),
            completed=data['completed'],
            block_id=data['block_id'],
            created_at=data['created_at'],
            completed_at=data.get('completed_at')
        )

    @strawberry.mutation
    async def update_table_row(
        self,
        info: Info,
        table: str,
        id: str,
        data: JSON
    ) -> JSON:
        """Update a row in a table"""
        pool = await db.connect()

        # Sanitize table name
        if not table.replace("_", "").isalnum():
            raise Exception("Invalid table name")

        # Build UPDATE query
        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ${i+2}" for i, col in enumerate(columns)])
        query = f"UPDATE {table} SET {set_clause} WHERE id = $1 RETURNING *"

        values = [id] + list(data.values())

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise Exception(f"Row with id {id} not found")

        # Serialize result
        def serialize_value(val):
            from uuid import UUID
            from datetime import datetime, date
            from decimal import Decimal

            if isinstance(val, UUID):
                return str(val)
            elif isinstance(val, (datetime, date)):
                return val.isoformat()
            elif isinstance(val, Decimal):
                return float(val)
            else:
                return val

        return {k: serialize_value(v) for k, v in dict(row).items()}

    @strawberry.mutation
    async def insert_table_row(
        self,
        info: Info,
        table: str,
        data: JSON
    ) -> JSON:
        """Insert a new row into a table"""
        pool = await db.connect()

        # Sanitize table name
        if not table.replace("_", "").isalnum():
            raise Exception("Invalid table name")

        # Build INSERT query
        columns = list(data.keys())
        columns_str = ", ".join(columns)
        placeholders = ", ".join([f"${i+1}" for i in range(len(columns))])
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING *"

        values = list(data.values())

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        # Serialize result
        def serialize_value(val):
            from uuid import UUID
            from datetime import datetime, date
            from decimal import Decimal

            if isinstance(val, UUID):
                return str(val)
            elif isinstance(val, (datetime, date)):
                return val.isoformat()
            elif isinstance(val, Decimal):
                return float(val)
            else:
                return val

        return {k: serialize_value(v) for k, v in dict(row).items()}

    @strawberry.mutation
    async def delete_table_rows(
        self,
        info: Info,
        table: str,
        ids: List[str]
    ) -> int:
        """Delete rows from a table"""
        pool = await db.connect()

        # Sanitize table name
        if not table.replace("_", "").isalnum():
            raise Exception("Invalid table name")

        # Build DELETE query with multiple ids
        placeholders = ", ".join([f"${i+1}" for i in range(len(ids))])
        query = f"DELETE FROM {table} WHERE id IN ({placeholders})"

        async with pool.acquire() as conn:
            result = await conn.execute(query, *ids)

        # Extract count from result (format: "DELETE N")
        count = int(result.split()[-1]) if result else 0

        return count


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

@strawberry.type
class Subscription:
    """GraphQL Subscription root - WebSocket real-time"""

    @strawberry.subscription
    async def chat_stream(
        self,
        info: Info,
        thread_id: str
    ) -> AsyncGenerator[ChatMessage, None]:
        """
        Stream chat responses in real-time

        Args:
            info: GraphQL context
            thread_id: Conversation thread ID

        Yields:
            Chat message chunks
        """
        agent_service: AgentService = info.context.agent_service
        user_id = getattr(info.context, "user_id", None)

        # Subscribe to Redis pub/sub for this thread
        redis = await redis_client.get_client()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"chat:{thread_id}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])

                    yield ChatMessage(
                        role=data["role"],
                        content=data["content"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        metadata=data.get("metadata")
                    )
        finally:
            await pubsub.unsubscribe(f"chat:{thread_id}")

    @strawberry.subscription
    async def memory_updates(
        self,
        info: Info,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Memory, None]:
        """
        Subscribe to memory updates

        Args:
            info: GraphQL context
            user_id: Optional user filter

        Yields:
            New memories as they're created
        """
        redis = await redis_client.get_client()
        pubsub = redis.pubsub()

        channel = f"memory:{user_id}" if user_id else "memory:*"
        await pubsub.psubscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    data = json.loads(message["data"])

                    yield Memory(
                        id=data["id"],
                        content=data["content"],
                        metadata=data["metadata"],
                        source_type=data["source_type"],
                        created_at=datetime.fromisoformat(data["created_at"])
                    )
        finally:
            await pubsub.punsubscribe(channel)

    @strawberry.subscription
    async def agent_thoughts(
        self,
        info: Info,
        thread_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent reasoning/thoughts (chain of thought)

        Args:
            info: GraphQL context
            thread_id: Thread ID

        Yields:
            Agent thought process
        """
        redis = await redis_client.get_client()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"thoughts:{thread_id}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"].decode("utf-8")
        finally:
            await pubsub.unsubscribe(f"thoughts:{thread_id}")


# ============================================================================
# SCHEMA
# ============================================================================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[RateLimitExtension]
)
