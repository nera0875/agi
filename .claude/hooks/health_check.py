#!/usr/bin/env python3
"""
Architecture Health Check
Quick validation that architecture follows guidelines
Runs optimization analysis and checks against thresholds
"""
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict

# Add hooks to path
sys.path.insert(0, str(Path(__file__).parent))
from optimize_hook import ArchitectureAnalyzer

# Health thresholds
THRESHOLDS = {
    "max_service_lines": 800,  # Services >800 lines should be split
    "max_services": 25,  # Too many services = poor organization
    "max_memory_services": 6,  # Memory tier services (L1/L2/L3 should be ~2 each)
    "max_large_files": 5,  # Alert if 5+ files >500 lines
    "max_complexity_hotspots": 10,  # Alert if 10+ hotspots
    "required_agents": 2,  # Minimum agents
}


def check_health() -> Dict:
    """Run health check and return status"""
    analyzer = ArchitectureAnalyzer()
    analysis = analyzer.analyze()

    stats = analysis["statistics"]
    health = {
        "timestamp": datetime.now().isoformat(),
        "status": "HEALTHY",
        "checks": [],
        "issues": [],
    }

    # Check service count
    service_count = stats.get("services", {}).get("total", 0)
    if service_count > THRESHOLDS["max_services"]:
        health["status"] = "WARNING"
        health["issues"].append(
            f"Too many services ({service_count} > {THRESHOLDS['max_services']})"
        )
        health["checks"].append(
            {"name": "service_count", "status": "FAIL", "value": service_count}
        )
    else:
        health["checks"].append(
            {"name": "service_count", "status": "PASS", "value": service_count}
        )

    # Check memory services
    mem_count = stats.get("services", {}).get("memory_services", 0)
    if mem_count > THRESHOLDS["max_memory_services"]:
        health["status"] = "WARNING"
        health["issues"].append(
            f"Too many memory services ({mem_count} > {THRESHOLDS['max_memory_services']})"
        )
        health["checks"].append(
            {"name": "memory_services", "status": "FAIL", "value": mem_count}
        )
    else:
        health["checks"].append(
            {"name": "memory_services", "status": "PASS", "value": mem_count}
        )

    # Check memory tiers
    tiers = stats.get("memory_tiers", {})
    missing_tiers = [t for t, v in tiers.items() if not v]
    if missing_tiers:
        health["status"] = "CRITICAL"
        health["issues"].append(f"Missing memory tiers: {missing_tiers}")
        health["checks"].append({"name": "memory_tiers", "status": "FAIL", "value": []})
    else:
        health["checks"].append({"name": "memory_tiers", "status": "PASS", "value": tiers})

    # Check agents
    agent_count = stats.get("agents", {}).get("total", 0)
    if agent_count < THRESHOLDS["required_agents"]:
        health["status"] = "WARNING"
        health["issues"].append(
            f"Insufficient agents ({agent_count} < {THRESHOLDS['required_agents']})"
        )
        health["checks"].append(
            {"name": "agents", "status": "FAIL", "value": agent_count}
        )
    else:
        health["checks"].append(
            {"name": "agents", "status": "PASS", "value": agent_count}
        )

    # Check complexity
    hotspot_count = stats.get("complexity_hotspots", 0)
    if hotspot_count > THRESHOLDS["max_complexity_hotspots"]:
        health["status"] = "WARNING"
        health["issues"].append(
            f"Too many complexity hotspots ({hotspot_count} > {THRESHOLDS['max_complexity_hotspots']})"
        )
        health["checks"].append(
            {"name": "complexity", "status": "FAIL", "value": hotspot_count}
        )
    else:
        health["checks"].append(
            {"name": "complexity", "status": "PASS", "value": hotspot_count}
        )

    # Count large files
    large_files = len(
        [r for r in analysis["recommendations"] if r.get("category") == "refactoring"]
    )
    if large_files > THRESHOLDS["max_large_files"]:
        health["status"] = "WARNING"
        health["issues"].append(f"Too many large files needing refactoring ({large_files})")

    # Naming violations
    naming_violations = stats.get("naming_violations", 0)
    if naming_violations > 5:
        health["status"] = "WARNING"
        health["issues"].append(f"Naming convention violations: {naming_violations}")
        health["checks"].append(
            {"name": "naming", "status": "FAIL", "value": naming_violations}
        )
    else:
        health["checks"].append(
            {"name": "naming", "status": "PASS", "value": naming_violations}
        )

    health["recommendations_count"] = len(analysis["recommendations"])

    return health


def display_health(health: Dict):
    """Display health check results"""
    print("\n" + "=" * 70)
    print("ARCHITECTURE HEALTH CHECK")
    print("=" * 70)

    status_icon = {
        "HEALTHY": "✅",
        "WARNING": "⚠️",
        "CRITICAL": "🔴",
    }

    status = health["status"]
    icon = status_icon.get(status, "❓")

    print(f"\n{icon} Status: {status}")
    print(f"Timestamp: {health['timestamp']}")

    # Checks
    print("\nDETAILED CHECKS:")
    print("-" * 70)

    for check in health["checks"]:
        check_icon = "✅" if check["status"] == "PASS" else "❌"
        print(f"{check_icon} {check['name']:20} : {check['value']}")

    # Issues
    if health["issues"]:
        print("\nISSUES DETECTED:")
        print("-" * 70)
        for issue in health["issues"]:
            print(f"• {issue}")

    # Recommendations
    print(f"\nOPTIMIZATION OPPORTUNITIES: {health['recommendations_count']}")

    print("\n" + "=" * 70)

    # Return exit code based on status
    if status == "CRITICAL":
        return 2
    elif status == "WARNING":
        return 1
    else:
        return 0


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Architecture Health Check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--threshold", nargs=2, help="Set custom threshold (key value)")

    args = parser.parse_args()

    # Set custom thresholds if provided
    if args.threshold:
        key, value = args.threshold
        try:
            THRESHOLDS[key] = int(value)
        except ValueError:
            print(f"Invalid threshold value: {value}")
            sys.exit(1)

    # Run health check
    health = check_health()

    if args.json:
        print(json.dumps(health, indent=2))
    else:
        exit_code = display_health(health)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
