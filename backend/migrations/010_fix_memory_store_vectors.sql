-- Migration 010: Fix memory_store for vector search
-- Change embedding column from TEXT to vector(1024)
-- Add full-text search support
-- Create hybrid_search function for memory_store

-- 1. Backup existing data (embeddings stored as text will be lost, need regeneration)
-- Note: Existing text embeddings can't be directly converted to vector type

-- 2. Drop old embedding column and recreate as vector
ALTER TABLE memory_store DROP COLUMN IF EXISTS embedding CASCADE;
ALTER TABLE memory_store ADD COLUMN embedding vector(1024);

-- 3. Add full-text search column for BM25
ALTER TABLE memory_store ADD COLUMN IF NOT EXISTS content_tsv tsvector;

-- 4. Create trigger for automatic tsvector updates
CREATE OR REPLACE FUNCTION memory_store_tsv_trigger() RETURNS trigger AS $$
BEGIN
  NEW.content_tsv := to_tsvector('english', NEW.content);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_memory_update ON memory_store;
CREATE TRIGGER tsvector_memory_update
BEFORE INSERT OR UPDATE ON memory_store
FOR EACH ROW EXECUTE FUNCTION memory_store_tsv_trigger();

-- 5. Update existing rows
UPDATE memory_store SET content_tsv = to_tsvector('english', content)
WHERE content_tsv IS NULL;

-- 6. Create indexes
CREATE INDEX IF NOT EXISTS idx_memory_embedding
ON memory_store
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_memory_tsv
ON memory_store
USING gin (content_tsv);

-- 7. Create hybrid_search function for memory_store
CREATE OR REPLACE FUNCTION hybrid_search_memory(
    query_embedding vector(1024),
    query_text TEXT,
    match_count INT DEFAULT 10,
    semantic_weight FLOAT DEFAULT 0.7,
    bm25_weight FLOAT DEFAULT 0.3
) RETURNS TABLE (
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
            1 - (m.embedding <=> query_embedding) AS semantic_score
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
            ts_rank(m.content_tsv, websearch_to_tsquery('english', query_text))::FLOAT AS bm25_score
        FROM memory_store m
        WHERE m.content_tsv @@ websearch_to_tsquery('english', query_text)
        ORDER BY bm25_score DESC
        LIMIT match_count * 2
    ),
    combined AS (
        SELECT
            COALESCE(s.id, b.id) AS comb_id,
            COALESCE(s.content, b.content) AS comb_content,
            COALESCE(s.metadata, b.metadata) AS comb_metadata,
            (COALESCE(s.semantic_score, 0) * semantic_weight +
             COALESCE(b.bm25_score, 0) * bm25_weight) AS final_score
        FROM semantic_results s
        FULL OUTER JOIN bm25_results b ON s.id = b.id
    )
    SELECT
        comb_id as id,
        comb_content as content,
        comb_metadata as metadata,
        final_score as similarity_score
    FROM combined
    ORDER BY final_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- ✅ Migration 010 complete
-- memory_store now supports hybrid search (semantic + BM25)
-- Note: Existing embeddings need to be regenerated
