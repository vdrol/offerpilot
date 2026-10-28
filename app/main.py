from __future__ import annotations

import io
import json
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pypdf import PdfReader

from . import config, llm
from .agents import run_pipeline

STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="OfferPilot — multi-agent job application copilot")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class RunRequest(BaseModel):
    resume: str
    job_text: str = ""
    job_url: str = ""


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "mock_mode": config.MOCK_MODE,
        "nebius_configured": bool(config.NEBIUS_API_KEY),
        "tavily_configured": bool(config.TAVILY_API_KEY),
        "model": "mock-model" if config.MOCK_MODE else (await llm.resolve_model() if config.NEBIUS_API_KEY else None),
        "provider": "Nebius Token Factory",
    }


@app.post("/api/resume")
async def parse_resume(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > 5_000_000:
        raise HTTPException(413, "File too large (max 5 MB)")
    name = (file.filename or "").lower()
    try:
        if name.endswith(".pdf"):
            text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
        else:
            text = data.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(400, f"Could not read file: {e}")
    if not text.strip():
        raise HTTPException(400, "No text found — if it's a scanned PDF, paste the text instead.")
    return {"text": text.strip()}


@app.post("/api/run")
async def run(req: RunRequest):
    async def stream():
        async for ev in run_pipeline(req.resume.strip(), req.job_text.strip(), req.job_url.strip()):
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
