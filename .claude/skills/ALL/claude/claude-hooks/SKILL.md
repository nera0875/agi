---
name: claude-hooks
description: Complete guide to Claude Code hooks - PreToolUse, PostToolUse, and lifecycle events
---

# Claude Code Hooks Guide

Learn how to customize and extend Claude Code's behavior by registering shell commands.

Claude Code hooks are user-defined shell commands that execute at various points in Claude Code's lifecycle. Hooks provide deterministic control over Claude Code's behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them.

## Hook Events Overview

Claude Code provides several hook events that run at different points in the workflow:

* **PreToolUse**: Runs before tool calls (can block them)
* **PostToolUse**: Runs after tool calls complete
* **UserPromptSubmit**: Runs when the user submits a prompt, before Claude processes it
* **Notification**: Runs when Claude Code sends notifications
* **Stop**: Runs when Claude Code finishes responding
* **SubagentStop**: Runs when subagent tasks complete
* **PreCompact**: Runs before Claude Code is about to run a compact operation
* **SessionStart**: Runs when Claude Code starts a new session or resumes an existing session
* **SessionEnd**: Runs when Claude Code session ends

Each event receives different data and can control Claude's behavior in different ways.

## Use Cases

* **Notifications**: Customize how you get notified when Claude Code is awaiting your input or permission to run something.
* **Automatic formatting**: Run `prettier` on .ts files, `gofmt` on .go files, etc. after every file edit.
* **Logging**: Track and count all executed commands for compliance or debugging.
* **Feedback**: Provide automated feedback when Claude Code produces code that does not follow your codebase conventions.
* **Custom permissions**: Block modifications to production files or sensitive directories.

## Quickstart: Command Logging Hook

### Prerequisites

Install `jq` for JSON processing.

### Step 1: Open hooks configuration

Run the `/hooks` slash command and select the `PreToolUse` hook event.

`PreToolUse` hooks run before tool calls and can block them while providing Claude feedback on what to do differently.

### Step 2: Add a matcher

Select `+ Add new matcher…` to run your hook only on Bash tool calls.

Type `Bash` for the matcher. You can use `*` to match all tools.

### Step 3: Add the hook command

Select `+ Add new hook…` and enter:

```bash
jq -r '"\(.tool_input.command) - \(.tool_input.description // "No description")"' >> ~/.claude/bash-command-log.txt
```

### Step 4: Save configuration

Select `User settings` for storage location. This hook will apply to all projects.

### Step 5: Verify the hook

Run `/hooks` again or check `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '\"\\(.tool_input.command) - \\(.tool_input.description // \"No description\")\"' >> ~/.claude/bash-command-log.txt"
          }
        ]
      }
    ]
  }
}
```

### Step 6: Test

Ask Claude to run `ls` and check:

```bash
cat ~/.claude/bash-command-log.txt
```

You should see entries like:

```
ls - Lists files and directories
```

## PostToolUse Hooks Examples

### Code Formatting Hook

Automatically format TypeScript files after editing:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | { read file_path; if echo \"$file_path\" | grep -q '\\.ts$'; then npx prettier --write \"$file_path\"; fi; }"
          }
        ]
      }
    ]
  }
}
```

### Markdown Formatting Hook

Automatically fix missing language tags and formatting issues in markdown files:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/markdown_formatter.py"
          }
        ]
      }
    ]
  }
}
```

Example Python formatter script:

```python
#!/usr/bin/env python3
"""
Markdown formatter for Claude Code output.
Fixes missing language tags and spacing issues while preserving code content.
"""
import json
import sys
import re
import os

def detect_language(code):
    """Best-effort language detection from code content."""
    s = code.strip()

    # JSON detection
    if re.search(r'^\s*[{\[]', s):
        try:
            json.loads(s)
            return 'json'
        except:
            pass

    # Python detection
    if re.search(r'^\s*def\s+\w+\s*\(', s, re.M) or \
       re.search(r'^\s*(import|from)\s+\w+', s, re.M):
        return 'python'

    # JavaScript detection
    if re.search(r'\b(function\s+\w+\s*\(|const\s+\w+\s*=)', s) or \
       re.search(r'=>|console\.(log|error)', s):
        return 'javascript'

    # Bash detection
    if re.search(r'^#!.*\b(bash|sh)\b', s, re.M) or \
       re.search(r'\b(if|then|fi|for|in|do|done)\b', s):
        return 'bash'

    # SQL detection
    if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE)\s+', s, re.I):
        return 'sql'

    return 'text'

def format_markdown(content):
    """Format markdown content with language detection."""
    # Fix unlabeled code fences
    def add_lang_to_fence(match):
        indent, info, body, closing = match.groups()
        if not info.strip():
            lang = detect_language(body)
            return f"{indent}```{lang}\n{body}{closing}\n"
        return match.group(0)

    fence_pattern = r'(?ms)^([ \t]{0,3})```([^\n]*)\n(.*?)(\n\1```)\s*$'
    content = re.sub(fence_pattern, add_lang_to_fence, content)

    # Fix excessive blank lines (only outside code fences)
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.rstrip() + '\n'

# Main execution
try:
    input_data = json.load(sys.stdin)
    file_path = input_data.get('tool_input', {}).get('file_path', '')

    if not file_path.endswith(('.md', '.mdx')):
        sys.exit(0)  # Not a markdown file

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        formatted = format_markdown(content)

        if formatted != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(formatted)
            print(f"✓ Fixed markdown formatting in {file_path}")

except Exception as e:
    print(f"Error formatting markdown: {e}", file=sys.stderr)
    sys.exit(1)
```

Make the script executable:

```bash
chmod +x .claude/hooks/markdown_formatter.py
```

This hook automatically:

* Detects programming languages in unlabeled code blocks
* Adds appropriate language tags for syntax highlighting
* Fixes excessive blank lines while preserving code content
* Only processes markdown files (`.md`, `.mdx`)

## PreToolUse Hooks Examples

### Custom Notification Hook

Get desktop notifications when Claude needs input:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "notify-send 'Claude Code' 'Awaiting your input'"
          }
        ]
      }
    ]
  }
}
```

### File Protection Hook

Block edits to sensitive files:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys; data=json.load(sys.stdin); path=data.get('tool_input',{}).get('file_path',''); sys.exit(2 if any(p in path for p in ['.env', 'package-lock.json', '.git/']) else 0)\""
          }
        ]
      }
    ]
  }
}
```

## Hook Configuration

Hook configuration is stored in `~/.claude/settings.json` for user-level hooks or `.claude/settings.json` for project-level hooks.

### Configuration Structure

```json
{
  "hooks": {
    "HOOK_EVENT": [
      {
        "matcher": "Tool1|Tool2|*",
        "hooks": [
          {
            "type": "command",
            "command": "shell command or script path"
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns

* `Bash` - Matches Bash tool only
* `Read|Write` - Matches multiple tools
* `*` - Matches all tools
* Empty string `""` - Matches for certain events like Notification

## Hook Input Data

Hooks receive JSON input via stdin containing:

* `tool_name`: Name of the tool being called
* `tool_input`: Input parameters for the tool
* Other event-specific data

Extract values using `jq` for shell hooks or `json.load(sys.stdin)` for Python hooks.

## Hook Exit Codes

* `0`: Success, continue normally
* `1`: Error occurred
* `2`: Block the operation (for PreToolUse hooks)

## Security Considerations

Security implications of hooks are critical to consider because hooks run automatically during the agent loop with your current environment's credentials:

* Malicious hooks code can exfiltrate your data
* Always review hooks implementation before registering them
* Never copy hooks from untrusted sources
* Validate hook scripts thoroughly
* Use least privilege principles (only access what's needed)
* Audit hooks regularly for security issues

## Best Practices

* **Keep hooks simple**: Single-purpose hooks are easier to maintain and audit
* **Test thoroughly**: Test hooks with various inputs before deploying
* **Log wisely**: Avoid logging sensitive data (API keys, credentials)
* **Use matchers**: Be specific with tool matchers to avoid unnecessary execution
* **Handle errors**: Always include error handling in hook scripts
* **Document purpose**: Add comments explaining what each hook does
* **Performance**: Keep hook execution time minimal (<1 second ideal)
