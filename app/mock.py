"""Canned agent/search responses so the UI can be developed and tested without API keys (MOCK_MODE=1)."""
from __future__ import annotations

import asyncio
import random


async def chat_json(system: str, user: str, **kw):
    await asyncio.sleep(random.uniform(0.3, 0.9))
    if "Claim Extractor" in system:
        return {"claims": [
            {"claim": "The Great Wall of China is visible from the Moon with the naked eye.", "quote": "visible from the Moon"},
            {"claim": "Mount Everest is 8,849 metres tall.", "quote": "8,849 metres"},
            {"claim": "Humans use only 10% of their brains.", "quote": "only 10%"},
        ]}
    if "Query Planner" in system:
        return {"queries": ["fact check " + user[7:60], user[7:60] + " official source"]}
    if "Verifier" in system:
        if "Everest" in user:
            return {"verdict": "TRUE", "confidence": 92, "explanation": "A 2020 joint survey measured 8,848.86 m [1].",
                    "correction": "", "citations": [1]}
        return {"verdict": "FALSE", "confidence": 88, "explanation": "Sources describe this as a myth [1][2].",
                "correction": "This is a popular misconception.", "citations": [1, 2]}
    return {"credibility_score": 34, "headline": "Mostly unreliable: 2 of 3 claims are false",
            "summary": "The text repeats two well-known myths. Only the height of Everest checks out.",
            "advice": "Do not share this content without corrections."}


async def search(query: str, max_results: int = 5):
    await asyncio.sleep(random.uniform(0.3, 0.8))
    return [{"title": f"Mock source {i} for: {query[:40]}", "url": f"https://example.com/{abs(hash(query)) % 999}/{i}",
             "content": "Mock evidence content."} for i in range(1, 4)]


async def extract(url: str) -> str:
    await asyncio.sleep(0.5)
    return "Mock article text from " + url
