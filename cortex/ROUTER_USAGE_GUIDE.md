# MCP Router Usage Guide

## Quick Start

### 1. Run the Router Server

```bash
python3 mcp_router.py
```

The router will:
- Load all MCPs from `mcp-registry.json`
- Start the MCP server on STDIO
- Watch for registry changes (hot-reload)
- Listen for tool calls

### 2. Test an MCP

```bash
# Test STDIO MCP
python3 mcp_router.py --test agi-memory

# Expected output
============================================================
MCP TEST RESULTS: agi-memory
============================================================
{
  "mcp_name": "agi-memory",
  "status": "passed",
  "transport": "stdio",
  "handshake": "success",
  "tools": ["memory_search", "memory_store", "memory_stats"],
  "tool_test": {...},
  "errors": []
}
============================================================
```

### 3. Call Tools via the Router

Once running, you can call any MCP tool via the single `use_mcp` tool:

```python
# Via Claude or any MCP client
{
  "tool": "use_mcp",
  "arguments": {
    "mcp_name": "agi-memory",
    "tool": "memory_stats",
    "args": {}
  }
}
```

---

## Transport Types

### STDIO (Local Subprocess)
- Best for: Local servers, custom Python scripts
- Command-based, spawns subprocess per call
- High latency but full control

**Registry Example:**
```json
{
  "agi-memory": {
    "command": "python3",
    "args": ["/path/to/server.py"],
    "transport": "stdio",
    "tools": ["memory_search", "memory_store", "memory_stats"]
  }
}
```

**CLI Test:**
```bash
python3 mcp_router.py --test agi-memory
```

### HTTP (REST API)
- Best for: Public APIs, simple integrations
- Low overhead, connection reuse
- Request-response model

**Registry Example:**
```json
{
  "my-api": {
    "url": "https://api.example.com/mcp",
    "transport": "http",
    "headers": {"Authorization": "Bearer token123"},
    "timeout": 30,
    "tools": ["query", "search"]
  }
}
```

**Protocol:**
```
POST /initialize
POST /tool/{tool_name}
```

### SSE (Server-Sent Events)
- Best for: Large responses, streaming data
- Persistent connection with streaming
- One-way server-to-client streaming

**Registry Example:**
```json
{
  "stream-data": {
    "url": "https://stream.example.com/mcp",
    "transport": "sse",
    "timeout": 60,
    "tools": ["stream_feed", "live_data"]
  }
}
```

### WebSocket (Real-time Bidirectional)
- Best for: Real-time queries, persistent connections
- Lowest latency, persistent connection
- JSON-RPC 2.0 protocol

**Registry Example:**
```json
{
  "realtime": {
    "url": "wss://socket.example.com/mcp",
    "transport": "websocket",
    "timeout": 120,
    "tools": ["compute", "stream"]
  }
}
```

---

## Advanced Usage

### Add New MCP to Registry

Edit `mcp-registry.json`:

```json
{
  "my-new-mcp": {
    "url": "https://api.example.com/mcp",
    "transport": "http",
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN"
    },
    "tools": ["tool1", "tool2", "tool3"],
    "category": "integration",
    "description": "My new MCP integration"
  }
}
```

Registry hot-reloads automatically!

### Test Multiple MCPs

```bash
# Test all STDIO MCPs
for mcp in agi-memory smithery-fetch github linear; do
  echo "Testing $mcp..."
  python3 mcp_router.py --test $mcp
done
```

### Custom Timeouts

```json
{
  "slow-api": {
    "url": "https://slow.example.com/mcp",
    "transport": "http",
    "timeout": 120,  // 2 minutes
    "tools": ["long_operation"]
  }
}
```

### Authentication Headers

```json
{
  "private-api": {
    "url": "https://private.example.com/mcp",
    "transport": "http",
    "headers": {
      "Authorization": "Bearer eyJhbGc...",
      "X-API-Key": "sk-proj-...",
      "X-Custom-Header": "value"
    },
    "tools": ["protected_tool"]
  }
}
```

### Environment Variables (STDIO Only)

```json
{
  "db-mcp": {
    "command": "python3",
    "args": ["db_server.py"],
    "transport": "stdio",
    "env": {
      "DATABASE_URL": "postgresql://user:pass@host/db",
      "LOG_LEVEL": "DEBUG"
    },
    "tools": ["query", "execute"]
  }
}
```

---

## Architecture

### Flow

```
Claude/Client
    |
    v
MCP Router (stdio_server)
    |
    +---> STDIO Handler   -> subprocess-based MCPs
    +---> HTTP Handler    -> REST API MCPs
    +---> SSE Handler     -> Streaming MCPs
    +---> WebSocket       -> Real-time MCPs
```

### Threading Model

- Main thread: Accepts STDIO connections from clients
- ThreadPoolExecutor (5 workers): Executes MCP calls concurrently
- Each transport has its own event loop (async)

### Caching

- 5-minute TTL for STDIO process connections
- Automatic cleanup on errors
- Hot-reload registry on file changes

---

## Troubleshooting

### "Unknown MCP"

```
ValueError: Unknown MCP: my-mcp
```

**Solution:** Add to registry and reload
```bash
# Add to mcp-registry.json, then:
python3 mcp_router.py --test my-mcp
```

### "Tool not found"

```
ValueError: Tool 'xyz' not found in MCP 'agi-memory'
```

**Solution:** Check available tools
```bash
python3 mcp_router.py --test agi-memory
# See "tools" field in output
```

### "HTTP 500"

For HTTP/SSE transports:
```
httpx.HTTPStatusError: Server error '500 Internal Server Error'
```

**Solution:** Check MCP server logs, ensure correct endpoint

### "Connection refused"

For WebSocket:
```
ConnectionRefusedError: Cannot connect to WebSocket server
```

**Solution:** Verify URL is correct and server is running
```bash
# Test with curl
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" https://socket.example.com/mcp
```

### "Timeout"

All transports:
```
TimeoutError: Request timed out after 30s
```

**Solution:** Increase timeout for slow operations
```json
{
  "slow-mcp": {
    "url": "https://slow.example.com",
    "timeout": 120
  }
}
```

---

## Performance Tips

### 1. Use WebSocket for Many Calls
```
WebSocket: 5ms latency per call
HTTP: 50ms latency per call (connection setup)
STDIO: 200ms latency per call (subprocess spawn)
```

### 2. Batch Requests
```python
# Inefficient
for item in items:
    result = router.use_mcp("api", "query", {"id": item})

# Efficient
results = router.use_mcp("api", "batch_query", {"ids": items})
```

### 3. Enable Caching (STDIO)
STDIO connections are cached for 5 minutes automatically

### 4. Use Appropriate Timeout
- HTTP API: 10-30s
- WebSocket: 30-60s
- Streaming: 60-300s

---

## Examples

### Example 1: Memory System Query

```python
result = await router.execute_mcp_tool(
    "agi-memory",
    "memory_search",
    {
        "query": "What did we discuss about AGI architecture?",
        "limit": 5
    }
)
```

### Example 2: API Integration

```python
result = await router.execute_mcp_tool(
    "openai",  # HTTP MCP
    "chat",
    {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

### Example 3: Real-time Data

```python
result = await router.execute_mcp_tool(
    "realtime-market",  # WebSocket MCP
    "get_price",
    {"symbol": "AAPL"}
)
```

---

## Monitoring

### Check Loaded MCPs

```bash
# List all MCPs
python3 -c "import mcp_router; print(list(mcp_router.router.registry.keys()))"
```

### View Logs

```bash
# Tail logs
tail -f /tmp/mcp_router.log  # if output redirected
```

### Test Mode Verbose

CLI tests show:
- Transport type detected
- Handshake success/failure
- Available tools
- Tool execution results
- Any errors

---

## Next Steps

1. Add more MCPs to registry (HTTP, WebSocket)
2. Test each MCP: `python3 mcp_router.py --test <name>`
3. Integrate with Claude: Use `use_mcp` tool
4. Monitor performance: Compare latencies
5. Tune timeouts and caching

---

## API Reference

### `execute_mcp_tool(mcp_name, tool, args)`

Execute any tool on any registered MCP

**Parameters:**
- `mcp_name` (str): MCP identifier from registry
- `tool` (str): Tool name to execute
- `args` (dict): Tool arguments

**Returns:**
- Tool result (any type)

**Raises:**
- `ValueError`: Unknown MCP or tool
- `RuntimeError`: Missing dependencies
- `TimeoutError`: Request timeout
- Transport-specific errors

**Example:**
```python
result = await router.execute_mcp_tool(
    "agi-memory",
    "memory_stats",
    {}
)
```

---

## Registry Schema

```json
{
  "mcp_name": {
    // STDIO
    "command": "python3",
    "args": ["script.py"],

    // OR HTTP/SSE/WebSocket
    "url": "https://api.example.com/mcp",

    // Common
    "transport": "stdio|http|sse|websocket",
    "headers": {"Authorization": "Bearer ..."},
    "timeout": 30,
    "env": {"KEY": "value"},
    "tools": ["tool1", "tool2"],
    "category": "integration",
    "description": "Human-readable description"
  }
}
```

---

## Contributing

To add a new MCP transport type:

1. Implement handler in `MCPRouter`:
   ```python
   def _call_new_transport_mcp(self, mcp_name, config, tool, args):
       # Implementation
   ```

2. Add transport detection in `_spawn_and_call_mcp()`

3. Update test_mcp() for CLI test support

4. Add examples to MCP_TRANSPORT_EXAMPLES.md
