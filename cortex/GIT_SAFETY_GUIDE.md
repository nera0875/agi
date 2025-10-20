# Git Safety Integration Guide

## Overview

The Git Safety Integration module (`git_safety_integration.py`) provides a **safety wrapper** for orchestrator agent calls, ensuring:

1. **Automatic Backups** - Before critical file modifications
2. **Atomic Checkpoints** - After successful task completion
3. **Intelligent Rollback** - On task failure (soft, hard, or branch-based)
4. **Task Tracking** - Complete execution history and validation

This prevents data loss and enables safe, atomic agent operations on critical files.

## Architecture

### Core Components

```
GitSafetyWrapper
├── create_backup()        # Pre-modification backup via git hook
├── create_checkpoint()    # Post-completion atomic commit
├── rollback()            # Error recovery (3 modes)
└── with_safety()         # Unified safety wrapper

SafeOrchestrator
├── run_agent_safe()           # Execute agent with safety
├── validate_task_sequence()   # Conflict detection
└── export_history()           # Audit trail export

OrchestratorWithSafety (advanced)
├── execute_feature_workflow() # Multi-phase features
└── execute_refactoring()     # Safe refactoring
```

### Integration with Git Hooks

The module uses three existing git hooks from `.claude/hooks/`:

1. **git_pre_modification_backup.sh**
   - Triggers: Before critical file modification
   - Action: Creates `safety/backup-*` branch with atomic commit
   - Returns: Backup branch name for recovery

2. **git_post_task_checkpoint.sh**
   - Triggers: After successful agent task
   - Action: Creates `checkpoint:` commit with task metadata
   - Includes: Task name, agent type, timestamp, changed file count

3. **git_rollback_on_error.sh**
   - Triggers: When agent task fails
   - Modes:
     - **soft**: Undo commit, keep changes in staging
     - **hard**: Complete reset, create backup branch
     - **branch**: Restore from safety backup branch

## Usage

### Simple Usage

```python
from cortex.git_safety_integration import run_with_safety

# Execute agent with automatic safety
result = run_with_safety(
    agent_type="code",
    prompt="Add new feature X",
    critical=True,
    file_path="backend/services/memory_service.py"
)

if result["success"]:
    print(f"✓ Task completed in {result['duration']:.2f}s")
else:
    print(f"✗ Task failed: {result['error']}")
```

### Advanced Usage with SafeOrchestrator

```python
from cortex.git_safety_integration import SafeOrchestrator

orch = SafeOrchestrator()

# Run single agent task
result = orch.run_agent_safe(
    agent_type="code",
    prompt="Refactor memory_service.py",
    critical=True,
    file_path="backend/services/memory_service.py"
)

# Validate sequence before execution
tasks = [
    {"agent_type": "code", "prompt": "...", "file_path": "..."},
    {"agent_type": "frontend", "prompt": "...", "file_path": "..."},
]
validation = orch.validate_task_sequence(tasks)

if validation["valid"]:
    for task in tasks:
        orch.run_agent_safe(**task)

# Export execution history
history_json = orch.export_history()
```

### Feature Workflows

```python
import asyncio
from cortex.orchestrator_with_safety import OrchestratorWithSafety

async def deploy_feature():
    orch = OrchestratorWithSafety()

    result = await orch.execute_feature_workflow(
        feature_name="Notifications",
        backend_tasks=[
            {
                "prompt": "Create GraphQL subscription",
                "file_path": "backend/api/schema.py"
            },
            {
                "prompt": "Implement notification service",
                "file_path": "backend/services/notification_service.py"
            }
        ],
        frontend_tasks=[
            {
                "prompt": "Create useNotification hook",
                "file_path": "frontend/src/hooks/use-notification.ts"
            }
        ],
        test_tasks=[
            {"prompt": "Write unit tests"}
        ]
    )

    return result

result = asyncio.run(deploy_feature())
```

### Safe Refactoring

```python
import asyncio
from cortex.orchestrator_with_safety import OrchestratorWithSafety

async def refactor_critical_file():
    orch = OrchestratorWithSafety()

    result = await orch.execute_refactoring(
        target_file="backend/services/memory_service.py",
        refactor_prompt="Refactor to async/await pattern",
        test_prompt="Run memory service tests"
    )

    # Automatic rollback if tests fail
    return result

result = asyncio.run(refactor_critical_file())
```

## Critical Files Detection

The module automatically identifies critical files based on patterns:

```python
CRITICAL_PATTERNS = [
    "CLAUDE.md",
    ".claude/agents/",
    ".claude/skills/",
    ".claude/commands/",
    "backend/api/schema.py",
    "backend/services/",
    "backend/agents/",
    "cortex/agi_tools_mcp.py",
    "cortex/local_mcp_router.py",
    "cortex/consolidation.py",
    "cortex/agi_orchestrator.py",
]
```

Any file matching these patterns is automatically:
- Backed up before modification
- Rolled back on failure (if critical=True)

## Rollback Modes

### 1. Soft Rollback (Default)

- Undoes the commit
- Preserves changes in staging area
- User can review/fix and recommit

```bash
bash git_rollback_on_error.sh agent_fail "Error message" soft
```

### 2. Hard Rollback

- Complete reset to previous commit
- Creates backup branch before hard reset
- Changes are discarded

```bash
bash git_rollback_on_error.sh agent_fail "Error message" hard
```

### 3. Branch Rollback

- Restores from safety backup branch
- Creates recovery branch
- Best for complex errors

```bash
bash git_rollback_on_error.sh agent_fail "Error message" branch
```

## Result Format

All agent execution returns a standardized dict:

```python
{
    "agent": str,              # Agent type (code, frontend, debug, etc)
    "prompt": str,             # Task prompt (truncated)
    "success": bool,           # Whether task succeeded
    "result": Any,             # Agent output
    "error": Optional[str],    # Error message if failed
    "executed_at": str,        # ISO timestamp
    "duration": float,         # Execution time in seconds
    "critical": bool,          # Whether task was critical
    "file_path": str           # Target file path if applicable
}
```

## Task Validation

Before running parallel tasks, validate for conflicts:

```python
orch = SafeOrchestrator()

tasks = [
    {"agent_type": "code", "prompt": "Edit file A", "file_path": "file_a.py"},
    {"agent_type": "code", "prompt": "Edit file A", "file_path": "file_a.py"},  # Conflict!
    {"agent_type": "frontend", "prompt": "Edit file B", "file_path": "file_b.tsx"},
]

validation = orch.validate_task_sequence(tasks)

if not validation["valid"]:
    print(f"Conflicts detected: {validation['conflicts']}")
    # Fix conflicts and retry
```

## Execution History

Track all executed tasks:

```python
orch = SafeOrchestrator()

# Execute tasks
for task in tasks:
    orch.run_agent_safe(**task)

# Export history
history = orch.export_history(Path("execution_history.json"))

# Or get JSON string
history_json = orch.export_history()
print(history_json)
```

History includes:
- Task name and type
- Success/failure status
- Execution timestamp
- Duration
- Error messages
- File modifications

## Error Handling

### Automatic Recovery

```python
try:
    result = orch.run_agent_safe(
        agent_type="code",
        prompt="Refactor memory_service",
        critical=True,
        file_path="backend/services/memory_service.py",
        rollback_on_error=True  # Automatic rollback on error
    )

    if result["success"]:
        print("✓ Success")
    else:
        # Already rolled back automatically
        print(f"✗ Failed and rolled back: {result['error']}")

except Exception as e:
    # Unexpected error
    print(f"✗ Unexpected error: {e}")
```

### Manual Recovery

```python
if not result["success"]:
    # Manual recovery options:

    # Option 1: View backup branches
    subprocess.run(["git", "branch", "--list", "safety/backup-*"])

    # Option 2: Restore from backup
    subprocess.run(["git", "checkout", "safety/backup-20251020_171000"])

    # Option 3: View rollback log
    with open(".claude/meta/rollback.log") as f:
        print(f.read())
```

## Logging

Module uses Python logging. Configure as needed:

```python
import logging

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels:
- **INFO**: Normal operations (backups, checkpoints, task completion)
- **WARNING**: Non-critical failures (checkpoint failed but task ok)
- **ERROR**: Critical failures (rollback executed, agent error)

## Workflow Examples

### Example 1: Safe Backend Refactoring

```python
async def refactor_backend():
    orch = OrchestratorWithSafety()

    result = await orch.execute_refactoring(
        target_file="backend/services/memory_service.py",
        refactor_prompt="Refactor to use async/await pattern",
        test_prompt="Run all memory service tests"
    )

    # If tests fail, automatically rolls back to safety branch
    # If tests pass, creates checkpoint commit

    print(f"Refactoring: {'✅ SUCCESS' if result['overall_success'] else '❌ FAILED'}")
```

### Example 2: Multi-phase Feature

```python
async def implement_feature():
    orch = OrchestratorWithSafety()

    result = await orch.execute_feature_workflow(
        feature_name="Real-time Notifications",
        backend_tasks=[
            {
                "prompt": "Add notification model to schema",
                "file_path": "backend/api/schema.py"
            },
            {
                "prompt": "Implement subscription resolver",
                "file_path": "backend/api/schema.py"
            },
            {
                "prompt": "Create notification service",
                "file_path": "backend/services/notification_service.py"
            }
        ],
        frontend_tasks=[
            {
                "prompt": "Create notification hook",
                "file_path": "frontend/src/hooks/use-notification.ts"
            },
            {
                "prompt": "Create notification component",
                "file_path": "frontend/src/components/notification.tsx"
            }
        ],
        test_tasks=[
            {"prompt": "Write notification tests"}
        ]
    )

    # Phase stops on first error, with automatic rollback
    print(f"Result: {result['overall_success']}")
```

## Git Workflow Integration

### With Pre-commit Hooks

```python
# In pre-commit hook
from cortex.git_safety_integration import SafeOrchestrator

orch = SafeOrchestrator()

# Validate staged changes
staged_files = subprocess.check_output(
    ["git", "diff", "--cached", "--name-only"]
).decode().split('\n')

for file in staged_files:
    if orch.safety.is_critical_file(file):
        # Require safety checkpoint
        pass
```

### With CI/CD

```python
# In CI/CD pipeline
from cortex.git_safety_integration import SafeOrchestrator
import subprocess

orch = SafeOrchestrator()

# Validate commit history
log = subprocess.check_output(
    ["git", "log", "--oneline", "-n", "10"]
).decode()

# Check for checkpoint commits
if "checkpoint:" in log:
    print("✓ Recent checkpoints found")
else:
    print("⚠ No recent safety checkpoints")
```

## Troubleshooting

### Checkpoints Not Created

1. Check git status: `git status`
2. Verify hooks exist: `ls -la .claude/hooks/`
3. Check .claude/meta/rollback.log for errors
4. Run hook manually: `bash .claude/hooks/git_post_task_checkpoint.sh`

### Backup Branches Pile Up

Clean old backup branches:

```bash
# List all backup branches
git branch --list 'safety/backup-*' -v

# Delete old branches
git branch -d safety/backup-20250101_*
```

### Rollback Failed

View rollback history:

```bash
cat .claude/meta/rollback.log
```

Manual recovery:

```bash
# View backup branches
git branch --list 'safety/backup-*'

# Checkout specific backup
git checkout safety/backup-20251020_171000

# Create recovery branch
git checkout -b recovery/manual-recovery
```

## Performance

- **Backup creation**: ~100-200ms
- **Checkpoint creation**: ~50-100ms
- **Rollback execution**: ~50-150ms
- **Task validation**: <10ms

Total overhead: **<400ms** per task

## Security Considerations

1. **Backup branches** are only created on local repository
2. **Rollback hooks** don't push to remote
3. **Checkpoint commits** use automation signature
4. **History export** includes full audit trail

For remote safety, manually push backup branches:

```bash
git push origin safety/backup-*
```

## Integration with Existing Orchestrator

To integrate with existing `agi_orchestrator.py`:

```python
# In agi_orchestrator.py

from cortex.git_safety_integration import SafeOrchestrator

class AGIOrchestratorWithSafety(AGIOrchestrator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.safety = SafeOrchestrator()

    def execute_agent(self, agent_type, prompt, **kwargs):
        # Wrap existing execution
        return self.safety.run_agent_safe(
            agent_type=agent_type,
            prompt=prompt,
            critical=self._is_critical(kwargs),
            file_path=kwargs.get("file_path")
        )
```

## References

- Git hooks: `.claude/hooks/git_*.sh`
- Integration module: `cortex/git_safety_integration.py`
- Example usage: `cortex/orchestrator_with_safety.py`
- This guide: `cortex/GIT_SAFETY_GUIDE.md`
