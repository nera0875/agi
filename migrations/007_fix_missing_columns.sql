-- ============================================================================
-- Migration 007: Fix missing columns
-- ============================================================================
-- Description: Ajoute colonnes manquantes trouvées lors des tests E2E
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

-- Add resumed_at to agi_sessions if not exists
ALTER TABLE agi_sessions ADD COLUMN IF NOT EXISTS resumed_at TIMESTAMP;

-- Make task_type nullable in agent_metrics (optional field)
ALTER TABLE agent_metrics ALTER COLUMN task_type DROP NOT NULL;

COMMIT;
