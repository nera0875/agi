"""
Database Manager - Handles connections to PostgreSQL, Neo4j, and Redis
"""

import asyncio
import logging
from typing import Optional
import asyncpg
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis
from config.settings import Settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database connections"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        self.redis_client = None
    
    async def initialize(self):
        """Initialize all database connections"""
        logger.info("🔌 Initializing database connections...")
        
        # PostgreSQL connection pool
        try:
            self.postgres_pool = await asyncpg.create_pool(
                self.settings.database_url,
                min_size=5,
                max_size=self.settings.db_pool_size,
                max_inactive_connection_lifetime=300
            )
            logger.info("✅ PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
        
        # Neo4j driver
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_url,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
                max_connection_pool_size=self.settings.neo4j_max_connection_pool_size
            )
            # Test connection
            await self.neo4j_driver.verify_connectivity()
            logger.info("✅ Neo4j driver initialized")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
        
        # Redis client
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                retry_on_timeout=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Redis client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close all database connections"""
        logger.info("🔌 Closing database connections...")
        
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("✅ PostgreSQL pool closed")
        
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            logger.info("✅ Neo4j driver closed")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Redis client closed")
    
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        return self.postgres_pool.acquire()
    
    async def get_neo4j_session(self):
        """Get Neo4j session"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j driver not initialized")
        return self.neo4j_driver.session()
    
    def get_redis_client(self):
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")
        return self.redis_client
    
    async def health_check(self) -> dict:
        """Check health of all database connections"""
        health = {
            "postgres": False,
            "neo4j": False,
            "redis": False
        }
        
        # PostgreSQL health check
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        # Neo4j health check
        try:
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            health["neo4j"] = True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
        
        # Redis health check
        try:
            await self.redis_client.ping()
            health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return health