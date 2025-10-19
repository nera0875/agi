// ============================================================================
// NEURAL MEMORY SCHEMA - Neo4j Brain Structure
// ============================================================================
// Système de mémoire fonctionnant exactement comme un cerveau humain:
// - Spreading activation (décroissance exponentielle)
// - LTP/LTD (renforcement/affaiblissement automatique)
// - Synaptic pruning (suppression connexions faibles)
// - Économie de tokens = économie de glucose

// ============================================================================
// CONSTRAINTS & INDEXES
// ============================================================================

// Concept unique ID
CREATE CONSTRAINT concept_id IF NOT EXISTS
FOR (c:Concept) REQUIRE c.id IS UNIQUE;

// Index pour recherche rapide
CREATE INDEX concept_content IF NOT EXISTS
FOR (c:Concept) ON (c.content);

CREATE INDEX concept_access IF NOT EXISTS
FOR (c:Concept) ON (c.access_count);

// Index vector (si Neo4j 5.11+ avec vector support)
// CREATE VECTOR INDEX concept_embedding IF NOT EXISTS
// FOR (c:Concept) ON (c.embedding)
// OPTIONS {indexConfig: {
//   `vector.dimensions`: 1024,
//   `vector.similarity_function`: 'cosine'
// }};

// ============================================================================
// NODE SCHEMA - Concepts (Neurones)
// ============================================================================

// Exemple de création de concept
// CREATE (:Concept {
//     id: randomUUID(),
//     content: "bootstrap system",
//     tags: ["system", "bootstrap", "agi-core"],
//     embedding: [...],  // Vector 1024 dimensions (Voyage AI)
//
//     // Métadonnées de renforcement
//     access_count: 0,
//     last_accessed: timestamp(),
//     quality_score: 0.5,
//
//     // Métadonnées
//     source_type: "system_rule",
//     created_at: timestamp()
// })

// ============================================================================
// RELATIONSHIP SCHEMA - Synapses (Connexions)
// ============================================================================

// Relations avec force synaptique (comme vraies synapses neuronales)
// (:Concept)-[:SYNAPSE {
//     strength: 0.5,              // Force 0-1 (poids synaptique)
//     use_count: 0,               // Fréquence d'activation conjointe
//     last_used: timestamp(),     // Récence (pour LTD)
//     relation_type: "semantic",  // Type: semantic, causal, temporal, etc.
//     created_at: timestamp()
// }]->(:Concept)

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// Function: Calculer activation strength avec décroissance
// Input: path (chemin dans graphe)
// Output: activation_strength (0-1)
// Formula: 1.0 / (depth + 1) * avg(synapse.strength)

// ============================================================================
// SPREADING ACTIVATION QUERY (Usage principal)
// ============================================================================

// MATCH (start:Concept)
// WHERE start.content CONTAINS $query
//    OR vector.similarity.cosine(start.embedding, $query_embedding) > 0.7
//
// CALL apoc.path.expandConfig(start, {
//     maxLevel: 2,
//     relationshipFilter: "SYNAPSE>",
//     minLevel: 0
// })
// YIELD path
//
// WITH
//     nodes(path) as concepts,
//     relationships(path) as synapses,
//     1.0 / (length(path) + 1) as base_activation,
//     reduce(s = 1.0, syn in relationships(path) | s * syn.strength) as path_strength
//
// LET final_activation = base_activation * path_strength
//
// WHERE final_activation > 0.2  // Seuil économie énergie
//
// // LTP - Renforcement automatique des synapses utilisées
// FOREACH (syn in synapses |
//     SET syn.strength = CASE
//         WHEN syn.strength + 0.1 > 1.0 THEN 1.0
//         ELSE syn.strength + 0.1
//     END,
//     syn.use_count = syn.use_count + 1,
//     syn.last_used = timestamp()
// )
//
// RETURN DISTINCT concepts, final_activation
// ORDER BY final_activation DESC
// LIMIT 20

// ============================================================================
// LTD - DECAY AUTOMATIQUE (Cron nocturne)
// ============================================================================

// Affaiblir synapses non utilisées depuis 7 jours
// MATCH ()-[syn:SYNAPSE]->()
// WHERE syn.last_used < timestamp() - 604800000  // 7 jours en ms
// SET syn.strength = syn.strength * 0.95
// RETURN count(syn) as decayed

// ============================================================================
// SYNAPTIC PRUNING (Cron nocturne)
// ============================================================================

// Supprimer synapses trop faibles (< 0.1)
// MATCH ()-[syn:SYNAPSE]->()
// WHERE syn.strength < 0.1
// DELETE syn
// RETURN count(syn) as pruned

// ============================================================================
// CONSOLIDATION - Fusionner concepts similaires (Cron nocturne)
// ============================================================================

// Trouver concepts très similaires co-activés fréquemment
// MATCH (a:Concept)-[r1:SYNAPSE]->(c:Concept)<-[r2:SYNAPSE]-(b:Concept)
// WHERE a <> b
//   AND id(a) < id(b)  // Éviter doublons
//   AND r1.use_count > 10
//   AND r2.use_count > 10
//   AND vector.similarity.cosine(a.embedding, b.embedding) > 0.95
//
// MERGE (a)-[r:CONSOLIDATED_WITH]-(b)
// SET r.strength = 1.0,
//     r.created_at = timestamp()
// RETURN count(r) as consolidated

// ============================================================================
// METRICS - Santé du système neural
// ============================================================================

// Graph density (doit diminuer avec pruning)
// MATCH (c:Concept)
// WITH count(c) as total_nodes
// MATCH ()-[syn:SYNAPSE]->()
// WITH total_nodes, count(syn) as total_synapses
// RETURN
//     total_nodes,
//     total_synapses,
//     toFloat(total_synapses) / (total_nodes * total_nodes) as density

// Average synapse strength (doit augmenter avec usage)
// MATCH ()-[syn:SYNAPSE]->()
// RETURN
//     avg(syn.strength) as avg_strength,
//     avg(syn.use_count) as avg_use_count,
//     count(syn) as total_synapses

// Top concepts (les plus activés)
// MATCH (c:Concept)
// RETURN c.content, c.access_count, c.tags
// ORDER BY c.access_count DESC
// LIMIT 10

// ============================================================================
// MIGRATION - Importer depuis PostgreSQL
// ============================================================================

// Créer concepts depuis memory_store
// LOAD CSV WITH HEADERS FROM 'file:///memory_export.csv' AS row
// CREATE (:Concept {
//     id: row.id,
//     content: row.content,
//     embedding: apoc.convert.fromJsonList(row.embedding),
//     tags: split(row.tags, ','),
//     access_count: toInteger(row.access_count),
//     quality_score: toFloat(row.quality_score),
//     source_type: row.source_type,
//     created_at: datetime(row.created_at)
// })

// Créer synapses depuis relations PostgreSQL
// LOAD CSV WITH HEADERS FROM 'file:///relations_export.csv' AS row
// MATCH (a:Concept {id: row.source_id})
// MATCH (b:Concept {id: row.target_id})
// CREATE (a)-[:SYNAPSE {
//     strength: 0.5,
//     use_count: 0,
//     relation_type: row.relation_type,
//     created_at: datetime(row.created_at),
//     last_used: datetime()
// }]->(b)

// ============================================================================
// NOTES D'IMPLÉMENTATION
// ============================================================================

// 1. APOC Procedures requises:
//    - apoc.path.expandConfig (spreading activation)
//    - apoc.convert.fromJsonList (import embeddings)

// 2. Vector similarity:
//    - Neo4j 5.11+ natif
//    - Sinon: calculer en Python avec numpy

// 3. Performance:
//    - Index sur access_count, last_accessed
//    - Limiter spreading depth à 2-3 max
//    - Seuil activation > 0.2 (économie)

// 4. Consolidation:
//    - Cron quotidien 3h du matin
//    - LTD + Pruning + Metrics
//    - Backup avant pruning!
