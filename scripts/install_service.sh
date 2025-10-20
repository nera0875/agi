#!/bin/bash
set -e

echo "Installing AGI Agents systemd service..."

# Copy service file
sudo cp /home/pilote/projet/agi/scripts/systemd/agi-agents.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable agi-agents

echo "Service installed. Start with: sudo systemctl start agi-agents"
echo "View logs with: journalctl -u agi-agents -f"
