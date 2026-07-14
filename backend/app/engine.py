"""IndustryIQ engine — orchestrates the graph, index, LLM and agents.

Holds the singleton application state and exposes the high-level operations the
API surface needs: bootstrap the base corpus, answer queries, run compliance,
ingest new documents live, and serve graph/document views.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from . import config
from .agents.compliance import run_compliance
from .agents.copilot import run_copilot
from .graph.store import KnowledgeGraph
from .ingestion.parsers import parse_upload
from .llm import get_llm
from .retrieval.index import HybridIndex
from .schemas import ComplianceReport, Document, Extraction, QueryResponse

# make backend/scripts importable for the authored corpus
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class Engine:
    def __init__(self) -> None:
        self.kg = KnowledgeGraph()
        self.index = HybridIndex()
        self.llm = get_llm()
        self._ready = False

    # ------------------------------------------------------------------ #
    def bootstrap(self) -> None:
        """Build the base knowledge graph + index from the authored corpus.

        The base corpus uses the authored ground-truth extractions (instant,
        free, deterministic) — this represents the plant's already-ingested
        history. NEW documents uploaded at runtime go through the live LLM
        extractor via `ingest_upload`.
        """
        import corpus_data  # authored single-source-of-truth

        for d in corpus_data.DOCS:
            doc = Document(
                id=d["id"], title=d["title"], doc_type=d["doc_type"],
                date=d.get("date"), unit=d.get("unit"), text=d["text"],
                is_image=d.get("is_image", False),
            )
            extraction = Extraction.model_validate(d["extraction"])
            self.kg.ingest_extraction(doc, extraction)

        self.index.build(self.kg.documents())
        self._ready = True

    # ------------------------------------------------------------------ #
    def status(self) -> dict:
        s = config.status()
        s.update({"ready": self._ready, "graph": self.kg.stats(),
                  "llm_provider": self.llm.name})
        return s

    def answer(self, question: str, mode: str = "copilot") -> QueryResponse:
        return run_copilot(self.kg, self.index, self.llm, question, mode)

    def compliance(self, scope: str = "Unit CDU-1 charge pumps") -> ComplianceReport:
        return run_compliance(self.kg, self.index, scope)

    def graph_view(self, focus: Optional[str] = None, radius: int = 2) -> dict:
        focus_list = [f.strip() for f in focus.split(",")] if focus else None
        return self.kg.to_viz(focus_list, radius)

    def documents(self) -> list[dict]:
        out = []
        for d in self.kg.documents():
            out.append({
                "id": d.id, "title": d.title,
                "doc_type": d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type),
                "date": d.date, "unit": d.unit, "is_image": d.is_image,
                "preview": d.text[:180].strip(),
            })
        return out

    def document(self, doc_id: str) -> Optional[dict]:
        d = self.kg.get_document(doc_id)
        if not d:
            return None
        return d.model_dump()

    # ------------------------------------------------------------------ #
    def ingest_upload(self, filename: str, content: bytes) -> dict:
        """Parse + extract + fold a newly uploaded document into the graph live."""
        doc, (kind, payload) = parse_upload(filename, content)
        if kind == "image":
            image_bytes, media_type = payload
            extraction = self.llm.extract_image(image_bytes, media_type,
                                                 doc_hint=f"{doc.id} P&ID/scanned form")
        else:
            extraction = self.llm.extract(payload, doc_hint=doc.id)

        before = self.kg.stats()
        self.kg.ingest_extraction(doc, extraction)
        self.index.build(self.kg.documents())
        after = self.kg.stats()

        return {
            "document": {
                "id": doc.id, "title": doc.title,
                "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
                "date": doc.date, "is_image": doc.is_image,
            },
            "extraction": extraction.model_dump(),
            "added_entities": after["entities"] - before["entities"],
            "added_relationships": after["relationships"] - before["relationships"],
            "provider": self.llm.name,
        }


_ENGINE: Optional[Engine] = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine()
        _ENGINE.bootstrap()
    return _ENGINE
