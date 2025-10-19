-- Migration 008: Add embeddings column to agi_knowledge
-- Enable semantic search with Voyage AI embeddings (1024 dimensions)

-- Add embedding column (voyage-3 uses 1024 dimensions)
ALTER TABLE agi_knowledge
ADD COLUMN IF NOT EXISTS embedding vector(1024);

-- Create index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_agi_knowledge_embedding
ON agi_knowledge
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Update hybrid_search function to include semantic search
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1024),
    query_text TEXT,
    match_count INT DEFAULT 10,
    semantic_weight FLOAT DEFAULT 0.7,
    bm25_weight FLOAT DEFAULT 0.3
) RETURNS TABLE (
    id UUID,
    content TEXT,
    section TEXT,
    tags TEXT[],
    priority INT,
    score FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT
            k.id,
            k.content,
            k.section,
            k.tags,
            k.priority,
            k.created_at,
            k.updated_at,
            1 - (k.embedding <=> query_embedding) AS semantic_score
        FROM agi_knowledge k
        WHERE k.embedding IS NOT NULL
        ORDER BY k.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    bm25_results AS (
        SELECT
            k.id,
            k.content,
            k.section,
            k.tags,
            k.priority,
            k.created_at,
            k.updated_at,
            ts_rank(k.content_tsv, websearch_to_tsquery('english', query_text))::FLOAT AS bm25_score
        FROM agi_knowledge k
        WHERE k.content_tsv @@ websearch_to_tsquery('english', query_text)
        ORDER BY bm25_score DESC
        LIMIT match_count * 2
    ),
    combined AS (
        SELECT
            COALESCE(s.id, b.id) AS id,
            COALESCE(s.content, b.content) AS content,
            COALESCE(s.section, b.section) AS section,
            COALESCE(s.tags, b.tags) AS tags,
            COALESCE(s.priority, b.priority) AS priority,
            COALESCE(s.created_at, b.created_at) AS created_at,
            COALESCE(s.updated_at, b.updated_at) AS updated_at,
            (COALESCE(s.semantic_score, 0) * semantic_weight +
             COALESCE(b.bm25_score, 0) * bm25_weight) AS final_score
        FROM semantic_results s
        FULL OUTER JOIN bm25_results b ON s.id = b.id
    )
    SELECT * FROM combined
    ORDER BY final_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- ✅ Migration 008 complete
-- Embeddings column and hybrid search ready
