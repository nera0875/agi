-- ============================================================================
-- Migration 004: Create circuit_breakers table
-- ============================================================================
-- Description: Track agent health and auto-disable failing agents
--              Prevent cascade failures by opening circuit on high error rate
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS circuit_breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Circuit identity
    agent_type TEXT NOT NULL UNIQUE,

    -- Circuit state
    status TEXT NOT NULL DEFAULT 'closed',
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    half_open_at TIMESTAMP,

    -- Failure tracking
    failure_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,

    -- Thresholds (configurable per agent)
    failure_threshold NUMERIC(3, 2) NOT NULL DEFAULT 0.5,  -- 50% failure rate
    min_requests INTEGER NOT NULL DEFAULT 10,  -- Minimum requests before opening
    timeout_seconds INTEGER NOT NULL DEFAULT 300,  -- 5min cooldown

    -- Last measurements
    last_failure_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_check_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Metadata
    reason TEXT,
    alert_sent BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('open', 'closed', 'half_open')),
    CONSTRAINT valid_threshold CHECK (failure_threshold > 0 AND failure_threshold <= 1),
    CONSTRAINT positive_counts CHECK (failure_count >= 0 AND success_count >= 0)
);

-- Indexes
CREATE INDEX idx_circuit_breakers_status ON circuit_breakers(status);

CREATE INDEX idx_circuit_breakers_agent_type ON circuit_breakers(agent_type);

CREATE INDEX idx_circuit_breakers_last_check ON circuit_breakers(last_check_at DESC);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_circuit_breakers_updated_at ON circuit_breakers;
CREATE TRIGGER update_circuit_breakers_updated_at
    BEFORE UPDATE ON circuit_breakers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Initialize circuit breakers for all known agents
INSERT INTO circuit_breakers (agent_type, status)
SELECT DISTINCT agent_type, 'closed'
FROM agent_prompts
ON CONFLICT (agent_type) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK
-- ============================================================================
-- BEGIN;
-- DROP TABLE IF EXISTS circuit_breakers CASCADE;
-- COMMIT;
