#!/bin/bash
# Install git hooks for AGI project
# Usage: ./scripts/install-hooks.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "🔧 Installing git hooks..."
echo "   Root: $REPO_ROOT"
echo "   Hooks: $HOOKS_DIR"

# Check if .git exists
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Make hooks executable
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    chmod +x "$HOOKS_DIR/pre-commit"
    echo "✅ pre-commit hook installed (executable)"
else
    echo "❌ Warning: pre-commit hook not found"
fi

# Verify installation
echo ""
echo "📋 Installed hooks:"
for hook in pre-commit pre-push commit-msg; do
    if [ -x "$HOOKS_DIR/$hook" ]; then
        echo "   ✅ $hook"
    elif [ -f "$HOOKS_DIR/$hook" ]; then
        echo "   ⚠️  $hook (not executable)"
    fi
done

echo ""
echo "🚀 Hooks ready!"
echo "   Documentation: .git/HOOKS_README.md"
echo "   Security scanner: python backend/agents/security_scanner.py"

exit 0
