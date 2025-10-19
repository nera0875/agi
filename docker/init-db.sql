-- AGI System Database Initialization
-- PostgreSQL 16 + pgvector extension
-- Created: 2025-10-15

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Trigram similarity for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Full-text search optimization
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- LANGGRAPH CHECKPOINTER TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at DESC);

COMMENT ON TABLE checkpoints IS 'LangGraph stateful agent checkpoints for conversation persistence';

-- ============================================================================
-- MEMORY STORE (RAG VECTOR STORAGE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_store (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(1024),  -- Voyage AI voyage-3 dimension
    content_tsv tsvector,    -- Full-text search vector (BM25)
    source_type TEXT,        -- document, conversation, user_input, etc.
    user_id TEXT,            -- For multi-tenant isolation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector similarity index (IVFFlat for approximate nearest neighbor)
CREATE INDEX IF NOT EXISTS idx_memory_embedding
ON memory_store USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Metadata JSONB index (GIN for fast lookup)
CREATE INDEX IF NOT EXISTS idx_memory_metadata
ON memory_store USING gin (metadata);

-- Full-text search index (BM25)
CREATE INDEX IF NOT EXISTS idx_memory_content_tsv
ON memory_store USING gin(content_tsv);

-- Timestamp indexes for time-based queries
CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory_store(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_updated_at ON memory_store(updated_at DESC);

-- User isolation index (multi-tenant)
CREATE INDEX IF NOT EXISTS idx_memory_user_id ON memory_store(user_id);

-- Source type index
CREATE INDEX IF NOT EXISTS idx_memory_source_type ON memory_store(source_type);

COMMENT ON TABLE memory_store IS 'Hybrid vector + full-text search storage for RAG system';
COMMENT ON COLUMN memory_store.embedding IS 'Voyage AI voyage-3 embeddings (1024 dimensions)';
COMMENT ON COLUMN memory_store.content_tsv IS 'tsvector for BM25 full-text search (RRF fusion)';

-- ============================================================================
-- TRIGGER: AUTO-UPDATE TSVECTOR FOR BM25
-- ============================================================================

CREATE OR REPLACE FUNCTION memory_store_tsvector_update()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english', COALESCE(NEW.content, ''));
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_memory_tsvector_update
    BEFORE INSERT OR UPDATE OF content ON memory_store
    FOR EACH ROW EXECUTE FUNCTION memory_store_tsvector_update();

-- ============================================================================
-- GRAPH RELATIONS (REPLACES NEO4J)
-- ============================================================================

CREATE TABLE IF NOT EXISTS relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES memory_store(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES memory_store(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,  -- RELATES_TO, DEPENDS_ON, CONTRADICTS, etc.
    metadata JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,     -- Relation strength
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_no_self_relation CHECK (source_id != target_id)
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_relations_weight ON relations(weight DESC);

COMMENT ON TABLE relations IS 'Graph relations between memory nodes (replaces Neo4j)';

-- ============================================================================
-- SESSION MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    thread_id TEXT UNIQUE NOT NULL,  -- Links to checkpoints.thread_id
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_thread_id ON sessions(thread_id);
CREATE INDEX IF NOT EXISTS idx_sessions_last_active ON sessions(last_active_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

COMMENT ON TABLE sessions IS 'User conversation sessions management';

-- ============================================================================
-- ROW-LEVEL SECURITY (MULTI-TENANT ISOLATION)
-- ============================================================================

-- Enable RLS on sensitive tables (optional, activated later)
ALTER TABLE memory_store ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Example policy (commented, activate when multi-tenant needed)
-- CREATE POLICY memory_user_isolation ON memory_store
--     USING (user_id = current_setting('app.current_user_id', TRUE));

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Cosine similarity search with hybrid RRF
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1024),
    query_text text,
    match_count int DEFAULT 10,
    semantic_weight float DEFAULT 0.7,
    bm25_weight float DEFAULT 0.3
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT
            m.id,
            m.content,
            m.metadata,
            1 - (m.embedding <=> query_embedding) AS score,
            ROW_NUMBER() OVER (ORDER BY m.embedding <=> query_embedding) AS rank
        FROM memory_store m
        WHERE m.embedding IS NOT NULL
        ORDER BY m.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    bm25_results AS (
        SELECT
            m.id,
            m.content,
            m.metadata,
            ts_rank_cd(m.content_tsv, plainto_tsquery('english', query_text)) AS score,
            ROW_NUMBER() OVER (ORDER BY ts_rank_cd(m.content_tsv, plainto_tsquery('english', query_text)) DESC) AS rank
        FROM memory_store m
        WHERE m.content_tsv @@ plainto_tsquery('english', query_text)
        ORDER BY score DESC
        LIMIT match_count * 2
    ),
    rrf_fusion AS (
        SELECT
            COALESCE(s.id, b.id) AS id,
            COALESCE(s.content, b.content) AS content,
            COALESCE(s.metadata, b.metadata) AS metadata,
            (COALESCE(semantic_weight / (60 + s.rank), 0) +
             COALESCE(bm25_weight / (60 + b.rank), 0)) AS rrf_score
        FROM semantic_results s
        FULL OUTER JOIN bm25_results b ON s.id = b.id
    )
    SELECT
        rf.id,
        rf.content,
        rf.metadata,
        rf.rrf_score AS similarity_score
    FROM rrf_fusion rf
    ORDER BY rf.rrf_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION hybrid_search IS 'RRF (Reciprocal Rank Fusion) hybrid search: 70% semantic + 30% BM25';

-- Function: Graph traversal (recursive CTE)
CREATE OR REPLACE FUNCTION get_related_memories(
    start_id UUID,
    max_depth int DEFAULT 3,
    relation_filter text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    relation_path TEXT[],
    depth INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE related AS (
        SELECT
            m.id,
            m.content,
            ARRAY[r.relation_type] AS relation_path,
            1 AS depth
        FROM memory_store m
        JOIN relations r ON m.id = r.target_id
        WHERE r.source_id = start_id
          AND (relation_filter IS NULL OR r.relation_type = relation_filter)

        UNION ALL

        SELECT
            m.id,
            m.content,
            rel.relation_path || r.relation_type,
            rel.depth + 1
        FROM memory_store m
        JOIN relations r ON m.id = r.target_id
        JOIN related rel ON r.source_id = rel.id
        WHERE rel.depth < max_depth
          AND (relation_filter IS NULL OR r.relation_type = relation_filter)
    )
    SELECT DISTINCT ON (related.id)
        related.id,
        related.content,
        related.relation_path,
        related.depth
    FROM related
    ORDER BY related.id, related.depth;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_related_memories IS 'Graph traversal using recursive CTE (replaces Neo4j queries)';

-- ============================================================================
-- INITIAL DATA & VERIFICATION
-- ============================================================================

-- Verify extensions
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension not installed';
    END IF;
    RAISE NOTICE 'Database initialized successfully with pgvector support';
END $$;
