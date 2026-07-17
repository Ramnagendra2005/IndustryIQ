"""Single source of truth for the synthetic industrial corpus.

Everything the demo needs is authored here so we can emit BOTH:
  * human-readable document files (for the UI document browser), and
  * a deterministic seed (ground-truth graph + copilot answers) for offline mode.

The corpus tells ONE coherent story so the copilot/RCA can "connect the dots":

    Crude charge pump P-101 in Unit CDU-1 keeps failing on bearing/vibration.
    Its identical sister pump P-102 suffered a catastrophic bearing failure in
    2023 whose root cause was coupling MISALIGNMENT / soft-foot — not a bad
    bearing. The same signature is now showing on P-101. No single team member
    sees all of: the work-order history, the inspection vibration reading, the
    OEM trip threshold, and the year-old sister-pump incident. IndustryIQ does.
"""
from __future__ import annotations

from typing import List, Optional

# A "doc" is a plain dict; kept dependency-free so scripts can import it easily.
# extraction = {"entities": [...], "relations": [...], "summary": "..."}


def E(name, type, aliases=None, description=""):
    return {"name": name, "type": type, "aliases": aliases or [], "description": description}


def R(source, target, type, evidence=""):
    return {"source": source, "target": target, "type": type, "evidence": evidence}


DOCS: List[dict] = []


def _doc(**kw):
    DOCS.append(kw)


# --------------------------------------------------------------------------- #
# 1. P&ID (image-parsed via vision in live mode; text stand-in for browser)
# --------------------------------------------------------------------------- #
_doc(
    id="PID-CDU1-002",
    title="P&ID — Crude Distillation Unit CDU-1, Charge Pump Loop",
    doc_type="P&ID",
    date="2019-04-12",
    unit="CDU-1",
    is_image=True,
    text=(
        "PIPING & INSTRUMENTATION DIAGRAM  DWG PID-CDU1-002  Rev 3\n"
        "Unit: CDU-1 Crude Distillation Unit — Charge Pump Loop\n\n"
        "Crude feed Tank T-01 --> suction header --> Pump P-101 (crude charge pump, "
        "operating) --> discharge --> Heat Exchanger E-204 (crude preheat) --> "
        "Distillation Column C-301 feed nozzle.\n"
        "Pump P-102 is an IDENTICAL spared standby pump on the same suction/discharge "
        "header, cross-tied via valve MOV-114.\n"
        "Vibration transmitter VT-101 and temperature TT-101 mounted on P-101 bearing "
        "housing. Pressure PT-204 on E-204 shell outlet.\n"
        "Instrument tags: VT-101, TT-101, PT-204, MOV-114, PSV-301 (on C-301).\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", ["Pump P-101", "crude charge pump"], "Operating crude charge pump, Unit CDU-1"),
            E("P-102", "Equipment", ["Pump P-102"], "Identical spared standby pump to P-101"),
            E("E-204", "Equipment", ["Heat Exchanger E-204"], "Crude preheat exchanger"),
            E("C-301", "Equipment", ["Column C-301"], "Distillation column"),
            E("T-01", "Equipment", ["Tank T-01"], "Crude feed tank"),
            E("VT-101", "Equipment", [], "Vibration transmitter on P-101 bearing housing"),
            E("MOV-114", "Equipment", [], "Cross-tie motor-operated valve"),
            E("CDU-1", "Location", ["Crude Distillation Unit"], "Crude distillation unit"),
        ],
        "relations": [
            R("T-01", "P-101", "CONNECTED_TO", "Tank T-01 --> suction header --> Pump P-101"),
            R("P-101", "E-204", "CONNECTED_TO", "P-101 discharge --> Heat Exchanger E-204"),
            R("E-204", "C-301", "CONNECTED_TO", "E-204 --> Distillation Column C-301 feed"),
            R("P-101", "P-102", "SIBLING_OF", "P-102 is an IDENTICAL spared standby pump"),
            R("P-101", "VT-101", "HAS_PART", "Vibration transmitter VT-101 mounted on P-101"),
            R("P-101", "CDU-1", "LOCATED_IN", "Unit: CDU-1 charge pump loop"),
            R("P-102", "CDU-1", "LOCATED_IN", "same suction/discharge header in CDU-1"),
        ],
        "summary": "Charge-pump loop: T-01→P-101→E-204→C-301, with identical standby pump P-102.",
    },
)

# --------------------------------------------------------------------------- #
# 2-4. Work order history on P-101 (spreadsheet-backed; also readable text)
# --------------------------------------------------------------------------- #
_doc(
    id="WO-2451",
    title="Work Order WO-2451 — P-101 bearing noise investigation",
    doc_type="WorkOrder",
    date="2024-01-18",
    unit="CDU-1",
    text=(
        "WORK ORDER WO-2451  Priority: P2  Unit CDU-1\n"
        "Equipment: P-101 (crude charge pump)\n"
        "Reported by: R. Menon (Shift Operator)\n"
        "Symptom: Audible bearing noise and intermittent vibration alarm on VT-101 "
        "during high-throughput operation.\n"
        "Action taken: Greased drive-end bearing, cleaned vibration probe. Vibration "
        "reduced temporarily. Recommended trending. Craft: A. Khan (Mechanical Fitter).\n"
        "Status: Closed — temporary fix. Bearing not replaced.\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", ["crude charge pump"], "Crude charge pump"),
            E("WO-2451", "Document", [], "Work order — bearing noise"),
            E("bearing wear", "FailureMode", ["bearing noise"], "Drive-end bearing degradation"),
            E("R. Menon", "Person", [], "Shift operator"),
            E("A. Khan", "Person", [], "Mechanical fitter"),
            E("VT-101", "Equipment", [], "Vibration transmitter"),
        ],
        "relations": [
            R("P-101", "bearing wear", "HAS_FAILURE", "Audible bearing noise and intermittent vibration alarm"),
            R("P-101", "A. Khan", "MAINTAINED_BY", "Craft: A. Khan (Mechanical Fitter)"),
            R("P-101", "WO-2451", "DOCUMENTED_IN", "Work Order WO-2451"),
            R("bearing wear", "2024-01-18", "OCCURRED_ON", "reported 2024-01-18"),
        ],
        "summary": "Jan 2024: P-101 bearing noise; greased only, bearing not replaced.",
    },
)

_doc(
    id="WO-2478",
    title="Work Order WO-2478 — P-101 high vibration, bearing replacement",
    doc_type="WorkOrder",
    date="2024-03-27",
    unit="CDU-1",
    text=(
        "WORK ORDER WO-2478  Priority: P1  Unit CDU-1\n"
        "Equipment: P-101 (crude charge pump)\n"
        "Symptom: High vibration trip on VT-101 (7.0 mm/s), pump tripped on protection.\n"
        "Action taken: Replaced BOTH drive-end and non-drive-end bearings (SKF 6312). "
        "Ran solo — vibration 3.9 mm/s after replacement. Coupling guard removed for "
        "access and NOT reinstalled at close-out (flagged for follow-up).\n"
        "NOTE by fitter A. Khan: 'This is the second bearing issue on P-101 in 3 months. "
        "Bearings looked spalled on the loaded side — recommend checking alignment.'\n"
        "Status: Closed. Craft: A. Khan.\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", [], "Crude charge pump"),
            E("WO-2478", "Document", [], "Work order — bearing replacement"),
            E("bearing wear", "FailureMode", ["spalled bearing"], "Bearings spalled on loaded side"),
            E("high vibration", "ProcessParameter", ["7.0 mm/s"], "Vibration trip 7.0 mm/s on VT-101"),
            E("misalignment", "FailureMode", [], "Suspected shaft/coupling misalignment"),
            E("coupling guard", "Part", [], "Removed and not reinstalled at close-out"),
            E("A. Khan", "Person", [], "Mechanical fitter"),
        ],
        "relations": [
            R("P-101", "high vibration", "HAS_PARAMETER", "High vibration trip 7.0 mm/s"),
            R("P-101", "bearing wear", "HAS_FAILURE", "Bearings spalled on loaded side"),
            R("P-101", "misalignment", "HAS_FAILURE", "recommend checking alignment"),
            R("P-101", "coupling guard", "HAS_PART", "Coupling guard removed and NOT reinstalled"),
            R("P-101", "WO-2478", "DOCUMENTED_IN", "Work Order WO-2478"),
            R("bearing wear", "2024-03-27", "OCCURRED_ON", "2024-03-27 replacement"),
        ],
        "summary": "Mar 2024: P-101 tripped at 7.0 mm/s; both bearings replaced (spalled); alignment suspected; coupling guard left off.",
    },
)

_doc(
    id="WO-2502",
    title="Work Order WO-2502 — P-101 mechanical seal weep",
    doc_type="WorkOrder",
    date="2024-06-09",
    unit="CDU-1",
    text=(
        "WORK ORDER WO-2502  Priority: P2  Unit CDU-1\n"
        "Equipment: P-101 (crude charge pump)\n"
        "Symptom: Mechanical seal weeping at drive end; small hydrocarbon drip.\n"
        "Action taken: Replaced mechanical seal cartridge. Vibration at close-out "
        "5.8 mm/s (above OEM alarm 4.5 mm/s — trending upward again since March).\n"
        "Craft: S. Reddy. Status: Closed. Follow-up: schedule laser alignment check.\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", [], "Crude charge pump"),
            E("WO-2502", "Document", [], "Work order — seal replacement"),
            E("seal leak", "FailureMode", ["seal weep"], "Mechanical seal weeping, hydrocarbon drip"),
            E("mechanical seal", "Part", [], "Seal cartridge"),
            E("high vibration", "ProcessParameter", ["5.8 mm/s"], "Vibration 5.8 mm/s at close-out, above alarm"),
            E("S. Reddy", "Person", [], "Mechanical fitter"),
        ],
        "relations": [
            R("P-101", "seal leak", "HAS_FAILURE", "Mechanical seal weeping at drive end"),
            R("P-101", "mechanical seal", "HAS_PART", "Replaced mechanical seal cartridge"),
            R("P-101", "high vibration", "HAS_PARAMETER", "vibration 5.8 mm/s, trending upward"),
            R("P-101", "WO-2502", "DOCUMENTED_IN", "Work Order WO-2502"),
            R("seal leak", "2024-06-09", "OCCURRED_ON", "2024-06-09"),
        ],
        "summary": "Jun 2024: P-101 seal weep replaced; vibration 5.8 mm/s still above OEM alarm, trending up.",
    },
)

# --------------------------------------------------------------------------- #
# 5. Inspection report (scanned form — vision in live mode)
# --------------------------------------------------------------------------- #
_doc(
    id="INS-088",
    title="Condition Monitoring Inspection INS-088 — P-101 vibration survey",
    doc_type="InspectionReport",
    date="2024-05-14",
    unit="CDU-1",
    is_image=True,
    text=(
        "CONDITION MONITORING / VIBRATION SURVEY  Report INS-088\n"
        "Asset: P-101 crude charge pump, Unit CDU-1  Analyst: P. Iyer (CAT-II)\n"
        "Overall vibration: 7.2 mm/s RMS (ISO 10816-3 Zone D — UNACCEPTABLE, above "
        "alarm 4.5 mm/s).\n"
        "Spectrum: dominant 1x and 2x running speed peaks with axial component — "
        "CLASSIC SIGNATURE OF SHAFT/COUPLING MISALIGNMENT. Bearing defect frequencies "
        "(BPFO) also present, indicating outer-race wear.\n"
        "Finding: Vibration signature consistent with misalignment driving repeat "
        "bearing damage. Recommend laser shaft alignment and soft-foot check before "
        "next bearing change. Baseplate condition to be verified.\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", [], "Crude charge pump"),
            E("INS-088", "Document", [], "Vibration survey report"),
            E("high vibration", "ProcessParameter", ["7.2 mm/s", "ISO 10816 Zone D"], "7.2 mm/s RMS, Zone D unacceptable"),
            E("misalignment", "FailureMode", ["coupling misalignment", "shaft misalignment"], "1x/2x + axial peaks — classic misalignment"),
            E("bearing wear", "FailureMode", ["outer-race wear", "BPFO"], "Bearing defect frequencies present"),
            E("soft foot", "FailureMode", [], "Baseplate soft-foot to be verified"),
            E("P. Iyer", "Person", [], "CAT-II vibration analyst"),
            E("ISO 10816", "Regulation", ["ISO 10816-3"], "Vibration severity standard"),
        ],
        "relations": [
            R("P-101", "high vibration", "HAS_PARAMETER", "Overall vibration 7.2 mm/s RMS Zone D"),
            R("P-101", "misalignment", "HAS_FAILURE", "classic signature of shaft/coupling misalignment"),
            R("P-101", "bearing wear", "HAS_FAILURE", "BPFO bearing defect frequencies present"),
            R("misalignment", "bearing wear", "CONNECTED_TO", "misalignment driving repeat bearing damage"),
            R("P-101", "soft foot", "HAS_FAILURE", "soft-foot check recommended"),
            R("P-101", "INS-088", "DOCUMENTED_IN", "Report INS-088"),
            R("P-101", "ISO 10816", "GOVERNED_BY", "ISO 10816-3 Zone D assessment"),
            R("high vibration", "2024-05-14", "OCCURRED_ON", "survey 2024-05-14"),
        ],
        "summary": "May 2024: INS-088 finds 7.2 mm/s Zone-D vibration; spectrum = MISALIGNMENT driving repeat bearing wear; recommends laser alignment + soft-foot check.",
    },
)

# --------------------------------------------------------------------------- #
# 6. OEM manual excerpt
# --------------------------------------------------------------------------- #
_doc(
    id="OEM-KDP-P101",
    title="OEM Manual — Kirloskar KDP-300 Centrifugal Pump (P-101/P-102)",
    doc_type="OEMManual",
    date="2018-01-01",
    unit="CDU-1",
    text=(
        "KIRLOSKAR KDP-300 CENTRIFUGAL PUMP — OPERATION & MAINTENANCE MANUAL\n"
        "Applies to tags P-101 and P-102 (identical units).\n\n"
        "Vibration limits (bearing housing, RMS velocity): ALARM 4.5 mm/s, TRIP 7.1 mm/s.\n"
        "Shaft alignment: cold parallel/angular offset must be within 0.05 mm; excessive "
        "misalignment is the leading cause of premature bearing and seal failure.\n"
        "Baseplate: check for soft foot at every coupling service; foot deflection > 0.05 mm "
        "must be corrected — soft foot induces frame distortion and misalignment.\n"
        "Bearing: SKF 6312 C3, rated L10 life 40,000 h at design load. Repeated short bearing "
        "life indicates an external cause (misalignment, soft foot, unbalance), NOT bearing "
        "quality — investigate the installation, do not simply replace the bearing.\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", [], "KDP-300 pump"),
            E("P-102", "Equipment", [], "KDP-300 pump (identical)"),
            E("OEM-KDP-P101", "Document", ["KDP-300 manual"], "OEM O&M manual"),
            E("vibration trip", "ProcessParameter", ["7.1 mm/s", "alarm 4.5 mm/s"], "Alarm 4.5 / Trip 7.1 mm/s"),
            E("misalignment", "FailureMode", [], "Leading cause of premature bearing/seal failure"),
            E("soft foot", "FailureMode", [], "Foot deflection >0.05mm induces misalignment"),
            E("SKF 6312", "Part", ["bearing"], "L10 life 40,000h"),
        ],
        "relations": [
            R("P-101", "vibration trip", "HAS_PARAMETER", "ALARM 4.5 mm/s, TRIP 7.1 mm/s"),
            R("P-101", "OEM-KDP-P101", "DOCUMENTED_IN", "OEM manual applies to P-101"),
            R("P-102", "OEM-KDP-P101", "DOCUMENTED_IN", "OEM manual applies to P-102"),
            R("misalignment", "bearing wear", "CONNECTED_TO", "misalignment is leading cause of bearing failure"),
            R("soft foot", "misalignment", "CONNECTED_TO", "soft foot induces misalignment"),
            R("P-101", "SKF 6312", "HAS_PART", "Bearing SKF 6312 C3"),
        ],
        "summary": "OEM: alarm 4.5 / trip 7.1 mm/s; repeated short bearing life = external cause (misalignment/soft foot) — investigate installation, don't just replace bearing.",
    },
)

# --------------------------------------------------------------------------- #
# 7. Sister-pump incident report (the KEY cross-document link)
# --------------------------------------------------------------------------- #
_doc(
    id="INC-2023-14",
    title="Incident Report INC-2023-14 — P-102 catastrophic bearing failure",
    doc_type="IncidentReport",
    date="2023-08-22",
    unit="CDU-1",
    text=(
        "INCIDENT / FAILURE REPORT  INC-2023-14  Unit CDU-1\n"
        "Equipment: P-102 (crude charge pump, sister to P-101)\n"
        "Event: Catastrophic drive-end bearing seizure leading to shaft damage; pump "
        "removed from service. Unplanned downtime 18 hours; standby unavailable so "
        "throughput cut 30%.\n"
        "ROOT CAUSE ANALYSIS (5-Why): repeat bearing failures -> bearings running hot -> "
        "coupling MISALIGNMENT -> baseplate SOFT FOOT (0.09 mm) never corrected since "
        "installation -> commissioning alignment accepted out of tolerance.\n"
        "Root cause: uncorrected baseplate soft foot causing chronic coupling misalignment.\n"
        "Corrective action: shimmed baseplate, laser-aligned coupling to 0.02 mm, added "
        "soft-foot check to PM. Lesson learned: treat repeat bearing failures on KDP-300 "
        "pumps as MISALIGNMENT until proven otherwise — do not just replace bearings.\n"
    ),
    extraction={
        "entities": [
            E("P-102", "Equipment", [], "Sister crude charge pump"),
            E("P-101", "Equipment", [], "Sister crude charge pump"),
            E("INC-2023-14", "Document", [], "Incident report"),
            E("bearing wear", "FailureMode", ["bearing seizure"], "Catastrophic bearing seizure"),
            E("misalignment", "FailureMode", ["coupling misalignment"], "Chronic coupling misalignment"),
            E("soft foot", "FailureMode", [], "Uncorrected baseplate soft foot 0.09mm — root cause"),
            E("unplanned downtime", "ProcessParameter", ["18 hours"], "18h downtime, 30% throughput cut"),
        ],
        "relations": [
            R("P-102", "bearing wear", "HAS_FAILURE", "Catastrophic drive-end bearing seizure"),
            R("P-102", "misalignment", "HAS_FAILURE", "coupling misalignment"),
            R("P-102", "soft foot", "HAS_FAILURE", "baseplate soft foot 0.09mm"),
            R("soft foot", "misalignment", "CONNECTED_TO", "soft foot causing chronic misalignment"),
            R("misalignment", "bearing wear", "CONNECTED_TO", "misalignment -> bearings running hot -> failure"),
            R("P-102", "P-101", "SIBLING_OF", "sister to P-101"),
            R("P-102", "INC-2023-14", "DOCUMENTED_IN", "INC-2023-14"),
            R("bearing wear", "2023-08-22", "OCCURRED_ON", "2023-08-22"),
        ],
        "summary": "Aug 2023: sister pump P-102 catastrophic bearing failure; RCA root cause = baseplate SOFT FOOT → misalignment. 18h downtime. Lesson: treat repeat bearing failures as misalignment.",
    },
)

# --------------------------------------------------------------------------- #
# 8. SOP
# --------------------------------------------------------------------------- #
_doc(
    id="SOP-CDU-07",
    title="SOP-CDU-07 — Charge Pump Changeover & Alignment Procedure",
    doc_type="SOP",
    date="2022-11-01",
    unit="CDU-1",
    text=(
        "STANDARD OPERATING PROCEDURE  SOP-CDU-07  Rev 2\n"
        "Title: Crude Charge Pump (P-101/P-102) Changeover, Bearing Service & Alignment.\n"
        "Scope: applies to KDP-300 pumps in CDU-1. References OISD-STD-116 (rotating "
        "equipment) and the KDP-300 OEM manual.\n"
        "Key steps: 4.3 Before returning a pump to service after ANY bearing or seal "
        "job, perform laser shaft alignment (tolerance 0.05 mm) AND a soft-foot check. "
        "4.7 Reinstate the coupling guard before start-up (Factory Act guarding "
        "requirement). 4.9 Record post-job vibration; if > 4.5 mm/s, do not accept the "
        "job — investigate alignment.\n"
    ),
    extraction={
        "entities": [
            E("SOP-CDU-07", "Procedure", [], "Charge pump alignment & changeover SOP"),
            E("P-101", "Equipment", [], "Charge pump"),
            E("P-102", "Equipment", [], "Charge pump"),
            E("coupling guard", "Part", [], "Must be reinstated before start-up"),
            E("OISD-STD-116", "Regulation", ["OISD 116"], "Rotating equipment standard"),
            E("Factory Act", "Regulation", ["Factory Act 1948"], "Guarding requirement"),
            E("misalignment", "FailureMode", [], "Alignment tolerance 0.05mm"),
        ],
        "relations": [
            R("SOP-CDU-07", "P-101", "PROCEDURE_FOR", "applies to P-101"),
            R("SOP-CDU-07", "P-102", "PROCEDURE_FOR", "applies to P-102"),
            R("SOP-CDU-07", "OISD-STD-116", "GOVERNED_BY", "References OISD-STD-116"),
            R("SOP-CDU-07", "Factory Act", "GOVERNED_BY", "coupling guard Factory Act requirement"),
            R("P-101", "coupling guard", "HAS_PART", "Reinstate coupling guard before start-up"),
        ],
        "summary": "SOP-CDU-07: mandatory laser alignment + soft-foot check after any bearing/seal job; reinstate coupling guard (Factory Act); reject job if vibration >4.5 mm/s.",
    },
)

# --------------------------------------------------------------------------- #
# 9-10. Regulations
# --------------------------------------------------------------------------- #
_doc(
    id="REG-FACTORYACT",
    title="Factory Act 1948 — Applicable Safety Provisions (extract)",
    doc_type="RegulatoryDocument",
    date="1948-01-01",
    unit="Plant",
    text=(
        "THE FACTORIES ACT, 1948 — extract of provisions relevant to rotating equipment.\n"
        "Section 21: Fencing of machinery — every dangerous moving part, including "
        "revolving shafts and couplings, shall be securely GUARDED while in motion.\n"
        "Section 28: Hoists and lifts — thorough examination by competent person at "
        "least once every 6 months.\n"
        "Section 7A: General duty of occupier to ensure health, safety and welfare.\n"
        "Compliance evidence required: guarding inspection records, competent-person "
        "certificates.\n"
    ),
    extraction={
        "entities": [
            E("Factory Act", "Regulation", ["Factories Act 1948", "Section 21"], "Guarding of moving parts"),
            E("coupling guard", "Part", [], "Couplings must be securely guarded (Sec 21)"),
            E("REG-FACTORYACT", "Document", [], "Factory Act extract"),
        ],
        "relations": [
            R("Factory Act", "coupling guard", "GOVERNED_BY", "Section 21: couplings shall be securely guarded"),
            R("Factory Act", "REG-FACTORYACT", "DOCUMENTED_IN", "Factory Act extract"),
        ],
        "summary": "Factory Act Sec 21: revolving shafts/couplings must be guarded in motion; evidence = guarding inspection records.",
    },
)

_doc(
    id="REG-OISD116",
    title="OISD-STD-116 — Fire Protection & Rotating Equipment (extract)",
    doc_type="RegulatoryDocument",
    date="2018-01-01",
    unit="Plant",
    text=(
        "OISD-STD-116 — extract on rotating equipment integrity.\n"
        "Clause 5.4: Critical rotating equipment (charge pumps, compressors) shall be on "
        "a condition-monitoring programme with vibration surveys at intervals not "
        "exceeding 3 months.\n"
        "Clause 5.7: Trip and alarm settings shall be maintained per OEM and tested "
        "periodically.\n"
        "Clause 6.2: Records of surveys, alarm tests and corrective actions shall be "
        "retained and auditable.\n"
    ),
    extraction={
        "entities": [
            E("OISD-STD-116", "Regulation", ["OISD 116"], "Rotating equipment integrity standard"),
            E("high vibration", "ProcessParameter", [], "Vibration surveys ≤3 months"),
            E("REG-OISD116", "Document", [], "OISD-116 extract"),
            E("P-101", "Equipment", [], "Critical charge pump"),
        ],
        "relations": [
            R("P-101", "OISD-STD-116", "GOVERNED_BY", "Critical charge pumps on condition-monitoring programme"),
            R("OISD-STD-116", "REG-OISD116", "DOCUMENTED_IN", "OISD-116 extract"),
        ],
        "summary": "OISD-116: critical pumps need vibration surveys ≤3 months; trip/alarm per OEM; auditable records.",
    },
)

# --------------------------------------------------------------------------- #
# 11. Email archive (unstructured)
# --------------------------------------------------------------------------- #
_doc(
    id="EMAIL-P101-TREND",
    title="Email — P-101 vibration trend concern (Reliability → Maintenance)",
    doc_type="Email",
    date="2024-06-20",
    unit="CDU-1",
    text=(
        "From: p.iyer@refinery.example (Reliability)\n"
        "To: maint.planner@refinery.example; cdu1.super@refinery.example\n"
        "Date: 2024-06-20\nSubject: P-101 vibration creeping up again — please schedule alignment\n\n"
        "Team, since the March bearing change (WO-2478) P-101 vibration has climbed back "
        "to ~5.8 mm/s (WO-2502) and my May survey INS-088 shows a misalignment "
        "signature. This is the SAME pattern that killed P-102 last year (INC-2023-14, "
        "soft foot). Please do NOT just swap the bearing again — we need a laser "
        "alignment + soft-foot check per SOP-CDU-07. Also the coupling guard has been "
        "off since March, which is a Factory Act issue. — Priya\n"
    ),
    extraction={
        "entities": [
            E("P-101", "Equipment", [], "Crude charge pump"),
            E("P-102", "Equipment", [], "Sister pump"),
            E("EMAIL-P101-TREND", "Document", [], "Reliability email"),
            E("misalignment", "FailureMode", [], "Misalignment signature"),
            E("coupling guard", "Part", [], "Off since March — Factory Act issue"),
            E("P. Iyer", "Person", ["Priya"], "Reliability engineer"),
            E("SOP-CDU-07", "Procedure", [], "Alignment procedure"),
        ],
        "relations": [
            R("P-101", "misalignment", "HAS_FAILURE", "May survey shows misalignment signature"),
            R("P-101", "P-102", "SIBLING_OF", "same pattern that killed P-102"),
            R("P-101", "coupling guard", "HAS_PART", "coupling guard off since March — Factory Act issue"),
            R("P-101", "EMAIL-P101-TREND", "DOCUMENTED_IN", "email"),
        ],
        "summary": "Jun 2024 email: reliability warns P-101 repeating P-102's misalignment/soft-foot pattern; asks for alignment not another bearing swap; flags coupling guard off (Factory Act).",
    },
)


# --------------------------------------------------------------------------- #
# Seeded copilot answers (offline mode). Live mode generates these instead.
# Keyed by an id; matched to questions by trigger keyword overlap.
# --------------------------------------------------------------------------- #
SEED_ANSWERS = {
    "rca_p101": {
        "triggers": [
            "why is p-101 vibrating", "p-101 tripping", "root cause p-101",
            "p-101 bearing failing", "what is wrong with p-101", "p-101 vibration",
            "rca p-101", "diagnose p-101",
        ],
        "answer": (
            "**Most likely root cause: coupling MISALIGNMENT driven by baseplate soft foot — "
            "not a bad bearing.** P-101 should be laser-aligned and soft-foot-checked before "
            "another bearing is fitted.\n\n"
            "Connecting the dots across the corpus:\n"
            "• P-101 has had 3 failures in 6 months — bearing noise [DOC:WO-2451], a high-"
            "vibration trip with spalled bearings [DOC:WO-2478], and a seal weep [DOC:WO-2502]. "
            "Vibration has climbed back to 5.8 mm/s, above the OEM 4.5 mm/s alarm.\n"
            "• The May vibration survey [DOC:INS-088] reads 7.2 mm/s (ISO 10816 Zone D) with a "
            "1x/2x + axial spectrum — a *classic misalignment signature* driving the repeat "
            "bearing wear.\n"
            "• The OEM manual [DOC:OEM-KDP-P101] states repeated short bearing life on the "
            "KDP-300 indicates an external cause (misalignment/soft foot) and says NOT to just "
            "replace the bearing.\n"
            "• Its identical sister pump P-102 failed catastrophically in 2023 [DOC:INC-2023-14] "
            "— RCA root cause was baseplate **soft foot (0.09 mm) → chronic coupling "
            "misalignment**, causing 18 h of unplanned downtime.\n\n"
            "**Recommended action (per [DOC:SOP-CDU-07]):** perform laser shaft alignment to "
            "0.05 mm and a soft-foot check, shim the baseplate if needed, then trend vibration — "
            "do not simply swap the bearing. Also reinstate the coupling guard removed in "
            "March (Factory Act Sec 21)."
        ),
    },
    "history_p101": {
        "triggers": ["maintenance history p-101", "work orders p-101", "past work p-101",
                     "history of p-101", "what happened to p-101"],
        "answer": (
            "P-101 maintenance history (last 6 months):\n"
            "• Jan 2024 — bearing noise, greased only, bearing not replaced [DOC:WO-2451].\n"
            "• Mar 2024 — high-vibration trip at 7.0 mm/s; both bearings replaced (spalled); "
            "fitter flagged alignment; coupling guard left off [DOC:WO-2478].\n"
            "• May 2024 — vibration survey 7.2 mm/s, Zone D, misalignment signature [DOC:INS-088].\n"
            "• Jun 2024 — mechanical seal weep replaced; vibration still 5.8 mm/s [DOC:WO-2502].\n"
            "The recurring theme is bearing distress with a rising vibration trend pointing to "
            "misalignment — the same failure mode that destroyed sister pump P-102 [DOC:INC-2023-14]."
        ),
    },
    "sister": {
        "triggers": ["sister pump", "p-102", "similar failure", "has this happened before",
                     "identical pump", "seen this before"],
        "answer": (
            "Yes — this exact pattern has occurred before on the identical sister pump **P-102**. "
            "In August 2023 [DOC:INC-2023-14] P-102 suffered a catastrophic drive-end bearing "
            "seizure. The 5-Why RCA traced it to an uncorrected baseplate **soft foot (0.09 mm)** "
            "causing chronic coupling **misalignment**, which cooked the bearings. It cost 18 hours "
            "of unplanned downtime and a 30% throughput cut. The documented lesson learned was to "
            "treat repeat bearing failures on these KDP-300 pumps as misalignment until proven "
            "otherwise. P-101 [DOC:INS-088] is now showing the same misalignment signature."
        ),
    },
    "vibration_limit": {
        "triggers": ["vibration limit p-101", "alarm setpoint", "trip setpoint", "oem vibration",
                     "what is the vibration limit", "vibration threshold"],
        "answer": (
            "For the KDP-300 pumps (P-101/P-102) the OEM bearing-housing vibration limits are "
            "**alarm 4.5 mm/s and trip 7.1 mm/s** RMS velocity [DOC:OEM-KDP-P101]. P-101 is "
            "currently at 5.8 mm/s (above alarm) [DOC:WO-2502] and hit 7.2 mm/s during the May "
            "survey [DOC:INS-088] — i.e. into the trip region and ISO 10816 Zone D (unacceptable)."
        ),
    },
    "downstream_p101": {
        "triggers": ["connected downstream of p-101", "downstream equipment",
                     "what is connected to p-101", "p-101 discharge", "process flow p-101",
                     "upstream downstream"],
        "answer": (
            "Per the CDU-1 charge-pump-loop P&ID [DOC:PID-CDU1-002], the flow path from P-101 is:\n"
            "• **Tank T-01** (crude feed) → suction header → **Pump P-101** → discharge →\n"
            "• **Heat Exchanger E-204** (crude preheat) →\n"
            "• **Distillation Column C-301** feed nozzle.\n\n"
            "The identical standby pump **P-102** shares the same suction/discharge header, "
            "cross-tied via valve MOV-114 — so a P-101 outage puts the full unit load on P-102. "
            "Instrumentation on the loop: VT-101 (vibration) and TT-101 (temperature) on the "
            "P-101 bearing housing, PT-204 on the E-204 shell outlet, PSV-301 on C-301."
        ),
    },
    "oem_bearing_advice": {
        "triggers": ["repeated bearing failures", "oem say about bearing", "bearing keeps failing",
                     "short bearing life", "replace the bearing again", "bearing recommendation"],
        "answer": (
            "The OEM manual is explicit [DOC:OEM-KDP-P101]: **repeated short bearing life on the "
            "KDP-300 indicates an external cause — misalignment, soft foot or unbalance — NOT "
            "bearing quality.** The instruction is to investigate the installation, not simply "
            "replace the bearing.\n\n"
            "Specifically it requires: shaft alignment within **0.05 mm** cold parallel/angular "
            "offset (excessive misalignment is the leading cause of premature bearing and seal "
            "failure), and a **soft-foot check at every coupling service** — foot deflection over "
            "0.05 mm must be corrected. The fitted bearing is an SKF 6312 C3 rated for 40,000 h "
            "L10 life; P-101's bearings lasted ~2 months after the March change [DOC:WO-2478], "
            "which by the OEM's own criterion points at the installation, matching the "
            "misalignment signature in the May survey [DOC:INS-088]."
        ),
    },
    "oisd_cadence": {
        "triggers": ["vibration survey cadence", "oisd-116 require", "survey interval",
                     "condition monitoring programme", "how often vibration survey",
                     "are we meeting oisd"],
        "answer": (
            "**OISD-STD-116 Clause 5.4 requires vibration surveys at intervals not exceeding "
            "3 months** for critical rotating equipment such as charge pumps [DOC:REG-OISD116].\n\n"
            "We are **at risk of non-compliance**: the only formal survey on file for P-101 is the "
            "May 2024 survey [DOC:INS-088]. Between the January bearing-noise work order "
            "[DOC:WO-2451] and that May survey there is a ~4-month gap with no documented survey, "
            "and no survey is scheduled since. Clause 6.2 also requires survey records to be "
            "retained and auditable — the evidence pack for an audit is currently incomplete. "
            "Recommended: put P-101/P-102 on a fixed quarterly survey schedule and log it against "
            "the condition-monitoring programme."
        ),
    },
}
