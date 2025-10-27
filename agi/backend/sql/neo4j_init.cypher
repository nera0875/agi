// Initialisation Neo4j pour le graphe de connaissances AGI
// Schéma pour les concepts, relations et patterns

// Contraintes d'unicité
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS FOR (p:Pattern) REQUIRE p.id IS UNIQUE;

// Index pour les performances
CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name);
CREATE INDEX concept_type_index IF NOT EXISTS FOR (c:Concept) ON (c.type);
CREATE INDEX memory_level_index IF NOT EXISTS FOR (m:Memory) ON (m.level);
CREATE INDEX pattern_type_index IF NOT EXISTS FOR (p:Pattern) ON (p.type);

// Nœuds de base

// Utilisateurs
// Les utilisateurs sont créés dynamiquement depuis PostgreSQL

// Concepts - Entités extraites des mémoires
// Propriétés: id, name, type, description, frequency, importance, created_at, updated_at
// Types: PERSON, PLACE, EVENT, IDEA, OBJECT, SKILL, GOAL, etc.

// Mémoires - Références aux mémoires PostgreSQL
// Propriétés: id, level (L1/L2/L3), content_summary, importance, created_at

// Patterns - Motifs récurrents détectés
// Propriétés: id, type, description, confidence, frequency, created_at
// Types: TEMPORAL, CAUSAL, BEHAVIORAL, SEMANTIC, etc.

// Relations de base

// Relations entre concepts
// (:Concept)-[:RELATED_TO {strength, type, created_at}]->(:Concept)
// (:Concept)-[:IS_A {confidence}]->(:Concept)  // Hiérarchie taxonomique
// (:Concept)-[:PART_OF {confidence}]->(:Concept)  // Composition
// (:Concept)-[:CAUSES {confidence, temporal_distance}]->(:Concept)  // Causalité
// (:Concept)-[:OCCURS_WITH {frequency, confidence}]->(:Concept)  // Co-occurrence

// Relations mémoire-concept
// (:Memory)-[:CONTAINS {relevance}]->(:Concept)
// (:Memory)-[:REFERENCES {strength}]->(:Memory)

// Relations utilisateur
// (:User)-[:OWNS]->(:Memory)
// (:User)-[:KNOWS {proficiency, last_used}]->(:Concept)
// (:User)-[:EXHIBITS]->(:Pattern)

// Relations temporelles
// (:Memory)-[:FOLLOWS {time_gap}]->(:Memory)
// (:Concept)-[:EVOLVES_TO {confidence}]->(:Concept)

// Procédures stockées pour les opérations courantes

// Procédure pour créer un concept avec vérification de doublons
CALL apoc.custom.asProcedure(
  'agi.createConcept',
  'MERGE (c:Concept {name: $name, type: $type, user_id: $user_id})
   ON CREATE SET 
     c.id = apoc.create.uuid(),
     c.description = $description,
     c.frequency = 1,
     c.importance = $importance,
     c.created_at = datetime(),
     c.updated_at = datetime()
   ON MATCH SET 
     c.frequency = c.frequency + 1,
     c.updated_at = datetime(),
     c.importance = CASE WHEN $importance > c.importance THEN $importance ELSE c.importance END
   RETURN c',
  'read',
  [['name', 'string'], ['type', 'string'], ['user_id', 'string'], ['description', 'string'], ['importance', 'float']]
);

// Procédure pour créer une relation entre concepts
CALL apoc.custom.asProcedure(
  'agi.createConceptRelation',
  'MATCH (c1:Concept {id: $concept1_id}), (c2:Concept {id: $concept2_id})
   MERGE (c1)-[r:RELATED_TO {type: $relation_type}]->(c2)
   ON CREATE SET 
     r.strength = $strength,
     r.created_at = datetime(),
     r.frequency = 1
   ON MATCH SET 
     r.strength = (r.strength + $strength) / 2,
     r.frequency = r.frequency + 1,
     r.updated_at = datetime()
   RETURN r',
  'write',
  [['concept1_id', 'string'], ['concept2_id', 'string'], ['relation_type', 'string'], ['strength', 'float']]
);

// Procédure pour trouver des concepts similaires
CALL apoc.custom.asProcedure(
  'agi.findSimilarConcepts',
  'MATCH (c:Concept {user_id: $user_id})
   WHERE c.name CONTAINS $query OR c.description CONTAINS $query
   RETURN c
   ORDER BY c.importance DESC, c.frequency DESC
   LIMIT $limit',
  'read',
  [['user_id', 'string'], ['query', 'string'], ['limit', 'int']]
);

// Procédure pour détecter des patterns temporels
CALL apoc.custom.asProcedure(
  'agi.detectTemporalPatterns',
  'MATCH (u:User {id: $user_id})-[:OWNS]->(m1:Memory)-[:FOLLOWS]->(m2:Memory)
   WHERE m1.created_at < m2.created_at
   WITH m1, m2, duration.between(m1.created_at, m2.created_at) as time_gap
   WHERE time_gap.seconds < $max_gap_seconds
   MATCH (m1)-[:CONTAINS]->(c1:Concept), (m2)-[:CONTAINS]->(c2:Concept)
   WITH c1, c2, count(*) as frequency, avg(time_gap.seconds) as avg_gap
   WHERE frequency >= $min_frequency
   MERGE (p:Pattern {type: "TEMPORAL", user_id: $user_id})
   SET p.description = "Pattern: " + c1.name + " followed by " + c2.name,
       p.frequency = frequency,
       p.avg_time_gap = avg_gap,
       p.confidence = frequency / 10.0,
       p.created_at = datetime()
   MERGE (p)-[:INVOLVES]->(c1)
   MERGE (p)-[:INVOLVES]->(c2)
   RETURN p, c1, c2',
  'write',
  [['user_id', 'string'], ['max_gap_seconds', 'int'], ['min_frequency', 'int']]
);

// Procédure pour calculer l'importance des concepts
CALL apoc.custom.asProcedure(
  'agi.calculateConceptImportance',
  'MATCH (c:Concept {user_id: $user_id})
   OPTIONAL MATCH (c)<-[r:CONTAINS]-(m:Memory)
   OPTIONAL MATCH (c)-[rel]-(other:Concept)
   WITH c, count(DISTINCT m) as memory_count, count(DISTINCT rel) as relation_count
   SET c.importance = (memory_count * 0.4 + relation_count * 0.3 + c.frequency * 0.3) / 10.0,
       c.updated_at = datetime()
   RETURN c.name, c.importance',
  'write',
  [['user_id', 'string']]
);

// Procédure pour nettoyer les concepts peu utilisés
CALL apoc.custom.asProcedure(
  'agi.cleanupUnusedConcepts',
  'MATCH (c:Concept {user_id: $user_id})
   WHERE c.frequency < $min_frequency 
     AND c.importance < $min_importance
     AND datetime() - c.created_at > duration({days: $min_age_days})
   OPTIONAL MATCH (c)-[r]-()
   DELETE r, c
   RETURN count(c) as deleted_count',
  'write',
  [['user_id', 'string'], ['min_frequency', 'int'], ['min_importance', 'float'], ['min_age_days', 'int']]
);

// Procédure pour explorer le graphe de connaissances
CALL apoc.custom.asProcedure(
  'agi.exploreKnowledgeGraph',
  'MATCH path = (start:Concept {name: $start_concept, user_id: $user_id})-[*1..$max_depth]-(end:Concept)
   WHERE end.user_id = $user_id
   WITH path, length(path) as depth, 
        reduce(score = 1.0, rel in relationships(path) | score * coalesce(rel.strength, 0.5)) as path_score
   WHERE path_score > $min_score
   RETURN path, depth, path_score
   ORDER BY path_score DESC, depth ASC
   LIMIT $limit',
  'read',
  [['start_concept', 'string'], ['user_id', 'string'], ['max_depth', 'int'], ['min_score', 'float'], ['limit', 'int']]
);

// Données d'exemple pour les tests
// Créer un utilisateur de test
MERGE (u:User {id: "test-user-uuid"})
SET u.email = "admin@agi.local",
    u.username = "admin",
    u.created_at = datetime();

// Créer quelques concepts d'exemple
CALL agi.createConcept("Intelligence Artificielle", "IDEA", "test-user-uuid", "Domaine de l'informatique", 0.9);
CALL agi.createConcept("Machine Learning", "SKILL", "test-user-uuid", "Sous-domaine de l'IA", 0.8);
CALL agi.createConcept("Python", "SKILL", "test-user-uuid", "Langage de programmation", 0.7);

// Créer des relations d'exemple
MATCH (ai:Concept {name: "Intelligence Artificielle"}), (ml:Concept {name: "Machine Learning"})
CALL agi.createConceptRelation(ai.id, ml.id, "CONTAINS", 0.9);

MATCH (ml:Concept {name: "Machine Learning"}), (py:Concept {name: "Python"})
CALL agi.createConceptRelation(ml.id, py.id, "USES", 0.8);

// Commentaires pour la documentation
// Ce schéma Neo4j complète PostgreSQL en fournissant:
// 1. Graphe de connaissances pour les relations complexes
// 2. Détection de patterns et motifs récurrents  
// 3. Navigation sémantique dans les concepts
// 4. Analyse de centralité et d'importance
// 5. Exploration de chemins de connaissances