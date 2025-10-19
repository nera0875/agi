#!/usr/bin/env python3
"""
Migrate System Rules to Neo4j with Reinforcement Learning
=========================================================

Migre les 8 rules PostgreSQL → Neo4j comme Concepts avec:
- strength (0-1): Force synaptique (working memory)
- access_count: Nombre d'utilisations
- last_accessed: Dernière activation
- essence: Version compressée
- full_text: Texte complet

Comme cerveau humain:
- Rules utilisées → strength ↑ (LTP)
- Rules non utilisées → strength ↓ (LTD)
- Bootstrap charge top-K par strength
"""

import asyncio
import asyncpg
from neo4j import AsyncGraphDatabase
from datetime import datetime


# Mapping category → essence
RULE_ESSENCES = {
    'llm_behavior': {
        'JAMAIS accepter': 'Sois critique et valide tout',
        'TU ES LE BOSS': 'Sois autonome et décide'
    },
    'objective': {
        'But ultime': 'Objectif: Milliardaire via mémoire puissante'
    },
    'tool_usage': {
        'Si tâche >2s': 'Workers headless, jamais attendre',
        'JAMAIS utiliser Task': 'Agents headless, jamais Task tool bloquant'
    },
    'memory_policy': {
        'Tout >50 mots': 'PostgreSQL first, pas fichiers',
        'Toujours mesurer': 'Auto-amélioration continue via métriques'
    },
    'workflow': {
        'Zéro temps perdu': 'Efficace, parallèle, zéro waste'
    }
}


def extract_essence(category: str, full_text: str) -> str:
    """Extrait essence d'une rule"""
    # Trouve la clé qui match
    if category in RULE_ESSENCES:
        for key, essence in RULE_ESSENCES[category].items():
            if key in full_text:
                return essence

    # Fallback: premiers 50 chars
    return full_text[:50]


async def migrate_rules_to_neo4j():
    """Migre rules PostgreSQL → Neo4j avec reinforcement learning"""

    print("=" * 80)
    print("🧠 MIGRATION RULES → NEO4J (Reinforcement Learning)")
    print("=" * 80)

    # Connect PostgreSQL
    pg_pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='agi_user',
        password='agi_password',
        database='agi_db'
    )

    # Connect Neo4j
    neo4j_driver = AsyncGraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "Voiture789")
    )

    try:
        # 1. Récupérer rules PostgreSQL
        async with pg_pool.acquire() as conn:
            rules = await conn.fetch("""
                SELECT
                    id,
                    rule_type as category,
                    rule_content as full_text,
                    priority
                FROM system_rules
                WHERE active = true
                ORDER BY priority DESC
            """)

        print(f"\n📥 Found {len(rules)} rules in PostgreSQL")

        # 2. Clear existing Rule nodes
        async with neo4j_driver.session() as session:
            await session.run("MATCH (r:Rule) DETACH DELETE r")
            print("🗑️  Cleared existing Rule nodes")

        # 3. Migrate each rule
        migrated = 0
        async with neo4j_driver.session() as session:
            for rule in rules:
                essence = extract_essence(rule['category'], rule['full_text'])

                await session.run("""
                    CREATE (r:Rule {
                        id: $id,
                        category: $category,
                        essence: $essence,
                        full_text: $full_text,
                        priority: $priority,
                        strength: 0.5,
                        access_count: 0,
                        last_accessed: null,
                        created_at: datetime()
                    })
                """,
                    id=str(rule['id']),
                    category=rule['category'],
                    essence=essence,
                    full_text=rule['full_text'],
                    priority=rule['priority']
                )

                migrated += 1
                print(f"  ✅ {rule['category']}: {essence[:50]}...")

        print(f"\n✅ Migrated {migrated} rules to Neo4j")

        # 4. Create category grouping
        async with neo4j_driver.session() as session:
            await session.run("""
                // Create Category nodes
                MATCH (r:Rule)
                WITH DISTINCT r.category as cat_name
                CREATE (c:RuleCategory {name: cat_name})
            """)

            await session.run("""
                // Link rules to categories
                MATCH (r:Rule)
                MATCH (c:RuleCategory {name: r.category})
                CREATE (r)-[:BELONGS_TO]->(c)
            """)

            print("🔗 Created category grouping")

        # 5. Stats
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (r:Rule)
                RETURN
                    count(r) as total_rules,
                    avg(r.strength) as avg_strength,
                    count(distinct r.category) as categories
            """)

            record = await result.single()

            print("\n" + "=" * 80)
            print("📊 NEO4J STATS")
            print("=" * 80)
            print(f"  Total rules: {record['total_rules']}")
            print(f"  Avg strength: {record['avg_strength']:.2f} (baseline)")
            print(f"  Categories: {record['categories']}")

        # 6. Preview rules
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (r:Rule)
                RETURN r.category, r.essence, r.strength, r.priority
                ORDER BY r.priority DESC
            """)

            print(f"\n🎯 RULES (Reinforcement Ready):")
            async for record in result:
                print(f"  [{record['r.priority']}] {record['r.category']}: {record['r.essence']}")
                print(f"       Strength: {record['r.strength']:.2f} (will adapt with usage!)")

        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETE")
        print("=" * 80)
        print("\nNow rules will:")
        print("  • Strengthen when used (LTP)")
        print("  • Weaken when unused (LTD)")
        print("  • Bootstrap loads top-K by strength")
        print("  • Personalize to your usage patterns!")

    finally:
        await pg_pool.close()
        await neo4j_driver.close()


if __name__ == "__main__":
    asyncio.run(migrate_rules_to_neo4j())
