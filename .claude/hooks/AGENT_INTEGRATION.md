# Agent Integration - Git Rollback Hook

This document shows how to integrate the git rollback hook into agent execution pipelines.

## Quick Integration (Copy-Paste Ready)

### 1. Agent Executor Wrapper

Add this to your agent execution code:

```python
import sys
from pathlib import Path

# Add hooks to path
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))

from rollback_manager import RollbackManager, RollbackMode


def execute_agent_with_rollback(agent_type, prompt, timeout=60):
    """
    Execute agent with automatic rollback on failure
    """
    manager = RollbackManager()

    try:
        # Your actual agent execution here
        result = Task(agent_type, prompt, timeout=timeout)
        return result

    except TimeoutError as e:
        print(f"⏱️ Agent timeout: {e}")
        manager.on_agent_fail(
            agent_name=agent_type,
            error=f"Timeout after {timeout}s",
            mode=RollbackMode.SOFT
        )
        raise

    except Exception as e:
        print(f"❌ Agent failed: {e}")
        manager.on_agent_fail(
            agent_name=agent_type,
            error=str(e),
            mode=RollbackMode.SOFT
        )
        raise
```

### 2. Test Runner Integration

Add this to your test running code:

```python
import subprocess
from rollback_manager import RollbackManager, RollbackMode


def run_tests_with_rollback(test_path="backend/tests/"):
    """
    Run tests with automatic rollback on failure
    """
    manager = RollbackManager()

    print(f"🧪 Running tests: {test_path}")

    try:
        result = subprocess.run(
            ["pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            # Tests failed - rollback with branch mode (safety first)
            output = result.stdout.split('\n')[-10:]  # Last 10 lines
            manager.on_test_fail(
                test_file=test_path,
                error='\n'.join(output),
                mode=RollbackMode.BRANCH
            )
            print("❌ Tests failed, rolled back to safety branch")
            return False

        print("✅ All tests passed")
        return True

    except subprocess.TimeoutExpired:
        manager.on_agent_fail(
            agent_name="pytest",
            error=f"Test timeout (120s)",
            mode=RollbackMode.SOFT
        )
        print("⏱️ Tests timeout, soft rollback applied")
        return False
```

### 3. Build Pipeline Integration

Add this to your build script:

```python
def run_build_pipeline():
    """
    Complete build pipeline with rollback safety
    """
    manager = RollbackManager()

    # Phase 1: Backend tests
    print("\n1️⃣ Backend tests...")
    if not run_tests_with_rollback("backend/tests/"):
        print("Pipeline failed at backend tests")
        return False

    # Phase 2: Frontend build
    print("\n2️⃣ Frontend build...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd="frontend",
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        manager.on_critical_error(
            error=f"Frontend build failed: {result.stderr[:200]}",
            mode=RollbackMode.HARD
        )
        print("Frontend build failed, hard rollback applied")
        return False

    # Phase 3: Frontend tests
    print("\n3️⃣ Frontend tests...")
    # Similar to backend tests...

    print("\n✅ All phases passed!")
    return True
```

## Integration Pattern

### Pattern 1: Sequential Execution (Most Common)

```
Agent execution → If fail → Soft rollback → Preserve work
                ↓
              Tests → If fail → Branch rollback → Safety backup
                ↓
              Build → If fail → Hard rollback → Clean slate
```

**Code:**
```python
try:
    # Execute agent
    result = execute_agent_with_rollback("code", prompt)

    # Run tests
    if not run_tests_with_rollback():
        sys.exit(1)

    # Build
    if not run_build_pipeline():
        sys.exit(1)

except Exception as e:
    print(f"Pipeline failed: {e}")
    sys.exit(1)
```

### Pattern 2: Parallel Agents (Advanced)

```
Agent 1 (code)     → soft rollback if fail
Agent 2 (frontend) → soft rollback if fail
Agent 3 (debug)    → soft rollback if fail
(All in parallel)

Then:
→ Aggregate results
→ If any failed: Branch rollback to safety
```

**Code:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_parallel_agents(agents):
    """Execute multiple agents in parallel"""
    manager = RollbackManager()
    results = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all agents
        futures = {
            executor.submit(execute_agent_with_rollback, agent, prompt): agent
            for agent, prompt in agents
        }

        # Collect results
        for future in as_completed(futures):
            agent = futures[future]
            try:
                results[agent] = future.result()
            except Exception as e:
                results[agent] = f"FAILED: {e}"

    # Check if any failed
    failures = [a for a, r in results.items() if "FAILED" in str(r)]
    if failures:
        print(f"⚠️ {len(failures)} agents failed, rolling back...")
        manager.on_agent_fail(
            agent_name=str(failures),
            error=f"{len(failures)} agents failed",
            mode=RollbackMode.SOFT
        )

    return results
```

## Real-World Examples

### Example 1: Simple Agent with Rollback

```python
#!/usr/bin/env python3

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "hooks"))

from rollback_manager import RollbackManager, RollbackMode

def main():
    manager = RollbackManager()

    try:
        # Execute code agent
        print("Executing code agent...")
        result = Task("code", "Implement memory service")

        print("✅ Success!")
        return 0

    except Exception as e:
        print(f"❌ Failed: {e}")

        # Rollback
        manager.on_agent_fail(
            agent_name="code",
            error=str(e),
            mode=RollbackMode.SOFT
        )

        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Example 2: Full CI Pipeline

```python
#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "hooks"))

from rollback_manager import RollbackManager, RollbackMode

def run_backend_tests(manager):
    """Run backend tests"""
    print("\n🧪 Running backend tests...")
    result = subprocess.run(
        ["pytest", "backend/tests/", "-v"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        manager.on_test_fail(
            test_file="backend/tests/",
            error="pytest failed",
            mode=RollbackMode.BRANCH
        )
        return False
    return True

def run_frontend_build(manager):
    """Build frontend"""
    print("\n📦 Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd="frontend",
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        manager.on_critical_error(
            error="npm build failed",
            mode=RollbackMode.HARD
        )
        return False
    return True

def main():
    manager = RollbackManager()

    # Backend tests
    if not run_backend_tests(manager):
        print("❌ Backend tests failed")
        return 1

    # Frontend build
    if not run_frontend_build(manager):
        print("❌ Frontend build failed")
        return 1

    print("\n✅ All checks passed!")
    manager.print_status()
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Modes Decision Tree

```
Agent Failed?
├─ Yes, timeout or minor issue
│  └─ Use: SOFT (preserve work, easy retry)
│
├─ No, check if tests failed
│
Tests Failed?
├─ Yes, simple test failure
│  └─ Use: SOFT (preserve work, debug)
│
├─ Yes, but complex issue
│  └─ Use: BRANCH (restore from safety)
│
├─ No, check if build failed
│
Build Failed?
├─ Yes, frontend build
│  └─ Use: HARD (clean slate)
│
├─ Yes, infrastructure change
│  └─ Use: BRANCH (restore known-good)
│
└─ All passed! ✅
```

## Monitoring

### Check Rollback Frequency

```python
manager = RollbackManager()
history = manager.get_log()

if len(history) > 10:
    print(f"⚠️ High rollback frequency: {len(history)} in recent period")
    print("   → Investigate system stability")
```

### View History

```bash
# Last 10 rollbacks
tail -10 .claude/meta/rollback.log

# Count by mode
grep "SOFT" .claude/meta/rollback.log | wc -l    # soft rollbacks
grep "HARD" .claude/meta/rollback.log | wc -l    # hard rollbacks
grep "BRANCH" .claude/meta/rollback.log | wc -l  # branch rollbacks
```

## Best Practices

1. **Always use SOFT for agent failures** - preserves work for debugging
2. **Use BRANCH for test failures** - safety first approach
3. **Use HARD only for critical infrastructure** - know what you're doing
4. **Monitor rollback frequency** - high rate = underlying issues
5. **Create safety branches regularly** - `git branch safety/backup-$(date +%Y%m%d_%H%M%S)`
6. **Review rollback history** - learn from failures
7. **Document why rollback happened** - helps debugging

## Troubleshooting

### "No previous commit"
- Normal on first commit
- Script handles gracefully

### "No safety branch found"
- Script falls back to soft reset
- Create safety branches: `git branch safety/backup-latest`

### "Rollback timeout"
- Rare (>30s)
- Check git status: `git status --short`

### High rollback rate
- Check system stability
- Review test failures
- Investigate agent issues

---

**Integration ready!** Copy examples above and adapt to your pipeline.
