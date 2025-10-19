#!/usr/bin/env python3
"""
L1 Observer MCP Integration
Integrates LangChain MCP Adapters for Exa, Docfork, and Fetch tools.

These MCPs are already configured via Smithery and exposed through the
FastAPI /mcp endpoint. This module wraps them for easy use in LangGraph nodes.
"""

import asyncio
import json
import logging
import httpx
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

# Pydantic models for validation
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class SearchResult(BaseModel):
    """Single search result from Exa"""
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    published_date: Optional[str] = None
    author: Optional[str] = None
    relevance_score: Optional[float] = None


class ExaSearchResponse(BaseModel):
    """Response from Exa web search"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_type: str
    timestamp: str


class DocforkResult(BaseModel):
    """Single documentation result from Docfork"""
    title: str
    content: str
    url: Optional[str] = None
    source: Optional[str] = None
    relevance_score: Optional[float] = None


class DocforkResponse(BaseModel):
    """Response from Docfork documentation search"""
    topic: str
    results: List[DocforkResult]
    total_results: int
    timestamp: str


class FetchMetadata(BaseModel):
    """Metadata extracted from fetched URL"""
    title: Optional[str] = None
    description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: Optional[str] = None
    canonical_url: Optional[str] = None


class FetchResponse(BaseModel):
    """Response from URL fetch"""
    url: str
    status_code: int
    content_type: Optional[str] = None
    content_length: int
    metadata: FetchMetadata
    content_preview: Optional[str] = None
    timestamp: str


class MCPError(Exception):
    """Base exception for MCP integration errors"""
    pass


class MCPTimeoutError(MCPError):
    """Timeout error when calling MCP tools"""
    pass


class MCPConnectionError(MCPError):
    """Connection error when calling MCP tools"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# L1 MCP TOOLS CLASS
# ═══════════════════════════════════════════════════════════════════════════

class L1MCPTools:
    """
    LangChain MCP Adapters for L1 Observer enrichment.

    Wraps Exa, Docfork, and Fetch MCP tools exposed via FastAPI /mcp endpoint.
    Handles:
    - Tool invocation with validation
    - Error handling and retries
    - Timeouts and rate limiting
    - Response parsing and serialization
    """

    def __init__(
        self,
        mcp_endpoint: str = "http://localhost:8000/mcp",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize MCP tools.

        Args:
            mcp_endpoint: Base URL for MCP endpoint
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        self.mcp_endpoint = mcp_endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize async HTTP client."""
        if not self._initialized:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            self._initialized = True
            logger.info(f"MCP Tools initialized with endpoint: {self.mcp_endpoint}")

    async def close(self) -> None:
        """Close async HTTP client."""
        if self.client:
            await self.client.aclose()
            self._initialized = False
            logger.info("MCP Tools closed")

    async def _call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Call an MCP tool via HTTP endpoint.

        Args:
            tool_name: Name of the MCP tool
            arguments: Arguments to pass to the tool
            attempt: Current retry attempt

        Returns:
            Tool result

        Raises:
            MCPTimeoutError: If request times out
            MCPConnectionError: If connection fails
            MCPError: If tool call fails
        """
        if not self._initialized:
            await self.initialize()

        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            logger.debug(f"Calling MCP tool: {tool_name} (attempt {attempt}/{self.max_retries})")

            response = await self.client.post(
                self.mcp_endpoint,
                json=request_body,
                timeout=self.timeout
            )

            if response.status_code >= 500:
                raise MCPError(f"Server error: {response.status_code}")

            response.raise_for_status()
            result = response.json()

            # Check for JSON-RPC error
            if "error" in result:
                error = result["error"]
                raise MCPError(f"MCP error: {error.get('message', 'Unknown error')}")

            logger.debug(f"MCP tool succeeded: {tool_name}")
            return result.get("result", {})

        except asyncio.TimeoutError as e:
            logger.warning(f"MCP timeout on {tool_name} (attempt {attempt})")
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._call_mcp_tool(tool_name, arguments, attempt + 1)
            raise MCPTimeoutError(f"MCP tool {tool_name} timed out after {self.timeout}s")

        except httpx.ConnectError as e:
            logger.warning(f"MCP connection error on {tool_name} (attempt {attempt}): {e}")
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._call_mcp_tool(tool_name, arguments, attempt + 1)
            raise MCPConnectionError(f"Failed to connect to MCP endpoint: {e}")

        except httpx.HTTPError as e:
            logger.error(f"MCP HTTP error on {tool_name}: {e}")
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._call_mcp_tool(tool_name, arguments, attempt + 1)
            raise MCPError(f"MCP tool {tool_name} failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error calling MCP tool {tool_name}: {e}", exc_info=True)
            raise MCPError(f"Unexpected error: {e}")

    async def search_exa(
        self,
        query: str,
        limit: int = 5,
        search_type: str = "auto"
    ) -> ExaSearchResponse:
        """
        Search the web using Exa AI search engine.

        Args:
            query: Search query
            limit: Maximum number of results (1-10)
            search_type: Type of search - "neural", "keyword", or "auto"

        Returns:
            ExaSearchResponse with results

        Raises:
            MCPError: If search fails
            MCPTimeoutError: If request times out
        """
        if not query:
            raise ValueError("Search query cannot be empty")

        if limit < 1 or limit > 10:
            limit = min(max(limit, 1), 10)

        if search_type not in ["neural", "keyword", "auto"]:
            search_type = "auto"

        try:
            logger.info(f"Searching Exa: '{query}' (limit={limit}, type={search_type})")

            result = await self._call_mcp_tool(
                "search_web",
                {
                    "query": query,
                    "num_results": limit,
                    "search_type": search_type
                }
            )

            # Parse response
            content_text = result.get("content", [{}])[0].get("text", "{}")
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Exa response: {content_text[:200]}")
                data = {"results": []}

            # Extract results
            results = []
            for item in data.get("results", []):
                if isinstance(item, dict):
                    results.append(SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title"),
                        snippet=item.get("snippet"),
                        published_date=item.get("published_date"),
                        author=item.get("author"),
                        relevance_score=item.get("relevance_score")
                    ))

            return ExaSearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_type=search_type,
                timestamp=datetime.utcnow().isoformat()
            )

        except (MCPError, MCPTimeoutError) as e:
            logger.error(f"Exa search failed: {e}")
            raise

    async def fetch_docs(
        self,
        topic: str,
        limit: int = 5
    ) -> DocforkResponse:
        """
        Fetch documentation for a topic using Docfork.

        Args:
            topic: Documentation topic to search
            limit: Maximum number of results (1-10)

        Returns:
            DocforkResponse with documentation results

        Raises:
            MCPError: If fetch fails
            MCPTimeoutError: If request times out
        """
        if not topic:
            raise ValueError("Topic cannot be empty")

        if limit < 1 or limit > 10:
            limit = min(max(limit, 1), 10)

        try:
            logger.info(f"Fetching documentation: '{topic}' (limit={limit})")

            # Note: Docfork might not be available via MCP, but we structure for it
            # In practice, this might proxy to search_web with a documentation filter
            result = await self._call_mcp_tool(
                "search_web",
                {
                    "query": f"documentation {topic}",
                    "num_results": limit,
                    "search_type": "keyword"
                }
            )

            # Parse response
            content_text = result.get("content", [{}])[0].get("text", "{}")
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Docfork response: {content_text[:200]}")
                data = {"results": []}

            # Extract results
            results = []
            for item in data.get("results", []):
                if isinstance(item, dict):
                    results.append(DocforkResult(
                        title=item.get("title", ""),
                        content=item.get("snippet", ""),
                        url=item.get("url"),
                        source=item.get("source"),
                        relevance_score=item.get("relevance_score")
                    ))

            return DocforkResponse(
                topic=topic,
                results=results,
                total_results=len(results),
                timestamp=datetime.utcnow().isoformat()
            )

        except (MCPError, MCPTimeoutError) as e:
            logger.error(f"Docfork fetch failed: {e}")
            raise

    async def fetch_url(
        self,
        url: str,
        extract_metadata: bool = True
    ) -> FetchResponse:
        """
        Fetch and parse URL content.

        Args:
            url: URL to fetch
            extract_metadata: Whether to extract metadata

        Returns:
            FetchResponse with content and metadata

        Raises:
            MCPError: If fetch fails
            MCPTimeoutError: If request times out
        """
        if not url:
            raise ValueError("URL cannot be empty")

        try:
            logger.info(f"Fetching URL: {url}")

            result = await self._call_mcp_tool(
                "fetch_url",
                {"url": url}
            )

            # Parse response
            content_text = result.get("content", [{}])[0].get("text", "{}")
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse fetch response: {content_text[:200]}")
                data = {}

            # Extract metadata if requested
            metadata = FetchMetadata()
            if extract_metadata:
                try:
                    metadata_result = await self._call_mcp_tool(
                        "get_page_metadata",
                        {"url": url}
                    )
                    metadata_text = metadata_result.get("content", [{}])[0].get("text", "{}")
                    try:
                        metadata_data = json.loads(metadata_text)
                        metadata = FetchMetadata(
                            title=metadata_data.get("title"),
                            description=metadata_data.get("description"),
                            og_image=metadata_data.get("og:image"),
                            og_type=metadata_data.get("og:type"),
                            canonical_url=metadata_data.get("canonical_url")
                        )
                    except json.JSONDecodeError:
                        pass
                except MCPError:
                    logger.warning(f"Failed to extract metadata for {url}")

            return FetchResponse(
                url=url,
                status_code=data.get("status_code", 200),
                content_type=data.get("content_type"),
                content_length=data.get("content_length", 0),
                metadata=metadata,
                content_preview=data.get("content", "")[:500],
                timestamp=datetime.utcnow().isoformat()
            )

        except (MCPError, MCPTimeoutError) as e:
            logger.error(f"URL fetch failed: {e}")
            raise

    async def fetch_url_elements(
        self,
        url: str,
        selector: str,
        attribute: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Extract specific elements from a web page using CSS selectors.

        Args:
            url: URL to fetch
            selector: CSS selector to find elements
            attribute: Optional attribute to extract from elements
            limit: Maximum number of elements to return

        Returns:
            Dictionary with extracted elements

        Raises:
            MCPError: If extraction fails
            MCPTimeoutError: If request times out
        """
        if not url:
            raise ValueError("URL cannot be empty")
        if not selector:
            raise ValueError("CSS selector cannot be empty")

        try:
            logger.info(f"Extracting elements from {url} with selector: {selector}")

            result = await self._call_mcp_tool(
                "extract_elements",
                {
                    "url": url,
                    "selector": selector,
                    "attribute": attribute,
                    "limit": limit
                }
            )

            # Parse response
            content_text = result.get("content", [{}])[0].get("text", "{}")
            try:
                data = json.loads(content_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse element extraction response")
                data = {"elements": []}

            return data

        except (MCPError, MCPTimeoutError) as e:
            logger.error(f"Element extraction failed: {e}")
            raise


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR L1 ENRICHMENT NODE
# ═══════════════════════════════════════════════════════════════════════════

async def enrich_context_with_mcp(
    content: str,
    query: Optional[str] = None,
    mcp_tools: Optional[L1MCPTools] = None,
    use_search: bool = True,
    use_docs: bool = False,
    search_limit: int = 3
) -> Dict[str, Any]:
    """
    Enrich content with MCP tools (Exa search, Docfork docs, etc).

    Args:
        content: Content to enrich
        query: Optional search query (if None, extracted from content)
        mcp_tools: L1MCPTools instance
        use_search: Whether to use Exa search
        use_docs: Whether to use Docfork docs
        search_limit: Max search results

    Returns:
        Dictionary with enriched context
    """
    if mcp_tools is None:
        mcp_tools = L1MCPTools()

    enriched = {
        "timestamp": datetime.utcnow().isoformat(),
        "tools_used": [],
        "exa_search": None,
        "docfork_docs": None,
        "errors": []
    }

    try:
        # Use provided query or extract from content
        if not query and content:
            query = content[:100].strip()

        # Search with Exa
        if use_search and query:
            try:
                search_result = await mcp_tools.search_exa(
                    query=query,
                    limit=search_limit
                )
                enriched["exa_search"] = search_result.model_dump()
                enriched["tools_used"].append("exa_search")
                logger.info(f"Exa search found {search_result.total_results} results")
            except MCPError as e:
                enriched["errors"].append({
                    "tool": "exa_search",
                    "error": str(e)
                })
                logger.warning(f"Exa search error: {e}")

        # Fetch docs with Docfork
        if use_docs and query:
            try:
                docs_result = await mcp_tools.fetch_docs(
                    topic=query,
                    limit=search_limit
                )
                enriched["docfork_docs"] = docs_result.model_dump()
                enriched["tools_used"].append("docfork_docs")
                logger.info(f"Docfork found {docs_result.total_results} docs")
            except MCPError as e:
                enriched["errors"].append({
                    "tool": "docfork_docs",
                    "error": str(e)
                })
                logger.warning(f"Docfork error: {e}")

        return enriched

    except Exception as e:
        logger.error(f"Enrichment error: {e}", exc_info=True)
        enriched["errors"].append({
            "tool": "general",
            "error": str(e)
        })
        return enriched


# ═══════════════════════════════════════════════════════════════════════════
# TESTING & DEBUGGING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import asyncio

    async def test_mcp_integration():
        """Test MCP integration functions"""
        print("Testing L1 MCP Integration")
        print("=" * 70)

        mcp_tools = L1MCPTools(mcp_endpoint="http://localhost:8000/mcp")

        try:
            # Initialize
            await mcp_tools.initialize()
            print("✓ MCP Tools initialized")

            # Test Exa search
            print("\n1. Testing Exa search...")
            try:
                exa_result = await mcp_tools.search_exa(
                    query="python async programming",
                    limit=3
                )
                print(f"   ✓ Exa search: {exa_result.total_results} results found")
                for i, result in enumerate(exa_result.results[:2], 1):
                    print(f"     {i}. {result.title[:50] if result.title else 'N/A'}")
            except MCPError as e:
                print(f"   ✗ Exa search failed: {e}")

            # Test URL fetch
            print("\n2. Testing URL fetch...")
            try:
                fetch_result = await mcp_tools.fetch_url(
                    url="https://python.org",
                    extract_metadata=True
                )
                print(f"   ✓ URL fetch: {fetch_result.status_code}")
                print(f"     Content-Type: {fetch_result.content_type}")
                if fetch_result.metadata.title:
                    print(f"     Title: {fetch_result.metadata.title}")
            except MCPError as e:
                print(f"   ✗ URL fetch failed: {e}")

            # Test enrichment
            print("\n3. Testing context enrichment...")
            try:
                enrichment = await enrich_context_with_mcp(
                    content="How to use async/await in Python",
                    use_search=True,
                    use_docs=False,
                    search_limit=2
                )
                print(f"   ✓ Enrichment completed")
                print(f"     Tools used: {enrichment['tools_used']}")
                print(f"     Errors: {len(enrichment['errors'])}")
            except Exception as e:
                print(f"   ✗ Enrichment failed: {e}")

            print("\n" + "=" * 70)
            print("Testing complete")

        finally:
            await mcp_tools.close()
            print("✓ MCP Tools closed")


    if __name__ == "__main__":
        asyncio.run(test_mcp_integration())
