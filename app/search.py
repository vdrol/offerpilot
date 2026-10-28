"""Tavily real-time web search + page extraction."""
from __future__ import annotations

import httpx

from . import config

TAVILY_URL = "https://api.tavily.com"


async def search(query: str, max_results: int = 5) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            f"{TAVILY_URL}/search",
            headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
            json={"query": query, "max_results": max_results, "search_depth": "advanced"},
        )
        r.raise_for_status()
        return [
            {"title": x.get("title", ""), "url": x.get("url", ""), "content": (x.get("content") or "")[:1200]}
            for x in r.json().get("results", [])
        ]


async def extract(url: str) -> str:
    async with httpx.AsyncClient(timeout=45) as c:
        r = await c.post(
            f"{TAVILY_URL}/extract",
            headers={"Authorization": f"Bearer {config.TAVILY_API_KEY}"},
            json={"urls": [url]},
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            raise ValueError("Could not extract text from that URL")
        return results[0].get("raw_content", "")
