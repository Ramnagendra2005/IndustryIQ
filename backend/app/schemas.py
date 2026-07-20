"""Domain ontology + API models for IndustryIQ.

The entity/relationship taxonomy below IS the industrial ontology — it is what
turns a pile of documents into a queryable knowledge graph. Keep it small,
opinionated, and industrial.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Ontology
# --------------------------------------------------------------------------- #
class EntityType(str, Enum):
    EQUIPMENT = "Equipment"          # pump P-101, exchanger E-204, valve...
    PROCESS_PARAM = "ProcessParameter"  # vibration, temperature, pressure setpoints
    FAILURE_MODE = "FailureMode"     # bearing wear, seal leak, cavitation
    PERSON = "Person"                # operator / engineer / inspector
    REGULATION = "Regulation"        # Factory Act, OISD-116, PESO clause
    PROCEDURE = "Procedure"          # SOP, maintenance procedure
    DOCUMENT = "Document"            # source doc node
    DATE = "Date"                    # significant dates / events
    LOCATION = "Location"            # unit / area / plant section
    PART = "Part"                    # bearing, mechanical seal, impeller


class RelationType(str, Enum):
    CONNECTED_TO = "CONNECTED_TO"        # equipment ↔ equipment (P&ID)
    HAS_FAILURE = "HAS_FAILURE"          # equipment → failure mode
    HAS_PARAM = "HAS_PARAMETER"          # equipment → parameter
    MAINTAINED_BY = "MAINTAINED_BY"      # equipment → person
    GOVERNED_BY = "GOVERNED_BY"          # equipment/procedure → regulation
    DOCUMENTED_IN = "DOCUMENTED_IN"      # entity → document
    SIBLING_OF = "SIBLING_OF"            # equipment ↔ identical equipment
    HAS_PART = "HAS_PART"                # equipment → part
    PROCEDURE_FOR = "PROCEDURE_FOR"      # procedure → equipment
    OCCURRED_ON = "OCCURRED_ON"          # event/failure → date
    LOCATED_IN = "LOCATED_IN"            # equipment → location
    MENTIONS = "MENTIONS"                # generic doc → entity fallback


class DocType(str, Enum):
    PID = "P&ID"
    WORK_ORDER = "WorkOrder"
    INSPECTION = "InspectionReport"
    OEM_MANUAL = "OEMManual"
    INCIDENT = "IncidentReport"
    SOP = "SOP"
    REGULATION = "RegulatoryDocument"
    SPREADSHEET = "Spreadsheet"
    EMAIL = "Email"
    OTHER = "Other"


# --------------------------------------------------------------------------- #
# Extraction result models (what the LLM returns per document)
# --------------------------------------------------------------------------- #
class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Canonical name, e.g. 'P-101' or 'bearing wear'")
    type: EntityType
    aliases: List[str] = Field(default_factory=list)
    description: str = ""


class ExtractedRelation(BaseModel):
    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    type: RelationType
    evidence: str = Field("", description="Short quote/snippet supporting the link")


class Extraction(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relations: List[ExtractedRelation] = Field(default_factory=list)
    summary: str = ""


# --------------------------------------------------------------------------- #
# Document model
# --------------------------------------------------------------------------- #
class Document(BaseModel):
    id: str
    title: str
    doc_type: DocType
    date: Optional[str] = None
    unit: Optional[str] = None
    text: str = ""            # extracted / raw text used for retrieval
    source_path: Optional[str] = None
    is_image: bool = False    # P&ID / scanned form parsed via vision


# --------------------------------------------------------------------------- #
# API models
# --------------------------------------------------------------------------- #
class Citation(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    snippet: str
    date: Optional[str] = None


class GraphPathHop(BaseModel):
    source: str
    relation: str
    target: str


class QueryRequest(BaseModel):
    question: str
    mode: str = "copilot"       # copilot | rca | compliance


class AnswerTrust(BaseModel):
    """Trust-layer annotation attached to every answer: how fresh are the
    sources behind it, and do any of them carry known conflicts?"""
    freshness: float            # 0..1 — worst freshness among cited sources
    stale_docs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    confidence: float           # 0..1
    citations: List[Citation] = Field(default_factory=list)
    graph_paths: List[GraphPathHop] = Field(default_factory=list)
    focus_entities: List[str] = Field(default_factory=list)
    elapsed_ms: int = 0
    mode: str = "copilot"
    trust: Optional[AnswerTrust] = None


class ComplianceGap(BaseModel):
    regulation: str
    requirement: str
    status: str                 # "gap" | "met" | "at_risk"
    finding: str
    evidence_docs: List[Citation] = Field(default_factory=list)
    severity: str = "medium"    # low | medium | high


class ComplianceReport(BaseModel):
    audit_scope: str
    gaps: List[ComplianceGap] = Field(default_factory=list)
    met: List[ComplianceGap] = Field(default_factory=list)
    readiness_score: float = 0.0
    elapsed_ms: int = 0


# --------------------------------------------------------------------------- #
# Trust layer — contradiction & staleness detection
# --------------------------------------------------------------------------- #
class DocFreshness(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    date: Optional[str] = None
    age_days: Optional[int] = None
    freshness: float            # 0..1 (1 = fresh, decays by doc-type half-life)
    status: str = "fresh"       # fresh | aging | stale
    note: str = ""


class Conflict(BaseModel):
    id: str
    kind: str                   # numeric_conflict | doc_vs_reality | stale_reference | version_conflict
    severity: str               # low | medium | high
    title: str
    detail: str
    doc_ids: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)


class TrustReport(BaseModel):
    corpus_health: float        # 0..1 aggregate trust score for the corpus
    conflicts: List[Conflict] = Field(default_factory=list)
    freshness: List[DocFreshness] = Field(default_factory=list)
    stale_count: int = 0
    aging_count: int = 0
    elapsed_ms: int = 0
