# Submission kit (not needed by the app — for you)

## Checklist
- [ ] Add the Nebius key to `.env`, run locally, confirm the sample run works end to end
- [ ] Push to a **public** GitHub repo (LICENSE + README included; `.env` is git-ignored)
- [ ] Deploy (Render/Railway/Nebius VM) → working demo URL; set the keys as environment variables there
- [ ] Record demo video < 3 min, upload to YouTube as **Public**
- [ ] Track: **Best Apps and Agents**
- [ ] Fill the Nebius/NVIDIA feedback form (draft below — edit with your real experience)
- [ ] Add teammates to the submission form

## Demo video script (~2:40)
1. **0:00–0:20 Problem.** "Tailoring a resume, writing a cover letter and prepping for one job takes hours. So people
   send the same generic resume everywhere — and get ignored. OfferPilot does it in a minute."
2. **0:20–0:45 How.** README agent table: six agents, NVIDIA Nemotron on Nebius Token Factory, Tavily live search.
   Flash `app/llm.py` (Token Factory base URL + Nemotron model) and `/api/health`.
3. **0:45–2:10 Live demo.** Upload a real resume PDF, paste a real job link → *Build my application*. Narrate the
   agents lighting up (two pairs run in parallel). Walk the tabs: fit score + gaps → before/after bullets →
   cover letter mentioning real company news → interview questions incl. one about your gap → company brief with sources.
4. **2:10–2:30 Why it matters.** Never invents experience; resume never stored on server; works for any job link.
5. **2:30–2:40 Close.** Open source (MIT), repo + demo links.

## Feedback draft (make it specific to what you actually saw)
- **Nebius Token Factory:** OpenAI-compatible API meant zero SDK changes — stock `openai` client with a different
  `base_url`. Running 3 agents concurrently worked without rate-limit issues at our scale. Latency per call: ___ s.
  Wish list: ___ (e.g. native JSON-schema structured output for Nemotron, clearer model-ID list, per-key usage view).
- **NVIDIA Nemotron:** strong instruction following for structured extraction and honest gap analysis; `/no_think` in the system prompt did NOT disable thinking on Nemotron 3 — long outputs came back empty (whole budget spent reasoning). Passing
  `chat_template_kwargs: {enable_thinking: false}` fixed it and cut a full run from 48s to ~13s. Worth documenting prominently. ___
- **Tavily:** `extract` made job-link input trivial (works on Greenhouse/Lever pages); `advanced` search gave good
  company-news snippets.
