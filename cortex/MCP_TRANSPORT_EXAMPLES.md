# MCP Router - Transport Configuration Examples

## Overview

The MCP Router now supports three transport types:
- **STDIO** (70% adoption) - Subprocess-based MCPs
- **HTTP** (20% adoption) - HTTP API endpoints
- **SSE** - Server-Sent Events for streaming
- **WebSocket** (5% adoption) - Real-time bidirectional communication

## Configuration Formats

### 1. STDIO Transport (Default)

Used for traditional subprocess-based MCPs.

```json
{
  "my-mcp": {
    "command": "python3",
    "args": ["/path/to/mcp_server.py"],
    "transport": "stdio",
    "env": {
      "DATABASE_URL": "postgresql://...",
      "API_KEY": "secret123"
    },
    "tools": ["tool1", "tool2", "tool3"],
    "category": "data",
    "description": "My local MCP server"
  }
}
```

**Key fields:**
- `command`: Executable to run
- `args`: Command arguments
- `transport`: "stdio" (or omit for default)
- `env`: Environment variables (optional)

---

### 2. HTTP Transport

For HTTP API-based MCPs.

```json
{
  "http-mcp": {
    "url": "https://api.example.com/mcp",
    "transport": "http",
    "headers": {
      "Authorization": "Bearer token123",
      "X-API-Key": "key123"
    },
    "timeout": 30,
    "tools": ["query", "search", "analytics"],
    "category": "api",
    "description": "Remote HTTP MCP"
  }
}
```

**Protocol:**
```
POST /initialize
  Request: {"protocol_version": "2024-11-05"}
  Response: {success}

POST /tool/{tool_name}
  Request: {"arguments": {...}}
  Response: {result}
```

**Key fields:**
- `url`: Base URL of the MCP server
- `transport`: "http"
- `headers`: Custom headers (auth, API keys, etc.)
- `timeout`: Request timeout in seconds (default: 30)

---

### 3. Server-Sent Events (SSE) Transport

For streaming responses over HTTP.

```json
{
  "sse-mcp": {
    "url": "https://stream.example.com/mcp",
    "transport": "sse",
    "headers": {
      "Authorization": "Bearer token123"
    },
    "timeout": 60,
    "tools": ["stream_data", "live_feed"],
    "category": "streaming",
    "description": "Streaming MCP with SSE"
  }
}
```

**Protocol:**
```
POST /initialize
  Request: {"protocol_version": "2024-11-05"}
  Response: {success}

POST /tool/{tool_name} (with SSE streaming)
  Request: {"arguments": {...}}
  Response: Server-Sent Events stream
    event: tool_result
    data: {"type": "tool_result", "content": {...}}
```

**Key fields:**
- `url`: Base URL with SSE endpoint
- `transport`: "sse"
- `headers`: Custom headers
- `timeout`: Longer timeout for streaming (default: 60)

---

### 4. WebSocket Transport

For real-time bidirectional communication using JSON-RPC.

```json
{
  "ws-mcp": {
    "url": "wss://socket.example.com/mcp",
    "transport": "websocket",
    "headers": {
      "Authorization": "Bearer token123"
    },
    "timeout": 60,
    "tools": ["realtime_compute", "stream_results"],
    "category": "realtime",
    "description": "Real-time WebSocket MCP"
  }
}
```

**Protocol (JSON-RPC 2.0):**
```
Initialize:
  Client: {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}
  Server: {"jsonrpc": "2.0", "id": 1, "result": {...}}

Call tool:
  Client: {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "tool1", "arguments": {...}}}
  Server: {"jsonrpc": "2.0", "id": 2, "result": {...}}
```

**Key fields:**
- `url`: WebSocket URL (ws:// or wss://)
- `transport`: "websocket"
- `headers`: Custom headers
- `timeout`: Request timeout in seconds (default: 60)

---

## Transport Auto-Detection

The router can auto-detect transport from URL if not explicitly set:

```json
{
  "auto-ws": {
    "url": "wss://api.example.com/mcp",
    // transport will be detected as "websocket"
    "tools": ["query"]
  },
  "auto-http": {
    "url": "https://api.example.com/mcp",
    // transport will be detected as "http"
    "tools": ["search"]
  }
}
```

---

## Testing MCPs

Use the CLI to test any MCP:

```bash
# Test STDIO MCP
python3 mcp_router.py --test agi-memory

# Test HTTP MCP
python3 mcp_router.py --test http-mcp

# Test WebSocket MCP
python3 mcp_router.py --test ws-mcp
```

**Output:**
```
============================================================
MCP TEST RESULTS: agi-memory
============================================================
{
  "mcp_name": "agi-memory",
  "status": "passed",
  "transport": "stdio",
  "handshake": "success",
  "tools": ["memory_search", "memory_store", "memory_stats"],
  "tool_test": {
    "tool": "memory_stats",
    "status": "success",
    "result": "{'total_memories': 60, ...}"
  },
  "errors": []
}
============================================================

✓ ALL TESTS PASSED
```

---

## Complete Registry Example

```json
{
  "agi-memory": {
    "command": "python3",
    "args": ["/home/pilote/projet/agi/cortex/memory/stdio_wrapper.py"],
    "transport": "stdio",
    "env": {
      "PYTHONPATH": "/home/pilote/projet/agi/backend",
      "DATABASE_URL": "postgresql://user:pass@localhost:5433/db"
    },
    "tools": ["memory_search", "memory_store", "memory_stats"],
    "category": "memory",
    "description": "AGI memory system"
  },

  "openai": {
    "url": "https://api.openai.com/v1/mcp",
    "transport": "http",
    "headers": {
      "Authorization": "Bearer sk-..."
    },
    "timeout": 30,
    "tools": ["chat", "embeddings", "images"],
    "category": "ai",
    "description": "OpenAI MCP"
  },

  "realtime-data": {
    "url": "wss://stream.example.com/mcp",
    "transport": "websocket",
    "headers": {
      "Authorization": "Bearer token123"
    },
    "timeout": 120,
    "tools": ["stream_prices", "live_metrics"],
    "category": "realtime",
    "description": "Real-time data streaming"
  }
}
```

---

## Dependencies

Install all transport libraries:

```bash
pip3 install httpx httpx-sse websockets
```

- `httpx`: HTTP/HTTPS client
- `httpx-sse`: Server-Sent Events support
- `websockets`: WebSocket protocol

---

## Error Handling

### Missing Dependencies

If a transport library is not installed, you'll see:

```
RuntimeError: httpx library not installed. Install with: pip3 install httpx
RuntimeError: websockets library not installed. Install with: pip3 install websockets
```

### Connection Errors

- **HTTP**: `httpx.HTTPError`, `httpx.TimeoutException`
- **WebSocket**: `websockets.exceptions.WebSocketException`, `TimeoutError`
- **STDIO**: Standard subprocess errors

All errors are logged and propagated with context.

---

## Performance Characteristics

| Transport | Latency | Overhead | Best For |
|-----------|---------|----------|----------|
| STDIO | 100-500ms | High (subprocess spawn) | Local servers, full control |
| HTTP | 50-200ms | Medium (connection reuse) | Public APIs, simple queries |
| SSE | 50-200ms + streaming | Medium | Large responses, streaming |
| WebSocket | 20-100ms | Low (persistent) | Real-time, many calls |

---

## Security Notes

1. **Headers**: All custom headers (Authorization, API keys) are passed through
2. **HTTPS/WSS**: Always use encrypted transports for production
3. **Environment Variables**: STDIO transport can use env vars
4. **Timeouts**: Prevent hanging requests (HTTP: 30s, WebSocket: 60s default)
5. **Auto-cleanup**: Connections are properly closed/terminated

---

## Upgrading from STDIO-Only

Existing STDIO configurations work unchanged:

```json
// Old format (still works)
{
  "my-mcp": {
    "command": "python3",
    "args": ["./server.py"],
    "tools": ["t1", "t2"]
  }
}

// Equivalent new format
{
  "my-mcp": {
    "command": "python3",
    "args": ["./server.py"],
    "transport": "stdio",  // Optional (default)
    "tools": ["t1", "t2"]
  }
}
```

No breaking changes - existing registries continue to work.
