---
name: claude-mcp
description: Model Context Protocol - MCP servers integration, configuration, and management for Claude Code
---

# Claude MCP - Model Context Protocol Integration

## Overview

The Model Context Protocol (MCP) is an open-source standard that enables Claude Code to connect to hundreds of external tools, databases, and APIs. MCP servers provide access to custom integrations, data sources, and specialized capabilities beyond Claude's native knowledge.

## What You Can Do with MCP

MCP servers enable Claude Code to:

- **Implement features from issue trackers**: "Add the feature described in JIRA issue ENG-4521 and create a PR on GitHub."
- **Analyze monitoring data**: "Check Sentry and Statsig to check usage of feature ENG-4521."
- **Query databases**: "Find emails of 10 random users based on our Postgres database."
- **Integrate designs**: "Update email template based on new Figma designs."
- **Automate workflows**: "Create Gmail drafts inviting users to feedback sessions."

## Popular MCP Server Categories

### Development & Testing Tools
- **Sentry** - Monitor errors, debug production issues
- **Socket** - Security analysis for dependencies
- **Hugging Face** - Access Hugging Face Hub information and Gradio AI Applications
- **Jam** - Debug faster with AI agents accessing Jam recordings

### Project Management & Documentation
- **Asana** - Interact with Asana workspace to keep projects on track
- **Atlassian** - Manage Jira tickets and Confluence docs
- **Linear** - Integrate with Linear's issue tracking
- **Notion** - Read docs, update pages, manage tasks
- **Monday** - Manage monday.com boards
- **Fireflies** - Extract insights from meeting transcripts
- **Box** - Ask questions about enterprise content

### Databases & Data Management
- **Airtable** - Read/write records, manage bases and tables
- **HubSpot** - Access and manage CRM data
- **Daloopa** - High quality financial data from SEC Filings

### Payments & Commerce
- **Stripe** - Payment processing, subscription management
- **PayPal** - Commerce capabilities and payment processing
- **Plaid** - Banking data, financial account linking
- **Square** - Payments, inventory, orders

### Design & Media
- **Figma** - Bring full Figma context to code generation
- **Canva** - Browse, summarize, and generate Canva designs
- **Cloudinary** - Upload, manage, transform media assets
- **invideo** - Build video creation capabilities

### Infrastructure & DevOps
- **Cloudflare** - Build applications, monitor performance, manage security
- **Netlify** - Create, deploy, and manage websites
- **Stytch** - Configure and manage authentication services
- **Vercel** - Search documentation, manage projects and deployments

### Automation & Integration
- **Zapier** - Connect to nearly 8,000 apps
- **Workato** - Access applications, workflows via Workato

### Other Categories
- **ClickUp** - Task management, project tracking
- **Intercom** - Real-time customer conversations and tickets

## Installing MCP Servers

### Option 1: Add a Remote HTTP Server

HTTP servers are recommended for remote MCP servers (most widely supported).

```bash
# Basic syntax
claude mcp add --transport http <name> <url>

# Example: Connect to Notion
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Example with Bearer token
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### Option 2: Add a Remote SSE Server

Server-Sent Events transport (deprecated, use HTTP where available).

```bash
# Basic syntax
claude mcp add --transport sse <name> <url>

# Example: Connect to Asana
claude mcp add --transport sse asana https://mcp.asana.com/sse

# Example with authentication header
claude mcp add --transport sse private-api https://api.company.com/sse \
  --header "X-API-Key: your-key-here"
```

### Option 3: Add a Local Stdio Server

Stdio servers run as local processes (ideal for system access or custom scripts).

```bash
# Basic syntax
claude mcp add --transport stdio <name> [args...] -- <command>

# Example: Add Airtable server
claude mcp add --transport stdio airtable --env AIRTABLE_API_KEY=YOUR_KEY \
  -- npx -y airtable-mcp-server
```

**Understanding the "--" parameter**:
- Everything before `--` are Claude CLI options (`--env`, `--scope`)
- Everything after `--` is the command to run the MCP server
- Prevents conflicts between Claude's flags and server's flags

## Managing MCP Servers

### Core Commands

```bash
# List all configured servers
claude mcp list

# Get details for specific server
claude mcp get github

# Remove a server
claude mcp remove github

# Check server status (within Claude Code)
/mcp
```

### Useful Flags

- `--scope local` (default): Available only in current project
- `--scope project`: Shared via `.mcp.json` (team collaboration)
- `--scope user`: Available across all projects (personal utilities)
- `--env KEY=value`: Set environment variables
- `MCP_TIMEOUT=10000`: Configure startup timeout (milliseconds)
- `MAX_MCP_OUTPUT_TOKENS=50000`: Increase output limit (default 10,000)

## MCP Installation Scopes

### Local Scope
Personal servers, experimental configs, sensitive credentials specific to one project (default, private).

```bash
claude mcp add --transport http stripe https://mcp.stripe.com
```

### Project Scope
Team-shared servers stored in `.mcp.json` (checked into version control). All team members get same tools.

```bash
claude mcp add --transport http paypal --scope project https://mcp.paypal.com/mcp
```

Requires approval before first use. Reset with: `claude mcp reset-project-choices`

### User Scope
Cross-project accessibility, available across all projects on your machine (personal utilities).

```bash
claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com/anthropic
```

### Scope Precedence
Local > Project > User (local configs override shared ones)

## Environment Variable Expansion

`.mcp.json` supports environment variable expansion for team flexibility:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "${SERVER_PATH}",
      "args": ["--config", "${CONFIG_PATH:-/default/config}"],
      "env": {
        "API_KEY": "${API_KEY}",
        "PORT": "8080"
      }
    }
  }
}
```

Syntax:
- `${VAR}` - Expands to environment variable
- `${VAR:-default}` - Uses default if VAR not set

## Plugin MCP Servers

Plugins can bundle MCP servers, automatically providing tools when plugin is enabled.

### Plugin Configuration Methods

In `.mcp.json` at plugin root:
```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

Or inline in `plugin.json`:
```json
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

### Features
- **Automatic lifecycle**: Servers start when plugin enables
- **Environment access**: `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- **Multiple transports**: stdio, SSE, HTTP support (varies by server)
- **Team consistency**: Same tools when plugin installed

## Windows-Specific Configuration

Native Windows requires `cmd /c` wrapper for `npx`-based local servers:

```bash
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

Without this wrapper, you'll get "Connection closed" errors.

## Security Considerations

- **Third-party risk**: Use MCP servers at your own risk - Anthropic hasn't verified all servers
- **Prompt injection**: Be careful with servers fetching untrusted content
- **Credentials**: Keep API keys in environment variables, not in configs
- **Project scopes**: Require approval before first use for security

## Common Integration Patterns

### Connect to GitHub
```bash
claude mcp add --transport http github https://mcp.github.com/mcp
```

### Connect to Stripe (with token)
```bash
claude mcp add --transport http stripe --scope project https://mcp.stripe.com \
  --header "Authorization: Bearer sk_live_YOUR_TOKEN"
```

### Add ClickUp
```bash
claude mcp add --transport stdio clickup --env CLICKUP_API_KEY=YOUR_KEY \
  -- npx -y @hauptsache.net/clickup-mcp
```

### Add Custom Local Server
```bash
claude mcp add --transport stdio custom-api -- python /path/to/server.py --port 8080
```

## Finding More Servers

- [MCP GitHub Registry](https://github.com/modelcontextprotocol/servers) - 100+ community servers
- [MCP Documentation](https://modelcontextprotocol.io/) - Build custom servers with MCP SDK
- Individual service documentation (Figma, Stripe, etc.)

## Troubleshooting

### Server Not Responding
- Check `MCP_TIMEOUT` (default ~30s)
- Verify authentication credentials
- Ensure network connectivity for HTTP/SSE servers
- Check firewall for stdio servers

### Output Token Limit Exceeded
- Increase `MAX_MCP_OUTPUT_TOKENS` environment variable
- Default is 10,000 tokens
- Claude Code displays warning when limit exceeded

### Project Scope Approval Issues
- Run `claude mcp reset-project-choices` to reset approval state
- Re-run command to re-approve

## Integration Best Practices

1. **Start with HTTP servers** for remote services (most stable)
2. **Use project scope** for team-shared integrations
3. **Secure credentials** with environment variables
4. **Test locally first** before adding to team project scope
5. **Document** which MCP servers your project requires
6. **Monitor output tokens** for large data operations
7. **Version pins** for local stdio servers when needed
