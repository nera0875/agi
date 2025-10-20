# Orchestrator Integration - Git Checkpoint Hook

## Quick Start (for Orchestrator Developers)

### 1. Import in Orchestrator

```python
from .claude.hooks.git_checkpoint_wrapper import GitCheckpointManager

class Orchestrator:
    def __init__(self):
        self.git_manager = GitCheckpointManager()

    async def execute_agent_task(self, task):
        """Execute agent task and create checkpoint on success"""
        # Execute task
        result = await self.agent.execute(task)

        # Create checkpoint after success
        if result.status == "success":
            checkpoint = self.git_manager.create_checkpoint(
                task_name=task.name,
                agent_type=task.agent_type,
                status="success",
                task_id=task.id
            )
            self.logger.info(f"Checkpoint created: {checkpoint['status']}")

        return result
```

### 2. Task Execution Flow

```
┌─────────────────────────────────┐
│  Orchestrator.execute_task()    │
└──────────┬──────────────────────┘
           │
           ├─→ agent.execute(task)
           │
           ├─→ RESULT: {status, data, error}
           │
           ├─→ if status == "success":
           │   └─→ GitCheckpointManager.create_checkpoint()
           │       ├─→ subprocess.run(hook script)
           │       ├─→ git commit -m "checkpoint: task_name"
           │       └─→ log to .checkpoint_log
           │
           └─→ return result
```

### 3. Agent Type Mapping

```python
AGENT_TYPES = {
    "ask": "Internal codebase exploration",
    "code": "Backend/Python implementation",
    "frontend": "React/TypeScript implementation",
    "debug": "Testing and debugging",
    "research": "External research",
    "architect": "Architecture design",
    "docs": "Documentation",
    "sre": "Infrastructure monitoring"
}
```

---

## Implementation Patterns

### Pattern 1: Simple Integration

```python
from .claude.hooks.git_checkpoint_wrapper import GitCheckpointManager

manager = GitCheckpointManager()

# After task completes
result = task.execute()

# Create checkpoint
if result.success:
    manager.create_checkpoint(
        task_name="feature_x",
        agent_type="code",
        status="success"
    )
```

### Pattern 2: With Error Handling

```python
try:
    result = await agent.execute(task)

    if result.status == "success":
        checkpoint = manager.create_checkpoint(
            task_name=task.name,
            agent_type=task.agent_type
        )

        if checkpoint["status"] != "complete":
            logger.warning(f"Checkpoint warning: {checkpoint}")

except Exception as e:
    logger.error(f"Task failed: {e}")
    # Don't create checkpoint (status != success)
```

### Pattern 3: Batch Tasks with Checkpoints

```python
async def execute_phase(tasks):
    """Execute phase and checkpoint each successful task"""
    results = []

    for task in tasks:
        result = await agent.execute(task)
        results.append(result)

        # Checkpoint each task individually
        if result.status == "success":
            self.git_manager.create_checkpoint(
                task_name=f"{phase}_{task.name}",
                agent_type=task.agent_type
            )

    return results
```

### Pattern 4: With Task ID Tracking

```python
import uuid

# Generate unique task ID
task_id = str(uuid.uuid4())

# Execute task
result = await agent.execute(task, task_id=task_id)

# Create checkpoint with tracking
if result.status == "success":
    checkpoint = manager.create_checkpoint(
        task_name=task.name,
        agent_type=task.agent_type,
        task_id=task_id
    )

    # Link to metrics
    metrics.checkpoint_created(checkpoint["task_id"])
```

---

## Response Format

### Checkpoint Creation Response

```json
{
  "status": "complete|skipped|error|timeout",
  "task_name": "string",
  "agent_type": "code|debug|frontend|etc",
  "task_id": "uuid",
  "timestamp": "2025-10-20T16:30:45.123456",
  "returncode": 0,
  "output": "✅ Checkpoint saved (5 files)"
}
```

### Status Meanings

| Status | Meaning | Action |
|--------|---------|--------|
| `complete` | Checkpoint created successfully | Continue normally |
| `skipped` | Task failed or no changes | Continue (expected) |
| `error` | Unexpected error | Log warning, continue |
| `timeout` | Exceeded 30 seconds | Log warning, continue |

### Example Responses

```python
# Successful checkpoint
{
  "status": "complete",
  "task_name": "implement_memory_service",
  "agent_type": "code",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-20T16:30:45.123456",
  "returncode": 0,
  "output": "✅ Checkpoint saved (7 files)"
}

# Skipped (task failed)
{
  "status": "skipped",
  "reason": "Task status is failed, not creating checkpoint",
  "task_name": "failing_task",
  "task_id": "abc123"
}

# Error case
{
  "status": "error",
  "task_name": "buggy_task",
  "error": "Hook script not found"
}

# Timeout
{
  "status": "timeout",
  "task_name": "slow_task",
  "timeout_seconds": 30
}
```

---

## Monitoring Checkpoints

### View Recent Checkpoints

```python
# Get last 20 checkpoints
checkpoints = manager.get_recent_checkpoints(limit=20)

for cp in checkpoints:
    print(f"{cp['task_name']}: {cp['status']}")
```

### Access Log File

```python
import json

# Read checkpoint log
with open(".claude/hooks/.checkpoint_log", "r") as f:
    for line in f:
        checkpoint = json.loads(line)
        print(checkpoint)
```

### Create Dashboard

```python
def checkpoint_stats():
    """Generate checkpoint statistics"""
    checkpoints = manager.get_recent_checkpoints(limit=100)

    stats = {
        "total": len(checkpoints),
        "completed": sum(1 for c in checkpoints if c["status"] == "complete"),
        "skipped": sum(1 for c in checkpoints if c["status"] == "skipped"),
        "errors": sum(1 for c in checkpoints if c["status"] == "error"),
        "by_agent": {}
    }

    for cp in checkpoints:
        agent = cp.get("agent_type", "unknown")
        stats["by_agent"][agent] = stats["by_agent"].get(agent, 0) + 1

    return stats
```

---

## Git Log Analysis

### View Checkpoints in Git

```bash
# Show all checkpoints
git log --oneline | grep "checkpoint:"

# Show checkpoint details
git log --grep="checkpoint:" --oneline

# Show specific agent's checkpoints
git log --grep="\[code\]" --oneline

# Show checkpoint commits with diffs
git log --grep="checkpoint:" --stat
```

### Example Git History

```
8f3d4a2 checkpoint: refactor_memory_service [code]
7e2c1b9 checkpoint: write_unit_tests [debug]
6d1a0c8 checkpoint: update_documentation [docs]
5c8f9a7 checkpoint: run_security_scan [sre]
...
```

---

## Error Handling Strategy

### Non-Blocking Failures

Checkpoint failures **should not** interrupt task pipeline:

```python
try:
    # Create checkpoint
    checkpoint = manager.create_checkpoint(...)
except Exception as e:
    # Log but don't re-raise
    logger.warning(f"Checkpoint creation failed: {e}")
    # Continue with next task
```

### Recovery Strategies

```python
# Retry once if timeout
if checkpoint["status"] == "timeout":
    logger.info("Retrying checkpoint...")
    checkpoint = manager.create_checkpoint(...)

# Log errors for later analysis
if checkpoint["status"] in ["error", "timeout"]:
    error_log.append({
        "task": checkpoint["task_name"],
        "issue": checkpoint.get("error", "timeout"),
        "timestamp": checkpoint["timestamp"]
    })
```

---

## Performance Considerations

### Execution Time

- Typical: 0.5-2 seconds per checkpoint
- Timeout: 30 seconds max
- Overhead: < 1% of task time (usually)

### Optimization Tips

1. **Batch commits** - Group related tasks
2. **Avoid large changesets** - Keep commits focused
3. **Monitor for slowness** - Check git performance if needed
4. **Parallel tasks** - Git handles concurrent commits safely

### Example: Batch Optimization

```python
# Instead of 100 individual checkpoints
checkpoints = []
for task in tasks:
    result = await agent.execute(task)
    if result.status == "success":
        # Batch checkpoint at phase end
        checkpoints.append(task)

# Create single phase checkpoint (optional)
if checkpoints:
    manager.create_checkpoint(
        task_name=f"phase_{len(checkpoints)}_tasks",
        agent_type="orchestrator"
    )
```

---

## Debugging

### Check Hook Script

```bash
# Verify script exists and is executable
ls -l .claude/hooks/git_post_task_checkpoint.sh

# Test directly
bash .claude/hooks/git_post_task_checkpoint.sh \
    "test_task" \
    "success" \
    "code"
```

### Check Git Config

```bash
# Verify git is configured
git config user.email
git config user.name

# Check git status
git status
```

### View Checkpoint Log

```bash
# Tail recent checkpoints
tail -20 .claude/hooks/.checkpoint_log | python -m json.tool

# Count checkpoints by agent
grep "agent_type" .claude/hooks/.checkpoint_log | sort | uniq -c
```

### Run Tests

```python
# Test wrapper directly
from .claude.hooks.git_checkpoint_wrapper import GitCheckpointManager

manager = GitCheckpointManager()

# Should skip (no changes)
result = manager.create_checkpoint("test1", "code", "success")
print(f"No changes: {result}")

# Should skip (failed status)
result = manager.create_checkpoint("test2", "code", "failed")
print(f"Failed status: {result}")
```

---

## Best Practices

### Do

✅ Create checkpoint after each task success
✅ Use descriptive task names
✅ Map agent types correctly
✅ Monitor checkpoint log
✅ Handle failures gracefully
✅ Keep task-focused commits

### Don't

❌ Create checkpoints for failed tasks
❌ Force commits if no changes
❌ Block on checkpoint failures
❌ Modify hook script without testing
❌ Assume checkpoint always succeeds
❌ Create mega-commits with unrelated changes

---

## Troubleshooting

### Q: Checkpoint not created?
A: Check task status is "success" and git has changes

### Q: Timeout errors?
A: Check git performance, reduce changesets

### Q: Import error?
A: Verify path: `.claude/hooks/git_checkpoint_wrapper.py`

### Q: Commit message looks wrong?
A: Check git config (user.email, user.name)

### Q: Want to skip checkpoints?
A: Just don't call `create_checkpoint()` (optional integration)

---

## Examples from Real Agents

### Code Agent After Implementation

```python
class CodeAgent:
    async def implement_feature(self, spec):
        # Implement feature
        changes = await self.write_code(spec)

        # Create checkpoint after success
        if changes:
            checkpoint = self.git_manager.create_checkpoint(
                task_name=f"implement_{spec.name}",
                agent_type="code",
                status="success"
            )
            self.logger.info(f"Feature checkpoint: {checkpoint['status']}")

        return changes
```

### Debug Agent After Tests

```python
class DebugAgent:
    async def run_tests(self, test_suite):
        # Run tests
        results = await self.execute_tests(test_suite)

        # Create checkpoint only if all pass
        if all(r.passed for r in results):
            checkpoint = self.git_manager.create_checkpoint(
                task_name=f"tests_{test_suite.name}",
                agent_type="debug",
                status="success"
            )
            self.logger.info(f"Test checkpoint: {checkpoint['status']}")

        return results
```

---

## Integration Checklist

- [ ] Import GitCheckpointManager in orchestrator
- [ ] Initialize manager in orchestrator __init__
- [ ] Call create_checkpoint after task success
- [ ] Handle checkpoint responses (don't block on errors)
- [ ] Monitor .checkpoint_log for issues
- [ ] Test with sample tasks
- [ ] Verify git log shows checkpoints
- [ ] Document in orchestrator README

---

**Version:** 1.0
**Last Updated:** 2025-10-20
**Status:** Ready for Integration
