#!/bin/bash
# Git Pre-Modification Backup Hook
# Purpose: Auto-backup critical files before Edit/Write operations
# Trigger: PreToolUse hook before Edit:* or Write:* tools
# Action: Creates safety feature branch + auto-commit

set -e

PROJECT_ROOT="/home/pilote/projet/agi"
cd "$PROJECT_ROOT" || exit 1

# Extract filepath from argument
CRITICAL_FILE="${1:-.}"

# Critical patterns that require backup before modification
CRITICAL_PATTERNS=(
    "CLAUDE.md"
    ".claude/agents/"
    ".claude/skills/"
    ".claude/commands/"
    "backend/api/schema.py"
    "backend/services/"
    "backend/agents/"
    "cortex/agi_tools_mcp.py"
    "cortex/local_mcp_router.py"
    "cortex/consolidation.py"
)

# Check if file matches critical pattern
is_critical=false
if [[ -z "$CRITICAL_FILE" ]] || [[ "$CRITICAL_FILE" == "." ]]; then
    is_critical=false
else
    for pattern in "${CRITICAL_PATTERNS[@]}"; do
        if [[ "$CRITICAL_FILE" == *"$pattern"* ]]; then
            is_critical=true
            break
        fi
    done
fi

# If not critical, exit silently
if [ "$is_critical" = false ]; then
    exit 0
fi

# Check git status
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "[⚠️  Git Backup] Not in git repository, skipping backup"
    exit 0
fi

# Check if there are uncommitted changes
if git diff --quiet && git diff --cached --quiet; then
    # No changes, safe to proceed
    exit 0
fi

# Generate unique timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BRANCH_NAME="safety/backup-before-modification-$TIMESTAMP"

# Log backup action
echo "[🔒 Git Backup] Critical file detected: $CRITICAL_FILE"
echo "[🔒 Git Backup] Creating safety backup..."

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create and switch to backup branch
if git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    git checkout "$BRANCH_NAME" >/dev/null 2>&1
else
    git checkout -b "$BRANCH_NAME" >/dev/null 2>&1
fi

# Stage all changes and commit
git add -A

git commit -m "🔒 SAFETY BACKUP before modifying: $CRITICAL_FILE

Timestamp: $TIMESTAMP
Original branch: $CURRENT_BRANCH
Trigger: pre-modification-hook
Backup branch: $BRANCH_NAME

This is an automatic safety commit before critical modification.

Rollback: git checkout $CURRENT_BRANCH && git branch -D $BRANCH_NAME" \
    -q 2>/dev/null || true

# Switch back to original branch for actual modification
git checkout "$CURRENT_BRANCH" >/dev/null 2>&1

echo "[✅ Git Backup] Backup created in branch: $BRANCH_NAME"
echo "[💡 Git Backup] Rollback command: git checkout $BRANCH_NAME"

exit 0
