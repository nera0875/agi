-- ═══════════════════════════════════════════════════════════
-- MASSIVE MEMORY UPGRADE - AGI Milliardaire
-- Augmentation L2/L3 : 100K → 1M-10M tokens
-- ═══════════════════════════════════════════════════════════

-- 1. Activer pgvector pour embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Table conversation_episodes - Mémoire épisodique
CREATE TABLE IF NOT EXISTS conversation_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES active_context(session_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Raw data (pour consolidation)
    raw_conversation TEXT,                  -- Conversation complète
    user_messages TEXT[],                   -- Messages utilisateur
    assistant_messages TEXT[],              -- Réponses AGI

    -- Compressed data (pour retrieval rapide)
    summary TEXT NOT NULL,                  -- Résumé Claude (100-500 tokens)
    key_learnings JSONB DEFAULT '[]',       -- ["learning 1", "learning 2", ...]
    decisions_made JSONB DEFAULT '[]',      -- [{"decision": "...", "reason": "..."}]
    patterns_discovered JSONB DEFAULT '[]', -- [{"pattern": "...", "type": "..."}]
    tools_used TEXT[],                      -- ["think", "memory", "database"]

    -- Semantic search
    embedding vector(1024),                 -- Voyage AI embedding

    -- Context for next session
    next_session_context TEXT,              -- "Continue à optimiser X, puis faire Y"
    context_snapshot JSONB,                 -- active_context au moment de la fermeture

    -- LTP/LTD
    strength FLOAT DEFAULT 1.0,             -- Importance (0.0-1.0)
    access_count INT DEFAULT 0,             -- Nombre de fois accédée
    last_accessed TIMESTAMPTZ,

    -- Metadata
    tokens_count INT,                       -- Nombre de tokens total
    duration_seconds INT,                   -- Durée conversation
    quality_score FLOAT,                    -- Score qualité (0-1)

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour performance
CREATE INDEX idx_conversation_episodes_timestamp ON conversation_episodes(timestamp DESC);
CREATE INDEX idx_conversation_episodes_strength ON conversation_episodes(strength DESC);
CREATE INDEX idx_conversation_episodes_embedding ON conversation_episodes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_conversation_episodes_session ON conversation_episodes(session_id);

-- 3. Augmenter agi_knowledge avec embeddings
ALTER TABLE agi_knowledge ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE agi_knowledge ADD COLUMN IF NOT EXISTS strength FLOAT DEFAULT 1.0;
ALTER TABLE agi_knowledge ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 0;
ALTER TABLE agi_knowledge ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMPTZ;

-- Index embeddings pour agi_knowledge
CREATE INDEX IF NOT EXISTS idx_agi_knowledge_embedding ON agi_knowledge USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_agi_knowledge_strength ON agi_knowledge(strength DESC);

-- 4. Table memory_store - Augmentation
ALTER TABLE memory_store ADD COLUMN IF NOT EXISTS embedding vector(1024);
ALTER TABLE memory_store ADD COLUMN IF NOT EXISTS strength FLOAT DEFAULT 1.0;
ALTER TABLE memory_store ADD COLUMN IF NOT EXISTS access_count INT DEFAULT 0;
ALTER TABLE memory_store ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMPTZ;

-- Index embeddings pour memory_store
CREATE INDEX IF NOT EXISTS idx_memory_store_embedding ON memory_store USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_memory_store_strength ON memory_store(strength DESC);

-- 5. Table claude_md_history - Versioning CLAUDE.md
CREATE TABLE IF NOT EXISTS claude_md_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INT GENERATED ALWAYS AS IDENTITY,
    content TEXT NOT NULL,
    diff TEXT,                              -- Diff avec version précédente
    reason TEXT,                            -- Raison de l'update

    -- Stats au moment de l'update
    project_state JSONB,                    -- État projet (tables, rules, tools, etc.)
    memory_stats JSONB,                     -- Stats mémoire

    -- Metadata
    generated_by TEXT DEFAULT 'auto-agent', -- 'auto-agent' ou 'manual'
    model_used TEXT,                        -- 'claude-haiku-4', etc.

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claude_md_history_version ON claude_md_history(version DESC);

-- 6. Table voyage_ai_cache - Cache embeddings (économie coût)
CREATE TABLE IF NOT EXISTS voyage_ai_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text_hash TEXT UNIQUE NOT NULL,         -- SHA256 du texte
    text TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    model TEXT DEFAULT 'voyage-3',

    -- Stats
    hit_count INT DEFAULT 1,
    last_hit TIMESTAMPTZ DEFAULT NOW(),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voyage_cache_hash ON voyage_ai_cache(text_hash);
CREATE INDEX idx_voyage_cache_hits ON voyage_ai_cache(hit_count DESC);

-- 7. Table cohere_rerank_cache - Cache reranking
CREATE TABLE IF NOT EXISTS cohere_rerank_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash TEXT NOT NULL,               -- SHA256(query + doc_ids)
    query TEXT NOT NULL,
    document_ids TEXT[] NOT NULL,
    reranked_ids TEXT[] NOT NULL,           -- IDs ordonnés par pertinence
    relevance_scores FLOAT[] NOT NULL,

    -- Stats
    hit_count INT DEFAULT 1,
    last_hit TIMESTAMPTZ DEFAULT NOW(),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cohere_cache_hash ON cohere_rerank_cache(query_hash);

-- 8. Table consolidation_log - Historique consolidations
CREATE TABLE IF NOT EXISTS consolidation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Stats before
    conversations_before INT,
    total_tokens_before BIGINT,
    avg_strength_before FLOAT,

    -- Stats after
    conversations_compressed INT,
    total_tokens_after BIGINT,
    avg_strength_after FLOAT,
    compression_ratio FLOAT,                -- Ratio compression

    -- Actions
    ltd_weakened INT,                       -- Concepts affaiblis
    ltp_strengthened INT,                   -- Concepts renforcés
    patterns_extracted INT,                 -- Patterns promus L2 → L3
    embeddings_generated INT,               -- Embeddings créés

    -- Performance
    duration_seconds FLOAT,
    cost_usd FLOAT,                         -- Coût APIs (Voyage + Claude)

    -- Details
    actions_log JSONB,                      -- Log détaillé actions

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_consolidation_history_timestamp ON consolidation_history(timestamp DESC);

-- 9. Vue pour monitoring mémoire
CREATE OR REPLACE VIEW memory_health AS
SELECT
    'L1' as layer,
    'working_memory' as table_name,
    COUNT(*) as concept_count,
    AVG(strength) as avg_strength,
    SUM(access_count) as total_accesses
FROM working_memory
UNION ALL
SELECT
    'L2',
    'conversation_episodes',
    COUNT(*),
    AVG(strength),
    SUM(access_count)
FROM conversation_episodes
UNION ALL
SELECT
    'L2',
    'agi_knowledge',
    COUNT(*),
    AVG(strength),
    SUM(access_count)
FROM agi_knowledge
UNION ALL
SELECT
    'L3',
    'memory_store',
    COUNT(*),
    AVG(strength),
    SUM(access_count)
FROM memory_store;

-- 10. Fonction trigger pour update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_episodes_updated_at
    BEFORE UPDATE ON conversation_episodes
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 11. Fonction LTD automatique (appelée par consolidation)
CREATE OR REPLACE FUNCTION apply_ltd(threshold_days INT DEFAULT 7)
RETURNS TABLE(table_name TEXT, weakened_count INT) AS $$
BEGIN
    -- Weaken unused conversation episodes
    UPDATE conversation_episodes
    SET strength = CASE
        WHEN strength * 0.95 < 0.1 THEN 0.1
        ELSE strength * 0.95
    END
    WHERE last_accessed IS NULL
       OR last_accessed < NOW() - (threshold_days || ' days')::INTERVAL;

    RETURN QUERY SELECT 'conversation_episodes'::TEXT, COUNT(*)::INT
    FROM conversation_episodes
    WHERE strength < 0.3;

    -- Weaken unused agi_knowledge
    UPDATE agi_knowledge
    SET strength = CASE
        WHEN strength * 0.95 < 0.1 THEN 0.1
        ELSE strength * 0.95
    END
    WHERE last_accessed IS NULL
       OR last_accessed < NOW() - (threshold_days || ' days')::INTERVAL;

    RETURN QUERY SELECT 'agi_knowledge'::TEXT, COUNT(*)::INT
    FROM agi_knowledge
    WHERE strength < 0.3;

    -- Weaken unused memory_store
    UPDATE memory_store
    SET strength = CASE
        WHEN strength * 0.95 < 0.1 THEN 0.1
        ELSE strength * 0.95
    END
    WHERE last_accessed IS NULL
       OR last_accessed < NOW() - (threshold_days || ' days')::INTERVAL;

    RETURN QUERY SELECT 'memory_store'::TEXT, COUNT(*)::INT
    FROM memory_store
    WHERE strength < 0.3;
END;
$$ LANGUAGE plpgsql;

-- 12. Fonction LTP automatique (renforcement lors d'accès)
CREATE OR REPLACE FUNCTION apply_ltp(concept_id UUID, table_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format(
        'UPDATE %I SET
            strength = CASE WHEN strength + 0.1 > 1.0 THEN 1.0 ELSE strength + 0.1 END,
            access_count = access_count + 1,
            last_accessed = NOW()
         WHERE id = $1',
        table_name
    ) USING concept_id;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════
-- MIGRATION COMPLETE
-- Tables créées: 5 (conversation_episodes, claude_md_history, etc.)
-- Columns ajoutées: embedding, strength, access_count sur 3 tables
-- Index: 15+ pour performance
-- Fonctions: LTD/LTP automatiques
-- Vue: memory_health pour monitoring
-- ═══════════════════════════════════════════════════════════
