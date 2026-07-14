# IndustryIQ — Domain-Expert Benchmark

A small evaluation set aligned to the challenge's stated evaluation focus. Each question
targets a specific capability and metric. Run them live (RCA/Copilot modes) or via
`POST /api/query`.

## Metric → capability map

| Evaluation focus (from the PS)            | How IndustryIQ demonstrates it                         |
|-------------------------------------------|--------------------------------------------------------|
| Entity-extraction accuracy across types   | Graph stats + Ingest panel (entities/relations per doc)|
| Query answer quality on expert questions  | Q1–Q8 below, checked against expected key facts        |
| Knowledge-graph linkage completeness      | `/api/graph` node/edge counts; SIBLING_OF / GOVERNED_BY|
| Time-to-answer vs traditional search      | per-answer ⚡ chip (ms) vs ~20 min manual baseline      |
| Compliance-gap detection accuracy         | `/api/compliance` — 2 true gaps, 2 met (see below)     |
| Cross-functional knowledge discovery      | Q1/Q3 retrieve links across doc *types* with no keyword |

## Benchmark questions & expected key facts

| # | Question | Mode | Must surface |
|---|----------|------|--------------|
| Q1 | Why is pump P-101 vibrating and tripping? | RCA | Root cause = misalignment/soft-foot (not bearing); cites WO-2478, INS-088, OEM-KDP-P101, **INC-2023-14** (sister pump); recommends laser alignment per SOP-CDU-07 |
| Q2 | What is the maintenance history of P-101? | Copilot | WO-2451 (Jan), WO-2478 (Mar, bearings), INS-088 (May), WO-2502 (Jun); rising vibration trend |
| Q3 | Has this failure happened on a similar pump before? | Copilot | P-102, INC-2023-14, soft foot → misalignment, 18 h downtime |
| Q4 | What are the OEM vibration alarm and trip limits for P-101? | Copilot | Alarm 4.5 mm/s, trip 7.1 mm/s (OEM-KDP-P101); current 5.8–7.2 mm/s |
| Q5 | Which equipment is connected downstream of P-101? | Copilot | E-204 (exchanger) → C-301 (column), per PID-CDU1-002 |
| Q6 | What does the OEM say to do about repeated bearing failures? | Copilot | External cause (misalignment/soft foot); investigate installation, don't just replace the bearing |
| Q7 | Is P-101 compliant with Factory Act guarding? | Copilot/Compliance | GAP — coupling guard removed in WO-2478 and not reinstated (Sec 21) |
| Q8 | What vibration-survey cadence does OISD-116 require and are we meeting it? | Compliance | ≤3 months (Clause 5.4); only INS-088 on file → cadence at risk |

## Expected compliance output (`GET /api/compliance`)
- **GAP (high):** Factory Act 1948 — Sec 21 (coupling guard removed, not reinstated).
- **AT RISK (high):** OISD-116 Clause 5.4 (vibration-survey cadence gap Jan–May).
- **MET:** OISD-116 Clause 5.7 (OEM alarm/trip documented).
- **MET:** OISD-116 Clause 6.2 / ISO 10816 (survey records + severity classification).
- Readiness score ≈ 0.62.

## Notes on scoring
- **Grounding:** every answer cites `[DOC:id]` sources; confidence reflects corroboration.
- **Determinism:** in seed/offline mode the answers are fixed, so the benchmark is
  reproducible on stage. In live mode Claude generates the same conclusions from the
  retrieved context.
- **Extend it:** add documents via the Ingest panel and add rows here to grow the set.
