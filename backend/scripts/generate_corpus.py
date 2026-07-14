"""Emit the authored corpus as human-readable files under backend/data/corpus.

These are the 'real industrial document samples' judges can open and inspect.
Run:  python backend/scripts/generate_corpus.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_data  # noqa: E402

CORPUS_DIR = Path(__file__).resolve().parents[1] / "data" / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

_EXT = {
    "P&ID": ".pid.txt", "WorkOrder": ".txt", "InspectionReport": ".txt",
    "OEMManual": ".txt", "IncidentReport": ".txt", "SOP": ".txt",
    "RegulatoryDocument": ".txt", "Email": ".eml", "Spreadsheet": ".csv",
}


def main() -> None:
    for d in corpus_data.DOCS:
        ext = _EXT.get(d["doc_type"], ".txt")
        path = CORPUS_DIR / f"{d['id']}{ext}"
        path.write_text(d["text"])
    print(f"wrote {len(corpus_data.DOCS)} corpus files to {CORPUS_DIR}")


if __name__ == "__main__":
    main()
