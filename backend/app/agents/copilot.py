"""Copilot & RCA agents — answer generation over GraphRAG retrieval.

Both share the same retrieval + answering pipeline; RCA just steers the model
harder toward connecting failure evidence across documents and stating a root
cause + recommended action.
"""
from __future__ import annotations

import re
import time
from typing import List

from ..llm import ANSWER_SYSTEM, BaseLLM
from ..retrieval.graphrag import GraphRAG, RetrievalResult
from ..schemas import Citation, QueryResponse

_RCA_SYSTEM = ANSWER_SYSTEM + (
    "\n\nThis is a ROOT CAUSE ANALYSIS request. Fuse work-order history, inspection "
    "findings, OEM limits, real-time readings and past incidents on sibling equipment. "
    "State the single most likely ROOT CAUSE, the evidence trail that supports it "
    "(citing each document), and a concrete recommended corrective action referencing "
    "the relevant SOP. Prefer the systemic cause over the symptom (e.g. misalignment "
    "over 'bad bearing') when the evidence supports it."
)

# Field technicians often don't work in English. The corpus stays English, but
# the ANSWER is delivered in the technician's language — with equipment tags,
# [DOC:id] citations and numeric values kept verbatim so nothing safety-critical
# is lost in translation.
_LANG_NAMES = {
    "hi": "Hindi (Devanagari script)",
    "te": "Telugu",
    "ta": "Tamil",
    "kn": "Kannada",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
}


def _lang_instruction(lang: str) -> str:
    name = _LANG_NAMES.get(lang)
    if not name:
        return ""
    return (
        f"\n\nIMPORTANT: Write the entire answer in {name}, as spoken by plant "
        "technicians (natural, spoken register — not literary). Keep equipment tags "
        "(P-101), instrument tags (VT-101), document citations like [DOC:WO-2478], "
        "numeric values and units (mm/s) EXACTLY as they are — never translate or "
        "transliterate those."
    )


def _confidence(res: RetrievalResult, answer: str) -> float:
    """Heuristic 0..1 confidence from retrieval + corroboration + grounding."""
    n_docs = len(res.citations)
    cited = set(re.findall(r"\[DOC:([A-Za-z0-9\-]+)\]", answer))
    corroboration = min(len(cited), 4) / 4.0
    breadth = min(n_docs, 5) / 5.0
    graph_bonus = 0.15 if res.graph_paths else 0.0
    focus_bonus = 0.1 if res.focus_entities else 0.0
    hedged = any(p in answer.lower() for p in
                 ["could not find", "insufficient", "not enough", "cannot"])
    score = 0.35 * breadth + 0.4 * corroboration + graph_bonus + focus_bonus
    if hedged:
        score *= 0.5
    return round(max(0.05, min(0.98, score)), 2)


def _filter_citations(citations: List[Citation], answer: str) -> List[Citation]:
    """Prefer citations the answer actually references; keep order, fall back to all."""
    cited = set(re.findall(r"\[DOC:([A-Za-z0-9\-]+)\]", answer))
    if not cited:
        return citations
    ranked = [c for c in citations if c.doc_id in cited]
    extra = [c for c in citations if c.doc_id not in cited]
    return ranked + extra


def run_copilot(kg, index, llm: BaseLLM, question: str, mode: str = "copilot",
                lang: str = "en") -> QueryResponse:
    t0 = time.perf_counter()
    graphrag = GraphRAG(kg, index)
    res = graphrag.retrieve(question, k=6, expand_radius=2)

    system = _RCA_SYSTEM if mode == "rca" else ANSWER_SYSTEM
    if llm.live:  # seed answers are authored in English; only live mode translates
        system += _lang_instruction(lang)
    if res.context.strip():
        answer = llm.answer(system, question, res.context)
    else:
        answer = ("I couldn't find anything in the plant corpus related to that. "
                  "Try naming an equipment tag (e.g. P-101) or ingest more documents.")

    conf = _confidence(res, answer)
    citations = _filter_citations(res.citations, answer)
    return QueryResponse(
        answer=answer,
        confidence=conf,
        citations=citations,
        graph_paths=res.graph_paths,
        focus_entities=res.focus_entities,
        elapsed_ms=int((time.perf_counter() - t0) * 1000),
        mode=mode,
    )
