"""Veritas multi-agent fact-checking pipeline.

Agents (all powered by NVIDIA Nemotron on Nebius Token Factory):
  1. Claim Extractor  - pulls atomic, check-worthy factual claims out of the input
  2. Query Planner    - writes targeted web-search queries for each claim
  3. Researcher       - runs Tavily real-time search and collects evidence
  4. Verifier         - judges each claim against the evidence, with citations
  5. Editor           - writes the overall credibility report
Claims are researched and verified in parallel; progress is streamed as events.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable

from . import config, llm, mock, search

VERDICTS = ["TRUE", "MOSTLY_TRUE", "MIXED", "MOSTLY_FALSE", "FALSE", "UNVERIFIABLE"]

Emit = Callable[[dict], Awaitable[None]]

if config.MOCK_MODE:
    chat_json = mock.chat_json
    web_search = mock.search
    web_extract = mock.extract
else:
    chat_json = llm.chat_json
    web_search = search.search
    web_extract = search.extract


EXTRACTOR_PROMPT = f"""You are the Claim Extractor agent in a fact-checking team.
Extract up to {config.MAX_CLAIMS} of the most important, independently verifiable factual claims from the text.
Rules: each claim must be self-contained (resolve pronouns, include names, dates, numbers);
skip opinions, predictions and trivial statements; prefer claims with numbers, dates, records or attributions.
Return: {{"claims": [{{"claim": "...", "quote": "short exact snippet from the text"}}]}}"""

PLANNER_PROMPT = """You are the Query Planner agent. Write 2 concise web-search queries that would surface
authoritative evidence to confirm OR refute the claim (one direct, one targeting primary sources or counter-evidence).
Return: {"queries": ["...", "..."]}"""

VERIFIER_PROMPT = f"""You are the Verifier agent, a rigorous professional fact-checker.
Judge the claim ONLY using the numbered evidence provided. Be skeptical of low-quality sources; prefer
official, academic and major news sources. If evidence is insufficient, say UNVERIFIABLE.
Verdict must be one of: {", ".join(VERDICTS)}.
Return: {{"verdict": "...", "confidence": 0-100, "explanation": "2-4 sentences citing evidence like [1], [3]",
"correction": "the accurate version of the claim, or empty string if TRUE", "citations": [1, 3]}}"""

EDITOR_PROMPT = """You are the Editor agent. Given the verified claims, write the final fact-check report.
Return: {"credibility_score": 0-100, "headline": "one-line overall assessment",
"summary": "3-5 sentence plain-language summary for a general reader, mentioning the most important errors",
"advice": "one practical sentence on how the reader should treat this content"}"""


async def extract_claims(text: str) -> list[dict]:
    data = await chat_json(EXTRACTOR_PROMPT, text[: config.MAX_INPUT_CHARS])
    claims = data.get("claims", data) if isinstance(data, dict) else data
    out = []
    for i, c in enumerate(claims[: config.MAX_CLAIMS]):
        if isinstance(c, str):
            c = {"claim": c, "quote": ""}
        if c.get("claim"):
            out.append({"id": i, "claim": c["claim"], "quote": c.get("quote", "")})
    return out


async def check_claim(claim: dict, emit: Emit) -> dict:
    cid = claim["id"]
    await emit({"type": "claim_update", "id": cid, "stage": "planning"})
    plan = await chat_json(PLANNER_PROMPT, f"Claim: {claim['claim']}")
    queries = [q for q in plan.get("queries", []) if isinstance(q, str)][:2] or [claim["claim"]]

    await emit({"type": "claim_update", "id": cid, "stage": "searching", "queries": queries})
    results = await asyncio.gather(*(web_search(q) for q in queries), return_exceptions=True)
    sources, seen = [], set()
    for batch in results:
        if isinstance(batch, Exception):
            continue
        for r in batch:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                sources.append(r)
    sources = sources[:7]

    await emit({"type": "claim_update", "id": cid, "stage": "verifying", "source_count": len(sources)})
    if not sources:
        verdict = {"verdict": "UNVERIFIABLE", "confidence": 0, "explanation": "No web evidence was found.",
                   "correction": "", "citations": []}
    else:
        evidence = "\n\n".join(f"[{i + 1}] {s['title']} ({s['url']})\n{s['content']}" for i, s in enumerate(sources))
        verdict = await chat_json(VERIFIER_PROMPT, f"Claim: {claim['claim']}\n\nEvidence:\n{evidence}")

    v = str(verdict.get("verdict", "UNVERIFIABLE")).upper().replace(" ", "_")
    cites = [int(n) for n in verdict.get("citations", []) if str(n).isdigit() and 1 <= int(n) <= len(sources)]
    result = {
        **claim,
        "verdict": v if v in VERDICTS else "UNVERIFIABLE",
        "confidence": max(0, min(100, int(verdict.get("confidence", 50) or 0))),
        "explanation": verdict.get("explanation", ""),
        "correction": verdict.get("correction", ""),
        "sources": [{"n": i + 1, "title": s["title"], "url": s["url"], "cited": (i + 1) in cites}
                    for i, s in enumerate(sources)],
        "queries": queries,
    }
    await emit({"type": "claim_done", "result": result})
    return result


async def run_pipeline(text: str = "", url: str = "") -> AsyncIterator[dict]:
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(ev: dict) -> None:
        await queue.put(ev)

    async def worker() -> None:
        try:
            body = text
            if url:
                await emit({"type": "stage", "stage": "fetch", "message": f"Reading {url} with Tavily Extract"})
                body = await web_extract(url)
            if not body.strip():
                raise ValueError("Nothing to fact-check — please provide text or a URL.")

            model = "mock-model" if config.MOCK_MODE else await llm.resolve_model()
            await emit({"type": "stage", "stage": "extract", "message": "Claim Extractor agent reading the text",
                        "model": model})
            claims = await extract_claims(body)
            if not claims:
                raise ValueError("No verifiable factual claims found in this text.")
            await emit({"type": "claims", "claims": claims})

            await emit({"type": "stage", "stage": "research",
                        "message": f"Researching {len(claims)} claims in parallel"})
            sem = asyncio.Semaphore(3)

            async def guarded(c: dict) -> dict:
                async with sem:
                    try:
                        return await check_claim(c, emit)
                    except Exception as e:
                        r = {**c, "verdict": "UNVERIFIABLE", "confidence": 0, "explanation": f"Agent error: {e}",
                             "correction": "", "sources": [], "queries": []}
                        await emit({"type": "claim_done", "result": r})
                        return r

            results = await asyncio.gather(*(guarded(c) for c in claims))

            await emit({"type": "stage", "stage": "report", "message": "Editor agent writing the report"})
            digest = "\n".join(
                f"- [{r['verdict']} {r['confidence']}%] {r['claim']} — {r['explanation']}" for r in results
            )
            report = await chat_json(EDITOR_PROMPT, digest)
            await emit({"type": "report", "report": report})
        except Exception as e:
            await emit({"type": "error", "message": str(e)})
        finally:
            await emit({"type": "done"})

    task = asyncio.create_task(worker())
    while True:
        ev = await queue.get()
        yield ev
        if ev["type"] == "done":
            break
    await task
