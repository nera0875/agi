"""
Database connection pool management
"""

import logging
from typing import Optional

import asyncpg
from asyncpg.pool import Pool

from config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    PostgreSQL connection pool manager
    """

    def __init__(self):
        self.pool: Optional[Pool] = None

    async def connect(self) -> Pool:
        """
        Create connection pool

        Returns:
            Connection pool
        """
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=10,
                max_size=20,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )

            logger.info("Database connection pool created")

        return self.pool

    async def disconnect(self):
        """
        Close connection pool
        """
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args):
        """
        Execute query

        Args:
            query: SQL query
            args: Query arguments

        Returns:
            Query result
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """
        Fetch query results

        Args:
            query: SQL query
            args: Query arguments

        Returns:
            Query results
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchval(self, query: str, *args):
        """
        Fetch single value

        Args:
            query: SQL query
            args: Query arguments

        Returns:
            Single value
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        Fetch single row

        Args:
            query: SQL query
            args: Query arguments

        Returns:
            Single row
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)


# Global database instance
db = Database()