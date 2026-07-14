# IndustryIQ — Architecture

## 1. System diagram

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ FRONTEND  (React + Vite + Tailwind)                                                  │
│                                                                                      │
│  Engineer dashboard (desktop)                 Field copilot (mobile-responsive)      │
│  • Copilot / RCA chat                          • chat-first, big touch targets        │
│  • Live knowledge-graph viz (force-directed)   • same GraphRAG answers on a phone     │
│  • Document browser (all formats)              • compliance + explore tabs            │
│  • Compliance evidence panel                                                          │
│  • Live ingestion panel                                                               │
└───────────────────────────────────────┬─────────────────────────────────────────────┘
                                         │ REST (/api/*)
┌────────────────────────────────────────▼─────────────────────────────────────────────┐
│ BACKEND  (FastAPI · Python)                     Engine (singleton orchestrator)        │
│                                                                                        │
│  ┌────────────── 1. INGESTION ──────────────┐                                          │
│  │ parsers: PDF · image/P&ID · CSV/XLSX ·    │                                          │
│  │          email · text                     │                                          │
│  └───────────────────┬──────────────────────┘                                          │
│                      ▼                                                                  │
│  ┌────────────── 2. EXTRACTION (LLM abstraction) ─────────────────────────────┐        │
│  │  LiveClaude  : Claude structured-output + vision  → entities + relationships │        │
│  │  SeedMock    : deterministic authored ground-truth (offline / air-gapped)    │        │
│  └───────────────────┬─────────────────────────────────────────────────────────┘        │
│           ┌──────────┴──────────┐                                                       │
│           ▼                     ▼                                                       │
│  ┌── 3a. KNOWLEDGE GRAPH ──┐   ┌── 3b. HYBRID INDEX ──┐                                  │
│  │ NetworkX MultiDiGraph   │   │ BM25 (lexical)        │                                 │
│  │ industrial ontology     │   │ + model2vec embeds    │                                 │
│  │ entity resolution       │   │ (torch-free, static)  │                                 │
│  │ typed edges, path query │   └──────────┬───────────┘                                 │
│  └──────────┬──────────────┘              │                                             │
│             └────────► 4. GraphRAG fusion ◄┘   (vector seeds → focus entities →         │
│                              │                  graph expansion → context + citations   │
│                              ▼                  + connecting graph paths)                │
│  ┌────────────── 5. AGENTS ──────────────────────────────────────────────────┐         │
│  │ Copilot   : grounded answer + confidence + citations                        │         │
│  │ RCA       : connect failure evidence across docs → root cause + action      │         │
│  │ Compliance: reg checklist × corpus → gaps + auto evidence pack              │         │
│  └─────────────────────────────────────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

## 2. The GraphRAG pipeline (the differentiator)

Plain RAG retrieves passages that lexically/semantically match the query and stops there.
That structurally **cannot** surface the cross-document links that make industrial
knowledge valuable. IndustryIQ adds graph traversal:

1. **Vector + lexical seeds** — `HybridIndex` fuses BM25 (exact tag matches like `P-101`)
   and static embeddings (semantic matches), min-max normalised and blended.
2. **Focus-entity resolution** — equipment tags in the query + equipment in the seed docs
   are resolved to canonical graph nodes (with alias merging).
3. **Graph expansion** — the neighbourhood of each focus entity is walked to pull in
   documents that share *no query keywords* — e.g. the sister-pump P-102 incident report
   retrieved via the `P-101 —SIBLING_OF→ P-102` edge.
4. **Context + evidence assembly** — seed and graph-linked docs are bundled with
   `[DOC:id]` tags; the shortest paths connecting the focus entities become the visible
   "evidence trail".
5. **Grounded generation** — the copilot/RCA agent answers over that bundle, citing
   documents inline; confidence is scored from retrieval breadth, corroboration and
   graph support.

## 3. Industrial ontology

Entities: `Equipment, ProcessParameter, FailureMode, Person, Regulation, Procedure,
Document, Date, Location, Part`.
Relations: `CONNECTED_TO, HAS_FAILURE, HAS_PARAMETER, MAINTAINED_BY, GOVERNED_BY,
DOCUMENTED_IN, SIBLING_OF, HAS_PART, PROCEDURE_FOR, OCCURRED_ON, LOCATED_IN, MENTIONS`.

This small, opinionated schema is what turns documents into a graph you can *reason over*
(e.g. `SIBLING_OF` is what makes cross-pump RCA possible; `GOVERNED_BY` powers compliance).

## 4. Dual-mode LLM abstraction

Nothing outside `llm.py` imports `anthropic`. Two providers implement one interface:

| Provider    | Used for                              | Network | Notes                                   |
|-------------|---------------------------------------|---------|-----------------------------------------|
| `LiveClaude`| live ingestion + generative answers   | yes     | Claude structured output + vision       |
| `SeedMock`  | offline demo / air-gapped sites       | no      | deterministic authored ground-truth     |

`LLM_MODE=auto` selects live when an API key is present, else seed. This makes the demo
reliable *and* is a genuine product feature (offline capability for secure plants).

## 5. Scalability path (what we'd say to judges)

- **Graph store** — the `KnowledgeGraph` API is deliberately Neo4j-shaped (typed nodes,
  typed edges, shortest-path queries). Swap NetworkX → Neo4j/Memgraph for millions of
  nodes with zero agent changes.
- **Retrieval** — swap the in-memory `HybridIndex` for a vector DB (pgvector/Qdrant) +
  a BM25 service; the fusion logic is unchanged.
- **Ingestion** — parsers are pluggable per MIME type; add CAD/DWG, historian/OPC-UA, or
  QMS connectors as new parsers. Extraction is already an async-friendly batch step.
- **Multi-tenant** — the Engine is a per-plant singleton; shard by site/unit behind a
  gateway. Ontology is shared; graph + index are per-tenant.
- **Continuous update** — new documents fold into the graph incrementally
  (`ingest_upload`), so the brain stays current "at the point of need".

## 6. Tech choices & why

| Concern            | Choice                     | Why                                             |
|--------------------|----------------------------|-------------------------------------------------|
| LLM                | Claude (Sonnet/Opus)       | best entity/relationship extraction + reasoning |
| Vision / OCR       | Claude vision              | digitises P&IDs / scanned forms — no tesseract  |
| Graph              | NetworkX (Neo4j-ready)     | zero infra for the demo; clean upgrade path     |
| Embeddings         | model2vec (static)         | torch-free, fast, runs anywhere incl. air-gapped|
| Lexical            | rank-bm25                  | exact equipment-tag matching                    |
| API / UI           | FastAPI · React/Vite/Tail  | fast, clean, mobile-responsive                  |
```
