import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.main import app
from app.services.concept_registry import ConceptRegistry
from app.sandbox.sandbox_service import SandboxService
from datetime import datetime

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

API_KEY = settings.API_KEY
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def test_template_rendering():
    """Test standard template variable substitution logic."""
    template = "Hello {{name}}, welcome to {{city}}!"
    inputs = {"name": "Alice", "city": "Wonderland"}
    rendered = SandboxService.render_template(template, inputs)
    assert rendered == "Hello Alice, welcome to Wonderland!"

    # Test single-bracket rendering fallback
    template_single = "Alert: {alert_name} resolved."
    inputs_single = {"alert_name": "Outage"}
    rendered_single = SandboxService.render_template(template_single, inputs_single)
    assert rendered_single == "Alert: Outage resolved."

def test_mock_completions():
    """Test simulated model responses based on keyword prompts."""
    # Test class classification
    prompt = "Classify this ticket SLA: System outage on main portal."
    res = SandboxService.get_mock_completion(prompt, "gemini-2.5-flash")
    assert "[gemini-2.5-flash Simulation]" in res
    assert "CRITICAL" in res

    # Test default fallback
    prompt_default = "Hello what is the capital of France?"
    res_default = SandboxService.get_mock_completion(prompt_default, "gpt-4o")
    assert "[gpt-4o Completion]" in res_default

def test_sandbox_evaluation_endpoint(client):
    """Test endpoint validation and warning generation for semantic debt."""
    # 1. Create temporary project
    proj_payload = {"name": "Sandbox Test Project", "domain": "support_tickets"}
    response = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]

    try:
        # 2. Ingest concepts via endpoint to populate Concept Registry
        # Urgent V1 (2h response)
        payload_v1 = {
            "concept_key": "urgent",
            "version": "v1",
            "definition": "Ticket requires response within two hours per SLA policy v2. Includes VIP escalations.",
            "effective_from": "2026-01-01T00:00:00Z"
        }
        res_v1 = client.post(f"/api/v1/projects/{project_id}/concepts", json=payload_v1, headers=headers)
        assert res_v1.status_code == 200

        # Urgent V2 (4h response, active)
        payload_v2 = {
            "concept_key": "urgent",
            "version": "v2",
            "definition": "Ticket requires response within four hours per SLA policy v3. Includes VIP escalations and payment failures.",
            "effective_from": "2026-03-01T00:00:00Z"
        }
        res_v2 = client.post(f"/api/v1/projects/{project_id}/concepts", json=payload_v2, headers=headers)
        assert res_v2.status_code == 200

        # 3. Call Sandbox Evaluate Endpoint with prompt containing legacy / conflict phrases
        sandbox_payload = {
            "template": "Analyze ticket: {{ticket_text}}. Urgent rule: Response must be within two hours per SLA policy v2 guidelines.",
            "inputs": {
                "ticket_text": "Need help resetting my password."
            },
            "mock_model": "gemini-2.5-pro"
        }

        eval_response = client.post(
            f"/api/v1/projects/{project_id}/sandbox/evaluate",
            json=sandbox_payload,
            headers=headers
        )
        assert eval_response.status_code == 200
        
        data = eval_response.json()
        assert "two hours" in data["rendered_prompt"]
        assert "Need help resetting" in data["rendered_prompt"]
        assert "[gemini-2.5-pro Simulation]" in data["mock_response"]
        
        # Check warnings generated
        warnings = data["warnings"]
        assert len(warnings) > 0
        
        # Verify that legacy concept reference is flagged
        legacy_warning = next((w for w in warnings if w["type"] == "LEGACY_CONCEPT_REFERENCE"), None)
        assert legacy_warning is not None
        assert "urgent" in legacy_warning["concept"]
        assert "v1" in legacy_warning["message"]

    finally:
        # 4. Clean up / Delete project
        client.delete(f"/api/v1/projects/{project_id}", headers=headers)
