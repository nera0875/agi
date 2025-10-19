#!/bin/bash
# AGI Backend Launcher
# Charge .env et démarre le backend MCP

cd "$(dirname "$0")"

# Load .env file
export $(cat .env | grep -v '^#' | xargs)

# Override ports pour Docker
export DATABASE_URL="postgresql://agi_user:mysecretpassword@localhost:5433/agi_db"
export REDIS_URL="redis://localhost:6380"

# Start backend
exec python3 main.py
