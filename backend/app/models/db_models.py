import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Numeric, String,
                        Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    concepts = relationship(
        "Concept", back_populates="project", cascade="all, delete-orphan"
    )
    model_versions = relationship(
        "ModelVersion", back_populates="project", cascade="all, delete-orphan"
    )
    label_schemas = relationship(
        "LabelSchema", back_populates="project", cascade="all, delete-orphan"
    )
    business_rules = relationship(
        "BusinessRule", back_populates="project", cascade="all, delete-orphan"
    )
    prompt_versions = relationship(
        "PromptVersion", back_populates="project", cascade="all, delete-orphan"
    )
    inference_logs = relationship(
        "InferenceLog", back_populates="project", cascade="all, delete-orphan"
    )
    override_logs = relationship(
        "OverrideLog", back_populates="project", cascade="all, delete-orphan"
    )
    graph_snapshots = relationship(
        "LineageGraphSnapshot", back_populates="project", cascade="all, delete-orphan"
    )
    detector_runs = relationship(
        "DetectorRun", back_populates="project", cascade="all, delete-orphan"
    )


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept_key = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("project_id", "concept_key"),)

    project = relationship("Project", back_populates="concepts")
    versions = relationship(
        "ConceptVersion", back_populates="concept", cascade="all, delete-orphan"
    )


class ConceptVersion(Base):
    __tablename__ = "concept_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
    )
    version = Column(String, nullable=False)
    definition = Column(Text, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    concept = relationship("Concept", back_populates="versions")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    endpoint_id = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    feature_schema_version = Column(String, nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=False)
    model_metadata = Column("metadata", JSON, default=dict)

    __table_args__ = (UniqueConstraint("project_id", "endpoint_id", "model_version"),)

    project = relationship("Project", back_populates="model_versions")


class LabelSchema(Base):
    __tablename__ = "label_schemas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    schema_id = Column(String, nullable=False)
    schema_version = Column(String, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON, nullable=False)  # Contains classes list: {classes: [...]}

    project = relationship("Project", back_populates="label_schemas")


class BusinessRule(Base):
    __tablename__ = "business_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_id = Column(String, nullable=False)
    rule_version = Column(String, nullable=False)
    endpoint_id = Column(String, nullable=False)
    expression = Column(String, nullable=False)
    created_for_model_version = Column(String, nullable=True)
    active_from = Column(DateTime(timezone=True), nullable=False)
    active_to = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSON, default=dict)

    project = relationship("Project", back_populates="business_rules")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_id = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    taxonomy_version = Column(String, nullable=True)
    template = Column(String, nullable=False)
    deployed_at = Column(DateTime(timezone=True), nullable=False)

    project = relationship("Project", back_populates="prompt_versions")


class InferenceLog(Base):
    __tablename__ = "inference_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    inference_id = Column(String, nullable=False)
    endpoint_id = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    input_features = Column(JSON, nullable=True)
    model_output = Column(JSON, nullable=True)
    final_decision = Column(String, nullable=True)
    segment = Column(JSON, nullable=True)

    __table_args__ = (UniqueConstraint("project_id", "inference_id"),)

    project = relationship("Project", back_populates="inference_logs")


class OverrideLog(Base):
    __tablename__ = "override_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    override_id = Column(String, nullable=False)
    inference_id = Column(String, nullable=False)
    original_decision = Column(String, nullable=True)
    override_decision = Column(String, nullable=True)
    override_class = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    comment = Column(String, nullable=True)
    ts = Column(DateTime(timezone=True), nullable=False)

    project = relationship("Project", back_populates="override_logs")


class LineageGraphSnapshot(Base):
    __tablename__ = "lineage_graph_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    as_of = Column(DateTime(timezone=True), nullable=False)
    graph = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="graph_snapshots")


class DetectorRun(Base):
    __tablename__ = "detector_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)  # pending, running, completed, failed
    sds_score = Column(Numeric(5, 2), nullable=True)
    summary = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="detector_runs")
    findings = relationship(
        "Finding", back_populates="run", cascade="all, delete-orphan"
    )
    action_cards = relationship(
        "ActionCard", back_populates="run", cascade="all, delete-orphan"
    )


class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("detector_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    detector = Column(String, nullable=False)  # CMD, ESF, RMC, HMD, GFM
    severity = Column(String, nullable=False)  # low, medium, high, critical
    target = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("DetectorRun", back_populates="findings")


class ActionCard(Base):
    __tablename__ = "action_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID(as_uuid=True),
        ForeignKey("detector_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type = Column(
        String, nullable=False
    )  # RELABEL_SUBSET, REINDEX_EMBEDDINGS, etc.
    priority = Column(Numeric(4, 3), nullable=False)
    title = Column(String, nullable=False)
    steps = Column(JSON, nullable=False)
    status = Column(String, default="open")  # open, acknowledged, resolved

    run = relationship("DetectorRun", back_populates="action_cards")
