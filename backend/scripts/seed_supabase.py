"""Push the demo corpus + demo tenant into Supabase.

Run ONCE after applying supabase_schema.sql in the Supabase SQL editor:

    cd backend && python scripts/seed_supabase.py

This mirrors the authored seed corpus (corpus_data.DOCS) and the demo
account into Supabase so the data lives in the database rather than only
in memory. The running app still rebuilds the seed graph at boot; this
script exists so the corpus is queryable/inspectable in Supabase and so a
fresh deployment starts from a populated, production-ready store.

Idempotent: every write upserts on its primary key, so re-running is safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

# make `app` and `corpus_data` importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import config  # noqa: E402  (loads .env on import)
from app.auth import (  # noqa: E402
    DEMO_EMAIL,
    DEMO_INDUSTRY_ID,
    DEMO_INDUSTRY_NAME,
    DEMO_PASSWORD,
    hash_password,
)
from app.persistence import SupabaseStore  # noqa: E402
from app.schemas import Document, Extraction  # noqa: E402

import corpus_data  # noqa: E402


def main() -> None:
    if not (config.SUPABASE_URL and config.SUPABASE_KEY):
        sys.exit("SUPABASE_URL and SUPABASE_KEY must be set in .env before seeding.")

    store = SupabaseStore()

    # -- tenant + demo account ------------------------------------------------
    store.save_industry({
        "id": DEMO_INDUSTRY_ID,
        "name": DEMO_INDUSTRY_NAME,
        "join_code": "DEMO-0000",
    })
    print(f"industry : {DEMO_INDUSTRY_NAME} ({DEMO_INDUSTRY_ID})")

    store.save_user({
        "id": "demo-user",
        "email": DEMO_EMAIL,
        "name": "Demo Engineer",
        "password_hash": hash_password(DEMO_PASSWORD),
        "industry_id": DEMO_INDUSTRY_ID,
        "role": "admin",
    })
    print(f"user     : {DEMO_EMAIL}")

    # -- corpus documents -----------------------------------------------------
    for d in corpus_data.DOCS:
        doc = Document(
            id=d["id"], title=d["title"], doc_type=d["doc_type"],
            date=d.get("date"), unit=d.get("unit"),
            text=d["text"], is_image=d.get("is_image", False),
        )
        extraction = Extraction.model_validate(d["extraction"])
        store.save_document(doc, extraction, industry_id=DEMO_INDUSTRY_ID)
        # ascii-safe: Windows consoles (cp1252) choke on unicode dashes in titles
        print(f"document : {doc.id:16s} - {doc.title}".encode("ascii", "replace").decode())

    if store.status().get("healthy"):
        print(f"\n[ok] Seeded {len(corpus_data.DOCS)} document(s) to Supabase.")
    else:
        sys.exit("\n[fail] Supabase writes failed — check SUPABASE_URL/SUPABASE_KEY "
                 "and that supabase_schema.sql has been applied.")


if __name__ == "__main__":
    main()
