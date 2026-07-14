"""Generate the deterministic seed used by the offline SeedMock LLM provider.

Writes backend/data/seed/seed_llm.json containing:
  * extractions: {doc_id -> Extraction}  (ground-truth, for offline re-ingest)
  * answers:     {key -> {triggers, answer}}  (offline copilot answers)

Run:  python backend/scripts/build_seed.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus_data  # noqa: E402

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "seed"
SEED_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    extractions = {d["id"]: d["extraction"] for d in corpus_data.DOCS}
    payload = {"extractions": extractions, "answers": corpus_data.SEED_ANSWERS}
    out = SEED_DIR / "seed_llm.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out}  ({len(extractions)} extractions, {len(corpus_data.SEED_ANSWERS)} answers)")


if __name__ == "__main__":
    main()
