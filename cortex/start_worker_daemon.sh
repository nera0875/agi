#!/bin/bash
# Start permanent task worker daemon
# Polls worker_tasks table and executes tasks continuously

WORKER_PID_FILE="/tmp/agi_worker.pid"
WORKER_LOG="/tmp/agi_worker.log"

# Check if already running
if [ -f "$WORKER_PID_FILE" ]; then
    PID=$(cat "$WORKER_PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "❌ Worker already running (PID: $PID)"
        exit 1
    fi
fi

echo "🚀 Starting AGI Task Worker Daemon..."

# Launch worker in background
cd /home/pilote/projet/agi

nohup python3 cortex/task_worker.py 1 > "$WORKER_LOG" 2>&1 &
WORKER_PID=$!

echo $WORKER_PID > "$WORKER_PID_FILE"

sleep 1

if ps -p "$WORKER_PID" > /dev/null 2>&1; then
    echo "✅ Worker started (PID: $WORKER_PID)"
    echo "📋 Log: $WORKER_LOG"
else
    echo "❌ Worker failed to start"
    rm "$WORKER_PID_FILE"
    exit 1
fi
