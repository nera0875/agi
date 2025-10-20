#!/usr/bin/env python3
"""
Test script for optimize_hook.py
Simulates hook execution and displays analysis results
"""
import sys
import os
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Simulate environment
os.environ["CLAUDE_TOOL_NAME"] = "Edit"
os.environ["CLAUDE_FILE_PATH"] = "backend/services/memory_service.py"

# Import and run optimizer
from optimize_hook import ArchitectureAnalyzer
import json

def main():
    """Run architecture analysis and display results"""
    analyzer = ArchitectureAnalyzer()
    analysis = analyzer.analyze()

    print("\n" + "=" * 70)
    print("ARCHITECTURE ANALYSIS REPORT")
    print("=" * 70)

    # Display statistics
    print("\n📊 STATISTICS:")
    print("-" * 70)
    for key, value in analysis["statistics"].items():
        if isinstance(value, dict):
            print(f"\n{key.upper()}:")
            for sub_key, sub_val in value.items():
                if isinstance(sub_val, dict):
                    print(f"  {sub_key}:")
                    for k, v in sub_val.items():
                        print(f"    - {k}: {v}")
                else:
                    print(f"  {sub_key}: {sub_val}")
        else:
            print(f"{key}: {value}")

    # Display recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)

    if analysis["recommendations"]:
        for i, rec in enumerate(analysis["recommendations"], 1):
            priority = rec.get("priority", "INFO")
            category = rec.get("category", "general")
            issue = rec.get("issue", "")
            action = rec.get("action", "")

            print(f"\n{i}. [{priority}] {category.upper()}")
            print(f"   Issue:  {issue}")
            print(f"   Target: {rec.get('target', 'N/A')}")
            print(f"   Action: {action}")
            print(f"   Impact: {rec.get('impact', 'N/A')}")

            # Show details if available
            if "files" in rec:
                print(f"   Files:")
                for file, size in rec["files"].items():
                    print(f"     - {file}: {size} lines")
            if "services" in rec:
                print(f"   Services:")
                for svc in rec["services"]:
                    print(f"     - {svc}")
            if "top_hotspots" in rec:
                print(f"   Top Hotspots:")
                for hs in rec["top_hotspots"]:
                    print(
                        f"     - {hs['file']}: {hs['lines']} lines, "
                        f"{hs['classes']} classes, score={hs['score']}"
                    )
    else:
        print("✅ No major issues detected. Architecture is healthy!")

    print("\n" + "=" * 70)
    print(f"Report generated: {analysis['timestamp']}")
    print("=" * 70 + "\n")

    # Save full report
    report_path = Path(__file__).parent.parent / "meta" / "optimize_test_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(analysis, f, indent=2)

    print(f"Full report saved to: {report_path}")

if __name__ == "__main__":
    main()
