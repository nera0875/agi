#!/usr/bin/env python3
"""
Optimize Hook CLI
Command-line interface to run architecture analysis and view reports
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict

PROJECT_ROOT = Path("/home/pilote/projet/agi")
META_DIR = PROJECT_ROOT / ".claude" / "meta"

# Add hooks dir to path
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "hooks"))
from optimize_hook import ArchitectureAnalyzer


def run_analysis() -> Dict:
    """Run architecture analysis"""
    analyzer = ArchitectureAnalyzer()
    analysis = analyzer.analyze()

    # Save report
    META_DIR.mkdir(parents=True, exist_ok=True)
    report_path = META_DIR / "optimize_latest.json"

    with open(report_path, "w") as f:
        json.dump(analysis, f, indent=2)

    return analysis


def display_analysis(analysis: Dict):
    """Display analysis in human-readable format"""
    print("\n" + "=" * 80)
    print("ARCHITECTURE OPTIMIZATION REPORT")
    print("=" * 80)

    # Header
    ts = datetime.fromisoformat(analysis["timestamp"])
    print(f"\n📅 Generated: {ts.strftime('%Y-%m-%d %H:%M:%S')}")

    # Statistics summary
    print("\n📊 ARCHITECTURE STATISTICS:")
    print("-" * 80)

    stats = analysis.get("statistics", {})

    if "services" in stats:
        s = stats["services"]
        print(f"\n🔧 Services ({s.get('total', 0)} total):")
        print(f"   • Wrappers: {s.get('wrappers', 0)}")
        print(f"   • Memory services: {s.get('memory_services', 0)}")
        print(f"   • Embeddings services: {s.get('embeddings_services', 0)}")

    if "agents" in stats:
        a = stats["agents"]
        print(f"\n🤖 Agents ({a.get('total', 0)} total)")

    if "routes" in stats:
        r = stats["routes"]
        print(f"\n🛣️  Routes: {len(r)} files")
        for name, data in r.items():
            print(f"   • {name}: {data.get('lines', 0)} lines")

    if "memory_tiers" in stats:
        mt = stats["memory_tiers"]
        print(f"\n💾 Memory Tiers:")
        for tier, files in mt.items():
            print(f"   • {tier}: {len(files)} services")
            for f in files:
                print(f"       - {f}")

    # Recommendations
    recs = analysis.get("recommendations", [])
    print("\n" + "=" * 80)
    print(f"RECOMMENDATIONS ({len(recs)} found)")
    print("=" * 80)

    if not recs:
        print("\n✅ Architecture is well-optimized!")
        return

    # Group by priority
    by_priority = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for rec in recs:
        priority = rec.get("priority", "LOW")
        if priority in by_priority:
            by_priority[priority].append(rec)

    # Display by priority
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        items = by_priority[priority]
        if not items:
            continue

        icon = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        print(f"\n{icon} {priority} PRIORITY ({len(items)})")
        print("-" * 80)

        for i, rec in enumerate(items, 1):
            print(f"\n{i}. {rec.get('category', 'general').upper()}")
            print(f"   📍 {rec.get('target', 'N/A')}")
            print(f"   ❌ Issue: {rec.get('issue', '')}")
            print(f"   ✅ Action: {rec.get('action', '')}")
            print(f"   💡 Impact: {rec.get('impact', '')}")

            # Details
            if "files" in rec and rec["files"]:
                print(f"   📄 Files affected:")
                for fname, size in list(rec["files"].items())[:3]:
                    print(f"      • {fname}: {size} lines")

            if "services" in rec and rec["services"]:
                print(f"   ⚙️  Services:")
                for svc in rec["services"][:3]:
                    print(f"      • {svc}")

            if "top_hotspots" in rec and rec["top_hotspots"]:
                print(f"   🔥 Complexity hotspots:")
                for hs in rec["top_hotspots"][:2]:
                    print(
                        f"      • {hs['file']}: {hs['lines']}L, "
                        f"{hs['classes']} classes, score={hs['score']}"
                    )

    print("\n" + "=" * 80)


def list_reports():
    """List recent analysis reports"""
    if not META_DIR.exists():
        print("No reports found.")
        return

    reports = sorted(META_DIR.glob("optimize_*.json"), reverse=True)

    if not reports:
        print("No reports found.")
        return

    print("\n" + "=" * 80)
    print("RECENT OPTIMIZATION REPORTS")
    print("=" * 80 + "\n")

    for i, report in enumerate(reports[:10], 1):
        try:
            with open(report) as f:
                data = json.load(f)

            ts = datetime.fromisoformat(data.get("timestamp", ""))
            rec_count = len(data.get("recommendations", []))

            print(f"{i}. {report.name}")
            print(f"   Generated: {ts.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Recommendations: {rec_count}")
            print()
        except Exception:
            pass


def view_report(report_name: str = "optimize_latest.json"):
    """View specific report"""
    report_path = META_DIR / report_name

    if not report_path.exists():
        # Try with .json suffix
        report_path = META_DIR / f"{report_name}.json"

    if not report_path.exists():
        print(f"❌ Report not found: {report_name}")
        return False

    try:
        with open(report_path) as f:
            analysis = json.load(f)

        display_analysis(analysis)
        return True
    except Exception as e:
        print(f"❌ Error reading report: {e}")
        return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Architecture Optimization Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  %(prog)s run              # Run analysis and display results
  %(prog)s list             # List recent reports
  %(prog)s view             # View latest report
  %(prog)s view optimize_20251020_161845  # View specific report
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    subparsers.add_parser("run", help="Run architecture analysis")

    # List command
    subparsers.add_parser("list", help="List recent reports")

    # View command
    view_parser = subparsers.add_parser("view", help="View optimization report")
    view_parser.add_argument(
        "report",
        nargs="?",
        default="optimize_latest",
        help="Report name (default: latest)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "run":
        print("🔍 Running architecture analysis...")
        analysis = run_analysis()
        display_analysis(analysis)

    elif args.command == "list":
        list_reports()

    elif args.command == "view":
        view_report(args.report)


if __name__ == "__main__":
    main()
