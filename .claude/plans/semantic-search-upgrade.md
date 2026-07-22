# Semantic Search Upgrade: Gemini Embeddings + Offline Fallback

## Context

Semantic search already exists (`HybridIndex` in `backend/app/retrieval/index.py`: model2vec static embeddings + BM25, fused). But static embeddings are weak at synonym/paraphrase understanding — that's why "similar meaning" queries miss. Decision: upgrade to **Gemini transformer embeddings** (`gemini-embedding-001`) with **model2vec as automatic offline fallback**, keeping the **in-memory numpy** vector store, plus a **disk cache** so the corpus is never re-embedded.

## Changes

### 1. New: `backend/app/retrieval/embeddings.py` — embedder abstraction (mirrors `llm.py` pattern)

- `StaticEmbedder` — wraps the existing model2vec logic (moved from `HybridIndex._load_model`), keeps the shared `_MODEL_CACHE`. `relevance_min_cosine = 0.33` (current calibrated value).
- `GeminiEmbedder` — uses the existing `google-genai` client:
  - `embed_docs(texts)` → batched `embed_content` calls (batches of 100) with `task_type="RETRIEVAL_DOCUMENT"`, `output_dimensionality=768`.
  - `embed_query(text)` → `task_type="RETRIEVAL_QUERY"` (asymmetric task types are what make paraphrase matching accurate).
  - Own `relevance_min_cosine` calibrated during implementation (Gemini cosines sit in a different range than model2vec; I'll measure on-topic benchmark questions vs off-topic ones against the corpus and pick the separating threshold, same method as the existing 0.33).
- **Disk cache**: `backend/data/emb_cache/<model-slug>.npz` keyed by sha256(text). On build, only cache-misses hit the API; restarts and per-upload rebuilds re-embed only new chunks. Cache write failures are non-fatal.
- `get_embedder()` factory: live when `GEMINI_API_KEY` present (respecting new `IIQ_EMBED_PROVIDER=auto|live|static`), else static — same pattern as `get_llm()` / `get_store()`.

### 2. `backend/app/retrieval/index.py` — dual-matrix `HybridIndex`

- `build()` embeds passages with **both** matrices when live: Gemini matrix (primary) + static matrix (fallback — model2vec is nearly free). Same swap-at-end thread-safety pattern.
- `search()` / `max_cosine()`: embed the query with Gemini; **if the API call fails mid-query, fall back to the static matrix** (query and passage vectors must always come from the same model — never mix spaces). Fusion stays min-max + alpha; alpha raised to 0.65 when the live matrix is used (semantic signal is now trustworthy), 0.5 for static.
- Expose `relevance_min_cosine` from the active embedder so the out-of-corpus gate stays correct per provider.

### 3. `backend/app/retrieval/graphrag.py`

- Replace the hardcoded `RELEVANCE_MIN_COSINE = 0.33` with `self.index.relevance_min_cosine` (provider-aware).

### 4. `backend/app/config.py`

- Add `IIQ_EMBED_PROVIDER` (auto/live/static), `IIQ_GEMINI_EMBED_MODEL` (default `gemini-embedding-001`), `IIQ_EMBED_DIM` (default 768). Report the active embed provider in `status()` so the UI/status endpoint shows it.

### 5. `.env` — document the new vars (commented defaults).

No new dependencies (google-genai + model2vec already present). No schema/frontend changes.

## Verification

1. Boot backend; confirm status shows `embed_provider: gemini` and the cache file appears.
2. Paraphrase test — queries sharing no keywords with the corpus, e.g. "pump making strange noise" → must retrieve the P-101 vibration/bearing docs; "rules for factory safety" → REG docs.
3. Off-topic test — "best pizza in town" → still returns the empty-corpus answer (gate calibrated).
4. Kill network / unset key → verify automatic static fallback still answers.
5. Upload a doc → confirm only new chunks are embedded (cache hit count logged).
