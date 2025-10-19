-- ============================================================================
-- Migration 001: Enhance worker_tasks for Production AGI
-- ============================================================================
-- Description: Add missing columns, indexes, and constraints for bulletproof
--              task queue with priority, timeout, retry logic
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

-- 1. Add missing columns if not exist
ALTER TABLE worker_tasks
    ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 50,
    ADD COLUMN IF NOT EXISTS timeout_seconds INTEGER NOT NULL DEFAULT 300,
    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS worker_id INTEGER,
    ADD COLUMN IF NOT EXISTS batch_id UUID,
    ADD COLUMN IF NOT EXISTS estimated_duration INTEGER,
    ADD COLUMN IF NOT EXISTS metadata JSONB;

-- 2. Add constraints (skip if exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_priority') THEN
        ALTER TABLE worker_tasks ADD CONSTRAINT valid_priority CHECK (priority >= 0 AND priority <= 100);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_timeout') THEN
        ALTER TABLE worker_tasks ADD CONSTRAINT valid_timeout CHECK (timeout_seconds > 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_retry_count') THEN
        ALTER TABLE worker_tasks ADD CONSTRAINT valid_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_status_enhanced') THEN
        ALTER TABLE worker_tasks ADD CONSTRAINT valid_status_enhanced CHECK (status IN ('pending', 'running', 'success', 'failed', 'timeout', 'cancelled'));
    END IF;
END$$;

-- 3. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_worker_tasks_status_priority
    ON worker_tasks(status, priority DESC, created_at ASC)
    WHERE status IN ('pending', 'running');

CREATE INDEX IF NOT EXISTS idx_worker_tasks_batch_id
    ON worker_tasks(batch_id)
    WHERE batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_worker_tasks_worker_id
    ON worker_tasks(worker_id)
    WHERE worker_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_worker_tasks_created_at
    ON worker_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_worker_tasks_completed_at
    ON worker_tasks(completed_at DESC)
    WHERE completed_at IS NOT NULL;

-- 4. Create updated_at trigger if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_worker_tasks_updated_at ON worker_tasks;
CREATE TRIGGER update_worker_tasks_updated_at
    BEFORE UPDATE ON worker_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
-- BEGIN;
-- DROP TRIGGER IF EXISTS update_worker_tasks_updated_at ON worker_tasks;
-- DROP INDEX IF EXISTS idx_worker_tasks_status_priority;
-- DROP INDEX IF EXISTS idx_worker_tasks_batch_id;
-- DROP INDEX IF EXISTS idx_worker_tasks_worker_id;
-- DROP INDEX IF EXISTS idx_worker_tasks_created_at;
-- DROP INDEX IF EXISTS idx_worker_tasks_completed_at;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS priority;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS timeout_seconds;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS retry_count;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS max_retries;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS worker_id;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS batch_id;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS estimated_duration;
-- ALTER TABLE worker_tasks DROP COLUMN IF EXISTS metadata;
-- COMMIT;
