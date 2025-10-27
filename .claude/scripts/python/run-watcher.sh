#!/bin/bash
# Run Memory Watcher - Trigger daemon sur nouvelle conversation

export OPENROUTER_API_KEY='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'

cd /home/pilote/projet/primaire/AGI/.claude/scripts/python

echo "Starting Memory Watcher..."
/usr/bin/python3 memory-watcher.py
