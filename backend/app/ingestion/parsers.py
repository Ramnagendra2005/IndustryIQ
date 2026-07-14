"""Heterogeneous document parsers for the ingestion pipeline.

Turns an uploaded file (PDF, scanned image / P&ID, spreadsheet, email, text)
into a normalized Document plus the payload the extractor needs:
  * text documents  -> ("text", <string>)
  * images/P&IDs    -> ("image", (<bytes>, <media_type>))   [parsed via Claude vision]
"""
from __future__ import annotations

import io
import re
from typing import Tuple

from ..schemas import DocType, Document

_IMAGE_EXT = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
              "gif": "image/gif", "webp": "image/webp"}


def _guess_doc_type(name: str, text: str) -> DocType:
    n = name.lower()
    t = text.lower()
    if "p&id" in n or "pid" in n or "p&id" in t or "piping" in t:
        return DocType.PID
    if "work order" in t or n.startswith("wo-"):
        return DocType.WORK_ORDER
    if "inspection" in t or "vibration survey" in t or "condition monitoring" in t:
        return DocType.INSPECTION
    if "incident" in t or "failure report" in t or "root cause" in t:
        return DocType.INCIDENT
    if "oem" in t or "manual" in t:
        return DocType.OEM_MANUAL
    if "sop" in t or "standard operating procedure" in t:
        return DocType.SOP
    if "factory act" in t or "oisd" in t or "peso" in t or "clause" in t:
        return DocType.REGULATION
    if n.endswith((".csv", ".xlsx", ".xls")):
        return DocType.SPREADSHEET
    if n.endswith(".eml") or "from:" in t[:200] and "subject:" in t.lower():
        return DocType.EMAIL
    return DocType.OTHER


def _extract_date(text: str) -> str | None:
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{2}/\d{2}/20\d{2})\b", text)
    return m.group(1) if m else None


def _slugify(name: str) -> str:
    base = re.sub(r"\.[^.]+$", "", name)
    return re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").upper()[:40] or "DOC"


def parse_upload(filename: str, content: bytes) -> Tuple[Document, Tuple[str, object]]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    doc_id = _slugify(filename)

    # --- image / P&ID ------------------------------------------------- #
    if ext in _IMAGE_EXT:
        doc = Document(id=doc_id, title=filename, doc_type=DocType.PID,
                       text=f"[image document: {filename} — parsed via vision]",
                       is_image=True, source_path=filename)
        return doc, ("image", (content, _IMAGE_EXT[ext]))

    # --- spreadsheet -------------------------------------------------- #
    if ext in ("csv", "xlsx", "xls"):
        text = _spreadsheet_to_text(filename, content, ext)
        doc = Document(id=doc_id, title=filename, doc_type=DocType.SPREADSHEET,
                       text=text, date=_extract_date(text), source_path=filename)
        return doc, ("text", text)

    # --- pdf ---------------------------------------------------------- #
    if ext == "pdf":
        text = _pdf_to_text(content)
        dt = _guess_doc_type(filename, text)
        doc = Document(id=doc_id, title=filename, doc_type=dt, text=text,
                       date=_extract_date(text), source_path=filename)
        return doc, ("text", text)

    # --- text / email / md / eml ------------------------------------- #
    text = content.decode("utf-8", errors="replace")
    dt = _guess_doc_type(filename, text)
    doc = Document(id=doc_id, title=filename, doc_type=dt, text=text,
                   date=_extract_date(text), source_path=filename)
    return doc, ("text", text)


def _pdf_to_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:  # pragma: no cover
        return f"[could not parse PDF: {exc}]"


def _spreadsheet_to_text(filename: str, content: bytes, ext: str) -> str:
    try:
        import pandas as pd

        if ext == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        # Render each row as a readable line so the extractor sees structured facts.
        lines = [f"Spreadsheet {filename} — columns: {', '.join(map(str, df.columns))}"]
        for _, row in df.iterrows():
            lines.append("; ".join(f"{c}={row[c]}" for c in df.columns))
        return "\n".join(lines)
    except Exception as exc:  # pragma: no cover
        return f"[could not parse spreadsheet: {exc}]"
