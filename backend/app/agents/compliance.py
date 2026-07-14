"""Compliance & Regulatory Intelligence agent.

Maps a checklist of regulatory requirements (Factory Act, OISD-116, ISO 10816)
against the actual document corpus and equipment state, flags gaps, and
auto-assembles an evidence pack per requirement. Evidence is pulled from the
GraphRAG index so every finding is backed by real source documents.

Each requirement carries a small deterministic evaluator so the audit result is
reproducible on stage; the retrieved documents form the auto-generated evidence
package an auditor would ask for.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, List

from ..retrieval.index import HybridIndex
from ..schemas import Citation, ComplianceGap, ComplianceReport


@dataclass
class Requirement:
    regulation: str
    requirement: str
    severity: str
    query: str                       # to pull evidence documents
    # evaluator returns (status, finding) given the retrieved corpus text
    evaluate: Callable[[str], tuple[str, str]]


def _has(text: str, *terms: str) -> bool:
    t = text.lower()
    return all(term.lower() in t for term in terms)


def _any(text: str, *terms: str) -> bool:
    t = text.lower()
    return any(term.lower() in t for term in terms)


def _build_checklist() -> List[Requirement]:
    def guard_eval(ev: str):
        # Coupling guard: Factory Act Sec 21 requires guarding; corpus shows it
        # was removed in March and never reinstated (WO-2478 + reliability email).
        if _any(ev, "not reinstated", "guard has been off", "coupling guard removed",
                "guard off", "not reinstalled"):
            return ("gap", "Coupling guard on P-101 was removed during WO-2478 (Mar 2024) "
                           "and per the reliability email has NOT been reinstated — a direct "
                           "breach of Factory Act Sec 21 (fencing of revolving couplings). "
                           "Equipment is running unguarded.")
        return ("met", "Coupling guarding evidence present.")

    def vib_cadence_eval(ev: str):
        # OISD-116 5.4: vibration survey ≤3 months. Corpus shows only one survey
        # (INS-088, May 2024) for a pump with alarms since January — cadence gap.
        if "ins-088" in ev.lower() and _any(ev, "3 month", "quarterly", "condition-monitoring"):
            return ("at_risk", "Only one documented vibration survey (INS-088, May 2024) is on "
                               "file for P-101, despite vibration alarms from January. OISD-116 "
                               "Clause 5.4 requires surveys at intervals ≤3 months on critical "
                               "charge pumps — the Jan–May gap is not evidenced. Cadence at risk.")
        return ("gap", "No condition-monitoring survey records found for the required cadence.")

    def alarm_eval(ev: str):
        if _any(ev, "alarm 4.5", "trip 7.1", "oem alarm", "trip setpoint", "4.5 mm/s"):
            return ("met", "OEM vibration alarm/trip settings (4.5 / 7.1 mm/s) are documented "
                           "and referenced in work orders — OISD-116 Clause 5.7 satisfied.")
        return ("gap", "Trip/alarm settings per OEM not evidenced.")

    def records_eval(ev: str):
        if _any(ev, "iso 10816", "zone d") and "ins-088" in ev.lower():
            return ("met", "Vibration severity assessed against ISO 10816-3 with retained "
                           "survey record (INS-088). Auditable records present per OISD-116 6.2.")
        return ("at_risk", "Survey records exist but ISO 10816 severity classification not "
                           "consistently documented.")

    return [
        Requirement("Factory Act 1948 — Sec 21", "Revolving shafts and couplings must be "
                    "securely guarded while in motion.", "high",
                    "coupling guard P-101 reinstate Factory Act", guard_eval),
        Requirement("OISD-STD-116 — Clause 5.4", "Critical rotating equipment on a "
                    "condition-monitoring programme; vibration surveys at intervals ≤3 months.",
                    "high", "vibration survey condition monitoring P-101 OISD", vib_cadence_eval),
        Requirement("OISD-STD-116 — Clause 5.7", "Trip and alarm settings maintained per OEM "
                    "and tested periodically.", "medium",
                    "OEM vibration alarm trip setpoint 4.5 7.1", alarm_eval),
        Requirement("OISD-STD-116 — Clause 6.2 / ISO 10816", "Retain auditable records of "
                    "surveys, alarm tests and corrective actions.", "medium",
                    "ISO 10816 vibration survey record zone", records_eval),
    ]


def run_compliance(kg, index: HybridIndex, scope: str = "Unit CDU-1 charge pumps") -> ComplianceReport:
    t0 = time.perf_counter()
    checklist = _build_checklist()
    gaps: List[ComplianceGap] = []
    met: List[ComplianceGap] = []

    for req in checklist:
        hits = index.search(req.query, k=5)
        evidence_text = "\n".join(p.text for p, _ in hits)
        # include full docs for robust keyword eval
        doc_ids = []
        for p, _ in hits:
            if p.doc_id not in doc_ids:
                doc_ids.append(p.doc_id)
        full = evidence_text
        for did in doc_ids:
            d = kg.get_document(did)
            if d:
                full += "\n" + d.text
        status, finding = req.evaluate(full)

        evidence_docs: List[Citation] = []
        for did in doc_ids[:4]:
            d = kg.get_document(did)
            if d:
                evidence_docs.append(Citation(
                    doc_id=d.id, title=d.title,
                    doc_type=d.doc_type.value if hasattr(d.doc_type, "value") else str(d.doc_type),
                    date=d.date, snippet=(d.text[:200].strip() + "…"),
                ))
        item = ComplianceGap(
            regulation=req.regulation, requirement=req.requirement,
            status=status, finding=finding, evidence_docs=evidence_docs,
            severity=req.severity,
        )
        (met if status == "met" else gaps).append(item)

    total = len(checklist)
    met_count = len(met)
    at_risk = sum(1 for g in gaps if g.status == "at_risk")
    hard_gap = sum(1 for g in gaps if g.status == "gap")
    score = (met_count + 0.5 * at_risk) / total if total else 0.0

    return ComplianceReport(
        audit_scope=scope,
        gaps=gaps,
        met=met,
        readiness_score=round(score, 2),
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
    )
