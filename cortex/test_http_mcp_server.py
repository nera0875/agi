#!/usr/bin/env python3
"""
Minimal HTTP MCP Server for testing router
Simple Flask server that implements MCP protocol over HTTP
"""

from flask import Flask, request, jsonify
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("http-mcp-server")

app = Flask(__name__)

@app.route("/initialize", methods=["POST"])
def initialize():
    """MCP initialize handshake"""
    logger.info("Initialize handshake")
    data = request.get_json() or {}

    return jsonify({
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "server_info": {
            "name": "test-http-mcp",
            "version": "1.0.0"
        }
    }), 200


@app.route("/tools", methods=["GET"])
def list_tools():
    """List available tools"""
    logger.info("List tools")
    return jsonify({
        "tools": [
            {
                "name": "echo",
                "description": "Echo back the input message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "health",
                "description": "Get server health status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "calculate",
                "description": "Simple calculator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "Operation to perform"
                        },
                        "a": {
                            "type": "number",
                            "description": "First operand"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second operand"
                        }
                    },
                    "required": ["operation", "a", "b"]
                }
            }
        ]
    }), 200


@app.route("/tool/<tool_name>", methods=["POST"])
def call_tool(tool_name):
    """Execute a tool"""
    logger.info(f"Tool call: {tool_name}")
    data = request.get_json() or {}
    args = data.get("arguments", {})

    if tool_name == "echo":
        message = args.get("message", "")
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"Echo: {message}"
                }
            ]
        }), 200

    elif tool_name == "health":
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": "Server is healthy"
                }
            ]
        }), 200

    elif tool_name == "calculate":
        operation = args.get("operation")
        a = args.get("a", 0)
        b = args.get("b", 0)

        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return jsonify({
                        "error": "Division by zero"
                    }), 400
                result = a / b
            else:
                return jsonify({
                    "error": f"Unknown operation: {operation}"
                }), 400

            return jsonify({
                "content": [
                    {
                        "type": "text",
                        "text": f"{a} {operation} {b} = {result}"
                    }
                ]
            }), 200
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 400

    else:
        return jsonify({
            "error": f"Unknown tool: {tool_name}"
        }), 404


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    logger.info(f"Starting HTTP MCP server on port {port}...")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
