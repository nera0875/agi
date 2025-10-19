-- AGI Task System Tables
-- Migration 001: Core task management with learning capabilities
-- Date: 2025-10-16

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Tasks table: Core task storage with semantic embeddings
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'done', 'blocked', 'deferred', 'cancelled')),
    complexity INT CHECK (complexity BETWEEN 1 AND 10),
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    embedding vector(1024),  -- Voyage AI embeddings
    metadata JSONB DEFAULT '{}',  -- Flexible additional data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    estimated_time_seconds INT,
    actual_time_seconds INT
);

-- Patterns learned: Auto-learning successful patterns
CREATE TABLE IF NOT EXISTS patterns_learned (
    id SERIAL PRIMARY KEY,
    pattern_name TEXT UNIQUE NOT NULL,
    pattern_type VARCHAR(50),  -- code, architecture, deployment, etc.
    success_rate FLOAT DEFAULT 0 CHECK (success_rate BETWEEN 0 AND 1),
    usage_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    avg_time_seconds FLOAT,
    context_tags TEXT[],
    description TEXT,
    example_code TEXT,  -- Optional code snippet
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Errors history: Learning from failures
CREATE TABLE IF NOT EXISTS errors_history (
    id SERIAL PRIMARY KEY,
    error_type TEXT NOT NULL,
    error_message TEXT,
    context TEXT,  -- What was happening when error occurred
    solution TEXT,  -- How it was fixed
    embedding vector(1024),  -- For semantic similarity search
    resolved BOOLEAN DEFAULT FALSE,
    task_id INT REFERENCES tasks(id) ON DELETE SET NULL,
    related_pattern_id INT REFERENCES patterns_learned(id) ON DELETE SET NULL,
    occurred_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_time_seconds INT
);

-- Metrics: Performance monitoring
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_type VARCHAR(50),  -- latency, success_rate, token_usage, etc.
    value FLOAT NOT NULL,
    task_id INT REFERENCES tasks(id) ON DELETE CASCADE,
    threshold_alert FLOAT,
    exceeded_threshold BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_tasks_embedding ON tasks USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_metadata ON tasks USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_patterns_success_rate ON patterns_learned(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_usage ON patterns_learned(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_tags ON patterns_learned USING gin(context_tags);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns_learned(pattern_type);

CREATE INDEX IF NOT EXISTS idx_errors_embedding ON errors_history USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_errors_type ON errors_history(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_resolved ON errors_history(resolved);
CREATE INDEX IF NOT EXISTS idx_errors_task ON errors_history(task_id);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_exceeded ON metrics(exceeded_threshold);
CREATE INDEX IF NOT EXISTS idx_metrics_task ON metrics(task_id);

-- Trigger: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON patterns_learned
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: Auto-calculate resolution time for errors
CREATE OR REPLACE FUNCTION calculate_error_resolution_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.resolved = TRUE AND OLD.resolved = FALSE THEN
        NEW.resolved_at = NOW();
        NEW.resolution_time_seconds = EXTRACT(EPOCH FROM (NOW() - NEW.occurred_at));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_resolution_time BEFORE UPDATE ON errors_history
    FOR EACH ROW EXECUTE FUNCTION calculate_error_resolution_time();

-- Trigger: Auto-calculate actual task time
CREATE OR REPLACE FUNCTION calculate_task_time()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'done' AND OLD.status != 'done' THEN
        NEW.completed_at = NOW();
        NEW.actual_time_seconds = EXTRACT(EPOCH FROM (NOW() - NEW.created_at));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_task_completion_time BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION calculate_task_time();

-- Views: Useful queries for agents

-- Next task view: Tasks ready to work on (no blocking dependencies)
CREATE OR REPLACE VIEW next_tasks AS
SELECT t.*,
    COALESCE(AVG(pl.success_rate), 0.5) as pattern_confidence,
    COUNT(pl.id) as matching_patterns
FROM tasks t
LEFT JOIN memory_relations mr_dep ON mr_dep.target_id = t.id::text
    AND mr_dep.relation_type = 'DEPENDS_ON'
LEFT JOIN tasks dep_task ON dep_task.id = mr_dep.source_id::int
LEFT JOIN memory_relations mr_pattern ON mr_pattern.source_id = t.id::text
    AND mr_pattern.relation_type = 'USES_PATTERN'
LEFT JOIN patterns_learned pl ON pl.pattern_name = mr_pattern.target_id
WHERE t.status = 'pending'
    AND (dep_task.id IS NULL OR dep_task.status = 'done')
GROUP BY t.id
ORDER BY (t.priority * 0.4 + COALESCE(AVG(pl.success_rate), 0.5) * 0.6) DESC,
    t.created_at ASC;

-- Pattern performance view: Most successful patterns
CREATE OR REPLACE VIEW pattern_performance AS
SELECT
    pattern_name,
    pattern_type,
    success_rate,
    usage_count,
    success_count,
    failure_count,
    avg_time_seconds,
    context_tags,
    CASE
        WHEN avg_time_seconds > 0 THEN success_rate / avg_time_seconds
        ELSE success_rate
    END as efficiency_score,
    last_used,
    NOW() - last_used as time_since_last_use
FROM patterns_learned
WHERE usage_count > 0
ORDER BY efficiency_score DESC;

-- Error patterns view: Common errors and solutions
CREATE OR REPLACE VIEW error_patterns AS
SELECT
    error_type,
    COUNT(*) as occurrence_count,
    SUM(CASE WHEN resolved THEN 1 ELSE 0 END) as resolved_count,
    ROUND(SUM(CASE WHEN resolved THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric, 2) as resolution_rate,
    AVG(resolution_time_seconds) as avg_resolution_time,
    array_agg(DISTINCT solution) FILTER (WHERE solution IS NOT NULL) as solutions,
    MAX(occurred_at) as last_occurrence
FROM errors_history
GROUP BY error_type
ORDER BY occurrence_count DESC;

-- Task completion metrics view
CREATE OR REPLACE VIEW task_metrics AS
SELECT
    DATE(completed_at) as date,
    COUNT(*) as tasks_completed,
    AVG(actual_time_seconds) as avg_time_seconds,
    AVG(complexity) as avg_complexity,
    SUM(CASE WHEN actual_time_seconds <= estimated_time_seconds THEN 1 ELSE 0 END)::float / COUNT(*) as accuracy_rate
FROM tasks
WHERE status = 'done'
    AND completed_at IS NOT NULL
GROUP BY DATE(completed_at)
ORDER BY date DESC;

-- Comments
COMMENT ON TABLE tasks IS 'Core task storage with semantic embeddings for intelligent retrieval';
COMMENT ON TABLE patterns_learned IS 'Auto-learned patterns with success rates for continuous improvement';
COMMENT ON TABLE errors_history IS 'Error logging with semantic search for finding similar past issues';
COMMENT ON TABLE metrics IS 'Performance metrics for monitoring and optimization';

COMMENT ON VIEW next_tasks IS 'Tasks ready to work on, ranked by priority and pattern confidence';
COMMENT ON VIEW pattern_performance IS 'Pattern success rates and efficiency scores';
COMMENT ON VIEW error_patterns IS 'Common errors with resolution rates and solutions';
COMMENT ON VIEW task_metrics IS 'Daily task completion statistics and accuracy';
