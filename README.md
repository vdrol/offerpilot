# Veritas — multi-agent AI fact checker

**Track:** Best Apps and Agents · **LLM:** NVIDIA Nemotron on **Nebius Token Factory** · **Search:** Tavily

Misinformation spreads faster than anyone can check it. Veritas lets anyone paste a post, article or transcript
(or just an article URL) and get back, in under a minute, a claim-by-claim verdict with live web sources.

## How it works

Five cooperating agents, all powered by an NVIDIA Nemotron model served on Nebius Token Factory:

| Agent | Job |
|---|---|
| **Claim Extractor** | Pulls the key verifiable factual claims out of the text, made self-contained |
| **Query Planner** | Writes targeted search queries per claim (direct + primary-source/counter-evidence) |
| **Researcher** | Runs Tavily real-time web search, de-duplicates evidence |
| **Verifier** | Judges each claim only against the numbered evidence → verdict, confidence, correction, citations |
| **Editor** | Writes an overall credibility score and plain-language summary |

Claims are researched and verified **in parallel**, and every step streams live to the browser (Server-Sent Events),
so you watch the agents work.

```
text / URL ─► Tavily Extract ─► Claim Extractor ─┬─► Planner ─► Researcher (Tavily) ─► Verifier ─┐
                                                 ├─► Planner ─► Researcher (Tavily) ─► Verifier ─┼─► Editor ─► report
                                                 └─► ...                                          ┘
```

## Nebius + NVIDIA usage

- All LLM calls go to **Nebius Token Factory**'s OpenAI-compatible endpoint (`NEBIUS_BASE_URL`), see [`app/llm.py`](app/llm.py).
- Default model: **`nvidia/Llama-3_3-Nemotron-Super-49B-v1_5`** (NVIDIA open model). Set `NEMOTRON_MODEL` to use any
  other Nemotron on Token Factory. If the configured model isn't listed, the app auto-selects an available `nvidia/` model.
- Nemotron's `/no_think` system switch is used for fast structured JSON output; any `<think>` traces are stripped.
- Optional: deploy the container on a **Nebius AI Cloud** VM (instructions below).

## Setup & run

Requires Python 3.9+.

```bash
git clone <your-repo-url> veritas && cd veritas
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add NEBIUS_API_KEY and TAVILY_API_KEY
uvicorn app.main:app --port 8000
```

Open http://localhost:8000, click **Try a sample**, then **Fact-check**.

- Get a Nebius Token Factory key: https://tokenfactory.nebius.com → API keys
- Get a Tavily key: https://app.tavily.com
- No keys yet? `MOCK_MODE=1 uvicorn app.main:app` runs the full UI with canned responses.
- Health check: `GET /api/health` shows the resolved model and which keys are configured.

## API

`POST /api/check` with `{"text": "..."}` or `{"url": "https://..."}` → `text/event-stream` of events:
`stage`, `claims`, `claim_update`, `claim_done`, `report`, `error`, `done`.

## Deploy

**Docker (any host):**
```bash
docker build -t veritas .
docker run -p 8000:8000 --env-file .env veritas
```

**Nebius AI Cloud VM:** create a small CPU VM (Ubuntu) in the Nebius console, open port 8000 (or put it behind
Caddy/nginx), install Docker, copy the repo and `.env`, and run the two commands above.

**Render / Railway (free tier):** new Web Service from this repo, runtime Docker, add the env vars from `.env.example`.

## Project layout

```
app/main.py     FastAPI server + SSE endpoint
app/agents.py   the five agents and the parallel orchestration
app/llm.py      Nebius Token Factory / Nemotron client
app/search.py   Tavily search + extract
app/mock.py     offline mock responses
static/index.html  single-file UI
```

## License

MIT — see [LICENSE](LICENSE).
