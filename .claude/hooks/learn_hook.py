#!/usr/bin/env python3
"""
Learn Hook - Détecte patterns répétés → Propose nouveau skill
Trigger: Post-session analysis (periodic)
Analyse patterns d'exécution et propose skills optimisés

Strategy:
1. Scan .claude/hooks/.trigger_log → Tâches répétées
2. Count occurrences sur 7 derniers jours
3. If count >= 5 → propose skill
4. Save proposals à .claude/skills/proposals/
"""
import sys
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def parse_trigger_log() -> list:
    """Parse .trigger_log pour extraire tâches"""
    log_file = Path(__file__).parent / '.trigger_log'

    if not log_file.exists():
        return []

    entries = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Filter: last 7 days only
                    timestamp = datetime.fromisoformat(entry['timestamp'])
                    if datetime.now() - timestamp <= timedelta(days=7):
                        entries.append(entry)
                except:
                    pass
    except:
        pass

    return entries


def analyze_patterns(entries: list) -> dict:
    """Analyse patterns dans entries"""
    # Count par (file, agent) pair
    file_agent_pairs = Counter()
    agent_reasons = Counter()

    for entry in entries:
        file_path = entry.get('file', '').split('/')[-1]  # Just filename
        agent = entry.get('agent', 'unknown')
        reason = entry.get('reason', '')

        file_agent_pairs[(file_path, agent)] += 1
        agent_reasons[(agent, reason)] += 1

    return {
        'file_agent_pairs': file_agent_pairs,
        'agent_reasons': agent_reasons
    }


def extract_skill_category(agent: str) -> str:
    """Map agent → skill category"""
    mapping = {
        'debug': '02-quality',
        'code': '03-backend',
        'frontend': '04-frontend',
        'architect': '05-architecture',
        'docs': '07-docs',
        'performance_optimizer': '06-workflow',
        'security_sentinel': '02-quality',
        'infra_watch': '06-workflow'
    }
    return mapping.get(agent, '08-custom')


def propose_skill(pattern: tuple, count: int, agent: str) -> dict:
    """Génère proposition skill pour pattern"""
    file_or_reason, _ = pattern

    # Generate skill name
    keywords = file_or_reason.lower().split()[:3]
    skill_name = f"{agent.replace('_', '-')}/{'-'.join(keywords)}"

    category = extract_skill_category(agent)
    priority = 'HIGH' if count >= 10 else 'MEDIUM'

    return {
        'skill_name': skill_name,
        'category': category,
        'agent': agent,
        'reason': f"Pattern detected {count} times in 7 days",
        'priority': priority,
        'detected_pattern': file_or_reason,
        'occurrence_count': count,
        'proposed_template': {
            'name': skill_name,
            'category': category,
            'description': f"Optimized workflow for repeated task on {file_or_reason}",
            'agent_type': agent
        },
        'timestamp': datetime.now().isoformat()
    }


def main():
    """Main learn hook"""
    # Parse logs
    entries = parse_trigger_log()

    if not entries:
        print("[Learn Hook] No log entries found")
        sys.exit(0)

    # Analyze patterns
    patterns = analyze_patterns(entries)

    proposals = []

    # Process file+agent pairs
    for (file_path, agent), count in patterns['file_agent_pairs'].items():
        if count >= 5:  # Threshold
            proposal = propose_skill((file_path, agent), count, agent)
            proposals.append(proposal)

    # Process agent+reason pairs
    for (agent, reason), count in patterns['agent_reasons'].items():
        if count >= 5 and reason:  # Threshold
            proposal = propose_skill((reason, agent), count, agent)
            proposals.append(proposal)

    # Save proposals
    if proposals:
        output_dir = Path(__file__).parent.parent / 'skills' / 'proposals'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as timestamped file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f'proposals_{timestamp}.json'

        result = {
            'generated_at': datetime.now().isoformat(),
            'patterns_analyzed': len(entries),
            'proposals_count': len(proposals),
            'proposals': proposals
        }

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"[Learn Hook] Generated {len(proposals)} skill proposals")
        print(f"[Learn Hook] Saved to {output_file}")
    else:
        print("[Learn Hook] No patterns detected (threshold: 5+ occurrences)")

    sys.exit(0)


if __name__ == '__main__':
    main()
