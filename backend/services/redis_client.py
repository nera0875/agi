"""
Redis client management
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis connection manager
    """

    def __init__(self):
        self.client: Optional[aioredis.Redis] = None

    async def connect(self) -> aioredis.Redis:
        """
        Create Redis connection

        Returns:
            Redis client
        """
        if self.client is None:
            self.client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False,  # For binary data (embeddings)
                max_connections=50
            )

            # Test connection
            await self.client.ping()
            logger.info("Redis connection established")

        return self.client

    async def disconnect(self):
        """
        Close Redis connection
        """
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Redis connection closed")

    async def get_client(self) -> aioredis.Redis:
        """
        Get Redis client

        Returns:
            Redis client
        """
        if not self.client:
            await self.connect()

        return self.client


# Global Redis instance
redis_client = RedisClient()