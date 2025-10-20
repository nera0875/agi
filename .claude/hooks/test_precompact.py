#!/usr/bin/env python3
"""
Test hook PreCompact sans dépendre de la DB réelle
Simule les opérations pour vérifier la structure
"""

import json
import subprocess
import sys
from pathlib import Path

def test_hook_json_format():
    """Teste que le hook retourne du JSON valide"""
    project_root = Path(__file__).parent.parent.parent
    hook_path = project_root / "cortex/hooks/pre_compact_consolidation.py"

    print("Testing PreCompact hook JSON format...")
    print(f"Hook path: {hook_path}")
    print()

    try:
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse JSON from output
        output_lines = result.stdout.split('\n')
        json_start = None
        for i, line in enumerate(output_lines):
            if line.strip().startswith('{'):
                json_start = i
                break

        if json_start is None:
            print("❌ No JSON output found")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            return False

        json_str = '\n'.join(output_lines[json_start:])
        report = json.loads(json_str)

        print("✅ Valid JSON returned")
        print()
        print("Report structure:")
        print(f"  - success: {report.get('success')}")
        print(f"  - mode: {report.get('mode')}")
        print(f"  - duration_seconds: {report.get('duration_seconds')}")
        print(f"  - actions: {report.get('actions', {})}")
        print(f"  - errors: {len(report.get('errors', []))} errors")
        print()

        # Validate required fields
        required = ['success', 'timestamp', 'mode', 'duration_seconds', 'actions']
        for field in required:
            if field not in report:
                print(f"❌ Missing required field: {field}")
                return False
            print(f"  ✓ {field}")

        print()
        print("✅ All tests passed!")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ Hook timeout (> 10s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_hook_json_format()
    sys.exit(0 if success else 1)
