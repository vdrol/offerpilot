"""OfferPilot multi-agent job-application pipeline.

Agents (all powered by NVIDIA Nemotron on Nebius Token Factory):
  1. Job Analyst         - turns a raw job posting into structured requirements
  2. Company Researcher  - Tavily live web search -> a cited company brief
  3. Fit Analyst         - scores resume vs. job, finds gaps and how to close them
  4. Resume Tailor       - rewrites the user's own bullets for this job (never invents facts)
  5. Cover Letter Writer - writes a specific, non-generic cover letter
  6. Interview Coach     - likely questions with answers drawn from the user's real experience
Stage 1 runs first; 2+3 run in parallel; then 4, 5, 6 run in parallel. Progress streams as events.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable

from . import config, llm, mock, search

Emit = Callable[[dict], Awaitable[None]]

if config.MOCK_MODE:
    chat_json = mock.chat_json
    web_search = mock.search
    web_extract = mock.extract
else:
    chat_json = llm.chat_json
    web_search = search.search
    web_extract = search.extract

HONESTY = ("Never invent employers, titles, degrees, metrics, tools or achievements that are not in the resume. "
           "You may rephrase, reorder and emphasise what is there.")

JOB_ANALYST = """You are the Job Analyst agent. Read the job posting and extract its real requirements.
Return: {"company": "...", "role": "...", "location": "...", "seniority": "...",
"must_have": ["skill or requirement", ...], "nice_to_have": [...], "responsibilities": ["...", ...],
"keywords": ["ATS keywords exactly as written in the posting", ...], "summary": "2 sentences on what this job really is"}"""

RESEARCHER = """You are the Company Researcher agent. Using ONLY the numbered web results, write a brief a candidate
can use in a cover letter and interview. Cite sources like [2].
Return: {"overview": "2-3 sentences on what the company does", "recent_news": ["fact with citation", ...],
"culture_values": ["...", ...], "talking_points": ["specific thing the candidate could mention", ...]}"""

FIT_ANALYST = f"""You are the Fit Analyst agent, a blunt but kind senior recruiter. Compare the resume to the job.
Return: {{"match_score": 0-100, "verdict": "one-line honest assessment",
"strengths": ["requirement -> evidence from resume", ...],
"gaps": [{{"requirement": "...", "severity": "high|medium|low", "how_to_address": "concrete advice"}}],
"missing_keywords": ["job keywords absent from the resume", ...]}}
Score honestly: 85+ = strong match, 60-84 = competitive with tailoring, below 60 = stretch. {HONESTY}"""

TAILOR = f"""You are the Resume Tailor agent. Rewrite the candidate's most relevant resume bullets so they target
this job: lead with impact, use the job's keywords where truthful, keep each bullet under 30 words. {HONESTY}
Return: {{"headline": "a tailored 1-2 sentence professional summary",
"bullets": [{{"original": "exact original bullet or line", "tailored": "rewritten bullet", "why": "which requirement it targets"}}],
"skills_to_list": ["skills from the resume worth listing first for this job"]}}
Give 5-8 bullets."""

COVER = f"""You are the Cover Letter Writer agent. Write a cover letter of 250-330 words: specific, warm, confident,
no cliches ("I am writing to express my interest", "passionate", "team player"). Open with a concrete hook that
connects the candidate to something real about the company from the research. Use 2 specific achievements from
the resume. {HONESTY}
Return: {{"cover_letter": "full letter text with \\n line breaks, signed with the candidate's name if known"}}"""

COACH = f"""You are the Interview Coach agent. Predict the questions this candidate is most likely to be asked for
this job (mix technical/role-specific, behavioural, and one about their biggest gap). For each, give an answer
outline built from the candidate's REAL experience using STAR where relevant. {HONESTY}
Return: {{"questions": [{{"question": "...", "why_they_ask": "...", "answer_outline": "..."}}],
"questions_to_ask_them": ["smart question referencing the company research", ...]}}
Give 6 questions and 3 questions to ask them."""


async def research_company(job: dict) -> dict:
    company = job.get("company") or ""
    if not company or company.lower() in ("unknown", "n/a"):
        return {"overview": "Company name not found in the posting.", "recent_news": [], "culture_values": [],
                "talking_points": [], "sources": []}
    queries = [f"{company} company news 2026", f"{company} mission values culture {job.get('role', '')}"]
    batches = await asyncio.gather(*(web_search(q, 5) for q in queries), return_exceptions=True)
    sources, seen = [], set()
    for b in batches:
        if isinstance(b, Exception):
            continue
        for r in b:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                sources.append(r)
    sources = sources[:8]
    if not sources:
        return {"overview": "No web results found.", "recent_news": [], "culture_values": [],
                "talking_points": [], "sources": []}
    evidence = "\n\n".join(f"[{i + 1}] {s['title']} ({s['url']})\n{s['content']}" for i, s in enumerate(sources))
    brief = await chat_json(RESEARCHER, f"Company: {company}\n\nWeb results:\n{evidence}")
    brief["sources"] = [{"n": i + 1, "title": s["title"], "url": s["url"]} for i, s in enumerate(sources)]
    return brief


def _brief_text(brief: dict) -> str:
    parts = [brief.get("overview", "")]
    for k in ("recent_news", "culture_values", "talking_points"):
        parts += [f"- {x}" for x in brief.get(k, []) if isinstance(x, str)]
    return "\n".join(parts)


async def run_pipeline(resume: str, job_text: str = "", job_url: str = "") -> AsyncIterator[dict]:
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(ev: dict) -> None:
        await queue.put(ev)

    async def agent(key: str, coro: Awaitable[Any]) -> Any:
        await emit({"type": "agent", "key": key, "state": "running"})
        try:
            data = await coro
            await emit({"type": "result", "key": key, "data": data})
            await emit({"type": "agent", "key": key, "state": "done"})
            return data
        except Exception as e:
            await emit({"type": "agent", "key": key, "state": "error", "message": str(e)})
            return None

    async def worker() -> None:
        try:
            if not resume.strip():
                raise ValueError("Add your resume first (upload a PDF or paste the text).")
            posting = job_text
            if job_url:
                await emit({"type": "status", "message": "Reading the job posting with Tavily Extract"})
                posting = await web_extract(job_url)
            if not posting.strip():
                raise ValueError("Add a job posting (paste the description or a link).")
            cv = resume[: config.MAX_INPUT_CHARS]
            posting = posting[: config.MAX_INPUT_CHARS]
            model = "mock-model" if config.MOCK_MODE else await llm.resolve_model()
            await emit({"type": "status", "message": f"Agents running on {model}", "model": model})

            job = await agent("job", chat_json(JOB_ANALYST, posting))
            if not job:
                raise ValueError("Couldn't understand the job posting.")
            job_ctx = (f"JOB: {job.get('role')} at {job.get('company')}\nSummary: {job.get('summary')}\n"
                       f"Must have: {job.get('must_have')}\nNice to have: {job.get('nice_to_have')}\n"
                       f"Responsibilities: {job.get('responsibilities')}\nKeywords: {job.get('keywords')}")

            brief, fit = await asyncio.gather(
                agent("company", research_company(job)),
                agent("fit", chat_json(FIT_ANALYST, f"{job_ctx}\n\nRESUME:\n{cv}")),
            )
            brief_ctx = _brief_text(brief or {})
            gaps = "; ".join(g.get("requirement", "") for g in (fit or {}).get("gaps", []) if isinstance(g, dict))

            await asyncio.gather(
                agent("tailor", chat_json(TAILOR, f"{job_ctx}\n\nRESUME:\n{cv}")),
                agent("cover", chat_json(COVER, f"{job_ctx}\n\nCOMPANY RESEARCH:\n{brief_ctx}\n\nRESUME:\n{cv}",
                                         temperature=0.6)),
                agent("coach", chat_json(COACH, f"{job_ctx}\n\nCANDIDATE GAPS: {gaps}\n\n"
                                                f"COMPANY RESEARCH:\n{brief_ctx}\n\nRESUME:\n{cv}",
                                         max_tokens=3000)),
            )
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
