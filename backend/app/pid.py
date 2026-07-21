"""Interactive P&ID digitization — "the drawing is the interface".

Two ways a P&ID becomes a clickable navigation layer over the knowledge graph:

  * VECTOR   — authored geometry for the built-in seed drawing (CDU-1 charge
               pump loop). Rendered as crisp ISA-style symbols, so it always
               works offline and every symbol maps to a real graph entity.
  * IMAGE    — any P&ID uploaded at runtime. Gemini vision detects each symbol's
               bounding box (see llm.locate_pid_symbols); we overlay transparent
               clickable hotspots on the original image. If localization is
               unavailable (offline seed mode), we still expose every detected
               equipment tag as a clickable rail, so the feature degrades
               gracefully instead of breaking.

Either way, clicking a symbol resolves to a graph entity and opens its dossier
(agents.dossier.build_dossier).
"""
from __future__ import annotations

import re
from typing import List, Optional

from .agents.dossier import entity_health
from .schemas import PidConnection, PidDiagram, PidSummary, PidSymbol


# --------------------------------------------------------------------------- #
# Symbol classification (generic — works for arbitrary plant tags)
# --------------------------------------------------------------------------- #
def symbol_for_tag(tag: str, type_hint: Optional[str] = None) -> str:
    """Best-effort ISA glyph for a tag like P-101, E-204, MOV-114, VT-101.

    Uses the tag prefix (the ISA equipment/instrument letter) so it generalizes
    to P&IDs we've never seen, not just the seed corpus.
    """
    t = (tag or "").upper().strip()
    m = re.match(r"^([A-Z]{1,4})", t)
    prefix = m.group(1) if m else ""
    if prefix.endswith("V"):                     # MOV, XV, FV, PSV, BV, CV, HV...
        return "valve"
    if len(prefix) >= 2 and prefix[-1] in "TEI":  # VT, TT, PT, FT, LT, AE, PI...
        return "instrument"
    first = prefix[:1]
    return {
        "P": "pump", "E": "exchanger", "C": "column", "T": "tank",
        "V": "valve", "K": "compressor", "D": "vessel", "R": "vessel",
        "F": "vessel", "B": "vessel", "S": "vessel", "H": "exchanger",
    }.get(first, "generic")


# --------------------------------------------------------------------------- #
# Authored vector geometry for the seed P&ID (viewBox coordinates)
# --------------------------------------------------------------------------- #
VECTOR_DIAGRAMS = {
    "PID-CDU1-002": {
        "view": {"w": 1000, "h": 560},
        "symbols": [
            {"tag": "T-01",    "symbol": "tank",       "cx": 110, "cy": 300},
            {"tag": "P-101",   "symbol": "pump",       "cx": 340, "cy": 235},
            {"tag": "P-102",   "symbol": "pump",       "cx": 340, "cy": 425},
            {"tag": "MOV-114", "symbol": "valve",      "cx": 340, "cy": 330},
            {"tag": "VT-101",  "symbol": "instrument", "cx": 460, "cy": 135},
            {"tag": "E-204",   "symbol": "exchanger",  "cx": 640, "cy": 235},
            {"tag": "C-301",   "symbol": "column",     "cx": 880, "cy": 250},
        ],
        "connections": [
            {"source": "T-01",    "target": "P-101",   "type": "CONNECTED_TO"},
            {"source": "T-01",    "target": "P-102",   "type": "CONNECTED_TO"},
            {"source": "P-101",   "target": "E-204",   "type": "CONNECTED_TO"},
            {"source": "P-102",   "target": "MOV-114", "type": "CONNECTED_TO"},
            {"source": "MOV-114", "target": "E-204",   "type": "CONNECTED_TO"},
            {"source": "E-204",   "target": "C-301",   "type": "CONNECTED_TO"},
            {"source": "P-101",   "target": "P-102",   "type": "SIBLING_OF", "label": "identical standby"},
            {"source": "P-101",   "target": "VT-101",  "type": "HAS_PART",   "label": "vibration"},
        ],
    },
}


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def _doc_equipment(kg, doc_id: str) -> List[str]:
    """Equipment/instrument tags the graph associates with a document."""
    out: List[str] = []
    for e in kg.equipment_tags():
        if doc_id in e["docs"] and e["key"] not in out:
            out.append(e["key"])
    return out


def _symbol_from_entity(kg, tag: str, compliance, trust, *, symbol=None,
                        cx=None, cy=None, box=None, type_hint=None) -> PidSymbol:
    view = kg.node_view(tag)
    label = view["label"] if view else tag
    etype = view["type"] if view else (type_hint or "Equipment")
    return PidSymbol(
        tag=tag,
        entity=view["key"] if view else None,
        label=label,
        type=etype,
        symbol=symbol or symbol_for_tag(label, etype),
        cx=cx, cy=cy, box=box,
        health=entity_health(kg, tag, compliance, trust) if view else "ok",
        doc_count=len(view["docs"]) if view else 0,
    )


def build_diagram(engine, doc_id: str) -> Optional[PidDiagram]:
    kg = engine.kg
    doc = kg.get_document(doc_id)
    if not doc and doc_id not in VECTOR_DIAGRAMS:
        return None
    compliance = engine.compliance_cached()
    trust = engine.trust()
    title = doc.title if doc else doc_id
    unit = doc.unit if doc else None

    # ---- vector (authored seed drawing) --------------------------------- #
    if doc_id in VECTOR_DIAGRAMS:
        spec = VECTOR_DIAGRAMS[doc_id]
        symbols = [
            _symbol_from_entity(kg, s["tag"], compliance, trust,
                                symbol=s["symbol"], cx=s["cx"], cy=s["cy"])
            for s in spec["symbols"]
        ]
        connections = [PidConnection(**c) for c in spec["connections"]]
        return PidDiagram(doc_id=doc_id, title=title, unit=unit, kind="vector",
                          view=spec["view"], symbols=symbols, connections=connections)

    # ---- image (uploaded drawing) --------------------------------------- #
    geom = engine.pid_geometry(doc_id)
    image_url = f"/api/pid/{doc_id}/image" if engine.has_pid_image(doc_id) else None
    symbols: List[PidSymbol] = []
    connections: List[PidConnection] = []
    note = ""

    if geom and geom.get("symbols"):
        for s in geom["symbols"]:
            symbols.append(_symbol_from_entity(
                kg, s["tag"], compliance, trust,
                symbol=s.get("symbol"), box=s.get("box"), type_hint=s.get("type")))
        connections = [PidConnection(**c) for c in geom.get("connections", [])]
    else:
        detail = ("this offline build can't localize symbols" if not engine.llm.live
                  else "symbol positions couldn't be auto-detected on this drawing")
        note = (f"Interactive hotspots unavailable — {detail}. Every detected tag is "
                "listed below as a clickable chip; each still opens its full dossier.")
        for tag in _doc_equipment(kg, doc_id):
            symbols.append(_symbol_from_entity(kg, tag, compliance, trust))

    view = geom.get("view", {"w": 1000, "h": 700}) if geom else {"w": 1000, "h": 700}
    return PidDiagram(doc_id=doc_id, title=title, unit=unit, kind="image",
                      image_url=image_url, view=view, symbols=symbols,
                      connections=connections, note=note)


def list_diagrams(engine) -> List[PidSummary]:
    """Every P&ID available to open: the seed vector drawing + any uploaded ones."""
    kg = engine.kg
    ids: List[str] = list(VECTOR_DIAGRAMS.keys())
    for d in kg.documents():
        dtype = d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type)
        is_pid_image = engine.has_pid_image(d.id) or bool(engine.pid_geometry(d.id))
        if (dtype == "P&ID" or is_pid_image) and d.id not in ids:
            ids.append(d.id)

    out: List[PidSummary] = []
    for did in ids:
        diagram = build_diagram(engine, did)
        if not diagram:
            continue
        out.append(PidSummary(
            doc_id=diagram.doc_id, title=diagram.title, unit=diagram.unit,
            kind=diagram.kind, symbol_count=len(diagram.symbols),
            alert_count=sum(1 for s in diagram.symbols if s.health == "alert"),
        ))
    return out
