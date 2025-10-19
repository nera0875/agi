"""
Graph Service - Neo4j Integration avec PostgreSQL
Gère la synchronisation PostgreSQL → Neo4j pour visualisation de graphe
Auto-détection de relations par similarité sémantique
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import asyncpg
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service de gestion du graphe de connaissances
    - Sync PostgreSQL relations → Neo4j
    - Auto-détection de relations par embedding similarity
    - Extraction d'entités pour enrichir le graphe
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: aioredis.Redis,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "Voiture789"
    ):
        self.db_pool = db_pool
        self.redis = redis_client
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self._neo4j_driver = None

    async def init_neo4j(self):
        """Initialize Neo4j driver"""
        try:
            from neo4j import AsyncGraphDatabase
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            logger.info("Neo4j driver initialized")
        except ImportError:
            logger.warning("Neo4j driver not installed. Install with: pip install neo4j")
            self._neo4j_driver = None
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            self._neo4j_driver = None

    async def close(self):
        """Close Neo4j connection"""
        if self._neo4j_driver:
            await self._neo4j_driver.close()

    # ============================================================================
    # GRAPH DATA QUERIES (PostgreSQL)
    # ============================================================================

    async def get_graph_nodes(
        self,
        node_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère les nœuds du graphe depuis PostgreSQL

        Args:
            node_types: Filtrer par types (Memory, Knowledge, Task)
            limit: Nombre max de nœuds

        Returns:
            Liste de nœuds avec id, label, type, properties
        """
        async with self.db_pool.acquire() as conn:
            nodes = []

            # Memory nodes
            if not node_types or "Memory" in node_types:
                query = """
                    SELECT
                        id,
                        content,
                        metadata,
                        source_type,
                        quality_score,
                        access_count,
                        created_at
                    FROM memory_store
                    ORDER BY quality_score DESC, access_count DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                for row in rows:
                    nodes.append({
                        "id": str(row["id"]),
                        "label": row["content"][:50] + "..." if len(row["content"]) > 50 else row["content"],
                        "type": "Memory",
                        "properties": {
                            "content": row["content"],
                            "source_type": row["source_type"],
                            "quality_score": float(row["quality_score"]) if row["quality_score"] else 0.5,
                            "access_count": row["access_count"] or 0,
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        }
                    })

            # Knowledge nodes
            if not node_types or "Knowledge" in node_types:
                query = """
                    SELECT
                        id,
                        section,
                        content,
                        tags,
                        priority,
                        created_at
                    FROM agi_knowledge
                    ORDER BY priority DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                for row in rows:
                    nodes.append({
                        "id": str(row["id"]),
                        "label": row["section"] or "Knowledge",
                        "type": "Knowledge",
                        "properties": {
                            "section": row["section"],
                            "content": row["content"],
                            "tags": row["tags"] or [],
                            "priority": row["priority"] or 0,
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        }
                    })

            # Task/Roadmap nodes
            if not node_types or "Task" in node_types:
                query = """
                    SELECT
                        id,
                        phase,
                        status,
                        next_actions,
                        priority,
                        created_at
                    FROM agi_roadmap
                    ORDER BY priority DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                for row in rows:
                    nodes.append({
                        "id": str(row["id"]),
                        "label": row["phase"] or "Task",
                        "type": "Task",
                        "properties": {
                            "phase": row["phase"],
                            "status": row["status"],
                            "next_actions": row["next_actions"] or [],
                            "priority": row["priority"] or 0,
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                        }
                    })

            return nodes

    async def get_graph_relations(
        self,
        source_id: Optional[str] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Récupère les relations du graphe depuis PostgreSQL

        Args:
            source_id: Filtrer par nœud source (optionnel)
            limit: Nombre max de relations

        Returns:
            Liste de relations avec id, source, target, type, weight
        """
        async with self.db_pool.acquire() as conn:
            if source_id:
                query = """
                    SELECT
                        id,
                        source_id,
                        target_id,
                        relation_type,
                        created_at
                    FROM relations
                    WHERE source_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, UUID(source_id), limit)
            else:
                query = """
                    SELECT
                        id,
                        source_id,
                        target_id,
                        relation_type,
                        created_at
                    FROM relations
                    ORDER BY created_at DESC
                    LIMIT $1
                """
                rows = await conn.fetch(query, limit)

            relations = []
            for row in rows:
                relations.append({
                    "id": str(row["id"]),
                    "source": str(row["source_id"]),
                    "target": str(row["target_id"]),
                    "type": row["relation_type"] or "RELATES_TO",
                    "weight": 1.0,  # Peut être calculé dynamiquement
                })

            return relations

    # ============================================================================
    # AUTO-DETECTION DE RELATIONS
    # ============================================================================

    async def detect_relations_by_similarity(
        self,
        threshold: float = 0.75,
        limit: int = 50
    ) -> int:
        """
        Détecte automatiquement les relations entre mémoires par similarité sémantique

        Args:
            threshold: Seuil de similarité (0-1)
            limit: Nombre max de paires à comparer

        Returns:
            Nombre de relations créées
        """
        async with self.db_pool.acquire() as conn:
            # Récupérer les mémoires avec leurs embeddings
            query = """
                SELECT id, content, embedding
                FROM memory_store
                WHERE embedding IS NOT NULL
                ORDER BY quality_score DESC, access_count DESC
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)

            if len(rows) < 2:
                logger.info("Pas assez de mémoires avec embeddings pour détecter des relations")
                return 0

            # Comparer les embeddings et créer des relations
            created_count = 0
            for i, row1 in enumerate(rows):
                for row2 in rows[i+1:]:
                    # Parse embeddings (stored as text/json)
                    try:
                        import json
                        emb1 = json.loads(row1["embedding"]) if isinstance(row1["embedding"], str) else row1["embedding"]
                        emb2 = json.loads(row2["embedding"]) if isinstance(row2["embedding"], str) else row2["embedding"]

                        # Calculer similarité cosine
                        similarity = self._cosine_similarity(emb1, emb2)

                        if similarity >= threshold:
                            # Créer la relation
                            insert_query = """
                                INSERT INTO relations (source_id, target_id, relation_type)
                                VALUES ($1, $2, $3)
                                ON CONFLICT DO NOTHING
                            """
                            await conn.execute(
                                insert_query,
                                row1["id"],
                                row2["id"],
                                f"SIMILAR_{int(similarity * 100)}"
                            )
                            created_count += 1
                    except Exception as e:
                        logger.error(f"Erreur lors du calcul de similarité: {e}")
                        continue

            logger.info(f"Créé {created_count} relations par similarité")
            return created_count

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        import numpy as np
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))

    # ============================================================================
    # NEO4J SYNC
    # ============================================================================

    async def sync_to_neo4j(self) -> Dict[str, int]:
        """
        Synchronise PostgreSQL → Neo4j

        Returns:
            Statistiques de sync (nodes_created, relations_created)
        """
        if not self._neo4j_driver:
            logger.warning("Neo4j driver not available, skipping sync")
            return {"nodes_created": 0, "relations_created": 0}

        async with self._neo4j_driver.session() as session:
            # Clear existing data (optionnel - à commenter en prod)
            # await session.run("MATCH (n) DETACH DELETE n")

            # Sync nodes
            nodes = await self.get_graph_nodes(limit=1000)
            nodes_created = 0

            for node in nodes:
                query = """
                    MERGE (n:Node {id: $id})
                    SET n.label = $label,
                        n.type = $type,
                        n.properties = $properties
                """
                await session.run(
                    query,
                    id=node["id"],
                    label=node["label"],
                    type=node["type"],
                    properties=node["properties"]
                )
                nodes_created += 1

            # Sync relations
            relations = await self.get_graph_relations(limit=1000)
            relations_created = 0

            for rel in relations:
                query = """
                    MATCH (source:Node {id: $source_id})
                    MATCH (target:Node {id: $target_id})
                    MERGE (source)-[r:RELATES {type: $rel_type}]->(target)
                    SET r.weight = $weight
                """
                await session.run(
                    query,
                    source_id=rel["source"],
                    target_id=rel["target"],
                    rel_type=rel["type"],
                    weight=rel["weight"]
                )
                relations_created += 1

            logger.info(f"Sync Neo4j: {nodes_created} nodes, {relations_created} relations")
            return {
                "nodes_created": nodes_created,
                "relations_created": relations_created
            }

    # ============================================================================
    # SEARCH & QUERY
    # ============================================================================

    async def search_nodes(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche de nœuds par texte

        Args:
            query: Texte de recherche
            limit: Nombre max de résultats

        Returns:
            Liste de nœuds correspondants
        """
        async with self.db_pool.acquire() as conn:
            search_query = f"%{query}%"

            # Search in memory_store
            sql = """
                SELECT
                    id,
                    content,
                    'Memory' as type,
                    metadata,
                    quality_score
                FROM memory_store
                WHERE content ILIKE $1
                ORDER BY quality_score DESC
                LIMIT $2
            """
            rows = await conn.fetch(sql, search_query, limit)

            results = []
            for row in rows:
                results.append({
                    "id": str(row["id"]),
                    "label": row["content"][:50] + "..." if len(row["content"]) > 50 else row["content"],
                    "type": row["type"],
                    "properties": {
                        "content": row["content"],
                        "quality_score": float(row["quality_score"]) if row["quality_score"] else 0.5,
                    }
                })

            return results

    async def get_node_neighbors(
        self,
        node_id: str,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Récupère les voisins d'un nœud

        Args:
            node_id: ID du nœud
            depth: Profondeur de recherche

        Returns:
            Graphe avec nœud central et ses voisins
        """
        async with self.db_pool.acquire() as conn:
            # Get relations where node is source or target
            query = """
                SELECT
                    id,
                    source_id,
                    target_id,
                    relation_type
                FROM relations
                WHERE source_id = $1 OR target_id = $1
            """
            relations = await conn.fetch(query, UUID(node_id))

            # Collect neighbor IDs
            neighbor_ids = set()
            for rel in relations:
                if str(rel["source_id"]) != node_id:
                    neighbor_ids.add(str(rel["source_id"]))
                if str(rel["target_id"]) != node_id:
                    neighbor_ids.add(str(rel["target_id"]))

            # Get all nodes (central + neighbors)
            all_nodes = await self.get_graph_nodes()
            filtered_nodes = [
                n for n in all_nodes
                if n["id"] == node_id or n["id"] in neighbor_ids
            ]

            filtered_relations = [
                {
                    "id": str(rel["id"]),
                    "source": str(rel["source_id"]),
                    "target": str(rel["target_id"]),
                    "type": rel["relation_type"] or "RELATES_TO",
                    "weight": 1.0,
                }
                for rel in relations
            ]

            return {
                "nodes": filtered_nodes,
                "relations": filtered_relations,
            }
