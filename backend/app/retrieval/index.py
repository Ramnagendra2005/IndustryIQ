"""Hybrid lexical + semantic retrieval index over document passages.

BM25 (rank_bm25) for exact-term/tag matching + static embeddings (model2vec,
torch-free) for semantic matching. Scores are min-max normalised and fused.
This is the 'vector' half of GraphRAG; graph traversal is layered on top in
graphrag.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
from rank_bm25 import BM25Okapi

from ..schemas import Document


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


# One StaticModel per model name, shared by every index instance — with one
# engine per industry, per-instance loading would duplicate the model N times.
_MODEL_CACHE: dict = {}


class HybridIndex:
    def __init__(self, embed_model: Optional[str] = None) -> None:
        self.passages: List[Passage] = []
        self._bm25: Optional[BM25Okapi] = None
        self._embeds: Optional[np.ndarray] = None
        self._model = None
        self._embed_model_name = embed_model

    # ------------------------------------------------------------------ #
    def _load_model(self):
        if self._model is None:
            from model2vec import StaticModel

            from .. import config
            name = self._embed_model_name or config.EMBED_MODEL
            if name not in _MODEL_CACHE:
                _MODEL_CACHE[name] = StaticModel.from_pretrained(name)
            self._model = _MODEL_CACHE[name]
        return self._model

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
        model = self._load_model()
        embeds = model.encode([p.text for p in passages])
        # normalise rows for cosine via dot product
        norms = np.linalg.norm(embeds, axis=1, keepdims=True)
        embeds = embeds / np.clip(norms, 1e-8, None)
        self.passages, self._bm25, self._embeds = passages, bm25, embeds

    # ------------------------------------------------------------------ #
    @staticmethod
    def _minmax(a: np.ndarray) -> np.ndarray:
        lo, hi = float(a.min()), float(a.max())
        if hi - lo < 1e-9:
            return np.zeros_like(a)
        return (a - lo) / (hi - lo)

    def max_cosine(self, query: str) -> float:
        """Best absolute semantic similarity of the query to any passage.

        Unlike search() scores (min-max normalised per query, so the top hit is
        always 1.0), this is comparable across queries — used to detect
        out-of-corpus questions before answering.
        """
        embeds = self._embeds
        if embeds is None:
            return 0.0
        qv = self._load_model().encode([query])[0]
        qv = qv / max(np.linalg.norm(qv), 1e-8)
        return float((embeds @ qv).max())

    def search(self, query: str, k: int = 6, alpha: float = 0.5) -> List[tuple[Passage, float]]:
        """Return top-k (passage, fused_score). alpha weights semantic vs lexical."""
        # snapshot so a concurrent rebuild can't mismatch passages vs scores
        passages, bm25, embeds = self.passages, self._bm25, self._embeds
        if not passages or bm25 is None or embeds is None:
            return []
        bm = np.array(bm25.get_scores(_tokenize(query)))
        qv = self._load_model().encode([query])[0]
        qv = qv / max(np.linalg.norm(qv), 1e-8)
        sem = embeds @ qv
        fused = alpha * self._minmax(sem) + (1 - alpha) * self._minmax(bm)
        order = np.argsort(-fused)[:k]
        return [(passages[i], float(fused[i])) for i in order]
