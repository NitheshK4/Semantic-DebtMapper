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


def test_create_concept_invalid_key(client):
    """Test creating a concept with invalid characters in key fails validation."""
    payload = {
        "concept_key": "high PRIORITY!",
        "version": "v1",
        "definition": "High priority",
        "effective_from": "2026-01-01T00:00:00Z",
    }
    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/concepts",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 422


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


def test_health_check(client):
    """Test that the health check endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_patch_action_card_not_found(client):
    """Test patching a non-existent action card returns 404."""
    from uuid import uuid4
    payload = {"status": "acknowledged", "notes": "Working on this"}
    response = client.patch(
        f"/api/v1/projects/{uuid4()}/actions/{uuid4()}",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 404


def test_paginated_and_filtered_findings_and_actions(client):
    """Test that findings and actions API routes correctly handle limit, offset, and detector filtering."""
    # 1. Create temporary project
    proj_payload = {"name": "Test Pagination Project", "domain": "support_tickets"}
    res = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    try:
        # 2. Seed data
        res = client.post(f"/api/v1/projects/{project_id}/seed", headers=headers)
        assert res.status_code == 200

        # 3. Run audit synchronously
        run_payload = {"detectors": ["CMD", "ESF", "RMC", "HMD", "GFM"]}
        res = client.post(
            f"/api/v1/projects/{project_id}/audits/run?sync=true",
            json=run_payload,
            headers=headers,
        )
        assert res.status_code in (200, 202)

        # 4. Get all findings to know total count
        res = client.get(f"/api/v1/projects/{project_id}/findings", headers=headers)
        assert res.status_code == 200
        all_findings = res.json()
        assert len(all_findings) > 0

        # Test Findings Pagination limit
        res = client.get(
            f"/api/v1/projects/{project_id}/findings?limit=2", headers=headers
        )
        assert res.status_code == 200
        limit_findings = res.json()
        assert len(limit_findings) <= 2

        # Test Findings Pagination offset
        if len(all_findings) > 1:
            res = client.get(
                f"/api/v1/projects/{project_id}/findings?limit=1&offset=1",
                headers=headers,
            )
            assert res.status_code == 200
            offset_findings = res.json()
            assert len(offset_findings) == 1
            assert offset_findings[0]["id"] == all_findings[1]["id"]

        # Test Findings Filter by Detector
        res = client.get(
            f"/api/v1/projects/{project_id}/findings?detector=CMD", headers=headers
        )
        assert res.status_code == 200
        cmd_findings = res.json()
        for f in cmd_findings:
            assert f["detector"] == "CMD"

        # Test Actions Pagination
        res = client.get(f"/api/v1/projects/{project_id}/actions", headers=headers)
        assert res.status_code == 200
        all_actions = res.json()
        assert len(all_actions) > 0

        res = client.get(
            f"/api/v1/projects/{project_id}/actions?limit=1", headers=headers
        )
        assert res.status_code == 200
        limit_actions = res.json()
        assert len(limit_actions) <= 1

        if len(all_actions) > 1:
            res = client.get(
                f"/api/v1/projects/{project_id}/actions?limit=1&offset=1",
                headers=headers,
            )
            assert res.status_code == 200
            offset_actions = res.json()
            assert len(offset_actions) == 1
            assert offset_actions[0]["id"] == all_actions[1]["id"]

    finally:
        # Cleanup
        client.delete(f"/api/v1/projects/{project_id}", headers=headers)


def test_concurrent_audit_runs_prevention(client):
    """Test that starting an audit run fails with 409 Conflict if there's already an active run."""
    # 1. Create project
    proj_payload = {"name": "Test Concurrent Runs Project", "domain": "support_tickets"}
    res = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    from app.core.db import SessionLocal
    from app.models.db_models import DetectorRun
    from datetime import datetime
    import uuid

    db = SessionLocal()
    try:
        # 2. Insert a dummy pending/running detector run
        active_run = DetectorRun(
            project_id=uuid.UUID(project_id),
            started_at=datetime.utcnow(),
            status="running",
        )
        db.add(active_run)
        db.commit()

        # 3. Attempt to trigger another run
        run_payload = {"detectors": ["CMD"]}
        res = client.post(
            f"/api/v1/projects/{project_id}/audits/run?sync=true",
            json=run_payload,
            headers=headers,
        )
        assert res.status_code == 409
        assert "already active" in res.json()["detail"]

    finally:
        db.close()
        # Cleanup project (which cascades and deletes the detector run)
        client.delete(f"/api/v1/projects/{project_id}", headers=headers)


def test_findings_export_endpoint(client):
    """Test that the findings export API route returns correctly structured project and findings data."""
    # 1. Create project
    proj_payload = {"name": "Test Export Project", "domain": "support_tickets"}
    res = client.post("/api/v1/projects", json=proj_payload, headers=headers)
    assert res.status_code == 201
    project_id = res.json()["id"]

    try:
        # 2. Seed data
        res = client.post(f"/api/v1/projects/{project_id}/seed", headers=headers)
        assert res.status_code == 200

        # 3. Run audit synchronously
        run_payload = {"detectors": ["CMD", "ESF", "RMC", "HMD", "GFM"]}
        res = client.post(
            f"/api/v1/projects/{project_id}/audits/run?sync=true",
            json=run_payload,
            headers=headers,
        )
        assert res.status_code in (200, 202)

        # 4. Trigger export
        res = client.get(
            f"/api/v1/projects/{project_id}/findings/export", headers=headers
        )
        assert res.status_code == 200
        data = res.json()
        assert data["project_id"] == project_id
        assert data["project_name"] == "Test Export Project"
        assert "findings" in data
        assert len(data["findings"]) > 0
        assert "latest_run" in data
        assert data["latest_run"]["findings_count"] == len(data["findings"])

    finally:
        # Cleanup
        client.delete(f"/api/v1/projects/{project_id}", headers=headers)
