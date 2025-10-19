-- ============================================================================
-- SYSTÈME DE BOOTSTRAP AUTONOME AGI
-- Architecture pour cerveau qui se souvient et continue automatiquement
-- ============================================================================

-- Table 1: Instructions de bootstrap (chargées au démarrage de chaque session)
CREATE TABLE IF NOT EXISTS system_bootstrap (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    priority INTEGER NOT NULL DEFAULT 0, -- Ordre d'exécution
    instruction_type TEXT NOT NULL, -- 'query_rules', 'load_context', 'setup_polling', etc.
    instruction_content TEXT NOT NULL, -- SQL ou instructions textuelles
    active BOOLEAN DEFAULT true,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table 2: Contexte actif de la session courante
CREATE TABLE IF NOT EXISTS active_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID UNIQUE NOT NULL, -- ID unique de la session Claude Code
    conversation_phase TEXT NOT NULL DEFAULT 'initialization', -- 'working', 'waiting_user', etc.
    current_task_id UUID, -- Référence à worker_tasks si applicable
    context_variables JSONB DEFAULT '{}', -- Variables d'état (colonnes en resize, table ouverte, etc.)
    pending_actions JSONB DEFAULT '[]', -- Actions à exécuter au prochain cycle
    last_user_message TEXT,
    last_agent_action TEXT,
    session_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Table 3: Queue d'instructions/ordres à exécuter
CREATE TABLE IF NOT EXISTS pending_instructions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instruction_type TEXT NOT NULL, -- 'user_command', 'system_task', 'scheduled_action'
    instruction_text TEXT NOT NULL,
    priority INTEGER DEFAULT 50,
    execution_context JSONB DEFAULT '{}', -- Contexte nécessaire pour exécution
    status TEXT DEFAULT 'pending', -- 'pending', 'executing', 'completed', 'failed'
    assigned_to TEXT, -- 'sonnet', 'haiku', 'worker', etc.
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    executed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Table 4: Checkpoints des agents background (pour reprise après interruption)
CREATE TABLE IF NOT EXISTS agent_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_task_id UUID REFERENCES worker_tasks(id) ON DELETE CASCADE,
    checkpoint_type TEXT NOT NULL, -- 'progress', 'intermediate_result', 'state_snapshot'
    checkpoint_data JSONB NOT NULL,
    progress_percentage INTEGER DEFAULT 0,
    can_resume BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_bootstrap_priority ON system_bootstrap(priority DESC) WHERE active = true;
CREATE INDEX IF NOT EXISTS idx_active_context_session ON active_context(session_id) WHERE session_active = true;
CREATE INDEX IF NOT EXISTS idx_pending_instructions_status ON pending_instructions(status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_agent_checkpoints_task ON agent_checkpoints(worker_task_id);

-- ============================================================================
-- DONNÉES INITIALES: Instructions de bootstrap
-- ============================================================================

INSERT INTO system_bootstrap (priority, instruction_type, instruction_content, tags) VALUES
-- Priorité 100: Charger les règles système
(100, 'load_rules', 'SELECT rule_content FROM system_rules WHERE active = true ORDER BY priority DESC',
 ARRAY['critical', 'startup']),

-- Priorité 95: Restaurer contexte de session
(95, 'restore_context', 'SELECT * FROM active_context WHERE session_active = true ORDER BY updated_at DESC LIMIT 1',
 ARRAY['critical', 'startup']),

-- Priorité 90: Check agents en cours
(90, 'check_workers', 'SELECT * FROM worker_tasks WHERE status IN (''pending'', ''running'') ORDER BY priority DESC',
 ARRAY['startup', 'monitoring']),

-- Priorité 85: Load pending instructions
(85, 'load_pending', 'SELECT * FROM pending_instructions WHERE status = ''pending'' ORDER BY priority DESC',
 ARRAY['startup', 'task-queue']),

-- Priorité 80: Setup polling loop
(80, 'setup_polling', 'Start background polling every 30s to check worker_tasks status',
 ARRAY['startup', 'monitoring']),

-- Priorité 75: Load agent prompts
(75, 'load_agents', 'SELECT agent_type, system_prompt FROM agent_prompts',
 ARRAY['startup', 'agents'])

ON CONFLICT DO NOTHING;

-- ============================================================================
-- FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction: Créer ou update le contexte actif
CREATE OR REPLACE FUNCTION upsert_active_context(
    p_session_id UUID,
    p_phase TEXT DEFAULT 'working',
    p_context_vars JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_context_id UUID;
BEGIN
    INSERT INTO active_context (session_id, conversation_phase, context_variables, updated_at)
    VALUES (p_session_id, p_phase, p_context_vars, now())
    ON CONFLICT (session_id)
    DO UPDATE SET
        conversation_phase = EXCLUDED.conversation_phase,
        context_variables = active_context.context_variables || EXCLUDED.context_variables,
        updated_at = now()
    RETURNING id INTO v_context_id;

    RETURN v_context_id;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Ajouter une instruction à la queue
CREATE OR REPLACE FUNCTION queue_instruction(
    p_instruction_text TEXT,
    p_priority INTEGER DEFAULT 50,
    p_context JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_instruction_id UUID;
BEGIN
    INSERT INTO pending_instructions (instruction_text, priority, execution_context)
    VALUES (p_instruction_text, p_priority, p_context)
    RETURNING id INTO v_instruction_id;

    RETURN v_instruction_id;
END;
$$ LANGUAGE plpgsql;

-- Fonction: Créer checkpoint pour agent
CREATE OR REPLACE FUNCTION save_agent_checkpoint(
    p_task_id UUID,
    p_checkpoint_data JSONB,
    p_progress INTEGER DEFAULT 0
) RETURNS UUID AS $$
DECLARE
    v_checkpoint_id UUID;
BEGIN
    INSERT INTO agent_checkpoints (worker_task_id, checkpoint_type, checkpoint_data, progress_percentage)
    VALUES (p_task_id, 'progress', p_checkpoint_data, p_progress)
    RETURNING id INTO v_checkpoint_id;

    RETURN v_checkpoint_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VUE: Dashboard du système
-- ============================================================================

CREATE OR REPLACE VIEW system_dashboard AS
SELECT
    (SELECT COUNT(*) FROM system_rules WHERE active = true) as active_rules,
    (SELECT COUNT(*) FROM active_context WHERE session_active = true) as active_sessions,
    (SELECT COUNT(*) FROM pending_instructions WHERE status = 'pending') as pending_instructions,
    (SELECT COUNT(*) FROM worker_tasks WHERE status = 'running') as running_workers,
    (SELECT COUNT(*) FROM worker_tasks WHERE status = 'pending') as queued_workers,
    (SELECT COUNT(*) FROM agent_checkpoints WHERE can_resume = true) as resumable_checkpoints;

COMMENT ON VIEW system_dashboard IS 'Vue d''ensemble de l''état du système AGI';
