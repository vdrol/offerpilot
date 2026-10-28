from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, llm
from .agents import run_pipeline

STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Veritas — multi-agent fact checker")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class CheckRequest(BaseModel):
    text: str = ""
    url: str = ""


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


@app.post("/api/check")
async def check(req: CheckRequest):
    async def stream():
        async for ev in run_pipeline(text=req.text.strip(), url=req.url.strip()):
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
