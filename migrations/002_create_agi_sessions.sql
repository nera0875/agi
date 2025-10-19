-- ============================================================================
-- Migration 002: Create agi_sessions table
-- ============================================================================
-- Description: Store Sonnet brain state for pause/resume functionality
--              Enables AGI to save state, terminate, and resume later
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS agi_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session identity
    session_name TEXT NOT NULL,
    session_type TEXT NOT NULL DEFAULT 'development',

    -- Current state
    current_phase TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',

    -- Context preservation
    context JSONB NOT NULL DEFAULT '{}',
    launched_tasks UUID[] DEFAULT '{}',
    next_action TEXT,

    -- Progress tracking
    completed_phases TEXT[] DEFAULT '{}',
    total_tasks_launched INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,

    -- Metadata
    created_by TEXT DEFAULT 'sonnet',
    priority INTEGER NOT NULL DEFAULT 50,
    tags TEXT[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_invocation_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 100),
    CONSTRAINT valid_session_type CHECK (session_type IN ('development', 'production', 'testing', 'research'))
);

-- Indexes for fast queries
CREATE INDEX idx_agi_sessions_status ON agi_sessions(status)
    WHERE status IN ('active', 'paused');

CREATE INDEX idx_agi_sessions_session_type ON agi_sessions(session_type);

CREATE INDEX idx_agi_sessions_created_at ON agi_sessions(created_at DESC);

CREATE INDEX idx_agi_sessions_tags ON agi_sessions USING GIN(tags);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_agi_sessions_updated_at ON agi_sessions;
CREATE TRIGGER update_agi_sessions_updated_at
    BEFORE UPDATE ON agi_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP TABLE IF EXISTS agi_sessions CASCADE;
-- COMMIT;
