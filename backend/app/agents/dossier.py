"""Entity dossier builder — the profile behind a clicked P&ID symbol.

Given an equipment tag (or any entity name), this walks the knowledge graph and
assembles everything an engineer would want in one place:

  * process connections (upstream / downstream), siblings, parts, parameters
  * failure modes seen on the asset
  * the full maintenance & document history (work orders, inspections,
    incidents, manuals, emails) sorted newest-first, each with its trust
    freshness
  * governing procedures and regulations
  * OPEN compliance gaps and trust conflicts that touch this asset

It is deliberately graph-driven (relation types, not hard-coded ids) so it works
for any entity the graph knows about — the seed corpus or anything ingested live.
"""
from __future__ import annotations

import re
from typing import List, Optional

from ..schemas import (ComplianceReport, DossierDoc, DossierLink, EntityDossier,
                       TrustReport)


def _date_key(d: Optional[str]) -> str:
    return d or "0000-00-00"


def _mentions(label: str, text: str) -> bool:
    """Whole-tag match: 'P-101' matches 'P-101' but not 'P-1012'."""
    if not label or len(label) < 2:
        return False
    return re.search(r"(?<![A-Za-z0-9])" + re.escape(label) + r"(?![A-Za-z0-9])",
                     text, re.IGNORECASE) is not None


def _conflict_text(kg, c) -> str:
    """A conflict is 'about' an asset if the tag appears in its wording OR in the
    title of a backing document. Work-order / inspection titles name their asset,
    so this is precise without propagating a shared SOP's issue onto every asset."""
    parts = [c.title, c.detail, " ".join(c.entities)]
    for did in c.doc_ids:
        doc = kg.get_document(did)
        if doc:
            parts.append(doc.title)
    return " ".join(parts)


def _gap_text(kg, g) -> str:
    parts = [g.finding, g.requirement, g.regulation]
    for cit in g.evidence_docs:
        parts.append(cit.title)
    return " ".join(parts)


def entity_health(kg, key: str, compliance: Optional[ComplianceReport],
                  trust: Optional[TrustReport]) -> str:
    """Traffic-light health for an asset: alert (high risk) / watch / ok.

    An asset is flagged when its tag appears in an open trust conflict or an
    unmet compliance requirement (by wording or by a backing record's title).
    That is what lets the P&ID itself glow red exactly where the problems are.
    """
    view = kg.node_view(key)
    if not view:
        return "ok"
    label = view["label"]
    alert = watch = False

    if trust:
        for c in trust.conflicts:
            if _mentions(label, _conflict_text(kg, c)):
                if c.severity == "high":
                    alert = True
                else:
                    watch = True
    if compliance:
        for g in compliance.gaps:
            if _mentions(label, _gap_text(kg, g)):
                if g.status == "gap":
                    alert = True
                elif g.status == "at_risk":
                    watch = True
    return "alert" if alert else ("watch" if watch else "ok")


def _link(rel: dict) -> DossierLink:
    return DossierLink(name=rel["other"], label=rel["label"], type=rel["type"],
                       relation=rel["relation"], evidence=rel.get("evidence", ""))


def _dedupe(links: List[DossierLink]) -> List[DossierLink]:
    seen: set = set()
    out: List[DossierLink] = []
    for l in links:
        if l.name in seen:
            continue
        seen.add(l.name)
        out.append(l)
    return out


def build_dossier(kg, name: str, compliance: Optional[ComplianceReport] = None,
                  trust: Optional[TrustReport] = None) -> EntityDossier:
    view = kg.node_view(name)
    if not view:
        return EntityDossier(name=name, label=name, type="Unknown", found=False)

    key = view["key"]
    rels = kg.relations_of(key)

    connections_up: List[DossierLink] = []
    connections_down: List[DossierLink] = []
    siblings: List[DossierLink] = []
    failure_modes: List[DossierLink] = []
    parts: List[DossierLink] = []
    parameters: List[DossierLink] = []
    people: List[DossierLink] = []
    regulations: List[DossierLink] = []
    procedures: List[DossierLink] = []

    for r in rels:
        rel, direction = r["relation"], r["direction"]
        if rel == "CONNECTED_TO":
            (connections_down if direction == "out" else connections_up).append(_link(r))
        elif rel == "SIBLING_OF":
            siblings.append(_link(r))
        elif rel == "HAS_FAILURE" and direction == "out":
            failure_modes.append(_link(r))
        elif rel == "HAS_PART" and direction == "out":
            parts.append(_link(r))
        elif rel == "HAS_PARAMETER" and direction == "out":
            parameters.append(_link(r))
        elif rel == "MAINTAINED_BY" and direction == "out":
            people.append(_link(r))
        elif rel == "GOVERNED_BY" and direction == "out":
            regulations.append(_link(r))
        elif rel == "PROCEDURE_FOR" and direction == "in":
            procedures.append(_link(r))

    # Document / maintenance history — everything that mentions this asset,
    # newest first, annotated with trust freshness.
    fresh_map = {f.doc_id: f for f in (trust.freshness if trust else [])}
    history: List[DossierDoc] = []
    for did in view["docs"]:
        doc = kg.get_document(did)
        if not doc:
            continue
        dtype = doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type)
        f = fresh_map.get(did)
        history.append(DossierDoc(
            doc_id=doc.id, title=doc.title, doc_type=dtype, date=doc.date,
            snippet=(doc.text[:160].strip() + ("…" if len(doc.text) > 160 else "")),
            freshness=(f.freshness if f else 1.0),
            status=(f.status if f else "fresh"),
        ))
    history.sort(key=lambda d: _date_key(d.date), reverse=True)

    # Open compliance gaps + trust conflicts touching this asset. An item
    # belongs to this asset only when its tag appears in the item's wording or
    # in the title of a backing record — the same precise, title-driven rule as
    # entity_health, so the dossier and the P&ID colouring never disagree.
    label = view["label"]
    gaps = []
    if compliance:
        for g in compliance.gaps:
            if _mentions(label, _gap_text(kg, g)):
                gaps.append(g)
    conflicts = []
    if trust:
        for c in trust.conflicts:
            if _mentions(label, _conflict_text(kg, c)):
                conflicts.append(c)

    unit = None
    for r in rels:
        if r["relation"] == "LOCATED_IN" and r["direction"] == "out":
            unit = r["label"]
            break

    return EntityDossier(
        name=key, label=view["label"], type=view["type"],
        description=view["description"], unit=unit,
        health=entity_health(kg, key, compliance, trust),
        connections_up=_dedupe(connections_up), connections_down=_dedupe(connections_down),
        siblings=_dedupe(siblings), failure_modes=_dedupe(failure_modes),
        parts=_dedupe(parts), parameters=_dedupe(parameters), people=_dedupe(people),
        regulations=_dedupe(regulations), procedures=_dedupe(procedures), history=history,
        compliance_gaps=gaps, conflicts=conflicts, found=True,
    )
