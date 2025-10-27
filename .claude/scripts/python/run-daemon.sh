#!/bin/bash
# Run Memory Daemon - Clustering + OpenRouter Gemini

export OPENROUTER_API_KEY='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'

cd /home/pilote/projet/primaire/AGI/.claude/scripts/python

echo "=== Memory Daemon Starting (OpenRouter) ==="
echo "Time: $(date)"
echo ""

/usr/bin/python3 memory-daemon.py

echo ""
echo "=== Memory Daemon Completed ==="
echo "Time: $(date)"
