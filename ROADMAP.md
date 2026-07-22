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
- [x] Live provider implemented (`LiveGemini`, google-genai SDK, structured output +
      vision). **Blocked on a key:** put a `GEMINI_API_KEY` in `.env` to verify.
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
- [x] Add a small **mode badge in the UI** ("● Live Gemini" / "● Offline demo") so judges
      always know which mode they're seeing — turns the constraint into a feature.

### 2.2 Robustness & failure handling — ~2–3 hrs
- [x] API-call failures degrade gracefully: live answer/extraction failures fall back
      to seed mode mid-request with a note appended to the answer (engine.py).
- [x] Ingest tab: unsupported/empty/huge (>10 MB)/duplicate/non-UTF-8 uploads are
      rejected with friendly error messages; progress state shown while extracting.
- [x] Chat: out-of-corpus questions honestly refused (absolute-cosine relevance gate
      in graphrag.py) — verified with 10 adversarial off-topic questions, 10/10 refused.
- [x] Concurrency: atomic index rebuild + ingest lock; verified with 4 parallel
      queries + 3 parallel ingests, graph stayed consistent.
- [ ] Kill any remaining console errors/warnings in the browser devtools.
      (needs a manual browser pass)

### 2.3 Clean-machine test — ~1 hr (do this Day 2 evening, not later)
- [ ] Clone the repo fresh on a second laptop (a friend's machine is perfect).
      Follow README verbatim. Every deviation you hit = a README bug; fix it.
- [ ] Verify `./run.sh` works from a totally clean checkout (venv creation,
      pip bootstrap path, seed build, npm install, build, serve).
- [ ] Test on the actual machine + network that will be used at the venue
      (offline seed mode must work with Wi-Fi off — prove it once).

### 2.4 Benchmark evidence — ~2 hrs
- [x] Executed in seed mode (2026-07-17): **100 % doc-citation recall, 100 % key-fact
      recall, median 4 ms latency, 10/10 off-topic refusals** — results table is in
      `docs/BENCHMARK.md`. Live-mode run still pending an API key.

---

## Day 3 (2026-07-16) — Polish, demo assets, and the pitch

Goal: everything a judge sees or touches is deliberate.

### 3.1 UI/UX polish pass — ~3–4 hrs
- [x] **GraphView:** evidence trail highlighted — answer `graph_paths` render as amber
      edges with animated particles + halo rings on trail nodes, with an
      "evidence trail from last answer" badge. Verified all RCA hops are drawable.
- [x] Chat: typing indicator, rich answer rendering, clickable citations that open
      the source doc in the Documents tab (was already in place; API errors now
      surface friendly messages).
- [x] Compliance tab: gap cards show severity + regulation clause + clickable
      evidence-doc chips (was already in place).
- [ ] Mobile/field-technician view: check the whole app at 390 px width —
      (needs a manual browser pass; layout has md: breakpoints + field mode).
- [x] Favicon + app title + theme-color added. Loading/empty states exist on
      Compliance/Chat/Ingest. (final visual sweep still manual)

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
- [x] **Proactive alert card** on the chat empty state ("P-101 at 5.8 mm/s trending
      toward the 7.1 mm/s trip limit — P-102 failed under the same signature");
      tapping it runs the RCA. Facts match the corpus (WO-2502 / OEM-KDP-P101).
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

## Phase 2 (2026-07-20 →) — Differentiator features

> The five suggested build areas are what every team will build. These features
> attack the parts of the problem statement everyone else ignores — the
> knowledge cliff and answer trust. Build order agreed: one at a time, verify,
> then next.

- [x] **1. Trust Layer — contradiction & staleness detection** (2026-07-20)
      `app/agents/trust.py` + `/api/trust` + Trust tab + trust strip on every answer.
      * Freshness: every doc scores 0..1, decaying by doc-type half-life against
        the **corpus clock** (newest evidence date — deterministic, moves on ingest).
        Incident reports & statutes are evergreen (lessons/law don't expire).
      * Conflict detectors (generic regex/graph scanners, run on ingested docs too):
        numeric setpoint disagreement (OEM trip 7.1 vs WO-2478's 7.0 mm/s),
        SOP acceptance breach (WO-2502 closed at 5.8 mm/s vs SOP-CDU-07 "do not
        accept > 4.5"), doc-vs-reality (coupling guard required but documented OFF),
        stale drawing (2019 P&ID pre-dates 4 maintenance events).
      * Every copilot answer now carries `trust`: worst-source freshness +
        warnings when cited docs are conflicted/stale (Chat shows amber TRUST CHECK).
      * Verified: seed mode intact (0.98 conf RCA + trust), live mode works,
        off-topic refusal unaffected, `/api/trust` ~5 ms.
- [x] **2. Voice-first, multilingual field mode** (2026-07-20)
      `src/voice.js` + `src/dossier.js` + Chat integration + backend `lang` param.
      * Voice queries via Web Speech API (mic button, live transcript, pulsing
        listening state); spoken answers via speechSynthesis; hands-free loop in
        field mode (answer spoken → mic re-opens automatically).
      * 7 languages (EN/HI/TE/TA/KN/MR/BN): live Gemini answers in the chosen
        language with equipment tags, [DOC:] citations, values & units kept
        verbatim (verified: Hindi answer preserved P-101 / 4.5 mm/s / [DOC:...]).
        Seed mode stays English (authored answers).
      * Offline dossier: every answer + full text of cited docs cached in
        localStorage; when connectivity drops the copilot serves the best-matching
        cached answer with an OFFLINE DOSSIER badge + banner (Chrome ASR needs
        network, so offline input is typed — that's a browser limit).
- [ ] **3. Tacit Knowledge Capture ("Exit Interview AI")** — structured interview
      agent for retiring experts → knowledge entries linked to equipment tags,
      contradiction check against SOPs via the Trust Layer.
- [ ] **4. Interactive P&ID** — clickable schematic as the navigation layer;
      tap a pump → full dossier (history, failure modes, procedures, gaps).
- [ ] **5. Proactive push on work-order ingest** — new WO for equipment X
      auto-attaches similar failures, lessons learned, permits, draft JSA.
- [ ] **6. Live metrics dashboard** — in-app benchmark panel (accuracy,
      time-to-answer, abstention) instead of only `docs/BENCHMARK.md`.

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
4. When in doubt about scope: **polishbeats features** from Day 3 onward.
