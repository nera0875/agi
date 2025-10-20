#!/usr/bin/env python3
"""
Cascade Hook - Auto-trigger phases séquentielles

Déclenche phase suivante automatiquement:
Phase 1 (understanding) done → Phase 2 (research) auto
Phase 2 done → Phase 3 (architecture) auto
Phase 3 done → Phase 4 (implementation) auto
Phase 4 done → Phase 5 (validation) auto
Phase 5 done → Phase 6 (documentation) auto

Runs in background (non-blocking) via subprocess
"""
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Phase cascade map: current_phase → next_phase
PHASE_CASCADE = {
    "understanding": "research",
    "research": "architecture",
    "architecture": "implementation",
    "implementation": "validation",
    "validation": "documentation"
}

# Phase → Primary Agent mapping
PHASE_AGENT_MAP = {
    "research": "research",
    "architecture": "architect",
    "implementation": "code",
    "validation": "debug",
    "documentation": "docs"
}

def get_completed_phase() -> str | None:
    """Extract completed phase from environment"""
    # Claude Code sets this when phase completes
    phase = os.environ.get('CLAUDE_COMPLETED_PHASE', '').strip()
    return phase if phase else None

def should_cascade() -> bool:
    """Check if auto-cascade is enabled"""
    auto_cascade = os.environ.get('CLAUDE_AUTO_CASCADE', 'false').lower()
    return auto_cascade == 'true'

def log_cascade_event(phase: str, next_phase: str, action: str):
    """Log cascade event to .cascade_log"""
    log_dir = Path('/home/pilote/projet/agi/.claude/hooks')
    log_file = log_dir / '.cascade_log'

    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': phase,
            'next_phase': next_phase,
            'action': action
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass  # Silently fail logging

def trigger_next_phase(next_phase: str, agent: str) -> bool:
    """Trigger next phase agent in background"""
    project_root = Path('/home/pilote/projet/agi')

    try:
        subprocess.Popen(
            [
                'python3',
                str(project_root / 'run_agents.py'),
                'agent',
                agent,
                '--auto-cascade'
            ],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach completely
        )
        return True
    except Exception as e:
        return False

def main():
    """Main cascade hook entry point"""
    # Get completed phase
    phase = get_completed_phase()

    if not phase:
        sys.exit(0)

    # Check if cascade enabled
    if not should_cascade():
        log_cascade_event(phase, '', 'skipped_disabled')
        sys.exit(0)

    # Get next phase
    next_phase = PHASE_CASCADE.get(phase)

    if not next_phase:
        log_cascade_event(phase, '', 'final_phase')
        sys.exit(0)

    # Get agent for next phase
    agent = PHASE_AGENT_MAP.get(next_phase)

    if not agent:
        log_cascade_event(phase, next_phase, 'no_agent_found')
        sys.exit(0)

    # Trigger next phase
    success = trigger_next_phase(next_phase, agent)

    if success:
        log_cascade_event(phase, next_phase, 'triggered')
    else:
        log_cascade_event(phase, next_phase, 'trigger_failed')

    sys.exit(0)

if __name__ == '__main__':
    main()
