# Submission kit (not needed by the app — for you)

## Checklist
- [ ] Add real keys to `.env`, run locally, confirm a sample check works
- [ ] Push to a **public** GitHub repo (LICENSE + README already included)
- [ ] Deploy (Render/Railway/Nebius VM) → working demo URL
- [ ] Record a demo video < 3 min, upload to YouTube as **Public**
- [ ] Track: **Best Apps and Agents**
- [ ] Fill the Nebius/NVIDIA feedback form (draft below — edit with your real experience)
- [ ] Add teammates to the submission form

## Demo video script (~2:30)
1. **0:00–0:20 Problem.** "Misinformation spreads faster than anyone can check it. Veritas fact-checks any text in under a minute."
2. **0:20–0:45 Stack.** Show README table: 5 agents, NVIDIA Nemotron on Nebius Token Factory, Tavily search. Show `app/llm.py` base URL + model name, and `/api/health` returning the model.
3. **0:45–1:50 Live demo.** Click *Try a sample* → *Fact-check*. Narrate the pipeline lighting up: Extractor finds claims, Planner/Researcher/Verifier run in parallel per claim, cited sources, corrections. Click a cited source.
4. **1:50–2:20 URL mode.** Paste a real news article URL and run it.
5. **2:20–2:30 Close.** Credibility score, open-source MIT, link to repo.

## Feedback draft (make it specific to what you actually saw)
- **Nebius Token Factory:** OpenAI-compatible API meant zero SDK changes — we used the stock `openai` client with a different `base_url`. Latency for Nemotron Super 49B with `/no_think` was ___ s per call. Wish list: ___ (e.g. native JSON-schema/structured output for Nemotron, clearer model-ID list in docs, per-key usage dashboard).
- **NVIDIA Nemotron:** strong at instruction-following for claim extraction and evidence-grounded verdicts. `/no_think` toggle was essential for structured JSON; reasoning traces occasionally leaked as `<think>` and needed stripping. ___
- **Tavily:** `search_depth=advanced` gave high-quality snippets; `extract` made URL input trivial.
