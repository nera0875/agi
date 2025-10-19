-- Migration 003: Create AGI Knowledge Table with BM25 Full-Text Search
--
-- This table stores consolidated knowledge from the AGI system
-- with full-text search capability using PostgreSQL tsvector and BM25 ranking

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Main AGI Knowledge table with embeddings and full-text search
CREATE TABLE IF NOT EXISTS agi_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Content
    content TEXT NOT NULL,
    context JSONB,  -- Additional context/metadata

    -- Classification
    knowledge_type TEXT NOT NULL,  -- pattern, architecture, decision, bug_fix, feature, etc.
    importance INT CHECK (importance >= 0 AND importance <= 10),
    tags TEXT[],

    -- Embeddings (Voyage AI v3: 1024 dimensions)
    embedding vector(1024),

    -- Full-text search (BM25)
    content_tsv tsvector,

    -- Quality metrics
    quality_score REAL DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,

    -- Source tracking
    source_url TEXT,
    source_model TEXT,  -- Which model generated/verified this knowledge

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_agi_knowledge_type ON agi_knowledge(knowledge_type);
CREATE INDEX idx_agi_knowledge_tags ON agi_knowledge USING GIN(tags);
CREATE INDEX idx_agi_knowledge_quality ON agi_knowledge(quality_score DESC);
CREATE INDEX idx_agi_knowledge_accessed ON agi_knowledge(last_accessed DESC NULLS LAST);
CREATE INDEX idx_agi_knowledge_embedding ON agi_knowledge USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_agi_knowledge_created ON agi_knowledge(created_at DESC);
CREATE INDEX idx_agi_knowledge_tsv ON agi_knowledge USING GIN(content_tsv);

-- Trigger: Auto-update tsvector for BM25 search
CREATE OR REPLACE FUNCTION agi_knowledge_tsv_trigger() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english',
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(NEW.knowledge_type, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agi_knowledge_tsv_update ON agi_knowledge;
CREATE TRIGGER agi_knowledge_tsv_update
BEFORE INSERT OR UPDATE ON agi_knowledge
FOR EACH ROW EXECUTE FUNCTION agi_knowledge_tsv_trigger();

-- Trigger: Auto-update updated_at
CREATE OR REPLACE FUNCTION agi_knowledge_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agi_knowledge_updated_at_trigger ON agi_knowledge;
CREATE TRIGGER agi_knowledge_updated_at_trigger
BEFORE UPDATE ON agi_knowledge
FOR EACH ROW EXECUTE FUNCTION agi_knowledge_updated_at();

-- Function: BM25 search with optional filters
CREATE OR REPLACE FUNCTION search_agi_bm25(
    query_text TEXT,
    result_limit INT DEFAULT 20,
    knowledge_type_filter TEXT DEFAULT NULL,
    tag_filter TEXT[] DEFAULT NULL
) RETURNS TABLE (
    id UUID,
    content TEXT,
    knowledge_type TEXT,
    tags TEXT[],
    quality_score REAL,
    bm25_rank REAL,
    created_at TIMESTAMPTZ
) AS $$
DECLARE
    v_tsquery tsquery;
BEGIN
    v_tsquery := websearch_to_tsquery('english', query_text);

    RETURN QUERY
    SELECT
        k.id,
        k.content,
        k.knowledge_type,
        k.tags,
        k.quality_score,
        ts_rank_cd(k.content_tsv, v_tsquery) AS bm25_rank,
        k.created_at
    FROM agi_knowledge k
    WHERE k.content_tsv @@ v_tsquery
      AND (knowledge_type_filter IS NULL OR k.knowledge_type = knowledge_type_filter)
      AND (tag_filter IS NULL OR k.tags && tag_filter)
    ORDER BY bm25_rank DESC, k.quality_score DESC, k.created_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Statistics
SELECT
    'AGI Knowledge table created with BM25 support!' as status,
    count(*) as total_records,
    pg_size_pretty(pg_total_relation_size('agi_knowledge')) as table_size
FROM agi_knowledge;
