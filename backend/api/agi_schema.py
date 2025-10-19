"""
AGI Schema - Strawberry GraphQL for AGI Database Tables
Exposes: agi_knowledge, agi_roadmap, worker_tasks, known_mcps
"""

import logging
from typing import Optional, List
from datetime import datetime
import json

import strawberry
from strawberry.types import Info
from strawberry.scalars import JSON

from services.database import db

logger = logging.getLogger(__name__)

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
class KnowledgeEntry:
    """AGI Knowledge Base entry"""
    id: Optional[UUID] = None
    section: str
    content: str
    tags: List[str]
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class RoadmapItem:
    """AGI Roadmap item"""
    id: Optional[UUID] = None
    phase: str
    status: str  # active, pending, completed
    next_actions: List[str]
    priority: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class WorkerTask:
    """Worker task from task queue"""
    id: Optional[UUID] = None
    task_type: str
    status: str  # pending, running, success, failed
    result: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None


@strawberry.type
class KnownMCP:
    """Known MCP (Model Context Protocol)"""
    id: Optional[UUID] = None
    mcp_id: str
    display_name: str
    capabilities: List[str]
    description: Optional[str] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None


# ============================================================================
# INPUT TYPES
# ============================================================================

@strawberry.input
class KnowledgeInput:
    """Input for creating/updating knowledge"""
    section: str
    content: str
    tags: List[str]
    priority: int


@strawberry.input
class RoadmapInput:
    """Input for creating roadmap items"""
    phase: str
    status: str
    next_actions: List[str]
    priority: int


@strawberry.input
class TaskInput:
    """Input for creating tasks"""
    task_type: str
    status: str = "pending"


@strawberry.input
class UpdateTaskInput:
    """Input for updating tasks"""
    status: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================================
# QUERIES
# ============================================================================

@strawberry.type
class AgiQuery:
    """GraphQL Query root for AGI tables"""

    @strawberry.field
    async def get_all_knowledge(
        self,
        info: Info,
        section: Optional[str] = None,
        priority_min: Optional[int] = None
    ) -> List[KnowledgeEntry]:
        """
        Get all knowledge entries, optionally filtered by section or priority

        Args:
            info: GraphQL context
            section: Optional section filter
            priority_min: Optional minimum priority filter

        Returns:
            List of knowledge entries
        """
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
                id=row["id"],
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
    async def get_knowledge_by_id(
        self,
        info: Info,
        knowledge_id: UUID
    ) -> Optional[KnowledgeEntry]:
        """
        Get single knowledge entry by ID

        Args:
            info: GraphQL context
            knowledge_id: Knowledge UUID

        Returns:
            Knowledge entry or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, section, content, tags, priority, created_at, updated_at FROM agi_knowledge WHERE id = $1",
                knowledge_id
            )

        if not row:
            return None

        return KnowledgeEntry(
            id=row["id"],
            section=row["section"],
            content=row["content"],
            tags=list(row["tags"]) if row["tags"] else [],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @strawberry.field
    async def get_all_roadmap(
        self,
        info: Info,
        status: Optional[str] = None,
        priority_min: Optional[int] = None
    ) -> List[RoadmapItem]:
        """
        Get all roadmap items, optionally filtered by status or priority

        Args:
            info: GraphQL context
            status: Optional status filter (active, pending, completed)
            priority_min: Optional minimum priority filter

        Returns:
            List of roadmap items
        """
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
                id=row["id"],
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
    async def get_roadmap_by_id(
        self,
        info: Info,
        roadmap_id: UUID
    ) -> Optional[RoadmapItem]:
        """
        Get single roadmap item by ID

        Args:
            info: GraphQL context
            roadmap_id: Roadmap UUID

        Returns:
            Roadmap item or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, phase, status, next_actions, priority, created_at, updated_at FROM agi_roadmap WHERE id = $1",
                roadmap_id
            )

        if not row:
            return None

        return RoadmapItem(
            id=row["id"],
            phase=row["phase"],
            status=row["status"],
            next_actions=list(row["next_actions"]) if row["next_actions"] else [],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @strawberry.field
    async def get_all_tasks(
        self,
        info: Info,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[WorkerTask]:
        """
        Get all worker tasks, optionally filtered by status or type

        Args:
            info: GraphQL context
            status: Optional status filter (pending, running, success, failed)
            task_type: Optional task type filter

        Returns:
            List of worker tasks
        """
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
                id=row["id"],
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
    async def get_task_by_id(
        self,
        info: Info,
        task_id: UUID
    ) -> Optional[WorkerTask]:
        """
        Get single worker task by ID

        Args:
            info: GraphQL context
            task_id: Task UUID

        Returns:
            Worker task or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, task_type, status, result, created_at, updated_at, error_message FROM worker_tasks WHERE id = $1",
                task_id
            )

        if not row:
            return None

        return WorkerTask(
            id=row["id"],
            task_type=row["task_type"],
            status=row["status"],
            result=row["result"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"]
        )

    @strawberry.field
    async def get_all_mcps(
        self,
        info: Info,
        capability: Optional[str] = None
    ) -> List[KnownMCP]:
        """
        Get all known MCPs, optionally filtered by capability

        Args:
            info: GraphQL context
            capability: Optional capability filter

        Returns:
            List of known MCPs
        """
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
                id=row["id"],
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
    async def get_mcp_by_id(
        self,
        info: Info,
        mcp_id: str
    ) -> Optional[KnownMCP]:
        """
        Get single MCP by ID

        Args:
            info: GraphQL context
            mcp_id: MCP ID

        Returns:
            Known MCP or None
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, mcp_id, display_name, capabilities, description, usage_count, last_used_at FROM known_mcps WHERE mcp_id = $1",
                mcp_id
            )

        if not row:
            return None

        return KnownMCP(
            id=row["id"],
            mcp_id=row["mcp_id"],
            display_name=row["display_name"],
            capabilities=list(row["capabilities"]) if row["capabilities"] else [],
            description=row["description"],
            usage_count=row["usage_count"],
            last_used_at=row["last_used_at"]
        )


# ============================================================================
# MUTATIONS
# ============================================================================

@strawberry.type
class AgiMutation:
    """GraphQL Mutation root for AGI tables"""

    @strawberry.mutation
    async def create_knowledge(
        self,
        info: Info,
        knowledge: KnowledgeInput
    ) -> KnowledgeEntry:
        """
        Create new knowledge entry

        Args:
            info: GraphQL context
            knowledge: Knowledge input data

        Returns:
            Created knowledge entry
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agi_knowledge (section, content, tags, priority, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5)
                RETURNING id, section, content, tags, priority, created_at, updated_at
                """,
                knowledge.section,
                knowledge.content,
                knowledge.tags,
                knowledge.priority,
                datetime.utcnow()
            )

        return KnowledgeEntry(
            id=row["id"],
            section=row["section"],
            content=row["content"],
            tags=list(row["tags"]) if row["tags"] else [],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @strawberry.mutation
    async def update_knowledge(
        self,
        info: Info,
        knowledge_id: UUID,
        section: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[int] = None
    ) -> Optional[KnowledgeEntry]:
        """
        Update existing knowledge entry

        Args:
            info: GraphQL context
            knowledge_id: Knowledge UUID
            section: Optional new section
            content: Optional new content
            tags: Optional new tags
            priority: Optional new priority

        Returns:
            Updated knowledge entry or None
        """
        pool = await db.connect()

        # Build update query dynamically
        updates = []
        params = []
        param_count = 1

        if section is not None:
            updates.append(f"section = ${param_count}")
            params.append(section)
            param_count += 1

        if content is not None:
            updates.append(f"content = ${param_count}")
            params.append(content)
            param_count += 1

        if tags is not None:
            updates.append(f"tags = ${param_count}")
            params.append(tags)
            param_count += 1

        if priority is not None:
            updates.append(f"priority = ${param_count}")
            params.append(priority)
            param_count += 1

        if not updates:
            # No updates provided, just return existing record
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, section, content, tags, priority, created_at, updated_at FROM agi_knowledge WHERE id = $1",
                    knowledge_id
                )
            if not row:
                return None
            return KnowledgeEntry(
                id=row["id"],
                section=row["section"],
                content=row["content"],
                tags=list(row["tags"]) if row["tags"] else [],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

        updates.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1

        params.append(knowledge_id)

        query = f"""
        UPDATE agi_knowledge
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING id, section, content, tags, priority, created_at, updated_at
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return KnowledgeEntry(
            id=row["id"],
            section=row["section"],
            content=row["content"],
            tags=list(row["tags"]) if row["tags"] else [],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @strawberry.mutation
    async def create_roadmap(
        self,
        info: Info,
        roadmap: RoadmapInput
    ) -> RoadmapItem:
        """
        Create new roadmap item

        Args:
            info: GraphQL context
            roadmap: Roadmap input data

        Returns:
            Created roadmap item
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO agi_roadmap (phase, status, next_actions, priority, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $5)
                RETURNING id, phase, status, next_actions, priority, created_at, updated_at
                """,
                roadmap.phase,
                roadmap.status,
                roadmap.next_actions,
                roadmap.priority,
                datetime.utcnow()
            )

        return RoadmapItem(
            id=row["id"],
            phase=row["phase"],
            status=row["status"],
            next_actions=list(row["next_actions"]) if row["next_actions"] else [],
            priority=row["priority"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @strawberry.mutation
    async def update_task(
        self,
        info: Info,
        task_id: UUID,
        update: UpdateTaskInput
    ) -> Optional[WorkerTask]:
        """
        Update worker task

        Args:
            info: GraphQL context
            task_id: Task UUID
            update: Update data

        Returns:
            Updated task or None
        """
        pool = await db.connect()

        updates = []
        params = []
        param_count = 1

        if update.status is not None:
            updates.append(f"status = ${param_count}")
            params.append(update.status)
            param_count += 1

        if update.result is not None:
            updates.append(f"result = ${param_count}")
            params.append(update.result)
            param_count += 1

        if update.error_message is not None:
            updates.append(f"error_message = ${param_count}")
            params.append(update.error_message)
            param_count += 1

        if not updates:
            # No updates provided
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, task_type, status, result, created_at, updated_at, error_message FROM worker_tasks WHERE id = $1",
                    task_id
                )
            if not row:
                return None
            return WorkerTask(
                id=row["id"],
                task_type=row["task_type"],
                status=row["status"],
                result=row["result"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error_message=row["error_message"]
            )

        updates.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())
        param_count += 1

        params.append(task_id)

        query = f"""
        UPDATE worker_tasks
        SET {', '.join(updates)}
        WHERE id = ${param_count}
        RETURNING id, task_type, status, result, created_at, updated_at, error_message
        """

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)

        if not row:
            return None

        return WorkerTask(
            id=row["id"],
            task_type=row["task_type"],
            status=row["status"],
            result=row["result"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"]
        )

    @strawberry.mutation
    async def create_task(
        self,
        info: Info,
        task: TaskInput
    ) -> WorkerTask:
        """
        Create new worker task

        Args:
            info: GraphQL context
            task: Task input data

        Returns:
            Created task
        """
        pool = await db.connect()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO worker_tasks (task_type, status, created_at, updated_at)
                VALUES ($1, $2, $3, $3)
                RETURNING id, task_type, status, result, created_at, updated_at, error_message
                """,
                task.task_type,
                task.status,
                datetime.utcnow()
            )

        return WorkerTask(
            id=row["id"],
            task_type=row["task_type"],
            status=row["status"],
            result=row["result"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error_message=row["error_message"]
        )


# ============================================================================
# SCHEMA
# ============================================================================

agi_schema = strawberry.Schema(
    query=AgiQuery,
    mutation=AgiMutation
)
