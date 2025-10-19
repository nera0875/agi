-- ============================================================================
-- Migration 008: Create agi_knowledge and agi_roadmap tables
-- ============================================================================
-- Description: Tables pour la boucle d'auto-renforcement AGI
--              - agi_knowledge: Rules, patterns, learnings (remplace .md files)
--              - agi_roadmap: Actions planifiées avec priorités
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

-- ============================================================================
-- Table: agi_knowledge (Knowledge Base)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agi_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL, -- 'rule', 'pattern', 'learning', 'decision'

    -- Organization
    tags TEXT[] DEFAULT '{}',
    category TEXT,
    priority INTEGER NOT NULL DEFAULT 50,

    -- Relationships
    parent_id UUID REFERENCES agi_knowledge(id) ON DELETE CASCADE,
    related_ids UUID[] DEFAULT '{}',

    -- Quality metrics
    usage_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    quality_score NUMERIC(3, 2) DEFAULT 0.5, -- 0.0 - 1.0

    -- Metadata
    created_by TEXT DEFAULT 'sonnet',
    source TEXT, -- 'manual', 'auto-learned', 'research-agent', etc.
    verified BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_content_type CHECK (content_type IN ('rule', 'pattern', 'learning', 'decision', 'reference')),
    CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 100),
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0 AND quality_score <= 1)
);

-- Indexes for agi_knowledge
CREATE INDEX idx_agi_knowledge_tags ON agi_knowledge USING GIN(tags);
CREATE INDEX idx_agi_knowledge_content_type ON agi_knowledge(content_type);
CREATE INDEX idx_agi_knowledge_priority ON agi_knowledge(priority DESC);
CREATE INDEX idx_agi_knowledge_category ON agi_knowledge(category);
CREATE INDEX idx_agi_knowledge_quality_score ON agi_knowledge(quality_score DESC);
CREATE INDEX idx_agi_knowledge_parent_id ON agi_knowledge(parent_id) WHERE parent_id IS NOT NULL;

-- Full-text search
CREATE INDEX idx_agi_knowledge_content_search ON agi_knowledge USING GIN(to_tsvector('english', content));
CREATE INDEX idx_agi_knowledge_title_search ON agi_knowledge USING GIN(to_tsvector('english', title));

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_agi_knowledge_updated_at ON agi_knowledge;
CREATE TRIGGER update_agi_knowledge_updated_at
    BEFORE UPDATE ON agi_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Table: agi_roadmap (Action Planning)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agi_roadmap (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Action definition
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    action_type TEXT NOT NULL, -- 'research', 'implement', 'test', 'optimize', 'fix'

    -- Execution
    status TEXT NOT NULL DEFAULT 'planned', -- 'planned', 'active', 'blocked', 'completed', 'cancelled'
    priority INTEGER NOT NULL DEFAULT 50,
    estimated_duration_minutes INTEGER,

    -- Dependencies
    depends_on UUID[] DEFAULT '{}', -- IDs of other roadmap items
    blocks UUID[] DEFAULT '{}', -- IDs that this blocks

    -- Assignment
    assigned_to TEXT, -- 'sonnet', 'research-agent', 'code-agent', etc.
    batch_id UUID, -- If executed as part of a batch

    -- Context
    context JSONB DEFAULT '{}',
    success_criteria TEXT[],

    -- Results
    result JSONB,
    lessons_learned TEXT,
    knowledge_created UUID[], -- IDs in agi_knowledge

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    deadline TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_action_type CHECK (action_type IN ('research', 'implement', 'test', 'optimize', 'fix', 'document', 'review')),
    CONSTRAINT valid_status CHECK (status IN ('planned', 'active', 'blocked', 'completed', 'cancelled', 'failed')),
    CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 100)
);

-- Indexes for agi_roadmap
CREATE INDEX idx_agi_roadmap_status ON agi_roadmap(status)
    WHERE status IN ('planned', 'active', 'blocked');
CREATE INDEX idx_agi_roadmap_priority ON agi_roadmap(priority DESC, created_at ASC)
    WHERE status IN ('planned', 'active');
CREATE INDEX idx_agi_roadmap_action_type ON agi_roadmap(action_type);
CREATE INDEX idx_agi_roadmap_assigned_to ON agi_roadmap(assigned_to);
CREATE INDEX idx_agi_roadmap_deadline ON agi_roadmap(deadline ASC)
    WHERE deadline IS NOT NULL AND status NOT IN ('completed', 'cancelled');

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_agi_roadmap_updated_at ON agi_roadmap;
CREATE TRIGGER update_agi_roadmap_updated_at
    BEFORE UPDATE ON agi_roadmap
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to get next action from roadmap
CREATE OR REPLACE FUNCTION get_next_action()
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    action_type TEXT,
    priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.id,
        r.title,
        r.description,
        r.action_type,
        r.priority
    FROM agi_roadmap r
    WHERE r.status = 'active'
      -- Check dependencies are met
      AND NOT EXISTS (
          SELECT 1
          FROM unnest(r.depends_on) dep
          JOIN agi_roadmap dep_item ON dep_item.id = dep
          WHERE dep_item.status NOT IN ('completed', 'cancelled')
      )
    ORDER BY r.priority DESC, r.created_at ASC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function to search knowledge
CREATE OR REPLACE FUNCTION search_knowledge(
    search_query TEXT,
    filter_tags TEXT[] DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    content_type TEXT,
    quality_score NUMERIC,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        k.id,
        k.title,
        k.content,
        k.content_type,
        k.quality_score,
        ts_rank(
            to_tsvector('english', k.content || ' ' || k.title),
            plainto_tsquery('english', search_query)
        ) as rank
    FROM agi_knowledge k
    WHERE
        (filter_tags IS NULL OR k.tags && filter_tags)
        AND (
            to_tsvector('english', k.content || ' ' || k.title) @@
            plainto_tsquery('english', search_query)
        )
    ORDER BY rank DESC, k.quality_score DESC, k.priority DESC
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Function to increment knowledge usage
CREATE OR REPLACE FUNCTION increment_knowledge_usage(knowledge_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE agi_knowledge
    SET usage_count = usage_count + 1,
        last_accessed_at = NOW()
    WHERE id = knowledge_id;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP FUNCTION IF EXISTS get_next_action();
-- DROP FUNCTION IF EXISTS search_knowledge(TEXT, TEXT[], INTEGER);
-- DROP FUNCTION IF EXISTS increment_knowledge_usage(UUID);
-- DROP TABLE IF EXISTS agi_roadmap CASCADE;
-- DROP TABLE IF EXISTS agi_knowledge CASCADE;
-- COMMIT;
