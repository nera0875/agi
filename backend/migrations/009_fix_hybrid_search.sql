-- Migration 009: Fix hybrid_search function to match Python code expectations
-- Python code expects: id, content, metadata, similarity_score

-- Update hybrid_search function with correct return structure
CREATE OR REPLACE FUNCTION hybrid_search(
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
            k.id,
            k.content,
            jsonb_build_object(
                'section', k.section,
                'tags', k.tags,
                'priority', k.priority,
                'created_at', k.created_at,
                'updated_at', k.updated_at
            ) as metadata,
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
            jsonb_build_object(
                'section', k.section,
                'tags', k.tags,
                'priority', k.priority,
                'created_at', k.created_at,
                'updated_at', k.updated_at
            ) as metadata,
            ts_rank(k.content_tsv, websearch_to_tsquery('english', query_text))::FLOAT AS bm25_score
        FROM agi_knowledge k
        WHERE k.content_tsv @@ websearch_to_tsquery('english', query_text)
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

-- ✅ Migration 009 complete
-- hybrid_search now returns: id, content, metadata, similarity_score
