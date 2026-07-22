# IndustryIQ — Unified Asset & Operations Brain

## AI-Powered Industrial Knowledge Intelligence

**Hackathon Submission Document**

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [Key Features & Wow Moments](#3-key-features--wow-moments)
4. [System Architecture](#4-system-architecture)
5. [GraphRAG Pipeline — The Core Differentiator](#5-graphrag-pipeline--the-core-differentiator)
6. [Industrial Ontology & Knowledge Graph](#6-industrial-ontology--knowledge-graph)
7. [Agent System](#7-agent-system)
8. [Trust Layer — Contradiction & Staleness Detection](#8-trust-layer--contradiction--staleness-detection)
9. [Universal Document Ingestion](#9-universal-document-ingestion)
10. [Interactive P&ID & Entity Dossiers](#10-interactive-pid--entity-dossiers)
11. [Voice-First Multilingual Field Mode](#11-voice-first-multilingual-field-mode)
12. [Multi-Tenant Architecture](#12-multi-tenant-architecture)
13. [Dual-Mode LLM Abstraction](#13-dual-mode-llm-abstraction)
14. [Frontend & User Experience](#14-frontend--user-experience)
15. [Benchmark Results](#15-benchmark-results)
16. [Tech Stack & Justification](#16-tech-stack--justification)
17. [Scalability Path](#17-scalability-path)
18. [Business Impact & Market Opportunity](#18-business-impact--market-opportunity)
19. [Repository Structure](#19-repository-structure)
20. [How to Run](#20-how-to-run)
21. [Future Roadmap](#21-future-roadmap)

---

## 1. Problem Statement

### The Knowledge Fragmentation Crisis in Industry

Asset-intensive industries — refineries, power plants, petrochemical complexes, manufacturing facilities — face a critical operational challenge that costs billions annually and, more importantly, risks lives.

**The numbers tell the story:**

| Metric | Value | Source |
|--------|-------|--------|
| Disconnected document systems per large plant | **7–12** | Industry surveys |
| Working day spent searching for existing information | **~35%** | McKinsey 2024 |
| Unplanned downtime caused by knowledge fragmentation | **18–22%** | BIS (India) |
| Experienced engineers retiring within a decade | **~25%** | Industry estimates |

A typical industrial plant's knowledge is scattered across:
- **P&ID drawings** (Piping & Instrumentation Diagrams)
- **Work order histories** (maintenance management systems)
- **Inspection reports** (vibration surveys, thickness readings)
- **OEM manuals** (Original Equipment Manufacturer specifications)
- **Incident reports** (root cause analyses, lessons learned)
- **Standard Operating Procedures** (SOPs)
- **Regulatory documents** (Factory Act, OISD standards, ISO codes)
- **Emails and memos** (reliability reviews, shift handover notes)
- **Spreadsheets** (equipment registers, calibration logs)

### Why Existing Solutions Fail

Traditional enterprise search, document management systems, and even modern vector-RAG chatbots all fail at the same point: **they retrieve documents that match the query, but cannot connect information across documents.** The most valuable industrial insights — root causes, cross-asset failure patterns, compliance gaps — live in the **links between** documents, not in any single document.

**Example:** When pump P-101 trips repeatedly on vibration, the root cause isn't in any one document. It emerges only when you connect:
- Three work orders showing repeat bearing distress (symptom)
- A vibration survey showing a misalignment signature (diagnostic)
- The OEM manual saying repeat bearing failures indicate external causes (knowledge)
- A year-old incident on the identical sister pump P-102 that failed from soft-foot misalignment (precedent)

No keyword search, no vector search, and no single engineer's memory can make this connection. **IndustryIQ can.**

---

## 2. Solution Overview

**IndustryIQ** ingests the heterogeneous documents that run a plant and fuses them into **one queryable knowledge graph + AI copilot** that connects the dots no single engineer can.

### Three Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                        IndustryIQ                               │
│                                                                 │
│   ┌─────────────┐   ┌──────────────┐   ┌───────────────────┐   │
│   │  GraphRAG    │   │  Compliance  │   │  Universal Live   │   │
│   │  Copilot &   │   │  & Regulatory│   │  Ingestion        │   │
│   │  RCA Engine  │   │  Intelligence│   │                   │   │
│   └─────────────┘   └──────────────┘   └───────────────────┘   │
│                                                                 │
│   ┌─────────────┐   ┌──────────────┐   ┌───────────────────┐   │
│   │  Trust Layer │   │  Interactive │   │  Voice-First      │   │
│   │  Contradiction│  │  P&ID with   │   │  Multilingual     │   │
│   │  Detection   │   │  Dossiers    │   │  Field Mode       │   │
│   └─────────────┘   └──────────────┘   └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**What makes IndustryIQ technically different:** Most AI teams ship plain vector-RAG (retrieve passages by similarity, feed to LLM). IndustryIQ implements **GraphRAG** — vector/lexical retrieval *fused with knowledge-graph traversal* — so it surfaces cross-document links (sister-pump failures, shared root causes) that share **no query keywords** and would never be retrieved by embeddings alone.

---

## 3. Key Features & Wow Moments

### Wow Moment #1: Root-Cause Analysis That Connects the Dots

**Ask:** *"Why is pump P-101 vibrating and tripping?"*

**In under 1 second**, IndustryIQ:
1. Traverses its knowledge graph
2. Connects a live symptom → 3 work orders → an inspection vibration signature → the OEM trip limit → a year-old catastrophic failure on the identical sister pump P-102
3. Returns: **Root cause = coupling misalignment / soft-foot (NOT a bad bearing)**
4. Provides: recommended corrective action, citations to every source document, a confidence score, and a visible graph evidence trail

**The killer insight:** The connection to sister pump P-102 shares **zero keywords** with the question. Plain vector search never finds it. GraphRAG does — via the `SIBLING_OF` edge in the knowledge graph.

### Wow Moment #2: Compliance & Regulatory Intelligence

IndustryIQ auto-maps regulatory requirements against actual equipment state:
- **Factory Act 1948 Sec 21 BREACH** — coupling guard removed in a March work order and never reinstated (discovered by cross-reading a work order AND a reliability email)
- **OISD-116 Clause 5.4 AT RISK** — vibration survey cadence gap (January–May with only one survey on file)
- Auto-generated **audit-ready evidence pack** per requirement

### Wow Moment #3: Universal Live Ingestion

Drop any PDF / scanned P&ID / spreadsheet / email and watch Gemini extract entities + relationships and fold them into the knowledge graph **live**, on any device. The brain grows with every document.

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (React + Vite + Tailwind)                                        │
│                                                                            │
│  Engineer Dashboard (desktop)              Field Copilot (mobile-responsive)│
│  • Copilot / RCA chat                      • Chat-first, big touch targets  │
│  • Live knowledge-graph viz (force-dir.)   • Same GraphRAG answers on phone │
│  • Document browser (all formats)          • Voice input/output (7 langs)   │
│  • Compliance evidence panel               • Offline dossier cache          │
│  • Live ingestion panel                                                     │
│  • Interactive P&ID with entity dossiers                                    │
│  • Trust layer visualization                                                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ REST (/api/*)
┌───────────────────────────────────▼─────────────────────────────────────────┐
│ BACKEND  (FastAPI · Python)              Engine (per-tenant orchestrator)    │
│                                                                             │
│  ┌────────── 1. INGESTION ────────────┐                                     │
│  │ Parsers: PDF · Image/P&ID (vision) │                                     │
│  │          CSV/XLSX · Email · Text    │                                     │
│  └──────────────┬─────────────────────┘                                     │
│                 ▼                                                            │
│  ┌────────── 2. EXTRACTION (LLM) ─────────────────────────────────┐         │
│  │  LiveGemini : Gemini structured-output + vision → entities +    │         │
│  │               relationships                                     │         │
│  │  SeedMock   : deterministic authored ground-truth (offline)     │         │
│  └──────────────┬──────────────────────────────────────────────────┘         │
│        ┌────────┴────────┐                                                  │
│        ▼                 ▼                                                  │
│  ┌─ 3a. KNOWLEDGE ──┐  ┌─ 3b. HYBRID INDEX ─┐                              │
│  │    GRAPH          │  │ BM25 (lexical)      │                              │
│  │ NetworkX DiGraph  │  │ + model2vec embeds  │                              │
│  │ Industrial ontol. │  │ (torch-free, static)│                              │
│  │ Entity resolution │  └────────┬───────────┘                              │
│  │ Typed edges, paths│           │                                           │
│  └────────┬──────────┘           │                                           │
│           └──────► 4. GraphRAG FUSION ◄──┘                                  │
│                         │                                                    │
│                         ▼                                                    │
│  ┌────────── 5. AGENTS ─────────────────────────────────────────┐           │
│  │ Copilot    : grounded answer + confidence + citations         │           │
│  │ RCA        : connect failure evidence → root cause + action   │           │
│  │ Compliance : reg checklist × corpus → gaps + evidence pack    │           │
│  │ Trust      : staleness + contradiction detection              │           │
│  │ Dossier    : full entity profile (history, connections, gaps)  │           │
│  └───────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌────────── 6. PERSISTENCE (optional) ──────────────────────────┐          │
│  │ Supabase PostgREST: documents, extractions, query history     │          │
│  │ Circuit-breaker pattern: never a point of failure             │          │
│  └───────────────────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Document arrives** (PDF, image, spreadsheet, email, text) → parsers extract raw content
2. **LLM extraction** (Gemini 2.5 Flash structured output / vision) → entities + relationships
3. **Knowledge graph grows** — entities resolved, aliases merged, typed edges created
4. **Hybrid index built** — BM25 (lexical) + model2vec (semantic) for retrieval
5. **Query arrives** → GraphRAG retrieves relevant context (vector seeds + graph expansion)
6. **Agent answers** — grounded generation with citations, confidence, evidence trail
7. **Trust layer annotates** — staleness + conflicts flagged per answer

---

## 5. GraphRAG Pipeline — The Core Differentiator

This is what separates IndustryIQ from every other RAG system. Here's the 5-step pipeline:

### Step 1: Vector + Lexical Seeds
The `HybridIndex` fuses two retrieval signals:
- **BM25** (rank-bm25): exact equipment-tag matching (e.g., "P-101" matches precisely)
- **Static Embeddings** (model2vec, torch-free): semantic matching (synonyms, paraphrases)

Scores are min-max normalized and blended with a 0.6/0.4 weight split.

### Step 2: Focus-Entity Resolution
Equipment tags in the query (regex pattern `[A-Za-z]{1,3}-\d{2,4}`) + equipment entities in the seed documents are resolved to canonical graph nodes, with alias merging (e.g., "Pump P-101", "CDU-1 charge pump A", "P-101" all resolve to the same node).

### Step 3: Graph Expansion (The Key Innovation)
The neighborhood of each focus entity is walked along typed edges to pull in documents that share **no query keywords**:
- `P-101 —SIBLING_OF→ P-102` pulls in P-102's incident report
- `P-101 —GOVERNED_BY→ Factory Act` pulls in the regulatory requirement
- `P-101 —HAS_FAILURE→ misalignment` connects to the failure mode

This is what enables the "sister pump P-102 reveal" — the most impressive moment in the demo.

### Step 4: Context + Evidence Assembly
Seed and graph-linked documents are bundled with `[DOC:id]` tags. The shortest paths connecting the focus entities become the visible "evidence trail" rendered as amber-highlighted edges on the graph visualization.

### Step 5: Grounded Generation
The copilot/RCA agent answers over the assembled context, citing documents inline. Confidence is scored from:
- **Breadth** (number of unique source documents)
- **Corroboration** (how many docs the answer actually cites)
- **Graph bonus** (evidence trail present)
- **Focus bonus** (named entities resolved)

### Out-of-Corpus Gate
An absolute cosine-similarity threshold (calibrated at 0.60) ensures off-topic questions return empty results instead of hallucinated answers. **10/10 adversarial off-topic questions correctly refused** with zero citations and confidence ≤ 0.1.

---

## 6. Industrial Ontology & Knowledge Graph

### Entity Types (10 types)

| Entity Type | Description | Example |
|---|---|---|
| Equipment | Pumps, exchangers, columns, valves | P-101, E-204, C-301 |
| ProcessParameter | Vibration, temperature, pressure setpoints | Alarm 4.5 mm/s, Trip 7.1 mm/s |
| FailureMode | Bearing wear, seal leak, cavitation, misalignment | High vibration, soft foot |
| Person | Operators, engineers, inspectors | K. Rao (vibration analyst) |
| Regulation | Statutes, standards, codes | Factory Act 1948 Sec 21 |
| Procedure | SOPs, maintenance procedures | SOP-CDU-07 |
| Document | Source document reference nodes | WO-2478, INS-088 |
| Date | Significant events and timestamps | 2024-03-15 |
| Location | Plant units, areas, sections | Unit CDU-1 |
| Part | Physical components | Bearing, mechanical seal, impeller |

### Relationship Types (12 types)

| Relationship | Meaning | Why It Matters |
|---|---|---|
| `CONNECTED_TO` | Equipment ↔ Equipment (P&ID flow) | Process flow understanding |
| `HAS_FAILURE` | Equipment → FailureMode | Failure pattern tracking |
| `HAS_PARAMETER` | Equipment → ProcessParameter | Performance monitoring |
| `MAINTAINED_BY` | Equipment → Person | Accountability |
| `GOVERNED_BY` | Equipment/Procedure → Regulation | Compliance mapping |
| `DOCUMENTED_IN` | Entity → Document | Source traceability |
| `SIBLING_OF` | Equipment ↔ Equipment (identical) | **Cross-asset RCA** (the key differentiator) |
| `HAS_PART` | Equipment → Part | Component-level analysis |
| `PROCEDURE_FOR` | Procedure → Equipment | Maintenance guidance |
| `OCCURRED_ON` | Event/Failure → Date | Temporal analysis |
| `LOCATED_IN` | Equipment → Location | Spatial context |
| `MENTIONS` | Document → Entity (generic fallback) | Universal linkage |

### Graph Statistics (Demo Corpus)

| Metric | Value |
|---|---|
| Total entities | **40** |
| Total relationships | **45** |
| Documents ingested | **11** |
| Entity types used | **9** |
| Relationship types used | **10** |

### Entity Resolution
The graph implements alias merging: when an LLM extraction produces "Pump P-101", "CDU-1 charge pump A", or just "P-101", all resolve to the same canonical node. This is critical for industrial data where the same asset is referenced by different names across document types.

---

## 7. Agent System

IndustryIQ has five specialized agents, each designed for a specific industrial use case:

### 7.1 Copilot Agent (`copilot.py`)
- **Purpose:** Answer operational and maintenance questions with cited evidence
- **Input:** Natural language question + mode (copilot/RCA) + language
- **Pipeline:** GraphRAG retrieval → context assembly → Gemini generation → confidence scoring → citation filtering
- **Output:** Answer + confidence score + citations + graph evidence trail + elapsed time

### 7.2 RCA (Root-Cause Analysis) Agent
- Uses the same pipeline as the Copilot but with a specialized system prompt that steers toward:
  - Connecting failure evidence across documents
  - Stating a single most likely root cause
  - Preferring systemic causes over symptoms (e.g., misalignment over "bad bearing")
  - Providing evidence trail and recommended corrective action with SOP reference

### 7.3 Compliance Agent (`compliance.py`)
- **Purpose:** Map regulatory requirements against actual equipment state
- **How it works:**
  1. Maintains a checklist of regulatory requirements (Factory Act, OISD-116, ISO 10816)
  2. For each requirement, retrieves relevant evidence from the corpus via BM25 search
  3. Runs a deterministic evaluator function against the evidence text
  4. Classifies each requirement as: **GAP** | **AT RISK** | **MET**
  5. Auto-assembles an evidence pack (citations + snippets) per requirement
  6. Computes an overall readiness score (0..1)
- **Output:** Audit-ready compliance report with gaps, met requirements, evidence docs, and readiness score

### 7.4 Trust Agent (`trust.py`)
- **Purpose:** Detect contradictions and staleness in the document corpus
- **Two detection modes:**
  - **Staleness:** Freshness score (0..1) per document, decaying by doc-type half-life against the corpus clock
  - **Conflicts:** Generic regex/graph scanners for numeric disagreements, acceptance violations, guard status contradictions, stale drawings
- **Per-answer annotation:** Every copilot answer carries trust metadata (worst-source freshness + warnings when cited docs are conflicted/stale)

### 7.5 Dossier Agent (`dossier.py`)
- **Purpose:** Build a complete profile for any entity (typically equipment)
- **Output:** EntityDossier with connections (upstream, downstream, siblings), failure modes, parts, parameters, people, regulations, procedures, document history, compliance gaps, and active conflicts

---

## 8. Trust Layer — Contradiction & Staleness Detection

In industry, a confidently wrong answer sourced from a stale or contradicted document is **worse than no answer**. The Trust Layer is IndustryIQ's answer to this critical problem.

### Freshness Model

Every document gets a freshness score (0..1) that decays exponentially by a doc-type-specific half-life:

| Document Type | Half-Life | Rationale |
|---|---|---|
| Work Order | 240 days | Describes point-in-time state |
| Inspection Report | 180 days | OISD-116 wants surveys every 3 months |
| Email | 150 days | Operational context ages quickly |
| P&ID | ~4 years | Must be re-verified after modifications |
| SOP | ~3 years | Follows review cycle |
| OEM Manual | ~11 years | Reference material, slow to change |
| Incident Report | **Evergreen** | Lessons learned never expire |
| Regulatory Document | **Evergreen** | Statutes stay in force until superseded |

Time is measured against the **corpus clock** (the newest evidence date in the plant), making the scoring deterministic and independent of wall-clock time.

### Conflict Detectors

| Detector | What It Catches | Example |
|---|---|---|
| Numeric Setpoint | Different documents state different values for the same safety setpoint | OEM says trip 7.1 mm/s, work order says 7.0 mm/s |
| Acceptance Violation | A closed work order breaches the SOP's acceptance limit | SOP says "do not accept > 4.5 mm/s", WO-2502 closed at 5.8 mm/s |
| Guard Status | SOP/regulation requires guarding, plant records say it's off | Factory Act requires guarding, WO-2478 removed it, email confirms not reinstated |
| Stale Drawing | A P&ID pre-dates newer maintenance activity on the same unit | 2019 P&ID with 4 later work orders/incidents |

### Per-Answer Trust Annotation

Every copilot answer now carries an `AnswerTrust` object:
- `freshness`: Worst freshness score among cited sources
- `stale_docs`: List of stale documents cited
- `warnings`: Up to 4 trust warnings (stale sources, known conflicts)

The frontend renders these as an amber "TRUST CHECK" hazard placard when warnings are present.

---

## 9. Universal Document Ingestion

IndustryIQ accepts any document format an industrial plant uses:

| Format | Parser | Extraction Method |
|---|---|---|
| **PDF** | pypdf → text extraction | Gemini structured output |
| **Images** (PNG/JPG/WebP) | Raw bytes | **Gemini Vision** — digitises P&IDs and scanned forms without OCR/Tesseract |
| **Spreadsheets** (CSV/XLSX) | pandas + openpyxl → text | Gemini structured output |
| **Email** (.eml) | Python email parser → text | Gemini structured output |
| **Text** (TXT/MD) | Direct read | Gemini structured output |

### Ingestion Pipeline

1. **Upload validation:** File type, size (≤10 MB), non-empty, non-duplicate
2. **Parsing:** Format-specific parser extracts raw text or image bytes
3. **LLM Extraction:** Gemini extracts entities + relationships using the industrial ontology schema
4. **Graph Integration:** Entities resolved, aliases merged, edges created, graph grows live
5. **Index Rebuild:** BM25 + semantic index rebuilt to include new content
6. **Persistence:** Document + extraction saved to Supabase (if configured)
7. **Cache Invalidation:** Trust and compliance caches cleared for lazy recomputation

### For P&ID Images
When a P&ID image is uploaded:
- Gemini Vision extracts entities and relationships from the drawing
- A second Gemini call attempts to **localize every symbol** on the image (bounding boxes)
- If successful, the P&ID becomes **clickable** — tap any equipment symbol to see its full dossier

---

## 10. Interactive P&ID & Entity Dossiers

### Interactive P&ID
- Uploaded P&ID drawings become navigable overlays
- Equipment symbols are clickable, linked to knowledge graph nodes
- Health status coloring: green (OK) / amber (watch) / red (alert) — driven by compliance gaps and conflicts
- Vector diagrams (from authored geometry) and image overlays (from uploaded photos) supported

### Entity Dossier
Clicking any equipment symbol (or searching by name) opens a full dossier:
- **Connections:** Upstream equipment, downstream equipment, siblings
- **Failure Modes:** Known failures linked to this asset
- **Parts:** Physical components (bearing, seal, impeller)
- **Parameters:** Measured values and setpoints
- **People:** Engineers and operators who've maintained it
- **Regulations:** Applicable standards and codes
- **Procedures:** Relevant SOPs
- **Document History:** Every document mentioning this entity, with freshness scores
- **Compliance Gaps:** Active regulatory gaps for this specific entity
- **Conflicts:** Active contradictions involving this entity

---

## 11. Voice-First Multilingual Field Mode

Built for the field technician on the plant floor, not just the engineer at a desk.

### Voice Input/Output
- **Voice queries** via Web Speech API (microphone button, live transcript, pulsing listening state)
- **Spoken answers** via speechSynthesis
- **Hands-free loop** in field mode: answer spoken → mic re-opens automatically

### 7 Languages Supported
| Code | Language | Script |
|------|----------|--------|
| en | English | Latin |
| hi | Hindi | Devanagari |
| te | Telugu | Telugu |
| ta | Tamil | Tamil |
| kn | Kannada | Kannada |
| mr | Marathi | Devanagari |
| bn | Bengali | Bengali |

**Safety-critical invariant:** Equipment tags (P-101), instrument tags (VT-101), document citations ([DOC:WO-2478]), numeric values, and units (mm/s) are **never translated or transliterated** — they stay verbatim in every language.

### Offline Dossier
- Every answer + full text of cited documents cached in localStorage
- When connectivity drops, the copilot serves the best-matching cached answer
- Displayed with an "OFFLINE DOSSIER" badge + banner

---

## 12. Multi-Tenant Architecture

Every user belongs to an **industry** (their company), and each industry has its own:
- Private knowledge graph
- Document corpus
- Query history
- Compliance state

**Isolation:** One tenant can never see another's data. Every API request is scoped to the caller's industry via a signed Bearer token (HMAC-signed, PBKDF2-hashed passwords).

### Account System
| Action | Description |
|---|---|
| **Demo login** | `demo@industryiq.app` / `demo123` — opens the pre-seeded Demo Refinery |
| **New industry** | Create account → New industry → fresh empty graph + invite code |
| **Join industry** | Create account → Enter invite code from your admin |

Accounts follow the same fallback contract as everything else: they work in memory (no database needed) and are mirrored to Supabase when it's reachable.

---

## 13. Dual-Mode LLM Abstraction

A key design principle: **the demo never breaks, and the app is genuinely useful offline.**

| Provider | When Used | Network Required | Implementation |
|---|---|---|---|
| `LiveGemini` | Live ingestion + generative answers | Yes | Gemini 2.5 Flash structured output + vision |
| `SeedMock` | Offline demo / air-gapped industrial sites | **No** | Deterministic authored ground-truth |

### How It Works
- `LLM_MODE=auto` selects live when a Gemini API key is present, else seed
- If a live API call fails mid-request, the engine automatically falls back to seed mode with a note appended
- Nothing outside `llm.py` ever imports `google.genai` — perfect abstraction

### Why This Matters
- **Demo reliability:** The demo works on stage with Wi-Fi off — always
- **Product feature:** Offline capability is a genuine need for secure/air-gapped industrial sites
- **Graceful degradation:** Network issues never crash the app; they just reduce to offline mode

---

## 14. Frontend & User Experience

### Design Philosophy: "Refinery Control Room After Dark"
Bloomberg-terminal density, mission-control calm. Instrument panels, not SaaS cards. The UI reads as **"the plant's collective memory — it sees what you can't."**

### Color System (OKLCH)
| Token | Color | Usage |
|---|---|---|
| `--iq-paper` | Dark navy (15% lightness) | Page background |
| `--iq-accent` | Amber | Brand/action hue (≤5% of viewport) |
| `--iq-data` | Teal | Telemetry & data only |
| `--iq-alarm` | Red | Danger states only, never décor |
| `--iq-ok` | Green | Confirmed-good only |

### Typography
- **Display:** Space Grotesk (600/700 weight)
- **Body:** Space Grotesk (400 weight)
- **Monospace:** JetBrains Mono — every data value, ID, timestamp, reading (engineers read mono)

### Application Tabs
1. **Chat (Copilot/RCA)** — Natural language questions with rich answer rendering, clickable citations, evidence trail, trust annotations, and proactive alert cards
2. **Knowledge Graph** — Force-directed graph visualization (react-force-graph-2d) with evidence trail highlighting, node clicking, and focus/radius controls
3. **Documents** — Document browser with type, date, unit metadata, and full-text viewing
4. **Compliance** — Regulatory gap cards with severity, regulation clause, and clickable evidence-doc chips
5. **Ingest** — Drag-and-drop document upload with live extraction progress
6. **P&ID** — Interactive piping and instrumentation diagrams with clickable equipment symbols
7. **Trust** — Corpus health dashboard with freshness scores and conflict list

### Special UI Elements
- **Proactive alert card** on chat empty state: "P-101 at 5.8 mm/s trending toward the 7.1 mm/s trip limit — P-102 failed under the same signature"
- **Evidence trail animation** on the graph: amber edges with animated particles + halo rings
- **Mode badge:** "● Live Gemini" / "● Offline demo" so viewers always know the mode
- **Boot sequence:** POST self-test animation (mono boot lines, [  ]→[✓] checks) — one theatrical moment

---

## 15. Benchmark Results

### Measured Results — Seed/Offline Mode

Executed via `POST /api/query` against the 11-document base corpus:

| # | Question | Mode | Doc Recall | Fact Recall | Confidence | Latency | Graph Paths |
|---|----------|------|-----------|-------------|------------|---------|-------------|
| Q1 | Why is pump P-101 vibrating and tripping? | RCA | 5/5 | 4/4 | 0.98 | 15 ms | ✅ |
| Q2 | Maintenance history of P-101? | Copilot | 4/4 | 1/1 | 0.98 | 3 ms | ✅ |
| Q3 | Has this failure happened on a similar pump? | Copilot | 1/1 | 4/4 | 0.80 | 2 ms | ✅ |
| Q4 | OEM vibration alarm and trip limits for P-101? | Copilot | 1/1 | 2/2 | 0.90 | 5 ms | ✅ |
| Q5 | Equipment downstream of P-101? | Copilot | 1/1 | 2/2 | 0.70 | 7 ms | ✅ |
| Q6 | OEM guidance on repeated bearing failures? | Copilot | 1/1 | 2/2 | 0.90 | 4 ms | ✅ |
| Q7 | P-101 compliant with Factory Act guarding? | Compliance | 2/2 | 1/1 | 0.90 | 11 ms | ✅ |
| Q8 | OISD-116 vibration-survey cadence? | Compliance | 2/2 | 1/1 | 0.90 | 4 ms | ✅ |

### Aggregate Metrics

| Metric | Result |
|---|---|
| **Source-document citation recall** | **17/17 (100%)** |
| **Key-fact recall** | **17/17 (100%)** |
| **Answer latency** | **Median 4 ms, max 15 ms** (vs ~20 min manual search baseline) |
| **Out-of-corpus honesty** (10 adversarial off-topic questions) | **10/10 refused** — zero citations, confidence ≤ 0.1 |
| **Cross-document graph linkage** (P-102 via SIBLING_OF) | **Hit** ✅ |
| **Compliance detection** | 2 gaps + 2 met controls (as expected) |
| **Readiness score** | 0.62 |

### Compliance Detection Detail

| Requirement | Status | Severity |
|---|---|---|
| Factory Act 1948 Sec 21 — coupling guard | **GAP** 🔴 | High |
| OISD-116 Clause 5.4 — vibration survey cadence | **AT RISK** 🟡 | High |
| OISD-116 Clause 5.7 — OEM alarm/trip settings | **MET** 🟢 | Medium |
| OISD-116 Clause 6.2 / ISO 10816 — survey records | **MET** 🟢 | Medium |

---

## 16. Tech Stack & Justification

| Concern | Choice | Why |
|---|---|---|
| **LLM** | Google Gemini 2.5 Flash | Strong entity/relationship extraction + reasoning; structured output; free tier available |
| **Vision / OCR** | Gemini Vision | Digitises P&IDs / scanned forms without Tesseract or external OCR |
| **Knowledge Graph** | NetworkX (Neo4j-ready API) | Zero infra dependencies for the demo; clean upgrade path to Neo4j/Memgraph |
| **Embeddings** | model2vec (potion-base-8M) | Torch-free, fast, runs anywhere including air-gapped sites |
| **Lexical Search** | rank-bm25 | Exact equipment-tag matching (critical for industrial queries) |
| **Backend** | FastAPI (Python) | Fast async API framework; Pydantic data validation |
| **Frontend** | React + Vite + Tailwind | Component-based UI with hot reload; responsive design |
| **Graph Viz** | react-force-graph-2d | Interactive force-directed graph rendering in the browser |
| **Fonts** | Space Grotesk + JetBrains Mono | Industrial aesthetic; monospace for data readability |
| **Animations** | Framer Motion | Smooth UI transitions; evidence trail animations |
| **Persistence** | Supabase (optional) | PostgREST-based; circuit-breaker pattern; never required to boot |
| **PDF Parsing** | pypdf | Lightweight, pure-Python |
| **Spreadsheets** | pandas + openpyxl | Industry-standard tabular data handling |

### Zero-Infra Principle
The entire application runs with **no external services required** in seed mode:
- No database server
- No vector database
- No Redis/message queue
- No Elasticsearch
- No GPU
- No Docker

Just Python + Node.js → `run.bat` → working application.

---

## 17. Scalability Path

| Component | Current (Demo) | Production Upgrade | Agent Changes Needed |
|---|---|---|---|
| **Graph Store** | NetworkX (in-memory) | Neo4j / Memgraph | **Zero** — API is deliberately Neo4j-shaped |
| **Vector Search** | model2vec + numpy | pgvector / Qdrant / Pinecone | Swap `HybridIndex` implementation |
| **Lexical Search** | rank-bm25 (in-memory) | Elasticsearch / OpenSearch | Swap BM25 backend |
| **Ingestion** | Synchronous, per-file | Async batch pipeline + Celery | Add async wrapper |
| **Multi-Tenant** | Per-industry Engine dict | Sharded by site/unit behind gateway | Gateway layer |
| **Persistence** | Supabase (PostgREST) | PostgreSQL + object store | Swap store implementation |
| **Parsers** | PDF, image, CSV, email, text | Add CAD/DWG, historian/OPC-UA, QMS | New parser module per format |

**Key design decision:** The `KnowledgeGraph` API was written to match Neo4j's interface (typed nodes, typed edges, shortest-path queries). Swapping the backend is a one-file change with zero agent modifications.

---

## 18. Business Impact & Market Opportunity

### Quantified Impact

| Metric | Before IndustryIQ | After IndustryIQ | Improvement |
|---|---|---|---|
| Time to answer an RCA question | ~20 minutes (4+ systems) | **< 1 second** | **~1200x faster** |
| Cross-asset failure pattern discovery | Manual, rare, depends on individual memory | **Automatic via SIBLING_OF traversal** | New capability |
| Compliance gap detection | Days (pre-audit manual review) | **Seconds (automated, continuous)** | **Orders of magnitude** |
| Knowledge retention when experts retire | Lost with the person | **Captured in the knowledge graph** | Structural improvement |

### Target Market
- **Oil & gas refineries** (7,000+ globally)
- **Power plants** (thermal, nuclear)
- **Petrochemical complexes**
- **Pharmaceutical manufacturing**
- **Large-scale manufacturing**
- **Mining and minerals**

### Revenue Model (Future)
- SaaS per-plant subscription
- Tiered by corpus size and number of users
- Premium features: OPC-UA historian integration, advanced compliance packs, multi-site federation

---

## 19. Repository Structure

```
IndustryIQ/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── engine.py            # Core engine — orchestrates graph, index, LLM, agents
│   │   ├── config.py            # Central configuration (env vars, paths, model selection)
│   │   ├── schemas.py           # Domain ontology + all API models (Pydantic)
│   │   ├── llm.py               # Dual-mode LLM abstraction (LiveGemini / SeedMock)
│   │   ├── persistence.py       # Supabase persistence layer (optional)
│   │   ├── auth.py              # Multi-tenant authentication (PBKDF2 + HMAC tokens)
│   │   ├── pid.py               # Interactive P&ID builder
│   │   ├── graph/
│   │   │   └── store.py         # Knowledge graph (NetworkX MultiDiGraph)
│   │   ├── retrieval/
│   │   │   ├── graphrag.py      # GraphRAG fusion pipeline
│   │   │   ├── index.py         # Hybrid BM25 + semantic index
│   │   │   └── embeddings.py    # Embedding providers (static + Gemini live)
│   │   └── agents/
│   │       ├── copilot.py       # Copilot & RCA agent
│   │       ├── compliance.py    # Compliance & regulatory intelligence
│   │       ├── trust.py         # Trust layer (staleness + contradiction detection)
│   │       └── dossier.py       # Entity dossier builder
│   ├── scripts/
│   │   ├── corpus_data.py       # Authored 11-document seed corpus (single source of truth)
│   │   ├── build_seed.py        # Generate offline seed extractions + answers
│   │   └── generate_corpus.py   # Generate readable corpus files
│   ├── data/                    # Generated corpus + seed data
│   ├── requirements.txt         # Python dependencies (14 packages)
│   └── supabase_schema.sql      # Database schema for persistence
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main application shell (7 tabs)
│   │   ├── api.js               # API client (fetch wrapper + auth)
│   │   ├── main.jsx             # React entry point
│   │   ├── tokens.css           # Design tokens (OKLCH color system)
│   │   ├── index.css            # Global styles
│   │   ├── fx.jsx               # Animations (Framer Motion)
│   │   ├── icons.jsx            # SVG icon components
│   │   ├── voice.js             # Voice input/output (Web Speech API)
│   │   ├── dossier.js           # Offline dossier cache
│   │   ├── lib.jsx              # Shared UI components
│   │   └── components/          # Feature-specific components
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── DEMO_SCRIPT.md           # 3-minute demo script
│   ├── PITCH_DECK.md            # 10-slide pitch deck outline
│   └── BENCHMARK.md             # Domain-expert benchmark results
├── README.md                    # Quick start guide
├── ARCHITECTURE.md              # Full architecture documentation
├── ROADMAP.md                   # Development roadmap
├── design.md                    # UI/UX design system specification
├── run.bat / run.sh             # One-command launcher (Windows / Unix)
└── .env                         # Environment configuration (not in git)
```

---

## 20. How to Run

### Prerequisites
- Python 3.11+ (tested on 3.14)
- Node.js 18+
- ~500 MB disk for the embedding model

### One-Command Launch (Windows)
```batch
run.bat              # Build everything and serve on http://localhost:8000
run.bat dev          # Backend on :8000 + Vite dev server on :5173 (hot reload)
```

### Manual Setup
```bash
# Backend
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt
.venv/Scripts/python backend/scripts/build_seed.py
.venv/Scripts/python backend/scripts/generate_corpus.py
.venv/Scripts/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run build    # Production (served by backend at /)
# or
npm run dev      # Development (hot reload at :5173)
```

### Demo Login
- **Email:** `demo@industryiq.app`
- **Password:** `demo123`

### Try These Questions
1. *"Why is pump P-101 vibrating and tripping?"* (RCA mode — the headline demo)
2. *"Has this kind of failure happened on a similar pump before?"*
3. *"What are the OEM vibration alarm and trip limits for P-101?"*
4. Open the **Compliance** tab → see the Factory Act guard gap
5. Open the **Ingest** tab → drop a document and watch it enter the graph

---

## 21. Future Roadmap

| Feature | Description | Status |
|---|---|---|
| ✅ GraphRAG Copilot + RCA | Core Q&A with graph traversal | **Complete** |
| ✅ Compliance Intelligence | Regulatory gap detection + evidence packs | **Complete** |
| ✅ Universal Ingestion | PDF, image, spreadsheet, email, text | **Complete** |
| ✅ Trust Layer | Staleness + contradiction detection | **Complete** |
| ✅ Voice + Multilingual | 7 languages, voice I/O, hands-free mode | **Complete** |
| ✅ Interactive P&ID | Clickable drawings with entity dossiers | **Complete** |
| ✅ Multi-Tenant | Per-industry isolation with auth | **Complete** |
| ✅ Proactive Alerts | Trending alerts on chat empty state | **Complete** |
| ✅ Offline Dossier | localStorage-cached answers for field use | **Complete** |
| 🔲 Tacit Knowledge Capture | "Exit Interview AI" for retiring experts | Planned |
| 🔲 Live Metrics Dashboard | In-app benchmark panel | Planned |
| 🔲 Neo4j Migration | Production graph database | Planned |
| 🔲 OPC-UA Integration | Real-time historian data | Planned |

---

## Summary

**IndustryIQ** transforms fragmented industrial knowledge into a unified, queryable, continuously-updated operations brain. Its GraphRAG architecture — fusing vector retrieval with knowledge-graph traversal — surfaces cross-document insights that no search system can find, while the Trust Layer ensures every answer is traceable and trustworthy.

**The system is not a prototype.** It is a fully functional, multi-tenant, offline-capable, multilingual application with measurable performance: **100% citation recall, 100% fact recall, median 4ms latency, and zero hallucinations on adversarial testing.**

The organisations that solve knowledge fragmentation first get a structural advantage in how they operate, maintain, and improve their assets. IndustryIQ is that brain.

---

*Built for the AI Industrial Knowledge Intelligence Hackathon*
*GitHub: [github.com/Ramnagendra2005/IndustryIQ](https://github.com/Ramnagendra2005/IndustryIQ)*
