"""Trust Layer — contradiction & staleness detection over the corpus.

In industry, a confidently wrong answer sourced from a stale or contradicted
document is worse than no answer. This agent continuously scans the corpus for:

  * STALENESS  — every document gets a freshness score that decays by a
                 doc-type half-life (a work order ages in months, a P&ID in
                 years, a statute never). Time is measured against the
                 "corpus clock" (the newest evidence date in the plant), so
                 the result is deterministic and moves forward as new
                 documents are ingested.
  * CONFLICTS  — deterministic detectors that cross-read documents:
                 numeric setpoint disagreements, procedures the plant's own
                 records show being violated, documented as-built reality
                 contradicting SOP requirements, and old drawings that no
                 longer reflect the modified plant.

Every copilot answer is then annotated with the trust of its OWN citations
(`annotate_answer`), so a warning travels with the answer to the field.
The detectors are generic (regex/graph driven, not keyed to doc ids) so newly
ingested documents participate immediately.
"""
from __future__ import annotations

import re
import time
from datetime import date
from typing import Dict, List, Optional, Tuple

from ..schemas import (AnswerTrust, Citation, Conflict, DocFreshness,
                       Document, TrustReport)

# --------------------------------------------------------------------------- #
# Staleness / freshness
# --------------------------------------------------------------------------- #
# Half-life in days per doc type: after one half-life the doc's freshness is
# 0.5. Grounded in plant practice: work orders describe a point-in-time state;
# SOPs sit on 2-3 year review cycles; P&IDs must track plant modifications.
_HALF_LIFE_DAYS = {
    "WorkOrder": 240,
    "InspectionReport": 180,     # OISD-116 wants surveys every 3 months
    "Email": 150,
    "Spreadsheet": 240,
    "P&ID": 1500,                # ~4y — must be re-verified after modifications
    "SOP": 1100,                 # ~3y review cycle
    "OEMManual": 4000,
    "Other": 365,
}
# Historical records don't expire: an incident report is a lesson learned, a
# statute stays in force until superseded.
_EVERGREEN = {"IncidentReport", "RegulatoryDocument"}

_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    m = _DATE_RE.search(s)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def _doc_type(d: Document) -> str:
    return d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type)


def corpus_clock(docs: List[Document]) -> Optional[date]:
    """'Now' for the plant = the newest evidence date in the corpus."""
    dates = [dt for dt in (_parse_date(d.date) for d in docs) if dt]
    return max(dates) if dates else None


def doc_freshness(d: Document, now: Optional[date]) -> DocFreshness:
    dtype = _doc_type(d)
    doc_date = _parse_date(d.date)

    if dtype in _EVERGREEN:
        return DocFreshness(
            doc_id=d.id, title=d.title, doc_type=dtype, date=d.date,
            age_days=(now - doc_date).days if (now and doc_date) else None,
            freshness=1.0, status="fresh",
            note="Historical record — does not expire (lesson learned / statute).",
        )
    if not doc_date or not now:
        return DocFreshness(
            doc_id=d.id, title=d.title, doc_type=dtype, date=d.date,
            age_days=None, freshness=0.5, status="aging",
            note="No reliable date on document — treat with caution.",
        )

    age = max(0, (now - doc_date).days)
    half_life = _HALF_LIFE_DAYS.get(dtype, 365)
    fresh = 0.5 ** (age / half_life)
    status = "fresh" if fresh >= 0.6 else ("aging" if fresh >= 0.3 else "stale")
    note = f"{age} days old on the corpus clock (half-life {half_life}d for {dtype})."
    return DocFreshness(doc_id=d.id, title=d.title, doc_type=dtype, date=d.date,
                        age_days=age, freshness=round(fresh, 2), status=status, note=note)


# --------------------------------------------------------------------------- #
# Conflict detectors (generic — driven by text patterns, not doc ids)
# --------------------------------------------------------------------------- #
_TRIP_RE = re.compile(r"trip[^.\n]{0,40}?(\d+(?:\.\d+)?)\s*mm/s", re.IGNORECASE)
_ALARM_RE = re.compile(r"alarm[^.\n]{0,40}?(\d+(?:\.\d+)?)\s*mm/s", re.IGNORECASE)
_ACCEPT_RE = re.compile(r"if\s*>\s*(\d+(?:\.\d+)?)\s*mm/s[^.\n]{0,60}do not accept",
                        re.IGNORECASE)
_CLOSEOUT_VIB_RE = re.compile(
    r"vibration[^.\n]{0,60}?(\d+(?:\.\d+)?)\s*mm/s", re.IGNORECASE)
_GUARD_MISSING_RE = re.compile(
    r"(not\s+reinstal?led|not\s+been\s+reinstated|guard\s+has\s+been\s+off|"
    r"guard\s+(?:removed|off)[^.\n]{0,60}(?:not|never))", re.IGNORECASE)
_GUARD_REQUIRED_RE = re.compile(
    r"(reinstate\s+the\s+coupling\s+guard|shall\s+be\s+securely\s+guarded|"
    r"guard(?:ed|ing)\s+requirement)", re.IGNORECASE)


def _setpoint_conflicts(docs: List[Document]) -> List[Conflict]:
    """Different documents stating different values for the same safety setpoint."""
    out: List[Conflict] = []
    for kind, rx, label in (("trip", _TRIP_RE, "trip setpoint"),
                            ("alarm", _ALARM_RE, "alarm setpoint")):
        seen: Dict[float, List[str]] = {}
        for d in docs:
            for m in rx.finditer(d.text):
                v = float(m.group(1))
                seen.setdefault(v, [])
                if d.id not in seen[v]:
                    seen[v].append(d.id)
        if len(seen) > 1:
            vals = sorted(seen.items())
            detail_parts = [f"{v:g} mm/s in {', '.join(ids)}" for v, ids in vals]
            doc_ids = sorted({i for _, ids in vals for i in ids})
            out.append(Conflict(
                id=f"setpoint-{kind}",
                kind="numeric_conflict",
                severity="medium",
                title=f"Vibration {label} disagrees across documents",
                detail=("The corpus states different values for the same "
                        f"{label}: " + "; ".join(detail_parts) +
                        ". Field decisions made against the wrong limit are a "
                        "safety risk — verify which value is current."),
                doc_ids=doc_ids,
                entities=["high vibration"],
            ))
    return out


def _acceptance_violations(docs: List[Document]) -> List[Conflict]:
    """A procedure sets an acceptance limit; a closed work order breaches it."""
    out: List[Conflict] = []
    limits: List[Tuple[float, Document]] = []
    for d in docs:
        for m in _ACCEPT_RE.finditer(d.text):
            limits.append((float(m.group(1)), d))
    if not limits:
        return out
    limit, sop = max(limits)  # most conservative documented limit
    for d in docs:
        if _doc_type(d) != "WorkOrder" or "closed" not in d.text.lower():
            continue
        # the LAST vibration reading in a work order is the close-out state;
        # earlier readings are the symptom that opened it
        readings = [float(m.group(1)) for m in _CLOSEOUT_VIB_RE.finditer(d.text)]
        breach = [readings[-1]] if readings and readings[-1] > limit else []
        if breach:
            out.append(Conflict(
                id=f"acceptance-{d.id}",
                kind="doc_vs_reality",
                severity="high",
                title=f"{d.id} closed in breach of the SOP acceptance limit",
                detail=(f"{sop.id} says: do not accept a job if post-job vibration "
                        f"exceeds {limit:g} mm/s — investigate alignment. "
                        f"{d.id} was closed with vibration at {max(breach):g} mm/s. "
                        "The procedure and the maintenance record contradict each "
                        "other; the job should not have been accepted."),
                doc_ids=[sop.id, d.id],
                entities=["high vibration", "misalignment"],
            ))
    return out


def _guard_conflicts(docs: List[Document]) -> List[Conflict]:
    """SOP/regulation requires guarding; the plant's own records say it's off."""
    required = [d for d in docs if _GUARD_REQUIRED_RE.search(d.text)]
    missing = [d for d in docs if _GUARD_MISSING_RE.search(d.text)]
    if not required or not missing:
        return []
    req_ids = [d.id for d in required]
    miss_ids = [d.id for d in missing]
    return [Conflict(
        id="guard-missing",
        kind="doc_vs_reality",
        severity="high",
        title="Coupling guard: required by procedure, documented as OFF",
        detail=("Guarding is mandatory per " + ", ".join(req_ids) +
                " (Factory Act Sec 21 — fencing of revolving couplings), but the "
                "plant's own records (" + ", ".join(miss_ids) + ") state the "
                "coupling guard was removed and never reinstated. The as-built "
                "reality contradicts the governing documents — equipment is "
                "running unguarded."),
        doc_ids=sorted(set(req_ids + miss_ids)),
        entities=["coupling guard"],
    )]


def _stale_drawing_conflicts(docs: List[Document],
                             fresh_map: Dict[str, DocFreshness]) -> List[Conflict]:
    """An old P&ID with newer maintenance activity on the same unit — the
    drawing may no longer reflect as-built reality."""
    out: List[Conflict] = []
    for d in docs:
        if _doc_type(d) != "P&ID":
            continue
        f = fresh_map.get(d.id)
        if not f or f.status == "fresh":
            continue
        d_date = _parse_date(d.date)
        newer = [x.id for x in docs
                 if x.unit and x.unit == d.unit and x.id != d.id
                 and _doc_type(x) in ("WorkOrder", "IncidentReport")
                 and (dt := _parse_date(x.date)) and d_date and dt > d_date]
        if newer:
            out.append(Conflict(
                id=f"stale-drawing-{d.id}",
                kind="stale_reference",
                severity="medium",
                title=f"{d.id} pre-dates {len(newer)} maintenance events on {d.unit}",
                detail=(f"The drawing is dated {d.date} (freshness "
                        f"{f.freshness:.0%}) while later records ({', '.join(newer[:5])}) "
                        "document repairs and part changes on the same unit. "
                        "Verify the drawing against as-built before using it for "
                        "isolation or modification work."),
                doc_ids=[d.id] + newer[:5],
                entities=[],
            ))
    return out


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def run_trust(kg) -> TrustReport:
    t0 = time.perf_counter()
    docs: List[Document] = kg.documents()
    now = corpus_clock(docs)

    freshness = [doc_freshness(d, now) for d in docs]
    fresh_map = {f.doc_id: f for f in freshness}

    conflicts: List[Conflict] = []
    conflicts += _guard_conflicts(docs)
    conflicts += _acceptance_violations(docs)
    conflicts += _setpoint_conflicts(docs)
    conflicts += _stale_drawing_conflicts(docs, fresh_map)
    sev_rank = {"high": 0, "medium": 1, "low": 2}
    conflicts.sort(key=lambda c: sev_rank.get(c.severity, 3))

    # corpus health: average freshness discounted by open conflicts
    avg_fresh = (sum(f.freshness for f in freshness) / len(freshness)) if freshness else 0.0
    penalty = min(0.6, sum(0.15 if c.severity == "high" else 0.07 for c in conflicts))
    health = max(0.0, min(1.0, avg_fresh * (1 - penalty)))

    return TrustReport(
        corpus_health=round(health, 2),
        conflicts=conflicts,
        freshness=sorted(freshness, key=lambda f: f.freshness),
        stale_count=sum(1 for f in freshness if f.status == "stale"),
        aging_count=sum(1 for f in freshness if f.status == "aging"),
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )


def annotate_answer(kg, citations: List[Citation],
                    report: Optional[TrustReport] = None) -> AnswerTrust:
    """Trust annotation for one answer, from the trust of its own citations."""
    rep = report or run_trust(kg)
    fresh_map = {f.doc_id: f for f in rep.freshness}
    cited_ids = [c.doc_id for c in citations]

    cited_fresh = [fresh_map[i] for i in cited_ids if i in fresh_map]
    worst = min((f.freshness for f in cited_fresh), default=1.0)
    stale_docs = [f.doc_id for f in cited_fresh if f.status == "stale"]

    warnings: List[str] = []
    for f in cited_fresh:
        if f.status == "stale":
            warnings.append(f"{f.doc_id} is stale ({f.date}) — verify before acting on it.")
    cited_set = set(cited_ids)
    for c in rep.conflicts:
        if cited_set & set(c.doc_ids):
            warnings.append(c.title)

    return AnswerTrust(freshness=round(worst, 2), stale_docs=stale_docs,
                       warnings=warnings[:4])
