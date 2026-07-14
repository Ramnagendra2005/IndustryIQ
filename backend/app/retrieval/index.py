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
            self._model = StaticModel.from_pretrained(
                self._embed_model_name or config.EMBED_MODEL
            )
        return self._model

    def build(self, documents: List[Document]) -> None:
        self.passages = []
        for d in documents:
            for chunk in _chunk(d.text) or [d.title]:
                self.passages.append(Passage(d.id, d.title, d.doc_type.value
                                             if hasattr(d.doc_type, "value") else str(d.doc_type),
                                             d.date, chunk))
        if not self.passages:
            return
        tokenized = [_tokenize(p.text) for p in self.passages]
        self._bm25 = BM25Okapi(tokenized)
        model = self._load_model()
        self._embeds = model.encode([p.text for p in self.passages])
        # normalise rows for cosine via dot product
        norms = np.linalg.norm(self._embeds, axis=1, keepdims=True)
        self._embeds = self._embeds / np.clip(norms, 1e-8, None)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _minmax(a: np.ndarray) -> np.ndarray:
        lo, hi = float(a.min()), float(a.max())
        if hi - lo < 1e-9:
            return np.zeros_like(a)
        return (a - lo) / (hi - lo)

    def search(self, query: str, k: int = 6, alpha: float = 0.5) -> List[tuple[Passage, float]]:
        """Return top-k (passage, fused_score). alpha weights semantic vs lexical."""
        if not self.passages:
            return []
        bm = np.array(self._bm25.get_scores(_tokenize(query)))
        qv = self._load_model().encode([query])[0]
        qv = qv / max(np.linalg.norm(qv), 1e-8)
        sem = self._embeds @ qv
        fused = alpha * self._minmax(sem) + (1 - alpha) * self._minmax(bm)
        order = np.argsort(-fused)[:k]
        return [(self.passages[i], float(fused[i])) for i in order]
