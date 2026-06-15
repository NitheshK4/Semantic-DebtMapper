import os
from datetime import datetime

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


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_project_crud_and_ingestion(client):
    # 1. Create project
    proj_payload = {"name": "E2E Test Classifier", "domain": "support_tickets"}
    response = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]
    assert project["name"] == "E2E Test Classifier"

    # 2. Get project details
    response = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == project_id

    # 3. Ingest model version
    mv_payload = [
        {
            "endpoint_id": "test_endpoint",
            "model_name": "xgb_test",
            "model_version": "v1.0.0",
            "deployed_at": "2026-06-01T10:00:00Z",
            "metadata": {"framework": "xgboost"},
        }
    ]
    response = client.post(
        f"/api/v1/projects/{project_id}/ingest/model-versions",
        json=mv_payload,
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 4. Clean up / Delete project
    response = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 204


def test_invalid_api_key(client):
    proj_payload = {"name": "Failed Classifier", "domain": "support_tickets"}
    bad_headers = {"X-API-Key": "wrong-key"}
    response = client.post("/api/v1/projects", json=proj_payload, headers=bad_headers)
    assert response.status_code == 403
