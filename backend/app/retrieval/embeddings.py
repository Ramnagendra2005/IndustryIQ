"""Embedding provider abstraction, mirroring the llm.py / persistence.py pattern.

Two providers behind one interface:

  * GeminiEmbedder — real transformer embeddings (gemini-embedding-001) with
                     asymmetric task types (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY),
                     which is what makes similar-meaning / paraphrase queries
                     actually land on the right passages.
  * StaticEmbedder — model2vec static embeddings (torch-free, offline). Weaker
                     semantics but zero network; the air-gapped fallback.

Document vectors are cached on disk keyed by content hash, so the corpus is
embedded once per model — restarts and per-upload index rebuilds only pay for
genuinely new chunks.
"""
from __future__ import annotations

import hashlib
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np

from .. import config


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(norms, 1e-8, None)


class BaseEmbedder:
    name = "base"
    live = False
    # Minimum absolute query→corpus cosine for a query to count as on-topic
    # (the out-of-corpus gate in graphrag.py). Calibrated per provider because
    # different models produce cosines in different ranges.
    relevance_min_cosine = 0.33

    def embed_docs(self, texts: List[str]) -> np.ndarray:
        """Row-normalised matrix of document/passage embeddings."""
        raise NotImplementedError

    def embed_query(self, text: str) -> np.ndarray:
        """Single normalised query vector (same space as embed_docs)."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Offline provider — model2vec static embeddings
# --------------------------------------------------------------------------- #
# One StaticModel per model name, shared across all engines/indexes — with one
# engine per industry, per-instance loading would duplicate the model N times.
_STATIC_MODEL_CACHE: dict = {}
_STATIC_LOCK = threading.Lock()


class StaticEmbedder(BaseEmbedder):
    name = "static-model2vec"
    live = False
    # Measured over the benchmark questions vs 10 off-topic ones: on-topic
    # queries score >= 0.386 max cosine against this corpus, off-topic <= 0.283.
    relevance_min_cosine = 0.33

    def __init__(self, model_name: Optional[str] = None) -> None:
        self._model_name = model_name or config.EMBED_MODEL
        self._model = None

    def _load(self):
        if self._model is None:
            with _STATIC_LOCK:
                if self._model_name not in _STATIC_MODEL_CACHE:
                    from model2vec import StaticModel
                    _STATIC_MODEL_CACHE[self._model_name] = StaticModel.from_pretrained(self._model_name)
            self._model = _STATIC_MODEL_CACHE[self._model_name]
        return self._model

    def embed_docs(self, texts: List[str]) -> np.ndarray:
        return _normalize(np.asarray(self._load().encode(texts), dtype=np.float32))

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_docs([text])[0]


# --------------------------------------------------------------------------- #
# Live provider — Gemini embeddings with a content-hash disk cache
# --------------------------------------------------------------------------- #
class GeminiEmbedder(BaseEmbedder):
    name = "gemini-embedding"
    live = True
    _BATCH = 100  # embed_content batch limit

    def __init__(self) -> None:
        from google import genai  # lazy so static mode needs no network stack

        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model = config.GEMINI_EMBED_MODEL
        self._dim = config.EMBED_DIM
        self.relevance_min_cosine = config.EMBED_RELEVANCE_MIN
        self._cache_lock = threading.Lock()
        slug = self._model.replace("/", "-") + f"-{self._dim}"
        self._cache_path = config.DATA_DIR / "emb_cache" / f"{slug}.npz"
        self._cache: dict[str, np.ndarray] = self._load_cache()

    # -- disk cache -------------------------------------------------------- #
    def _load_cache(self) -> dict[str, np.ndarray]:
        try:
            if self._cache_path.exists():
                with np.load(self._cache_path) as z:
                    return {k: z[k] for k in z.files}
        except Exception as exc:
            print(f"[embed] cache load failed ({exc}) — starting empty")
        return {}

    def _save_cache(self) -> None:
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._cache_path.with_suffix(".tmp.npz")
            np.savez_compressed(tmp, **self._cache)
            tmp.replace(self._cache_path)
        except Exception as exc:  # cache is an optimisation, never a failure
            print(f"[embed] cache save failed ({exc}) — continuing uncached")

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # -- API --------------------------------------------------------------- #
    def _api_embed(self, texts: List[str], task_type: str) -> np.ndarray:
        from google.genai import types

        vecs: list = []
        for i in range(0, len(texts), self._BATCH):
            resp = self._client.models.embed_content(
                model=self._model,
                contents=texts[i:i + self._BATCH],
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._dim,
                ),
            )
            vecs.extend(e.values for e in resp.embeddings)
        return _normalize(np.asarray(vecs, dtype=np.float32))

    def embed_docs(self, texts: List[str]) -> np.ndarray:
        with self._cache_lock:
            missing = [t for t in texts if self._key(t) not in self._cache]
            if missing:
                fresh = self._api_embed(missing, "RETRIEVAL_DOCUMENT")
                for t, v in zip(missing, fresh):
                    self._cache[self._key(t)] = v
                self._save_cache()
                print(f"[embed] embedded {len(missing)} new chunk(s) via {self._model} "
                      f"({len(texts) - len(missing)} from cache)")
            return np.stack([self._cache[self._key(t)] for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        # Queries are not cached: they're one API call and rarely repeat verbatim.
        return self._api_embed([text], "RETRIEVAL_QUERY")[0]


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_INSTANCE: Optional[BaseEmbedder] = None
_FACTORY_LOCK = threading.Lock()


def get_embedder() -> BaseEmbedder:
    """Shared live embedder (or static when no key / forced static)."""
    global _INSTANCE
    if _INSTANCE is None:
        with _FACTORY_LOCK:
            if _INSTANCE is None:
                if config.EMBED_PROVIDER == "live":
                    try:
                        _INSTANCE = GeminiEmbedder()
                    except Exception as exc:
                        print(f"[embed] gemini init failed ({exc}); using static embeddings")
                        _INSTANCE = StaticEmbedder()
                else:
                    _INSTANCE = StaticEmbedder()
    return _INSTANCE


def get_static_embedder() -> StaticEmbedder:
    """The offline embedder, always available — used as the query-time fallback
    matrix even when the live provider is active."""
    return StaticEmbedder()
