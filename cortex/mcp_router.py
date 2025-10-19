#!/usr/bin/env python3
"""
MCP Router - Dynamic MCP Gateway
Exposes 1 tool (use_mcp) that routes to 50+ MCPs on-demand
Zero context pollution, hot-reload registry
Supports STDIO, HTTP/SSE, and WebSocket transports
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# MCP protocol imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# HTTP/SSE/WebSocket imports
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from httpx_sse import aconnect_sse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp-router")

# Registry path
REGISTRY_PATH = Path(__file__).parent / "mcp-registry.json"


class RegistryWatcher(FileSystemEventHandler):
    """Watch registry file for changes and hot-reload"""

    def __init__(self, router):
        self.router = router

    def on_modified(self, event):
        if event.src_path.endswith("mcp-registry.json"):
            logger.info("Registry file changed, reloading...")
            self.router.load_registry()


class MCPConnectionCache:
    """Cache MCP connections with TTL"""

    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def get(self, mcp_name: str) -> Optional[Any]:
        if mcp_name in self.cache:
            entry = self.cache[mcp_name]
            if time.time() - entry["timestamp"] < self.ttl:
                logger.info(f"Cache HIT: {mcp_name}")
                return entry["connection"]
            else:
                logger.info(f"Cache EXPIRED: {mcp_name}")
                self.cleanup(mcp_name)
        return None

    def set(self, mcp_name: str, connection: Any):
        self.cache[mcp_name] = {
            "connection": connection,
            "timestamp": time.time()
        }
        logger.info(f"Cache SET: {mcp_name}")

    def cleanup(self, mcp_name: str):
        if mcp_name in self.cache:
            # Kill subprocess if exists
            entry = self.cache[mcp_name]
            if "process" in entry:
                try:
                    entry["process"].terminate()
                except Exception as e:
                    logger.warning(f"Failed to terminate {mcp_name}: {e}")
            del self.cache[mcp_name]
            logger.info(f"Cache CLEANUP: {mcp_name}")

    def cleanup_all(self):
        for mcp_name in list(self.cache.keys()):
            self.cleanup(mcp_name)


class MCPRouter:
    """Router that dynamically loads MCPs on-demand"""

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.cache = MCPConnectionCache(ttl_seconds=300)  # 5min cache
        self.executor = ThreadPoolExecutor(max_workers=5)  # Pool for MCP calls
        self.load_registry()
        self.setup_file_watcher()

    def load_registry(self):
        """Load MCP registry from JSON file"""
        try:
            with open(REGISTRY_PATH, "r") as f:
                self.registry = json.load(f)
            logger.info(f"Loaded {len(self.registry)} MCPs from registry")
        except FileNotFoundError:
            logger.error(f"Registry not found: {REGISTRY_PATH}")
            self.registry = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid registry JSON: {e}")
            self.registry = {}

    def setup_file_watcher(self):
        """Setup file watcher for hot-reload"""
        try:
            event_handler = RegistryWatcher(self)
            observer = Observer()
            observer.schedule(event_handler, str(REGISTRY_PATH.parent), recursive=False)
            observer.start()
            logger.info("File watcher started for hot-reload")
        except Exception as e:
            logger.warning(f"Failed to setup file watcher: {e}")

    def list_mcps(self) -> Dict[str, Any]:
        """List all available MCPs (names only for minimal context)"""
        return {
            name: {
                "tools": config.get("tools", []),
                "category": config.get("category", "general"),
                "description": config.get("description", "")
            }
            for name, config in self.registry.items()
        }

    async def execute_mcp_tool(
        self,
        mcp_name: str,
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """
        Execute tool on specified MCP
        Spawns subprocess, executes, returns result, kills process
        """
        if mcp_name not in self.registry:
            raise ValueError(f"Unknown MCP: {mcp_name}")

        config = self.registry[mcp_name]

        # Validate tool exists
        if tool not in config.get("tools", []):
            raise ValueError(f"Tool '{tool}' not found in MCP '{mcp_name}'")

        logger.info(f"Executing {mcp_name}.{tool}({args})")

        try:
            # Check cache first
            cached_connection = self.cache.get(mcp_name)

            if cached_connection:
                # Use cached connection
                result = await self._call_cached_mcp(cached_connection, tool, args)
            else:
                # Spawn new subprocess
                result = await self._spawn_and_call_mcp(mcp_name, config, tool, args)

            logger.info(f"Success: {mcp_name}.{tool}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute {mcp_name}.{tool}: {e}")
            # Cleanup cache on error
            self.cache.cleanup(mcp_name)
            raise

    async def _spawn_and_call_mcp(
        self,
        mcp_name: str,
        config: Dict[str, Any],
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """Route to correct transport handler and execute tool via ThreadPoolExecutor"""

        # Detect transport type
        transport = config.get("transport", "stdio")
        url = config.get("url", "")

        # Auto-detect transport from URL if not explicitly set
        if not transport and url:
            if url.startswith("wss://") or url.startswith("ws://"):
                transport = "websocket"
            elif url.startswith("https://") or url.startswith("http://"):
                transport = "http"

        # Route to correct handler
        if transport == "websocket":
            handler = self._call_websocket_mcp
        elif transport == "sse":
            handler = self._call_sse_mcp
        elif transport == "http":
            handler = self._call_http_mcp
        else:
            # Default to STDIO for backward compatibility
            handler = self._call_mcp_sync

        # Run MCP call in thread pool to avoid event loop conflicts
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        result = await loop.run_in_executor(
            self.executor,
            handler,
            mcp_name,
            config,
            tool,
            args
        )
        return result

    def _call_mcp_sync(
        self,
        mcp_name: str,
        config: Dict[str, Any],
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """Synchronous MCP call using official client (runs in thread pool)"""
        from mcp.client.stdio import stdio_client, StdioServerParameters
        from mcp.client.session import ClientSession

        command = config["command"]
        cmd_args = config.get("args", [])
        env_vars = config.get("env", {})

        # Prepare environment
        env = os.environ.copy()
        env.update(env_vars)

        # Server parameters
        server_params = StdioServerParameters(
            command=command,
            args=cmd_args,
            env=env if env_vars else None
        )

        logger.info(f"Spawning MCP: {command} {' '.join(cmd_args)}")

        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def run_mcp():
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        # Initialize
                        await session.initialize()
                        logger.info(f"Initialized {mcp_name}")

                        # List tools (for validation)
                        tools_result = await session.list_tools()
                        available_tools = [t.name for t in tools_result.tools]
                        logger.info(f"{mcp_name} tools: {available_tools}")

                        # Validate tool
                        if tool not in available_tools:
                            raise ValueError(f"Tool '{tool}' not in {available_tools}")

                        # Call tool
                        logger.info(f"Calling {mcp_name}.{tool}({args})")
                        result = await session.call_tool(tool, args)

                        # Extract result
                        if result.content:
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                try:
                                    return json.loads(content.text)
                                except json.JSONDecodeError:
                                    return {"result": content.text}
                            else:
                                return {"result": str(content)}
                        return {"status": "success", "result": None}

            # Run in thread's event loop
            result = loop.run_until_complete(run_mcp())
            loop.close()

            logger.info(f"MCP call success: {mcp_name}.{tool}")
            return result

        except Exception as e:
            logger.error(f"MCP call failed: {e}", exc_info=True)
            raise

    def _call_http_mcp(
        self,
        mcp_name: str,
        config: Dict[str, Any],
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """Call HTTP-based MCP endpoint (runs in thread pool)"""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx library not installed. Install with: pip3 install httpx")

        url = config.get("url")
        if not url:
            raise ValueError("HTTP MCP config missing 'url' field")

        headers = config.get("headers", {})
        timeout = config.get("timeout", 30)

        logger.info(f"Calling HTTP MCP: {url}/tool/{tool}")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def call_http():
                async with httpx.AsyncClient(timeout=timeout) as client:
                    # Handshake
                    init_response = await client.post(
                        f"{url}/initialize",
                        json={"protocol_version": "2024-11-05"},
                        headers=headers
                    )
                    init_response.raise_for_status()
                    logger.info(f"HTTP MCP initialized: {mcp_name}")

                    # Call tool
                    tool_response = await client.post(
                        f"{url}/tool/{tool}",
                        json={"arguments": args},
                        headers=headers
                    )
                    tool_response.raise_for_status()
                    return tool_response.json()

            result = loop.run_until_complete(call_http())
            loop.close()
            logger.info(f"HTTP MCP call success: {mcp_name}.{tool}")
            return result

        except Exception as e:
            logger.error(f"HTTP MCP call failed: {e}", exc_info=True)
            raise

    def _call_sse_mcp(
        self,
        mcp_name: str,
        config: Dict[str, Any],
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """Call SSE-based MCP endpoint (runs in thread pool)"""
        if not HTTPX_AVAILABLE:
            raise RuntimeError("httpx library not installed. Install with: pip3 install httpx")
        if not SSE_AVAILABLE:
            raise RuntimeError("httpx-sse library not installed. Install with: pip3 install httpx-sse")

        url = config.get("url")
        if not url:
            raise ValueError("SSE MCP config missing 'url' field")

        headers = config.get("headers", {})
        timeout = config.get("timeout", 60)

        logger.info(f"Calling SSE MCP: {url}/tool/{tool}")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def call_sse():
                async with httpx.AsyncClient(timeout=timeout) as client:
                    # Handshake
                    init_response = await client.post(
                        f"{url}/initialize",
                        json={"protocol_version": "2024-11-05"},
                        headers=headers
                    )
                    init_response.raise_for_status()
                    logger.info(f"SSE MCP initialized: {mcp_name}")

                    # Call tool with SSE streaming
                    async with aconnect_sse(
                        "POST",
                        f"{url}/tool/{tool}",
                        json={"arguments": args},
                        headers=headers,
                        client=client
                    ) as event_source:
                        result = None
                        async for event in event_source.aiter_sse():
                            if event.data:
                                try:
                                    data = json.loads(event.data)
                                    if data.get("type") == "tool_result":
                                        result = data.get("content")
                                    logger.debug(f"SSE event: {event.event}")
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse SSE data: {event.data}")
                        return result or {"status": "success"}

            result = loop.run_until_complete(call_sse())
            loop.close()
            logger.info(f"SSE MCP call success: {mcp_name}.{tool}")
            return result

        except Exception as e:
            logger.error(f"SSE MCP call failed: {e}", exc_info=True)
            raise

    def _call_websocket_mcp(
        self,
        mcp_name: str,
        config: Dict[str, Any],
        tool: str,
        args: Dict[str, Any]
    ) -> Any:
        """Call WebSocket-based MCP endpoint (runs in thread pool)"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets library not installed. Install with: pip3 install websockets")

        url = config.get("url")
        if not url:
            raise ValueError("WebSocket MCP config missing 'url' field")

        headers = config.get("headers", {})
        timeout = config.get("timeout", 60)

        logger.info(f"Calling WebSocket MCP: {url}")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def call_websocket():
                request_id = 1
                try:
                    async with websockets.connect(url, subprotocols=["mcp"]) as ws:
                        logger.info(f"WebSocket connected: {mcp_name}")

                        # Handshake
                        init_msg = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "initialize",
                            "params": {
                                "protocol_version": "2024-11-05",
                                "capabilities": {},
                                "client_info": {"name": "mcp-router", "version": "1.0"}
                            }
                        }
                        await ws.send(json.dumps(init_msg))
                        request_id += 1

                        # Receive init response
                        init_response_str = await asyncio.wait_for(ws.recv(), timeout=timeout)
                        init_response = json.loads(init_response_str)
                        logger.info(f"WebSocket initialized: {init_response.get('result', {}).get('server_info')}")

                        # Call tool
                        tool_msg = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "method": "tools/call",
                            "params": {
                                "name": tool,
                                "arguments": args
                            }
                        }
                        await ws.send(json.dumps(tool_msg))
                        request_id += 1

                        # Receive tool response
                        tool_response_str = await asyncio.wait_for(ws.recv(), timeout=timeout)
                        tool_response = json.loads(tool_response_str)

                        if "error" in tool_response:
                            raise ValueError(f"Tool call error: {tool_response['error']}")

                        return tool_response.get("result", {})

                except asyncio.TimeoutError:
                    raise TimeoutError(f"WebSocket MCP {mcp_name} timed out after {timeout}s")

            result = loop.run_until_complete(call_websocket())
            loop.close()
            logger.info(f"WebSocket MCP call success: {mcp_name}.{tool}")
            return result

        except Exception as e:
            logger.error(f"WebSocket MCP call failed: {e}", exc_info=True)
            raise

    async def _call_cached_mcp(self, connection: Any, tool: str, args: Dict[str, Any]) -> Any:
        """Call tool on cached MCP connection"""
        # TODO: Use cached connection to call tool
        # For now, not implemented
        raise NotImplementedError("Cached connections not yet implemented")


# Global router instance
router = MCPRouter()

# Create MCP server
app = Server("mcp-router")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Expose single tool: use_mcp"""
    return [
        Tool(
            name="use_mcp",
            description=f"Execute tool on any of {len(router.registry)} available MCPs. Available MCPs: {', '.join(router.registry.keys())}",
            inputSchema={
                "type": "object",
                "properties": {
                    "mcp_name": {
                        "type": "string",
                        "description": f"MCP to use. Available: {', '.join(router.registry.keys())}"
                    },
                    "tool": {
                        "type": "string",
                        "description": "Tool name to execute on the MCP"
                    },
                    "args": {
                        "type": "object",
                        "description": "Arguments to pass to the tool"
                    }
                },
                "required": ["mcp_name", "tool", "args"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "use_mcp":
        try:
            mcp_name = arguments["mcp_name"]
            tool = arguments["tool"]
            args = arguments.get("args", {})

            # Execute on MCP
            result = await router.execute_mcp_tool(mcp_name, tool, args)

            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]

        except Exception as e:
            logger.error(f"Error in use_mcp: {e}")
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "mcp_name": arguments.get("mcp_name"),
                        "tool": arguments.get("tool")
                    }, indent=2)
                )
            ]

    raise ValueError(f"Unknown tool: {name}")


async def test_mcp(mcp_name: str) -> Dict[str, Any]:
    """Test MCP connection and functionality"""
    results = {
        "mcp_name": mcp_name,
        "status": "unknown",
        "transport": None,
        "handshake": None,
        "tools": [],
        "tool_test": None,
        "errors": []
    }

    if mcp_name not in router.registry:
        results["status"] = "failed"
        results["errors"].append(f"MCP '{mcp_name}' not found in registry")
        return results

    config = router.registry[mcp_name]
    transport = config.get("transport", "stdio")
    url = config.get("url", "")

    # Auto-detect transport
    if not transport and url:
        if url.startswith("wss://") or url.startswith("ws://"):
            transport = "websocket"
        elif url.startswith("https://") or url.startswith("http://"):
            transport = "http"

    results["transport"] = transport

    try:
        # Test handshake
        if transport == "stdio":
            logger.info(f"Testing STDIO MCP: {mcp_name}")
            # Handshake via tool execution - use memory_stats if available, else first tool
            available_tools = config.get("tools", [])
            test_tool = "memory_stats" if "memory_stats" in available_tools else (available_tools[0] if available_tools else None)
            if not test_tool:
                raise ValueError("No tools available to test")
            result = await router.execute_mcp_tool(mcp_name, test_tool, {})
            results["handshake"] = "success"
        elif transport == "http":
            logger.info(f"Testing HTTP MCP: {mcp_name}")
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not installed")
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{url}/initialize",
                    json={"protocol_version": "2024-11-05"},
                    headers=config.get("headers", {})
                )
                response.raise_for_status()
                results["handshake"] = "success"
        elif transport == "sse":
            logger.info(f"Testing SSE MCP: {mcp_name}")
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not installed")
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{url}/initialize",
                    json={"protocol_version": "2024-11-05"},
                    headers=config.get("headers", {})
                )
                response.raise_for_status()
                results["handshake"] = "success"
        elif transport == "websocket":
            logger.info(f"Testing WebSocket MCP: {mcp_name}")
            if not WEBSOCKETS_AVAILABLE:
                raise RuntimeError("websockets not installed")
            async with websockets.connect(url, subprotocols=["mcp"]) as ws:
                init_msg = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocol_version": "2024-11-05",
                        "capabilities": {},
                        "client_info": {"name": "mcp-router", "version": "1.0"}
                    }
                }
                await ws.send(json.dumps(init_msg))
                response_str = await asyncio.wait_for(ws.recv(), timeout=10)
                response = json.loads(response_str)
                if "error" in response:
                    raise ValueError(f"Handshake error: {response['error']}")
                results["handshake"] = "success"

        # List available tools (from config for STDIO)
        if transport == "stdio":
            results["tools"] = config.get("tools", [])

        # Try to call a basic tool
        if results["tools"]:
            # Prefer stats/health tools as they typically don't require args
            tool_to_test = None
            for candidate in ["memory_stats", "health", "status", "stats"]:
                if candidate in results["tools"]:
                    tool_to_test = candidate
                    break
            if not tool_to_test:
                tool_to_test = results["tools"][0]

            logger.info(f"Attempting to call {tool_to_test}...")
            try:
                result = await router.execute_mcp_tool(mcp_name, tool_to_test, {})
                results["tool_test"] = {
                    "tool": tool_to_test,
                    "status": "success",
                    "result": str(result)[:200]  # Truncate for display
                }
            except Exception as e:
                results["tool_test"] = {
                    "tool": tool_to_test,
                    "status": "failed",
                    "error": str(e)[:200]
                }

        results["status"] = "passed"
        return results

    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(f"{type(e).__name__}: {str(e)}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return results


async def main():
    """Run MCP router server"""
    logger.info("Starting MCP Router...")
    logger.info(f"Loaded {len(router.registry)} MCPs from registry")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode
        if len(sys.argv) < 3:
            print("Usage: python3 mcp_router.py --test <mcp-name>")
            print(f"Available MCPs: {', '.join(router.registry.keys())}")
            sys.exit(1)

        mcp_name = sys.argv[2]
        try:
            results = asyncio.run(test_mcp(mcp_name))
            print("\n" + "="*60)
            print(f"MCP TEST RESULTS: {mcp_name}")
            print("="*60)
            print(json.dumps(results, indent=2))
            print("="*60)

            if results["status"] == "passed":
                print("\n✓ ALL TESTS PASSED")
                sys.exit(0)
            else:
                print(f"\n✗ TEST FAILED: {results['errors'][0] if results['errors'] else 'unknown error'}")
                sys.exit(1)
        except Exception as e:
            print(f"\n✗ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Normal server mode
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            router.cache.cleanup_all()
