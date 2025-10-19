-- Migration 004: Add BM25 Full-Text Search to AGI Knowledge
--
-- Comme cerveau humain: recherche sémantique sans embeddings!
--
-- BM25 (Best Matching 25):
-- - Gratuit (vs embeddings $40-100/an)
-- - Rapide (<50ms vs embeddings 200ms)
-- - Intelligent (pondération TF-IDF)
-- - Local (vs API externe)

-- 1. Add tsvector column for full-text search
ALTER TABLE agi_knowledge
ADD COLUMN IF NOT EXISTS content_tsv tsvector;

-- 2. Create GIN index for fast search (comme index synaptique)
CREATE INDEX IF NOT EXISTS idx_agi_knowledge_tsv
ON agi_knowledge USING GIN(content_tsv);

-- 3. Populate existing data
UPDATE agi_knowledge
SET content_tsv = to_tsvector('english',
    COALESCE(content, '') || ' ' ||
    COALESCE(context::text, '') || ' ' ||
    COALESCE(array_to_string(tags, ' '), '')
);

-- 4. Create trigger for auto-update (comme LTP automatique!)
CREATE OR REPLACE FUNCTION agi_knowledge_tsv_trigger() RETURNS trigger AS $$
BEGIN
    NEW.content_tsv := to_tsvector('english',
        COALESCE(NEW.content, '') || ' ' ||
        COALESCE(NEW.context::text, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tsvector_update ON agi_knowledge;
CREATE TRIGGER tsvector_update
BEFORE INSERT OR UPDATE ON agi_knowledge
FOR EACH ROW EXECUTE FUNCTION agi_knowledge_tsv_trigger();

-- 5. Create BM25 search function
CREATE OR REPLACE FUNCTION search_bm25(
    query_text TEXT,
    result_limit INT DEFAULT 5
) RETURNS TABLE (
    id UUID,
    content TEXT,
    knowledge_type TEXT,
    tags TEXT[],
    rank REAL,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.id,
        k.content,
        k.knowledge_type,
        k.tags,
        ts_rank(k.content_tsv, websearch_to_tsquery('english', query_text)) AS rank,
        k.created_at
    FROM agi_knowledge k
    WHERE k.content_tsv @@ websearch_to_tsquery('english', query_text)
    ORDER BY rank DESC, k.created_at DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- 6. Statistics
SELECT
    count(*) as total_knowledge,
    count(content_tsv) as indexed_knowledge,
    pg_size_pretty(pg_total_relation_size('agi_knowledge')) as table_size,
    pg_size_pretty(pg_total_relation_size('idx_agi_knowledge_tsv')) as index_size
FROM agi_knowledge;

-- ✅ Migration complete
-- Prochaine étape: Mettre à jour memory_search() dans agi_tools_mcp.py
