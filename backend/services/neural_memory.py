"""
Neural Memory Service - Brain-like memory system

Système de mémoire fonctionnant exactement comme un cerveau humain:
- Spreading activation (activation locale avec décroissance)
- LTP/LTD (renforcement/affaiblissement automatique des synapses)
- Synaptic pruning (suppression connexions faibles)
- Économie de tokens = économie de glucose

Architecture:
- Neo4j: Graph de concepts avec synapses
- Voyage AI: Embeddings sémantiques (similarité)
- Cohere: Reranking (attention sélective)
- Redis: Cache (prédiction neuronale)
- PostgreSQL: Storage persistant
"""

import logging
import asyncio
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta

import numpy as np
import asyncpg
from neo4j import AsyncGraphDatabase
from langchain_voyageai import VoyageAIEmbeddings
from langchain_cohere import CohereRerank
from langchain_core.documents import Document
from redis import asyncio as aioredis

from config import settings
from backend.services.neurotransmitter_system import NeurotransmitterSystem

logger = logging.getLogger(__name__)


class NeuralMemory:
    """
    Système de mémoire neural comme cerveau humain

    Principes:
    1. Spreading activation - Activation locale avec décroissance
    2. Hebbian learning - "Neurons that fire together, wire together"
    3. Synaptic pruning - Suppression connexions inutiles
    4. Predictive coding - Cache = prédiction neuronale
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

        # Neo4j driver
        self.neo4j = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        logger.info(f"Neo4j driver initialized: {neo4j_uri}")

        # Voyage AI embeddings
        self.embeddings = VoyageAIEmbeddings(
            voyage_api_key=settings.voyage_api_key,
            model=settings.voyage_model,
            batch_size=128
        )
        logger.info("Voyage AI embeddings initialized (voyage-3, 1024 dims)")

        # Cohere reranker
        from pydantic import SecretStr
        self.reranker = CohereRerank(
            cohere_api_key=SecretStr(settings.cohere_api_key),
            top_n=5,  # Working memory limit (7±2)
            model="rerank-english-v3.0"
        )
        logger.info("Cohere reranker initialized")

        # 🧠 NEUROTRANSMITTER SYSTEM - Dynamic resource allocation
        self.neurotransmitters = NeurotransmitterSystem(db_pool)
        logger.info("🧠 Neurotransmitter system initialized (glutamate, dopamine, GABA, serotonin)")

        # Tracking for feedback loop and idle detection
        self.last_query_time = None
        self.activation_count = 0
        self.idle_threshold = 3600  # 1 hour idle = trigger consolidation
        self.last_consolidation = None

        logger.info("🧠 NeuralMemory initialized - Brain-like system ready")

    async def close(self):
        """Close connections"""
        await self.neo4j.close()
        logger.info("Neo4j driver closed")

    # ========================================================================
    # CORE - NEURAL ACTIVATION (Query principale)
    # ========================================================================

    async def activate(
        self,
        query: str,
        query_type: str = 'interactive',  # 'urgent', 'interactive', 'background'
        context: Dict = None,
        max_depth: int = None,  # Override neurotransmitter modulation
        activation_threshold: float = None,
        top_k: int = None
    ) -> List[Document]:
        """
        Activation neurale comme cerveau humain avec neurotransmetteurs

        Process:
        0. 🧠 NEUROTRANSMITTER MODULATION - Adapt parameters to context
        1. Cache check (prédiction neuronale - comme "bonjour" en français)
        2. Embedding sémantique (Voyage AI)
        3. Spreading activation (Neo4j avec décroissance)
        4. Renforcement LTP automatique (boosted by dopamine!)
        5. Reranking (Cohere - attention sélective)
        6. Cache pour prochaine fois
        7. 🔄 FEEDBACK LOOP - Update neurotransmitters based on success

        Args:
            query: Requête utilisateur
            query_type: Type de query ('urgent', 'interactive', 'background')
                - urgent: GLUTAMATE high → depth 3, threshold 0.1, ~800 tokens
                - interactive: Balanced → depth 2, threshold 0.2, ~400 tokens
                - background: GABA high → depth 1, threshold 0.4, ~150 tokens
            context: Additional context for neurotransmitter modulation
            max_depth: Manual override (if None, uses neurotransmitters)
            activation_threshold: Manual override
            top_k: Manual override

        Returns:
            Liste de Documents activés et pertinents
        """
        import time
        start_time = time.time()

        # 0. 🧠 IDLE DETECTION - Natural consolidation (replaces cron!)
        current_time = time.time()
        if self.last_query_time:
            idle_duration = current_time - self.last_query_time

            # If idle > 1 hour → trigger consolidation (like brain during sleep)
            if idle_duration > self.idle_threshold:
                logger.info(f"💤 System idle for {idle_duration/60:.1f}min → triggering consolidation...")
                await self._natural_consolidation()
                self.last_consolidation = current_time

        self.last_query_time = current_time

        # 1. 🧠 NEUROTRANSMITTER MODULATION - Dynamic parameters
        params = await self.neurotransmitters.modulate(
            query_type=query_type,
            context=context or {}
        )

        # Use neurotransmitter params unless manually overridden
        final_max_depth = max_depth if max_depth is not None else params['max_depth']
        final_threshold = activation_threshold if activation_threshold is not None else params['activation_threshold']
        final_top_k = top_k if top_k is not None else params['top_k']
        ltp_strength = params['ltp_strength']

        logger.info(
            f"🧠 Neurotransmitters: {query_type} → "
            f"depth={final_max_depth}, threshold={final_threshold:.2f}, "
            f"top_k={final_top_k}, ltp={ltp_strength:.2f} "
            f"(Glu={params['glutamate']:.2f}, DA={params['dopamine']:.2f}, GABA={params['gaba']:.2f})"
        )

        # 1. PRÉDICTION (Cache = prédiction neuronale)
        cache_key = f"neural:activation:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await self.redis.get(cache_key)

        if cached:
            logger.info(f"🎯 Cache HIT (prédiction correcte) - {query[:30]}...")

            # Feedback: cache hit = fast success!
            response_time = int((time.time() - start_time) * 1000)
            await self.neurotransmitters.feedback(
                success=True,
                response_time=response_time,
                tokens_used=100  # Cache = very cheap
            )

            docs = json.loads(cached)
            return [
                Document(page_content=d["content"], metadata=d["metadata"])
                for d in docs
            ]

        # 2. EMBEDDING SÉMANTIQUE (Voyage AI)
        query_embedding = await self.embeddings.aembed_query(query)

        # 3. SPREADING ACTIVATION (Neo4j) - WITH ADAPTIVE PARAMETERS!
        activated_concepts = await self._spreading_activation(
            query_embedding=query_embedding,
            max_depth=final_max_depth,
            threshold=final_threshold,
            ltp_strength=ltp_strength  # Dopamine-boosted LTP!
        )

        if not activated_concepts:
            logger.warning(f"No concepts activated for query: {query}")

            # Feedback: failure
            response_time = int((time.time() - start_time) * 1000)
            await self.neurotransmitters.feedback(
                success=False,
                response_time=response_time,
                tokens_used=0
            )

            return []

        # 4. RERANKING (Cohere - attention sélective)
        documents = [
            Document(
                page_content=concept["content"],
                metadata={
                    "id": concept["id"],
                    "activation": concept["activation"],
                    "tags": concept.get("tags", [])
                }
            )
            for concept in activated_concepts
        ]

        reranked = await self._rerank_documents(query, documents, final_top_k)

        # 5. CACHE (Apprentissage pour prochaine fois)
        cache_data = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in reranked
        ]
        await self.redis.setex(cache_key, 3600, json.dumps(cache_data))

        # Estimate tokens used
        tokens_estimate = sum(len(doc.page_content) // 4 for doc in reranked)

        logger.info(
            f"✅ Activated {len(reranked)} concepts (from {len(activated_concepts)} explored) "
            f"~{tokens_estimate} tokens"
        )

        # 6. 🔄 FEEDBACK LOOP - Update neurotransmitters
        response_time = int((time.time() - start_time) * 1000)
        await self.neurotransmitters.feedback(
            success=True,
            response_time=response_time,
            tokens_used=tokens_estimate
        )

        # Track activation count for metrics
        self.activation_count += 1

        return reranked

    async def _spreading_activation(
        self,
        query_embedding: List[float],
        max_depth: int = 2,
        threshold: float = 0.2,
        ltp_strength: float = 0.1  # 🧠 Dopamine-boosted LTP!
    ) -> List[Dict[str, Any]]:
        """
        Spreading activation avec décroissance exponentielle

        Comme cerveau humain:
        - Depth 0: activation 1.0
        - Depth 1: activation 0.5
        - Depth 2: activation 0.25
        - Pondéré par force synaptique
        - 🧠 LTP strength adaptatif (dopamine boost!)
        """

        async with self.neo4j.session() as session:
            # Query Cypher - Spreading activation avec neurotransmitters
            result = await session.run(f"""
                // 1. Trouver concepts similaires (activation initiale)
                MATCH (start:Concept)
                WHERE start.embedding IS NOT NULL

                WITH start,
                     gds.similarity.cosine(start.embedding, $query_embedding) as similarity
                WHERE similarity > 0.7

                // 2. Spreading avec décroissance (DEPTH ADAPTATIF!)
                CALL {{
                    WITH start
                    MATCH path = (start)-[:SYNAPSE*0..{max_depth}]->(target:Concept)

                    WITH
                        target,
                        length(path) as depth,
                        relationships(path) as synapses,
                        1.0 / (length(path) + 1) as base_activation,
                        CASE
                            WHEN length(path) = 0 THEN 1.0
                            ELSE reduce(s = 1.0, syn in relationships(path) | s * syn.strength)
                        END as path_strength

                    WITH
                        target,
                        base_activation * path_strength as final_activation,
                        synapses

                    WHERE final_activation > $threshold

                    // 3. LTP - Renforcement ADAPTATIF (dopamine boost!)
                    FOREACH (syn in synapses |
                        SET syn.strength = CASE
                            WHEN syn.strength + $ltp_boost > 1.0 THEN 1.0
                            ELSE syn.strength + $ltp_boost
                        END,
                        syn.use_count = syn.use_count + 1,
                        syn.last_used = datetime()
                    )

                    RETURN target, final_activation
                }}

                RETURN DISTINCT
                    target.id as id,
                    target.content as content,
                    target.tags as tags,
                    final_activation as activation
                ORDER BY final_activation DESC
                LIMIT 20
            """,
                query_embedding=query_embedding,
                threshold=threshold,
                ltp_boost=ltp_strength  # 🧠 Adaptive LTP!
            )

            concepts = []
            async for record in result:
                concepts.append({
                    "id": record["id"],
                    "content": record["content"],
                    "tags": record["tags"] or [],
                    "activation": record["activation"]
                })

            return concepts

    async def _rerank_documents(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5
    ) -> List[Document]:
        """
        Reranking avec Cohere (attention sélective)

        Comme attention humaine: focus sur 5-7 items les plus pertinents
        """

        if len(documents) <= top_k:
            return documents

        # Cohere rerank
        reranked = await asyncio.to_thread(
            self.reranker.compress_documents,
            documents=documents,
            query=query
        )

        return reranked[:top_k]

    # ========================================================================
    # LTP - RENFORCEMENT AUTOMATIQUE
    # ========================================================================

    async def reinforce_path(
        self,
        concept_ids: List[str],
        strength_increase: float = 0.1
    ) -> int:
        """
        Renforce synapses entre concepts co-activés (LTP)

        Hebbian learning: "Neurons that fire together, wire together"
        """

        if len(concept_ids) < 2:
            return 0

        async with self.neo4j.session() as session:
            result = await session.run("""
                UNWIND $pairs as pair
                MATCH (a:Concept {id: pair[0]})-[syn:SYNAPSE]->(b:Concept {id: pair[1]})

                SET syn.strength = CASE
                    WHEN syn.strength + $increase > 1.0 THEN 1.0
                    ELSE syn.strength + $increase
                END,
                syn.use_count = syn.use_count + 1,
                syn.last_used = datetime()

                RETURN count(syn) as reinforced
            """,
                pairs=[[concept_ids[i], concept_ids[i+1]] for i in range(len(concept_ids)-1)],
                increase=strength_increase
            )

            record = await result.single()
            count = record["reinforced"] if record else 0

            logger.info(f"💪 Reinforced {count} synapses (LTP)")
            return count

    # ========================================================================
    # LTD - AFFAIBLISSEMENT AUTOMATIQUE (Cron)
    # ========================================================================

    async def decay_synapses(
        self,
        days_threshold: int = 7,
        decay_factor: float = 0.95
    ) -> int:
        """
        Affaiblit synapses non utilisées (LTD)

        Exécuté par cron nocturne (3h du matin)
        Comme cerveau pendant sommeil
        """

        async with self.neo4j.session() as session:
            cutoff = datetime.now() - timedelta(days=days_threshold)

            result = await session.run("""
                MATCH ()-[syn:SYNAPSE]->()
                WHERE syn.last_used < datetime($cutoff)

                SET syn.strength = syn.strength * $decay_factor

                RETURN count(syn) as decayed
            """, cutoff=cutoff.isoformat(), decay_factor=decay_factor)

            record = await result.single()
            count = record["decayed"] if record else 0

            logger.info(f"📉 Decayed {count} synapses (LTD)")
            return count

    # ========================================================================
    # PRUNING - SUPPRESSION CONNEXIONS FAIBLES (Cron)
    # ========================================================================

    async def prune_weak_synapses(
        self,
        strength_threshold: float = 0.1
    ) -> int:
        """
        Supprime synapses trop faibles (Synaptic Pruning)

        Exécuté par cron nocturne
        Comme cerveau: 60% synapses supprimées entre enfance et adulte
        """

        async with self.neo4j.session() as session:
            result = await session.run("""
                MATCH ()-[syn:SYNAPSE]->()
                WHERE syn.strength < $threshold
                DELETE syn
                RETURN count(syn) as pruned
            """, threshold=strength_threshold)

            record = await result.single()
            count = record["pruned"] if record else 0

            logger.info(f"✂️  Pruned {count} weak synapses")
            return count

    # ========================================================================
    # CONSOLIDATION - FUSION CONCEPTS SIMILAIRES (Cron)
    # ========================================================================

    async def consolidate_concepts(
        self,
        similarity_threshold: float = 0.95,
        min_use_count: int = 10
    ) -> int:
        """
        Fusionne concepts très similaires co-activés fréquemment

        Exécuté par cron nocturne
        Comme consolidation mémoire pendant REM sleep
        """

        async with self.neo4j.session() as session:
            result = await session.run("""
                MATCH (a:Concept)-[r1:SYNAPSE]->(c:Concept)<-[r2:SYNAPSE]-(b:Concept)
                WHERE a <> b
                  AND id(a) < id(b)
                  AND r1.use_count > $min_use
                  AND r2.use_count > $min_use
                  AND a.embedding IS NOT NULL
                  AND b.embedding IS NOT NULL
                  AND gds.similarity.cosine(a.embedding, b.embedding) > $threshold

                MERGE (a)-[r:CONSOLIDATED_WITH]-(b)
                SET r.strength = 1.0,
                    r.created_at = datetime()

                RETURN count(r) as consolidated
            """, threshold=similarity_threshold, min_use=min_use_count)

            record = await result.single()
            count = record["consolidated"] if record else 0

            logger.info(f"🔗 Consolidated {count} concept pairs")
            return count

    # ========================================================================
    # METRICS - SANTÉ DU SYSTÈME
    # ========================================================================

    async def get_neural_metrics(self) -> Dict[str, Any]:
        """
        Métriques de santé du système neural

        Indicateurs:
        - Graph density (doit diminuer avec pruning)
        - Avg synapse strength (doit augmenter avec usage)
        - Top concepts (les plus activés)
        - 🧠 Neurotransmitter levels (glutamate, dopamine, GABA, serotonin)
        """

        async with self.neo4j.session() as session:
            # Graph density
            density_result = await session.run("""
                MATCH (c:Concept)
                WITH count(c) as total_nodes
                MATCH ()-[syn:SYNAPSE]->()
                WITH total_nodes, count(syn) as total_synapses
                RETURN
                    total_nodes,
                    total_synapses,
                    toFloat(total_synapses) / (total_nodes * total_nodes) as density
            """)
            density_record = await density_result.single()

            # Synapse stats
            synapse_result = await session.run("""
                MATCH ()-[syn:SYNAPSE]->()
                RETURN
                    avg(syn.strength) as avg_strength,
                    avg(syn.use_count) as avg_use_count,
                    count(syn) as total_synapses
            """)
            synapse_record = await synapse_result.single()

            # Top concepts
            top_result = await session.run("""
                MATCH (c:Concept)
                RETURN c.content, c.access_count, c.tags
                ORDER BY c.access_count DESC
                LIMIT 10
            """)
            top_concepts = [
                {
                    "content": record["c.content"][:50],
                    "access_count": record["c.access_count"],
                    "tags": record["c.tags"]
                }
                async for record in top_result
            ]

        # 🧠 Neurotransmitter metrics
        neurotransmitter_metrics = await self.neurotransmitters.get_metrics()

        return {
            "graph": {
                "total_nodes": density_record["total_nodes"],
                "total_synapses": density_record["total_synapses"],
                "density": float(density_record["density"])
            },
            "synapses": {
                "avg_strength": float(synapse_record["avg_strength"]),
                "avg_use_count": float(synapse_record["avg_use_count"]),
                "total": synapse_record["total_synapses"]
            },
            "top_concepts": top_concepts,
            "neurotransmitters": neurotransmitter_metrics,
            "activation_count": self.activation_count
        }

    # ========================================================================
    # NATURAL CONSOLIDATION - Trigger-based (replaces cron!)
    # ========================================================================

    async def _natural_consolidation(self):
        """
        Consolidation naturelle déclenchée par idle detection

        Comme cerveau pendant sommeil:
        - LTD: Affaiblit synapses non utilisées
        - Pruning: Supprime synapses trop faibles
        - Consolidation: Fusionne concepts similaires

        Déclenché quand système idle > 1h (pas de cron externe!)
        """
        logger.info("💤 Starting natural consolidation (brain sleep mode)...")

        # 1. LTD - Decay unused synapses
        decayed = await self.decay_synapses(days_threshold=7, decay_factor=0.95)

        # 2. Pruning - Remove weak synapses
        pruned = await self.prune_weak_synapses(strength_threshold=0.1)

        # 3. Consolidation - Merge similar concepts
        consolidated = await self.consolidate_concepts(
            similarity_threshold=0.95,
            min_use_count=10
        )

        logger.info(
            f"💤 Consolidation complete: "
            f"{decayed} decayed, {pruned} pruned, {consolidated} consolidated"
        )
