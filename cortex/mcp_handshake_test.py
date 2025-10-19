#!/usr/bin/env python3
"""
MCP Handshake Tester
Tests connection to MCP servers (STDIO, HTTP, SSE, WebSocket)
"""

import sys
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import uuid

try:
    import httpx
    import websockets
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "websockets", "-q"])
    import httpx
    import websockets


async def test_stdio_mcp(command: str, args: list = None, env: dict = None) -> Dict[str, Any]:
    """Test STDIO MCP handshake"""
    if args is None:
        args = []

    try:
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env or {}
        )

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-handshake-tester",
                    "version": "1.0"
                }
            }
        }

        request_line = json.dumps(init_request) + "\n"
        process.stdin.write(request_line.encode())
        await process.stdin.drain()

        # Read response with timeout
        try:
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )

            if not response_line:
                return {"status": "error", "message": "No response from STDIO server"}

            response = json.loads(response_line.decode())

            # Try to list tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            tools_line = json.dumps(tools_request) + "\n"
            process.stdin.write(tools_line.encode())
            await process.stdin.drain()

            tools_response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )

            tools_response = json.loads(tools_response_line.decode()) if tools_response_line else {}

            # Terminate process
            process.terminate()
            await asyncio.sleep(0.1)

            return {
                "status": "success",
                "transport": "STDIO",
                "command": command,
                "initialize_response": response,
                "tools_count": len(tools_response.get("result", {}).get("tools", [])),
                "tools_response": tools_response
            }

        except asyncio.TimeoutError:
            process.terminate()
            return {"status": "error", "message": "Timeout waiting for STDIO response"}

    except Exception as e:
        return {"status": "error", "message": f"STDIO test failed: {str(e)}"}


async def test_http_mcp(url: str, headers: dict = None) -> Dict[str, Any]:
    """Test HTTP/SSE MCP handshake"""
    if headers is None:
        headers = {}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test initialize endpoint
            init_request = {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-handshake-tester",
                    "version": "1.0"
                }
            }

            base_url = url.rstrip('/')

            try:
                init_response = await client.post(
                    f"{base_url}/initialize",
                    json=init_request,
                    headers=headers
                )
                init_response.raise_for_status()
                init_data = init_response.json()
            except Exception as e:
                return {"status": "error", "message": f"Initialize failed: {str(e)}"}

            # Try to list tools
            try:
                tools_response = await client.get(
                    f"{base_url}/tools",
                    headers=headers
                )
                tools_response.raise_for_status()
                tools_data = tools_response.json()
            except Exception as e:
                tools_data = {"error": str(e)}

            return {
                "status": "success",
                "transport": "HTTP",
                "url": url,
                "initialize_response": init_data,
                "tools_count": len(tools_data.get("tools", [])),
                "tools_response": tools_data
            }

    except Exception as e:
        return {"status": "error", "message": f"HTTP test failed: {str(e)}"}


async def test_websocket_mcp(url: str, headers: dict = None) -> Dict[str, Any]:
    """Test WebSocket MCP handshake"""
    if headers is None:
        headers = {}

    try:
        # Convert http(s) to ws(s)
        ws_url = url.replace("https://", "wss://").replace("http://", "ws://")

        async with websockets.connect(ws_url, subprotocols=["mcp"]) as websocket:
            # Send initialize
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-handshake-tester",
                        "version": "1.0"
                    }
                }
            }

            await websocket.send(json.dumps(init_request))

            # Receive response
            try:
                init_response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5.0
                )
                init_data = json.loads(init_response)
            except asyncio.TimeoutError:
                return {"status": "error", "message": "WebSocket timeout on initialize"}

            # List tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            await websocket.send(json.dumps(tools_request))

            try:
                tools_response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=5.0
                )
                tools_data = json.loads(tools_response)
            except asyncio.TimeoutError:
                tools_data = {}

            return {
                "status": "success",
                "transport": "WebSocket",
                "url": ws_url,
                "initialize_response": init_data,
                "tools_count": len(tools_data.get("result", {}).get("tools", [])),
                "tools_response": tools_data
            }

    except Exception as e:
        return {"status": "error", "message": f"WebSocket test failed: {str(e)}"}


def print_result(result: Dict[str, Any]):
    """Pretty print test result"""
    print(f"\nTransport: {result.get('transport', 'Unknown')}")
    print(f"Status: {result['status'].upper()}")

    if result['status'] == 'error':
        print(f"Error: {result.get('message', 'Unknown error')}")
    else:
        print(f"Tools found: {result.get('tools_count', 0)}")
        if result.get('tools_count', 0) > 0:
            print("Tools:", [tool.get('name', '?') for tool in result.get('tools_response', {}).get('result', {}).get('tools', [])])


async def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: mcp_handshake_test.py <config.json>")
        print("   or: mcp_handshake_test.py --stdio <command> [args...]")
        print("   or: mcp_handshake_test.py --http <url>")
        print("   or: mcp_handshake_test.py --websocket <url>")
        sys.exit(1)

    results = []

    if sys.argv[1] == "--stdio":
        if len(sys.argv) < 3:
            print("Error: --stdio requires command")
            sys.exit(1)
        cmd = sys.argv[2]
        args = sys.argv[3:] if len(sys.argv) > 3 else []
        print(f"Testing STDIO: {cmd} {' '.join(args)}")
        result = await test_stdio_mcp(cmd, args)
        results.append(result)

    elif sys.argv[1] == "--http":
        if len(sys.argv) < 3:
            print("Error: --http requires URL")
            sys.exit(1)
        url = sys.argv[2]
        print(f"Testing HTTP: {url}")
        result = await test_http_mcp(url)
        results.append(result)

    elif sys.argv[1] == "--websocket":
        if len(sys.argv) < 3:
            print("Error: --websocket requires URL")
            sys.exit(1)
        url = sys.argv[2]
        print(f"Testing WebSocket: {url}")
        result = await test_websocket_mcp(url)
        results.append(result)

    else:
        # Load config file
        config_file = sys.argv[1]
        try:
            with open(config_file) as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error reading config: {e}")
            sys.exit(1)

        # Test each configured server
        for server in config.get("servers", []):
            transport = server.get("transport", "stdio")

            if transport == "stdio":
                print(f"\nTesting STDIO: {server.get('command')}")
                result = await test_stdio_mcp(
                    server.get("command"),
                    server.get("args", []),
                    server.get("env")
                )
            elif transport == "http" or transport == "sse":
                print(f"\nTesting HTTP: {server.get('url')}")
                result = await test_http_mcp(
                    server.get("url"),
                    server.get("headers")
                )
            elif transport == "websocket":
                print(f"\nTesting WebSocket: {server.get('url')}")
                result = await test_websocket_mcp(
                    server.get("url"),
                    server.get("headers")
                )
            else:
                result = {"status": "error", "message": f"Unknown transport: {transport}"}

            results.append(result)
            print_result(result)

    # Print summary
    print("\n" + "="*50)
    print("Summary:")
    for r in results:
        status_icon = "✓" if r['status'] == 'success' else "✗"
        print(f"{status_icon} {r.get('transport', 'Unknown')}: {r['status']}")

    # Exit with error if any failed
    if any(r['status'] != 'success' for r in results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
