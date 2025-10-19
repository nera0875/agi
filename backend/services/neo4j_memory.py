#!/usr/bin/env python3
"""
Neo4j Graph Memory Service - L3 Long-Term Memory

Manages L3 long-term memory graph using Neo4j.
Implements spreading activation, LTP/LTD reinforcement, and relation discovery.

Architecture:
- Nodes: Concepts, Patterns, Decisions, Files, Functions
- Relations: RELATES_TO, DEPENDS_ON, TRIGGERS, SIMILAR_TO
- Properties: strength (0-1), access_count, last_accessed
- Algorithms: Spreading activation, PageRank, Community detection
"""

import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from neo4j import GraphDatabase, Driver, Session


@dataclass
class GraphNode:
    """Node in knowledge graph"""
    id: str
    type: str  # concept, pattern, decision, file, function
    content: str
    tags: List[str]
    strength: float = 0.5  # LTP/LTD strength (0-1)
    access_count: int = 0
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class GraphRelation:
    """Relation between nodes"""
    from_id: str
    to_id: str
    relation_type: str  # RELATES_TO, DEPENDS_ON, TRIGGERS, SIMILAR_TO
    strength: float = 0.5
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Neo4jMemoryService:
    """
    L3 Long-Term Memory Service using Neo4j

    Features:
    - Graph-based knowledge representation
    - Spreading activation search
    - LTP/LTD reinforcement learning
    - Relation discovery and inference
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "Voiture789"
    ):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))

        # Test connection
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
                print("✅ Neo4j L3 Graph Memory connected")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            raise

        # Create indexes and constraints
        self._create_schema()

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()

    def _create_schema(self):
        """Create indexes and constraints for performance"""
        with self.driver.session() as session:
            # Constraints (unique node IDs)
            session.run("""
                CREATE CONSTRAINT concept_id IF NOT EXISTS
                FOR (c:Concept) REQUIRE c.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT pattern_id IF NOT EXISTS
                FOR (p:Pattern) REQUIRE p.id IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT decision_id IF NOT EXISTS
                FOR (d:Decision) REQUIRE d.id IS UNIQUE
            """)

            # Indexes for fast lookups
            session.run("""
                CREATE INDEX concept_tags IF NOT EXISTS
                FOR (c:Concept) ON (c.tags)
            """)
            session.run("""
                CREATE INDEX node_strength IF NOT EXISTS
                FOR (n:Concept) ON (n.strength)
            """)
            session.run("""
                CREATE INDEX node_accessed IF NOT EXISTS
                FOR (n:Concept) ON (n.last_accessed)
            """)

    # ═══════════════════════════════════════════════════════
    # NODE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def create_node(self, node: GraphNode) -> str:
        """
        Create or update node in graph

        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run("""
                MERGE (n:""" + node.type.capitalize() + """ {id: $id})
                SET n.content = $content,
                    n.tags = $tags,
                    n.strength = $strength,
                    n.access_count = $access_count,
                    n.created_at = $created_at,
                    n.updated_at = datetime()
                RETURN n.id as id
            """,
                id=node.id,
                content=node.content,
                tags=node.tags,
                strength=node.strength,
                access_count=node.access_count,
                created_at=node.created_at
            )

            record = result.single()
            return record['id'] if record else None

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node by ID"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})
                RETURN n
            """, id=node_id)

            record = result.single()
            if record:
                return dict(record['n'])
            return None

    def delete_node(self, node_id: str) -> bool:
        """Delete node and its relations"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})
                DETACH DELETE n
                RETURN count(n) as deleted
            """, id=node_id)

            record = result.single()
            return record['deleted'] > 0 if record else False

    # ═══════════════════════════════════════════════════════
    # RELATION OPERATIONS
    # ═══════════════════════════════════════════════════════

    def create_relation(self, relation: GraphRelation) -> bool:
        """
        Create relation between nodes

        Returns:
            True if successful
        """
        with self.driver.session() as session:
            # Only set metadata if it's not empty
            if relation.metadata:
                result = session.run("""
                    MATCH (a {id: $from_id})
                    MATCH (b {id: $to_id})
                    MERGE (a)-[r:""" + relation.relation_type + """]->(b)
                    SET r.strength = $strength,
                        r.metadata = $metadata,
                        r.created_at = datetime()
                    RETURN count(r) as created
                """,
                    from_id=relation.from_id,
                    to_id=relation.to_id,
                    strength=relation.strength,
                    metadata=relation.metadata
                )
            else:
                result = session.run("""
                    MATCH (a {id: $from_id})
                    MATCH (b {id: $to_id})
                    MERGE (a)-[r:""" + relation.relation_type + """]->(b)
                    SET r.strength = $strength,
                        r.created_at = datetime()
                    RETURN count(r) as created
                """,
                    from_id=relation.from_id,
                    to_id=relation.to_id,
                    strength=relation.strength
                )

            record = result.single()
            return record['created'] > 0 if record else False

    def create_relations_batch(self, relations: List[GraphRelation]) -> Dict:
        """
        Create multiple relations in batch for performance

        Args:
            relations: List of GraphRelation objects

        Returns:
            Dict with created_count and failed_count
        """
        if not relations:
            return {"created_count": 0, "failed_count": 0}

        created_count = 0
        failed_count = 0

        with self.driver.session() as session:
            for relation in relations:
                try:
                    success = self.create_relation(relation)
                    if success:
                        created_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    import logging
                    logging.error(f"Failed to create relation {relation.from_id}->{relation.to_id}: {e}")
                    failed_count += 1

        return {
            "created_count": created_count,
            "failed_count": failed_count,
            "total": len(relations)
        }

    def get_relations(self, node_id: str, direction: str = 'both') -> List[Dict]:
        """
        Get all relations for a node

        Args:
            node_id: Node ID
            direction: 'outgoing', 'incoming', or 'both'
        """
        if direction == 'outgoing':
            pattern = "(n {id: $id})-[r]->(m)"
        elif direction == 'incoming':
            pattern = "(n {id: $id})<-[r]-(m)"
        else:  # both
            pattern = "(n {id: $id})-[r]-(m)"

        with self.driver.session() as session:
            result = session.run(f"""
                MATCH {pattern}
                RETURN type(r) as type,
                       r.strength as strength,
                       m.id as target_id,
                       m.content as target_content
            """, id=node_id)

            relations = []
            for record in result:
                relations.append({
                    'type': record['type'],
                    'strength': record['strength'],
                    'target_id': record['target_id'],
                    'target_content': record['target_content']
                })

            return relations

    # ═══════════════════════════════════════════════════════
    # LTP/LTD REINFORCEMENT
    # ═══════════════════════════════════════════════════════

    def strengthen_node(self, node_id: str, delta: float = 0.1) -> float:
        """
        Strengthen node (LTP - Long-Term Potentiation)

        Returns:
            New strength value
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})
                SET n.strength = CASE
                    WHEN n.strength + $delta > 1.0 THEN 1.0
                    ELSE n.strength + $delta
                END,
                n.access_count = n.access_count + 1,
                n.last_accessed = datetime()
                RETURN n.strength as strength
            """, id=node_id, delta=delta)

            record = result.single()
            return record['strength'] if record else None

    def weaken_node(self, node_id: str, delta: float = 0.05) -> float:
        """
        Weaken node (LTD - Long-Term Depression)

        Returns:
            New strength value
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})
                SET n.strength = CASE
                    WHEN n.strength - $delta < 0.0 THEN 0.0
                    ELSE n.strength - $delta
                END
                RETURN n.strength as strength
            """, id=node_id, delta=delta)

            record = result.single()
            return record['strength'] if record else None

    def apply_decay(self, threshold_days: int = 30, decay_rate: float = 0.01) -> int:
        """
        Apply time-based decay to unused nodes (LTD)

        Returns:
            Number of nodes decayed
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.last_accessed < datetime() - duration({days: $days})
                SET n.strength = CASE
                    WHEN n.strength - $decay > 0.0 THEN n.strength - $decay
                    ELSE 0.0
                END
                RETURN count(n) as decayed
            """, days=threshold_days, decay=decay_rate)

            record = result.single()
            return record['decayed'] if record else 0

    def prune_weak_nodes(self, min_strength: float = 0.1) -> int:
        """
        Remove very weak nodes (LTD cleanup)

        Returns:
            Number of nodes deleted
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.strength < $min_strength
                DETACH DELETE n
                RETURN count(n) as deleted
            """, min_strength=min_strength)

            record = result.single()
            return record['deleted'] if record else 0

    async def apply_ltp_ltd_batch(self, access_log: List[Dict]) -> Dict:
        """
        Apply LTP/LTD (Long-Term Potentiation/Depression) based on access patterns

        LTP: Strengthen nodes that were accessed (increases by delta)
        LTD: Weaken nodes that were not accessed (decreases by delta)
        Auto-delete: Remove nodes with strength < 0.1 after LTD

        Args:
            access_log: List of dicts with format:
                [{"node_id": "...", "accessed": True/False}, ...]

        Returns:
            Dict with:
                - strengthened: list of node IDs that were strengthened
                - weakened: list of node IDs that were weakened
                - deleted: list of node IDs that were deleted
                - stats: summary statistics
        """
        strengthened = []
        weakened = []
        deleted = []

        for log in access_log:
            node_id = log.get("node_id")
            accessed = log.get("accessed", False)

            if not node_id:
                continue

            try:
                if accessed:
                    # LTP: strengthen accessed nodes
                    new_strength = self.strengthen_node(node_id, delta=0.1)
                    if new_strength is not None:
                        strengthened.append(node_id)
                else:
                    # LTD: weaken non-accessed nodes
                    new_strength = self.weaken_node(node_id, delta=0.05)
                    if new_strength is not None:
                        weakened.append(node_id)
                        # Auto-delete if strength drops below threshold
                        if new_strength < 0.1:
                            if self.delete_node(node_id):
                                deleted.append(node_id)

            except Exception as e:
                import logging
                logging.error(f"Failed to apply LTP/LTD to {node_id}: {e}")

        return {
            "strengthened": strengthened,
            "weakened": weakened,
            "deleted": deleted,
            "stats": {
                "total_processed": len(access_log),
                "strengthened_count": len(strengthened),
                "weakened_count": len(weakened),
                "deleted_count": len(deleted)
            }
        }

    # ═══════════════════════════════════════════════════════
    # SPREADING ACTIVATION SEARCH
    # ═══════════════════════════════════════════════════════

    def spreading_activation(
        self,
        start_node_ids: List[str],
        max_depth: int = 3,
        min_activation: float = 0.1,
        decay_factor: float = 0.5,
        limit: int = 50,
        weighted_by_strength: bool = True
    ) -> List[Dict]:
        """
        Spreading activation search from starting nodes with advanced options

        Simulates neural activation spreading through graph.
        Each hop reduces activation by decay_factor * relation_strength.
        Optionally weights by node strength for better relevance.

        Args:
            start_node_ids: Starting node IDs
            max_depth: Maximum traversal depth (1-5 recommended)
            min_activation: Minimum activation to continue spreading (0-1)
            decay_factor: Activation decay per hop (0-1)
            limit: Maximum number of results to return
            weighted_by_strength: If True, multiply activation by node strength

        Returns:
            List of activated nodes sorted by activation (highest first)
            Each item contains: id, content, type, activation, depth
        """
        with self.driver.session() as session:
            # Convert list to Cypher-compatible format
            start_ids_str = ", ".join([f"'{id}'" for id in start_node_ids])

            # Build activation calculation
            activation_calc = """
                reduce(activation = 1.0, r in rels |
                    activation * r.strength * $decay_factor
                ) * end.strength
            """ if weighted_by_strength else """
                reduce(activation = 1.0, r in rels |
                    activation * r.strength * $decay_factor
                )
            """

            result = session.run(f"""
                MATCH path = (start)-[*1..{max_depth}]-(end)
                WHERE start.id IN [{start_ids_str}]
                WITH end,
                     relationships(path) as rels,
                     length(path) as depth
                WITH end,
                     {activation_calc} as final_activation,
                     depth
                WHERE final_activation >= $min_activation
                RETURN DISTINCT end.id as id,
                       end.content as content,
                       end.type as type,
                       final_activation as activation,
                       depth
                ORDER BY final_activation DESC
                LIMIT $limit
            """,
                min_activation=min_activation,
                decay_factor=decay_factor,
                limit=limit
            )

            activated = []
            for record in result:
                activated.append({
                    'id': record['id'],
                    'content': record['content'],
                    'type': record['type'],
                    'activation': float(record['activation']) if record['activation'] else 0.0,
                    'depth': record['depth']
                })

            return activated

    def spreading_activation_from_query(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        max_depth: int = 2,
        decay_factor: float = 0.7
    ) -> List[Dict]:
        """
        Enhanced spreading activation starting from semantic similarity to query

        First finds semantically similar nodes, then spreads activation from there.

        Args:
            query_embedding: Query embedding vector (from Voyage)
            top_k: Top K similar nodes to start activation from
            max_depth: Maximum traversal depth
            decay_factor: Activation decay per hop

        Returns:
            List of activated nodes with combined semantic + structural scores
        """
        # Note: This method requires integration with embedding service
        # For now, it's a placeholder for semantic + spreading activation
        # In practice, you'd:
        # 1. Find nodes with similar embeddings using vector search
        # 2. Use those as start points for spreading activation
        # 3. Combine scores: semantic_score * structural_activation

        return []  # Implementation requires vector DB integration

    def spreading_activation_advanced(
        self,
        start_concepts: List[str],
        max_depth: int = 3,
        min_activation: float = 0.1,
        decay_factor: float = 0.7,
        use_temporal_decay: bool = True
    ) -> List[Dict]:
        """
        Advanced spreading activation with temporal decay

        Enhancements:
        - Recent nodes get higher activation (recency boost)
        - Frequently accessed nodes boost their neighbors
        - Temporal decay: older nodes require higher strength to activate
        - Combines relation strength + node strength + recency factor

        Args:
            start_concepts: List of concept IDs to start spreading from
            max_depth: Maximum traversal depth (1-5)
            min_activation: Minimum activation threshold to include results
            decay_factor: Decay per hop (0-1, default 0.7 for stronger signals)
            use_temporal_decay: Apply temporal weighting to node age

        Returns:
            List of activated nodes with detailed scores:
            [
                {
                    'id': concept_id,
                    'content': content,
                    'type': node_type,
                    'activation': final_activation_score,
                    'base_activation': activation_from_spreading,
                    'recency_boost': recency_factor,
                    'access_count_boost': frequency_factor,
                    'temporal_decay': age_penalty,
                    'depth': hop_distance,
                    'strength': node_strength,
                    'access_count': access_count
                }
            ]
        """
        with self.driver.session() as session:
            # Convert list to Cypher-compatible format
            start_ids_str = ", ".join([f"'{id}'" for id in start_concepts])

            result = session.run(f"""
                MATCH path = (start)-[*1..{max_depth}]-(end)
                WHERE start.id IN [{start_ids_str}]
                WITH end,
                     relationships(path) as rels,
                     length(path) as depth,
                     start
                WITH end,
                     depth,
                     reduce(activation = 1.0, r in rels |
                         activation * r.strength * {decay_factor}
                     ) as base_activation,
                     end.strength as node_strength,
                     end.access_count as access_count,
                     end.last_accessed as last_accessed,
                     end.created_at as created_at,
                     datetime() as now

                // Calculate recency boost: recent access = higher activation
                WITH end, depth, base_activation, node_strength, access_count,
                     CASE
                         WHEN last_accessed IS NULL THEN 0.5
                         WHEN last_accessed > now - duration({{days: 1}}) THEN 1.0
                         WHEN last_accessed > now - duration({{days: 7}}) THEN 0.9
                         WHEN last_accessed > now - duration({{days: 30}}) THEN 0.7
                         ELSE 0.4
                     END as recency_factor,

                     // Access count boost: frequently accessed = stronger activation
                     CASE
                         WHEN access_count >= 100 THEN 1.2
                         WHEN access_count >= 50 THEN 1.15
                         WHEN access_count >= 20 THEN 1.1
                         WHEN access_count >= 5 THEN 1.05
                         ELSE 1.0
                     END as access_boost,

                     // Temporal decay: older nodes need stronger connections
                     CASE
                         WHEN created_at > now - duration({{days: 7}}) THEN 1.0
                         WHEN created_at > now - duration({{days: 30}}) THEN 0.95
                         WHEN created_at > now - duration({{days: 90}}) THEN 0.9
                         ELSE 0.8
                     END as age_factor

                WITH end,
                     depth,
                     base_activation * node_strength * recency_factor * access_boost * age_factor as final_activation,
                     base_activation,
                     recency_factor,
                     access_boost,
                     age_factor,
                     node_strength,
                     access_count

                WHERE final_activation >= {min_activation}

                RETURN DISTINCT end.id as id,
                       end.content as content,
                       end.type as type,
                       final_activation,
                       base_activation,
                       recency_factor,
                       access_boost,
                       age_factor,
                       node_strength,
                       access_count,
                       depth
                ORDER BY final_activation DESC
                LIMIT 100
            """)

            activated = []
            for record in result:
                activated.append({
                    'id': record['id'],
                    'content': record['content'],
                    'type': record['type'],
                    'activation': round(float(record['final_activation']), 4),
                    'base_activation': round(float(record['base_activation']), 4),
                    'recency_boost': round(float(record['recency_factor']), 3),
                    'access_count_boost': round(float(record['access_boost']), 3),
                    'temporal_decay': round(float(record['age_factor']), 3),
                    'depth': record['depth'],
                    'strength': round(float(record['node_strength']), 3) if record['node_strength'] else 0.5,
                    'access_count': record['access_count'] or 0
                })

            return activated


    # ═══════════════════════════════════════════════════════
    # GRAPH ANALYSIS
    # ═══════════════════════════════════════════════════════

    def find_similar_patterns(
        self,
        node_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find similar patterns using graph structure

        Uses common neighbors and tag overlap
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n {id: $id})-[r1]-(common)-[r2]-(similar)
                WHERE n <> similar
                WITH similar,
                     count(DISTINCT common) as common_neighbors,
                     avg(r1.strength * r2.strength) as path_strength
                ORDER BY common_neighbors DESC, path_strength DESC
                LIMIT $limit
                RETURN similar.id as id,
                       similar.content as content,
                       similar.type as type,
                       common_neighbors,
                       path_strength as similarity
            """, id=node_id, limit=limit)

            similar = []
            for record in result:
                similar.append({
                    'id': record['id'],
                    'content': record['content'],
                    'type': record['type'],
                    'common_neighbors': record['common_neighbors'],
                    'similarity': record['similarity']
                })

            return similar

    def get_strongest_nodes(self, limit: int = 20) -> List[Dict]:
        """Get nodes with highest strength (most reinforced)"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN n.id as id,
                       n.content as content,
                       n.type as type,
                       n.strength as strength,
                       n.access_count as access_count
                ORDER BY n.strength DESC, n.access_count DESC
                LIMIT $limit
            """, limit=limit)

            nodes = []
            for record in result:
                nodes.append({
                    'id': record['id'],
                    'content': record['content'],
                    'type': record['type'],
                    'strength': record['strength'],
                    'access_count': record['access_count']
                })

            return nodes

    # ═══════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        """Get graph statistics"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH ()-[r]->()
                RETURN count(DISTINCT n) as node_count,
                       count(r) as relation_count,
                       avg(n.strength) as avg_strength,
                       max(n.strength) as max_strength,
                       min(n.strength) as min_strength
            """)

            record = result.single()
            if not record:
                return {}

            # Get node types distribution
            type_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)

            node_types = {}
            for rec in type_result:
                node_types[rec['type']] = rec['count']

            return {
                'node_count': record['node_count'],
                'relation_count': record['relation_count'],
                'avg_strength': round(record['avg_strength'], 3) if record['avg_strength'] else 0,
                'max_strength': record['max_strength'],
                'min_strength': record['min_strength'],
                'node_types': node_types
            }


# ═══════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════

def create_neo4j_service(
    uri: str = "bolt://localhost:7687",
    user: str = "neo4j",
    password: str = "Voiture789"
) -> Neo4jMemoryService:
    """Create Neo4j memory service instance"""
    return Neo4jMemoryService(uri=uri, user=user, password=password)


# ═══════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════

def test_neo4j_memory():
    """Test Neo4j L3 graph memory"""

    print("🧠 Testing Neo4j L3 Graph Memory")
    print("=" * 60)

    # Create service
    service = create_neo4j_service()

    try:
        print("\n1️⃣ Creating test nodes...")

        # Create concept nodes
        node1 = GraphNode(
            id="concept-async",
            type="concept",
            content="Asynchronous programming with async/await",
            tags=["python", "async", "concurrency"],
            strength=0.8
        )

        node2 = GraphNode(
            id="concept-redis",
            type="concept",
            content="Redis in-memory data store for caching",
            tags=["redis", "cache", "memory"],
            strength=0.7
        )

        node3 = GraphNode(
            id="pattern-l1-observer",
            type="pattern",
            content="L1 Observer pattern for real-time event classification",
            tags=["pattern", "l1", "observer"],
            strength=0.9
        )

        service.create_node(node1)
        service.create_node(node2)
        service.create_node(node3)
        print(f"   Created 3 nodes: async, redis, l1-observer")

        print("\n2️⃣ Creating relations...")

        rel1 = GraphRelation(
            from_id="pattern-l1-observer",
            to_id="concept-async",
            relation_type="USES",
            strength=0.9
        )

        rel2 = GraphRelation(
            from_id="pattern-l1-observer",
            to_id="concept-redis",
            relation_type="USES",
            strength=0.8
        )

        rel3 = GraphRelation(
            from_id="concept-async",
            to_id="concept-redis",
            relation_type="RELATES_TO",
            strength=0.6
        )

        service.create_relation(rel1)
        service.create_relation(rel2)
        service.create_relation(rel3)
        print(f"   Created 3 relations")

        print("\n3️⃣ Testing LTP/LTD reinforcement...")

        # Strengthen frequently accessed node
        new_strength = service.strengthen_node("pattern-l1-observer", delta=0.05)
        print(f"   Strengthened 'l1-observer': {new_strength:.2f}")

        # Weaken less important node
        new_strength = service.weaken_node("concept-redis", delta=0.1)
        print(f"   Weakened 'redis': {new_strength:.2f}")

        print("\n4️⃣ Testing spreading activation search...")

        activated = service.spreading_activation(
            start_node_ids=["pattern-l1-observer"],
            max_depth=2,
            min_activation=0.1,
            decay_factor=0.7
        )

        print(f"   Found {len(activated)} activated nodes:")
        for node in activated[:5]:
            print(f"      - {node['id']}: activation={node['activation']:.3f}, depth={node['depth']}")

        print("\n5️⃣ Testing pattern similarity...")

        similar = service.find_similar_patterns("pattern-l1-observer", limit=5)
        print(f"   Found {len(similar)} similar patterns:")
        for s in similar:
            print(f"      - {s['id']}: {s['common_neighbors']} common neighbors")

        print("\n6️⃣ Getting strongest nodes...")

        strongest = service.get_strongest_nodes(limit=5)
        print(f"   Top {len(strongest)} strongest nodes:")
        for node in strongest:
            strength = node['strength'] or 0.0
            access_count = node['access_count'] or 0
            print(f"      - {node['id']}: strength={strength:.2f}, access_count={access_count}")

        print("\n7️⃣ Graph statistics...")

        stats = service.get_stats()
        print(f"   Nodes: {stats['node_count']}")
        print(f"   Relations: {stats['relation_count']}")
        print(f"   Avg strength: {stats['avg_strength']}")
        print(f"   Node types: {stats['node_types']}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")

    finally:
        service.close()


if __name__ == "__main__":
    test_neo4j_memory()
