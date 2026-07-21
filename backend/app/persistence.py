"""Persistence abstraction layer.

Two stores behind one interface, mirroring the LLM layer in llm.py:

  * SupabaseStore — persists uploaded documents, their extractions, P&ID
                    image/geometry and query history to Supabase (PostgREST),
                    and restores them at boot so uploads survive restarts.
  * NullStore     — in-memory no-op. Used when SUPABASE_URL/KEY are absent,
                    so the app boots and demos exactly as before.

Persistence is an ENHANCEMENT layer, never a point of failure:

  * no new dependency — talks to Supabase's REST API via httpx (already here)
  * every call has a short timeout and swallows its own exceptions
  * a circuit breaker disables the store after repeated consecutive failures,
    so a network that dies mid-demo costs a few log lines, not the demo

The rest of the app never imports httpx/Supabase details directly — it goes
through `get_store()` so the two modes are fully swappable.
"""
from __future__ import annotations

import base64
import threading
from typing import Optional

from . import config
from .schemas import Document, Extraction

_TIMEOUT_S = 4.0          # per-request budget; boot restore + writes stay snappy
_MAX_FAILURES = 3         # consecutive failures before the breaker opens


# --------------------------------------------------------------------------- #
# Base interface (also the offline no-op)
# --------------------------------------------------------------------------- #
class NullStore:
    name = "memory"
    live = False

    def restore_documents(self, industry_id: str = "demo") -> list[dict]:
        """Rows for previously-uploaded documents of one industry:
        [{document, extraction, pid_geometry, image}]. Offline store has none."""
        return []

    def save_document(self, doc: Document, extraction: Extraction,
                      pid_geometry: Optional[dict] = None,
                      image: Optional[tuple[bytes, str]] = None,
                      industry_id: str = "demo") -> None:
        pass

    def log_query(self, question: str, mode: str, lang: str, answer: str,
                  confidence: float, provider: str,
                  industry_id: str = "demo") -> None:
        pass

    # -- auth mirror (industries + users survive restarts when live) -------- #
    def save_industry(self, row: dict) -> None:
        pass

    def save_user(self, row: dict) -> None:
        pass

    def load_industries(self) -> list[dict]:
        return []

    def load_users(self) -> list[dict]:
        return []

    def status(self) -> dict:
        return {"provider": self.name, "healthy": True}


# --------------------------------------------------------------------------- #
# Live provider — Supabase over PostgREST
# --------------------------------------------------------------------------- #
class SupabaseStore(NullStore):
    name = "supabase"
    live = True

    def __init__(self) -> None:
        import httpx  # imported lazily so memory mode needs nothing extra

        self._client = httpx.Client(
            base_url=f"{config.SUPABASE_URL}/rest/v1",
            headers={
                "apikey": config.SUPABASE_KEY,
                "Authorization": f"Bearer {config.SUPABASE_KEY}",
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT_S,
        )
        self._failures = 0
        self._down = False
        self._lock = threading.Lock()

    # -- circuit breaker --------------------------------------------------- #
    def _ok(self) -> None:
        with self._lock:
            self._failures = 0

    def _fail(self, op: str, exc: Exception) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= _MAX_FAILURES and not self._down:
                self._down = True
                print(f"[store] {self._failures} consecutive Supabase failures — "
                      "persistence disabled for this session (app continues in-memory)")
        print(f"[store] {op} failed ({exc}) — continuing without persistence")

    def _request(self, op: str, method: str, path: str, *,
                 params: Optional[dict] = None, payload=None,
                 prefer: Optional[str] = None):
        """One guarded REST call. Returns parsed JSON or None on any failure."""
        if self._down:
            return None
        headers = {"Prefer": prefer} if prefer else None
        try:
            resp = self._client.request(method, path, params=params,
                                        json=payload, headers=headers)
            resp.raise_for_status()
            self._ok()
            return resp.json() if resp.content else []
        except Exception as exc:
            self._fail(op, exc)
            return None

    # -- documents ---------------------------------------------------------- #
    def save_document(self, doc: Document, extraction: Extraction,
                      pid_geometry: Optional[dict] = None,
                      image: Optional[tuple[bytes, str]] = None,
                      industry_id: str = "demo") -> None:
        row = {
            "id": f"{industry_id}:{doc.id}",   # PK stays unique across industries
            "industry_id": industry_id,
            "doc_id": doc.id,
            "title": doc.title,
            "doc_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
            "date": doc.date,
            "unit": doc.unit,
            "text": doc.text,
            "is_image": doc.is_image,
            "extraction": extraction.model_dump(),
            "pid_geometry": pid_geometry,
            "image_b64": base64.b64encode(image[0]).decode("ascii") if image else None,
            "media_type": image[1] if image else None,
        }
        self._request(f"save_document({doc.id})", "POST", "/iiq_documents",
                      payload=row, prefer="resolution=merge-duplicates",
                      params={"on_conflict": "id"})

    def restore_documents(self, industry_id: str = "demo") -> list[dict]:
        rows = self._request("restore_documents", "GET", "/iiq_documents",
                             params={"select": "*", "order": "created_at.asc",
                                     "industry_id": f"eq.{industry_id}"})
        if not rows:
            return []
        out: list[dict] = []
        for r in rows:
            try:
                doc = Document(
                    id=r.get("doc_id") or r["id"], title=r["title"], doc_type=r["doc_type"],
                    date=r.get("date"), unit=r.get("unit"),
                    text=r.get("text") or "", is_image=bool(r.get("is_image")),
                )
                extraction = Extraction.model_validate(r.get("extraction") or {})
            except Exception as exc:
                print(f"[store] skipping bad persisted row {r.get('id')} ({exc})")
                continue
            image = None
            if r.get("image_b64"):
                try:
                    image = (base64.b64decode(r["image_b64"]), r.get("media_type") or "image/png")
                except Exception:
                    image = None
            out.append({
                "document": doc,
                "extraction": extraction,
                "pid_geometry": r.get("pid_geometry"),
                "image": image,
            })
        return out

    # -- query history (conversation context) -------------------------------- #
    def log_query(self, question: str, mode: str, lang: str, answer: str,
                  confidence: float, provider: str,
                  industry_id: str = "demo") -> None:
        # fire-and-forget on a daemon thread: answering never waits on the network
        def _send() -> None:
            self._request("log_query", "POST", "/iiq_queries", payload={
                "question": question, "mode": mode, "lang": lang,
                "answer": answer, "confidence": confidence, "provider": provider,
                "industry_id": industry_id,
            })
        threading.Thread(target=_send, daemon=True).start()

    # -- auth mirror ---------------------------------------------------------- #
    def save_industry(self, row: dict) -> None:
        self._request(f"save_industry({row.get('id')})", "POST", "/iiq_industries",
                      payload=row, prefer="resolution=merge-duplicates",
                      params={"on_conflict": "id"})

    def save_user(self, row: dict) -> None:
        self._request(f"save_user({row.get('email')})", "POST", "/iiq_users",
                      payload=row, prefer="resolution=merge-duplicates",
                      params={"on_conflict": "email"})

    def load_industries(self) -> list[dict]:
        return self._request("load_industries", "GET", "/iiq_industries",
                             params={"select": "*"}) or []

    def load_users(self) -> list[dict]:
        return self._request("load_users", "GET", "/iiq_users",
                             params={"select": "*"}) or []

    def status(self) -> dict:
        return {"provider": self.name, "healthy": not self._down}


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_INSTANCE: Optional[NullStore] = None


def get_store() -> NullStore:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    if config.PERSIST_MODE == "supabase":
        try:
            _INSTANCE = SupabaseStore()
        except Exception as exc:  # pragma: no cover — fall back rather than crash
            print(f"[store] supabase init failed ({exc}); falling back to memory mode")
            _INSTANCE = NullStore()
    else:
        _INSTANCE = NullStore()
    return _INSTANCE
