#!/usr/bin/env python3
"""
🧠 HUMAN BRAIN SYSTEM - Renforcement Learning + 3 Couches

Comme cerveau humain:
- L1 (Working Memory): 5-7 items en focus
- L2 (Short-term): Session actuelle + édits récents
- L3 (Long-term): Tout l'historique (Neo4j + PostgreSQL)

Auto-renforcement:
- LTP: Patterns utilisés → strength ↑
- LTD: Patterns non utilisés → strength ↓
- Consolidation nocturne: Nettoyage + optimisation
"""

import asyncio
import asyncpg
from neo4j import AsyncGraphDatabase
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("human-brain")

class HumanBrain:
    """Système cerveau humain avec 3 couches mémoire"""
    
    def __init__(self, pg_pool: asyncpg.Pool):
        self.pg_pool = pg_pool
        self.neo4j_driver = AsyncGraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "Voiture789")
        )
        self.session_id = None  # Set by bootstrap
    
    async def track_edit(self, file_path: str, edit_type: str, content_preview: str = "") -> Dict:
        """
        Track code edit → Auto-store in Neo4j + PostgreSQL
        
        Cascade automatique:
        1. Store in PostgreSQL (L2 session)
        2. Update Neo4j File node (L3 long-term)
        3. Reinforce (LTP)
        4. Update working memory (L1)
        """
        async with self.pg_pool.acquire() as conn:
            # 1. PostgreSQL L2 (session edits)
            await conn.execute("""
                INSERT INTO code_edits (
                    file_path, edit_type, content_preview, session_id
                ) VALUES ($1, $2, $3, $4)
            """, file_path, edit_type, content_preview[:500], self.session_id)
        
        # 2. Neo4j L3 (long-term file knowledge)
        async with self.neo4j_driver.session() as session:
            result = await session.run("""
                MERGE (f:File {path: $path})
                ON CREATE SET
                    f.name = $name,
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
                
                WITH f
                
                // Link to current session (L2)
                MERGE (s:Session {id: $session_id})
                MERGE (s)-[:EDITED_TODAY]->(f)
                
                RETURN f.strength as strength, f.access_count as accesses
            """, path=file_path, name=file_path.split('/')[-1], session_id=str(self.session_id))
            
            record = await result.single()
        
        # 3. Update working memory L1
        await self._update_working_memory(current_file=file_path)
        
        return {
            "tracked": True,
            "file": file_path,
            "strength": record["strength"],
            "accesses": record["accesses"],
            "layer": "L2" if record["strength"] < 0.7 else "L1"
        }
    
    async def _update_working_memory(self, current_file: str = None, current_task: str = None):
        """Update L1 working memory context"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO working_memory (session_id, current_file, current_task, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET
                    current_file = COALESCE($2, working_memory.current_file),
                    current_task = COALESCE($3, working_memory.current_task),
                    updated_at = NOW()
            """, self.session_id, current_file, current_task)
    
    async def get_working_memory(self) -> Dict:
        """Get L1 working memory (current focus)"""
        async with self.pg_pool.acquire() as conn:
            wm = await conn.fetchrow("""
                SELECT current_file, current_function, current_task, focus_concepts
                FROM working_memory
                WHERE session_id = $1
            """, self.session_id)
            
            if not wm:
                return {}
            
            return {
                "current_file": wm["current_file"],
                "current_function": wm["current_function"],
                "current_task": wm["current_task"],
                "focus_concepts": wm["focus_concepts"] or []
            }
    
    async def get_recent_edits(self, limit: int = 10) -> List[Dict]:
        """Get L2 recent edits (short-term memory)"""
        async with self.pg_pool.acquire() as conn:
            edits = await conn.fetch("""
                SELECT file_path, edit_type, edited_at
                FROM code_edits
                WHERE session_id = $1
                ORDER BY edited_at DESC
                LIMIT $2
            """, self.session_id, limit)
            
            return [
                {
                    "file": e["file_path"],
                    "type": e["edit_type"],
                    "when": str(e["edited_at"])
                }
                for e in edits
            ]
    
    async def spreading_activation(self, query: str, depth: int = 2) -> List[Dict]:
        """
        L3 - Spreading activation dans Neo4j
        
        Comme cerveau: activation se propage de concept en concept
        Depth contrôlé par neurotransmitters (dopamine/GABA)
        """
        async with self.neo4j_driver.session() as session:
            result = await session.run("""
                // Find seed concepts matching query
                MATCH (seed:Concept)
                WHERE seed.content ILIKE $query
                   OR seed.tags && [$query]
                
                // Spread activation
                OPTIONAL MATCH path = (seed)-[:SYNAPSE*0..$depth]-(target:Concept)
                
                WITH target, length(path) as distance,
                     1.0 / (length(path) + 1) as activation
                
                WHERE activation >= 0.3
                
                // LTP: Renforce synapses utilisées
                WITH target, activation
                MATCH (target)-[syn:SYNAPSE]-(related)
                SET syn.strength = CASE
                    WHEN syn.strength + 0.05 > 1.0 THEN 1.0
                    ELSE syn.strength + 0.05
                END,
                syn.use_count = syn.use_count + 1
                
                RETURN DISTINCT
                    target.content as content,
                    target.tags as tags,
                    activation
                ORDER BY activation DESC
                LIMIT 20
            """, query=f"%{query}%", depth=depth)
            
            results = []
            async for record in result:
                results.append({
                    "content": record["content"],
                    "tags": record["tags"] or [],
                    "activation": record["activation"]
                })
            
            return results
    
    async def consolidate_night(self) -> Dict:
        """
        Consolidation nocturne (LTD + cleanup)
        
        Comme cerveau pendant sommeil:
        - Weaken unused patterns (LTD)
        - Delete very weak patterns (< 0.1)
        - Strengthen important patterns
        - Cleanup old sessions
        """
        start_time = datetime.now()
        stats = {
            "rules_weakened": 0,
            "files_weakened": 0,
            "concepts_deleted": 0,
            "sessions_cleaned": 0
        }
        
        async with self.neo4j_driver.session() as session:
            # 1. LTD on Rules (unused >7 days)
            result = await session.run("""
                MATCH (r:Rule)
                WHERE r.last_accessed IS NULL
                   OR r.last_accessed < datetime() - duration('P7D')
                
                SET r.strength = CASE
                    WHEN r.strength * 0.95 < 0.1 THEN 0.1
                    ELSE r.strength * 0.95
                END
                
                RETURN count(r) as weakened
            """)
            record = await result.single()
            stats["rules_weakened"] = record["weakened"]
            
            # 2. LTD on Files (unused >30 days)
            result = await session.run("""
                MATCH (f:File)
                WHERE f.last_modified < datetime() - duration('P30D')
                
                SET f.strength = CASE
                    WHEN f.strength * 0.90 < 0.1 THEN 0.1
                    ELSE f.strength * 0.90
                END
                
                RETURN count(f) as weakened
            """)
            record = await result.single()
            stats["files_weakened"] = record["weakened"]
            
            # 3. Delete very weak concepts (< 0.1 strength, unused >90 days)
            result = await session.run("""
                MATCH (c:Concept)
                WHERE c.strength < 0.1
                  AND c.last_accessed < datetime() - duration('P90D')
                
                DETACH DELETE c
                RETURN count(c) as deleted
            """)
            record = await result.single()
            stats["concepts_deleted"] = record["deleted"]
        
        # 4. Cleanup old sessions (>30 days)
        async with self.pg_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM code_edits
                WHERE edited_at < NOW() - INTERVAL '30 days'
            """)
            stats["sessions_cleaned"] = int(result.split()[-1])
        
        # 5. Log consolidation
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO consolidation_log (
                    consolidation_type, items_processed, items_weakened,
                    items_deleted, executed_at, duration_ms
                ) VALUES ('night_consolidation', $1, $2, $3, NOW(), $4)
            """,
                stats["rules_weakened"] + stats["files_weakened"],
                stats["rules_weakened"] + stats["files_weakened"],
                stats["concepts_deleted"],
                int(duration)
            )
        
        return {
            "success": True,
            "stats": stats,
            "duration_ms": int(duration)
        }
    
    async def close(self):
        """Close connections"""
        await self.neo4j_driver.close()


# ═══════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════

async def test_brain():
    """Test human brain system"""
    import asyncpg
    
    pool = await asyncpg.create_pool(
        "postgresql://agi_user:agi_password@localhost:5432/agi_db"
    )
    
    brain = HumanBrain(pool)
    brain.session_id = "test-session-123"
    
    print("🧠 Testing Human Brain System")
    print("=" * 80)
    
    # Test 1: Track edit
    print("\n1️⃣ Track edit...")
    result = await brain.track_edit(
        "/home/pilote/projet/agi/test.py",
        "modified",
        "def test(): pass"
    )
    print(f"   ✅ {result}")
    
    # Test 2: Get working memory
    print("\n2️⃣ Working memory (L1)...")
    wm = await brain.get_working_memory()
    print(f"   ✅ {wm}")
    
    # Test 3: Recent edits
    print("\n3️⃣ Recent edits (L2)...")
    edits = await brain.get_recent_edits(5)
    print(f"   ✅ {len(edits)} edits")
    
    # Test 4: Spreading activation
    print("\n4️⃣ Spreading activation (L3)...")
    results = await brain.spreading_activation("test", depth=2)
    print(f"   ✅ {len(results)} concepts activated")
    
    await brain.close()
    await pool.close()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(test_brain())
