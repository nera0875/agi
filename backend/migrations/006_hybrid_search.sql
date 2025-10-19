-- Migration 006: Hybrid Search (BM25 + Semantic)
--
-- Combine le meilleur des 2 mondes:
-- - BM25: recherche par mots-clés (rapide, gratuit)
-- - Semantic: recherche par sens (précis, intelligent)
--
-- Weighted hybrid: 0.3 * BM25 + 0.7 * semantic = résultats optimaux

-- 1. Create hybrid_search function (simplified for agi_knowledge table)
-- Note: This version uses ONLY BM25 since embedding column doesn't exist yet
-- TODO: Add semantic search when embeddings are implemented
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
    -- For now, just use BM25 full-text search
    -- When embeddings are added, we'll combine semantic + BM25
    RETURN QUERY
    SELECT
        k.id,
        k.content,
        k.section,
        k.tags,
        k.priority,
        ts_rank(k.content_tsv, websearch_to_tsquery('english', query_text))::FLOAT AS score,
        k.created_at,
        k.updated_at
    FROM agi_knowledge k
    WHERE k.content_tsv @@ websearch_to_tsquery('english', query_text)
    ORDER BY score DESC, k.created_at DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;

-- 3. Test the function (commented out - uncomment to test manually)
-- SELECT * FROM hybrid_search(
--     query_embedding := (SELECT embedding FROM agi_knowledge LIMIT 1),
--     query_text := 'test',
--     match_count := 5,
--     semantic_weight := 0.7,
--     bm25_weight := 0.3
-- );

-- ✅ Migration 006 complete
-- Hybrid search function created successfully
