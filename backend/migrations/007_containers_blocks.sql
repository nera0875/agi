-- Migration 007: Time Blocking Containers & Blocks System
-- Description: Tables for Asperger-friendly time blocking with strict limits

-- ============================================================================
-- CONTAINERS TABLE
-- Container = Project with hard time limit (e.g., "Frontend Refactor" - 90min)
-- ============================================================================
CREATE TABLE IF NOT EXISTS containers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    total_duration INTEGER NOT NULL, -- Minutes (HARD LIMIT)
    pause_after INTEGER NOT NULL DEFAULT 10, -- Auto pause duration in minutes
    status VARCHAR(50) NOT NULL DEFAULT 'idle', -- idle | locked | completed
    locked BOOLEAN NOT NULL DEFAULT FALSE, -- true = running, cannot modify
    progress INTEGER NOT NULL DEFAULT 0, -- Minutes elapsed
    current_block_index INTEGER NOT NULL DEFAULT 0,
    color VARCHAR(7), -- Hex color (e.g., #000000)
    is_template BOOLEAN NOT NULL DEFAULT TRUE, -- Template vs active instance
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Constraints
    CONSTRAINT progress_within_total CHECK (progress <= total_duration),
    CONSTRAINT valid_status CHECK (status IN ('idle', 'locked', 'completed'))
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_containers_status ON containers(status);
CREATE INDEX IF NOT EXISTS idx_containers_locked ON containers(locked);
CREATE INDEX IF NOT EXISTS idx_containers_created_at ON containers(created_at DESC);

-- ============================================================================
-- BLOCKS TABLE
-- Block = Task segment within container (e.g., "Frontend" - 30min)
-- ============================================================================
CREATE TABLE IF NOT EXISTS blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    container_id UUID NOT NULL REFERENCES containers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    duration INTEGER NOT NULL, -- Minutes
    position INTEGER NOT NULL, -- Order in container (0, 1, 2, ...)
    color VARCHAR(7), -- Hex color for UI
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_duration CHECK (duration > 0),
    CONSTRAINT valid_position CHECK (position >= 0),
    UNIQUE(container_id, position) -- No duplicate positions in same container
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_blocks_container ON blocks(container_id);
CREATE INDEX IF NOT EXISTS idx_blocks_position ON blocks(container_id, position);

-- ============================================================================
-- TASKS TABLE
-- Task = Sub-item within block (optional, for checklist)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_id UUID NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Constraints
    CONSTRAINT completed_at_requires_completed CHECK (
        (completed = TRUE AND completed_at IS NOT NULL) OR
        (completed = FALSE AND completed_at IS NULL)
    )
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_tasks_block ON tasks(block_id);
CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);

-- ============================================================================
-- VALIDATION FUNCTION
-- Ensures blocks total duration doesn't exceed container total_duration
-- ============================================================================
CREATE OR REPLACE FUNCTION validate_blocks_duration()
RETURNS TRIGGER AS $$
DECLARE
    container_total INTEGER;
    blocks_total INTEGER;
BEGIN
    -- Get container total duration
    SELECT total_duration INTO container_total
    FROM containers
    WHERE id = NEW.container_id;

    -- Calculate total blocks duration
    SELECT COALESCE(SUM(duration), 0) INTO blocks_total
    FROM blocks
    WHERE container_id = NEW.container_id;

    -- Check if exceeds
    IF blocks_total > container_total THEN
        RAISE EXCEPTION 'Blocks total duration (% min) exceeds container limit (% min)',
            blocks_total, container_total;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to validate on INSERT/UPDATE
DROP TRIGGER IF EXISTS trigger_validate_blocks_duration ON blocks;
CREATE TRIGGER trigger_validate_blocks_duration
    BEFORE INSERT OR UPDATE ON blocks
    FOR EACH ROW
    EXECUTE FUNCTION validate_blocks_duration();

-- ============================================================================
-- HELPER FUNCTION: Get container with all blocks and tasks
-- ============================================================================
CREATE OR REPLACE FUNCTION get_container_full(container_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'id', c.id,
        'name', c.name,
        'totalDuration', c.total_duration,
        'pauseAfter', c.pause_after,
        'status', c.status,
        'locked', c.locked,
        'progress', c.progress,
        'currentBlockIndex', c.current_block_index,
        'color', c.color,
        'isTemplate', c.is_template,
        'createdAt', c.created_at,
        'startedAt', c.started_at,
        'completedAt', c.completed_at,
        'blocks', COALESCE(
            (
                SELECT json_agg(
                    json_build_object(
                        'id', b.id,
                        'name', b.name,
                        'duration', b.duration,
                        'position', b.position,
                        'color', b.color,
                        'tasks', COALESCE(
                            (
                                SELECT json_agg(
                                    json_build_object(
                                        'id', t.id,
                                        'title', t.title,
                                        'description', t.description,
                                        'completed', t.completed,
                                        'blockId', t.block_id,
                                        'createdAt', t.created_at,
                                        'completedAt', t.completed_at
                                    )
                                    ORDER BY t.created_at
                                )
                                FROM tasks t
                                WHERE t.block_id = b.id
                            ),
                            '[]'::json
                        )
                    )
                    ORDER BY b.position
                )
                FROM blocks b
                WHERE b.container_id = c.id
            ),
            '[]'::json
        )
    ) INTO result
    FROM containers c
    WHERE c.id = container_uuid;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- HELPER FUNCTION: Get all containers (lightweight, without blocks/tasks)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_all_containers()
RETURNS SETOF containers AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM containers
    ORDER BY created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================
-- Uncomment to insert sample data:
/*
INSERT INTO containers (name, total_duration, pause_after) VALUES
    ('Morning Deep Work', 90, 15),
    ('Afternoon Sprint', 60, 10)
RETURNING id;

-- Get the IDs and insert blocks manually
*/

COMMENT ON TABLE containers IS 'Time blocking containers (projects with hard time limits)';
COMMENT ON TABLE blocks IS 'Task blocks within containers (e.g., Frontend, Backend, Tests)';
COMMENT ON TABLE tasks IS 'Optional checklist items within blocks';
COMMENT ON FUNCTION validate_blocks_duration() IS 'Ensures blocks total duration never exceeds container limit';
COMMENT ON FUNCTION get_container_full(UUID) IS 'Returns container with all nested blocks and tasks as JSON';
COMMENT ON FUNCTION get_all_containers() IS 'Returns all containers (lightweight, no blocks/tasks)';
