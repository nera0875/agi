-- Initialisation de la base de données AGI avec pgvector
-- Schémas pour le système de mémoire L1/L2/L3 et graphe de connaissances

-- Extension pgvector pour les embeddings
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des sessions utilisateur
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table principale des mémoires (L1/L2/L3)
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, image, audio, etc.
    memory_level INTEGER NOT NULL CHECK (memory_level IN (1, 2, 3)), -- L1, L2, L3
    embedding vector(1536), -- Voyage AI embeddings (1536 dimensions)
    metadata JSONB DEFAULT '{}',
    importance_score FLOAT DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE -- Pour L1 uniquement
);

-- Index pour les recherches vectorielles
CREATE INDEX IF NOT EXISTS memories_embedding_idx ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS memories_user_level_idx ON memories(user_id, memory_level);
CREATE INDEX IF NOT EXISTS memories_importance_idx ON memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS memories_created_idx ON memories(created_at DESC);

-- Table des relations entre mémoires
CREATE TABLE IF NOT EXISTS memory_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL, -- similarity, causality, temporal, etc.
    strength FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_memory_id, target_memory_id, relation_type)
);

-- Table des concepts extraits
CREATE TABLE IF NOT EXISTS concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    concept_type VARCHAR(50) DEFAULT 'general', -- person, place, event, idea, etc.
    embedding vector(1536),
    frequency INTEGER DEFAULT 1,
    importance_score FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name, concept_type)
);

-- Index pour les concepts
CREATE INDEX IF NOT EXISTS concepts_embedding_idx ON concepts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS concepts_user_idx ON concepts(user_id);
CREATE INDEX IF NOT EXISTS concepts_importance_idx ON concepts(importance_score DESC);

-- Table des liens entre mémoires et concepts
CREATE TABLE IF NOT EXISTS memory_concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(memory_id, concept_id)
);

-- Table des conversations/dialogues
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des messages dans les conversations
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des tâches de consolidation (L1→L2→L3)
CREATE TABLE IF NOT EXISTS consolidation_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL, -- l1_to_l2, l2_to_l3, pattern_extraction
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    input_data JSONB NOT NULL,
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des métriques et analytics
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    dimensions JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les analytics
CREATE INDEX IF NOT EXISTS analytics_user_metric_idx ON analytics(user_id, metric_name);
CREATE INDEX IF NOT EXISTS analytics_timestamp_idx ON analytics(timestamp DESC);

-- Fonctions utilitaires

-- Fonction pour calculer la similarité cosinus
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector)
RETURNS float AS $$
BEGIN
    RETURN 1 - (a <=> b);
END;
$$ LANGUAGE plpgsql;

-- Fonction pour nettoyer les mémoires L1 expirées
CREATE OR REPLACE FUNCTION cleanup_expired_l1_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM memories 
    WHERE memory_level = 1 
    AND expires_at IS NOT NULL 
    AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour mettre à jour le score d'importance
CREATE OR REPLACE FUNCTION update_importance_score(memory_id UUID)
RETURNS void AS $$
DECLARE
    new_score FLOAT;
BEGIN
    -- Calcul basé sur l'accès, l'âge et les relations
    SELECT 
        LEAST(10.0, 
            (access_count * 0.1) + 
            (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 86400 * -0.01) +
            (SELECT COUNT(*) * 0.2 FROM memory_relations WHERE source_memory_id = memory_id OR target_memory_id = memory_id)
        )
    INTO new_score
    FROM memories 
    WHERE id = memory_id;
    
    UPDATE memories 
    SET importance_score = COALESCE(new_score, 0.0),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = memory_id;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour maintenir les timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Appliquer le trigger aux tables nécessaires
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Données de test (optionnel)
INSERT INTO users (email, username, password_hash) 
VALUES ('admin@agi.local', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS') -- password: admin123
ON CONFLICT (email) DO NOTHING;

-- Commentaires pour la documentation
COMMENT ON TABLE memories IS 'Table principale pour le système de mémoire L1/L2/L3';
COMMENT ON COLUMN memories.memory_level IS '1=Mémoire immédiate, 2=Mémoire étendue, 3=Mémoire long terme';
COMMENT ON COLUMN memories.embedding IS 'Vecteur d''embedding Voyage AI (1536 dimensions)';
COMMENT ON TABLE concepts IS 'Concepts extraits automatiquement des mémoires';
COMMENT ON TABLE memory_relations IS 'Relations sémantiques entre mémoires';
COMMENT ON TABLE consolidation_tasks IS 'Tâches de consolidation automatique L1→L2→L3';