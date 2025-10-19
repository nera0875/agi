#!/usr/bin/env python3
"""
Migration PostgreSQL → Neo4j

Migre les données existantes vers le système neural:
1. memory_store → Concepts (neurones)
2. relations → Synapses (connexions)
3. Détection automatique relations par similarité embeddings

Comme transformer fichiers → cerveau neural
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from neo4j import AsyncGraphDatabase
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class Neo4jMigrator:
    """Migrateur PostgreSQL → Neo4j"""

    def __init__(
        self,
        pg_pool: asyncpg.Pool,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "Voiture789"
    ):
        self.pg = pg_pool
        self.neo4j = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

    async def close(self):
        await self.neo4j.close()

    async def migrate_concepts(self) -> int:
        """
        Migre memory_store → Concepts Neo4j

        Chaque mémoire devient un neurone (Concept)
        """
        logger.info("📦 Migrating memory_store → Neo4j Concepts...")

        # Récupérer toutes les mémoires
        memories = await self.pg.fetch("""
            SELECT
                id,
                content,
                embedding,
                metadata,
                source_type,
                quality_score,
                access_count,
                created_at
            FROM memory_store
            ORDER BY quality_score DESC, access_count DESC
        """)

        logger.info(f"Found {len(memories)} memories to migrate")

        # Créer concepts dans Neo4j
        async with self.neo4j.session() as session:
            for i, mem in enumerate(memories, 1):
                # Parse embedding (peut être JSON string ou déjà array)
                embedding = mem['embedding']
                if isinstance(embedding, str):
                    import json
                    embedding = json.loads(embedding)

                # Parse metadata (peut être JSON string)
                metadata = mem['metadata'] or {}
                if isinstance(metadata, str):
                    import json
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                tags = metadata.get('tags', []) if isinstance(metadata, dict) else []

                # Créer concept
                await session.run("""
                    CREATE (c:Concept {
                        id: $id,
                        content: $content,
                        embedding: $embedding,
                        tags: $tags,
                        source_type: $source_type,
                        quality_score: $quality_score,
                        access_count: $access_count,
                        last_accessed: datetime($created_at),
                        created_at: datetime($created_at)
                    })
                """,
                    id=str(mem['id']),
                    content=mem['content'],
                    embedding=embedding,
                    tags=tags,
                    source_type=mem['source_type'],
                    quality_score=float(mem['quality_score']) if mem['quality_score'] else 0.5,
                    access_count=mem['access_count'] or 0,
                    created_at=mem['created_at'].isoformat()
                )

                if i % 10 == 0:
                    logger.info(f"  Migrated {i}/{len(memories)} concepts...")

        logger.info(f"✅ Migrated {len(memories)} concepts")
        return len(memories)

    async def migrate_relations(self) -> int:
        """
        Migre relations PostgreSQL → Synapses Neo4j
        """
        logger.info("🔗 Migrating relations → Neo4j Synapses...")

        # Récupérer relations existantes
        relations = await self.pg.fetch("""
            SELECT
                source_id,
                target_id,
                relation_type,
                created_at
            FROM relations
        """)

        logger.info(f"Found {len(relations)} existing relations")

        if not relations:
            logger.info("No relations to migrate, skipping...")
            return 0

        # Créer synapses dans Neo4j
        async with self.neo4j.session() as session:
            for i, rel in enumerate(relations, 1):
                await session.run("""
                    MATCH (a:Concept {id: $source_id})
                    MATCH (b:Concept {id: $target_id})
                    CREATE (a)-[:SYNAPSE {
                        strength: 0.5,
                        use_count: 0,
                        relation_type: $relation_type,
                        last_used: datetime($created_at),
                        created_at: datetime($created_at)
                    }]->(b)
                """,
                    source_id=str(rel['source_id']),
                    target_id=str(rel['target_id']),
                    relation_type=rel['relation_type'],
                    created_at=rel['created_at'].isoformat()
                )

                if i % 10 == 0:
                    logger.info(f"  Migrated {i}/{len(relations)} synapses...")

        logger.info(f"✅ Migrated {len(relations)} synapses")
        return len(relations)

    async def auto_detect_relations(
        self,
        similarity_threshold: float = 0.75,
        max_relations_per_concept: int = 5
    ) -> int:
        """
        Détecte automatiquement relations par similarité embeddings

        Comme cerveau: concepts similaires → connexions automatiques
        """
        logger.info(f"🔍 Auto-detecting relations (threshold: {similarity_threshold})...")

        # Récupérer tous concepts avec embeddings
        async with self.neo4j.session() as session:
            result = await session.run("""
                MATCH (c:Concept)
                WHERE c.embedding IS NOT NULL
                RETURN c.id as id, c.embedding as embedding, c.content as content
            """)

            concepts = []
            async for record in result:
                concepts.append({
                    'id': record['id'],
                    'embedding': np.array(record['embedding'], dtype=np.float32),
                    'content': record['content']
                })

        logger.info(f"Found {len(concepts)} concepts with embeddings")

        if len(concepts) < 2:
            logger.info("Not enough concepts for relation detection")
            return 0

        # Calculer similarités et créer relations
        created = 0
        async with self.neo4j.session() as session:
            for i, concept_a in enumerate(concepts):
                similarities = []

                # Calculer similarité avec tous les autres
                for j, concept_b in enumerate(concepts):
                    if i >= j:  # Éviter doublons et self-loops
                        continue

                    # Cosine similarity
                    emb_a = concept_a['embedding']
                    emb_b = concept_b['embedding']

                    dot = np.dot(emb_a, emb_b)
                    norm_a = np.linalg.norm(emb_a)
                    norm_b = np.linalg.norm(emb_b)

                    if norm_a == 0 or norm_b == 0:
                        continue

                    similarity = float(dot / (norm_a * norm_b))

                    if similarity >= similarity_threshold:
                        similarities.append({
                            'target_id': concept_b['id'],
                            'similarity': similarity,
                            'target_content': concept_b['content']
                        })

                # Garder top N similaires
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                top_similar = similarities[:max_relations_per_concept]

                # Créer synapses
                for sim in top_similar:
                    await session.run("""
                        MATCH (a:Concept {id: $source_id})
                        MATCH (b:Concept {id: $target_id})
                        MERGE (a)-[s:SYNAPSE]-(b)
                        ON CREATE SET
                            s.strength = $similarity,
                            s.use_count = 0,
                            s.relation_type = 'semantic_similarity',
                            s.created_at = datetime(),
                            s.last_used = datetime()
                    """,
                        source_id=concept_a['id'],
                        target_id=sim['target_id'],
                        similarity=sim['similarity']
                    )
                    created += 1

                if (i + 1) % 5 == 0:
                    logger.info(f"  Processed {i + 1}/{len(concepts)} concepts, created {created} synapses...")

        logger.info(f"✅ Auto-detected {created} semantic relations")
        return created

    async def create_indexes(self):
        """Créer indexes Neo4j pour performance"""
        logger.info("📇 Creating Neo4j indexes...")

        async with self.neo4j.session() as session:
            # Constraint unique ID
            try:
                await session.run("""
                    CREATE CONSTRAINT concept_id IF NOT EXISTS
                    FOR (c:Concept) REQUIRE c.id IS UNIQUE
                """)
                logger.info("  ✅ Created constraint: concept_id")
            except Exception as e:
                logger.warning(f"  ⚠️  Constraint already exists: {e}")

            # Index content
            try:
                await session.run("""
                    CREATE INDEX concept_content IF NOT EXISTS
                    FOR (c:Concept) ON (c.content)
                """)
                logger.info("  ✅ Created index: concept_content")
            except Exception as e:
                logger.warning(f"  ⚠️  Index already exists: {e}")

            # Index access_count
            try:
                await session.run("""
                    CREATE INDEX concept_access IF NOT EXISTS
                    FOR (c:Concept) ON (c.access_count)
                """)
                logger.info("  ✅ Created index: concept_access")
            except Exception as e:
                logger.warning(f"  ⚠️  Index already exists: {e}")

    async def verify_migration(self):
        """Vérifier migration"""
        logger.info("\n📊 Migration Verification:")

        async with self.neo4j.session() as session:
            # Count concepts
            result = await session.run("MATCH (c:Concept) RETURN count(c) as count")
            record = await result.single()
            concept_count = record['count']
            logger.info(f"  Concepts: {concept_count}")

            # Count synapses
            result = await session.run("MATCH ()-[s:SYNAPSE]->() RETURN count(s) as count")
            record = await result.single()
            synapse_count = record['count']
            logger.info(f"  Synapses: {synapse_count}")

            # Average degree
            if concept_count > 0:
                avg_degree = (synapse_count * 2) / concept_count
                logger.info(f"  Avg degree: {avg_degree:.2f}")

            # Top 5 concepts
            result = await session.run("""
                MATCH (c:Concept)
                RETURN c.content, c.access_count
                ORDER BY c.access_count DESC
                LIMIT 5
            """)
            logger.info("\n  Top 5 concepts:")
            async for record in result:
                logger.info(f"    [{record['c.access_count']:3d}x] {record['c.content'][:60]}")


async def main():
    """Main migration process"""

    logger.info("=" * 80)
    logger.info("🚀 MIGRATION PostgreSQL → Neo4j Neural System")
    logger.info("=" * 80)

    # Connect to PostgreSQL
    pg_pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='agi_user',
        password='agi_password',
        database='agi_db'
    )

    migrator = Neo4jMigrator(pg_pool)

    try:
        # 1. Create indexes
        await migrator.create_indexes()

        # 2. Migrate concepts
        concepts = await migrator.migrate_concepts()

        # 3. Migrate existing relations
        relations = await migrator.migrate_relations()

        # 4. Auto-detect new relations
        auto_relations = await migrator.auto_detect_relations(
            similarity_threshold=0.75,
            max_relations_per_concept=5
        )

        # 5. Verify
        await migrator.verify_migration()

        logger.info("\n" + "=" * 80)
        logger.info("✅ MIGRATION COMPLETE")
        logger.info(f"  Migrated: {concepts} concepts, {relations} existing relations")
        logger.info(f"  Created: {auto_relations} auto-detected relations")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        raise

    finally:
        await migrator.close()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
