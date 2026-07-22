"""Calibrate the live-embedding out-of-corpus gate + smoke-test semantic search.

Run:  .venv/Scripts/python backend/scripts/calibrate_embeddings.py
Prints max query->corpus cosine for on-topic paraphrase queries (no shared
keywords with the corpus wording) and off-topic queries, then shows top search
hits so the 'similar meaning' behaviour is visible.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.engine import get_engine  # noqa: E402

ON_TOPIC = [
    "Why did the charge pump fail?",
    "pump making strange noises and shaking",          # paraphrase of vibration
    "machine wobbling more than the manufacturer allows",
    "what are the legal safety rules we must follow",   # paraphrase of regulations
    "how do I safely shut down the crude unit equipment",
    "history of repairs done on the pumps",
    "worn out rotating part inside the pump",           # paraphrase of bearing
    "is the sister pump showing the same problem",
]
OFF_TOPIC = [
    "best pizza places in town",
    "how to train a puppy",
    "latest cricket world cup score",
    "recipe for chocolate cake",
    "cheap flights to Paris",
    "what is the capital of Australia",
    "top 10 movies this year",
    "how to learn guitar chords",
    "stock market prediction for tomorrow",
    "birthday gift ideas for mom",
]

eng = get_engine("demo")
idx = eng.index
provider = idx._providers()[0]
print(f"\nembedder: {provider.name} (live={provider.live}), "
      f"passages={len(idx.passages)}\n")

print("=== ON-TOPIC (paraphrases) ===")
on_scores = []
for q in ON_TOPIC:
    c, thr = idx.max_cosine(q)
    on_scores.append(c)
    print(f"  {c:.3f}  (thr {thr:.2f})  {q}")

print("\n=== OFF-TOPIC ===")
off_scores = []
for q in OFF_TOPIC:
    c, thr = idx.max_cosine(q)
    off_scores.append(c)
    print(f"  {c:.3f}  (thr {thr:.2f})  {q}")

print(f"\non-topic  min = {min(on_scores):.3f}")
print(f"off-topic max = {max(off_scores):.3f}")
mid = (min(on_scores) + max(off_scores)) / 2
print(f"suggested threshold (midpoint) = {mid:.3f}")

print("\n=== SAMPLE SEARCHES (top-3) ===")
for q in ["pump making strange noises and shaking",
          "machine wobbling more than the manufacturer allows",
          "what are the legal safety rules we must follow"]:
    print(f"\nQ: {q}")
    for p, s in idx.search(q, k=3):
        print(f"   {s:.3f}  [{p.doc_id}] {p.title}")
