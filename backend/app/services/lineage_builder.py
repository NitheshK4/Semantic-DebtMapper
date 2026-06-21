import json
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db_models import (BusinessRule, Concept, ConceptVersion,
                                  InferenceLog, LabelSchema,
                                  LineageGraphSnapshot, ModelVersion,
                                  OverrideLog, PromptVersion)


class LineageBuilder:
    """Builder for constructing the semantic lineage graph of a project pipeline.

    The graph tracks how model versions, concepts, label schemas, business rules,
    prompt configurations, input features, and data segments are connected as of
    a specific point in time.
    """

    @staticmethod
    def build_graph(db: Session, project_id: UUID, as_of: datetime) -> dict:
        """Construct the lineage graph nodes and edges as of the target timestamp.

        Crawls active model versions, label classes, business rules, prompts,
        and samples input features and segments from inference logs. Generates
        directed relationships (e.g. predicts, uses_feature, post_processes, defines)
        and persists the snapshot in the database.

        Args:
            db: SQLAlchemy database session.
            project_id: Unique identifier of the project.
            as_of: The reference timestamp for active lineage components.

        Returns:
            A dictionary with 'nodes' and 'edges' representing the graph.
        """
        nodes = []
        edges = []
        node_ids = set()

        def add_node(node_id: str, node_type: str, label: str, metadata: dict = None):
            if node_id not in node_ids:
                nodes.append(
                    {
                        "id": node_id,
                        "type": node_type,
                        "label": label,
                        "metadata": metadata or {},
                    }
                )
                node_ids.add(node_id)

        def add_edge(source: str, target: str, edge_type: str):
            edges.append({"source": source, "target": target, "type": edge_type})

        # 1. Models deployed as of `as_of`
        models = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.project_id == project_id, ModelVersion.deployed_at <= as_of
            )
            .order_by(ModelVersion.deployed_at.desc())
            .all()
        )

        # Group models by endpoint to find the active model version
        endpoints = {}
        for m in models:
            if m.endpoint_id not in endpoints:
                endpoints[m.endpoint_id] = m
                # Active model node
                add_node(
                    node_id=f"model:{m.endpoint_id}:{m.model_version}",
                    node_type="model_version",
                    label=f"{m.model_name} ({m.model_version})",
                    metadata={
                        "endpoint_id": m.endpoint_id,
                        "model_name": m.model_name,
                        "model_version": m.model_version,
                        "feature_schema_version": m.feature_schema_version,
                        "metadata": m.model_metadata,
                        "deployed_at": m.deployed_at.isoformat(),
                        "is_active": True,
                    },
                )
            else:
                # Historical model node
                add_node(
                    node_id=f"model:{m.endpoint_id}:{m.model_version}",
                    node_type="model_version",
                    label=f"{m.model_name} ({m.model_version})",
                    metadata={
                        "endpoint_id": m.endpoint_id,
                        "model_name": m.model_name,
                        "model_version": m.model_version,
                        "feature_schema_version": m.feature_schema_version,
                        "metadata": m.model_metadata,
                        "deployed_at": m.deployed_at.isoformat(),
                        "is_active": False,
                    },
                )

        # 2. Label Schemas effective as of `as_of`
        schemas = (
            db.query(LabelSchema)
            .filter(
                LabelSchema.project_id == project_id,
                LabelSchema.effective_from <= as_of,
            )
            .order_by(LabelSchema.effective_from.desc())
            .all()
        )

        active_schema = None
        seen_schemas = set()
        for s in schemas:
            if s.schema_id not in seen_schemas:
                seen_schemas.add(s.schema_id)
                if active_schema is None:
                    active_schema = s

            # Label classes inside payload
            classes_list = s.payload.get("classes", [])
            for cls_def in classes_list:
                class_id = cls_def.get("class_id")
                add_node(
                    node_id=f"class:{class_id}",
                    node_type="label_class",
                    label=cls_def.get("display_name", class_id),
                    metadata={
                        "schema_id": s.schema_id,
                        "schema_version": s.schema_version,
                        "definition": cls_def.get("definition"),
                        "positive_criteria": cls_def.get("positive_criteria"),
                        "negative_criteria": cls_def.get("negative_criteria"),
                    },
                )

                # Link model to label classes it predicts
                # Standard endpoint models predict classes belonging to its label schema
                for endpoint_id, m in endpoints.items():
                    add_edge(
                        source=f"model:{endpoint_id}:{m.model_version}",
                        target=f"class:{class_id}",
                        edge_type="predicts",
                    )

        # 3. Concepts active as of `as_of`
        concepts = db.query(Concept).filter(Concept.project_id == project_id).all()
        for concept in concepts:
            active_ver = (
                db.query(ConceptVersion)
                .filter(
                    ConceptVersion.concept_id == concept.id,
                    ConceptVersion.effective_from <= as_of,
                    (
                        (ConceptVersion.effective_to.is_(None))
                        | (ConceptVersion.effective_to > as_of)
                    ),
                )
                .order_by(ConceptVersion.effective_from.desc())
                .first()
            )

            if active_ver:
                add_node(
                    node_id=f"concept:{concept.concept_key}",
                    node_type="concept",
                    label=f"Concept: {concept.concept_key}",
                    metadata={
                        "version": active_ver.version,
                        "definition": active_ver.definition,
                        "effective_from": active_ver.effective_from.isoformat(),
                    },
                )
                # Link Concept → Label Class (defines)
                # If concept key matches label class ID
                class_node_id = f"class:{concept.concept_key}"
                if class_node_id in node_ids:
                    add_edge(
                        source=f"concept:{concept.concept_key}",
                        target=class_node_id,
                        edge_type="defines",
                    )

        # 4. Rules active as of `as_of`
        rules = (
            db.query(BusinessRule)
            .filter(
                BusinessRule.project_id == project_id,
                BusinessRule.active_from <= as_of,
                ((BusinessRule.active_to.is_(None)) | (BusinessRule.active_to > as_of)),
            )
            .all()
        )

        for r in rules:
            add_node(
                node_id=f"rule:{r.rule_id}",
                node_type="rule",
                label=f"Rule: {r.rule_id}",
                metadata={
                    "rule_version": r.rule_version,
                    "expression": r.expression,
                    "created_for_model_version": r.created_for_model_version,
                    "endpoint_id": r.endpoint_id,
                    "description": r.description,
                },
            )

            # Link rule -> model version it depends on
            if r.created_for_model_version:
                model_node_id = f"model:{r.endpoint_id}:{r.created_for_model_version}"
                if model_node_id in node_ids:
                    add_edge(
                        source=f"rule:{r.rule_id}",
                        target=model_node_id,
                        edge_type="depends_on",
                    )

            # Rule post processes model decisions
            # We will link it to the predicted class if the class is mentioned or general decision outcome
            for endpoint_id, m in endpoints.items():
                if r.endpoint_id == endpoint_id:
                    # Link rule to model output path
                    add_edge(
                        source=f"rule:{r.rule_id}",
                        target=f"model:{endpoint_id}:{m.model_version}",
                        edge_type="post_processes",
                    )

        # 5. Prompts active as of `as_of`
        prompts = (
            db.query(PromptVersion)
            .filter(
                PromptVersion.project_id == project_id,
                PromptVersion.deployed_at <= as_of,
            )
            .order_by(PromptVersion.deployed_at.desc())
            .all()
        )

        seen_prompts = set()
        for p in prompts:
            if p.prompt_id not in seen_prompts:
                seen_prompts.add(p.prompt_id)
                add_node(
                    node_id=f"prompt:{p.prompt_id}",
                    node_type="prompt_version",
                    label=f"Prompt: {p.prompt_id} ({p.prompt_version})",
                    metadata={
                        "prompt_version": p.prompt_version,
                        "template": p.template[:150] + "...",
                        "taxonomy_version": p.taxonomy_version,
                    },
                )

        # 6. Features & Segments from inference logs
        # Query sample logs to find distinct features and segments
        logs = (
            db.query(InferenceLog)
            .filter(InferenceLog.project_id == project_id, InferenceLog.ts <= as_of)
            .order_by(InferenceLog.ts.desc())
            .limit(100)
            .all()
        )

        features_seen = set()
        segments_seen = set()

        for log in logs:
            if log.input_features:
                for f_name in log.input_features.keys():
                    if f_name not in features_seen:
                        features_seen.add(f_name)
                        add_node(
                            node_id=f"feature:{f_name}",
                            node_type="feature",
                            label=f"Feature: {f_name}",
                            metadata={},
                        )
                    # Link active model to feature it uses
                    model_node_id = f"model:{log.endpoint_id}:{log.model_version}"
                    if model_node_id in node_ids:
                        add_edge(
                            source=model_node_id,
                            target=f"feature:{f_name}",
                            edge_type="uses_feature",
                        )

            if log.segment:
                # Represent segment as string "region=EU,channel=mobile"
                seg_items = sorted([f"{k}={v}" for k, v in log.segment.items()])
                seg_label = ", ".join(seg_items)
                seg_id = f"segment:{'_'.join(seg_items)}"
                if seg_id not in segments_seen:
                    segments_seen.add(seg_id)
                    add_node(
                        node_id=seg_id,
                        node_type="segment",
                        label=seg_label,
                        metadata={"segment_dict": log.segment},
                    )

        graph = {"nodes": nodes, "edges": edges}

        # Save snapshot
        snapshot = LineageGraphSnapshot(project_id=project_id, as_of=as_of, graph=graph)
        db.add(snapshot)
        db.commit()

        return graph
