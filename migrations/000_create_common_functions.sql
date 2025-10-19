-- ============================================================================
-- Migration 000: Create common functions (run first)
-- ============================================================================
-- Description: Common utility functions used by multiple migrations
-- Author: AGI System
-- Date: 2025-10-18
-- ============================================================================

BEGIN;

-- Function to auto-update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION update_updated_at_column() IS 'Auto-updates updated_at column on row modification';

COMMIT;
