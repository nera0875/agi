#!/usr/bin/env python3
"""
Monitor script for cascade_hook.py

Analyzes cascade logs:
- Phase transitions history
- Cascade success/failure rate
- Timeline of cascades
- Recently triggered phases
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

LOG_FILE = Path('/home/pilote/projet/agi/.claude/hooks/.cascade_log')

def parse_logs() -> List[Dict]:
    """Parse cascade log file"""
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
    """Show cascade statistics"""
    if not logs:
        print("No cascade events recorded yet.")
        return

    triggered = [l for l in logs if l.get('action') == 'triggered']
    skipped = [l for l in logs if l.get('action') == 'skipped_disabled']
    failed = [l for l in logs if l.get('action') == 'trigger_failed']
    final = [l for l in logs if l.get('action') == 'final_phase']

    phase_transitions = defaultdict(int)
    for log in triggered:
        phase = log.get('phase', 'unknown')
        next_phase = log.get('next_phase', 'unknown')
        phase_transitions[f"{phase} → {next_phase}"] += 1

    print("=" * 70)
    print("CASCADE HOOK STATISTICS")
    print("=" * 70)

    print(f"\nTotal Events: {len(logs)}")
    print(f"  ✅ Triggered: {len(triggered)}")
    print(f"  ⏸️  Skipped (disabled): {len(skipped)}")
    print(f"  ❌ Failed: {len(failed)}")
    print(f"  ✨ Final phase: {len(final)}")

    success_rate = (len(triggered) / (len(triggered) + len(failed)) * 100) if (len(triggered) + len(failed)) > 0 else 0
    print(f"\n✅ Success Rate: {success_rate:.1f}%")

    print("\nPhase Transitions:")
    for transition, count in sorted(phase_transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {transition:30} {count:3}x")

    print("\nRecent Events (last 10):")
    for log in reversed(logs[-10:]):
        ts = log.get('timestamp', 'unknown')
        phase = log.get('phase', 'unknown')
        action = log.get('action', 'unknown')
        next_phase = log.get('next_phase', '')

        status_icon = {
            'triggered': '✅',
            'skipped_disabled': '⏸️',
            'trigger_failed': '❌',
            'final_phase': '✨',
            'no_agent_found': '⚠️'
        }.get(action, '❓')

        print(f"  [{ts}] {status_icon} {phase:15} → {next_phase:15} ({action})")

    print("\n" + "=" * 70)

def show_cascade_chains(logs: List[Dict]):
    """Show cascade chains (complete phase sequences)"""
    if not logs:
        return

    triggered = [l for l in logs if l.get('action') == 'triggered']

    if not triggered:
        print("No cascades triggered yet.")
        return

    print("\n" + "=" * 70)
    print("CASCADE CHAINS")
    print("=" * 70)

    # Group by initiation time (assume same chain if within 60s)
    chains = []
    current_chain = []
    last_time = None

    for log in triggered:
        try:
            ts = datetime.fromisoformat(log.get('timestamp', ''))

            if last_time and (ts - last_time).total_seconds() > 60:
                if current_chain:
                    chains.append(current_chain)
                current_chain = []

            current_chain.append({
                'phase': log.get('phase'),
                'next': log.get('next_phase'),
                'ts': ts
            })
            last_time = ts
        except ValueError:
            pass

    if current_chain:
        chains.append(current_chain)

    print(f"\nComplete Chains: {len(chains)}")

    for i, chain in enumerate(chains[-5:], 1):  # Last 5 chains
        phases = ' → '.join([step['phase'] for step in chain] + [chain[-1]['next']])
        start_time = chain[0]['ts'].strftime('%H:%M:%S')
        end_time = chain[-1]['ts'].strftime('%H:%M:%S')
        duration = (chain[-1]['ts'] - chain[0]['ts']).total_seconds()

        print(f"\n  Chain {i}: {phases}")
        print(f"    Start: {start_time}, End: {end_time} ({duration:.1f}s)")

    print("\n" + "=" * 70)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor cascade_hook.py')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--chains', action='store_true', help='Show cascade chains')
    parser.add_argument('--clear', action='store_true', help='Clear log file')
    parser.add_argument('--follow', action='store_true', help='Follow log file (tail -f)')

    args = parser.parse_args()

    if args.clear:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print("Cascade log cleared.")
        sys.exit(0)

    if args.follow:
        import subprocess
        try:
            subprocess.run(['tail', '-f', str(LOG_FILE)])
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
        sys.exit(0)

    # Default: show stats + chains
    logs = parse_logs()

    if args.stats or not args.chains:
        show_statistics(logs)

    if args.chains:
        show_cascade_chains(logs)

if __name__ == '__main__':
    main()
