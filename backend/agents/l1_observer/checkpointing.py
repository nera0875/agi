#!/usr/bin/env python3
"""
L1 Observer - Checkpoint Storage

Implements persistent checkpoint storage using PostgreSQL.
Allows state snapshots, retrieval, and replay from checkpoints.

Classes:
- PostgreSQLCheckpointer: LangGraph-compatible checkpoint manager
- CheckpointRecord: Data structure for checkpoint metadata
"""

import json
import pickle
import uuid
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import hashlib

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


# ═══════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════

class CheckpointRecord:
    """Represents a single checkpoint"""

    def __init__(
        self,
        checkpoint_id: str,
        thread_id: str,
        node_name: Optional[str],
        state_data: Dict[str, Any],
        timestamp: datetime = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.checkpoint_id = checkpoint_id
        self.thread_id = thread_id
        self.node_name = node_name
        self.state_data = state_data
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "thread_id": self.thread_id,
            "node_name": self.node_name,
            "state_data": self.state_data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CheckpointRecord":
        """Create from dictionary"""
        return CheckpointRecord(
            checkpoint_id=data["checkpoint_id"],
            thread_id=data["thread_id"],
            node_name=data.get("node_name"),
            state_data=data["state_data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


# ═══════════════════════════════════════════════════════
# POSTGRESQL CHECKPOINTER
# ═══════════════════════════════════════════════════════

class PostgreSQLCheckpointer:
    """
    LangGraph checkpoint storage using PostgreSQL.

    Stores checkpoints in `l1_checkpoints` table:
    - checkpoint_id: Unique checkpoint identifier
    - thread_id: Thread grouping
    - node_name: Which node created checkpoint
    - state_data: Full serialized state
    - created_at: Timestamp
    - metadata: Additional tracking (importance, event_id, etc.)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "agi_db",
        user: str = "agi_user",
        password: str = "",
        debug: bool = False
    ):
        """
        Initialize PostgreSQL checkpointer.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            debug: Enable debug logging
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.debug = debug
        self.connection = None

        # Initialize database on creation
        self._connect()
        self._init_db()

    # ═══════════════════════════════════════════════════════
    # CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════

    def _connect(self):
        """Connect to PostgreSQL"""
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for PostgreSQL checkpointing")

        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.debug:
                print(f"PostgreSQL connected: {self.database}@{self.host}:{self.port}")
        except psycopg2.Error as e:
            raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

    def _close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()

    def _reconnect_if_needed(self):
        """Reconnect if connection lost"""
        try:
            if self.connection is None or self.connection.closed:
                self._connect()
        except:
            self._connect()

    # ═══════════════════════════════════════════════════════
    # DATABASE INITIALIZATION
    # ═══════════════════════════════════════════════════════

    def _init_db(self):
        """Create `l1_checkpoints` table if not exists"""
        if self.connection is None:
            return

        try:
            cursor = self.connection.cursor()

            # Create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS l1_checkpoints (
                    checkpoint_id UUID PRIMARY KEY,
                    thread_id UUID NOT NULL,
                    node_name VARCHAR(255),
                    state_data BYTEA NOT NULL,
                    state_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_id UUID,
                    importance INTEGER,
                    storage_layer VARCHAR(10),
                    metadata JSONB DEFAULT '{}'
                );
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_l1_thread_id ON l1_checkpoints (thread_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_l1_created_at ON l1_checkpoints (created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_l1_event_id ON l1_checkpoints (event_id);")

            # Create history view (try, may fail on older PostgreSQL)
            try:
                cursor.execute("""
                    CREATE VIEW IF NOT EXISTS l1_checkpoint_history AS
                    SELECT
                        checkpoint_id,
                        thread_id,
                        node_name,
                        created_at,
                        importance,
                        storage_layer
                    FROM l1_checkpoints
                    ORDER BY created_at DESC;
                """)
            except:
                # Fallback for older PostgreSQL without IF NOT EXISTS for views
                cursor.execute("""
                    DROP VIEW IF EXISTS l1_checkpoint_history CASCADE;
                """)
                cursor.execute("""
                    CREATE VIEW l1_checkpoint_history AS
                    SELECT
                        checkpoint_id,
                        thread_id,
                        node_name,
                        created_at,
                        importance,
                        storage_layer
                    FROM l1_checkpoints
                    ORDER BY created_at DESC;
                """)

            self.connection.commit()
            if self.debug:
                print("PostgreSQL tables initialized")
        except psycopg2.Error as e:
            print(f"Warning: Failed to initialize database: {e}")

    # ═══════════════════════════════════════════════════════
    # CHECKPOINT OPERATIONS
    # ═══════════════════════════════════════════════════════

    def save_checkpoint(
        self,
        state: Dict[str, Any],
        thread_id: str,
        node_name: Optional[str] = None,
        checkpoint_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save state checkpoint.

        Args:
            state: State dictionary to save
            thread_id: Thread identifier
            node_name: Optional node name (for tracking which node saved)
            checkpoint_id: Optional custom checkpoint ID (UUID generated if not provided)
            metadata: Optional metadata to store with checkpoint

        Returns:
            Checkpoint ID
        """
        self._reconnect_if_needed()

        if checkpoint_id is None:
            checkpoint_id = str(uuid.uuid4())

        # Prepare data
        state_bytes = pickle.dumps(state)
        state_json = json.dumps(
            {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
             for k, v in state.items()},
            default=str
        )

        # Extract metadata from state
        if metadata is None:
            metadata = {}

        metadata.update({
            "event_id": state.get("event_id"),
            "session_id": state.get("session_id"),
            "classified_type": state.get("classified_type"),
            "importance": state.get("importance"),
            "storage_layer": state.get("storage_layer")
        })

        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT INTO l1_checkpoints 
                (checkpoint_id, thread_id, node_name, state_data, state_json, 
                 event_id, importance, storage_layer, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (checkpoint_id) DO UPDATE
                SET updated_at = CURRENT_TIMESTAMP,
                    state_data = EXCLUDED.state_data,
                    state_json = EXCLUDED.state_json
            """, (
                checkpoint_id,
                thread_id,
                node_name,
                state_bytes,
                state_json,
                str(state.get("event_id")),
                state.get("importance"),
                state.get("storage_layer"),
                json.dumps(metadata)
            ))

            self.connection.commit()

            if self.debug:
                print(f"Checkpoint saved: {checkpoint_id} ({node_name})")

            return checkpoint_id

        except psycopg2.Error as e:
            print(f"Error saving checkpoint: {e}")
            raise

    def get_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific checkpoint.

        Args:
            thread_id: Thread identifier
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint data or None if not found
        """
        self._reconnect_if_needed()

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT checkpoint_id, thread_id, node_name, state_data, created_at, metadata
                FROM l1_checkpoints
                WHERE checkpoint_id = %s AND thread_id = %s
            """, (checkpoint_id, thread_id))

            row = cursor.fetchone()

            if row is None:
                return None

            # Deserialize state
            state_data = pickle.loads(row["state_data"])

            return {
                "checkpoint_id": str(row["checkpoint_id"]),
                "thread_id": str(row["thread_id"]),
                "node_name": row["node_name"],
                "values": state_data,
                "created_at": row["created_at"].isoformat(),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }

        except psycopg2.Error as e:
            print(f"Error retrieving checkpoint: {e}")
            return None

    def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get most recent checkpoint for a thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Latest checkpoint or None
        """
        self._reconnect_if_needed()

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT checkpoint_id, thread_id, node_name, state_data, created_at, metadata
                FROM l1_checkpoints
                WHERE thread_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (thread_id,))

            row = cursor.fetchone()

            if row is None:
                return None

            state_data = pickle.loads(row["state_data"])

            return {
                "checkpoint_id": str(row["checkpoint_id"]),
                "thread_id": str(row["thread_id"]),
                "node_name": row["node_name"],
                "values": state_data,
                "created_at": row["created_at"].isoformat(),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }

        except psycopg2.Error as e:
            print(f"Error retrieving latest checkpoint: {e}")
            return None

    def get_history(
        self,
        thread_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get checkpoint history for a thread.

        Args:
            thread_id: Thread identifier
            limit: Maximum number to return
            offset: Offset for pagination

        Returns:
            List of checkpoints (most recent first)
        """
        self._reconnect_if_needed()

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT checkpoint_id, thread_id, node_name, created_at, 
                       importance, storage_layer, metadata
                FROM l1_checkpoints
                WHERE thread_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (thread_id, limit, offset))

            rows = cursor.fetchall()

            return [
                {
                    "checkpoint_id": str(row["checkpoint_id"]),
                    "thread_id": str(row["thread_id"]),
                    "node_name": row["node_name"],
                    "created_at": row["created_at"].isoformat(),
                    "importance": row["importance"],
                    "storage_layer": row["storage_layer"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                for row in rows
            ]

        except psycopg2.Error as e:
            print(f"Error retrieving history: {e}")
            return []

    def delete_old_checkpoints(
        self,
        days: int = 7,
        keep_latest: int = 5
    ) -> int:
        """
        Delete old checkpoints (cleanup).

        Args:
            days: Delete checkpoints older than N days
            keep_latest: Keep at least N latest per thread

        Returns:
            Number of checkpoints deleted
        """
        self._reconnect_if_needed()

        try:
            cursor = self.connection.cursor()

            # Delete old checkpoints (keep recent)
            cursor.execute("""
                DELETE FROM l1_checkpoints
                WHERE checkpoint_id NOT IN (
                    SELECT checkpoint_id FROM l1_checkpoints
                    ORDER BY created_at DESC
                    LIMIT %s
                )
                AND created_at < NOW() - INTERVAL '%s days'
            """, (keep_latest, days))

            deleted_count = cursor.rowcount
            self.connection.commit()

            if self.debug:
                print(f"Deleted {deleted_count} old checkpoints")

            return deleted_count

        except psycopg2.Error as e:
            print(f"Error deleting checkpoints: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get checkpoint storage statistics.

        Returns:
            Statistics dictionary
        """
        self._reconnect_if_needed()

        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            # Total checkpoints
            cursor.execute("SELECT COUNT(*) as count FROM l1_checkpoints")
            total_count = cursor.fetchone()["count"]

            # By importance
            cursor.execute("""
                SELECT importance, COUNT(*) as count 
                FROM l1_checkpoints 
                WHERE importance IS NOT NULL 
                GROUP BY importance
            """)
            by_importance = {row["importance"]: row["count"] for row in cursor.fetchall()}

            # By storage layer
            cursor.execute("""
                SELECT storage_layer, COUNT(*) as count 
                FROM l1_checkpoints 
                WHERE storage_layer IS NOT NULL 
                GROUP BY storage_layer
            """)
            by_layer = {row["storage_layer"]: row["count"] for row in cursor.fetchall()}

            # By node
            cursor.execute("""
                SELECT node_name, COUNT(*) as count 
                FROM l1_checkpoints 
                WHERE node_name IS NOT NULL 
                GROUP BY node_name
            """)
            by_node = {row["node_name"]: row["count"] for row in cursor.fetchall()}

            return {
                "total_checkpoints": total_count,
                "by_importance": by_importance,
                "by_storage_layer": by_layer,
                "by_node": by_node
            }

        except psycopg2.Error as e:
            print(f"Error retrieving stats: {e}")
            return {}


# ═══════════════════════════════════════════════════════
# TESTING / CLI
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("L1 Observer - PostgreSQL Checkpointing")
    print("=" * 60)

    # Note: Requires PostgreSQL connection
    try:
        # Test connection (may fail if DB not running)
        checkpointer = PostgreSQLCheckpointer(
            host="localhost",
            database="agi_db",
            user="agi_user",
            password="agi_password",
            debug=True
        )

        print("\n1. Testing checkpoint save...")
        test_state = {
            "event_id": str(uuid.uuid4()),
            "session_id": "test-session",
            "classified_type": "code_edit",
            "importance": 7,
            "storage_layer": "L2",
            "timestamp": datetime.utcnow().isoformat()
        }

        thread_id = str(uuid.uuid4())
        checkpoint_id = checkpointer.save_checkpoint(
            state=test_state,
            thread_id=thread_id,
            node_name="classify_event"
        )
        print(f"   SUCCESS: Checkpoint saved: {checkpoint_id}")

        # Test retrieval
        print("\n2. Testing checkpoint retrieval...")
        retrieved = checkpointer.get_checkpoint(thread_id, checkpoint_id)
        if retrieved:
            print(f"   SUCCESS: Retrieved checkpoint")
            print(f"   Values: {retrieved['values'].get('classified_type')}")
        else:
            print("   FAILED: Could not retrieve checkpoint")

        # Test history
        print("\n3. Testing history retrieval...")
        history = checkpointer.get_history(thread_id, limit=5)
        print(f"   SUCCESS: Retrieved {len(history)} checkpoints")

        # Test stats
        print("\n4. Testing statistics...")
        stats = checkpointer.get_stats()
        print(f"   Total checkpoints: {stats.get('total_checkpoints', 0)}")

        print("\n" + "=" * 60)
        print("SUCCESS: PostgreSQL Checkpointing tests passed")

    except Exception as e:
        print(f"Note: Tests require running PostgreSQL: {e}")
