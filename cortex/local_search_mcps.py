#!/usr/bin/env python3
"""
LOCAL SEARCH MCPs - Remplacements Smithery
Implémentations locales de Exa, Docfork, Context7 sans API Smithery
"""
import asyncio
import httpx
import json
import os
from typing import List, Dict, Any

# === EXA SEARCH (via API directe) ===

EXA_API_KEY = os.getenv("EXA_API_KEY", "")  # Optionnel

async def exa_search(query: str, num_results: int = 5, include_domains: List[str] = None) -> Dict[str, Any]:
    """
    Recherche web intelligente (alternative à Exa officiel)

    Utilise DuckDuckGo + metadata extraction comme fallback si pas de clé API Exa
    """
    if EXA_API_KEY:
        # Use official Exa API
        return await _exa_official_search(query, num_results, include_domains)
    else:
        # Fallback: DuckDuckGo + metadata
        return await _exa_fallback_search(query, num_results, include_domains)


async def _exa_official_search(query: str, num_results: int, include_domains: List[str] = None) -> Dict:
    """Exa officiel via API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "query": query,
            "numResults": num_results,
            "type": "auto",
            "contents": {"text": True}
        }

        if include_domains:
            payload["includeDomains"] = include_domains

        response = await client.post(
            "https://api.exa.ai/search",
            json=payload,
            headers={"Authorization": f"Bearer {EXA_API_KEY}"}
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Exa API error: {response.status_code}", "results": []}


async def _exa_fallback_search(query: str, num_results: int, include_domains: List[str] = None) -> Dict:
    """Fallback: DuckDuckGo HTML search + metadata extraction"""
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # DuckDuckGo HTML search
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        response = await client.get(search_url, headers={
            "User-Agent": "Mozilla/5.0 (compatible)"
        })

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for result_div in soup.find_all("div", class_="result")[:num_results]:
            title_tag = result_div.find("a", class_="result__a")
            snippet_tag = result_div.find("a", class_="result__snippet")

            if title_tag:
                url = title_tag.get("href", "")
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                # Filter by domain if specified
                if include_domains:
                    if not any(domain in url for domain in include_domains):
                        continue

                results.append({
                    "url": url,
                    "title": title,
                    "text": snippet,
                    "publishedDate": None
                })

        return {
            "results": results,
            "query": query,
            "fallback": "duckduckgo",
            "requestId": "local-search"
        }


# === DOCFORK (GitHub docs search) ===

async def docfork_search(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Recherche dans documentation GitHub (alternative Docfork)

    Utilise GitHub Search API + content fetching
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # GitHub code search
        search_url = "https://api.github.com/search/code"
        params = {
            "q": f"{query} in:file extension:md path:docs",
            "per_page": limit
        }

        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        response = await client.get(search_url, params=params, headers=headers)

        if response.status_code != 200:
            return {
                "error": f"GitHub API error: {response.status_code}",
                "results": [],
                "note": "Set GITHUB_TOKEN env for better rate limits"
            }

        data = response.json()
        results = []

        for item in data.get("items", [])[:limit]:
            results.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "repository": item.get("repository", {}).get("full_name"),
                "url": item.get("html_url"),
                "score": item.get("score")
            })

        return {
            "results": results,
            "total_count": data.get("total_count", 0),
            "query": query
        }


# === CONTEXT7 (Library docs) ===

async def context7_resolve_library(library_name: str) -> List[Dict[str, Any]]:
    """
    Résout library ID Context7 (fallback: cherche sur npm/pypi)
    """
    results = []

    # Try npm
    async with httpx.AsyncClient(timeout=15.0) as client:
        npm_url = f"https://registry.npmjs.org/{library_name}"
        try:
            response = await client.get(npm_url)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "library_id": f"/npm/{library_name}",
                    "source": "npm",
                    "version": data.get("dist-tags", {}).get("latest"),
                    "description": data.get("description", ""),
                    "homepage": data.get("homepage", "")
                })
        except:
            pass

    # Try PyPI
    async with httpx.AsyncClient(timeout=15.0) as client:
        pypi_url = f"https://pypi.org/pypi/{library_name}/json"
        try:
            response = await client.get(pypi_url)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "library_id": f"/pypi/{library_name}",
                    "source": "pypi",
                    "version": data.get("info", {}).get("version"),
                    "description": data.get("info", {}).get("summary", ""),
                    "homepage": data.get("info", {}).get("home_page", "")
                })
        except:
            pass

    return results


async def context7_get_docs(library_id: str, query: str = "") -> Dict[str, Any]:
    """
    Récupère documentation (fallback: GitHub README + docs)
    """
    # Extract library name from ID
    library_name = library_id.split("/")[-1]

    # Search GitHub for library docs
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to get README
        search_url = f"https://api.github.com/search/repositories"
        params = {"q": library_name, "per_page": 1}

        headers = {"Accept": "application/vnd.github+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        response = await client.get(search_url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if items:
                repo = items[0]
                readme_url = f"https://raw.githubusercontent.com/{repo['full_name']}/main/README.md"

                # Fetch README
                readme_response = await client.get(readme_url)
                if readme_response.status_code == 200:
                    content = readme_response.text

                    # Filter by query if provided
                    if query:
                        lines = content.split("\n")
                        relevant_lines = [l for l in lines if query.lower() in l.lower()]
                        content = "\n".join(relevant_lines[:100])  # Limit

                    return {
                        "library_id": library_id,
                        "source": "github_readme",
                        "repository": repo["full_name"],
                        "content": content[:20000],  # Limit
                        "url": readme_url
                    }

        return {
            "error": "Documentation not found",
            "library_id": library_id
        }


# === TEST ===

if __name__ == "__main__":
    async def test():
        print("🧪 Testing Local Search MCPs\n")

        # Test 1: Exa fallback search
        print("1. Exa Search (fallback):")
        results = await exa_search("Claude Code hooks documentation", num_results=3)
        print(f"   Found {len(results.get('results', []))} results")
        if results.get('results'):
            print(f"   First: {results['results'][0].get('title', 'N/A')}")
        print()

        # Test 2: Docfork
        print("2. Docfork GitHub search:")
        results = await docfork_search("fastapi lifespan events", limit=3)
        print(f"   Total: {results.get('total_count', 0)}")
        if results.get('results'):
            print(f"   First: {results['results'][0].get('repository', 'N/A')}")
        print()

        # Test 3: Context7
        print("3. Context7 library resolution:")
        results = await context7_resolve_library("fastapi")
        print(f"   Found {len(results)} sources")
        for r in results:
            print(f"   - {r['source']}: {r.get('version', 'N/A')}")

    asyncio.run(test())
