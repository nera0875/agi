#!/usr/bin/env python3
"""
LOCAL MCP ROUTER - Routeur pour MCPs hébergés localement
Gère Exa, Context7, Fetch sans dépendre de Smithery
"""
import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-router")

# Chemins des MCPs locaux
MCP_SERVERS_DIR = Path(__file__).parent.parent / "mcp_servers"

MCP_CONFIGS = {
    "exa": {
        "command": "node",
        "args": [str(MCP_SERVERS_DIR / "exa-mcp-server" / ".smithery" / "stdio" / "index.cjs")],
        "env": {
            "EXA_API_KEY": "YOUR_EXA_API_KEY"  # À configurer
        }
    },
    "context7": {
        "command": "node",
        "args": [str(MCP_SERVERS_DIR / "context7" / "dist" / "index.js")],
        "env": {}
    },
    "fetch": {
        "command": "node",
        "args": [str(MCP_SERVERS_DIR / "fetch-mcp" / "dist" / "index.js")],
        "env": {}
    }
}


class LocalMCPClient:
    """Client pour communiquer avec un MCP local via stdio"""

    def __init__(self, mcp_id: str):
        self.mcp_id = mcp_id
        self.config = MCP_CONFIGS.get(mcp_id)
        if not self.config:
            raise ValueError(f"Unknown MCP: {mcp_id}")

        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    async def start(self):
        """Démarre le processus MCP"""
        if self.process:
            return  # Déjà démarré

        logger.info(f"🚀 Starting MCP: {self.mcp_id}")

        self.process = subprocess.Popen(
            [self.config["command"]] + self.config["args"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**self.config.get("env", {}), **dict(subprocess.os.environ)},
            text=True,
            bufsize=1
        )

        # Initialize MCP protocol
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "agi-tools",
                "version": "1.0.0"
            }
        })

        logger.info(f"✅ MCP {self.mcp_id} started")

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une requête JSON-RPC au MCP"""
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }

        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str)
        self.process.stdin.flush()

        # Lire la réponse
        response_str = self.process.stdout.readline()
        if not response_str:
            raise Exception(f"MCP {self.mcp_id} closed unexpectedly")

        response = json.loads(response_str)

        if "error" in response:
            raise Exception(f"MCP error: {response['error']}")

        return response.get("result", {})

    async def list_tools(self) -> list:
        """Liste les tools disponibles"""
        result = await self._send_request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Appelle un tool"""
        logger.info(f"📞 Calling {self.mcp_id}.{tool_name}({arguments})")

        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        return result.get("content", [])

    async def stop(self):
        """Arrête le processus MCP"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

            self.process = None
            logger.info(f"🛑 MCP {self.mcp_id} stopped")


# Pool de clients MCP (réutilisés entre appels)
_mcp_pool: Dict[str, LocalMCPClient] = {}


async def get_mcp_client(mcp_id: str) -> LocalMCPClient:
    """Récupère ou crée un client MCP"""
    if mcp_id not in _mcp_pool:
        client = LocalMCPClient(mcp_id)
        await client.start()
        _mcp_pool[mcp_id] = client

    return _mcp_pool[mcp_id]


async def route_mcp_call(mcp_id: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Route un appel vers le bon MCP local

    Args:
        mcp_id: "exa", "context7", ou "fetch"
        tool_name: Nom du tool à appeler
        arguments: Arguments du tool

    Returns:
        Résultat du tool
    """
    client = await get_mcp_client(mcp_id)
    result = await client.call_tool(tool_name, arguments)
    return result


async def list_local_mcps() -> Dict[str, list]:
    """Liste tous les MCPs locaux et leurs tools"""
    mcps_tools = {}

    for mcp_id in MCP_CONFIGS.keys():
        try:
            client = await get_mcp_client(mcp_id)
            tools = await client.list_tools()
            mcps_tools[mcp_id] = [t.get("name") for t in tools]
        except Exception as e:
            logger.error(f"❌ Failed to list tools for {mcp_id}: {e}")
            mcps_tools[mcp_id] = []

    return mcps_tools


async def shutdown_all_mcps():
    """Arrête tous les MCPs"""
    for client in _mcp_pool.values():
        await client.stop()

    _mcp_pool.clear()


# === TEST ===

if __name__ == "__main__":
    async def test():
        print("🧪 Testing Local MCP Router\n")

        # Test 1: List all MCPs and tools
        print("1. List local MCPs:")
        mcps = await list_local_mcps()
        for mcp_id, tools in mcps.items():
            print(f"   {mcp_id}: {len(tools)} tools")
            for tool in tools[:3]:
                print(f"     - {tool}")
        print()

        # Test 2: Call Exa search (si API key configurée)
        # print("2. Test Exa search:")
        # result = await route_mcp_call("exa", "search", {
        #     "query": "Claude Code hooks",
        #     "numResults": 3
        # })
        # print(f"   Result: {result[:200]}...")
        # print()

        # Test 3: Call Context7
        print("3. Test Context7 resolve:")
        result = await route_mcp_call("context7", "resolve-library-id", {
            "libraryName": "fastapi"
        })
        print(f"   Result: {json.dumps(result, indent=2)[:500]}...")
        print()

        # Test 4: Call Fetch
        print("4. Test Fetch:")
        result = await route_mcp_call("fetch", "fetch_html", {
            "url": "https://docs.claude.com/en/docs/claude-code/hooks-guide"
        })
        print(f"   Result: {str(result)[:200]}...")
        print()

        # Cleanup
        await shutdown_all_mcps()
        print("✅ All tests complete")

    asyncio.run(test())
