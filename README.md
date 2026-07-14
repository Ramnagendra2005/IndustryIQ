# IndustryIQ — Unified Asset & Operations Brain

**AI-powered Industrial Knowledge Intelligence.** IndustryIQ ingests the heterogeneous
documents that run a plant — P&IDs, work orders, inspection reports, OEM manuals,
incident histories, SOPs, regulations, emails — and fuses them into **one queryable
knowledge graph + copilot** that connects the dots no single engineer can.

> A refinery operates across 7–12 disconnected document systems. Professionals in
> asset-intensive industries spend ~35% of their day *searching* for information that
> already exists. IndustryIQ turns that fragmented corpus into a single brain that
> answers operational, maintenance, RCA and compliance questions **in seconds, with
> sources**, on desktop or on a field technician's phone.

---

## ✨ What it does (the three wow moments)

1. **GraphRAG Copilot & Root-Cause Analysis** — ask *"Why does pump P-101 keep
   tripping on vibration?"* and IndustryIQ traverses its knowledge graph to connect a
   live symptom → 3 work orders → an inspection vibration signature → the OEM trip
   limit → **a year-old catastrophic failure on the identical sister pump P-102** —
   and returns a root cause (misalignment / soft-foot, *not* a bad bearing) with a
   recommended action, **citations, a confidence score, and a graph evidence trail**.

2. **Compliance & Regulatory Intelligence** — auto-maps Factory Act, OISD-116 and
   ISO 10816 requirements against the actual document corpus and equipment state,
   flags gaps (e.g. *coupling guard removed and never reinstated → Factory Act Sec 21
   breach*), and assembles an **audit-ready evidence pack** per requirement.

3. **Universal Live Ingestion** — drop any PDF / scanned P&ID / spreadsheet / email
   and watch Claude extract entities + relationships and fold them into the graph
   **live**, on any device.

---

## 🏗️ Architecture (one glance)

```
 React + Vite + Tailwind  ── Engineer dashboard + mobile Field copilot
        │  REST
 FastAPI ─ Engine ─┬─ Ingestion (PDF·image·xlsx·email·text  → Claude vision/structured extraction)
                   ├─ Knowledge Graph (NetworkX, industrial ontology, entity resolution, path queries)
                   ├─ Hybrid Retrieval (BM25 + torch-free embeddings)  ─┐
                   ├─ GraphRAG fusion (vector seeds + graph traversal) ─┘
                   └─ Agents: Copilot · RCA · Compliance-gap
```

Full detail + scalability story: [`ARCHITECTURE.md`](ARCHITECTURE.md).

**Why it's technically different:** most teams ship plain vector-RAG. IndustryIQ does
**GraphRAG** — vector/lexical retrieval *fused with knowledge-graph traversal* — so it
surfaces cross-document links (sister-pump failures, shared root causes) that share **no
query keywords** and would never be retrieved by embeddings alone.

---

## 🚀 Quickstart

### 0. Prerequisites
- Python 3.11+ (tested on 3.14) · Node 18+ · ~500 MB disk for the embedding model.

### 1. Backend
```bash
# from the repo root
python3 -m venv .venv         # if the system lacks pip: see "Bootstrapping pip" below
.venv/bin/pip install -r backend/requirements.txt

# build the deterministic offline seed + corpus files
.venv/bin/python backend/scripts/build_seed.py
.venv/bin/python backend/scripts/generate_corpus.py

# run the API (serves the built frontend at / too)
.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run build          # production build served by the backend at http://localhost:8000
# ── or for hot-reload dev (proxies /api to :8000): ──
npm run dev            # http://localhost:5173
```

Open **http://localhost:8000** (prod) or **http://localhost:5173** (dev).

### 3. (Optional) Live Claude mode
IndustryIQ runs fully offline by default (deterministic seed). To enable **live**
document ingestion + generative copilot answers, copy `.env.example` → `.env` and add
your own Anthropic API key (`sk-ant-...` from https://console.anthropic.com):

```bash
cp .env.example .env
# set ANTHROPIC_API_KEY=sk-ant-...   (LLM_MODE=auto flips to live automatically)
```

> **Offline / air-gapped by design.** Because the app runs with zero external calls in
> seed mode, the demo is bulletproof on stage — and it doubles as the "works air-gapped
> for secure industrial sites" pitch. Live mode is a drop-in upgrade, not a rewrite.

---

## 🧭 Try these
- `Why is pump P-101 vibrating and tripping?` *(RCA mode — the headline demo)*
- `Has this kind of failure happened on a similar pump before?`
- `What are the OEM vibration alarm and trip limits for P-101?`
- Open the **Compliance** tab → see the Factory Act guard gap + OISD cadence risk.
- Open the **Ingest** tab → drop a `.txt`/`.pdf` and watch it enter the graph.

## 📊 Evaluation & benchmark
Domain-expert benchmark questions and the metrics they map to (entity-extraction
accuracy, answer quality, graph linkage, time-to-answer, compliance detection) are in
[`docs/BENCHMARK.md`](docs/BENCHMARK.md).

## 📁 Repo layout
```
backend/app/          FastAPI app, engine, graph, retrieval, agents, llm abstraction
backend/scripts/      corpus_data.py (authored corpus) + seed/corpus generators
backend/data/         corpus/ (readable docs)  seed/ (offline extractions + answers)
frontend/src/         React app (Chat, GraphView, Documents, Compliance, Ingest)
docs/                 demo script, pitch deck outline, benchmark
ARCHITECTURE.md       architecture diagram + scalability
```

## Bootstrapping pip (if `python3 -m venv` has no pip)
Some minimal distros ship Python without `ensurepip`:
```bash
python3 -m venv .venv
curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
.venv/bin/python /tmp/get-pip.py
```
