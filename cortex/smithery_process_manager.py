#!/usr/bin/env python3
"""
Smithery Process Manager - Lifecycle management pour MCPs Smithery

Gère les process npx @smithery/cli en mode long-lived:
- Spawn à la demande
- Keep alive avec timeout inactivity
- Auto-cleanup pour éviter memory leak
- Limite max process simultanés
- Cache persistent en PostgreSQL des MCPs utilisés

Architecture:
  use_mcp("exa", "search", {...})
    → SmitheryProcessManager.call()
    → Spawn si pas existant OU réutilise process
    → Envoie JSON-RPC via stdin
    → Lit réponse sur stdout
    → Reset inactivity timer (auto-kill après 5min)
    → Cache le MCP en DB pour réutilisation future

Cache persistent:
  smithery_mcp_cache table:
  - mcp_id: @smithery-ai/fetch
  - last_used: datetime
  - call_count: int
  - tools: [list]
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smithery-process-manager")

# Config
SMITHERY_API_KEY = "0cccee52-3826-4658-8e05-b35aaf2627f1"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
INACTIVITY_TIMEOUT = 300  # 5 minutes
MAX_PROCESSES = 10  # Limite RAM


@dataclass
class MCPProcess:
    """Représente un process MCP Smithery"""
    mcp_id: str
    process: subprocess.Popen
    last_used: datetime
    request_counter: int = 0

    def is_alive(self) -> bool:
        return self.process.poll() is None

    def is_inactive(self) -> bool:
        """Process inactif depuis > INACTIVITY_TIMEOUT"""
        return datetime.now() - self.last_used > timedelta(seconds=INACTIVITY_TIMEOUT)


class SmitheryProcessManager:
    """Gestionnaire de process Smithery avec lifecycle management + cache persistent"""

    def __init__(self, db_pool=None):
        self.processes: Dict[str, MCPProcess] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        self.db_pool = db_pool  # PostgreSQL connection pool

    async def start(self):
        """Démarre le cleanup task + pré-charge MCPs fréquents"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Pré-charge les MCPs fréquents du cache persistent
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    top_mcps = await conn.fetch("""
                        SELECT mcp_id FROM smithery_mcp_cache
                        ORDER BY call_count DESC
                        LIMIT 3
                    """)

                if top_mcps:
                    logger.info(f"📦 Pre-loading {len(top_mcps)} frequent MCPs...")
                    for row in top_mcps:
                        mcp_id = row['mcp_id']
                        # Spawn process en background (non-blocking)
                        asyncio.create_task(self._preload_mcp(mcp_id))
            except Exception as e:
                logger.warning(f"Could not preload MCPs: {e}")

        logger.info("✅ SmitheryProcessManager started")

    async def stop(self):
        """Arrête tous les process et le cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        for mcp_id in list(self.processes.keys()):
            await self._kill_process(mcp_id)

        logger.info("✅ SmitheryProcessManager stopped")

    async def call_tool(
        self,
        mcp_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute tool sur MCP Smithery

        Spawne process si nécessaire, réutilise sinon
        """
        async with self._lock:
            # Get or spawn process
            mcp_process = await self._get_or_spawn(mcp_id)

            if not mcp_process:
                raise Exception(f"Failed to spawn process for {mcp_id}")

            # Send request
            request_id = mcp_process.request_counter + 1
            mcp_process.request_counter = request_id

            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            try:
                # Write to stdin
                request_json = json.dumps(request) + '\n'
                mcp_process.process.stdin.write(request_json)
                mcp_process.process.stdin.flush()

                # Read from stdout (with timeout)
                loop = asyncio.get_event_loop()
                response_line = await asyncio.wait_for(
                    loop.run_in_executor(None, mcp_process.process.stdout.readline),
                    timeout=timeout
                )

                if not response_line:
                    raise Exception(f"No response from {mcp_id}")

                response = json.loads(response_line)

                # Update last used
                mcp_process.last_used = datetime.now()

                # Check for errors
                if "error" in response:
                    raise Exception(f"MCP error: {response['error']}")

                result = response.get("result", {})

                # Cache the MCP for future use
                await self._save_to_cache(mcp_id)

                return result

            except asyncio.TimeoutError:
                logger.error(f"Timeout calling {mcp_id}.{tool_name}")
                await self._kill_process(mcp_id)
                raise Exception(f"Timeout calling {mcp_id}.{tool_name}")

            except Exception as e:
                logger.error(f"Error calling {mcp_id}.{tool_name}: {e}")
                await self._kill_process(mcp_id)
                raise

    async def _get_or_spawn(self, mcp_id: str) -> Optional[MCPProcess]:
        """Get existing process or spawn new one"""

        # Check existing
        if mcp_id in self.processes:
            mcp_process = self.processes[mcp_id]

            if mcp_process.is_alive():
                logger.info(f"♻️  Reusing existing process for {mcp_id}")
                return mcp_process
            else:
                logger.warning(f"Process for {mcp_id} died, respawning...")
                del self.processes[mcp_id]

        # Check limit
        if len(self.processes) >= MAX_PROCESSES:
            logger.warning(f"Max processes reached ({MAX_PROCESSES}), cleaning oldest...")
            await self._cleanup_oldest()

        # Spawn new
        return await self._spawn_process(mcp_id)

    async def _preload_mcp(self, mcp_id: str):
        """Pré-charge MCP fréquent en background au démarrage"""
        try:
            logger.info(f"🔄 Pre-loading {mcp_id} from cache...")
            process = await self._spawn_process(mcp_id)
            if process:
                logger.info(f"✅ Pre-loaded {mcp_id} (ready for instant reuse)")
        except Exception as e:
            logger.warning(f"Could not preload {mcp_id}: {e}")

    async def _spawn_process(self, mcp_id: str) -> Optional[MCPProcess]:
        """Spawn new Smithery CLI process"""

        try:
            logger.info(f"🚀 Spawning process for {mcp_id}...")

            process = subprocess.Popen(
                [
                    "npx", "-y", "@smithery/cli@latest", "run", mcp_id,
                    "--key", SMITHERY_API_KEY,
                    "--profile", SMITHERY_PROFILE
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Wait for CLI to connect (3s)
            await asyncio.sleep(3)

            if not process.poll() is None:
                stderr = process.stderr.read()
                raise Exception(f"Process died immediately: {stderr}")

            # Initialize MCP
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "agi-tools", "version": "1.0"}
                }
            }

            process.stdin.write(json.dumps(init_request) + '\n')
            process.stdin.flush()

            # Read init response
            init_response = process.stdout.readline()
            if not init_response:
                raise Exception("No initialize response")

            response = json.loads(init_response)
            if "error" in response:
                raise Exception(f"Initialize error: {response['error']}")

            # List tools pour capturer les tools disponibles
            tools_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }

            process.stdin.write(json.dumps(tools_request) + '\n')
            process.stdin.flush()

            # Read tools response
            tools_response = process.stdout.readline()
            available_tools = []

            if tools_response:
                try:
                    tools_result = json.loads(tools_response)
                    if "result" in tools_result and "tools" in tools_result["result"]:
                        available_tools = [
                            tool["name"] for tool in tools_result["result"]["tools"]
                        ]
                        logger.info(f"📋 Discovered {len(available_tools)} tools: {available_tools}")
                except:
                    pass

            logger.info(f"✅ Process spawned for {mcp_id} (PID: {process.pid})")

            mcp_process = MCPProcess(
                mcp_id=mcp_id,
                process=process,
                last_used=datetime.now()
            )

            self.processes[mcp_id] = mcp_process

            # Cache tools in DB for future reference
            if available_tools:
                await self._save_to_cache(mcp_id, tools=available_tools)

            return mcp_process

        except Exception as e:
            logger.error(f"Failed to spawn {mcp_id}: {e}")
            return None

    async def _kill_process(self, mcp_id: str):
        """Kill process and remove from dict"""

        if mcp_id not in self.processes:
            return

        mcp_process = self.processes[mcp_id]

        try:
            mcp_process.process.terminate()
            mcp_process.process.wait(timeout=3)
        except:
            mcp_process.process.kill()

        del self.processes[mcp_id]
        logger.info(f"🗑️  Killed process for {mcp_id}")

    async def _cleanup_oldest(self):
        """Kill oldest inactive process"""

        if not self.processes:
            return

        # Sort by last_used
        sorted_processes = sorted(
            self.processes.items(),
            key=lambda x: x[1].last_used
        )

        oldest_mcp_id, _ = sorted_processes[0]
        await self._kill_process(oldest_mcp_id)

    async def _cleanup_loop(self):
        """Background task to cleanup inactive processes"""

        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                to_kill = []

                for mcp_id, mcp_process in self.processes.items():
                    if mcp_process.is_inactive():
                        to_kill.append(mcp_id)

                for mcp_id in to_kill:
                    logger.info(f"⏱️  Process {mcp_id} inactive, killing...")
                    await self._kill_process(mcp_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _save_to_cache(self, mcp_id: str, tools: list = None):
        """Sauvegarde MCP en DB pour cache persistent LONG TERME"""
        if not self.db_pool:
            logger.info(f"💾 MCP {mcp_id} en cache mémoire (5min TTL)")
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Si tools fournis, update tools aussi (permet capture post-création)
                if tools:
                    await conn.execute("""
                        INSERT INTO smithery_mcp_cache (mcp_id, call_count, tools, last_used)
                        VALUES ($1, 1, $2, NOW())
                        ON CONFLICT (mcp_id) DO UPDATE
                        SET call_count = smithery_mcp_cache.call_count + 1,
                            tools = $2,
                            last_used = NOW()
                    """, mcp_id, tools)
                else:
                    # Pas de tools, juste incrementer count
                    await conn.execute("""
                        INSERT INTO smithery_mcp_cache (mcp_id, call_count, tools, last_used)
                        VALUES ($1, 1, '{}', NOW())
                        ON CONFLICT (mcp_id) DO UPDATE
                        SET call_count = smithery_mcp_cache.call_count + 1, last_used = NOW()
                    """, mcp_id)

            logger.info(f"💾 MCP {mcp_id} cachés en DB (persistent)")
        except Exception as e:
            logger.warning(f"Failed to cache {mcp_id} in DB: {e}")
            logger.info(f"💾 MCP {mcp_id} en cache mémoire (fallback)")

    async def get_cached_mcps(self) -> Dict[str, Any]:
        """Récupère tous les MCPs cachés"""
        if not self.db_pool:
            return {}

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT mcp_id, call_count, tools, last_used
                    FROM smithery_mcp_cache
                    ORDER BY call_count DESC
                """)

            return {
                row['mcp_id']: {
                    'call_count': row['call_count'],
                    'tools': row['tools'],
                    'last_used': row['last_used']
                }
                for row in rows
            }
        except Exception as e:
            logger.warning(f"Failed to get cached MCPs: {e}")
            return {}


# Global singleton
_manager: Optional[SmitheryProcessManager] = None


async def get_manager(db_pool=None) -> SmitheryProcessManager:
    """Get or create global manager"""
    global _manager

    if _manager is None:
        _manager = SmitheryProcessManager(db_pool=db_pool)
        await _manager.start()

    return _manager
