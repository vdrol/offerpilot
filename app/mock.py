"""Canned agent/search responses so the UI can be developed and tested without API keys (MOCK_MODE=1)."""
from __future__ import annotations

import asyncio
import random


async def chat_json(system: str, user: str, **kw):
    await asyncio.sleep(random.uniform(0.6, 1.6))
    if "Job Analyst" in system:
        return {"company": "Acme Robotics", "role": "Backend Engineer", "location": "Remote", "seniority": "Mid",
                "must_have": ["Python", "REST APIs", "PostgreSQL"], "nice_to_have": ["Kubernetes"],
                "responsibilities": ["Build APIs for fleet telemetry"], "keywords": ["Python", "FastAPI", "Postgres"],
                "summary": "Backend role building telemetry APIs for warehouse robots."}
    if "Company Researcher" in system:
        return {"overview": "Acme Robotics builds warehouse robots [1].",
                "recent_news": ["Raised a Series C in 2026 [2]"], "culture_values": ["Ship weekly [1]"],
                "talking_points": ["Their telemetry platform rewrite [2]"]}
    if "Fit Analyst" in system:
        return {"match_score": 74, "verdict": "Competitive with tailoring.",
                "strengths": ["Python -> 3 years building Flask services"],
                "gaps": [{"requirement": "Kubernetes", "severity": "medium",
                          "how_to_address": "Mention Docker experience; do a weekend k8s project."}],
                "missing_keywords": ["FastAPI", "telemetry"]}
    if "Resume Tailor" in system:
        return {"headline": "Backend engineer who builds reliable Python APIs.",
                "bullets": [{"original": "Worked on Flask APIs", "tailored": "Built Flask REST APIs serving 2M requests/day",
                             "why": "REST APIs"}], "skills_to_list": ["Python", "PostgreSQL"]}
    if "Cover Letter" in system:
        return {"cover_letter": "Dear Acme Robotics team,\n\nMock cover letter.\n\nBest,\nAlex"}
    return {"questions": [{"question": "Design a telemetry ingestion API.", "why_they_ask": "Core of the role",
                           "answer_outline": "Describe your Flask service..."}],
            "questions_to_ask_them": ["How is the Series C changing the roadmap?"]}


async def search(query: str, max_results: int = 5):
    await asyncio.sleep(random.uniform(0.3, 0.8))
    return [{"title": f"Mock source {i} for: {query[:40]}", "url": f"https://example.com/{abs(hash(query)) % 999}/{i}",
             "content": "Mock evidence content."} for i in range(1, 4)]


async def extract(url: str) -> str:
    await asyncio.sleep(0.5)
    return "Mock job posting text from " + url
