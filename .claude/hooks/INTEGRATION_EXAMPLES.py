#!/usr/bin/env python3
"""
Git Rollback Integration Examples
Real-world code examples for integration into agent executor and test runners
"""

import sys
from pathlib import Path

# Import the rollback manager
sys.path.insert(0, str(Path(__file__).parent))
from rollback_manager import RollbackManager, RollbackMode


# ============================================================================
# EXAMPLE 1: Agent Executor with Rollback
# ============================================================================

class AgentExecutor:
    """
    Execute agents with automatic rollback on failure
    """

    def __init__(self):
        self.rollback = RollbackManager()
        self.successful_agents = 0
        self.failed_agents = 0

    def execute(self, agent_type: str, prompt: str, timeout: int = 60):
        """
        Execute agent with rollback on failure

        Example:
            executor = AgentExecutor()
            executor.execute("code", "Implement memory service")
        """
        print(f"\n🤖 Executing {agent_type} agent...")

        try:
            # Simulate agent execution
            # In real code: result = Task(agent_type, prompt, timeout)
            result = self._mock_agent_execution(agent_type, prompt)

            self.successful_agents += 1
            print(f"✅ {agent_type} agent succeeded")
            return result

        except TimeoutError as e:
            self.failed_agents += 1
            print(f"⏱️ {agent_type} agent timeout: {e}")

            # Rollback with soft mode (preserve work for analysis)
            self.rollback.on_agent_fail(
                agent_name=agent_type,
                error=f"Timeout: {str(e)}",
                mode=RollbackMode.SOFT,
            )
            raise

        except Exception as e:
            self.failed_agents += 1
            print(f"❌ {agent_type} agent failed: {e}")

            # Rollback with soft mode (preserve work for debugging)
            self.rollback.on_agent_fail(
                agent_name=agent_type,
                error=str(e),
                mode=RollbackMode.SOFT,
            )
            raise

    def print_stats(self):
        """Print execution statistics"""
        total = self.successful_agents + self.failed_agents
        success_rate = (
            (self.successful_agents / total * 100) if total > 0 else 0
        )
        print(
            f"\n📊 Execution Stats:"
            f"\n  Successful: {self.successful_agents}"
            f"\n  Failed: {self.failed_agents}"
            f"\n  Success Rate: {success_rate:.1f}%"
        )

    @staticmethod
    def _mock_agent_execution(agent_type: str, prompt: str):
        """Mock agent execution for demo"""
        if "error" in prompt.lower():
            raise RuntimeError(f"Simulated error in {agent_type}")
        return {"status": "success", "agent": agent_type}


# ============================================================================
# EXAMPLE 2: Test Runner with Rollback
# ============================================================================

class TestRunner:
    """
    Run tests with automatic rollback on failure
    """

    def __init__(self):
        self.rollback = RollbackManager()

    def run_pytest(self, test_path: str = "backend/tests/"):
        """
        Run pytest with rollback on failure

        Example:
            runner = TestRunner()
            runner.run_pytest("backend/tests/test_memory.py")
        """
        import subprocess

        print(f"\n🧪 Running tests: {test_path}")

        try:
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                print(f"❌ Tests failed")

                # Rollback with branch mode (safety first)
                self.rollback.on_test_fail(
                    test_file=test_path,
                    error=result.stdout[-500:],  # Last 500 chars
                    mode=RollbackMode.BRANCH,
                )
                return False

            print(f"✅ All tests passed")
            return True

        except subprocess.TimeoutExpired:
            print(f"⏱️ Tests timeout (120s)")

            # Fallback to soft rollback (preserve for investigation)
            self.rollback.on_agent_fail(
                agent_name="pytest",
                error="Test timeout (120s)",
                mode=RollbackMode.SOFT,
            )
            return False

    def run_npm_build(self):
        """
        Run npm build with rollback on failure

        Example:
            runner = TestRunner()
            runner.run_npm_build()
        """
        import subprocess

        print(f"\n📦 Building frontend...")

        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd="frontend",
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                print(f"❌ Build failed")

                # Rollback on build failure (hard mode for critical)
                self.rollback.on_critical_error(
                    error=f"Frontend build failed: {result.stderr[-300:]}",
                    mode=RollbackMode.HARD,
                )
                return False

            print(f"✅ Build succeeded")
            return True

        except subprocess.TimeoutExpired:
            print(f"⏱️ Build timeout")
            self.rollback.on_critical_error(
                error="Frontend build timeout (60s)",
                mode=RollbackMode.SOFT,
            )
            return False


# ============================================================================
# EXAMPLE 3: CI/CD Pipeline with Rollback
# ============================================================================

def run_ci_pipeline():
    """
    Complete CI/CD pipeline with rollback
    """
    print("\n🚀 CI/CD PIPELINE")
    print("=" * 50)

    executor = AgentExecutor()
    tester = TestRunner()

    try:
        # Phase 1: Execute agents
        print("\n📋 PHASE 1: Agent Execution")
        executor.execute("code", "Implement feature X")
        executor.execute("frontend", "Create UI component")
        executor.execute("debug", "Run tests")

        # Phase 2: Run tests
        print("\n📋 PHASE 2: Testing")
        if not tester.run_pytest("backend/tests/"):
            print("⚠️ Backend tests failed, rolling back...")
            return False

        # Phase 3: Build
        print("\n📋 PHASE 3: Build")
        if not tester.run_npm_build():
            print("⚠️ Frontend build failed, rolling back...")
            return False

        # Success
        print("\n" + "=" * 50)
        print("✅ ALL PHASES PASSED")
        executor.print_stats()
        return True

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        executor.print_stats()
        return False


# ============================================================================
# EXAMPLE 4: Monitoring Rollback Frequency
# ============================================================================

def monitor_rollback_health():
    """
    Monitor rollback frequency and system health
    """
    manager = RollbackManager()

    history = manager.get_log()

    print("\n📊 ROLLBACK HEALTH CHECK")
    print("=" * 50)

    if not history:
        print("✅ No rollbacks (system healthy)")
        return

    # Analyze rollbacks
    soft_count = sum(1 for line in history if "SOFT" in line)
    hard_count = sum(1 for line in history if "HARD" in line)
    branch_count = sum(1 for line in history if "BRANCH" in line)

    print(f"\n📈 Rollback Statistics:")
    print(f"  Soft (recoverable):    {soft_count}")
    print(f"  Hard (discarded):      {hard_count}")
    print(f"  Branch (critical):     {branch_count}")
    print(f"  Total:                 {len(history)}")

    # Alert on high frequency
    if len(history) > 10:
        print(f"\n⚠️ WARNING: High rollback frequency ({len(history)} in last period)")
        print("   → Check system stability")
        print("   → Review recent commits")
        print("   → Consider environment issues")

    # Show recent
    print(f"\n📜 Last 3 rollbacks:")
    for line in history[-3:]:
        print(f"   {line}")


# ============================================================================
# EXAMPLE 5: Integration Point - Actual Usage
# ============================================================================

def demo():
    """
    Demo showing all integration examples
    """
    print("\n" + "=" * 60)
    print("🎯 GIT ROLLBACK INTEGRATION EXAMPLES")
    print("=" * 60)

    # Example 1: Agent Executor
    print("\n\n1️⃣ AGENT EXECUTOR WITH ROLLBACK")
    print("-" * 60)
    executor = AgentExecutor()
    try:
        executor.execute("code", "Implement memory service")
        executor.execute("frontend", "Create dashboard")
    except Exception:
        pass
    executor.print_stats()

    # Example 2: Test Runner
    print("\n\n2️⃣ TEST RUNNER WITH ROLLBACK")
    print("-" * 60)
    runner = TestRunner()
    # runner.run_pytest()
    print("(Skipped for demo - would run actual tests)")

    # Example 3: Monitor Health
    print("\n\n3️⃣ ROLLBACK HEALTH MONITORING")
    print("-" * 60)
    monitor_rollback_health()

    print("\n" + "=" * 60)
    print("✅ INTEGRATION EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Run demo
    demo()

    # Or run CI pipeline
    # success = run_ci_pipeline()
    # exit(0 if success else 1)
