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


def test_get_project_not_found(client):
    """Test retrieving a non-existent project returns 404."""
    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_create_concept_not_found_project(client):
    """Test creating a concept for a non-existent project."""
    payload = {
        "concept_key": "high",
        "version": "v1",
        "definition": "High priority",
        "effective_from": "2026-01-01T00:00:00Z",
    }
    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/concepts",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 404


def test_run_audit_invalid_project(client):
    """Test running an audit on a non-existent project."""
    payload = {"detectors": ["cmd"]}
    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/audits/run",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 404


def test_ingest_invalid_project(client):
    """Test data ingestion to invalid project."""
    payload = [
        {
            "endpoint_id": "test",
            "model_name": "test",
            "model_version": "v1",
            "deployed_at": "2026-01-01T00:00:00Z",
            "metadata": {},
        }
    ]
    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/ingest/model-versions",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 404
