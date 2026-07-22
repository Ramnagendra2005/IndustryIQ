"""GraphRAG: fuse vector retrieval with knowledge-graph traversal.

Plain RAG retrieves passages that lexically/semantically match the query. That
misses the cross-document links that make industrial knowledge valuable — e.g.
a symptom on P-101 whose explanation lives in a year-old incident report on its
sister pump P-102, which shares no query keywords.

GraphRAG fixes this:
  1. vector/lexical retrieve seed passages         (index.HybridIndex)
  2. identify focus entities (query tags + seeds)  (graph resolution)
  3. EXPAND along graph edges to pull in connected docs no keyword would find
  4. assemble a context bundle + citation set + the graph paths that connect
     the focus entities (the "connect the dots" evidence)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from ..graph.store import KnowledgeGraph
from ..schemas import Citation, GraphPathHop
from .index import HybridIndex


@dataclass
class RetrievalResult:
    context: str
    citations: List[Citation]
    focus_entities: List[str]
    graph_paths: List[GraphPathHop]
    seed_doc_ids: List[str] = field(default_factory=list)
    expanded_doc_ids: List[str] = field(default_factory=list)


_TAG_RE = re.compile(r"\b[A-Za-z]{1,3}-\d{2,4}[A-Za-z]?\b")


class GraphRAG:
    def __init__(self, kg: KnowledgeGraph, index: HybridIndex) -> None:
        self.kg = kg
        self.index = index

    def _focus_from_query(self, query: str) -> List[str]:
        """Resolve entities the query mentions, by tag and by name/alias match."""
        found: List[str] = []
        for tag in _TAG_RE.findall(query):
            k = self.kg.resolve(tag)
            if k and k not in found:
                found.append(k)
        ql = query.lower()
        for key, data in self.kg.g.nodes(data=True):
            label = data.get("label", "")
            if len(label) >= 4 and label.lower() in ql and key not in found:
                found.append(key)
        return found

    def retrieve(self, query: str, k: int = 6, expand_radius: int = 2) -> RetrievalResult:
        # 0. out-of-corpus gate: unless the query names a known entity, require
        # a minimum absolute semantic match so off-topic questions come back
        # empty instead of dragging in the top-k-by-rank passages. The threshold
        # is provider-calibrated and returned alongside the cosine (the embedder
        # can differ per query when a live call falls back to static).
        if not self._focus_from_query(query):
            cosine, threshold = self.index.max_cosine(query)
            if cosine < threshold:
                return RetrievalResult(context="", citations=[],
                                       focus_entities=[], graph_paths=[])

        # 1. vector/lexical seeds
        hits = self.index.search(query, k=k)
        seed_doc_ids: List[str] = []
        for p, _ in hits:
            if p.doc_id not in seed_doc_ids:
                seed_doc_ids.append(p.doc_id)

        # 2. focus entities: from query + from entities in the seed docs
        focus = self._focus_from_query(query)
        for did in seed_doc_ids:
            for key, data in self.kg.g.nodes(data=True):
                if did in data.get("docs", set()) and data.get("type") == "Equipment":
                    if key not in focus:
                        focus.append(key)
        focus = focus[:6]

        # 3. graph expansion: pull in docs attached to the neighborhood of focus
        expanded_keys: set[str] = set()
        for f in focus:
            expanded_keys |= self.kg.neighbors(f, radius=expand_radius)
        expanded_doc_ids = [d for d in self.kg.docs_for_entities(expanded_keys)
                            if d not in seed_doc_ids]

        all_doc_ids = seed_doc_ids + expanded_doc_ids

        # 4. assemble context + citations
        context_parts: List[str] = []
        citations: List[Citation] = []
        for did in all_doc_ids:
            doc = self.kg.get_document(did)
            if not doc:
                continue
            tag = "SEED" if did in seed_doc_ids else "GRAPH-LINKED"
            context_parts.append(
                f"[DOC:{doc.id}] ({tag}) {doc.title} — {doc.doc_type.value if hasattr(doc.doc_type,'value') else doc.doc_type}"
                f" ({doc.date or 'n/a'})\n{doc.text.strip()}"
            )
            citations.append(Citation(
                doc_id=doc.id, title=doc.title,
                doc_type=doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
                date=doc.date,
                snippet=_snippet(doc.text, query),
            ))

        # graph paths connecting the focus entities — the evidence trail
        graph_paths = self.kg.connecting_paths([self.kg.label(f) for f in focus], cutoff=3)
        flat_paths, seen_hops = [], set()
        for path in graph_paths:
            for hop in path:
                sig = (hop.source, hop.relation, hop.target)
                if sig not in seen_hops:
                    seen_hops.add(sig)
                    flat_paths.append(hop)

        return RetrievalResult(
            context="\n\n".join(context_parts),
            citations=citations,
            focus_entities=[self.kg.label(f) for f in focus],
            graph_paths=flat_paths[:20],
            seed_doc_ids=seed_doc_ids,
            expanded_doc_ids=expanded_doc_ids,
        )


def _snippet(text: str, query: str, width: int = 220) -> str:
    q_terms = [t for t in re.findall(r"[a-z0-9-]+", query.lower()) if len(t) > 2]
    low = text.lower()
    pos = -1
    for t in q_terms:
        pos = low.find(t)
        if pos != -1:
            break
    if pos == -1:
        return text[:width].strip()
    start = max(0, pos - width // 3)
    return ("…" if start > 0 else "") + text[start:start + width].strip() + "…"
