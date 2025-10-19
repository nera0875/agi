#!/usr/bin/env python3
"""
MCP Installer Worker - Standalone script for background installation
Can be run in parallel for multiple MCPs
"""

import sys
import json
import time
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cortex.mcp_handshake_test import test_stdio_mcp, test_http_mcp, test_websocket_mcp
from cortex.auth_helper import validate_api_key


class MCPInstaller:
    """Standalone MCP installer that runs in background"""

    def __init__(self, mcp_name: str, config: Dict[str, Any]):
        self.mcp_name = mcp_name
        self.config = config
        self.result = {
            "mcp_name": mcp_name,
            "status": "pending",
            "tools": [],
            "errors": [],
            "duration_ms": 0
        }

    def detect_type(self) -> str:
        """Detect MCP type from config"""
        if "url" in self.config:
            if self.config["url"].startswith("ws"):
                return "websocket"
            return "http"
        elif "command" in self.config:
            cmd = self.config["command"]
            if cmd == "npx":
                return "npx"
            elif cmd == "python3" or cmd.endswith(".py"):
                return "python"
            else:
                return "binary"
        else:
            raise ValueError(f"Cannot detect type for config: {self.config}")

    async def test_connection(self, transport_type: str) -> Dict[str, Any]:
        """Test MCP connection based on type"""
        try:
            if transport_type in ["npx", "python", "binary"]:
                # STDIO transport
                result = await test_stdio_mcp(
                    command=self.config.get("command"),
                    args=self.config.get("args", []),
                    env=self.config.get("env", {})
                )
            elif transport_type == "http":
                # HTTP/SSE transport
                result = await test_http_mcp(
                    url=self.config["url"],
                    headers=self.config.get("headers", {})
                )
            elif transport_type == "websocket":
                # WebSocket transport
                result = await test_websocket_mcp(
                    url=self.config["url"],
                    headers=self.config.get("headers", {})
                )
            else:
                raise ValueError(f"Unknown transport type: {transport_type}")

            return result
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "tools": []
            }

    def update_registry(self, tools: list) -> bool:
        """Update MCP registry with new entry"""
        registry_path = Path(__file__).parent.parent / "mcp-registry.json"

        try:
            # Read current registry
            with open(registry_path, 'r') as f:
                registry = json.load(f)

            # Add new MCP
            registry[self.mcp_name] = {
                **self.config,
                "tools": tools,
                "category": "auto-installed",
                "description": f"Auto-installed MCP: {self.mcp_name}"
            }

            # Write updated registry
            with open(registry_path, 'w') as f:
                json.dump(registry, f, indent=2)

            return True
        except Exception as e:
            self.result["errors"].append(f"Registry update failed: {e}")
            return False

    async def install(self) -> Dict[str, Any]:
        """Main installation workflow"""
        start_time = time.time()

        try:
            # 1. Detect type
            transport_type = self.detect_type()
            self.result["transport_type"] = transport_type

            # 2. Test connection
            test_result = await self.test_connection(transport_type)

            if test_result.get("status") == "error":
                self.result["status"] = "failed"
                self.result["errors"].append(test_result.get("error", "Unknown error"))
                return self.result

            # 3. Extract tools
            tools = test_result.get("tools", [])
            self.result["tools"] = tools

            if not tools:
                self.result["status"] = "failed"
                self.result["errors"].append("No tools found in MCP")
                return self.result

            # 4. Update registry
            if not self.update_registry(tools):
                self.result["status"] = "failed"
                return self.result

            # 5. Success
            self.result["status"] = "success"
            self.result["duration_ms"] = int((time.time() - start_time) * 1000)

        except Exception as e:
            self.result["status"] = "failed"
            self.result["errors"].append(f"Installation error: {e}")

        return self.result


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "error": "Usage: install_mcp.py <mcp_name> <config_json>"
        }))
        sys.exit(1)

    mcp_name = sys.argv[1]
    config = json.loads(sys.argv[2])

    # Create installer
    installer = MCPInstaller(mcp_name, config)

    # Run installation
    result = asyncio.run(installer.install())

    # Write result to temp file for easy retrieval
    output_file = f"/tmp/mcp_install_{mcp_name}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Print result to stdout
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
