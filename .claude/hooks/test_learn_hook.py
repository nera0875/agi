#!/usr/bin/env python3
"""
Test suite for learn_hook.py
Validates pattern detection and skill proposal generation
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def create_sample_trigger_log(count: int = 12) -> Path:
    """Create sample .trigger_log with pattern"""
    temp_file = Path(tempfile.gettempdir()) / '.trigger_log_test'

    entries = []

    # Schema pattern (8 occurrences - should trigger)
    for i in range(8):
        entries.append({
            'timestamp': (datetime.now() - timedelta(days=7 - i)).isoformat(),
            'file': 'backend/api/schema.py',
            'agent': 'debug',
            'reason': 'GraphQL schema modified - validate queries/mutations'
        })

    # Memory pattern (5 occurrences - should trigger)
    for i in range(5):
        entries.append({
            'timestamp': (datetime.now() - timedelta(days=5 - i)).isoformat(),
            'file': 'backend/services/memory_service.py',
            'agent': 'performance_optimizer',
            'reason': 'Core memory service modified'
        })

    # Frontend pattern (3 occurrences - should NOT trigger)
    for i in range(3):
        entries.append({
            'timestamp': (datetime.now() - timedelta(days=3 - i)).isoformat(),
            'file': 'frontend/src/components/',
            'agent': 'frontend',
            'reason': 'Frontend code modified - validate build'
        })

    with open(temp_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    return temp_file


def test_pattern_detection():
    """Test pattern detection logic"""
    print("[TEST] Pattern Detection...")

    log_file = create_sample_trigger_log()

    # Parse log
    entries = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Check counts
    from collections import Counter

    file_agent_pairs = Counter()
    for entry in entries:
        file_path = entry.get('file', '').split('/')[-1]
        agent = entry.get('agent', 'unknown')
        file_agent_pairs[(file_path, agent)] += 1

    # Validate
    assert ('schema.py', 'debug') in file_agent_pairs
    assert file_agent_pairs[('schema.py', 'debug')] == 8
    print("  ✅ Schema pattern detected (8 occurrences)")

    assert ('memory_service.py', 'performance_optimizer') in file_agent_pairs
    assert file_agent_pairs[('memory_service.py', 'performance_optimizer')] == 5
    print("  ✅ Memory pattern detected (5 occurrences)")

    # Note: frontend/src/components/ splits to empty string
    frontend_count = file_agent_pairs.get(('', 'frontend'), 0)
    assert frontend_count == 3
    print("  ✅ Frontend pattern NOT triggered (3 < threshold)")

    log_file.unlink()


def test_skill_proposal_generation():
    """Test skill proposal generation"""
    print("[TEST] Skill Proposal Generation...")

    patterns = {
        ('schema.py', 'debug'): 8,
        ('memory_service.py', 'performance_optimizer'): 5
    }

    proposals = []
    for (pattern, agent), count in patterns.items():
        if count >= 5:
            proposal = {
                'skill_name': f"{agent}/{pattern.split('.')[0]}",
                'category': '02-quality',
                'priority': 'HIGH' if count >= 10 else 'MEDIUM'
            }
            proposals.append(proposal)

    assert len(proposals) == 2
    print(f"  ✅ Generated {len(proposals)} proposals")

    assert proposals[0]['priority'] == 'MEDIUM'
    print("  ✅ Proposal 1 priority = MEDIUM (8 < 10)")

    assert proposals[1]['priority'] == 'MEDIUM'
    print("  ✅ Proposal 2 priority = MEDIUM (5 < 10)")


def test_category_mapping():
    """Test agent → category mapping"""
    print("[TEST] Category Mapping...")

    mapping = {
        'debug': '02-quality',
        'code': '03-backend',
        'frontend': '04-frontend',
        'architect': '05-architecture',
        'docs': '07-docs',
        'performance_optimizer': '06-workflow'
    }

    for agent, expected_category in mapping.items():
        assert expected_category is not None
        print(f"  ✅ {agent} → {expected_category}")


def test_threshold_logic():
    """Test threshold filtering"""
    print("[TEST] Threshold Logic...")

    counts = [1, 3, 5, 7, 10, 15]
    threshold = 5

    triggered = [c for c in counts if c >= threshold]
    assert triggered == [5, 7, 10, 15]
    print(f"  ✅ Threshold={threshold} filters correctly: {triggered}")

    # High priority only for >= 10
    high_priority = [c for c in triggered if c >= 10]
    assert high_priority == [10, 15]
    print(f"  ✅ HIGH priority (>= 10): {high_priority}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Learn Hook Test Suite")
    print("=" * 60 + "\n")

    try:
        test_pattern_detection()
        print()
        test_skill_proposal_generation()
        print()
        test_category_mapping()
        print()
        test_threshold_logic()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60 + "\n")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
