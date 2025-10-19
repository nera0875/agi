#!/usr/bin/env python3
"""
LOCAL FETCH MCP - Remplacement Smithery
Fetch URL directement sans dépendre de Smithery API
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-fetch")


async def fetch_url(url: str, max_length: int = 50000) -> dict:
    """
    Récupère contenu d'une URL (comme @smithery-ai/fetch)

    Args:
        url: URL à récupérer
        max_length: Longueur max du contenu

    Returns:
        {
            "url": str,
            "content": str,
            "title": str,
            "status_code": int
        }
    """
    logger.info(f"🌐 Fetching URL: {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AGI-Bot/1.0)"
            })

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator='\n', strip=True)

            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "\n\n[... truncated]"

            # Get title
            title = soup.title.string if soup.title else url

            result = {
                "url": url,
                "content": text,
                "title": str(title),
                "status_code": response.status_code,
                "success": True
            }

            logger.info(f"✅ Fetched {len(text)} chars from {url}")
            return result

    except Exception as e:
        logger.error(f"❌ Failed to fetch {url}: {e}")
        return {
            "url": url,
            "content": "",
            "title": "",
            "status_code": 0,
            "error": str(e),
            "success": False
        }


async def extract_elements(url: str, selector: str) -> dict:
    """
    Extrait éléments spécifiques via CSS selector

    Args:
        url: URL à récupérer
        selector: CSS selector (ex: "h1", ".content", "#main")

    Returns:
        {
            "elements": [{"tag": str, "text": str, "html": str}, ...]
        }
    """
    logger.info(f"🔍 Extracting '{selector}' from {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AGI-Bot/1.0)"
            })

            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(selector)

            results = []
            for elem in elements[:50]:  # Max 50 elements
                results.append({
                    "tag": elem.name,
                    "text": elem.get_text(strip=True),
                    "html": str(elem)[:500]  # Limit HTML length
                })

            logger.info(f"✅ Extracted {len(results)} elements")
            return {
                "elements": results,
                "count": len(results),
                "success": True
            }

    except Exception as e:
        logger.error(f"❌ Failed to extract: {e}")
        return {
            "elements": [],
            "count": 0,
            "error": str(e),
            "success": False
        }


async def get_page_metadata(url: str) -> dict:
    """
    Récupère metadata d'une page (title, description, og:tags)

    Returns:
        {
            "title": str,
            "description": str,
            "og_title": str,
            "og_description": str,
            "og_image": str
        }
    """
    logger.info(f"📋 Getting metadata from {url}")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AGI-Bot/1.0)"
            })

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get metadata
            metadata = {
                "url": url,
                "title": "",
                "description": "",
                "og_title": "",
                "og_description": "",
                "og_image": ""
            }

            # Title
            if soup.title:
                metadata["title"] = soup.title.string.strip()

            # Description
            desc = soup.find("meta", attrs={"name": "description"})
            if desc and desc.get("content"):
                metadata["description"] = desc["content"].strip()

            # OpenGraph tags
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                metadata["og_title"] = og_title["content"].strip()

            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                metadata["og_description"] = og_desc["content"].strip()

            og_image = soup.find("meta", attrs={"property": "og:image"})
            if og_image and og_image.get("content"):
                metadata["og_image"] = og_image["content"].strip()

            metadata["success"] = True
            logger.info(f"✅ Got metadata: {metadata['title']}")
            return metadata

    except Exception as e:
        logger.error(f"❌ Failed to get metadata: {e}")
        return {
            "url": url,
            "error": str(e),
            "success": False
        }


# === TEST ===
if __name__ == "__main__":
    async def test():
        print("🧪 Testing Local Fetch MCP\n")

        # Test 1: Fetch URL
        print("1. Fetch Claude Code hooks guide:")
        result = await fetch_url("https://docs.claude.com/en/docs/claude-code/hooks-guide")
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Content: {result.get('content', '')[:200]}...")
        print()

        # Test 2: Metadata
        print("2. Get metadata:")
        metadata = await get_page_metadata("https://docs.claude.com/en/docs/claude-code/hooks-guide")
        print(f"   Title: {metadata.get('title', 'N/A')}")
        print(f"   Description: {metadata.get('description', 'N/A')[:100]}...")
        print()

        # Test 3: Extract elements
        print("3. Extract h2 headers:")
        elements = await extract_elements("https://docs.claude.com/en/docs/claude-code/hooks-guide", "h2")
        for elem in elements.get('elements', [])[:5]:
            print(f"   - {elem['text']}")

    asyncio.run(test())
