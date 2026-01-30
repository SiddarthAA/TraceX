"""
Data models for requirements and traceability links.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SAFETY = "safety"
    INTERFACE = "interface"
    DIAGNOSTIC = "diagnostic"
    OTHER = "other"


class SafetyLevel(str, Enum):
    DAL_A = "DAL-A"
    DAL_B = "DAL-B"
    DAL_C = "DAL-C"
    DAL_D = "DAL-D"
    QM = "QM"
    ASIL_A = "ASIL-A"
    ASIL_B = "ASIL-B"
    ASIL_C = "ASIL-C"
    ASIL_D = "ASIL-D"
    NOT_SPECIFIED = "not_specified"


class StructuredRequirement(BaseModel):
    """Structured semantic understanding of a requirement."""
    intent_verb: str = Field(description="Main action verb (e.g., maintain, respond, process)")
    subject: str = Field(description="What performs the action")
    object: str = Field(description="What is acted upon")
    constraint: Optional[str] = Field(default=None, description="Timing, range, or accuracy constraints")
    requirement_type: RequirementType = Field(description="Category of requirement")
    abstraction_level: str = Field(description="system, subsystem, or component")
    key_concepts: List[str] = Field(default_factory=list, description="Key technical concepts")


class Requirement(BaseModel):
    """Base requirement model."""
    id: str
    title: str
    description: str
    type: str = "other"
    safety_level: str = "not_specified"
    component: Optional[str] = None
    structured: Optional[StructuredRequirement] = None
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)


class HLR(Requirement):
    """High-Level Requirement."""
    pass


class LLR(Requirement):
    """Low-Level Requirement."""
    pass


class LinkType(str, Enum):
    SUPPORTS = "supports"
    IMPLEMENTS = "implements"
    REFINES = "refines"
    CONTRIBUTES = "contributes"
    NOT_LINKED = "not_linked"


class CoverageType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class CandidateLink(BaseModel):
    """Candidate link before reasoning."""
    hlr_id: str
    llr_id: str
    embedding_score: float = 0.0
    bm25_score: float = 0.0
    ontology_overlap: List[str] = Field(default_factory=list)
    combined_score: float = 0.0


class ReasoningTrace(BaseModel):
    """Detailed reasoning for a link decision."""
    intent_alignment: str
    conceptual_chain: str
    type_compatibility: str
    safety_consistency: str
    coverage_logic: str
    decision: str


class TraceabilityLink(BaseModel):
    """Final traceability link with explanation."""
    hlr_id: str
    llr_id: str
    link_type: LinkType
    coverage: CoverageType
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    reasoning_trace: Optional[ReasoningTrace] = None
    accepted: bool = True
    human_validated: bool = False


class GapReport(BaseModel):
    """Gap analysis report."""
    orphan_hlrs: List[str] = Field(default_factory=list, description="HLRs with no linked LLRs")
    orphan_llrs: List[str] = Field(default_factory=list, description="LLRs with no linked HLRs")
    partial_coverage_hlrs: List[str] = Field(default_factory=list, description="HLRs with partial coverage")
    coverage_percentage: float = 0.0


class TraceabilityMatrix(BaseModel):
    """Complete traceability matrix."""
    links: List[TraceabilityLink]
    gap_report: GapReport
    hlr_count: int
    llr_count: int
    link_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
