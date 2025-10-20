#!/usr/bin/env python3
"""
MetaOrchestrator - Infrastructure .claude/ manager
Audit quotidien automatique, détection patterns, optimisation
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import subprocess

class MetaOrchestrator:
    def __init__(self, project_root: Path = None):
        self.root = project_root or Path(__file__).parent.parent.parent
        self.claude_dir = self.root / ".claude"
        self.reports_dir = self.claude_dir / "meta" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def audit_daily(self) -> dict:
        """Audit quotidien complet 60s max"""
        report = {
            "audit_date": datetime.now().isoformat(),
            "skills": self.analyze_skills(),
            "commands": self.analyze_commands(),
            "hooks": self.analyze_hooks(),
            "agents": self.analyze_agents(),
            "claude_md": self.check_claude_md(),
            "recommendations": []
        }

        # Generate recommendations
        report["recommendations"] = self.generate_recommendations(report)

        # Save report
        filename = f"meta_audit_{datetime.now().strftime('%Y%m%d')}.json"
        with open(self.reports_dir / filename, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def analyze_skills(self) -> dict:
        """Analyse Skills usage"""
        skills_dir = self.claude_dir / "skills"
        if not skills_dir.exists():
            return {"total": 0, "categories": {}, "size_kb": 0}

        skills = list(skills_dir.glob("**/README.md"))

        return {
            "total": len(skills),
            "categories": self.count_by_category(skills),
            "size_kb": sum(s.stat().st_size for s in skills) // 1024
        }

    def analyze_commands(self) -> dict:
        """Analyse Commands"""
        commands_dir = self.claude_dir / "commands"
        if not commands_dir.exists():
            return {"total": 0, "list": []}

        commands = list(commands_dir.glob("*.md"))
        return {
            "total": len(commands),
            "list": [c.stem for c in commands]
        }

    def analyze_hooks(self) -> dict:
        """Analyse Hooks performance"""
        hooks_dir = self.claude_dir / "hooks"
        if not hooks_dir.exists():
            return {"total": 0, "list": []}

        hooks = list(hooks_dir.glob("*.py"))
        return {
            "total": len(hooks),
            "list": [h.stem for h in hooks]
        }

    def analyze_agents(self) -> dict:
        """Analyse Agents"""
        agents_dir = self.claude_dir / "agents"
        if not agents_dir.exists():
            return {"total": 0, "list": []}

        agents = list(agents_dir.glob("*.md"))

        return {
            "total": len(agents),
            "list": [a.stem for a in agents]
        }

    def check_claude_md(self) -> dict:
        """Check CLAUDE.md size"""
        claude_md = self.root / "CLAUDE.md"
        if not claude_md.exists():
            return {"lines": 0, "bloated": False, "recommendation": "File not found"}

        lines = len(claude_md.read_text().splitlines())

        return {
            "lines": lines,
            "bloated": lines > 850,
            "recommendation": "Extract to Skills" if lines > 850 else "OK"
        }

    def generate_recommendations(self, report: dict) -> list:
        """Generate optimization recommendations"""
        recs = []

        # Check CLAUDE.md bloat
        if report["claude_md"]["bloated"]:
            recs.append({
                "type": "optimize",
                "target": "CLAUDE.md",
                "reason": f"{report['claude_md']['lines']} lines (>850)",
                "action": "Extract sections to Skills"
            })

        # Check hooks count
        if report["hooks"]["total"] > 5:
            recs.append({
                "type": "consolidate",
                "target": "hooks/",
                "reason": f"{report['hooks']['total']} hooks (consolidate related)",
                "action": "Group by domain (memory, agents, etc)"
            })

        # Check if reports directory growing
        reports_dir = self.claude_dir / "meta" / "reports"
        if reports_dir.exists():
            reports = list(reports_dir.glob("*.json"))
            if len(reports) > 30:
                recs.append({
                    "type": "cleanup",
                    "target": "meta/reports/",
                    "reason": f"{len(reports)} reports (keep last 15 days)",
                    "action": "Archive or delete old reports"
                })

        return recs

    def count_by_category(self, skills: list) -> dict:
        """Count skills by category"""
        categories = Counter()
        for skill in skills:
            category = skill.parent.parent.name
            categories[category] += 1
        return dict(categories)

    def print_report(self, report: dict) -> None:
        """Pretty print audit report"""
        print("\n" + "="*60)
        print("DAILY META AUDIT")
        print("="*60)
        print(f"Date: {report['audit_date']}")
        print(f"\nSkills: {report['skills']['total']} ({report['skills']['size_kb']}KB)")
        print(f"Commands: {report['commands']['total']}")
        print(f"Hooks: {report['hooks']['total']}")
        print(f"Agents: {report['agents']['total']}")
        print(f"\nCLAUDE.md: {report['claude_md']['lines']} lines ({report['claude_md']['recommendation']})")

        if report["recommendations"]:
            print(f"\nRECOMMENDATIONS ({len(report['recommendations'])}):")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"  {i}. [{rec['type']}] {rec['target']}: {rec['action']}")
        else:
            print("\nNo recommendations - All systems healthy!")
        print("="*60 + "\n")

if __name__ == "__main__":
    orchestrator = MetaOrchestrator()
    report = orchestrator.audit_daily()
    orchestrator.print_report(report)
    print(json.dumps(report, indent=2))
