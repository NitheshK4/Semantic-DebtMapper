from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import verify_api_key
from app.models.db_models import Project
from app.sandbox.sandbox_service import SandboxService

router = APIRouter(prefix="/projects/{project_id}/sandbox", tags=["Sandbox"])


class SandboxEvaluateRequest(BaseModel):
    template: str = Field(..., description="Prompt template with {{variables}}")
    inputs: dict[str, str] = Field(default_factory=dict, description="Variables to substitute")
    mock_model: str = Field("gemini-2.5-pro", description="Simulated target model")


class SandboxEvaluateResponse(BaseModel):
    rendered_prompt: str
    mock_response: str
    warnings: list[dict] = Field(default_factory=list)


def check_project_exists(project_id: UUID, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/evaluate", response_model=SandboxEvaluateResponse, status_code=status.HTTP_200_OK)
def evaluate_prompt(
    project_id: UUID,
    payload: SandboxEvaluateRequest,
    db: Session = Depends(get_db),
    _=Depends(verify_api_key),
):
    check_project_exists(project_id, db)
    
    rendered_prompt = SandboxService.render_template(payload.template, payload.inputs)
    warnings = SandboxService.run_semantic_debt_check(db, project_id, rendered_prompt)
    mock_response = SandboxService.get_mock_completion(rendered_prompt, payload.mock_model)
    
    return SandboxEvaluateResponse(
        rendered_prompt=rendered_prompt,
        mock_response=mock_response,
        warnings=warnings
    )
