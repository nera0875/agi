-- ============================================================================
-- Migration 006: Create LISTEN/NOTIFY triggers for real-time events
-- ============================================================================
-- Description: Auto-notify continuation daemon when events occur
--              <50ms latency vs 2000ms polling - 40x faster
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

-- ============================================================================
-- FUNCTION: Check if all tasks in batch are complete
-- ============================================================================
CREATE OR REPLACE FUNCTION check_batch_completion()
RETURNS TRIGGER AS $$
DECLARE
    pending_count INTEGER;
    batch_session_id UUID;
    batch_context JSONB;
BEGIN
    -- Only process if task has batch_id
    IF NEW.batch_id IS NULL THEN
        RETURN NEW;
    END IF;

    -- Count remaining pending/running tasks in same batch
    SELECT COUNT(*) INTO pending_count
    FROM worker_tasks
    WHERE batch_id = NEW.batch_id
      AND status IN ('pending', 'running');

    -- If all tasks complete, notify continuation daemon
    IF pending_count = 0 THEN
        -- Get session context from any task in batch
        SELECT
            (instructions->'session_id')::text,
            instructions->'context'
        INTO
            batch_session_id,
            batch_context
        FROM worker_tasks
        WHERE batch_id = NEW.batch_id
        LIMIT 1;

        -- NOTIFY with batch completion event
        PERFORM pg_notify(
            'batch_complete',
            json_build_object(
                'batch_id', NEW.batch_id,
                'session_id', batch_session_id,
                'context', batch_context,
                'completed_at', NOW(),
                'total_tasks', (
                    SELECT COUNT(*)
                    FROM worker_tasks
                    WHERE batch_id = NEW.batch_id
                ),
                'success_count', (
                    SELECT COUNT(*)
                    FROM worker_tasks
                    WHERE batch_id = NEW.batch_id
                      AND status = 'success'
                ),
                'failed_count', (
                    SELECT COUNT(*)
                    FROM worker_tasks
                    WHERE batch_id = NEW.batch_id
                      AND status IN ('failed', 'timeout')
                )
            )::text
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Notify on task completion
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_batch_completion ON worker_tasks;
CREATE TRIGGER trigger_batch_completion
    AFTER UPDATE ON worker_tasks
    FOR EACH ROW
    WHEN (
        NEW.status IN ('success', 'failed', 'timeout', 'cancelled')
        AND OLD.status IN ('pending', 'running')
    )
    EXECUTE FUNCTION check_batch_completion();

-- ============================================================================
-- FUNCTION: Notify on individual task completion
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_task_completion()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'task_completed',
        json_build_object(
            'task_id', NEW.id,
            'task_type', NEW.task_type,
            'status', NEW.status,
            'batch_id', NEW.batch_id,
            'worker_id', NEW.worker_id,
            'duration_seconds', EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)),
            'completed_at', NEW.completed_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Notify on each task completion
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_task_completion ON worker_tasks;
CREATE TRIGGER trigger_task_completion
    AFTER UPDATE ON worker_tasks
    FOR EACH ROW
    WHEN (
        NEW.status IN ('success', 'failed', 'timeout')
        AND OLD.status = 'running'
        AND NEW.completed_at IS NOT NULL
    )
    EXECUTE FUNCTION notify_task_completion();

-- ============================================================================
-- FUNCTION: Notify on critical errors
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_critical_error()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify on failures after retries exhausted
    IF NEW.retry_count >= NEW.max_retries AND NEW.status = 'failed' THEN
        PERFORM pg_notify(
            'critical_error',
            json_build_object(
                'task_id', NEW.id,
                'task_type', NEW.task_type,
                'agent_type', NEW.instructions->>'agent_type',
                'error', NEW.error,
                'retry_count', NEW.retry_count,
                'batch_id', NEW.batch_id
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Notify on critical errors
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_critical_error ON worker_tasks;
CREATE TRIGGER trigger_critical_error
    AFTER UPDATE ON worker_tasks
    FOR EACH ROW
    WHEN (NEW.status = 'failed')
    EXECUTE FUNCTION notify_critical_error();

-- ============================================================================
-- FUNCTION: Notify on circuit breaker state change
-- ============================================================================
CREATE OR REPLACE FUNCTION notify_circuit_breaker_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify when status changes
    IF NEW.status != OLD.status THEN
        PERFORM pg_notify(
            'circuit_breaker_changed',
            json_build_object(
                'agent_type', NEW.agent_type,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'reason', NEW.reason,
                'failure_count', NEW.failure_count,
                'success_count', NEW.success_count
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Notify on circuit breaker changes
-- ============================================================================
DROP TRIGGER IF EXISTS trigger_circuit_breaker_change ON circuit_breakers;
CREATE TRIGGER trigger_circuit_breaker_change
    AFTER UPDATE ON circuit_breakers
    FOR EACH ROW
    EXECUTE FUNCTION notify_circuit_breaker_change();

-- ============================================================================
-- FUNCTION: Manual trigger for continuation (for testing/debugging)
-- ============================================================================
CREATE OR REPLACE FUNCTION trigger_manual_continuation(p_session_id UUID, p_phase TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM pg_notify(
        'manual_trigger',
        json_build_object(
            'session_id', p_session_id,
            'phase', p_phase,
            'triggered_at', NOW(),
            'triggered_by', current_user
        )::text
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- HELPER: View active listeners (for debugging)
-- ============================================================================
-- Note: pg_listening_channels() not available in all PostgreSQL versions
-- Alternative: query pg_stat_activity for LISTEN commands
COMMENT ON DATABASE agi_db IS 'Active listeners can be queried via: SELECT * FROM pg_stat_activity WHERE query LIKE ''%LISTEN%''';

COMMIT;

-- ============================================================================
-- TESTING (run after migration)
-- ============================================================================
-- -- Test manual trigger
-- SELECT trigger_manual_continuation(gen_random_uuid(), 'test_phase');
--
-- -- View active listeners
-- SELECT * FROM active_listeners;
--
-- -- Listen in psql:
-- LISTEN batch_complete;
-- LISTEN task_completed;
-- LISTEN critical_error;
-- LISTEN circuit_breaker_changed;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP TRIGGER IF EXISTS trigger_batch_completion ON worker_tasks;
-- DROP TRIGGER IF EXISTS trigger_task_completion ON worker_tasks;
-- DROP TRIGGER IF EXISTS trigger_critical_error ON worker_tasks;
-- DROP TRIGGER IF EXISTS trigger_circuit_breaker_change ON circuit_breakers;
-- DROP FUNCTION IF EXISTS check_batch_completion();
-- DROP FUNCTION IF EXISTS notify_task_completion();
-- DROP FUNCTION IF EXISTS notify_critical_error();
-- DROP FUNCTION IF EXISTS notify_circuit_breaker_change();
-- DROP FUNCTION IF EXISTS trigger_manual_continuation(UUID, TEXT);
-- DROP VIEW IF EXISTS active_listeners;
-- COMMIT;
