"""LLM abstraction layer.

Two providers behind one interface:

  * LiveGemini  — calls the Google Gemini API using the user's own key. Powers
                  live ingestion of newly-uploaded documents and copilot answers.
  * SeedMock    — deterministic, offline. Because we author the synthetic corpus,
                  we can pre-compute ground-truth extractions and hand-authored
                  answers, so the demo is bulletproof with no network / no key.

The rest of the app never imports `google.genai` directly — it goes through
`get_llm()` so the two modes are fully swappable. This is also the "works
air-gapped for secure industrial sites" story for the pitch.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from . import config
from .schemas import Extraction


# --------------------------------------------------------------------------- #
# Base interface
# --------------------------------------------------------------------------- #
class BaseLLM:
    name = "base"
    live = False

    def extract(self, text: str, doc_hint: str = "") -> Extraction:
        raise NotImplementedError

    def extract_image(self, image_bytes: bytes, media_type: str, doc_hint: str = "") -> Extraction:
        raise NotImplementedError

    def answer(self, system: str, question: str, context: str) -> str:
        raise NotImplementedError

    def locate_pid_symbols(self, image_bytes: bytes, media_type: str) -> list[dict]:
        """Detect clickable symbols on a P&ID image.

        Returns a list of {tag, symbol, type, box:[x,y,w,h]} where the box is
        normalized 0..1 over the image. Providers that cannot do vision return [].
        """
        return []


# --------------------------------------------------------------------------- #
# Prompts / JSON schema shared by both providers
# --------------------------------------------------------------------------- #
_LOCATE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "symbols": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tag": {"type": "string"},
                    "symbol": {
                        "type": "string",
                        "enum": ["pump", "valve", "exchanger", "column", "tank",
                                 "vessel", "compressor", "instrument", "generic"],
                    },
                    "type": {
                        "type": "string",
                        "enum": ["Equipment", "ProcessParameter", "Location", "Part"],
                    },
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "w": {"type": "number"},
                    "h": {"type": "number"},
                },
                "required": ["tag", "symbol", "type", "x", "y", "w", "h"],
            },
        },
    },
    "required": ["symbols"],
}

_LOCATE_SYSTEM = (
    "You are a P&ID digitizer. Find every equipment and instrument symbol that "
    "carries a printed tag (pumps P-xxx, exchangers E-xxx, columns/vessels C-xxx/"
    "D-xxx, tanks T-xxx, valves like MOV-xxx/XV-xxx, instrument bubbles like "
    "VT/TT/PT/FT-xxx). For each, return its tag, an ISA symbol class, an entity "
    "type, and a TIGHT bounding box around the symbol as x,y,w,h where every value "
    "is a fraction of the image (0..1): x,y is the top-left corner, w,h the width "
    "and height. Do not include piping, notes, title blocks or the border."
)
_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "Equipment", "ProcessParameter", "FailureMode", "Person",
                            "Regulation", "Procedure", "Document", "Date", "Location", "Part",
                        ],
                    },
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "description": {"type": "string"},
                },
                "required": ["name", "type", "aliases", "description"],
            },
        },
        "relations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "CONNECTED_TO", "HAS_FAILURE", "HAS_PARAMETER", "MAINTAINED_BY",
                            "GOVERNED_BY", "DOCUMENTED_IN", "SIBLING_OF", "HAS_PART",
                            "PROCEDURE_FOR", "OCCURRED_ON", "LOCATED_IN", "MENTIONS",
                        ],
                    },
                    "evidence": {"type": "string"},
                },
                "required": ["source", "target", "type", "evidence"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["entities", "relations", "summary"],
}

_EXTRACTION_SYSTEM = (
    "You are an industrial knowledge-graph extraction engine for asset-intensive "
    "plants (refineries, petrochemical, power). Extract equipment tags (e.g. P-101, "
    "E-204), process parameters with values, failure modes, parts, people, dates, "
    "locations/units, regulations (Factory Act, OISD, PESO, environmental norms) and "
    "procedures. Extract the RELATIONSHIPS between them — this is the most important "
    "part. Prefer canonical equipment tags as entity names. Only extract what is "
    "supported by the text; put a short supporting quote in each relation's evidence."
)

ANSWER_SYSTEM = (
    "You are IndustryIQ, an expert industrial operations copilot for maintenance "
    "engineers and field technicians. You answer using ONLY the retrieved context "
    "from the plant's document corpus and knowledge graph. Connect information across "
    "multiple documents to reach conclusions no single document states. Always be "
    "concrete and cite the source documents by their [DOC:id] tags inline. If the "
    "context is insufficient, say so rather than inventing. Lead with the direct "
    "answer, then the supporting reasoning. Keep it tight and field-ready."
)


# --------------------------------------------------------------------------- #
# Live provider
# --------------------------------------------------------------------------- #
class LiveGemini(BaseLLM):
    name = "live-gemini"
    live = True

    def __init__(self) -> None:
        from google import genai  # imported lazily so seed mode needs no network at all

        self._client = genai.Client(api_key=config.GEMINI_API_KEY)

    def _structured(self, model: str, contents, doc_hint: str) -> Extraction:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_EXTRACTION_SYSTEM,
                max_output_tokens=16000,
                response_mime_type="application/json",
                response_json_schema=_EXTRACTION_SCHEMA,
            ),
        )
        raw = resp.text or "{}"
        try:
            return Extraction.model_validate_json(raw)
        except Exception:
            # dense drawings can truncate the JSON — salvage the complete objects
            # instead of dropping the whole extraction to the offline stub.
            salvaged = _salvage_extraction(raw)
            print(f"[llm] extraction JSON invalid for {doc_hint or 'doc'} "
                  f"(raw {len(raw)} chars); salvaged {len(salvaged.entities)} entities / "
                  f"{len(salvaged.relations)} relations")
            return salvaged

    def extract(self, text: str, doc_hint: str = "") -> Extraction:
        contents = f"Document type hint: {doc_hint}\n\n---\n{text[:60000]}"
        return self._structured(config.EXTRACT_MODEL, contents, doc_hint)

    def extract_image(self, image_bytes: bytes, media_type: str, doc_hint: str = "") -> Extraction:
        from google.genai import types

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            (
                f"This is an industrial {doc_hint} (e.g. a P&ID or scanned inspection form). "
                "Read every equipment tag, connection, parameter and note. Digitise it into "
                "the knowledge-graph schema — connections between equipment are CONNECTED_TO "
                "relations."
            ),
        ]
        return self._structured(config.VISION_MODEL, contents, doc_hint)

    def answer(self, system: str, question: str, context: str) -> str:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=config.ANSWER_MODEL,
            contents=f"CONTEXT FROM PLANT KNOWLEDGE BASE:\n{context}\n\n---\nQUESTION: {question}",
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=2000,
            ),
        )
        return resp.text or ""

    def locate_pid_symbols(self, image_bytes: bytes, media_type: str) -> list[dict]:
        from google.genai import types

        # Vision JSON occasionally comes back truncated or fence-wrapped, which used
        # to make this silently return [] (drawing falls back to the tag rail). We
        # salvage partial output and retry once so localization is reliable.
        for attempt in range(2):
            resp = self._client.models.generate_content(
                model=config.VISION_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                    "Digitize this P&ID: locate every tagged equipment and instrument symbol.",
                ],
                config=types.GenerateContentConfig(
                    system_instruction=_LOCATE_SYSTEM,
                    max_output_tokens=16000,
                    response_mime_type="application/json",
                    response_json_schema=_LOCATE_SCHEMA,
                ),
            )
            raw = resp.text or ""
            out = _normalize_pid_symbols(_parse_symbol_objects(raw))
            if out:
                return out
            print(f"[llm] locate_pid_symbols: no usable symbols on attempt {attempt + 1} "
                  f"(raw {len(raw)} chars){' — retrying' if attempt == 0 else ''}")
        return []


# --------------------------------------------------------------------------- #
# Seed / mock provider (deterministic, offline)
# --------------------------------------------------------------------------- #
class SeedMock(BaseLLM):
    """Serves pre-computed extractions/answers keyed by document id or question.

    The seed data is authored alongside the synthetic corpus so the whole app —
    ingestion, graph, retrieval, answering — runs end-to-end without any API key.
    Unknown inputs fall back to a lightweight heuristic extractor so newly
    uploaded documents still land *something* in the graph during an offline demo.
    """
    name = "seed-mock"
    live = False

    def __init__(self, seed_path: Optional[Path] = None) -> None:
        self._extractions: dict[str, dict] = {}
        self._answers: dict[str, dict] = {}
        path = seed_path or (config.SEED_DIR / "seed_llm.json")
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self._extractions = data.get("extractions", {})
            self._answers = data.get("answers", {})

    # -- extraction ------------------------------------------------------- #
    def _by_hint(self, doc_hint: str) -> Optional[Extraction]:
        # doc_hint carries the document id in seed mode (set by the ingester).
        raw = self._extractions.get(doc_hint)
        if raw:
            return Extraction.model_validate(raw)
        return None

    def extract(self, text: str, doc_hint: str = "") -> Extraction:
        seeded = self._by_hint(doc_hint)
        if seeded:
            return seeded
        return _heuristic_extract(text)

    def extract_image(self, image_bytes: bytes, media_type: str, doc_hint: str = "") -> Extraction:
        seeded = self._by_hint(doc_hint)
        if seeded:
            return seeded
        return Extraction(summary=f"[offline] image {doc_hint} not in seed set")

    # -- answering -------------------------------------------------------- #
    def answer(self, system: str, question: str, context: str) -> str:
        # Match a seeded answer by keyword overlap; otherwise synthesise a
        # grounded extractive answer straight from the retrieved context so the
        # copilot is still useful offline.
        best_key, best_score = None, 0.0
        q_tokens = set(_tok(question))
        for key, entry in self._answers.items():
            trig = set()
            for t in entry.get("triggers", []):
                trig |= set(_tok(t))
            score = len(q_tokens & trig) / (len(trig) + 1)
            if score > best_score:
                best_key, best_score = key, score
        if best_key and best_score >= 0.15:
            return self._answers[best_key]["answer"]
        return _extractive_answer(question, context)


# --------------------------------------------------------------------------- #
# Offline helpers
# --------------------------------------------------------------------------- #
def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text[:4].lower() == "json":
            text = text[4:]
    return text.strip()


def _all_json_objects(text: str) -> list[dict]:
    """Every individually-complete ``{...}`` object anywhere in the string.

    Balanced-brace scan that stays valid even when the enclosing array/object is
    truncated mid-stream — the recovery path for cut-off vision/LLM JSON.
    """
    out: list[dict] = []
    stack: list[int] = []
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            frag = text[stack.pop():i + 1]
            try:
                o = json.loads(frag)
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                out.append(o)
    return out


def _parse_symbol_objects(raw: str) -> list[dict]:
    """Pull symbol dicts out of a vision JSON response, tolerating truncation.

    The happy path is a clean ``{"symbols": [...]}`` blob. But vision models
    sometimes wrap it in ```json fences or get cut off mid-array when the drawing
    is dense — a plain ``json.loads`` then throws and we lose every symbol. So we
    fall back to scanning for individually-complete ``{...}`` objects (which stay
    valid even when the outer array never closes) and keep the located ones.
    """
    if not raw:
        return []
    text = _strip_json_fence(raw)
    try:
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("symbols"), list):
            return [s for s in data["symbols"] if isinstance(s, dict)]
    except json.JSONDecodeError:
        pass
    return [o for o in _all_json_objects(text) if "tag" in o and "x" in o]


def _salvage_extraction(raw: str) -> "Extraction":
    """Recover a partial Extraction from truncated/invalid LLM JSON.

    Entities and relations are distinguished by shape (name/type vs
    source/target/type). Individual objects that don't validate are dropped
    rather than sinking the whole extraction to the offline stub.
    """
    from .schemas import ExtractedEntity, ExtractedRelation

    ents: list = []
    rels: list = []
    seen: set[str] = set()
    for o in _all_json_objects(_strip_json_fence(raw)):
        if "source" in o and "target" in o and "type" in o:
            try:
                rels.append(ExtractedRelation.model_validate(o))
            except Exception:
                continue
        elif "name" in o and "type" in o:
            name = str(o.get("name", "")).strip()
            if not name or name in seen:
                continue
            try:
                ent = ExtractedEntity.model_validate({
                    "name": name, "type": o["type"],
                    "aliases": o.get("aliases", []) or [],
                    "description": o.get("description", "") or "",
                })
            except Exception:
                continue
            seen.add(name)
            ents.append(ent)
    return Extraction(entities=ents, relations=rels, summary="")


def _normalize_pid_symbols(symbols: list[dict]) -> list[dict]:
    """Clamp boxes to the image, drop degenerate/untagged ones, dedupe by tag."""
    out: list[dict] = []
    seen: set[str] = set()
    for s in symbols:
        try:
            x, y, w, h = float(s["x"]), float(s["y"]), float(s["w"]), float(s["h"])
        except (KeyError, TypeError, ValueError):
            continue
        x, y = max(0.0, min(1.0, x)), max(0.0, min(1.0, y))
        w, h = max(0.0, min(1.0, w)), max(0.0, min(1.0, h))
        if w < 0.005 or h < 0.005:
            continue
        tag = str(s.get("tag", "")).strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append({
            "tag": tag,
            "symbol": s.get("symbol", "generic"),
            "type": s.get("type", "Equipment"),
            "box": [round(x, 4), round(y, 4), round(w, 4), round(h, 4)],
        })
    return out


def _tok(s: str) -> list[str]:
    return [w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if len(w) > 2]


def _heuristic_extract(text: str) -> Extraction:
    """Very small regex-ish fallback so uploaded docs still populate the graph."""
    import re

    ents: dict[str, ExtractedEntityDict] = {}
    tags = set(re.findall(r"\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b", text))
    for t in tags:
        ents[t] = {"name": t, "type": "Equipment", "aliases": [], "description": "auto-detected tag"}
    for kw, typ in [
        ("Factory Act", "Regulation"), ("OISD", "Regulation"), ("PESO", "Regulation"),
        ("vibration", "ProcessParameter"), ("temperature", "ProcessParameter"),
        ("pressure", "ProcessParameter"), ("bearing", "Part"), ("seal", "Part"),
    ]:
        if kw.lower() in text.lower():
            ents[kw] = {"name": kw, "type": typ, "aliases": [], "description": "auto-detected"}
    from .schemas import ExtractedEntity
    return Extraction(
        entities=[ExtractedEntity.model_validate(e) for e in ents.values()],
        relations=[],
        summary=text[:200],
    )


def _extractive_answer(question: str, context: str) -> str:
    """Rank context lines by keyword overlap and stitch a grounded answer."""
    q = set(_tok(question))
    scored = []
    for block in context.split("\n"):
        b = block.strip()
        if len(b) < 20:
            continue
        overlap = len(q & set(_tok(b)))
        if overlap:
            scored.append((overlap, b))
    scored.sort(reverse=True)
    if not scored:
        return ("I could not find enough in the plant corpus to answer confidently. "
                "Try rephrasing or ingest more documents.")
    top = [b for _, b in scored[:5]]
    return ("Based on the retrieved plant records:\n\n" + "\n".join(f"• {b}" for b in top) +
            "\n\n(Offline mode: this is an extractive summary of the source documents. "
            "Provide a GEMINI_API_KEY for full generative reasoning.)")


# type alias only for annotation clarity above
ExtractedEntityDict = dict


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
_INSTANCE: Optional[BaseLLM] = None


def get_llm() -> BaseLLM:
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE
    if config.LLM_MODE == "live":
        try:
            _INSTANCE = LiveGemini()
        except Exception as exc:  # pragma: no cover - fall back rather than crash
            print(f"[llm] live init failed ({exc}); falling back to seed mode")
            _INSTANCE = SeedMock()
    else:
        _INSTANCE = SeedMock()
    return _INSTANCE
