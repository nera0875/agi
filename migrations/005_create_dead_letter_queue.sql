-- ============================================================================
-- Migration 005: Create dead_letter_queue table
-- ============================================================================
-- Description: Store tasks that failed after max retries
--              Prevent loss of failed tasks, enable manual intervention
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Original task reference
    original_task_id UUID NOT NULL,
    task_type TEXT NOT NULL,
    instructions JSONB NOT NULL,

    -- Failure tracking
    failure_reason TEXT NOT NULL,
    retry_count INTEGER NOT NULL,
    last_error TEXT,
    all_errors JSONB,  -- Array of all error messages from retries

    -- Context for debugging
    batch_id UUID,
    session_id UUID,
    agent_type TEXT,

    -- Resolution tracking
    status TEXT NOT NULL DEFAULT 'pending',
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'investigating', 'resolved', 'ignored', 'requeued'))
);

-- Indexes
CREATE INDEX idx_dlq_status ON dead_letter_queue(status)
    WHERE status IN ('pending', 'investigating');

CREATE INDEX idx_dlq_task_type ON dead_letter_queue(task_type);

CREATE INDEX idx_dlq_agent_type ON dead_letter_queue(agent_type);

CREATE INDEX idx_dlq_created_at ON dead_letter_queue(created_at DESC);

CREATE INDEX idx_dlq_batch_id ON dead_letter_queue(batch_id)
    WHERE batch_id IS NOT NULL;

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_dlq_updated_at ON dead_letter_queue;
CREATE TRIGGER update_dlq_updated_at
    BEFORE UPDATE ON dead_letter_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP TABLE IF EXISTS dead_letter_queue CASCADE;
-- COMMIT;
