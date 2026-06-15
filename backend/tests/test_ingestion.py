from datetime import datetime
from uuid import uuid4

import pytest

from app.core.db import SessionLocal, engine
from app.models.db_models import Base, ModelVersion, Project
from app.models.schemas import ModelVersionIngest
from app.services.ingestion_service import IngestionService


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_ingest_model_versions(db_session):
    """Test ingestion of model versions into the database with conflict handling."""
    # Create project
    proj_id = uuid4()
    project = Project(id=proj_id, name="Test Project", domain="test")
    db_session.add(project)
    db_session.commit()

    # Ingest model version
    payload = [
        ModelVersionIngest(
            endpoint_id="ep1",
            model_name="xgb",
            model_version="v1",
            feature_schema_version="v1",
            deployed_at=datetime.utcnow(),
            metadata={"test": True},
        )
    ]
    IngestionService.ingest_model_versions(db_session, proj_id, payload)

    mv = db_session.query(ModelVersion).filter_by(project_id=proj_id).first()
    assert mv is not None
    assert mv.endpoint_id == "ep1"
    assert mv.model_name == "xgb"
    assert mv.model_metadata["test"] is True

    # Test upsert/conflict
    payload[0].metadata = {"test": False}
    IngestionService.ingest_model_versions(db_session, proj_id, payload)

    mv_updated = db_session.query(ModelVersion).filter_by(project_id=proj_id).first()
    assert mv_updated.model_metadata["test"] is False
