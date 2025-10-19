"""
Container Service - Time Blocking System
Handles CRUD operations for containers, blocks, and tasks
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.database import db

logger = logging.getLogger(__name__)


class ContainerService:
    """Service for time blocking containers"""

    @staticmethod
    async def get_all_containers() -> List[Dict[str, Any]]:
        """
        Get all containers (lightweight, without blocks/tasks)

        Returns:
            List of containers
        """
        query = """
            SELECT
                id::text,
                name,
                total_duration,
                pause_after,
                status,
                locked,
                progress,
                current_block_index,
                color,
                is_template,
                created_at,
                started_at,
                completed_at
            FROM containers
            ORDER BY created_at DESC
        """

        rows = await db.fetch_all(query)
        return [dict(row) for row in rows]

    @staticmethod
    async def get_container(container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get single container with all blocks and tasks

        Args:
            container_id: Container UUID

        Returns:
            Container with nested blocks and tasks, or None
        """
        query = "SELECT get_container_full($1::uuid) as data"
        result = await db.fetch_one(query, container_id)

        if not result or not result['data']:
            return None

        return result['data']

    @staticmethod
    async def create_container(
        name: str,
        total_duration: int,
        pause_after: int = 10,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new container

        Args:
            name: Container name
            total_duration: Total time in minutes (HARD LIMIT)
            pause_after: Pause duration after container
            color: Optional hex color

        Returns:
            Created container
        """
        query = """
            INSERT INTO containers (name, total_duration, pause_after, color)
            VALUES ($1, $2, $3, $4)
            RETURNING id::text
        """

        result = await db.fetch_one(query, name, total_duration, pause_after, color)
        container_id = result['id']

        return await ContainerService.get_container(container_id)

    @staticmethod
    async def update_container(
        container_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """
        Update container

        Args:
            container_id: Container UUID
            **updates: Fields to update

        Returns:
            Updated container or None
        """
        # Build dynamic UPDATE query
        set_clauses = []
        values = []
        param_counter = 1

        allowed_fields = [
            'name', 'total_duration', 'pause_after', 'status',
            'locked', 'progress', 'current_block_index', 'color'
        ]

        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                set_clauses.append(f"{field} = ${param_counter}")
                values.append(value)
                param_counter += 1

        if not set_clauses:
            return await ContainerService.get_container(container_id)

        values.append(container_id)
        query = f"""
            UPDATE containers
            SET {', '.join(set_clauses)}
            WHERE id = ${param_counter}::uuid
            RETURNING id::text
        """

        await db.execute(query, *values)
        return await ContainerService.get_container(container_id)

    @staticmethod
    async def delete_container(container_id: str) -> bool:
        """
        Delete container (cascades to blocks and tasks)

        Args:
            container_id: Container UUID

        Returns:
            True if deleted
        """
        query = "DELETE FROM containers WHERE id = $1::uuid"
        await db.execute(query, container_id)
        return True

    @staticmethod
    async def add_block(
        container_id: str,
        name: str,
        duration: int,
        position: int,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add block to container

        Args:
            container_id: Container UUID
            name: Block name
            duration: Block duration in minutes
            position: Position in container
            color: Optional hex color

        Returns:
            Updated container

        Raises:
            Exception: If blocks exceed container total_duration
        """
        query = """
            INSERT INTO blocks (container_id, name, duration, position, color)
            VALUES ($1::uuid, $2, $3, $4, $5)
            RETURNING id::text
        """

        try:
            await db.execute(query, container_id, name, duration, position, color)
        except Exception as e:
            if "exceeds container limit" in str(e):
                raise Exception(f"Cannot add block: {str(e)}")
            raise

        return await ContainerService.get_container(container_id)

    @staticmethod
    async def update_blocks(
        container_id: str,
        blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Replace all blocks in container

        Args:
            container_id: Container UUID
            blocks: List of block data

        Returns:
            Updated container
        """
        async with db.transaction():
            # Delete existing blocks
            await db.execute(
                "DELETE FROM blocks WHERE container_id = $1::uuid",
                container_id
            )

            # Insert new blocks
            for block in blocks:
                await db.execute(
                    """
                    INSERT INTO blocks (container_id, name, duration, position, color)
                    VALUES ($1::uuid, $2, $3, $4, $5)
                    """,
                    container_id,
                    block['name'],
                    block['duration'],
                    block['position'],
                    block.get('color')
                )

        return await ContainerService.get_container(container_id)

    @staticmethod
    async def add_task(
        block_id: str,
        title: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add task to block

        Args:
            block_id: Block UUID
            title: Task title
            description: Optional description

        Returns:
            Created task
        """
        query = """
            INSERT INTO tasks (block_id, title, description)
            VALUES ($1::uuid, $2, $3)
            RETURNING id::text, title, description, completed, block_id::text, created_at, completed_at
        """

        result = await db.fetch_one(query, block_id, title, description)
        return dict(result)

    @staticmethod
    async def toggle_task(
        task_id: str,
        completed: bool
    ) -> Dict[str, Any]:
        """
        Toggle task completion

        Args:
            task_id: Task UUID
            completed: New completion status

        Returns:
            Updated task
        """
        query = """
            UPDATE tasks
            SET completed = $1,
                completed_at = CASE WHEN $1 THEN NOW() ELSE NULL END
            WHERE id = $2::uuid
            RETURNING id::text, title, description, completed, block_id::text, created_at, completed_at
        """

        result = await db.fetch_one(query, completed, task_id)
        return dict(result)
