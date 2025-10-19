#!/usr/bin/env python3
"""
MCP Type Detector - Automatically detect MCP type and generate registry config

Supports:
- NPX packages (@org/package format)
- HTTP URLs
- Python scripts (.py files)
- Binary executables (absolute paths)
- Node.js scripts (.js files)
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class MCPDetector:
    """Detect MCP type and generate configuration"""

    # Type detection patterns
    TYPE_PATTERNS = {
        "npx": lambda x: ("@" in x and "/" in x) or re.match(r"^@[\w-]+/[\w-]+", x),
        "http": lambda x: x.startswith("http://") or x.startswith("https://"),
        "python": lambda x: x.endswith(".py"),
        "nodejs": lambda x: x.endswith(".js"),
        "binary": lambda x: os.path.isabs(x) and os.path.isfile(x) and os.access(x, os.X_OK),
    }

    COMMAND_MAP = {
        "npx": "npx",
        "http": "curl",
        "python": "python3",
        "nodejs": "node",
        "binary": None,  # Use the path as command
    }

    DEFAULT_TOOLS = {
        "npx": [],  # Will be set per provider
        "http": ["fetch", "parse"],
        "python": ["execute", "call_function"],
        "nodejs": ["execute", "call_function"],
        "binary": ["execute"],
    }

    def __init__(self):
        self.detected_type = None
        self.input_str = None
        self.credentials = {}

    def detect_type(self, input_str: str) -> str:
        """Detect MCP type from input string"""
        for mcp_type, pattern_func in self.TYPE_PATTERNS.items():
            try:
                if pattern_func(input_str):
                    self.detected_type = mcp_type
                    return mcp_type
            except Exception:
                continue

        # Default to binary if it's an absolute path
        if os.path.isabs(input_str):
            self.detected_type = "binary"
            return "binary"

        raise ValueError(f"Cannot detect MCP type from: {input_str}")

    def parse_npx_package(self, package: str) -> Tuple[str, str]:
        """Parse NPX package into org and name"""
        match = re.match(r"^@([\w-]+)/([\w-]+)(?:@(.+))?$", package)
        if match:
            org, name, version = match.groups()
            return f"{org}/{name}", version or "latest"
        raise ValueError(f"Invalid NPX package format: {package}")

    def extract_provider_name(self, input_str: str, mcp_type: str) -> str:
        """Extract provider name from input"""
        if mcp_type == "npx":
            # Extract from @org/package -> package
            match = re.search(r"/(\w+)(?:@|$)", input_str)
            if match:
                return match.group(1)
            return input_str.replace("@", "").replace("/", "-")

        elif mcp_type == "http":
            # Extract domain from URL
            match = re.search(r"https?://([^/]+)", input_str)
            if match:
                domain = match.group(1)
                return domain.split(".")[-2]  # Get main domain part
            return "http-service"

        elif mcp_type == "python":
            # Extract filename without .py
            return Path(input_str).stem

        elif mcp_type == "nodejs":
            # Extract filename without .js
            return Path(input_str).stem

        elif mcp_type == "binary":
            # Extract binary name
            return Path(input_str).stem

        return "mcp-service"

    def build_npx_args(self, package: str, credentials: Dict = None) -> list:
        """Build NPX command arguments"""
        args = ["-y", "@smithery/cli@latest", "run", package]

        # Add credentials as flags if provided
        if credentials:
            for key, value in credentials.items():
                # Convert key to flag format (API_KEY -> --api-key)
                flag = "--" + key.lower().replace("_", "-")
                args.extend([flag, value])

        return args

    def build_python_args(self, script_path: str) -> list:
        """Build Python command arguments"""
        return [script_path]

    def build_nodejs_args(self, script_path: str) -> list:
        """Build Node.js command arguments"""
        return [script_path]

    def build_binary_args(self, binary_path: str) -> list:
        """Build binary command arguments"""
        return []

    def build_config(
        self,
        input_str: str,
        credentials: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[list] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate MCP registry configuration"""

        self.input_str = input_str
        self.credentials = credentials or {}

        # Detect type
        mcp_type = self.detect_type(input_str)

        # Determine name
        provider_name = name or self.extract_provider_name(input_str, mcp_type)

        # Build command and args
        if mcp_type == "npx":
            command = "npx"
            args = self.build_npx_args(input_str, self.credentials)

        elif mcp_type == "http":
            command = "curl"
            args = ["-s", input_str]

        elif mcp_type == "python":
            if not os.path.isfile(input_str):
                raise ValueError(f"Python script not found: {input_str}")
            command = "python3"
            args = self.build_python_args(input_str)

        elif mcp_type == "nodejs":
            if not os.path.isfile(input_str):
                raise ValueError(f"Node.js script not found: {input_str}")
            command = "node"
            args = self.build_nodejs_args(input_str)

        elif mcp_type == "binary":
            if not os.path.isfile(input_str):
                raise ValueError(f"Binary not found: {input_str}")
            if not os.access(input_str, os.X_OK):
                raise ValueError(f"File is not executable: {input_str}")
            command = input_str
            args = []

        else:
            raise ValueError(f"Unsupported MCP type: {mcp_type}")

        # Build config dict
        config = {
            "command": command,
            "args": args,
            "transport": "stdio",
        }

        # Add environment variables from credentials if applicable
        env_vars = {}
        if mcp_type in ["python", "nodejs", "binary"] and self.credentials:
            env_vars.update(self.credentials)

        if env_vars:
            config["env"] = env_vars

        # Add tools
        config["tools"] = tools or self.DEFAULT_TOOLS.get(mcp_type, [])

        # Add category
        config["category"] = category or self._infer_category(provider_name, mcp_type)

        # Add description
        config["description"] = (
            description
            or f"{provider_name.capitalize()} MCP ({mcp_type})"
        )

        return {provider_name: config}

    def _infer_category(self, provider_name: str, mcp_type: str) -> str:
        """Infer category from provider name"""
        categories_map = {
            "search": ["search", "exa", "algolia", "typesense", "elasticsearch"],
            "database": ["postgres", "mongodb", "redis", "dynamodb"],
            "ai": [
                "openai",
                "anthropic",
                "huggingface",
                "replicate",
                "stability",
            ],
            "web": ["fetch", "browser", "playwright", "puppeteer"],
            "communication": [
                "slack",
                "discord",
                "telegram",
                "twilio",
                "sendgrid",
            ],
            "development": ["github", "gitlab", "jira", "linear"],
            "infrastructure": ["docker", "kubernetes", "terraform"],
            "observability": ["sentry", "datadog", "grafana", "prometheus"],
        }

        provider_lower = provider_name.lower()
        for category, keywords in categories_map.items():
            if any(keyword in provider_lower for keyword in keywords):
                return category

        return "utility"


def detect_and_config(
    input_str: str,
    credentials: Optional[Dict[str, str]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tools: Optional[list] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to detect MCP type and generate config"""
    detector = MCPDetector()
    return detector.build_config(
        input_str=input_str,
        credentials=credentials,
        name=name,
        description=description,
        tools=tools,
        category=category,
    )


# Example usage and CLI
if __name__ == "__main__":
    import sys

    print("MCP Detector - Type Detection and Configuration Generator\n")

    # Example 1: NPX Package
    print("=" * 60)
    print("Example 1: NPX Package (@openai/mcp)")
    print("=" * 60)
    config1 = detect_and_config(
        "@openai/mcp",
        credentials={"OPENAI_API_KEY": "sk-xxx"},
        description="OpenAI MCP integration",
        tools=["chat", "embeddings"],
        category="ai",
    )
    print(json.dumps(config1, indent=2))

    # Example 2: HTTP URL
    print("\n" + "=" * 60)
    print("Example 2: HTTP Service URL")
    print("=" * 60)
    config2 = detect_and_config(
        "https://api.example.com/mcp",
        credentials={"API_KEY": "bearer-token-xxx"},
        description="External HTTP MCP service",
    )
    print(json.dumps(config2, indent=2))

    # Example 3: Python Script
    print("\n" + "=" * 60)
    print("Example 3: Python Script")
    print("=" * 60)
    # Create a dummy Python script for demo
    test_script = "/tmp/test_mcp.py"
    with open(test_script, "w") as f:
        f.write("#!/usr/bin/env python3\nprint('MCP Service')\n")

    try:
        config3 = detect_and_config(
            test_script,
            credentials={"DATABASE_URL": "postgresql://..."},
            description="Custom Python MCP service",
            tools=["query", "execute"],
            category="database",
        )
        print(json.dumps(config3, indent=2))
    except Exception as e:
        print(f"Error: {e}")

    # Example 4: Interactive mode
    print("\n" + "=" * 60)
    print("Interactive Mode")
    print("=" * 60)
    print("\nUsage:")
    print("  python mcp_detector.py <input> [--name NAME] [--creds JSON]")
    print("\nExamples:")
    print("  python mcp_detector.py @smithery/fetch")
    print("  python mcp_detector.py https://api.example.com/mcp")
    print("  python mcp_detector.py /usr/local/bin/mcp-service")
    print("  python mcp_detector.py /path/to/script.py --creds '{\"KEY\": \"value\"}'")

    if len(sys.argv) > 1 and sys.argv[1] not in ["--help", "-h"]:
        detector = MCPDetector()
        try:
            input_str = sys.argv[1]
            creds = {}

            # Parse credentials if provided
            if "--creds" in sys.argv:
                idx = sys.argv.index("--creds")
                if idx + 1 < len(sys.argv):
                    creds = json.loads(sys.argv[idx + 1])

            mcp_type = detector.detect_type(input_str)
            config = detector.build_config(input_str, credentials=creds)

            print(f"\nDetected type: {mcp_type}")
            print("\nGenerated configuration:")
            print(json.dumps(config, indent=2))

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
