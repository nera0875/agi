-- ============================================================================
-- Migration 003: Create agent_metrics table
-- ============================================================================
-- Description: Track execution metrics for ML-based smart routing
--              Learn optimal path (DB queue vs CLI direct) per agent type
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Agent identification
    agent_type TEXT NOT NULL,
    task_type TEXT NOT NULL,

    -- Execution data
    execution_path TEXT NOT NULL,
    duration_seconds NUMERIC(10, 3) NOT NULL,
    status TEXT NOT NULL,

    -- Resource usage
    tokens_used INTEGER,
    cost_dollars NUMERIC(10, 6),

    -- Context
    task_complexity TEXT,
    prompt_length INTEGER,
    result_length INTEGER,

    -- Error tracking
    error_type TEXT,
    error_message TEXT,

    -- Timestamp
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_execution_path CHECK (execution_path IN ('db_queue', 'cli_direct', 'cli_streaming')),
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
    CONSTRAINT valid_complexity CHECK (task_complexity IN ('simple', 'medium', 'complex') OR task_complexity IS NULL),
    CONSTRAINT positive_duration CHECK (duration_seconds >= 0)
);

-- Indexes for analytics queries
CREATE INDEX idx_agent_metrics_agent_type ON agent_metrics(agent_type);

CREATE INDEX idx_agent_metrics_execution_path ON agent_metrics(execution_path);

CREATE INDEX idx_agent_metrics_status ON agent_metrics(status);

CREATE INDEX idx_agent_metrics_timestamp ON agent_metrics(timestamp DESC);

-- Composite index for smart routing queries
CREATE INDEX idx_agent_metrics_routing_analysis
    ON agent_metrics(agent_type, execution_path, status, timestamp DESC);

-- Partitioning hint for future scaling (optional)
-- COMMENT ON TABLE agent_metrics IS 'Consider partitioning by timestamp (monthly) when >10M rows';

COMMIT;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP TABLE IF EXISTS agent_metrics CASCADE;
-- COMMIT;
