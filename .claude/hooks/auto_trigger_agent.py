#!/usr/bin/env python3
"""
Hook PostToolUse - Auto-trigger agents sur fichiers critiques

Mapping: file patterns → agent à trigger
- Edit schema.py → debug (tests)
- Edit memory_service.py → performance_optimizer
- Edit critical files → appropriate agent validation

Runs in background (non-blocking) via subprocess
"""
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Mapping: file patterns → agent à trigger
TRIGGER_RULES = {
    'backend/api/schema.py': {
        'agent': 'debug',
        'prompt': 'Run tests for GraphQL schema: pytest backend/tests/api/ -q --timeout=10',
        'reason': 'GraphQL schema modified - validate queries/mutations'
    },
    'backend/services/memory_service.py': {
        'agent': 'performance_optimizer',
        'prompt': 'Analyze memory service performance and query optimization',
        'reason': 'Core memory service modified'
    },
    'backend/services/graph_service.py': {
        'agent': 'debug',
        'prompt': 'Test Neo4j graph service: pytest backend/tests/services/test_graph* -q',
        'reason': 'Graph service modified - validate Neo4j operations'
    },
    'backend/services/voyage_wrapper.py': {
        'agent': 'performance_optimizer',
        'prompt': 'Analyze embeddings performance and Voyage API costs',
        'reason': 'Embeddings wrapper modified - check API efficiency'
    },
    'cortex/agi_tools_mcp.py': {
        'agent': 'debug',
        'prompt': 'Validate MCP tools implementation: pytest backend/tests/cortex/ -q',
        'reason': 'MCP tools modified - ensure compatibility'
    },
    'backend/agents/': {
        'agent': 'debug',
        'prompt': 'Test agent implementations: pytest backend/tests/agents/ -q',
        'reason': 'Agent logic modified - validate behavior'
    },
    'CLAUDE.md': {
        'agent': 'docs',
        'prompt': 'Verify CLAUDE.md documentation structure and consistency',
        'reason': 'Core instructions modified'
    },
    'frontend/src/': {
        'agent': 'frontend',
        'prompt': 'Check frontend TypeScript types: npm run build --prefix frontend',
        'reason': 'Frontend code modified - validate build'
    }
}

def get_file_path() -> str:
    """Extract file path from environment"""
    # Claude Code provides file path in CLAUDE_FILE_PATH or TOOL_RESULT
    file_path = os.environ.get('CLAUDE_FILE_PATH', '')

    # Fallback: parse from tool name if available
    tool_context = os.environ.get('CLAUDE_TOOL_CONTEXT', '')

    return file_path

def should_trigger(file_path: str) -> dict | None:
    """Check if file matches trigger rules"""
    if not file_path:
        return None

    for pattern, config in TRIGGER_RULES.items():
        if pattern in file_path:
            return config

    return None

def log_trigger(file_path: str, agent: str, reason: str):
    """Log trigger event to .claude/hooks/.trigger_log"""
    log_dir = Path('/home/pilote/projet/agi/.claude/hooks')
    log_file = log_dir / '.trigger_log'

    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'file': file_path,
            'agent': agent,
            'reason': reason
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        pass  # Silently fail logging

def trigger_agent_background(agent: str, prompt: str, reason: str):
    """Trigger agent in background (non-blocking)"""
    project_root = Path('/home/pilote/projet/agi')

    # Log trigger
    log_trigger('', agent, reason)

    # Launch agent in background via subprocess
    try:
        subprocess.Popen(
            [
                'python3',
                str(project_root / 'run_agents.py'),
                'agent',
                agent
            ],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Detach completely
        )
    except Exception:
        pass  # Silently fail if agents not available

def main():
    """Main hook entry point"""
    # Get environment variables
    tool_name = os.environ.get('CLAUDE_TOOL_NAME', '')
    file_path = get_file_path()

    # Only trigger on Edit/Write operations
    if tool_name not in ['Edit', 'Write']:
        sys.exit(0)

    if not file_path:
        sys.exit(0)

    # Check if should trigger
    config = should_trigger(file_path)
    if config:
        trigger_agent_background(
            agent=config['agent'],
            prompt=config['prompt'],
            reason=config['reason']
        )

    # Always exit 0 (non-blocking - don't interrupt main workflow)
    sys.exit(0)

if __name__ == '__main__':
    main()
