"""Thin client for NVIDIA Nemotron served on Nebius Token Factory (OpenAI-compatible API)."""
from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI

from . import config

_client: AsyncOpenAI | None = None
_resolved_model: str | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL)
    return _client


async def resolve_model() -> str:
    """Use the configured Nemotron model; if Token Factory doesn't list it, fall back to any NVIDIA model it does."""
    global _resolved_model
    if _resolved_model:
        return _resolved_model
    _resolved_model = config.NEMOTRON_MODEL
    try:
        models = [m.id async for m in client().models.list()]
        if config.NEMOTRON_MODEL not in models:
            nvidia = [m for m in models if m.lower().startswith("nvidia/")]
            if nvidia:
                preferred = [m for m in nvidia if "nemotron" in m.lower()] or nvidia
                _resolved_model = preferred[0]
    except Exception:
        pass
    return _resolved_model


_THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def _strip_thinking(text: str) -> str:
    text = _THINK_RE.sub("", text)
    if "</think>" in text:  # opening tag was in the prompt template
        text = text.split("</think>", 1)[1]
    return text.strip()


def _extract_json(text: str) -> Any:
    text = _strip_thinking(text)
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
    if start == -1:
        raise ValueError(f"No JSON in model output: {text[:200]}")
    end = max(text.rfind("}"), text.rfind("]"))
    return json.loads(text[start : end + 1])


async def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 4096) -> str:
    model = await resolve_model()
    resp = await client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        # Nemotron 3 reasons by default and can spend the whole budget thinking; agents need direct JSON answers
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return _strip_thinking(resp.choices[0].message.content or "")


async def chat_json(system: str, user: str, **kw) -> Any:
    last_err: Exception | None = None
    for _ in range(2):
        raw = await chat(system + "\nRespond with valid JSON only, no prose.", user, **kw)
        try:
            return _extract_json(raw)
        except Exception as e:  # retry once on malformed JSON
            last_err = e
    raise last_err  # type: ignore[misc]
