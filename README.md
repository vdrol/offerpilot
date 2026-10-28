# OfferPilot — your multi-agent job application copilot

**Track:** Best Apps and Agents · **LLM:** NVIDIA Nemotron on **Nebius Token Factory** · **Search:** Tavily

Job seekers send dozens of applications, and every one deserves a tailored resume, a specific cover letter and
interview prep — hours of work per job, so most people send the same generic resume everywhere and get ignored.

OfferPilot does that work in about a minute. Upload your resume (PDF or text), paste a job link or description, and
six AI agents produce:

- **Fit score & gaps** — honest match score, your strengths, each gap with severity and how to close it, missing ATS keywords
- **Tailored resume** — your own bullets rewritten for this job, before → after, with the requirement each one targets
- **Cover letter** — specific to the company, using real recent news found on the web; editable, copy or download
- **Interview prep** — the questions you're likely to get, with answer outlines built from *your* experience, plus smart questions to ask them
- **Company brief** — overview, recent news, culture and talking points, with live sources

It never invents experience: every agent is instructed to only rephrase and emphasise what's in your resume.

## The agents

All six run on an NVIDIA Nemotron model served by Nebius Token Factory.

| Agent | Job |
|---|---|
| **Job Analyst** | Turns a raw posting into structured requirements, responsibilities and ATS keywords |
| **Company Researcher** | Tavily live web search → cited company brief |
| **Fit Analyst** | Scores resume vs. job, finds gaps and how to address them |
| **Resume Tailor** | Rewrites your bullets for this job (truthfully) |
| **Cover Letter Writer** | Writes a specific, cliché-free letter using the research |
| **Interview Coach** | Predicts questions incl. one on your biggest gap, with STAR answer outlines |

```
job link ─► Tavily Extract ─► Job Analyst ─┬─► Company Researcher (Tavily search) ─┬─► Resume Tailor
resume PDF ─► text ────────────────────────┴─► Fit Analyst ─────────────────────────┼─► Cover Letter Writer
                                                                                    └─► Interview Coach
```

Independent agents run in parallel, and progress streams live to the browser (Server-Sent Events).

## Nebius + NVIDIA usage

- All LLM calls go to **Nebius Token Factory**'s OpenAI-compatible endpoint (`NEBIUS_BASE_URL`) — see [`app/llm.py`](app/llm.py).
- Default model: **`nvidia/Llama-3_3-Nemotron-Super-49B-v1_5`** (NVIDIA open model). Set `NEMOTRON_MODEL` to any
  Nemotron on Token Factory; if the configured one isn't listed, the app auto-selects an available `nvidia/` model.
- Nemotron's `/no_think` switch gives fast structured JSON; any `<think>` traces are stripped.
- Optional: run the container on a **Nebius AI Cloud** VM (see Deploy).

## Setup & run

Requires Python 3.9+.

```bash
git clone <your-repo-url> offerpilot && cd offerpilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add NEBIUS_API_KEY and TAVILY_API_KEY
uvicorn app.main:app --port 8000
```

Open http://localhost:8000 → **Use sample resume** → **Use sample job** → **Build my application**.

- Nebius Token Factory key: https://tokenfactory.nebius.com → API keys
- Tavily key: https://app.tavily.com
- No keys? `MOCK_MODE=1 uvicorn app.main:app` runs the full UI with canned responses.
- `GET /api/health` shows the resolved model and which keys are configured.

## API

- `POST /api/resume` (multipart `file`, PDF/TXT) → `{"text": "..."}`
- `POST /api/run` `{"resume": "...", "job_text": "...", "job_url": "..."}` → `text/event-stream` of
  `status`, `agent` (running/done/error), `result` (per agent), `error`, `done` events.

## Deploy

**Docker:**
```bash
docker build -t offerpilot .
docker run -p 8000:8000 --env-file .env offerpilot
```

**Nebius AI Cloud VM:** create a small CPU VM (Ubuntu), install Docker, copy the repo and `.env`, run the two
commands above, open port 8000 (or proxy through Caddy for HTTPS).

**Render / Railway:** new Web Service from this repo, runtime Docker, add the env vars from `.env.example`.

## Privacy

Resumes are processed in memory only and never stored on the server. The browser keeps your resume in
`localStorage` so you don't have to re-upload it for the next job.

## Project layout

```
app/main.py     FastAPI server: resume parsing + SSE endpoint
app/agents.py   the six agents and the parallel orchestration
app/llm.py      Nebius Token Factory / Nemotron client
app/search.py   Tavily search + extract
app/mock.py     offline mock responses
static/index.html  single-file UI
```

## License

MIT — see [LICENSE](LICENSE).
