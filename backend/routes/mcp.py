"""
MCP Streamable HTTP Routes
Implements MCP spec 2025-03-26 for Claude Code integration
Unified agi-tools MCP: Memory + Smithery + Dynamic Router

Core tools from backend.mcp.agi_tools_mcp:
1. think() - L1/L2/L3 pipeline orchestration
2. memory_search() - Hybrid RAG search
3. memory_store() - Direct L3 storage
4. memory_stats() - System statistics
"""

import json
import logging
from typing import Optional
import httpx

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Import AGI tools
try:
    from backend.mcp.agi_tools_mcp import (
        think,
        memory_search,
        memory_store,
        memory_stats,
        AGI_TOOLS,
    )
    AGI_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AGI Tools MCP not available: {e}")
    AGI_TOOLS_AVAILABLE = False
    AGI_TOOLS = {}

# Smithery configuration
SMITHERY_API_KEY = "0cccee52-3826-4658-8e05-b35aaf2627f1"
SMITHERY_PROFILE = "rolling-ladybug-4DEfPv"
SMITHERY_FETCH_URL = "https://server.smithery.ai/@smithery-ai/fetch/mcp"
SMITHERY_EXA_URL = f"https://server.smithery.ai/exa/mcp?profile={SMITHERY_PROFILE}"

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/health")
async def mcp_health():
    """MCP endpoint health check"""
    tools = ["think", "memory_search", "memory_store", "memory_stats", "fetch_url", "extract_elements", "get_page_metadata", "search_web"]
    return {
        "status": "healthy",
        "transport": "streamable-http",
        "specification": "2025-03-26",
        "tools": tools,
        "agi_tools_available": AGI_TOOLS_AVAILABLE
    }


@router.post("")
async def mcp_endpoint(request: Request):
    """
    MCP Streamable HTTP endpoint
    Implements MCP spec 2025-03-26 (JSON-RPC 2.0)
    """

    # Get memory service from app state
    memory_service = request.app.state.memory_service

    try:
        # Parse JSON-RPC request
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"MCP request: {method}")

        # Handle initialize
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "agi-tools",
                        "version": "1.0.0"
                    }
                }
            })

        # Handle tools/list
        elif method == "tools/list":
            tools_list = [
                {
                    "name": "think",
                    "description": "Super-tool: Process thought through complete L1/L2/L3 memory pipeline. Classifies, extracts concepts, finds relations, searches similar memories, and consolidates knowledge.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The thought, question, or content to process through the memory pipeline"},
                            "context": {"type": "object", "description": "Optional context with session_id, user_id, metadata", "default": {}}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "memory_search",
                    "description": "Search memory using hybrid RAG (semantic + BM25)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "number", "description": "Max results", "default": 5},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                            "project": {"type": "string", "description": "Project ID", "default": "default"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "memory_store",
                    "description": "Store new memory with auto-embeddings",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Content to store"},
                            "type": {"type": "string", "description": "Memory type"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "project": {"type": "string", "default": "default"}
                        },
                        "required": ["text", "type"]
                    }
                },
                {
                    "name": "memory_stats",
                    "description": "Get memory system statistics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "fetch_url",
                    "description": "Fetch a URL and return basic information about the page (via Smithery fetch)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The URL to fetch"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "extract_elements",
                    "description": "Extract specific elements from a web page using CSS selectors (via Smithery fetch)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The URL to fetch"},
                            "selector": {"type": "string", "description": "CSS selector to find elements"},
                            "attribute": {"type": "string", "description": "Optional attribute to extract from elements"},
                            "limit": {"type": "number", "description": "Maximum number of elements to return", "default": 10}
                        },
                        "required": ["url", "selector"]
                    }
                },
                {
                    "name": "get_page_metadata",
                    "description": "Extract comprehensive metadata from a web page (via Smithery fetch)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "The URL to analyze"}
                        },
                        "required": ["url"]
                    }
                },
                {
                    "name": "search_web",
                    "description": "Search the web using Exa AI search (via Smithery)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "num_results": {"type": "number", "description": "Number of results", "default": 10},
                            "search_type": {"type": "string", "description": "Type: neural, keyword, or auto", "default": "auto"}
                        },
                        "required": ["query"]
                    }
                }
            ]
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            })

        # Handle notifications (no response needed)
        elif method.startswith("notifications/"):
            logger.info(f"MCP notification: {method}")
            return Response(status_code=204)  # No Content

        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            result = None

            if tool_name == "think":
                # New think() super-tool - full L1/L2/L3 pipeline
                if AGI_TOOLS_AVAILABLE:
                    try:
                        think_result = await think(
                            query=arguments.get("query", ""),
                            context=arguments.get("context", {})
                        )
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(think_result, indent=2, default=str)
                                }
                            ]
                        }
                    except Exception as e:
                        logger.error(f"Error in think tool: {e}", exc_info=True)
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({"error": str(e), "status": "error"})
                                }
                            ]
                        }
                else:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": "AGI Tools MCP not available", "status": "error"})
                            }
                        ]
                    }

            elif tool_name == "memory_search":
                results = await memory_service.hybrid_search(
                    query=arguments["query"],
                    top_k=arguments.get("limit", 5),
                    user_id=arguments.get("project", "default")
                )

                # Filter by minimum relevance (30%)
                RELEVANCE_THRESHOLD = 0.30
                filtered_results = [
                    doc for doc in results
                    if doc.metadata.get("relevance_score", 0) >= RELEVANCE_THRESHOLD
                ]

                # Filter by tags if provided
                tags_filter = arguments.get("tags", [])
                if tags_filter:
                    filtered_results = [
                        doc for doc in filtered_results
                        if any(tag in doc.metadata.get("tags", []) for tag in tags_filter)
                    ]

                # Serialize Document objects
                serialized_results = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in filtered_results
                ]

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "results": serialized_results,
                                "count": len(results)
                            }, indent=2)
                        }
                    ]
                }

            elif tool_name == "memory_store":
                memory_id = await memory_service.add_memory(
                    content=arguments["text"],
                    source_type=arguments["type"],
                    metadata={"tags": arguments.get("tags", [])},
                    user_id=arguments.get("project", "default")
                )
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "memory_id": str(memory_id),
                                "status": "stored"
                            })
                        }
                    ]
                }

            elif tool_name == "memory_stats":
                stats = await memory_service.get_stats()
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(stats, indent=2)
                        }
                    ]
                }

            elif tool_name == "fetch_url":
                url = arguments["url"]
                async with httpx.AsyncClient(timeout=30) as client:
                    try:
                        response = await client.get(url)
                        response.raise_for_status()
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({
                                        "url": url,
                                        "status_code": response.status_code,
                                        "content_type": response.headers.get("content-type", ""),
                                        "content_length": len(response.content),
                                        "title": response.text.split("<title>")[1].split("</title>")[0] if "<title>" in response.text else None
                                    }, indent=2)
                                }
                            ]
                        }
                    except Exception as e:
                        result = {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps({"error": str(e)})
                                }
                            ]
                        }

            elif tool_name == "extract_elements":
                # Proxy to Smithery fetch MCP
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        smithery_response = await client.post(
                            SMITHERY_FETCH_URL,
                            json={
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "tools/call",
                                "params": {
                                    "name": "extract_elements",
                                    "arguments": arguments
                                }
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        smithery_data = smithery_response.json()
                        result = smithery_data.get("result", {"content": [{"type": "text", "text": json.dumps({"error": "No result from Smithery"})}]})
                except Exception as e:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": f"Smithery error: {str(e)}"})
                            }
                        ]
                    }

            elif tool_name == "get_page_metadata":
                # Proxy to Smithery fetch MCP
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        smithery_response = await client.post(
                            SMITHERY_FETCH_URL,
                            json={
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "tools/call",
                                "params": {
                                    "name": "get_page_metadata",
                                    "arguments": arguments
                                }
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        smithery_data = smithery_response.json()
                        result = smithery_data.get("result", {"content": [{"type": "text", "text": json.dumps({"error": "No result from Smithery"})}]})
                except Exception as e:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": f"Smithery error: {str(e)}"})
                            }
                        ]
                    }

            elif tool_name == "search_web":
                # Proxy to Smithery Exa MCP
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        smithery_response = await client.post(
                            SMITHERY_EXA_URL,
                            json={
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "tools/call",
                                "params": {
                                    "name": "search",
                                    "arguments": arguments
                                }
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        smithery_data = smithery_response.json()
                        result = smithery_data.get("result", {"content": [{"type": "text", "text": json.dumps({"error": "No result from Smithery"})}]})
                except Exception as e:
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": f"Smithery Exa error: {str(e)}"})
                            }
                        ]
                    }

            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }, status_code=400)

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })

        # Unknown method
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=400)

    except Exception as e:
        logger.error(f"MCP error: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status_code=500)
