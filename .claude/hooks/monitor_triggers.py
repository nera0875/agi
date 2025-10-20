#!/usr/bin/env python3
"""
Monitor script for auto_trigger_agent.py

Analyzes trigger logs and provides statistics:
- Trigger frequency by file
- Trigger frequency by agent
- Recent triggers
- Success rates (if agents report)
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

LOG_FILE = Path('/home/pilote/projet/agi/.claude/hooks/.trigger_log')

def parse_logs() -> List[Dict]:
    """Parse trigger log file"""
    if not LOG_FILE.exists():
        return []

    logs = []
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"Error reading log file: {e}", file=sys.stderr)

    return logs

def show_statistics(logs: List[Dict]):
    """Show trigger statistics"""
    if not logs:
        print("No triggers recorded yet.")
        return

    # Stats by agent
    agents = defaultdict(int)
    files = defaultdict(int)
    recent = logs[-20:]  # Last 20

    for log in logs:
        agents[log.get('agent', 'unknown')] += 1
        files[log.get('file', 'unknown')] += 1

    print("=" * 60)
    print("TRIGGER STATISTICS")
    print("=" * 60)

    print(f"\nTotal Triggers: {len(logs)}")

    # Most triggered agents
    print("\nAgents (most triggered):")
    for agent, count in sorted(agents.items(), key=lambda x: x[1], reverse=True):
        print(f"  {agent:20} {count:3} triggers")

    # Most triggered files
    print("\nFiles (most triggered):")
    for file, count in sorted(files.items(), key=lambda x: x[1], reverse=True)[:10]:
        short_file = file if file else "(unknown)"
        if len(short_file) > 40:
            short_file = "..." + short_file[-37:]
        print(f"  {short_file:40} {count:3} triggers")

    # Recent triggers
    print("\nRecent Triggers (last 20):")
    for log in reversed(recent):
        ts = log.get('timestamp', 'unknown')
        agent = log.get('agent', 'unknown')
        reason = log.get('reason', 'unknown')[:40]
        print(f"  [{ts}] {agent:15} - {reason}")

    print("\n" + "=" * 60)

def show_timeline(logs: List[Dict], hours: int = 24):
    """Show trigger timeline (last N hours)"""
    if not logs:
        return

    now = datetime.fromisoformat(datetime.now().isoformat().split('.')[0])
    cutoff = now - timedelta(hours=hours)

    recent_logs = []
    for log in logs:
        try:
            ts = datetime.fromisoformat(log.get('timestamp', ''))
            if ts >= cutoff:
                recent_logs.append(log)
        except ValueError:
            pass

    if not recent_logs:
        print(f"No triggers in last {hours} hours")
        return

    print(f"\nTriggers Last {hours} Hours: {len(recent_logs)}")

    # Group by hour
    by_hour = defaultdict(int)
    for log in recent_logs:
        try:
            ts = datetime.fromisoformat(log.get('timestamp', ''))
            hour = ts.strftime('%H:00')
            by_hour[hour] += 1
        except ValueError:
            pass

    for hour in sorted(by_hour.keys()):
        count = by_hour[hour]
        bar = '█' * min(count, 50)
        print(f"  {hour} {bar} ({count})")

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor auto_trigger_agent.py')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--timeline', type=int, metavar='HOURS', help='Show timeline (default: 24h)')
    parser.add_argument('--clear', action='store_true', help='Clear log file')
    parser.add_argument('--follow', action='store_true', help='Follow log file (tail -f)')

    args = parser.parse_args()

    if args.clear:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print("Log file cleared.")
        sys.exit(0)

    if args.follow:
        import time
        import subprocess
        try:
            subprocess.run(['tail', '-f', str(LOG_FILE)])
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
        sys.exit(0)

    # Default: show stats
    logs = parse_logs()

    if args.stats or not args.timeline:
        show_statistics(logs)

    if args.timeline:
        show_timeline(logs, args.timeline)

if __name__ == '__main__':
    main()
