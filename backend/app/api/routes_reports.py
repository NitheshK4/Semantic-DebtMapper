from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_api_key
from app.models.db_models import Project
from app.services.report_service import ReportService

router = APIRouter(prefix="/projects/{project_id}/reports", tags=["Reports"])


def check_project_exists(project_id: UUID, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/weekly", response_class=Response)
def get_weekly_report_markdown(
    project_id: UUID,
    run_id: Optional[UUID] = Query(None, description="Filter report by specific detector run ID"),
    db: Session = Depends(get_db),
    _=Depends(verify_api_key)
):
    check_project_exists(project_id, db)
    report_md = ReportService.get_weekly_report_markdown(db, project_id, run_id=run_id)
    return Response(content=report_md, media_type="text/markdown")


@router.get("/weekly.pdf", response_class=Response)
def get_weekly_report_pdf(
    project_id: UUID,
    run_id: Optional[UUID] = Query(None, description="Filter report by specific detector run ID"),
    db: Session = Depends(get_db),
    _=Depends(verify_api_key)
):
    check_project_exists(project_id, db)
    pdf_bytes = ReportService.get_weekly_report_pdf(db, project_id, run_id=run_id)

    headers = {
        "Content-Disposition": f"attachment; filename=weekly_report_{project_id}.pdf"
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
