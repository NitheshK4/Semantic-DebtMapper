import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

API_KEY = settings.API_KEY
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def test_full_mitigation_workflow(client):
    # 1. Create project
    proj_payload = {"name": "Test Mitigation Project", "domain": "support_tickets"}
    response = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]

    # 2. Seed data
    response = client.post(f"/api/v1/projects/{project_id}/seed", headers=headers)
    assert response.status_code == 200

    # 3. Run initial audit
    audit_trigger = {
        "as_of": "2026-06-15T00:00:00Z",
        "detectors": ["CMD", "ESF", "RMC", "HMD", "GFM"]
    }
    response = client.post(f"/api/v1/projects/{project_id}/audits/run?sync=true", json=audit_trigger, headers=headers)
    assert response.status_code in (200, 202)

    # Verify SDS is non-zero
    response = client.get(f"/api/v1/projects/{project_id}/audits/latest", headers=headers)
    assert response.status_code == 200
    latest_run = response.json()
    print("Initial SDS score:", latest_run["sds_score"])
    assert latest_run["sds_score"] > 0.0

    # 4. Fetch the action cards
    response = client.get(f"/api/v1/projects/{project_id}/actions?status=open", headers=headers)
    assert response.status_code == 200
    action_cards = response.json()
    assert len(action_cards) > 0

    # 5. Resolve each action card one by one
    for card in action_cards:
        action_id = card["id"]
        patch_payload = {"status": "resolved"}
        response = client.patch(f"/api/v1/projects/{project_id}/actions/{action_id}", json=patch_payload, headers=headers)
        assert response.status_code == 200

    # 6. Verify that all findings are resolved and SDS is 0.0
    response = client.get(f"/api/v1/projects/{project_id}/audits/latest", headers=headers)
    assert response.status_code == 200
    mitigated_run = response.json()
    assert mitigated_run["sds_score"] == 0.0

    # Clean up the project
    client.delete(f"/api/v1/projects/{project_id}", headers=headers)
