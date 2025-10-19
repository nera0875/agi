#!/usr/bin/env python3
"""
STDIO → Streamable HTTP Wrapper
Bridges Claude Code (STDIO) to Backend Streamable HTTP (2025-03-26)

Architecture:
  Claude Code (STDIO) → This script → Backend (http://localhost:8000/mcp)

Spec: MCP 2025-03-26 Streamable HTTP
Transport: JSON-RPC 2.0
"""

import sys
import json
import urllib.request
import urllib.error

BACKEND_URL = "http://localhost:8000/mcp"


def forward_request(request_data: dict) -> dict:
    """Forward JSON-RPC request to Streamable HTTP backend"""

    try:
        # Prepare HTTP request
        data = json.dumps(request_data).encode('utf-8')
        req = urllib.request.Request(
            BACKEND_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            method='POST'
        )

        # Send to backend
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))

    except urllib.error.HTTPError as e:
        # HTTP error from backend
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32603,
                "message": f"Backend HTTP {e.code}: {e.reason}"
            }
        }
    except Exception as e:
        # Other errors
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32603,
                "message": f"Wrapper error: {str(e)}"
            }
        }


def main():
    """STDIO loop - read from stdin, forward to HTTP, write to stdout"""

    while True:
        try:
            # Read JSON-RPC request from stdin
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())

            # Forward to Streamable HTTP backend
            response = forward_request(request)

            # Write JSON-RPC response to stdout
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            # Invalid JSON from Claude Code
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as e:
            # Unexpected error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(error_response) + '\n')
            sys.stdout.flush()


if __name__ == "__main__":
    main()
