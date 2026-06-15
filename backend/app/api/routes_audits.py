import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import verify_api_key
from app.models.db_models import (ActionCard, DetectorRun, Finding,
                                  LineageGraphSnapshot, Project)
from app.models.schemas import (ActionCardOut, ActionCardUpdate,
                                AuditRunTrigger, DetectorRunOut, FindingOut)
from app.workers.worker import run_audit_task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}", tags=["Audits"])


def check_project_exists(project_id: UUID, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/audits/run", status_code=status.HTTP_202_ACCEPTED)
async def run_audit(
    project_id: UUID,
    payload: AuditRunTrigger,
    sync: bool = Query(False, description="Run synchronously for debugging/testing"),
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)

    as_of_str = (
        payload.as_of.isoformat() if payload.as_of else datetime.now().isoformat()
    )

    if sync:
        logger.info("Executing audit synchronously...")
        # Execute task directly
        res = await run_audit_task(
            ctx={},
            project_id_str=str(project_id),
            detector_names=payload.detectors,
            as_of_iso=as_of_str,
        )
        if "Failed" in res:
            raise HTTPException(status_code=500, detail=res)

        # Fetch the run we just created
        latest_run = (
            db.query(DetectorRun)
            .filter(DetectorRun.project_id == project_id)
            .order_by(DetectorRun.started_at.desc())
            .first()
        )

        return {
            "status": "success",
            "run_id": str(latest_run.id) if latest_run else None,
            "result": res,
        }
    else:
        # Enqueue via arq
        try:
            import urllib.parse

            parsed = urllib.parse.urlparse(settings.REDIS_URL)
            redis_host = parsed.hostname or "redis"
            redis_port = parsed.port or 6379

            # Connect to Redis settings
            pool = await create_pool(RedisSettings(host=redis_host, port=redis_port))
            job = await pool.enqueue_job(
                "run_audit_task", str(project_id), payload.detectors, as_of_str
            )
            return {"status": "enqueued", "job_id": job.job_id}
        except Exception as e:
            logger.error(f"Failed to enqueue audit task: {e}")
            # Fallback to sync run if Redis fails or worker is not running
            logger.warning("Falling back to synchronous audit execution...")
            res = await run_audit_task(
                ctx={},
                project_id_str=str(project_id),
                detector_names=payload.detectors,
                as_of_iso=as_of_str,
            )
            latest_run = (
                db.query(DetectorRun)
                .filter(DetectorRun.project_id == project_id)
                .order_by(DetectorRun.started_at.desc())
                .first()
            )
            return {
                "status": "success (sync fallback)",
                "run_id": str(latest_run.id) if latest_run else None,
                "result": res,
            }


@router.get("/audits/latest", response_model=Optional[DetectorRunOut])
def get_latest_audit(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    check_project_exists(project_id, db)
    run = (
        db.query(DetectorRun)
        .filter(DetectorRun.project_id == project_id, DetectorRun.status == "completed")
        .order_by(DetectorRun.started_at.desc())
        .first()
    )
    return run


@router.get("/audits/{run_id}", response_model=DetectorRunOut)
def get_audit_by_id(
    project_id: UUID,
    run_id: UUID,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    run = (
        db.query(DetectorRun)
        .filter(DetectorRun.project_id == project_id, DetectorRun.id == run_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    return run


@router.get("/findings", response_model=List[FindingOut])
def list_findings(
    project_id: UUID,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)

    # Get latest completed run
    run = (
        db.query(DetectorRun)
        .filter(DetectorRun.project_id == project_id, DetectorRun.status == "completed")
        .order_by(DetectorRun.started_at.desc())
        .first()
    )

    if not run:
        return []

    query = db.query(Finding).filter(Finding.run_id == run.id)
    if severity:
        query = query.filter(Finding.severity == severity.lower())

    return query.all()


@router.get("/actions", response_model=List[ActionCardOut])
def list_actions(
    project_id: UUID,
    status: Optional[str] = Query(
        None, description="Filter by status (open, acknowledged, resolved)"
    ),
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)

    # Get latest completed run
    run = (
        db.query(DetectorRun)
        .filter(DetectorRun.project_id == project_id, DetectorRun.status == "completed")
        .order_by(DetectorRun.started_at.desc())
        .first()
    )

    if not run:
        return []

    query = db.query(ActionCard).filter(ActionCard.run_id == run.id)
    if status:
        query = query.filter(ActionCard.status == status.lower())

    return query.order_by(ActionCard.priority.desc()).all()


@router.patch("/actions/{action_id}", response_model=ActionCardOut)
def update_action_status(
    project_id: UUID,
    action_id: UUID,
    payload: ActionCardUpdate,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    card = db.query(ActionCard).filter(ActionCard.id == action_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Action card not found")

    card.status = payload.status.lower()
    db.commit()
    db.refresh(card)
    return card


@router.get("/lineage/latest")
def get_latest_lineage(
    project_id: UUID, db: Session = Depends(get_db), _=Depends(verify_api_key)
):
    check_project_exists(project_id, db)
    snapshot = (
        db.query(LineageGraphSnapshot)
        .filter(LineageGraphSnapshot.project_id == project_id)
        .order_by(LineageGraphSnapshot.as_of.desc())
        .first()
    )

    if not snapshot:
        raise HTTPException(
            status_code=404, detail="No lineage snapshot found. Run an audit first."
        )

    return snapshot.graph
