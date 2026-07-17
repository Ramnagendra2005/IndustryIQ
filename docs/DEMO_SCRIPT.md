# IndustryIQ — 3-Minute Demo Script

Goal: land two "wow" moments (cross-document RCA, compliance gap) and the mobile
angle, while name-dropping the metrics judges score. Keep the browser on
`http://localhost:8000`. Have the **RCA** mode pill pre-selected.

---

### 0:00 — The problem (15s, on the landing screen)
> "A large plant runs across 7 to 12 disconnected document systems. Engineers spend
> **a third of their day just searching** for information that already exists — and
> when a pump fails, no one person has seen the P&ID, the work-order history, the
> inspection reading, the OEM manual **and** the incident from a sister asset two years
> ago. That fragmentation drives ~1 in 5 unplanned downtime events."

Gesture to the header: *"IndustryIQ has already ingested 11 heterogeneous documents into
one knowledge graph — 40 entities, 45 relationships."*

### 0:15 — WOW #1: Root-Cause Analysis that connects the dots (60s)
Click the suggestion **"Why is pump P-101 vibrating and tripping?"** (RCA mode).

While it answers (note the **⚡ time-to-answer vs ~20 min manual** chip):
> "In under a second it did what a reliability engineer needs 20 minutes and four
> systems to do."

Read the punchline from the answer:
> "It concludes the root cause is **coupling misalignment / soft foot — not a bad
> bearing** — and it's *right*. Look how it got there:" → point at the **evidence trail**
> chips and the **citations**:
> - three work orders showing repeat bearing distress,
> - the May vibration survey with a misalignment signature,
> - the OEM manual saying repeat bearing life = external cause, don't just swap the bearing,
> - and the **killer link: the identical sister pump P-102 failed the same way in 2023 —
>   root cause soft foot** — retrieved via a graph edge, sharing *zero* keywords with the
>   question. **Plain vector search never finds that. GraphRAG does.**"

Click a citation chip (e.g. `INC-2023-14`) → the document opens. *"Every claim is
traceable to source."* Click a graph-path chip → jumps to the graph.

### 1:15 — The knowledge graph (25s)
On the **Knowledge Graph** tab, P-101 is highlighted at the centre.
> "This is the unified brain. P-101 wired to its sister P-102, to its failure modes,
> its parameters, the people who worked on it, and the regulations that govern it —
> built automatically from the documents. Click any node to pivot."

### 1:40 — WOW #2: Compliance & audit readiness (45s)
Click the **Compliance** tab.
> "Second agent: it maps Factory Act, OISD-116 and ISO 10816 against the *actual*
> equipment state and flags gaps **before** an auditor does."
Point at the red gap:
> "**Factory Act Section 21 breach** — the coupling guard was removed during the March
> work order and never reinstated; the pump is running unguarded. It found that by
> cross-reading a work order *and* a reliability email. And here's the auto-generated
> **evidence pack** for the audit." Point at the OISD cadence **at-risk** item.

### 2:25 — Live ingestion + mobile (25s)
Click **Ingest**, drop a document → *"watch Gemini extract entities and relationships
and fold them into the graph live."* Then toggle **📱 Field** in the header:
> "And it's built for the technician on the plant floor, not just the engineer at a
> desk — same brain, same citations, on a phone."

### 2:50 — Close (10s)
> "IndustryIQ: fragmented plant documents become one queryable, cited, continuously-
> updated operations brain — cutting time-to-answer from tens of minutes to seconds,
> and catching the safety and compliance gaps that hide between systems. And it runs
> **fully offline** for secure sites."

---

## Backup / Q&A ammo
- **"Is the corpus real?"** — synthetic but realistic and internally consistent; the
  pipeline is document-format-agnostic — point at the parsers and the live-ingest tab.
- **"Does it hallucinate?"** — answers are grounded in retrieved docs with inline
  citations + a confidence score; offline mode is fully deterministic.
- **"How does it scale?"** — see ARCHITECTURE.md §5: Neo4j-ready graph API, swappable
  vector DB, pluggable parsers, per-tenant engine.
- **"What's novel?"** — GraphRAG (graph traversal fused with retrieval) surfacing
  cross-asset links no keyword search can, plus agentic RCA + compliance on top.
