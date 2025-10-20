#!/bin/bash
# Git Post-Task Checkpoint Hook
# Trigger: APRÈS agent task complete
# Action: Atomic commit avec context
# Purpose: Create checkpoints after each agent task execution

PROJECT_ROOT="${PROJECT_ROOT:=/home/pilote/projet/agi}"
cd "$PROJECT_ROOT" || exit 1

TASK_NAME="${1:-unknown_task}"
TASK_STATUS="${2:-unknown}"
AGENT_TYPE="${3:-generic}"
TASK_ID="${4:-$(date +%s)}"

# Only commit if success
if [ "$TASK_STATUS" != "success" ]; then
    echo "[GitCheckpoint] ⚠️  Task failed ($TASK_NAME), skipping commit"
    exit 0
fi

# Check if there are any changes to commit
if ! git diff --quiet && [ -n "$(git diff --name-only)" ]; then
    TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)

    echo "[GitCheckpoint] 📸 Creating checkpoint: $TASK_NAME"

    # Stage all changes
    git add -A

    # Get summary of changes
    CHANGED_FILES=$(git diff --cached --name-only | wc -l)

    # Atomic commit with context
    git commit -m "checkpoint: $TASK_NAME [${AGENT_TYPE}]

Task: $TASK_NAME
Agent: $AGENT_TYPE
Status: $TASK_STATUS
Timestamp: $TIMESTAMP
TaskID: $TASK_ID
Files: $CHANGED_FILES

Automated checkpoint after agent task execution." \
        --quiet 2>/dev/null || {
        echo "[GitCheckpoint] ⚠️  Commit failed, but continuing..."
        exit 1
    }

    echo "[GitCheckpoint] ✅ Checkpoint saved ($CHANGED_FILES files)"

else
    if ! git diff --cached --quiet; then
        # There are staged changes but no unstaged changes
        TIMESTAMP=$(date +%Y-%m-%d_%H:%M:%S)
        CHANGED_FILES=$(git diff --cached --name-only | wc -l)

        git commit -m "checkpoint: $TASK_NAME [${AGENT_TYPE}]

Task: $TASK_NAME
Agent: $AGENT_TYPE
Status: $TASK_STATUS
Timestamp: $TIMESTAMP
TaskID: $TASK_ID
Files: $CHANGED_FILES

Automated checkpoint after agent task execution." \
            --quiet 2>/dev/null || {
            echo "[GitCheckpoint] ⚠️  Commit failed"
            exit 1
        }

        echo "[GitCheckpoint] ✅ Checkpoint saved (staged: $CHANGED_FILES files)"
    else
        echo "[GitCheckpoint] ℹ️  No changes to commit"
        exit 0
    fi
fi

exit 0
