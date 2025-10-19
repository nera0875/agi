-- ═══════════════════════════════════════════════════════════════════
-- AGI MEMORY SYSTEM - PostgreSQL Schemas L1/L2/L3
-- ═══════════════════════════════════════════════════════════════════
--
-- Architecture 3 couches:
-- L1 (Working Memory): 5-7 items, contexte immédiat, <50ms
-- L2 (Short-term): Session actuelle, batch events, <200ms
-- L3 (Long-term): Historique complet, consolidation, illimité
--
-- Stack: OpenAI + Anthropic + Cohere + Voyage AI
-- ═══════════════════════════════════════════════════════════════════

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ═══════════════════════════════════════════════════════════════════
-- L1: WORKING MEMORY (Temps Réel)
-- ═══════════════════════════════════════════════════════════════════

-- Events bruts capturés par L1 Observer
CREATE TABLE IF NOT EXISTS l1_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event data
    event_type TEXT NOT NULL,  -- Edit, Read, Write, think, etc.
    file_path TEXT,
    content TEXT,
    content_preview TEXT,  -- First 500 chars

    -- Classification (GPT-5-nano)
    classified_type TEXT,  -- code_edit, bug_fix, feature, decision, etc.
    importance INT CHECK (importance >= 0 AND importance <= 10),

    -- Storage decision
    storage_layer TEXT CHECK (storage_layer IN ('L1', 'L2', 'skip')),

    -- Context enrichment
    enriched_context JSONB,  -- MCP tools results

    -- Metadata
    session_id UUID,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    -- Indexes
    CONSTRAINT valid_importance CHECK (importance IS NULL OR (importance >= 0 AND importance <= 10))
);

CREATE INDEX idx_l1_events_session ON l1_events(session_id);
CREATE INDEX idx_l1_events_created ON l1_events(created_at DESC);
CREATE INDEX idx_l1_events_importance ON l1_events(importance DESC) WHERE importance IS NOT NULL;
CREATE INDEX idx_l1_events_unprocessed ON l1_events(processed, created_at) WHERE NOT processed;

-- Working memory current state (7±2 items max)
CREATE TABLE IF NOT EXISTS l1_working_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,

    -- Current focus
    current_file TEXT,
    current_function TEXT,
    current_task TEXT,
    focus_concepts TEXT[],

    -- Recent items (max 7)
    recent_events JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(session_id)
);

CREATE INDEX idx_l1_wm_session ON l1_working_memory(session_id);

-- ═══════════════════════════════════════════════════════════════════
-- L2: SHORT-TERM MEMORY (Session)
-- ═══════════════════════════════════════════════════════════════════

-- Code edits with embeddings (Voyage Code-2)
CREATE TABLE IF NOT EXISTS l2_code_edits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event data
    file_path TEXT NOT NULL,
    edit_type TEXT NOT NULL,  -- modified, created, deleted
    content TEXT,
    content_preview TEXT,

    -- Classification
    event_type TEXT,  -- From L1 classification
    importance INT,

    -- Embeddings (Voyage Code-2: 1536 dimensions)
    embedding vector(1536),

    -- Analysis results
    concepts_extracted TEXT[],
    relations_found JSONB,

    -- Metadata
    session_id UUID,
    language TEXT,  -- python, javascript, etc.
    lines_added INT DEFAULT 0,
    lines_removed INT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    analyzed_at TIMESTAMPTZ
);

CREATE INDEX idx_l2_code_session ON l2_code_edits(session_id);
CREATE INDEX idx_l2_code_created ON l2_code_edits(created_at DESC);
CREATE INDEX idx_l2_code_file ON l2_code_edits(file_path);
CREATE INDEX idx_l2_code_embedding ON l2_code_edits USING ivfflat (embedding vector_cosine_ops);

-- Text/decisions (Voyage v3)
CREATE TABLE IF NOT EXISTS l2_text_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Content
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- decision, documentation, note, etc.

    -- Classification
    importance INT,
    tags TEXT[],

    -- Embeddings (Voyage v3: 1024 dimensions)
    embedding vector(1024),

    -- Metadata
    session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_l2_text_session ON l2_text_memory(session_id);
CREATE INDEX idx_l2_text_type ON l2_text_memory(memory_type);
CREATE INDEX idx_l2_text_embedding ON l2_text_memory USING ivfflat (embedding vector_cosine_ops);

-- Batch processing queue
CREATE TABLE IF NOT EXISTS l2_batch_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Batch info
    batch_id UUID NOT NULL,
    event_ids UUID[] NOT NULL,
    event_count INT NOT NULL,

    -- Processing status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),

    -- Results
    concepts_extracted TEXT[],
    relations_found JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Processing time
    duration_ms INT
);

CREATE INDEX idx_l2_batch_status ON l2_batch_queue(status, created_at);
CREATE INDEX idx_l2_batch_id ON l2_batch_queue(batch_id);

-- ═══════════════════════════════════════════════════════════════════
-- L3: LONG-TERM MEMORY (Permanent)
-- ═══════════════════════════════════════════════════════════════════

-- Consolidated knowledge with embeddings (Voyage v3-large)
CREATE TABLE IF NOT EXISTS l3_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Content
    content TEXT NOT NULL,
    content_compressed TEXT,  -- Essence/summary
    knowledge_type TEXT NOT NULL,  -- pattern, architecture, decision, bug_fix, etc.

    -- Classification
    importance INT CHECK (importance >= 0 AND importance <= 10),
    tags TEXT[],

    -- Embeddings (Voyage v3-large: 1024 dimensions)
    embedding vector(1024),

    -- Full-text search (BM25)
    content_tsv tsvector,

    -- Relationships (will link to Neo4j)
    neo4j_node_id TEXT,  -- Reference to Neo4j node
    related_concepts TEXT[],

    -- Reinforcement (LTP/LTD)
    strength REAL DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,

    -- Source tracking
    source_session_id UUID,
    source_event_ids UUID[],

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_l3_knowledge_type ON l3_knowledge(knowledge_type);
CREATE INDEX idx_l3_knowledge_tags ON l3_knowledge USING GIN(tags);
CREATE INDEX idx_l3_knowledge_strength ON l3_knowledge(strength DESC);
CREATE INDEX idx_l3_knowledge_accessed ON l3_knowledge(last_accessed DESC NULLS LAST);
CREATE INDEX idx_l3_knowledge_embedding ON l3_knowledge USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_l3_knowledge_tsv ON l3_knowledge USING GIN(content_tsv);

-- Consolidation history
CREATE TABLE IF NOT EXISTS l3_consolidations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Consolidation type
    consolidation_type TEXT NOT NULL,  -- daily, weekly, manual

    -- Stats
    events_processed INT DEFAULT 0,
    concepts_created INT DEFAULT 0,
    concepts_updated INT DEFAULT 0,
    relations_created INT DEFAULT 0,

    -- LTP/LTD stats
    items_strengthened INT DEFAULT 0,
    items_weakened INT DEFAULT 0,
    items_deleted INT DEFAULT 0,

    -- Average strength before/after
    avg_strength_before REAL,
    avg_strength_after REAL,

    -- Model used
    model_used TEXT,  -- claude-3-5-sonnet, o3-deep-research, etc.

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INT,

    -- Results
    insights JSONB,
    error_message TEXT
);

CREATE INDEX idx_l3_consolidations_type ON l3_consolidations(consolidation_type);
CREATE INDEX idx_l3_consolidations_started ON l3_consolidations(started_at DESC);

-- ═══════════════════════════════════════════════════════════════════
-- SHARED TABLES
-- ═══════════════════════════════════════════════════════════════════

-- Sessions tracking
CREATE TABLE IF NOT EXISTS agi_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session info
    session_name TEXT,
    phase TEXT,  -- autonomous_mode, planning, coding, etc.

    -- Stats
    events_count INT DEFAULT 0,
    l1_items INT DEFAULT 0,
    l2_items INT DEFAULT 0,
    l3_items INT DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_agi_sessions_started ON agi_sessions(started_at DESC);
CREATE INDEX idx_agi_sessions_activity ON agi_sessions(last_activity DESC);

-- Cost tracking
CREATE TABLE IF NOT EXISTS agi_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Provider & model
    provider TEXT NOT NULL,  -- openai, anthropic, cohere, voyageai
    model TEXT NOT NULL,  -- gpt-5-nano, claude-3-5-sonnet, etc.

    -- Usage
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    tokens_cached INT DEFAULT 0,

    -- Cost (USD)
    cost_input DECIMAL(10, 6) DEFAULT 0,
    cost_output DECIMAL(10, 6) DEFAULT 0,
    cost_total DECIMAL(10, 6) DEFAULT 0,

    -- Context
    layer TEXT,  -- L1, L2, L3
    operation TEXT,  -- classify, analyze, consolidate, etc.
    session_id UUID,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agi_costs_provider ON agi_costs(provider);
CREATE INDEX idx_agi_costs_created ON agi_costs(created_at DESC);
CREATE INDEX idx_agi_costs_session ON agi_costs(session_id);

-- Roadmap/Tasks (pour stocker les 56 tâches!)
CREATE TABLE IF NOT EXISTS agi_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Task info
    phase TEXT NOT NULL,  -- Phase 1, Phase 2, etc.
    task_number INT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),

    -- Dependencies
    depends_on UUID[],  -- Other task IDs

    -- Metadata
    estimated_duration TEXT,  -- "2h", "1 day", etc.
    actual_duration_ms BIGINT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    UNIQUE(phase, task_number)
);

CREATE INDEX idx_agi_tasks_phase ON agi_tasks(phase);
CREATE INDEX idx_agi_tasks_status ON agi_tasks(status);
CREATE INDEX idx_agi_tasks_created ON agi_tasks(created_at);

-- ═══════════════════════════════════════════════════════════════════
-- TRIGGERS
-- ═══════════════════════════════════════════════════════════════════

-- Auto-update tsvector for L3 knowledge (BM25 search)
CREATE OR REPLACE FUNCTION l3_knowledge_tsv_trigger() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english',
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(NEW.content_compressed, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS l3_knowledge_tsv_update ON l3_knowledge;
CREATE TRIGGER l3_knowledge_tsv_update
BEFORE INSERT OR UPDATE ON l3_knowledge
FOR EACH ROW EXECUTE FUNCTION l3_knowledge_tsv_trigger();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS l3_knowledge_updated_at ON l3_knowledge;
CREATE TRIGGER l3_knowledge_updated_at
BEFORE UPDATE ON l3_knowledge
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════
-- VIEWS (Convenience)
-- ═══════════════════════════════════════════════════════════════════

-- Recent activity across all layers
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    'L1' as layer,
    id,
    event_type as type,
    content_preview as content,
    importance,
    created_at
FROM l1_events
WHERE created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'L2-Code' as layer,
    id,
    edit_type as type,
    content_preview as content,
    importance,
    created_at
FROM l2_code_edits
WHERE created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'L2-Text' as layer,
    id,
    memory_type as type,
    LEFT(content, 100) as content,
    importance,
    created_at
FROM l2_text_memory
WHERE created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'L3' as layer,
    id,
    knowledge_type as type,
    LEFT(content_compressed, 100) as content,
    importance,
    created_at
FROM l3_knowledge
WHERE created_at > NOW() - INTERVAL '7 days'

ORDER BY created_at DESC
LIMIT 100;

-- Cost summary by provider
CREATE OR REPLACE VIEW v_cost_summary AS
SELECT
    provider,
    model,
    layer,
    COUNT(*) as call_count,
    SUM(tokens_input) as total_input_tokens,
    SUM(tokens_output) as total_output_tokens,
    SUM(cost_total) as total_cost_usd,
    DATE(created_at) as date
FROM agi_costs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY provider, model, layer, DATE(created_at)
ORDER BY date DESC, total_cost_usd DESC;

-- ═══════════════════════════════════════════════════════════════════
-- INITIAL DATA
-- ═══════════════════════════════════════════════════════════════════

-- Create default session
INSERT INTO agi_sessions (id, session_name, phase)
VALUES (uuid_generate_v4(), 'Initial Setup', 'infrastructure')
ON CONFLICT DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════
-- STATISTICS
-- ═══════════════════════════════════════════════════════════════════

SELECT
    'AGI Memory System PostgreSQL Schemas Created!' as message,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'l%_%') as layer_tables,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'agi_%') as agi_tables;
