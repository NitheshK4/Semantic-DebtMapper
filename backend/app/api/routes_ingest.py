from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_api_key
from app.models.db_models import Project
from app.models.schemas import (BusinessRuleIngest, InferenceLogIngest,
                                LabelSchemaIngest, ModelVersionIngest,
                                OverrideLogIngest, PromptVersionIngest)
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/projects/{project_id}/ingest", tags=["Ingestion"])


def check_project_exists(project_id: UUID, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/model-versions", status_code=status.HTTP_200_OK)
def ingest_model_versions(
    project_id: UUID,
    payload: List[ModelVersionIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_model_versions(db, project_id, payload)
    return {"status": "success", "ingested": count}


@router.post("/label-schemas", status_code=status.HTTP_200_OK)
def ingest_label_schemas(
    project_id: UUID,
    payload: List[LabelSchemaIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_label_schemas(db, project_id, payload)
    return {"status": "success", "ingested": count}


@router.post("/rules", status_code=status.HTTP_200_OK)
def ingest_rules(
    project_id: UUID,
    payload: List[BusinessRuleIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_rules(db, project_id, payload)
    return {"status": "success", "ingested": count}


@router.post("/prompts", status_code=status.HTTP_200_OK)
def ingest_prompts(
    project_id: UUID,
    payload: List[PromptVersionIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_prompts(db, project_id, payload)
    return {"status": "success", "ingested": count}


@router.post("/inferences:batch", status_code=status.HTTP_200_OK)
def ingest_inferences(
    project_id: UUID,
    payload: List[InferenceLogIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_inferences_batch(db, project_id, payload)
    return {"status": "success", "ingested": count}


@router.post("/overrides:batch", status_code=status.HTTP_200_OK)
def ingest_overrides(
    project_id: UUID,
    payload: List[OverrideLogIngest],
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    count = IngestionService.ingest_overrides_batch(db, project_id, payload)
    return {"status": "success", "ingested": count}
