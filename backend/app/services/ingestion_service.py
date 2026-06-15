from typing import List
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.db_models import (BusinessRule, InferenceLog, LabelSchema,
                                  ModelVersion, OverrideLog, PromptVersion)
from app.models.schemas import (BusinessRuleIngest, InferenceLogIngest,
                                LabelSchemaIngest, ModelVersionIngest,
                                OverrideLogIngest, PromptVersionIngest)


class IngestionService:
    """Service responsible for ingesting pipeline artifacts into the database.

    Provides idempotent methods for loading model versions, label schemas,
    business rules, prompt configurations, inference logs, and human override inputs.
    """

    @staticmethod
    def ingest_model_versions(
        db: Session, project_id: UUID, events: List[ModelVersionIngest]
    ) -> int:
        """Ingest model version events into the database.

        Updates existing definitions if endpoint and version already exist.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            events: List of model version ingestion payloads.

        Returns:
            Number of successfully processed model versions.
        """
        count = 0
        for event in events:
            # PostgreSQL upsert (ON CONFLICT DO UPDATE)
            stmt = insert(ModelVersion).values(
                project_id=project_id,
                endpoint_id=event.endpoint_id,
                model_name=event.model_name,
                model_version=event.model_version,
                feature_schema_version=event.feature_schema_version,
                deployed_at=event.deployed_at,
                model_metadata=event.metadata,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["project_id", "endpoint_id", "model_version"],
                set_={
                    "model_name": stmt.excluded.model_name,
                    "feature_schema_version": stmt.excluded.feature_schema_version,
                    "deployed_at": stmt.excluded.deployed_at,
                    "metadata": stmt.excluded.metadata,
                },
            )
            db.execute(stmt)
            count += 1
        db.commit()
        return count

    @staticmethod
    def ingest_label_schemas(
        db: Session, project_id: UUID, schemas: List[LabelSchemaIngest]
    ) -> int:
        """Ingest label schemas and version mappings.

        Saves or updates label schema versions, including classes and criteria.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            schemas: List of label schema ingestion payloads.

        Returns:
            Number of successfully processed label schemas.
        """
        count = 0
        for schema in schemas:
            # Store label schemas - we can store multiple versions, so we don't necessarily overwrite.
            # But let's check if the exact project_id, schema_id, schema_version exists to do updates.
            # The database doesn't have a unique constraint on schema_version in label_schemas, but let's query first or delete and insert.
            # To be simple and robust:
            existing = (
                db.query(LabelSchema)
                .filter(
                    LabelSchema.project_id == project_id,
                    LabelSchema.schema_id == schema.schema_id,
                    LabelSchema.schema_version == schema.schema_version,
                )
                .first()
            )

            payload = {"classes": [cls.dict() for cls in schema.classes]}

            if existing:
                existing.effective_from = schema.effective_from
                existing.payload = payload
            else:
                db.add(
                    LabelSchema(
                        project_id=project_id,
                        schema_id=schema.schema_id,
                        schema_version=schema.schema_version,
                        effective_from=schema.effective_from,
                        payload=payload,
                    )
                )
            count += 1
        db.commit()
        return count

    @staticmethod
    def ingest_rules(
        db: Session, project_id: UUID, rules: List[BusinessRuleIngest]
    ) -> int:
        """Ingest business rules that post-process model predictions.

        Upserts rule definitions by rule_id and rule_version.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            rules: List of business rules to ingest.

        Returns:
            Number of successfully processed business rules.
        """
        count = 0
        for rule in rules:
            existing = (
                db.query(BusinessRule)
                .filter(
                    BusinessRule.project_id == project_id,
                    BusinessRule.rule_id == rule.rule_id,
                    BusinessRule.rule_version == rule.rule_version,
                )
                .first()
            )

            if existing:
                existing.endpoint_id = rule.endpoint_id
                existing.expression = rule.expression
                existing.created_for_model_version = rule.created_for_model_version
                existing.active_from = rule.active_from
                existing.active_to = rule.active_to
                existing.payload = rule.payload
            else:
                db.add(
                    BusinessRule(
                        project_id=project_id,
                        rule_id=rule.rule_id,
                        rule_version=rule.rule_version,
                        endpoint_id=rule.endpoint_id,
                        expression=rule.expression,
                        created_for_model_version=rule.created_for_model_version,
                        active_from=rule.active_from,
                        active_to=rule.active_to,
                        payload=rule.payload,
                    )
                )
            count += 1
        db.commit()
        return count

    @staticmethod
    def ingest_prompts(
        db: Session, project_id: UUID, prompts: List[PromptVersionIngest]
    ) -> int:
        """Ingest prompt templates and version configurations.

        Upserts prompt versions by prompt_id and prompt_version.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            prompts: List of prompt versions to ingest.

        Returns:
            Number of successfully processed prompt versions.
        """
        count = 0
        for prompt in prompts:
            existing = (
                db.query(PromptVersion)
                .filter(
                    PromptVersion.project_id == project_id,
                    PromptVersion.prompt_id == prompt.prompt_id,
                    PromptVersion.prompt_version == prompt.prompt_version,
                )
                .first()
            )

            if existing:
                existing.template = prompt.template
                existing.taxonomy_version = prompt.taxonomy_version
                existing.deployed_at = prompt.deployed_at
            else:
                db.add(
                    PromptVersion(
                        project_id=project_id,
                        prompt_id=prompt.prompt_id,
                        prompt_version=prompt.prompt_version,
                        template=prompt.template,
                        taxonomy_version=prompt.taxonomy_version,
                        deployed_at=prompt.deployed_at,
                    )
                )
            count += 1
        db.commit()
        return count

    @staticmethod
    def ingest_inferences_batch(
        db: Session, project_id: UUID, inferences: List[InferenceLogIngest]
    ) -> int:
        """Ingest a batch of inference logs with inputs and outputs.

        Uses upsert mapping by inference_id to allow safe re-ingestion.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            inferences: List of inference log ingestion payloads.

        Returns:
            Number of successfully processed inference logs.
        """
        count = 0
        for inf in inferences:
            # We can use ON CONFLICT DO UPDATE for inference logs based on inference_id
            stmt = insert(InferenceLog).values(
                project_id=project_id,
                inference_id=inf.inference_id,
                endpoint_id=inf.endpoint_id,
                model_version=inf.model_version,
                ts=inf.timestamp,
                input_features=inf.input_features,
                model_output={
                    **(inf.model_output or {}),
                    "rule_applied": inf.rule_applied,
                },
                final_decision=inf.final_decision,
                segment=inf.segment,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["project_id", "inference_id"],
                set_={
                    "endpoint_id": stmt.excluded.endpoint_id,
                    "model_version": stmt.excluded.model_version,
                    "ts": stmt.excluded.ts,
                    "input_features": stmt.excluded.input_features,
                    "model_output": stmt.excluded.model_output,
                    "final_decision": stmt.excluded.final_decision,
                    "segment": stmt.excluded.segment,
                },
            )
            db.execute(stmt)
            count += 1
        db.commit()
        return count

    @staticmethod
    def ingest_overrides_batch(
        db: Session, project_id: UUID, overrides: List[OverrideLogIngest]
    ) -> int:
        """Ingest a batch of human override logs.

        Validates and updates or inserts logs mapping human decisions to inferences.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique project identifier.
            overrides: List of override log ingestion payloads.

        Returns:
            Number of successfully processed override logs.
        """
        count = 0
        for ovr in overrides:
            # Delete if exists, then insert to maintain idempotency since there's no primary key unique constraint on override_id in overrides
            # Wait, let's look at the database_schema.sql. Override logs do not have a unique constraint, but we can query by project_id and override_id.
            existing = (
                db.query(OverrideLog)
                .filter(
                    OverrideLog.project_id == project_id,
                    OverrideLog.override_id == ovr.override_id,
                )
                .first()
            )

            if existing:
                existing.inference_id = ovr.inference_id
                existing.original_decision = ovr.original_decision
                existing.override_decision = ovr.override_decision
                existing.override_class = ovr.override_class
                existing.reason_code = ovr.reason_code
                existing.comment = ovr.comment
                existing.ts = ovr.timestamp
            else:
                db.add(
                    OverrideLog(
                        project_id=project_id,
                        override_id=ovr.override_id,
                        inference_id=ovr.inference_id,
                        original_decision=ovr.original_decision,
                        override_decision=ovr.override_decision,
                        override_class=ovr.override_class,
                        reason_code=ovr.reason_code,
                        comment=ovr.comment,
                        ts=ovr.timestamp,
                    )
                )
            count += 1
        db.commit()
        return count
