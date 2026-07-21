"""Unified knowledge graph over the whole document corpus.

Backed by NetworkX (in-memory, JSON-persistable) so the demo has zero infra
dependencies. The API is deliberately Neo4j-shaped (nodes, typed edges, path
queries) so the pitch can say "swap NetworkX for Neo4j to scale" truthfully.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import networkx as nx

from ..schemas import Document, Extraction, GraphPathHop


def _norm(name: str) -> str:
    return " ".join(name.strip().lower().split())


class KnowledgeGraph:
    def __init__(self) -> None:
        self.g = nx.MultiDiGraph()
        self._alias: Dict[str, str] = {}          # normalized alias -> canonical key
        self._documents: Dict[str, Document] = {}  # doc_id -> Document

    # ------------------------------------------------------------------ #
    # Building
    # ------------------------------------------------------------------ #
    def _resolve_key(self, name: str) -> Optional[str]:
        return self._alias.get(_norm(name))

    def resolve(self, name: str) -> Optional[str]:
        """Return the canonical node key for a name/alias, if known."""
        return self._resolve_key(name)

    def add_entity(self, name: str, type: str, aliases: Optional[Iterable[str]] = None,
                   description: str = "", doc_id: Optional[str] = None) -> str:
        key = self._resolve_key(name) or name
        norm = _norm(name)
        if key not in self.g:
            self.g.add_node(key, type=type, label=name, description=description,
                            docs=set(), mentions=0)
        node = self.g.nodes[key]
        node["mentions"] += 1
        if description and len(description) > len(node.get("description", "")):
            node["description"] = description
        if type and node.get("type") in (None, "Document") and type != "Document":
            node["type"] = type
        self._alias[norm] = key
        for a in aliases or []:
            self._alias[_norm(a)] = key
        if doc_id:
            node["docs"].add(doc_id)
        return key

    def add_relation(self, source: str, target: str, type: str, evidence: str = "",
                     doc_id: Optional[str] = None) -> None:
        s = self._resolve_key(source) or self.add_entity(source, "Equipment")
        t = self._resolve_key(target) or self.add_entity(target, "Equipment")
        if s == t:
            return
        self.g.add_edge(s, t, key=type, type=type, evidence=evidence, doc_id=doc_id)

    def add_document(self, doc: Document) -> None:
        self._documents[doc.id] = doc

    def ingest_extraction(self, doc: Document, extraction: Extraction) -> None:
        """Fold one document's extraction into the graph."""
        self.add_document(doc)
        for e in extraction.entities:
            self.add_entity(e.name, e.type.value if hasattr(e.type, "value") else str(e.type),
                            e.aliases, e.description, doc_id=doc.id)
        for r in extraction.relations:
            self.add_relation(r.source, r.target,
                              r.type.value if hasattr(r.type, "value") else str(r.type),
                              r.evidence, doc_id=doc.id)

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def documents(self) -> List[Document]:
        return list(self._documents.values())

    def get_document(self, doc_id: str) -> Optional[Document]:
        return self._documents.get(doc_id)

    def neighbors(self, key: str, radius: int = 1) -> set[str]:
        """Undirected neighborhood within `radius` hops."""
        if key not in self.g:
            return set()
        ug = self.g.to_undirected(as_view=True)
        seen = {key}
        frontier = {key}
        for _ in range(radius):
            nxt = set()
            for n in frontier:
                nxt |= set(ug.neighbors(n))
            frontier = nxt - seen
            seen |= nxt
        return seen

    def docs_for_entities(self, keys: Iterable[str]) -> List[str]:
        out: List[str] = []
        for k in keys:
            if k in self.g:
                for d in self.g.nodes[k].get("docs", set()):
                    if d not in out:
                        out.append(d)
        return out

    def node_view(self, key: str) -> Optional[dict]:
        """Resolved snapshot of one node (type/label/description/docs), or None."""
        k = self._resolve_key(key) or (key if key in self.g else None)
        if not k or k not in self.g:
            return None
        n = self.g.nodes[k]
        return {
            "key": k,
            "label": n.get("label", k),
            "type": n.get("type", "Unknown"),
            "description": n.get("description", ""),
            "mentions": n.get("mentions", 1),
            "docs": sorted(n.get("docs", set())),
        }

    def relations_of(self, key: str) -> List[dict]:
        """Every typed edge touching `key`, normalized to a direction-aware view.

        Each item: {relation, direction ('out'|'in'), other (canonical key),
        label, type (of the other node), evidence, doc_id}. Direction lets the
        dossier tell "P-101 CONNECTED_TO E-204" (downstream) apart from
        "T-01 CONNECTED_TO P-101" (upstream) even though both touch P-101.
        """
        k = self._resolve_key(key) or (key if key in self.g else None)
        if not k or k not in self.g:
            return []
        out: List[dict] = []
        seen: set[tuple] = set()

        def _emit(other: str, rel: str, direction: str, evidence, doc_id) -> None:
            if other == k or other not in self.g:
                return
            sig = (other, rel, direction)
            if sig in seen:
                return
            seen.add(sig)
            n = self.g.nodes[other]
            out.append({
                "relation": rel,
                "direction": direction,
                "other": other,
                "label": n.get("label", other),
                "type": n.get("type", "Unknown"),
                "evidence": evidence or "",
                "doc_id": doc_id,
            })

        for _, v, data in self.g.out_edges(k, data=True):
            _emit(v, data.get("type", "RELATED"), "out",
                  data.get("evidence"), data.get("doc_id"))
        for u, _, data in self.g.in_edges(k, data=True):
            _emit(u, data.get("type", "RELATED"), "in",
                  data.get("evidence"), data.get("doc_id"))
        return out

    def equipment_tags(self) -> List[dict]:
        """All Equipment/Location nodes with a plant-tag-shaped label — the
        candidate clickable symbols on any P&ID."""
        import re
        tagish = re.compile(r"^[A-Za-z]{1,4}-?\d{1,4}[A-Za-z]?$")
        out: List[dict] = []
        for k, n in self.g.nodes(data=True):
            label = n.get("label", k)
            if n.get("type") == "Equipment" or tagish.match(label):
                out.append({"key": k, "label": label, "type": n.get("type", "Equipment"),
                            "docs": sorted(n.get("docs", set()))})
        return out


    def paths_between(self, a: str, b: str, cutoff: int = 4) -> List[List[GraphPathHop]]:
        ka, kb = self._resolve_key(a), self._resolve_key(b)
        if not ka or not kb or ka not in self.g or kb not in self.g:
            return []
        ug = self.g.to_undirected(as_view=True)
        try:
            node_path = nx.shortest_path(ug, ka, kb)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
        return [self._edges_along(node_path)]

    def _edges_along(self, node_path: List[str]) -> List[GraphPathHop]:
        hops: List[GraphPathHop] = []
        for u, v in zip(node_path, node_path[1:]):
            rel, src, tgt = self._best_edge(u, v)
            hops.append(GraphPathHop(source=self.label(src), relation=rel, target=self.label(tgt)))
        return hops

    def _best_edge(self, u: str, v: str) -> Tuple[str, str, str]:
        if self.g.has_edge(u, v):
            data = list(self.g.get_edge_data(u, v).values())[0]
            return data.get("type", "RELATED"), u, v
        if self.g.has_edge(v, u):
            data = list(self.g.get_edge_data(v, u).values())[0]
            return data.get("type", "RELATED"), v, u
        return "RELATED", u, v

    def connecting_paths(self, focus: List[str], cutoff: int = 3) -> List[List[GraphPathHop]]:
        """Shortest paths pairwise among focus entities — the 'connect the dots' view."""
        resolved = [k for k in (self._resolve_key(f) for f in focus) if k]
        paths: List[List[GraphPathHop]] = []
        seen: set[tuple] = set()
        for i in range(len(resolved)):
            for j in range(i + 1, len(resolved)):
                for p in self.paths_between(resolved[i], resolved[j], cutoff):
                    sig = tuple((h.source, h.relation, h.target) for h in p)
                    if sig and sig not in seen and len(p) <= cutoff:
                        seen.add(sig)
                        paths.append(p)
        return paths

    def label(self, key: str) -> str:
        if key in self.g:
            return self.g.nodes[key].get("label", key)
        return key

    # ------------------------------------------------------------------ #
    # Visualization + stats
    # ------------------------------------------------------------------ #
    def to_viz(self, focus: Optional[Iterable[str]] = None, radius: int = 2) -> dict:
        keys = set(self.g.nodes)
        highlight: set[str] = set()
        if focus:
            focus_keys = {k for k in (self._resolve_key(f) for f in focus) if k}
            keys = set()
            for fk in focus_keys:
                keys |= self.neighbors(fk, radius)
            highlight = focus_keys
        nodes = []
        for k in keys:
            n = self.g.nodes[k]
            nodes.append({
                "id": k,
                "label": n.get("label", k),
                "type": n.get("type", "Unknown"),
                "mentions": n.get("mentions", 1),
                "docs": sorted(n.get("docs", set())),
                "highlight": k in highlight,
            })
        links = []
        for u, v, data in self.g.edges(data=True):
            if u in keys and v in keys:
                links.append({
                    "source": u, "target": v,
                    "type": data.get("type", "RELATED"),
                    "evidence": data.get("evidence", ""),
                    "doc_id": data.get("doc_id"),
                })
        return {"nodes": nodes, "links": links}

    def stats(self) -> dict:
        by_type: Dict[str, int] = defaultdict(int)
        for _, n in self.g.nodes(data=True):
            by_type[n.get("type", "Unknown")] += 1
        rel_types: Dict[str, int] = defaultdict(int)
        for _, _, d in self.g.edges(data=True):
            rel_types[d.get("type", "RELATED")] += 1
        return {
            "entities": self.g.number_of_nodes(),
            "relationships": self.g.number_of_edges(),
            "documents": len(self._documents),
            "entity_types": dict(by_type),
            "relation_types": dict(rel_types),
        }

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def save(self, path: Path) -> None:
        data = {
            "nodes": [
                {"key": k, **{kk: (sorted(vv) if isinstance(vv, set) else vv)
                              for kk, vv in n.items()}}
                for k, n in self.g.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **d} for u, v, d in self.g.edges(data=True)
            ],
            "alias": self._alias,
            "documents": [d.model_dump() for d in self._documents.values()],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "KnowledgeGraph":
        kg = cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        for n in data["nodes"]:
            key = n.pop("key")
            n["docs"] = set(n.get("docs", []))
            kg.g.add_node(key, **n)
        for e in data["edges"]:
            s, t = e.pop("source"), e.pop("target")
            kg.g.add_edge(s, t, key=e.get("type"), **e)
        kg._alias = data.get("alias", {})
        for d in data.get("documents", []):
            doc = Document.model_validate(d)
            kg._documents[doc.id] = doc
        return kg
