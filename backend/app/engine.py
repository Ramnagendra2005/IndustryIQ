"""IndustryIQ engine — orchestrates the graph, index, LLM and agents.

Holds the singleton application state and exposes the high-level operations the
API surface needs: bootstrap the base corpus, answer queries, run compliance,
ingest new documents live, and serve graph/document views.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Optional

from . import config
from .agents.compliance import run_compliance
from .agents.copilot import run_copilot
from .graph.store import KnowledgeGraph
from .ingestion.parsers import parse_upload
from .llm import SeedMock, get_llm
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
        self._ingest_lock = threading.Lock()
        self._seed_fallback: Optional[SeedMock] = None

    def _fallback_llm(self) -> SeedMock:
        """Offline provider used when a live API call fails mid-request."""
        if self._seed_fallback is None:
            self._seed_fallback = SeedMock()
        return self._seed_fallback

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
        try:
            return run_copilot(self.kg, self.index, self.llm, question, mode)
        except Exception as exc:
            if not self.llm.live:
                raise
            print(f"[engine] live answer failed ({exc}); retrying in offline seed mode")
            resp = run_copilot(self.kg, self.index, self._fallback_llm(), question, mode)
            resp.answer += "\n\n_(Live API unavailable — this answer was generated offline.)_"
            return resp

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
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024
    SUPPORTED_EXTS = {"pdf", "txt", "md", "eml", "csv", "xlsx", "xls",
                      "png", "jpg", "jpeg", "gif", "webp"}

    def _validate_upload(self, filename: str, content: bytes) -> Optional[str]:
        """Return a user-facing error string, or None if the upload is acceptable."""
        if not content or not content.strip():
            return "The file is empty — nothing to ingest."
        if len(content) > self.MAX_UPLOAD_BYTES:
            return f"File is too large ({len(content) / 1e6:.1f} MB) — the limit is 10 MB."
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.SUPPORTED_EXTS:
            return (f"Unsupported file type '.{ext or filename}' — supported: "
                    "PDF, image (png/jpg), spreadsheet (csv/xlsx), email (eml), text (txt/md).")
        return None

    def ingest_upload(self, filename: str, content: bytes) -> dict:
        """Parse + extract + fold a newly uploaded document into the graph live."""
        err = self._validate_upload(filename, content)
        if err:
            return {"error": err}

        doc, (kind, payload) = parse_upload(filename, content)
        if self.kg.get_document(doc.id):
            return {"error": f"'{doc.id}' is already in the knowledge base — duplicate upload skipped."}

        try:
            if kind == "image":
                image_bytes, media_type = payload
                extraction = self.llm.extract_image(image_bytes, media_type,
                                                     doc_hint=f"{doc.id} P&ID/scanned form")
            else:
                extraction = self.llm.extract(payload, doc_hint=doc.id)
        except Exception as exc:
            if not self.llm.live:
                raise
            print(f"[engine] live extraction failed ({exc}); using offline extractor")
            if kind == "image":
                extraction = self._fallback_llm().extract_image(payload[0], payload[1], doc_hint=doc.id)
            else:
                extraction = self._fallback_llm().extract(payload, doc_hint=doc.id)

        with self._ingest_lock:
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
