# IndustryIQ — Pitch Deck Outline

10 slides, mapped to the judging rubric (Business Impact 25 · Technical Excellence 25 ·
Scalability 20 · User Experience 15 · Innovation 15). Speaker notes in *italics*.

---

### Slide 1 — Title
**IndustryIQ — The Unified Asset & Operations Brain**
AI-powered Industrial Knowledge Intelligence.
*One line: "Turn 7–12 disconnected document systems into one queryable, cited brain."*
Team · logo · one-line tagline.

### Slide 2 — The Problem (Business Impact)
- 35% of the working day lost to *searching* for existing information (McKinsey 2024).
- Avg. large Indian plant: **7–12 disconnected document systems**.
- Fragmentation → **18–22% of unplanned downtime** in Indian heavy industry (BIS).
- The **knowledge cliff**: ~25% of experienced engineers retire within a decade —
  undocumented know-how walks out the door.
*"This is a safety, quality and efficiency problem that compounds over time."*

### Slide 3 — The Insight
> Knowledge fragmentation isn't a file-management problem. The value is in the **links
> between documents** — links no single person can hold in their head. The winning
> system doesn't just *search* documents, it **reasons across them**.

### Slide 4 — Solution overview (UX)
Screenshot of the dashboard: copilot + live knowledge graph + citations + confidence.
Three capabilities: **RCA Copilot · Compliance Intelligence · Universal Live Ingestion**.
Built for **both** the desk engineer and the **field technician's phone**.

### Slide 5 — Live demo hook (Innovation + Business Impact)
The P-101 RCA moment on one slide:
`symptom → 3 work orders → inspection signature → OEM limit → sister-pump P-102 2023 failure`
→ **root cause: misalignment/soft-foot, not a bad bearing**, in **<1s vs ~20 min**.
*"The connection that solves it shares zero keywords with the question."*

### Slide 6 — How it works: GraphRAG (Technical Excellence)
The architecture diagram (ARCHITECTURE.md §1). Emphasise:
- Heterogeneous ingestion (PDF, **P&ID via vision**, spreadsheet, email).
- **Knowledge graph** with an industrial ontology + entity resolution.
- **GraphRAG** = vector/lexical retrieval **fused with graph traversal** (vs plain RAG).
- Grounded answers with citations, confidence, and a visible evidence trail.

### Slide 7 — Beyond Q&A: Agents (Technical Excellence + Business Impact)
- **RCA agent** — fuses work orders, inspections, OEM limits, incident history.
- **Compliance agent** — maps Factory Act / OISD-116 / ISO 10816 to equipment state,
  flags gaps, auto-builds evidence packs. *Show the Factory Act guard gap.*
- **Lessons-learned** — sister-asset failure patterns pushed to current operations.

### Slide 8 — Scalability (Scalability)
- Graph API is **Neo4j-ready**; retrieval swaps to a vector DB; parsers are pluggable
  (add historian/OPC-UA, CAD, QMS connectors).
- Per-tenant engine, shared ontology; incremental continuous updates.
- **Runs fully offline / air-gapped** — critical for secure industrial sites.

### Slide 9 — Impact & metrics (Business Impact)
- Time-to-answer: **tens of minutes → seconds** (measured, shown live).
- Cross-functional discovery: surfaces links across doc types no search finds.
- Compliance gaps caught **before** audit → fewer stoppages, safer plant.
- Captures retiring experts' knowledge as a durable, queryable graph.
- Benchmark set + metrics: `docs/BENCHMARK.md`.

### Slide 10 — Vision & ask
From CDU-1 charge pumps → whole-plant → enterprise brain across sites.
*"The organisations that solve knowledge fragmentation first get a structural advantage
in how they operate, maintain and improve their assets. IndustryIQ is that brain."*

---

## Deliverables checklist
- [x] Working prototype (this repo — offline demo runs with no key)
- [x] Architecture diagram (`ARCHITECTURE.md`)
- [x] Presentation deck (this outline → build slides)
- [ ] Demo video (record following `docs/DEMO_SCRIPT.md`)
