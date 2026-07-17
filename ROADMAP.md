# IndustryIQ — Development Roadmap (Day 2 → Ship)

> **Who this is for:** anyone on the team picking up the project from here.
> Day 1 (2026-07-14) is DONE — the full prototype works end-to-end.
> This file is the single source of truth for **what remains**, in order,
> until the product is submitted/shipped for the *AI Industrial Knowledge
> Intelligence* hackathon (2–4 day build → target ship: **2026-07-17**).

---

## 0. Where we are right now (end of Day 1)

**Working today** (commit `36f5b9a "Done with prototyping"`):

| Area | Status |
|---|---|
| FastAPI backend (`backend/app/`) — engine, graph store (NetworkX), hybrid retrieval (BM25 + model2vec embeddings), GraphRAG fusion | ✅ Done |
| Agents: Copilot / RCA (`app/agents/copilot.py`) + Compliance-gap (`app/agents/compliance.py`) | ✅ Done |
| Dual-mode LLM abstraction (`app/llm.py`): `LiveGemini` (real API) vs `SeedMock` (deterministic offline), `LLM_MODE=auto` | ✅ Done |
| Synthetic-but-coherent corpus (P-101 vibration RCA story; sister pump **P-102** is the cross-doc payoff) — `backend/scripts/corpus_data.py`, `generate_corpus.py`, `build_seed.py` | ✅ Done |
| React/Vite/Tailwind frontend — 5 tabs: **Chat, GraphView, Documents, Compliance, Ingest** | ✅ Done |
| Docs: `README.md`, `ARCHITECTURE.md`, `docs/DEMO_SCRIPT.md`, `docs/PITCH_DECK.md`, `docs/BENCHMARK.md` | ✅ Written |
| One-command run: `./run.sh` (build + serve on :8000), `./run.sh dev` (hot reload) | ✅ Done |

**⚠️ Critical constraint every teammate must know:**
The `ANTHROPIC_API_KEY` in Ram's dev environment is **Claude-Code-restricted** and
cannot power the app, so the live provider was **switched to Google Gemini**
(`google-genai` SDK, free-tier key from https://aistudio.google.com/apikey).
For live mode, put a **`GEMINI_API_KEY` (`AIza...`)** into `.env` (`cp .env.example .env`).
Until then: develop and test with `LLM_MODE=seed` — the app is fully demoable offline.

**Getting started (any machine):** follow README §Quickstart, then run `./run.sh`
and open http://localhost:8000. Ask the chat: *"Why is pump P-101 vibrating and tripping?"*
— if you get the RCA answer with the P-102 sister-pump link + citations, your setup is good.

---

## Day 2 (2026-07-15) — Live mode, hardening, and truth-testing

Goal: go from "prototype that works on Ram's machine in seed mode" to
"robust app that works in **both** modes, on a clean machine, without embarrassing edge cases."

### 2.1 Wire and verify LIVE Gemini mode (highest priority) — ~half day
- [ ] Obtain a personal Gemini API key; put it in `.env`; confirm `LLM_MODE=auto` flips to live.
- [ ] **Live copilot answers:** run every question in `docs/BENCHMARK.md` in live mode.
      Compare against seed answers. Fix prompt issues in `app/agents/copilot.py`
      (grounding, citation format, hallucination guardrails — the answer must cite
      real doc IDs from the retrieval context, never invented ones).
- [ ] **Live ingestion showcase:** run live Gemini extraction over the base corpus
      (entities + relationships) instead of only the authored seed extractions —
      this is a judging differentiator ("a real LLM built this graph").
      Keep the seed as fallback; never delete it.
- [ ] **Live Ingest tab:** drop a real PDF and a scanned image (P&ID photo) —
      verify Gemini vision extraction lands correct nodes/edges in the graph.
      Fix parser bugs in `app/ingestion/parsers.py`.
- [ ] Add a small **mode badge in the UI** ("● Live" / "● Offline seed") so judges
      always know which mode they're seeing — turns the constraint into a feature.

### 2.2 Robustness & failure handling — ~2–3 hrs
- [ ] API-call failures (rate limit, timeout, bad key) must degrade gracefully to
      seed mode with a visible toast — **never** a blank screen or stack trace.
- [ ] Ingest tab: reject/handle unsupported files, empty files, huge files (>10 MB),
      duplicate uploads, non-UTF-8 text. Show progress state while extraction runs.
- [ ] Chat: handle out-of-corpus questions honestly ("I don't have documents on X")
      instead of hallucinating — test with ~10 adversarial off-topic questions.
- [ ] Concurrency: two chat requests at once shouldn't corrupt graph state.
- [ ] Kill any remaining console errors/warnings in the browser devtools.

### 2.3 Clean-machine test — ~1 hr (do this Day 2 evening, not later)
- [ ] Clone the repo fresh on a second laptop (a friend's machine is perfect).
      Follow README verbatim. Every deviation you hit = a README bug; fix it.
- [ ] Verify `./run.sh` works from a totally clean checkout (venv creation,
      pip bootstrap path, seed build, npm install, build, serve).
- [ ] Test on the actual machine + network that will be used at the venue
      (offline seed mode must work with Wi-Fi off — prove it once).

### 2.4 Benchmark evidence — ~2 hrs
- [ ] Execute the benchmark in `docs/BENCHMARK.md` for real (both modes if live
      works): record entity-extraction accuracy, answer correctness, graph-linkage
      hits, time-to-answer. Put actual numbers + a small results table back into
      `BENCHMARK.md`. Judges reward measured claims over adjectives.

---

## Day 3 (2026-07-16) — Polish, demo assets, and the pitch

Goal: everything a judge sees or touches is deliberate.

### 3.1 UI/UX polish pass — ~3–4 hrs
- [ ] **GraphView:** make the evidence-trail traversal visually obvious — highlight
      the path P-101 → work orders → inspection → OEM limit → **P-102 failure**
      when an RCA answer is shown. This is the money shot of the demo.
- [ ] Chat: streaming or typing indicator, markdown rendering of answers,
      clickable citations that open the source doc in the Documents tab.
- [ ] Compliance tab: each gap should link to its evidence pack; make the
      Factory-Act-guard-gap card look audit-ready (severity, regulation clause, docs).
- [ ] Mobile/field-technician view: check the whole app at 390 px width —
      the "works on a technician's phone" claim is in the README; make it true.
- [ ] Loading/empty/error states on every tab. Consistent spacing, dark-mode
      check if applicable, favicon + app title.

### 3.2 Demo video — ~2–3 hrs (record only after 3.1)
- [ ] Follow `docs/DEMO_SCRIPT.md` beat-for-beat. Target 2–3 min.
- [ ] Structure: 15 s problem hook → RCA wow moment (P-102 reveal on the graph)
      → compliance gap → live ingestion of a fresh PDF → close with architecture slide.
- [ ] Record at 1080p+, clean browser profile, hide bookmarks, zoom UI to ~110 %.
      Do 2–3 takes; keep the best. Add voiceover or captions.
- [ ] Upload (YouTube unlisted or per hackathon rules) and link it in README.

### 3.3 Pitch deck & narrative — ~2 hrs
- [ ] Turn `docs/PITCH_DECK.md` outline into actual slides (Google Slides / Pitch).
      Slide order: problem (35 % of the day searching) → demo → **why GraphRAG beats
      vector-RAG** (the no-shared-keywords sister-pump retrieval) → benchmark numbers
      from Day 2.4 → architecture/scalability → business case → team.
- [ ] Rehearse the live demo twice with a timer. Assign roles if presenting as a
      team (driver vs speaker). Prepare answers for the obvious judge questions:
      "is the data real?" (synthetic-but-coherent, and live ingestion proves the
      pipeline), "how does it scale?" (ARCHITECTURE.md story), "what if the API is
      down?" (offline mode — demo it by killing Wi-Fi).

### 3.4 Stretch features — ONLY if 3.1–3.3 are done
Pick at most one; do not start any of these while core polish is unfinished:
- [ ] **Proactive alert card** on the dashboard ("P-101 vibration trending toward
      OEM trip limit — sister pump P-102 failed under the same signature") — makes
      the product feel alive without being asked.
- [ ] Voice input on the mobile field view (Web Speech API) — great on-stage moment.
- [ ] Export compliance evidence pack as PDF.
- [ ] Graph diff animation when a new doc is ingested (before/after node count).

---

## Day 4 (2026-07-17) — Freeze, submit, ship

Goal: zero new features. Only verification and packaging.

### 4.1 Code freeze & final QA — morning
- [ ] Feature freeze by 10:00. Full run-through of the demo script on the
      presentation machine, offline mode first, then live mode.
- [ ] Re-run the clean-machine test one final time from `main`.
- [ ] Tag the release: `git tag v1.0.0 && git push --tags`.

### 4.2 Submission package — check the hackathon rules for exact requirements
- [ ] Public repo (or per rules) with: README (with video link), ARCHITECTURE.md,
      BENCHMARK.md with real numbers, demo video, deck link.
- [ ] `.env.example` committed, **no real keys anywhere in git history**
      (run `git log -p | grep -i "sk-ant"` to be sure).
- [ ] Fill the submission form early — don't fight the portal at the deadline.
- [ ] Optional but strong: deploy a live instance (Render/Railway/Fly.io free tier
      runs FastAPI + static frontend fine; seed mode needs no API key, so a public
      demo URL is safe and free). Add the URL to README + submission.

### 4.3 Presentation
- [ ] Backup plan stack: local offline demo > deployed URL > demo video. Have all three.
- [ ] Bring: charged laptop, HDMI/USB-C adapter, phone with the mobile view open,
      hotspot as network backup.

---

## Ownership template (fill in when the team divides work)

| Workstream | Owner | Days |
|---|---|---|
| Live Gemini mode + prompts (2.1) | ______ | 2 |
| Robustness + ingestion edge cases (2.2) | ______ | 2 |
| Benchmark run + numbers (2.4) | ______ | 2 |
| UI polish + GraphView evidence trail (3.1) | ______ | 3 |
| Demo video (3.2) | ______ | 3 |
| Deck + rehearsal (3.3) | ______ | 3 |
| Submission + deploy (4.x) | ______ | 4 |

## Ground rules for everyone continuing this
1. **Never break seed mode.** It is the stage-proof demo and the air-gapped pitch.
   Every change must pass: `LLM_MODE=seed ./run.sh` → ask the P-101 question → correct RCA answer with citations.
2. **The P-102 sister-pump reveal is the product.** Any refactor of corpus, graph,
   or retrieval must preserve that cross-document link working end-to-end.
3. Commit small and often to `main` (we're a hackathon team, not a PR bureaucracy),
   but pull before push and never force-push.
4. When in doubt about scope: **polish beats features** from Day 3 onward.
