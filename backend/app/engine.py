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
from .agents.trust import annotate_answer, run_trust
from .graph.store import KnowledgeGraph
from .ingestion.parsers import parse_upload
from .llm import SeedMock, get_llm
from .persistence import get_store
from .retrieval.index import HybridIndex
from .schemas import ComplianceReport, Document, Extraction, QueryResponse, TrustReport

# make backend/scripts importable for the authored corpus
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


class Engine:
    """One engine per industry (tenant): its own graph, index and documents.

    The 'demo' industry boots with the authored seed corpus; every other
    industry starts empty and is built purely from its own uploads."""

    def __init__(self, industry_id: str = "demo") -> None:
        self.industry_id = industry_id
        self.kg = KnowledgeGraph()
        self.index = HybridIndex()
        self.llm = get_llm()
        self.store = get_store()
        self._ready = False
        self._ingest_lock = threading.Lock()
        self._seed_fallback: Optional[SeedMock] = None
        self._trust_cache: Optional[TrustReport] = None
        self._compliance_cache: Optional[ComplianceReport] = None
        # Interactive P&ID: raw image bytes + detected symbol geometry, keyed by
        # doc id, for uploaded drawings (the seed drawing is authored in pid.py).
        self._pid_images: dict[str, tuple[bytes, str]] = {}
        self._pid_geometry: dict[str, dict] = {}

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
        if self.industry_id == "demo":
            import corpus_data  # authored single-source-of-truth

            for d in corpus_data.DOCS:
                doc = Document(
                    id=d["id"], title=d["title"], doc_type=d["doc_type"],
                    date=d.get("date"), unit=d.get("unit"), text=d["text"],
                    is_image=d.get("is_image", False),
                )
                extraction = Extraction.model_validate(d["extraction"])
                self.kg.ingest_extraction(doc, extraction)

        self._restore_persisted()
        self.index.build(self.kg.documents())
        self._ready = True

    def _restore_persisted(self) -> None:
        """Fold previously-uploaded documents back in from the persistence store.

        Purely additive on top of the seed corpus: if the store is offline,
        empty, or half-broken, the app still boots with seed data alone.
        """
        try:
            rows = self.store.restore_documents(self.industry_id)
        except Exception as exc:  # store swallows its own errors; belt-and-braces
            print(f"[engine] persisted restore failed ({exc}); continuing with seed corpus")
            return
        restored = 0
        for row in rows:
            doc, extraction = row["document"], row["extraction"]
            if self.kg.get_document(doc.id):
                continue  # already in the seed corpus / duplicate row
            self.kg.ingest_extraction(doc, extraction)
            if row.get("image"):
                self._pid_images[doc.id] = row["image"]
            if row.get("pid_geometry"):
                self._pid_geometry[doc.id] = row["pid_geometry"]
            restored += 1
        if restored:
            print(f"[engine] restored {restored} persisted document(s) from {self.store.name}")

    # ------------------------------------------------------------------ #
    def status(self) -> dict:
        s = config.status()
        s.update({"ready": self._ready, "graph": self.kg.stats(),
                  "llm_provider": self.llm.name,
                  "industry_id": self.industry_id,
                  "persistence": self.store.status()})
        return s

    def answer(self, question: str, mode: str = "copilot", lang: str = "en") -> QueryResponse:
        try:
            resp = run_copilot(self.kg, self.index, self.llm, question, mode, lang)
        except Exception as exc:
            if not self.llm.live:
                raise
            print(f"[engine] live answer failed ({exc}); retrying in offline seed mode")
            resp = run_copilot(self.kg, self.index, self._fallback_llm(), question, mode, lang)
            resp.answer += "\n\n_(Live API unavailable — this answer was generated offline.)_"
        if resp.citations:
            resp.trust = annotate_answer(self.kg, resp.citations, self.trust())
        # store the conversation context (fire-and-forget; never blocks the answer)
        try:
            self.store.log_query(question, mode, lang, resp.answer,
                                 resp.confidence, self.llm.name,
                                 industry_id=self.industry_id)
        except Exception as exc:
            print(f"[engine] query log failed ({exc}) — answer unaffected")
        return resp

    def compliance(self, scope: str = "Unit CDU-1 charge pumps") -> ComplianceReport:
        return run_compliance(self.kg, self.index, scope)

    def compliance_cached(self) -> ComplianceReport:
        """Default-scope compliance report; cached until the corpus changes.
        Used by the P&ID health colouring and entity dossiers."""
        if self._compliance_cache is None:
            self._compliance_cache = run_compliance(self.kg, self.index)
        return self._compliance_cache

    def trust(self) -> TrustReport:
        """Corpus-wide trust report; cached until the corpus changes."""
        if self._trust_cache is None:
            self._trust_cache = run_trust(self.kg)
        return self._trust_cache

    def graph_view(self, focus: Optional[str] = None, radius: int = 2) -> dict:
        focus_list = [f.strip() for f in focus.split(",")] if focus else None
        return self.kg.to_viz(focus_list, radius)

    # ------------------------------------------------------------------ #
    # Interactive P&ID + entity dossiers
    # ------------------------------------------------------------------ #
    def has_pid_image(self, doc_id: str) -> bool:
        return doc_id in self._pid_images

    def pid_geometry(self, doc_id: str) -> Optional[dict]:
        return self._pid_geometry.get(doc_id)

    def pid_image(self, doc_id: str) -> Optional[tuple[bytes, str]]:
        return self._pid_images.get(doc_id)

    def pid_list(self) -> list[dict]:
        from .pid import list_diagrams
        return [s.model_dump() for s in list_diagrams(self)]

    def pid_diagram(self, doc_id: str) -> Optional[dict]:
        from .pid import build_diagram
        d = build_diagram(self, doc_id)
        return d.model_dump() if d else None

    def entity_dossier(self, name: str) -> dict:
        from .agents.dossier import build_dossier
        return build_dossier(self.kg, name, self.compliance_cached(),
                             self.trust()).model_dump()

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

        # For P&ID images: keep the bytes (to display) and try to localize every
        # symbol so the drawing becomes clickable. Failure is non-fatal — the
        # drawing still works via the equipment-tag rail fallback.
        pid_symbols: list = []
        if kind == "image":
            image_bytes, media_type = payload
            self._pid_images[doc.id] = (image_bytes, media_type)
            if self.llm.live:
                try:
                    pid_symbols = self.llm.locate_pid_symbols(image_bytes, media_type)
                except Exception as exc:
                    print(f"[engine] symbol localization failed ({exc})")
            if pid_symbols:
                self._pid_geometry[doc.id] = {"view": {"w": 1000, "h": 700},
                                              "symbols": pid_symbols, "connections": []}

        with self._ingest_lock:
            before = self.kg.stats()
            self.kg.ingest_extraction(doc, extraction)
            self.index.build(self.kg.documents())
            after = self.kg.stats()
            self._trust_cache = None       # corpus changed — recompute lazily
            self._compliance_cache = None

        # persist the upload so it survives restarts (non-fatal if the store is down)
        try:
            self.store.save_document(doc, extraction,
                                     pid_geometry=self._pid_geometry.get(doc.id),
                                     image=self._pid_images.get(doc.id),
                                     industry_id=self.industry_id)
        except Exception as exc:
            print(f"[engine] persist failed ({exc}) — document remains in memory")

        return {
            "document": {
                "id": doc.id, "title": doc.title,
                "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
                "date": doc.date, "is_image": doc.is_image,
            },
            "extraction": extraction.model_dump(),
            "added_entities": after["entities"] - before["entities"],
            "added_relationships": after["relationships"] - before["relationships"],
            "pid_symbols_located": len(pid_symbols),
            "provider": self.llm.name,
        }


_ENGINES: dict[str, Engine] = {}
_ENGINE_LOCK = threading.Lock()


def get_engine(industry_id: str = "demo") -> Engine:
    """Return the engine for an industry, building + bootstrapping it on first
    use. One tenant's graph is never visible to another. The embedding
    providers are shared across engines (see retrieval/embeddings.py)."""
    industry_id = industry_id or "demo"
    eng = _ENGINES.get(industry_id)
    if eng is None:
        with _ENGINE_LOCK:
            eng = _ENGINES.get(industry_id)
            if eng is None:
                eng = Engine(industry_id)
                eng.bootstrap()
                _ENGINES[industry_id] = eng
    return eng
