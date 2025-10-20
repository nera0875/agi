#!/bin/bash
# Git Rollback On Error Hook
# Trigger: Si agent fail OU tests fail
# Action: Rollback dernier commit ou reset to safety branch
# Modes: soft (keep changes), hard (discard), branch (restore from backup)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:=/home/pilote/projet/agi}"
cd "$PROJECT_ROOT" || exit 1

ERROR_TYPE="${1:-unknown}"       # agent_fail/test_fail/critical_error
ERROR_MSG="${2:-No message}"     # Error message
ROLLBACK_MODE="${3:-soft}"       # soft/hard/branch

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Création dossiers de log s'ils n'existent pas
mkdir -p .claude/meta

ROLLBACK_LOG=".claude/meta/rollback.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_BEFORE=$(git rev-parse --short HEAD)

echo -e "${RED}[Git Rollback]${NC} ${YELLOW}🚨 Error detected${NC}"
echo -e "${BLUE}Type:${NC} $ERROR_TYPE"
echo -e "${BLUE}Mode:${NC} $ROLLBACK_MODE"
echo -e "${BLUE}Commit:${NC} $COMMIT_BEFORE"
echo ""

case "$ROLLBACK_MODE" in
    "soft")
        echo -e "${YELLOW}[Soft Rollback]${NC} Preserving changes, undoing commit..."

        # Vérifier s'il y a un commit à rollback
        if git rev-parse HEAD~1 >/dev/null 2>&1; then
            CHANGES_COUNT=$(git diff --name-only HEAD | wc -l)
            git reset --soft HEAD~1
            echo -e "${GREEN}✅ Success:${NC} Commit undone, $CHANGES_COUNT changes in staging"
            echo "$TIMESTAMP | SOFT | $ERROR_TYPE | From: $COMMIT_BEFORE | Changes preserved" >> "$ROLLBACK_LOG"
        else
            echo -e "${YELLOW}⚠️ Warning:${NC} No previous commit, skipping rollback"
        fi
        ;;

    "hard")
        echo -e "${YELLOW}[Hard Rollback]${NC} Creating backup before hard reset..."

        # Vérifier s'il y a un commit à rollback
        if git rev-parse HEAD~1 >/dev/null 2>&1; then
            BACKUP_BRANCH="backup/before-rollback-$(date +%Y%m%d_%H%M%S)"
            echo -e "${BLUE}Backup branch:${NC} $BACKUP_BRANCH"

            git branch "$BACKUP_BRANCH"
            git reset --hard HEAD~1

            COMMIT_AFTER=$(git rev-parse --short HEAD)
            echo -e "${GREEN}✅ Success:${NC} Hard reset complete"
            echo -e "   From: $COMMIT_BEFORE → To: $COMMIT_AFTER"
            echo -e "   Backup: $BACKUP_BRANCH"
            echo "$TIMESTAMP | HARD | $ERROR_TYPE | From: $COMMIT_BEFORE | Backup: $BACKUP_BRANCH" >> "$ROLLBACK_LOG"
        else
            echo -e "${YELLOW}⚠️ Warning:${NC} No previous commit, skipping hard reset"
        fi
        ;;

    "branch")
        echo -e "${YELLOW}[Branch Rollback]${NC} Finding safety backup branch..."

        SAFETY_BRANCH=$(git branch --list 'safety/backup-*' --sort=-committerdate | head -1 | xargs)

        if [ -n "$SAFETY_BRANCH" ]; then
            echo -e "${BLUE}Safety branch found:${NC} $SAFETY_BRANCH"

            # Créer branche recovery
            RECOVERY_BRANCH="recovery/from-error-$(date +%Y%m%d_%H%M%S)"
            git checkout "$SAFETY_BRANCH" 2>/dev/null || {
                echo -e "${YELLOW}⚠️ Could not checkout $SAFETY_BRANCH${NC}"
                echo "   Falling back to soft reset"
                git reset --soft HEAD~1
                RECOVERY_BRANCH="fallback/soft-reset-$(date +%Y%m%d_%H%M%S)"
            }

            git checkout -b "$RECOVERY_BRANCH"
            echo -e "${GREEN}✅ Success:${NC} Recovery branch created"
            echo -e "   From safety: $SAFETY_BRANCH"
            echo -e "   Recovery: $RECOVERY_BRANCH"
            echo "$TIMESTAMP | BRANCH | $ERROR_TYPE | From: $COMMIT_BEFORE | To: $RECOVERY_BRANCH | Safety: $SAFETY_BRANCH" >> "$ROLLBACK_LOG"
        else
            echo -e "${YELLOW}⚠️ No safety branch found${NC}, falling back to soft reset"
            git reset --soft HEAD~1
            echo -e "${GREEN}✅ Fallback:${NC} Soft reset applied"
            echo "$TIMESTAMP | FALLBACK | $ERROR_TYPE | From: $COMMIT_BEFORE | Soft reset applied" >> "$ROLLBACK_LOG"
        fi
        ;;

    *)
        echo -e "${YELLOW}[Unknown Mode]${NC} Defaulting to soft reset..."
        git reset --soft HEAD~1
        echo -e "${GREEN}✅ Default:${NC} Soft reset applied"
        echo "$TIMESTAMP | DEFAULT | $ERROR_TYPE | From: $COMMIT_BEFORE" >> "$ROLLBACK_LOG"
        ;;
esac

echo ""
echo -e "${BLUE}Current status:${NC}"
git status --short | head -5 || echo "   (no changes)"

echo ""
echo -e "${RED}[Git Rollback]${NC} ${GREEN}🔒 Complete${NC}"
echo -e "Log: $ROLLBACK_LOG"

exit 0
