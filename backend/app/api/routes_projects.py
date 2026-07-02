import csv
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_api_key
from app.models.db_models import Project
from app.models.schemas import (BusinessRuleIngest, ClassDefinition,
                                ConceptCreate, ConceptOut, ConceptVersionOut, InferenceLogIngest,
                                LabelSchemaIngest, ModelVersionIngest,
                                OverrideLogIngest, ProjectCreate, ProjectOut,
                                PromptVersionIngest)
from app.services.concept_registry import ConceptRegistry
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    project = Project(name=payload.name, domain=payload.domain)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), _=Depends(verify_api_key)):
    return db.query(Project).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None


@router.post("/{project_id}/concepts", response_model=ConceptOut)
def create_concept(
    project_id: UUID,
    payload: ConceptCreate,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    concept = ConceptRegistry.create_concept(
        db=db,
        project_id=project_id,
        concept_key=payload.concept_key,
        version=payload.version,
        definition=payload.definition,
        effective_from=payload.effective_from,
    )
    return concept


@router.get("/{project_id}/concepts", response_model=List[ConceptOut])
def list_concepts(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ConceptRegistry.list_concepts(db, project_id)


@router.delete("/{project_id}/concepts/{concept_key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(
    project_id: UUID,
    concept_key: str,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    deleted = ConceptRegistry.delete_concept(db, project_id, concept_key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Concept not found")
    return None


@router.get("/{project_id}/concepts/{concept_key}/history", response_model=List[ConceptVersionOut])
def get_concept_history(
    project_id: UUID,
    concept_key: str,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models.db_models import Concept
    concept = (
        db.query(Concept)
        .filter(Concept.project_id == project_id, Concept.concept_key == concept_key)
        .first()
    )
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    return sorted(concept.versions, key=lambda x: x.effective_from, reverse=True)




@router.post("/{project_id}/seed", status_code=status.HTTP_200_OK)
def seed_project_data(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Paths to datasets — resolve dynamically for both standard local dev and Docker context
    _app_root = Path(__file__).resolve().parent.parent.parent
    data_dir = _app_root / "datasets" / "demo_support_tickets"
    if not data_dir.exists():
        data_dir = _app_root.parent / "datasets" / "demo_support_tickets"
    data_dir = str(data_dir)

    # 1. Seed Concepts
    concepts = [
        {"key": "low", "def": "Ticket can be addressed within 48 hours per SLA.", "version": "v1", "date": "2026-01-01T00:00:00Z"},
        {"key": "medium", "def": "Ticket should be addressed within 24 hours per SLA.", "version": "v1", "date": "2026-01-01T00:00:00Z"},
        {"key": "critical", "def": "System outage or security incident requiring response within 30 minutes.", "version": "v1", "date": "2026-01-01T00:00:00Z"},
    ]
    for c in concepts:
        ConceptRegistry.create_concept(
            db=db,
            project_id=project_id,
            concept_key=c["key"],
            version=c["version"],
            definition=c["def"],
            effective_from=datetime.fromisoformat(c["date"]),
        )

    # Seed urgent v1 (historical)
    ConceptRegistry.create_concept(
        db=db,
        project_id=project_id,
        concept_key="urgent",
        version="v1",
        definition="Ticket requires response within two hours per SLA policy v2. Includes VIP escalations.",
        effective_from=datetime.fromisoformat("2026-01-01T00:00:00Z"),
    )
    # Seed urgent v2 (active)
    ConceptRegistry.create_concept(
        db=db,
        project_id=project_id,
        concept_key="urgent",
        version="v2",
        definition="Ticket requires response within four hours per SLA policy v3. Includes VIP escalations and payment failures.",
        effective_from=datetime.fromisoformat("2026-03-01T00:00:00Z"),
    )

    # 2. Ingest Model Versions
    with open(f"{data_dir}/model_versions.json", "r") as f:
        mvs = json.load(f)
    mv_payload = [
        ModelVersionIngest(
            endpoint_id=mv["endpoint_id"],
            model_name=mv["model_name"],
            model_version=mv["model_version"],
            feature_schema_version=mv["metadata"].get("feature_schema_version"),
            deployed_at=datetime.fromisoformat(mv["deployed_at"]),
            metadata=mv["metadata"],
        )
        for mv in mvs
    ]
    IngestionService.ingest_model_versions(db, project_id, mv_payload)

    # 3. Ingest Label Schemas
    with open(f"{data_dir}/label_schemas.json", "r") as f:
        lss = json.load(f)
    ls_payload = [
        LabelSchemaIngest(
            schema_id=ls["schema_id"],
            schema_version=ls["schema_version"],
            effective_from=datetime.fromisoformat(ls["effective_from"]),
            classes=[
                ClassDefinition(
                    class_id=cls["class_id"],
                    display_name=cls["display_name"],
                    definition=cls["definition"],
                    positive_criteria=cls.get("positive_criteria", []),
                    negative_criteria=cls.get("negative_criteria", []),
                )
                for cls in ls["classes"]
            ],
        )
        for ls in lss
    ]
    IngestionService.ingest_label_schemas(db, project_id, ls_payload)

    # 4. Ingest Rules
    with open(f"{data_dir}/rules.json", "r") as f:
        rls = json.load(f)
    rls_payload = [
        BusinessRuleIngest(
            rule_id=r["rule_id"],
            rule_version=r["rule_version"],
            endpoint_id=r["endpoint_id"],
            expression=r["expression"],
            created_for_model_version=r["created_for_model_version"],
            active_from=datetime.fromisoformat(r["active_from"]),
            active_to=(
                datetime.fromisoformat(r["active_to"]) if r.get("active_to") else None
            ),
            description=r.get("description", f"Business post-processing rule threshold filter for {r['rule_id']}"),
        )
        for r in rls
    ]
    IngestionService.ingest_rules(db, project_id, rls_payload)

    # 5. Ingest Prompts
    with open(f"{data_dir}/prompts.json", "r") as f:
        pts = json.load(f)
    pt_payload = [
        PromptVersionIngest(
            prompt_id=pt["prompt_id"],
            prompt_version=pt["prompt_version"],
            template=pt["template"],
            taxonomy_version=pt.get("taxonomy_version"),
            deployed_at=datetime.fromisoformat(pt["deployed_at"]),
        )
        for pt in pts
    ]
    IngestionService.ingest_prompts(db, project_id, pt_payload)

    # 6. Ingest Inferences
    inferences_payload = []
    with open(f"{data_dir}/inference_logs.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inferences_payload.append(
                InferenceLogIngest(
                    inference_id=row["inference_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    endpoint_id=row["endpoint_id"],
                    model_version=row["model_version"],
                    input_features={
                        "customer_tier": row["customer_tier"],
                        "ticket_age_hours": float(row["ticket_age_hours"]),
                        "channel": row["channel"],
                    },
                    model_output={
                        "score": float(row["score"]),
                        "predicted_class": row["predicted_class"],
                    },
                    rule_applied=["threshold_urgent"],
                    final_decision=row["final_decision"],
                    segment={"region": row["region"], "channel": row["channel"]},
                )
            )
    IngestionService.ingest_inferences_batch(db, project_id, inferences_payload)

    # 7. Ingest Overrides
    overrides_payload = []
    with open(f"{data_dir}/override_logs.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            overrides_payload.append(
                OverrideLogIngest(
                    override_id=row["override_id"],
                    inference_id=row["inference_id"],
                    reviewer_id=row["reviewer_id"],
                    original_decision=row["original_decision"],
                    override_decision=row["override_decision"],
                    override_class=row["override_class"],
                    reason_code=row["reason_code"],
                    comment=row["comment"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                )
            )
    IngestionService.ingest_overrides_batch(db, project_id, overrides_payload)

    return {"status": "success", "seeded": True}


@router.get("/{project_id}/findings/export")
def export_findings(
    project_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    from app.models.db_models import DetectorRun, Finding

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get latest completed run
    run = (
        db.query(DetectorRun)
        .filter(DetectorRun.project_id == project_id, DetectorRun.status == "completed")
        .order_by(DetectorRun.started_at.desc())
        .first()
    )

    findings_data = []
    sds_score = None
    run_id = None
    run_date = None

    if run:
        run_id = str(run.id)
        sds_score = float(run.sds_score) if run.sds_score is not None else None
        run_date = run.finished_at.isoformat() if run.finished_at else run.started_at.isoformat()
        findings = db.query(Finding).filter(Finding.run_id == run.id).all()
        for f in findings:
            findings_data.append({
                "id": str(f.id),
                "detector": f.detector,
                "severity": f.severity,
                "target": f.target,
                "payload": f.payload,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "project_domain": project.domain,
        "exported_at": datetime.now().isoformat(),
        "latest_run": {
            "run_id": run_id,
            "sds_score": sds_score,
            "completed_at": run_date,
            "findings_count": len(findings_data),
        },
        "findings": findings_data
    }


@router.delete("/{project_id}/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business_rule(
    project_id: UUID,
    rule_id: str,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    from app.models.db_models import BusinessRule

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rules = (
        db.query(BusinessRule)
        .filter(BusinessRule.project_id == project_id, BusinessRule.rule_id == rule_id)
        .all()
    )
    if not rules:
        raise HTTPException(status_code=404, detail="Business rule not found")

    for r in rules:
        db.delete(r)
    db.commit()
    return None
