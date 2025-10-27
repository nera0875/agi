"""
Service de gestion des mémoires L1/L2/L3 avec intégration PostgreSQL + pgvector
Implémente la hiérarchie de mémoire selon la documentation technique
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4

import asyncpg
import numpy as np
from pgvector.asyncpg import register_vector

from config.settings import get_settings
from services.external_services import ExternalServicesManager

logger = logging.getLogger(__name__)

class MemoryLevel:
    L1 = "L1"  # Mémoire immédiate (minutes/heures)
    L2 = "L2"  # Mémoire de travail (jours/semaines) 
    L3 = "L3"  # Mémoire à long terme (mois/années)

class MemoryService:
    """Service de gestion des mémoires avec hiérarchie L1/L2/L3"""
    
    def __init__(self, external_services: ExternalServicesManager):
        self.settings = get_settings()
        self.external_services = external_services
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialise la connexion à PostgreSQL"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.settings.postgres_host,
                port=self.settings.postgres_port,
                user=self.settings.postgres_user,
                password=self.settings.postgres_password,
                database=self.settings.postgres_db,
                min_size=5,
                max_size=20
            )
            
            # Enregistrer le type vector pour pgvector
            async with self.pool.acquire() as conn:
                await register_vector(conn)
                
            logger.info("MemoryService initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de MemoryService: {e}")
            raise
    
    async def close(self):
        """Ferme les connexions"""
        if self.pool:
            await self.pool.close()
    
    async def create_memory(
        self,
        user_id: UUID,
        content: str,
        level: str = MemoryLevel.L1,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Crée une nouvelle mémoire avec embedding"""
        
        try:
            # Générer l'embedding du contenu
            embedding = await self.external_services.voyage_ai.get_embedding(content)
            
            # Calculer l'importance automatiquement si non fournie
            if importance == 0.5:  # Valeur par défaut
                importance = await self._calculate_importance(content, level)
            
            # Déterminer la date d'expiration selon le niveau
            expires_at = self._calculate_expiration(level)
            
            async with self.pool.acquire() as conn:
                memory_id = uuid4()
                
                query = """
                INSERT INTO memories (
                    id, user_id, content, level, importance, 
                    embedding, metadata, conversation_id, expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, created_at
                """
                
                result = await conn.fetchrow(
                    query,
                    memory_id, user_id, content, level, importance,
                    embedding, metadata or {}, conversation_id, expires_at
                )
                
                logger.info(f"Mémoire {level} créée: {memory_id}")
                
                return {
                    "id": result["id"],
                    "user_id": user_id,
                    "content": content,
                    "level": level,
                    "importance": importance,
                    "created_at": result["created_at"],
                    "expires_at": expires_at
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la création de mémoire: {e}")
            raise
    
    async def search_memories(
        self,
        user_id: UUID,
        query: str,
        level: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Recherche sémantique dans les mémoires"""
        
        try:
            # Générer l'embedding de la requête
            query_embedding = await self.external_services.voyage_ai.get_embedding(query)
            
            async with self.pool.acquire() as conn:
                # Construire la requête SQL avec filtres optionnels
                where_conditions = ["user_id = $1", "expires_at > NOW()"]
                params = [user_id]
                param_count = 1
                
                if level:
                    param_count += 1
                    where_conditions.append(f"level = ${param_count}")
                    params.append(level)
                
                # Ajouter le seuil de similarité
                param_count += 1
                where_conditions.append(f"1 - (embedding <=> ${param_count}) >= ${param_count + 1}")
                params.extend([query_embedding, similarity_threshold])
                
                sql_query = f"""
                SELECT 
                    id, content, level, importance, created_at, updated_at,
                    metadata, conversation_id,
                    1 - (embedding <=> ${param_count}) as similarity
                FROM memories 
                WHERE {' AND '.join(where_conditions)}
                ORDER BY similarity DESC, importance DESC, created_at DESC
                LIMIT ${param_count + 2}
                """
                
                params.append(limit)
                
                results = await conn.fetch(sql_query, *params)
                
                memories = []
                for row in results:
                    memories.append({
                        "id": row["id"],
                        "content": row["content"],
                        "level": row["level"],
                        "importance": row["importance"],
                        "similarity": float(row["similarity"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "metadata": row["metadata"],
                        "conversation_id": row["conversation_id"]
                    })
                
                logger.info(f"Trouvé {len(memories)} mémoires pour la requête: {query[:50]}...")
                return memories
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de mémoires: {e}")
            raise
    
    async def get_memory_by_id(self, user_id: UUID, memory_id: UUID) -> Optional[Dict[str, Any]]:
        """Récupère une mémoire par son ID"""
        
        try:
            async with self.pool.acquire() as conn:
                query = """
                SELECT id, content, level, importance, created_at, updated_at,
                       metadata, conversation_id, expires_at
                FROM memories 
                WHERE id = $1 AND user_id = $2 AND expires_at > NOW()
                """
                
                result = await conn.fetchrow(query, memory_id, user_id)
                
                if result:
                    return {
                        "id": result["id"],
                        "content": result["content"],
                        "level": result["level"],
                        "importance": result["importance"],
                        "created_at": result["created_at"],
                        "updated_at": result["updated_at"],
                        "metadata": result["metadata"],
                        "conversation_id": result["conversation_id"],
                        "expires_at": result["expires_at"]
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de mémoire {memory_id}: {e}")
            raise
    
    async def update_memory_importance(
        self, 
        user_id: UUID, 
        memory_id: UUID, 
        new_importance: float
    ) -> bool:
        """Met à jour l'importance d'une mémoire"""
        
        try:
            async with self.pool.acquire() as conn:
                query = """
                UPDATE memories 
                SET importance = $1, updated_at = NOW()
                WHERE id = $2 AND user_id = $3
                """
                
                result = await conn.execute(query, new_importance, memory_id, user_id)
                
                if result == "UPDATE 1":
                    logger.info(f"Importance mise à jour pour mémoire {memory_id}: {new_importance}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'importance: {e}")
            raise
    
    async def consolidate_memories(self, user_id: UUID) -> Dict[str, int]:
        """Consolide les mémoires L1 -> L2 -> L3 selon l'importance"""
        
        try:
            stats = {"l1_to_l2": 0, "l2_to_l3": 0, "deleted": 0}
            
            async with self.pool.acquire() as conn:
                # Consolider L1 -> L2 (mémoires importantes de plus de 1 jour)
                l1_to_l2_query = """
                UPDATE memories 
                SET level = 'L2', updated_at = NOW(),
                    expires_at = NOW() + INTERVAL '30 days'
                WHERE user_id = $1 
                  AND level = 'L1' 
                  AND importance >= 0.7
                  AND created_at < NOW() - INTERVAL '1 day'
                """
                
                result = await conn.execute(l1_to_l2_query, user_id)
                stats["l1_to_l2"] = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
                # Consolider L2 -> L3 (mémoires très importantes de plus de 7 jours)
                l2_to_l3_query = """
                UPDATE memories 
                SET level = 'L3', updated_at = NOW(),
                    expires_at = NOW() + INTERVAL '1 year'
                WHERE user_id = $1 
                  AND level = 'L2' 
                  AND importance >= 0.8
                  AND created_at < NOW() - INTERVAL '7 days'
                """
                
                result = await conn.execute(l2_to_l3_query, user_id)
                stats["l2_to_l3"] = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
                # Supprimer les mémoires expirées de faible importance
                delete_query = """
                DELETE FROM memories 
                WHERE user_id = $1 
                  AND (expires_at < NOW() OR (importance < 0.3 AND level = 'L1'))
                """
                
                result = await conn.execute(delete_query, user_id)
                stats["deleted"] = int(result.split()[-1]) if result.split()[-1].isdigit() else 0
                
                logger.info(f"Consolidation terminée pour {user_id}: {stats}")
                return stats
                
        except Exception as e:
            logger.error(f"Erreur lors de la consolidation: {e}")
            raise
    
    async def get_memory_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Récupère les statistiques des mémoires d'un utilisateur"""
        
        try:
            async with self.pool.acquire() as conn:
                query = """
                SELECT 
                    level,
                    COUNT(*) as count,
                    AVG(importance) as avg_importance,
                    MAX(created_at) as last_created
                FROM memories 
                WHERE user_id = $1 AND expires_at > NOW()
                GROUP BY level
                """
                
                results = await conn.fetch(query, user_id)
                
                stats = {
                    "total": 0,
                    "by_level": {},
                    "avg_importance": 0.0
                }
                
                total_memories = 0
                total_importance = 0.0
                
                for row in results:
                    level_stats = {
                        "count": row["count"],
                        "avg_importance": float(row["avg_importance"]),
                        "last_created": row["last_created"]
                    }
                    
                    stats["by_level"][row["level"]] = level_stats
                    total_memories += row["count"]
                    total_importance += row["count"] * float(row["avg_importance"])
                
                stats["total"] = total_memories
                stats["avg_importance"] = total_importance / total_memories if total_memories > 0 else 0.0
                
                return stats
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            raise
    
    def _calculate_expiration(self, level: str) -> datetime:
        """Calcule la date d'expiration selon le niveau de mémoire"""
        now = datetime.utcnow()
        
        if level == MemoryLevel.L1:
            return now + timedelta(hours=24)  # 1 jour
        elif level == MemoryLevel.L2:
            return now + timedelta(days=30)   # 1 mois
        elif level == MemoryLevel.L3:
            return now + timedelta(days=365)  # 1 an
        else:
            return now + timedelta(hours=24)  # Par défaut L1
    
    async def _calculate_importance(self, content: str, level: str) -> float:
        """Calcule l'importance automatiquement basée sur le contenu et le niveau"""
        
        # Facteurs d'importance de base selon le niveau
        base_importance = {
            MemoryLevel.L1: 0.3,
            MemoryLevel.L2: 0.6,
            MemoryLevel.L3: 0.8
        }
        
        importance = base_importance.get(level, 0.5)
        
        # Ajuster selon la longueur du contenu
        if len(content) > 500:
            importance += 0.1
        elif len(content) < 50:
            importance -= 0.1
        
        # Mots-clés importants
        important_keywords = [
            "important", "urgent", "critique", "essentiel", "priorité",
            "décision", "objectif", "projet", "deadline", "problème"
        ]
        
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in important_keywords if keyword in content_lower)
        importance += keyword_count * 0.05
        
        # Limiter entre 0.1 et 1.0
        return max(0.1, min(1.0, importance))
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du service de mémoire"""
        
        try:
            if not self.pool:
                return {"status": "unhealthy", "error": "Pool de connexions non initialisé"}
            
            async with self.pool.acquire() as conn:
                # Test de connexion simple
                result = await conn.fetchval("SELECT 1")
                
                if result == 1:
                    # Compter les mémoires actives
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM memories WHERE expires_at > NOW()"
                    )
                    
                    return {
                        "status": "healthy",
                        "active_memories": count,
                        "pool_size": self.pool.get_size(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {"status": "unhealthy", "error": "Test de connexion échoué"}
                    
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}