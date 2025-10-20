#!/usr/bin/env python3
"""
Cascade Hook Integration Example

Shows how to integrate cascade hook into orchestrator.py
"""
import os
import subprocess
import sys
from pathlib import Path

# Example: How to trigger cascade from orchestrator
class OrchestrationWithCascade:
    """Example orchestrator with cascade support"""

    def __init__(self):
        self.project_root = Path('/home/pilote/projet/agi')

    def execute_phase(self, phase_name: str, agents: list) -> dict:
        """
        Execute phase and automatically cascade to next

        Args:
            phase_name: Phase identifier (understanding, research, etc.)
            agents: List of agents to execute

        Returns:
            Results dictionary
        """
        print(f"\n[Orchestrator] 🚀 Starting phase: {phase_name}")
        print(f"[Orchestrator] 🤖 {len(agents)} agents assigned")

        # Execute agents (parallel)
        results = {
            "phase": phase_name,
            "agents": agents,
            "status": "executing"
        }

        # In real code, run agents here
        # For example: parallel_run_agents(agents)

        print(f"[Orchestrator] ✅ Phase {phase_name} completed")

        # Signal completion for cascade hook
        self._signal_cascade(phase_name)

        return results

    def _signal_cascade(self, phase_name: str):
        """Signal phase completion to cascade hook"""
        print(f"[Orchestrator] 📢 Signaling cascade: {phase_name}")

        # Set environment variables
        os.environ['CLAUDE_COMPLETED_PHASE'] = phase_name
        os.environ['CLAUDE_AUTO_CASCADE'] = 'true'

        # Run cascade hook (non-blocking)
        try:
            cascade_hook = self.project_root / '.claude/hooks/cascade_hook.py'
            subprocess.Popen(
                ['python3', str(cascade_hook)],
                cwd=self.project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            print(f"[Orchestrator] ✅ Cascade hook triggered")
        except Exception as e:
            print(f"[Orchestrator] ❌ Cascade trigger failed: {e}")

    def full_workflow(self):
        """Example: Full workflow with cascading"""
        print("=" * 70)
        print("FULL WORKFLOW WITH CASCADE")
        print("=" * 70)

        # Phase 1: Understanding
        self.execute_phase('understanding', [
            'ask:backend',
            'ask:frontend',
            'ask:database'
        ])
        # → Cascade hook will auto-trigger research

        # Phase 2: Research
        # (Would be auto-triggered by cascade)
        # self.execute_phase('research', [...])

        # Phase 3: Architecture
        # (Would be auto-triggered by cascade)
        # self.execute_phase('architecture', [...])

        # ... and so on until documentation


def example_quick_cascade():
    """Quick example: Test cascade"""
    print("\n" + "=" * 70)
    print("QUICK EXAMPLE: TEST CASCADE")
    print("=" * 70)

    # Enable cascade
    os.environ['CLAUDE_AUTO_CASCADE'] = 'true'

    # Simulate phase completion
    test_phases = ['understanding', 'research', 'architecture']

    for phase in test_phases:
        print(f"\n[Example] Testing cascade from {phase}")

        os.environ['CLAUDE_COMPLETED_PHASE'] = phase

        # Run cascade hook
        cascade_hook = Path('/home/pilote/projet/agi/.claude/hooks/cascade_hook.py')
        result = subprocess.run(
            ['python3', str(cascade_hook)],
            cwd=Path('/home/pilote/projet/agi'),
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"[Example] ✅ Cascade executed successfully")
        else:
            print(f"[Example] ❌ Cascade failed: {result.stderr}")


def example_with_monitoring():
    """Example: Run cascade with monitoring"""
    print("\n" + "=" * 70)
    print("EXAMPLE: CASCADE WITH MONITORING")
    print("=" * 70)

    # Clear previous logs
    cascade_monitor = Path('/home/pilote/projet/agi/.claude/hooks/cascade_monitor.py')
    subprocess.run(
        ['python3', str(cascade_monitor), '--clear'],
        cwd=Path('/home/pilote/projet/agi')
    )

    # Run cascade tests
    os.environ['CLAUDE_AUTO_CASCADE'] = 'true'
    phases = ['understanding', 'research']

    for phase in phases:
        os.environ['CLAUDE_COMPLETED_PHASE'] = phase
        cascade_hook = Path('/home/pilote/projet/agi/.claude/hooks/cascade_hook.py')
        subprocess.run(
            ['python3', str(cascade_hook)],
            cwd=Path('/home/pilote/projet/agi'),
            capture_output=True
        )

    # Show monitoring results
    print("\n[Example] 📊 Cascade Statistics:")
    subprocess.run(
        ['python3', str(cascade_monitor), '--stats'],
        cwd=Path('/home/pilote/projet/agi')
    )


def main():
    """Main example"""
    import argparse

    parser = argparse.ArgumentParser(description='Cascade Hook Integration Examples')
    parser.add_argument('--demo', choices=['full', 'quick', 'monitor'], default='quick',
                        help='Which demo to run')

    args = parser.parse_args()

    if args.demo == 'full':
        orch = OrchestrationWithCascade()
        orch.full_workflow()
    elif args.demo == 'quick':
        example_quick_cascade()
    elif args.demo == 'monitor':
        example_with_monitoring()


if __name__ == '__main__':
    main()
