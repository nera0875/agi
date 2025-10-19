#!/usr/bin/env python3
"""
Simple MCP Installer Worker
No external dependencies - just adds to registry
"""

import sys
import json
import time
from pathlib import Path


def install_mcp_simple(mcp_name: str, config: dict) -> dict:
    """
    Simple MCP installation - just add to registry
    No handshake test (will be validated later via router)
    """
    start_time = time.time()
    result = {
        "mcp_name": mcp_name,
        "status": "pending",
        "duration_ms": 0
    }

    try:
        # Path to registry
        registry_path = Path(__file__).parent.parent / "mcp-registry.json"

        # Read current registry
        with open(registry_path, 'r') as f:
            registry = json.load(f)

        # Add new MCP
        registry[mcp_name] = {
            **config,
            "category": "auto-installed",
            "description": f"Auto-installed: {mcp_name}"
        }

        # Write updated registry
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)

        # Success
        result["status"] = "success"
        result["duration_ms"] = int((time.time() - start_time) * 1000)

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        result["duration_ms"] = int((time.time() - start_time) * 1000)

    return result


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print(json.dumps({
            "status": "error",
            "error": "Usage: install_mcp_simple.py <mcp_name> <config_json>"
        }))
        sys.exit(1)

    mcp_name = sys.argv[1]
    config = json.loads(sys.argv[2])

    # Run installation
    result = install_mcp_simple(mcp_name, config)

    # Write result to temp file
    output_file = f"/tmp/mcp_install_{mcp_name}.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Print result
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
