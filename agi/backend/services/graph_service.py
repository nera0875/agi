"""
Service de gestion du graphe de connaissances Neo4j
Implémente les opérations sur les concepts, relations et patterns
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, TransientError

from config.settings import get_settings
from services.external_services import ExternalServicesManager

logger = logging.getLogger(__name__)

class GraphService:
    """Service de gestion du graphe de connaissances Neo4j"""
    
    def __init__(self, external_services: ExternalServicesManager):
        self.settings = get_settings()
        self.external_services = external_services
        self.driver: Optional[AsyncDriver] = None
        
    async def initialize(self):
        """Initialise la connexion à Neo4j"""
        try:
            neo4j_uri = f"bolt://{self.settings.neo4j_host}:{self.settings.neo4j_port}"
            
            self.driver = AsyncGraphDatabase.driver(
                neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Vérifier la connexion
            await self.driver.verify_connectivity()
            
            logger.info("GraphService initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de GraphService: {e}")
            raise
    
    async def close(self):
        """Ferme les connexions"""
        if self.driver:
            await self.driver.close()
    
    async def create_concept(
        self,
        user_id: UUID,
        name: str,
        concept_type: str,
        description: str = "",
        importance: float = 0.5
    ) -> Dict[str, Any]:
        """Crée ou met à jour un concept dans le graphe"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.createConcept($name, $type, $user_id, $description, $importance)
                YIELD value as concept
                RETURN concept
                """
                
                result = await session.run(
                    query,
                    name=name,
                    type=concept_type,
                    user_id=str(user_id),
                    description=description,
                    importance=importance
                )
                
                record = await result.single()
                if record:
                    concept = record["concept"]
                    logger.info(f"Concept créé/mis à jour: {name} ({concept_type})")
                    
                    return {
                        "id": concept["id"],
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept.get("description", ""),
                        "importance": concept["importance"],
                        "frequency": concept["frequency"],
                        "created_at": concept["created_at"],
                        "updated_at": concept.get("updated_at")
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de concept: {e}")
            raise
    
    async def create_concept_relation(
        self,
        concept1_id: str,
        concept2_id: str,
        relation_type: str,
        strength: float = 0.5
    ) -> Dict[str, Any]:
        """Crée une relation entre deux concepts"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.createConceptRelation($concept1_id, $concept2_id, $relation_type, $strength)
                YIELD value as relation
                RETURN relation
                """
                
                result = await session.run(
                    query,
                    concept1_id=concept1_id,
                    concept2_id=concept2_id,
                    relation_type=relation_type,
                    strength=strength
                )
                
                record = await result.single()
                if record:
                    relation = record["relation"]
                    logger.info(f"Relation créée: {concept1_id} -{relation_type}-> {concept2_id}")
                    
                    return {
                        "type": relation["type"],
                        "strength": relation["strength"],
                        "frequency": relation["frequency"],
                        "created_at": relation["created_at"],
                        "updated_at": relation.get("updated_at")
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de relation: {e}")
            raise
    
    async def find_similar_concepts(
        self,
        user_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Trouve des concepts similaires par recherche textuelle"""
        
        try:
            async with self.driver.session() as session:
                cypher_query = """
                CALL agi.findSimilarConcepts($user_id, $query, $limit)
                YIELD value as concept
                RETURN concept
                ORDER BY concept.importance DESC, concept.frequency DESC
                """
                
                result = await session.run(
                    cypher_query,
                    user_id=str(user_id),
                    query=query,
                    limit=limit
                )
                
                concepts = []
                async for record in result:
                    concept = record["concept"]
                    concepts.append({
                        "id": concept["id"],
                        "name": concept["name"],
                        "type": concept["type"],
                        "description": concept.get("description", ""),
                        "importance": concept["importance"],
                        "frequency": concept["frequency"]
                    })
                
                logger.info(f"Trouvé {len(concepts)} concepts similaires pour: {query}")
                return concepts
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de concepts: {e}")
            raise
    
    async def get_concept_neighbors(
        self,
        concept_id: str,
        max_depth: int = 2,
        min_strength: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Récupère les concepts voisins avec leurs relations"""
        
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (c:Concept {id: $concept_id})-[r*1..$max_depth]-(neighbor:Concept)
                WHERE ALL(rel in r WHERE rel.strength >= $min_strength)
                WITH neighbor, r, 
                     reduce(strength = 1.0, rel in r | strength * rel.strength) as path_strength
                RETURN DISTINCT neighbor, path_strength, length(r) as distance
                ORDER BY path_strength DESC, distance ASC
                LIMIT 20
                """
                
                result = await session.run(
                    query,
                    concept_id=concept_id,
                    max_depth=max_depth,
                    min_strength=min_strength
                )
                
                neighbors = []
                async for record in result:
                    neighbor = record["neighbor"]
                    neighbors.append({
                        "concept": {
                            "id": neighbor["id"],
                            "name": neighbor["name"],
                            "type": neighbor["type"],
                            "importance": neighbor["importance"]
                        },
                        "path_strength": record["path_strength"],
                        "distance": record["distance"]
                    })
                
                return neighbors
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des voisins: {e}")
            raise
    
    async def explore_knowledge_graph(
        self,
        user_id: UUID,
        start_concept: str,
        max_depth: int = 3,
        min_score: float = 0.2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Explore le graphe de connaissances à partir d'un concept"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.exploreKnowledgeGraph($start_concept, $user_id, $max_depth, $min_score, $limit)
                YIELD value as result
                RETURN result.path as path, result.depth as depth, result.path_score as score
                """
                
                result = await session.run(
                    query,
                    start_concept=start_concept,
                    user_id=str(user_id),
                    max_depth=max_depth,
                    min_score=min_score,
                    limit=limit
                )
                
                paths = []
                async for record in result:
                    path_data = record["path"]
                    
                    # Extraire les nœuds et relations du chemin
                    nodes = []
                    relationships = []
                    
                    for i, node in enumerate(path_data.nodes):
                        nodes.append({
                            "id": node["id"],
                            "name": node["name"],
                            "type": node["type"],
                            "importance": node.get("importance", 0.5)
                        })
                    
                    for rel in path_data.relationships:
                        relationships.append({
                            "type": rel.type,
                            "strength": rel.get("strength", 0.5)
                        })
                    
                    paths.append({
                        "nodes": nodes,
                        "relationships": relationships,
                        "depth": record["depth"],
                        "score": record["score"]
                    })
                
                logger.info(f"Exploré {len(paths)} chemins depuis {start_concept}")
                return paths
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exploration du graphe: {e}")
            raise
    
    async def detect_temporal_patterns(
        self,
        user_id: UUID,
        max_gap_seconds: int = 3600,  # 1 heure
        min_frequency: int = 3
    ) -> List[Dict[str, Any]]:
        """Détecte des patterns temporels dans les concepts"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.detectTemporalPatterns($user_id, $max_gap_seconds, $min_frequency)
                YIELD value as result
                RETURN result.p as pattern, result.c1 as concept1, result.c2 as concept2
                """
                
                result = await session.run(
                    query,
                    user_id=str(user_id),
                    max_gap_seconds=max_gap_seconds,
                    min_frequency=min_frequency
                )
                
                patterns = []
                async for record in result:
                    pattern = record["pattern"]
                    concept1 = record["concept1"]
                    concept2 = record["concept2"]
                    
                    patterns.append({
                        "pattern": {
                            "type": pattern["type"],
                            "description": pattern["description"],
                            "frequency": pattern["frequency"],
                            "confidence": pattern["confidence"],
                            "avg_time_gap": pattern.get("avg_time_gap")
                        },
                        "concepts": [
                            {
                                "id": concept1["id"],
                                "name": concept1["name"],
                                "type": concept1["type"]
                            },
                            {
                                "id": concept2["id"],
                                "name": concept2["name"],
                                "type": concept2["type"]
                            }
                        ]
                    })
                
                logger.info(f"Détecté {len(patterns)} patterns temporels")
                return patterns
                
        except Exception as e:
            logger.error(f"Erreur lors de la détection de patterns: {e}")
            raise
    
    async def calculate_concept_importance(self, user_id: UUID) -> Dict[str, float]:
        """Recalcule l'importance de tous les concepts d'un utilisateur"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.calculateConceptImportance($user_id)
                YIELD value as result
                RETURN result
                """
                
                result = await session.run(query, user_id=str(user_id))
                
                importance_scores = {}
                async for record in result:
                    result_data = record["result"]
                    importance_scores[result_data[0]] = result_data[1]  # name, importance
                
                logger.info(f"Recalculé l'importance pour {len(importance_scores)} concepts")
                return importance_scores
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul d'importance: {e}")
            raise
    
    async def cleanup_unused_concepts(
        self,
        user_id: UUID,
        min_frequency: int = 2,
        min_importance: float = 0.2,
        min_age_days: int = 30
    ) -> int:
        """Nettoie les concepts peu utilisés"""
        
        try:
            async with self.driver.session() as session:
                query = """
                CALL agi.cleanupUnusedConcepts($user_id, $min_frequency, $min_importance, $min_age_days)
                YIELD value as result
                RETURN result.deleted_count as deleted_count
                """
                
                result = await session.run(
                    query,
                    user_id=str(user_id),
                    min_frequency=min_frequency,
                    min_importance=min_importance,
                    min_age_days=min_age_days
                )
                
                record = await result.single()
                deleted_count = record["deleted_count"] if record else 0
                
                logger.info(f"Supprimé {deleted_count} concepts inutilisés")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            raise
    
    async def get_graph_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Récupère les statistiques du graphe pour un utilisateur"""
        
        try:
            async with self.driver.session() as session:
                query = """
                MATCH (c:Concept {user_id: $user_id})
                OPTIONAL MATCH (c)-[r]-(other:Concept {user_id: $user_id})
                RETURN 
                    count(DISTINCT c) as concept_count,
                    count(DISTINCT r) as relation_count,
                    avg(c.importance) as avg_importance,
                    collect(DISTINCT c.type) as concept_types
                """
                
                result = await session.run(query, user_id=str(user_id))
                record = await result.single()
                
                if record:
                    return {
                        "concept_count": record["concept_count"],
                        "relation_count": record["relation_count"],
                        "avg_importance": float(record["avg_importance"]) if record["avg_importance"] else 0.0,
                        "concept_types": record["concept_types"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                return {
                    "concept_count": 0,
                    "relation_count": 0,
                    "avg_importance": 0.0,
                    "concept_types": [],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            raise
    
    async def link_memory_to_concepts(
        self,
        memory_id: UUID,
        user_id: UUID,
        concepts: List[Dict[str, Any]]
    ) -> int:
        """Lie une mémoire à des concepts dans le graphe"""
        
        try:
            async with self.driver.session() as session:
                # Créer le nœud mémoire s'il n'existe pas
                memory_query = """
                MERGE (m:Memory {id: $memory_id, user_id: $user_id})
                SET m.created_at = CASE WHEN m.created_at IS NULL THEN datetime() ELSE m.created_at END
                """
                
                await session.run(memory_query, memory_id=str(memory_id), user_id=str(user_id))
                
                # Lier aux concepts
                links_created = 0
                for concept in concepts:
                    link_query = """
                    MATCH (m:Memory {id: $memory_id}), (c:Concept {id: $concept_id})
                    MERGE (m)-[r:CONTAINS]->(c)
                    SET r.relevance = $relevance,
                        r.created_at = datetime()
                    """
                    
                    await session.run(
                        link_query,
                        memory_id=str(memory_id),
                        concept_id=concept["id"],
                        relevance=concept.get("relevance", 0.5)
                    )
                    links_created += 1
                
                logger.info(f"Créé {links_created} liens mémoire-concept")
                return links_created
                
        except Exception as e:
            logger.error(f"Erreur lors de la liaison mémoire-concepts: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du service de graphe"""
        
        try:
            if not self.driver:
                return {"status": "unhealthy", "error": "Driver Neo4j non initialisé"}
            
            async with self.driver.session() as session:
                # Test de connexion simple
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                
                if record and record["test"] == 1:
                    # Compter les nœuds
                    count_result = await session.run("MATCH (n) RETURN count(n) as node_count")
                    count_record = await count_result.single()
                    
                    return {
                        "status": "healthy",
                        "node_count": count_record["node_count"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"status": "unhealthy", "error": "Test de connexion échoué"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}