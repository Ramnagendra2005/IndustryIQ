"""Central configuration for IndustryIQ, loaded from environment / .env."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (two levels up from this file) if present.
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
CORPUS_DIR = DATA_DIR / "corpus"
SEED_DIR = DATA_DIR / "seed"

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()

# Resolve LLM mode. "auto" => live when a key is present, else deterministic seed.
_MODE = os.getenv("LLM_MODE", "auto").strip().lower()
if _MODE == "auto":
    LLM_MODE = "live" if GEMINI_API_KEY else "seed"
else:
    LLM_MODE = _MODE

ANSWER_MODEL = os.getenv("IIQ_ANSWER_MODEL", "gemini-2.5-flash")
EXTRACT_MODEL = os.getenv("IIQ_EXTRACT_MODEL", "gemini-2.5-flash")
VISION_MODEL = os.getenv("IIQ_VISION_MODEL", "gemini-2.5-flash")

HOST = os.getenv("IIQ_HOST", "0.0.0.0")
PORT = int(os.getenv("IIQ_PORT", "8000"))

# Embedding model (torch-free static embeddings, downloaded once from HF).
EMBED_MODEL = os.getenv("IIQ_EMBED_MODEL", "minishlab/potion-base-8M")


def status() -> dict:
    """Small dict describing runtime config (safe to expose to the UI)."""
    return {
        "llm_mode": LLM_MODE,
        "has_api_key": bool(GEMINI_API_KEY),
        "answer_model": ANSWER_MODEL,
        "extract_model": EXTRACT_MODEL,
        "vision_model": VISION_MODEL,
    }
