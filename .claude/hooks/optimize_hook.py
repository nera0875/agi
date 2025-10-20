#!/usr/bin/env python3
"""
Optimize Hook - Architecture Analysis & Optimization Recommendations

Trigger: PostToolUse on critical files (Edit/Write: backend/**, .claude/**)
Purpose: Analyze project architecture and propose improvements

Analysis:
- File organization & naming conventions
- Service layer consolidation
- Complexity hotspots (line counts, dependencies)
- Memory system health (L1/L2/L3 tier coverage)
- Agent specialization & coverage

Output: JSON report with actionable recommendations
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

PROJECT_ROOT = Path("/home/pilote/projet/agi")
HOOKS_DIR = PROJECT_ROOT / ".claude" / "hooks"
META_DIR = PROJECT_ROOT / ".claude" / "meta"


class ArchitectureAnalyzer:
    """Analyzes project architecture for optimization opportunities"""

    def __init__(self):
        self.backend_root = PROJECT_ROOT / "backend"
        self.services_dir = self.backend_root / "services"
        self.agents_dir = self.backend_root / "agents"
        self.routes_dir = self.backend_root / "routes"
        self.recommendations = []
        self.stats = {}

    def analyze(self) -> Dict:
        """Run full architecture analysis"""
        self._analyze_services()
        self._analyze_agents()
        self._analyze_routes()
        self._analyze_memory_system()
        self._check_naming_conventions()
        self._detect_complexity_hotspots()

        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.stats,
            "recommendations": self.recommendations,
        }

    def _analyze_services(self):
        """Analyze backend services layer"""
        if not self.services_dir.exists():
            return

        services = {}
        wrappers = []
        memory_services = []
        embeddings_services = []

        for py_file in self.services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                lines = len(py_file.read_text().splitlines())
                services[py_file.name] = lines

                # Categorize services
                if "wrapper" in py_file.name:
                    wrappers.append(py_file.name)
                if "memory" in py_file.name:
                    memory_services.append(py_file.name)
                if "embedding" in py_file.name or "voyage" in py_file.name:
                    embeddings_services.append(py_file.name)

            except Exception:
                pass

        self.stats["services"] = {
            "total": len(services),
            "wrappers": len(wrappers),
            "memory_services": len(memory_services),
            "embeddings_services": len(embeddings_services),
        }

        # Check for over-specialized wrappers
        if len(wrappers) > 3:
            self.recommendations.append(
                {
                    "priority": "LOW",
                    "category": "consolidation",
                    "target": "backend/services/",
                    "issue": f"Found {len(wrappers)} wrapper services",
                    "wrappers": wrappers,
                    "action": "Consider creating unified wrapper manager or facade pattern",
                    "impact": "Reduced cognitive load, easier maintenance",
                }
            )

        # Check memory service duplication
        if len(memory_services) > 4:
            self.recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "consolidation",
                    "target": "backend/services/",
                    "issue": f"Found {len(memory_services)} memory-related services",
                    "services": memory_services,
                    "action": "Review for overlapping responsibilities (L1/L2/L3 tiers clear?)",
                    "impact": "Better separation of concerns",
                }
            )

        # Detect large files (>500 lines = refactoring candidate)
        large_files = {k: v for k, v in services.items() if v > 500}
        if large_files:
            self.recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "refactoring",
                    "target": "backend/services/",
                    "issue": f"Found {len(large_files)} large service files (>500 lines)",
                    "files": large_files,
                    "action": "Split into focused modules (single responsibility)",
                    "impact": "Improved testability and maintainability",
                }
            )

    def _analyze_agents(self):
        """Analyze backend agents layer"""
        if not self.agents_dir.exists():
            return

        agents = {}
        for py_file in self.agents_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                lines = len(py_file.read_text().splitlines())
                agents[py_file.name] = lines
            except Exception:
                pass

        self.stats["agents"] = {"total": len(agents), "files": agents}

        # Check for unspecialized agents
        if len(agents) < 2:
            self.recommendations.append(
                {
                    "priority": "LOW",
                    "category": "expansion",
                    "target": "backend/agents/",
                    "issue": f"Only {len(agents)} agent(s) found",
                    "action": "Consider specialized agents: L1Observer, GraphAnalyzer, MemoryConsolidator",
                    "impact": "Better task distribution, autonomous capabilities",
                }
            )

    def _analyze_routes(self):
        """Analyze API routes layer"""
        if not self.routes_dir.exists():
            return

        routes = {}
        for py_file in self.routes_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                routes[py_file.name] = {
                    "lines": len(content.splitlines()),
                    "endpoints": content.count("@app."),
                }
            except Exception:
                pass

        self.stats["routes"] = routes

        # Check coverage
        if len(routes) < 2:
            self.recommendations.append(
                {
                    "priority": "LOW",
                    "category": "coverage",
                    "target": "backend/routes/",
                    "issue": "Limited route files",
                    "action": "Organize routes by domain: memory.py, graph.py, agents.py, search.py",
                    "impact": "Cleaner API structure, easier to find endpoints",
                }
            )

    def _analyze_memory_system(self):
        """Analyze memory L1/L2/L3 system coverage"""
        expected_tiers = {
            "L1": ["redis_"],
            "L2": ["store_", "memory_"],
            "L3": ["graph_", "neo4j_"],
        }

        services_found = {tier: [] for tier in expected_tiers}
        for py_file in self.services_dir.glob("*.py"):
            name = py_file.name.lower()
            for tier, patterns in expected_tiers.items():
                if any(p in name for p in patterns):
                    services_found[tier].append(py_file.name)

        self.stats["memory_tiers"] = services_found

        # Check each tier coverage
        missing_tiers = [tier for tier, files in services_found.items() if not files]
        if missing_tiers:
            self.recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "architecture",
                    "target": "backend/services/",
                    "issue": f"Missing memory tier implementations: {missing_tiers}",
                    "action": "Verify all L1/L2/L3 tiers are properly implemented",
                    "impact": "Complete memory architecture",
                }
            )

    def _check_naming_conventions(self):
        """Check Python naming conventions compliance"""
        violations = []

        # Check service files
        for py_file in self.services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Should be snake_case
            if py_file.name != py_file.name.lower():
                violations.append(f"❌ {py_file.name} (not lowercase)")

            # Should match pattern: *_service.py, *_wrapper.py, *_client.py, *_memory.py
            valid_suffix = any(
                py_file.name.endswith(s)
                for s in ["_service.py", "_wrapper.py", "_client.py", "_memory.py", "_embeddings.py"]
            )
            if not valid_suffix and py_file.name not in ["database.py"]:
                violations.append(f"⚠️ {py_file.name} (unusual suffix)")

        self.stats["naming_violations"] = len(violations)

        if violations:
            self.recommendations.append(
                {
                    "priority": "LOW",
                    "category": "conventions",
                    "target": "backend/services/",
                    "issue": f"Found {len(violations)} naming convention violations",
                    "violations": violations[:5],  # Top 5
                    "action": "Standardize to: {domain}_{type}.py (e.g., memory_service.py)",
                    "impact": "Better code discoverability",
                }
            )

    def _detect_complexity_hotspots(self):
        """Detect files with high complexity"""
        hotspots = []

        # Sample backend files
        backend_files = list(self.backend_root.rglob("*.py"))[:50]  # Sample first 50

        for py_file in backend_files:
            try:
                content = py_file.read_text()
                lines = len(content.splitlines())

                # Complexity heuristics
                class_count = content.count("class ")
                func_count = content.count("def ")
                import_count = content.count("import ")

                complexity_score = (lines / 50) + (class_count * 2) + func_count

                if complexity_score > 30:
                    hotspots.append(
                        {
                            "file": str(py_file.relative_to(PROJECT_ROOT)),
                            "lines": lines,
                            "classes": class_count,
                            "functions": func_count,
                            "score": round(complexity_score, 1),
                        }
                    )
            except Exception:
                pass

        self.stats["complexity_hotspots"] = len(hotspots)

        if hotspots:
            # Sort by score
            hotspots.sort(key=lambda x: x["score"], reverse=True)

            self.recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "refactoring",
                    "target": "backend/",
                    "issue": f"Found {len(hotspots)} complexity hotspots",
                    "top_hotspots": hotspots[:3],
                    "action": "Prioritize refactoring top files into smaller modules",
                    "impact": "Better testability, easier debugging",
                }
            )


def get_changed_files() -> List[str]:
    """Extract changed file from environment"""
    file_path = os.environ.get("CLAUDE_FILE_PATH", "")
    return [file_path] if file_path else []


def should_analyze(file_path: str) -> bool:
    """Check if file warrants architecture analysis"""
    critical_patterns = [
        "backend/api/",
        "backend/services/",
        "backend/agents/",
        "backend/routes/",
        ".claude/hooks/",
        ".claude/agents/",
        "CLAUDE.md",
    ]

    return any(pattern in file_path for pattern in critical_patterns)


def save_report(analysis: Dict):
    """Save analysis report to JSON"""
    META_DIR.mkdir(parents=True, exist_ok=True)

    # Always save latest
    report_path = META_DIR / "optimize_latest.json"

    with open(report_path, "w") as f:
        json.dump(analysis, f, indent=2)

    # Also save timestamped version
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ts_path = META_DIR / f"optimize_{ts}.json"

    with open(ts_path, "w") as f:
        json.dump(analysis, f, indent=2)


def main():
    """Main optimize hook entry point"""
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    changed_files = get_changed_files()

    # Only trigger on Edit/Write operations
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    if not changed_files or not any(should_analyze(f) for f in changed_files):
        sys.exit(0)

    # Run analysis
    try:
        analyzer = ArchitectureAnalyzer()
        analysis = analyzer.analyze()

        # Save report
        save_report(analysis)

        # Print summary
        if analysis["recommendations"]:
            print(
                f"[Optimize Hook] 🔍 Found {len(analysis['recommendations'])} optimization opportunities"
            )
            for i, rec in enumerate(analysis["recommendations"][:3], 1):
                priority = rec.get("priority", "INFO")
                issue = rec.get("issue", "")[:60]
                print(f"  [{priority}] {rec['category']}: {issue}")
        else:
            print("[Optimize Hook] ✅ Architecture optimized")

    except Exception as e:
        # Silently fail - don't interrupt main workflow
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
