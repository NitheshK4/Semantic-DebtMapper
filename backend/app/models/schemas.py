from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


# Projects
class ProjectCreate(BaseModel):
    name: str
    domain: str


class ProjectOut(BaseModel):
    id: UUID
    name: str
    domain: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Ingestion Schemas
class ModelVersionIngest(BaseModel):
    endpoint_id: str
    model_name: str
    model_version: str
    feature_schema_version: Optional[str] = None
    deployed_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClassDefinition(BaseModel):
    class_id: str
    display_name: str
    definition: str
    positive_criteria: List[str] = Field(default_factory=list)
    negative_criteria: List[str] = Field(default_factory=list)


class LabelSchemaIngest(BaseModel):
    schema_id: str
    schema_version: str
    effective_from: datetime
    classes: List[ClassDefinition]


class BusinessRuleIngest(BaseModel):
    rule_id: str
    rule_version: str
    endpoint_id: str
    expression: str
    created_for_model_version: Optional[str] = None
    active_from: datetime
    active_to: Optional[datetime] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class PromptVersionIngest(BaseModel):
    prompt_id: str
    prompt_version: str
    template: str
    taxonomy_version: Optional[str] = None
    deployed_at: datetime


class InferenceLogIngest(BaseModel):
    inference_id: str
    timestamp: datetime
    endpoint_id: str
    model_version: str
    input_features: Optional[Dict[str, Any]] = None
    model_output: Optional[Dict[str, Any]] = None
    rule_applied: List[str] = Field(default_factory=list)
    final_decision: Optional[str] = None
    segment: Optional[Dict[str, Any]] = None


class OverrideLogIngest(BaseModel):
    override_id: str
    inference_id: str
    reviewer_id: Optional[str] = None
    original_decision: Optional[str] = None
    override_decision: Optional[str] = None
    override_class: Optional[str] = None
    reason_code: Optional[str] = None
    comment: Optional[str] = None
    timestamp: datetime


# Concepts
class ConceptCreate(BaseModel):
    concept_key: str
    version: str
    definition: str
    effective_from: datetime

    @field_validator("concept_key")
    @classmethod
    def validate_concept_key(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Concept key must be lowercase alphanumeric, underscores, or hyphens only")
        return v


class ConceptVersionOut(BaseModel):
    id: UUID
    version: str
    definition: str
    effective_from: datetime
    effective_to: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConceptOut(BaseModel):
    id: UUID
    concept_key: str
    created_at: datetime
    versions: List[ConceptVersionOut] = []

    model_config = ConfigDict(from_attributes=True)


# Audits and Runs
class AuditRunTrigger(BaseModel):
    as_of: Optional[datetime] = None
    detectors: List[str] = Field(
        default_factory=lambda: ["CMD", "ESF", "RMC", "HMD", "GFM"]
    )


class FindingOut(BaseModel):
    id: UUID
    detector: str
    severity: str
    target: Optional[str]
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionCardOut(BaseModel):
    id: UUID
    action_type: str
    priority: float
    title: str
    steps: List[str]
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ActionCardUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class DetectorRunOut(BaseModel):
    id: UUID
    project_id: UUID
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    sds_score: Optional[float]
    summary: Optional[Dict[str, Any]]
    findings: List[FindingOut] = []
    action_cards: List[ActionCardOut] = []

    model_config = ConfigDict(from_attributes=True)
