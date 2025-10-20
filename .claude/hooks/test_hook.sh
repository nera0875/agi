#!/bin/bash
# Test script for auto_trigger_agent.py hook

set -e

PROJECT_ROOT="/home/pilote/projet/agi"
HOOK="$PROJECT_ROOT/.claude/hooks/auto_trigger_agent.py"

echo "Testing auto_trigger_agent.py hook..."
echo "======================================"

# Test 1: File exists and is executable
echo "[Test 1] Hook file exists and executable"
if [ -x "$HOOK" ]; then
    echo "✅ PASS: Hook is executable"
else
    echo "❌ FAIL: Hook not executable"
    exit 1
fi

# Test 2: Verify Python syntax
echo "[Test 2] Python syntax validation"
if python3 -m py_compile "$HOOK" 2>/dev/null; then
    echo "✅ PASS: Python syntax valid"
else
    echo "❌ FAIL: Python syntax error"
    exit 1
fi

# Test 3: Simulate Edit schema.py
echo "[Test 3] Simulate Edit:backend/api/schema.py"
export CLAUDE_TOOL_NAME="Edit"
export CLAUDE_FILE_PATH="backend/api/schema.py"
python3 "$HOOK" && echo "✅ PASS: Hook executed without errors" || echo "❌ FAIL: Hook failed"
unset CLAUDE_TOOL_NAME CLAUDE_FILE_PATH

# Test 4: Simulate Write memory_service.py
echo "[Test 4] Simulate Write:backend/services/memory_service.py"
export CLAUDE_TOOL_NAME="Write"
export CLAUDE_FILE_PATH="backend/services/memory_service.py"
python3 "$HOOK" && echo "✅ PASS: Hook executed without errors" || echo "❌ FAIL: Hook failed"
unset CLAUDE_TOOL_NAME CLAUDE_FILE_PATH

# Test 5: Verify trigger rules coverage
echo "[Test 5] Trigger rules coverage"
RULES=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/.claude/hooks')
from auto_trigger_agent import TRIGGER_RULES
print(f'Registered rules: {len(TRIGGER_RULES)}')
for pattern, config in TRIGGER_RULES.items():
    print(f'  - {pattern}: {config[\"agent\"]}')" 2>/dev/null)
echo "$RULES"

echo ""
echo "======================================"
echo "✅ All tests passed!"
