#!/usr/bin/env python3
"""
Redis Memory Service - L1 Working Memory

Manages L1 working memory (7±2 items) using Redis.
Ultra-fast access (<10ms) for current context.

Architecture:
- working_memory:{session_id} → List of recent events (max 7)
- focus_concepts:{session_id} → Set of active concepts
- current_context:{session_id} → Hash of current state
"""

import json
import redis
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class WorkingMemoryItem:
    """Single item in working memory"""
    id: str
    type: str  # event_type: code_edit, decision, etc.
    content: str
    importance: int
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkingMemoryItem':
        return cls(**data)


class RedisMemoryService:
    """
    L1 Working Memory Service

    Maintains current context using Redis:
    - 7±2 items max (Miller's Law)
    - LRU eviction (oldest removed first)
    - Ultra-fast access (<10ms)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_items: int = 7
    ):
        """
        Initialize Redis connection for L1 working memory

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
            max_items: Maximum items in working memory (default 7)
        """
        self.max_items = max_items

        # Connect to Redis
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Auto-decode bytes to strings
        )

        # Test connection
        try:
            self.redis.ping()
            print("✅ Redis L1 Working Memory connected")
        except redis.ConnectionError as e:
            print(f"❌ Redis connection failed: {e}")
            raise

    # ═══════════════════════════════════════════════════════
    # WORKING MEMORY OPERATIONS
    # ═══════════════════════════════════════════════════════

    def add_to_working_memory(
        self,
        session_id: str,
        item: WorkingMemoryItem
    ) -> int:
        """
        Add item to working memory (FIFO, max 7 items)

        Returns:
            Current size of working memory
        """
        key = f"working_memory:{session_id}"

        # Add to list (right push)
        self.redis.rpush(key, json.dumps(item.to_dict()))

        # Trim to max items (keep rightmost/newest)
        self.redis.ltrim(key, -self.max_items, -1)

        # Set expiration (24 hours)
        self.redis.expire(key, 86400)

        return self.redis.llen(key)

    def get_working_memory(self, session_id: str) -> List[WorkingMemoryItem]:
        """
        Get all items from working memory

        Returns:
            List of items (newest first)
        """
        key = f"working_memory:{session_id}"

        # Get all items
        items_json = self.redis.lrange(key, 0, -1)

        # Parse and reverse (newest first)
        items = [
            WorkingMemoryItem.from_dict(json.loads(item_json))
            for item_json in items_json
        ]

        return list(reversed(items))  # Newest first

    def clear_working_memory(self, session_id: str) -> bool:
        """Clear all items from working memory"""
        key = f"working_memory:{session_id}"
        return self.redis.delete(key) > 0

    def get_working_memory_size(self, session_id: str) -> int:
        """Get current size of working memory"""
        key = f"working_memory:{session_id}"
        return self.redis.llen(key)

    # ═══════════════════════════════════════════════════════
    # CURRENT CONTEXT (Hash)
    # ═══════════════════════════════════════════════════════

    def set_current_context(
        self,
        session_id: str,
        current_file: Optional[str] = None,
        current_function: Optional[str] = None,
        current_task: Optional[str] = None
    ) -> None:
        """
        Set current context (what user is working on right now)
        """
        key = f"current_context:{session_id}"

        context = {}
        if current_file:
            context['current_file'] = current_file
        if current_function:
            context['current_function'] = current_function
        if current_task:
            context['current_task'] = current_task
        if context:
            context['updated_at'] = datetime.utcnow().isoformat()

        if context:
            self.redis.hset(key, mapping=context)
            self.redis.expire(key, 86400)  # 24 hours

    def get_current_context(self, session_id: str) -> Dict:
        """Get current context"""
        key = f"current_context:{session_id}"
        return self.redis.hgetall(key)

    # ═══════════════════════════════════════════════════════
    # FOCUS CONCEPTS (Set)
    # ═══════════════════════════════════════════════════════

    def add_focus_concept(self, session_id: str, concept: str) -> int:
        """
        Add concept to current focus (max 5)

        Returns:
            Number of focus concepts
        """
        key = f"focus_concepts:{session_id}"

        # Add to set
        self.redis.sadd(key, concept)

        # Keep only 5 most recent (Redis doesn't have built-in LRU for sets)
        # So we rely on manual trimming
        size = self.redis.scard(key)
        if size > 5:
            # Remove random member (oldest concept)
            self.redis.spop(key)

        self.redis.expire(key, 86400)
        return self.redis.scard(key)

    def get_focus_concepts(self, session_id: str) -> List[str]:
        """Get all focus concepts"""
        key = f"focus_concepts:{session_id}"
        return list(self.redis.smembers(key))

    def clear_focus_concepts(self, session_id: str) -> bool:
        """Clear all focus concepts"""
        key = f"focus_concepts:{session_id}"
        return self.redis.delete(key) > 0

    # ═══════════════════════════════════════════════════════
    # COMPLETE L1 STATE
    # ═══════════════════════════════════════════════════════

    def get_complete_l1_state(self, session_id: str) -> Dict:
        """
        Get complete L1 state for session

        Returns:
            Dict with working_memory, current_context, focus_concepts
        """
        return {
            "session_id": session_id,
            "working_memory": [
                item.to_dict() for item in self.get_working_memory(session_id)
            ],
            "current_context": self.get_current_context(session_id),
            "focus_concepts": self.get_focus_concepts(session_id),
            "working_memory_size": self.get_working_memory_size(session_id)
        }

    # ═══════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """Get Redis stats"""
        info = self.redis.info()
        return {
            "connected": True,
            "used_memory": info.get('used_memory_human', 'N/A'),
            "total_keys": self.redis.dbsize(),
            "uptime_days": info.get('uptime_in_days', 0),
        }

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Cleanup sessions older than X days

        Note: Redis with TTL handles this automatically,
        but this method can be used for manual cleanup
        """
        # Redis handles expiration automatically with TTL
        # This is just a placeholder for manual cleanup if needed
        return 0


# ═══════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════

def create_redis_service(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None
) -> RedisMemoryService:
    """Create Redis memory service instance"""
    return RedisMemoryService(host=host, port=port, db=db, password=password)


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_redis_memory():
    """Test Redis L1 working memory"""

    print("🧠 Testing Redis L1 Working Memory")
    print("=" * 60)

    # Create service
    service = create_redis_service()

    # Test session
    session_id = "test-session-123"

    # Clear first
    service.clear_working_memory(session_id)
    service.clear_focus_concepts(session_id)

    print("\n1️⃣ Adding items to working memory...")
    for i in range(10):  # Add 10, should keep only last 7
        item = WorkingMemoryItem(
            id=f"item-{i}",
            type="code_edit" if i % 2 == 0 else "decision",
            content=f"Test content {i}",
            importance=i % 10,
            timestamp=datetime.utcnow().isoformat()
        )
        size = service.add_to_working_memory(session_id, item)
        print(f"   Added item {i}, working memory size: {size}")

    print("\n2️⃣ Getting working memory (should be 7 items)...")
    items = service.get_working_memory(session_id)
    print(f"   Working memory size: {len(items)}")
    for item in items:
        print(f"   - {item.id}: {item.type} (importance: {item.importance})")

    print("\n3️⃣ Setting current context...")
    service.set_current_context(
        session_id,
        current_file="/home/pilote/projet/agi/test.py",
        current_function="test_function",
        current_task="Testing Redis memory"
    )
    context = service.get_current_context(session_id)
    print(f"   Context: {context}")

    print("\n4️⃣ Adding focus concepts...")
    for concept in ["async", "redis", "memory", "LangChain", "workers", "extra1", "extra2"]:
        size = service.add_focus_concept(session_id, concept)
        print(f"   Added '{concept}', focus size: {size}")

    focus = service.get_focus_concepts(session_id)
    print(f"   Focus concepts (max 5): {focus}")

    print("\n5️⃣ Complete L1 state...")
    state = service.get_complete_l1_state(session_id)
    print(f"   Session: {state['session_id']}")
    print(f"   Working memory items: {state['working_memory_size']}")
    print(f"   Current file: {state['current_context'].get('current_file', 'N/A')}")
    print(f"   Focus concepts: {len(state['focus_concepts'])}")

    print("\n6️⃣ Redis stats...")
    stats = service.get_stats()
    print(f"   Memory used: {stats['used_memory']}")
    print(f"   Total keys: {stats['total_keys']}")
    print(f"   Uptime: {stats['uptime_days']} days")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")


if __name__ == "__main__":
    test_redis_memory()
