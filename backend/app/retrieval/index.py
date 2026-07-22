"""Hybrid lexical + semantic retrieval index over document passages.

BM25 (rank_bm25) for exact-term/tag matching + dense embeddings for semantic
matching (Gemini transformer embeddings when live, model2vec static offline —
see embeddings.py). Scores are min-max normalised and fused. This is the
'vector' half of GraphRAG; graph traversal is layered on top in graphrag.py.

When the live provider is active the index keeps TWO passage matrices: the
Gemini one (primary) and the static one (nearly free to build). Query and
passage vectors must come from the same model for cosine to mean anything, so
if a live query embed fails mid-request we drop to the static matrix for that
query instead of mixing spaces or losing semantic search entirely.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from ..schemas import Document
from .embeddings import BaseEmbedder, get_embedder, get_static_embedder


def _tokenize(text: str) -> List[str]:
    # Keep equipment tags like P-101 intact, lowercase everything else.
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())


def _chunk(text: str, size: int = 340, overlap: int = 60) -> List[str]:
    words = text.split()
    if len(words) <= size:
        return [text.strip()] if text.strip() else []
    chunks = []
    step = size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


@dataclass
class Passage:
    doc_id: str
    title: str
    doc_type: str
    date: Optional[str]
    text: str


class HybridIndex:
    def __init__(self, embed_model: Optional[str] = None) -> None:
        self.passages: List[Passage] = []
        self._bm25: Optional[BM25Okapi] = None
        self._embeds_live: Optional[np.ndarray] = None
        self._embeds_static: Optional[np.ndarray] = None
        self._embedder: Optional[BaseEmbedder] = None
        self._static: Optional[BaseEmbedder] = None
        self._embed_model_name = embed_model  # static model override

    # ------------------------------------------------------------------ #
    def _providers(self) -> Tuple[BaseEmbedder, BaseEmbedder]:
        """(primary, static-fallback). When the primary IS static, they're one."""
        if self._embedder is None:
            if self._embed_model_name:
                from .embeddings import StaticEmbedder
                self._embedder = StaticEmbedder(self._embed_model_name)
            else:
                self._embedder = get_embedder()
            self._static = self._embedder if not self._embedder.live else get_static_embedder()
        return self._embedder, self._static

    def build(self, documents: List[Document]) -> None:
        # Build into locals and swap at the end, so a search() running
        # concurrently (e.g. during a live ingest) never sees a half-built index.
        passages: List[Passage] = []
        for d in documents:
            for chunk in _chunk(d.text) or [d.title]:
                passages.append(Passage(d.id, d.title, d.doc_type.value
                                        if hasattr(d.doc_type, "value") else str(d.doc_type),
                                        d.date, chunk))
        if not passages:
            self.passages = []
            return
        tokenized = [_tokenize(p.text) for p in passages]
        bm25 = BM25Okapi(tokenized)
        embedder, static = self._providers()
        texts = [p.text for p in passages]
        embeds_static = static.embed_docs(texts)
        embeds_live: Optional[np.ndarray] = None
        if embedder.live:
            try:
                embeds_live = embedder.embed_docs(texts)
            except Exception as exc:
                print(f"[index] live embedding build failed ({exc}); "
                      "semantic search degrades to static embeddings")
        self.passages, self._bm25 = passages, bm25
        self._embeds_live, self._embeds_static = embeds_live, embeds_static

    # ------------------------------------------------------------------ #
    @staticmethod
    def _minmax(a: np.ndarray) -> np.ndarray:
        lo, hi = float(a.min()), float(a.max())
        if hi - lo < 1e-9:
            return np.zeros_like(a)
        return (a - lo) / (hi - lo)

    def _query_vec(self, query: str, embeds_live: Optional[np.ndarray],
                   embeds_static: Optional[np.ndarray]
                   ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[BaseEmbedder]]:
        """(query_vector, passage_matrix, provider) in a single embedding space."""
        embedder, static = self._providers()
        if embeds_live is not None:
            try:
                return embedder.embed_query(query), embeds_live, embedder
            except Exception as exc:
                print(f"[index] live query embed failed ({exc}); using static embeddings")
        if embeds_static is None:
            return None, None, None
        return static.embed_query(query), embeds_static, static

    def max_cosine(self, query: str) -> Tuple[float, float]:
        """(best absolute cosine of the query to any passage, on-topic threshold).

        Unlike search() scores (min-max normalised per query, so the top hit is
        always 1.0), the cosine is comparable across queries — used to detect
        out-of-corpus questions before answering. The threshold comes with it
        because it's provider-specific and the provider is resolved per query
        (a live failure falls back to static, whose calibration differs).
        """
        qv, embeds, provider = self._query_vec(query, self._embeds_live, self._embeds_static)
        if qv is None or embeds is None:
            return 0.0, 0.0
        return float((embeds @ qv).max()), provider.relevance_min_cosine

    def search(self, query: str, k: int = 6,
               alpha: Optional[float] = None) -> List[tuple[Passage, float]]:
        """Return top-k (passage, fused_score). alpha weights semantic vs lexical;
        default leans on semantics harder when the live embedder answered."""
        # snapshot so a concurrent rebuild can't mismatch passages vs scores
        passages, bm25 = self.passages, self._bm25
        embeds_live, embeds_static = self._embeds_live, self._embeds_static
        if not passages or bm25 is None:
            return []
        bm = np.array(bm25.get_scores(_tokenize(query)))
        qv, embeds, provider = self._query_vec(query, embeds_live, embeds_static)
        if qv is None or embeds is None:
            order = np.argsort(-bm)[:k]
            return [(passages[i], float(bm[i])) for i in order]
        if alpha is None:
            alpha = 0.65 if provider.live else 0.5
        sem = embeds @ qv
        fused = alpha * self._minmax(sem) + (1 - alpha) * self._minmax(bm)
        order = np.argsort(-fused)[:k]
        return [(passages[i], float(fused[i])) for i in order]
