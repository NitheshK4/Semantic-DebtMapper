from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.embeddings import get_embedding
from app.models.db_models import Concept, ConceptVersion


class ConceptRegistry:
    """Registry for managing and versioning domain concepts.

    Concepts represent business definitions or classifications (e.g., categories)
    whose meanings may change over time, requiring versioning.
    """

    @staticmethod
    def create_concept(
        db: Session,
        project_id: UUID,
        concept_key: str,
        version: str,
        definition: str,
        effective_from: datetime,
    ) -> Concept:
        """Create a new concept or a new version of an existing concept.

        If the concept does not exist, it is created. If it already exists,
        previous active versions are marked as inactive by setting `effective_to`
        to `effective_from`, and a new version is created with the updated
        definition and its vector embedding.

        Args:
            db: SQLAlchemy database session.
            project_id: The unique identifier of the project.
            concept_key: The key identifier for the concept (e.g., "urgent").
            version: The version string (e.g., "v1").
            definition: The textual description of the concept.
            effective_from: The timestamp when this version becomes active.

        Returns:
            The Concept database instance.
        """
        # Check if concept already exists
        concept = (
            db.query(Concept)
            .filter(
                Concept.project_id == project_id, Concept.concept_key == concept_key
            )
            .first()
        )

        if not concept:
            concept = Concept(project_id=project_id, concept_key=concept_key)
            db.add(concept)
            db.flush()

        # Update previous active versions to end their lifespan
        # Find version that overlaps or is the latest before this one
        db.query(ConceptVersion).filter(
            ConceptVersion.concept_id == concept.id,
            ConceptVersion.effective_to.is_(None),
        ).update({"effective_to": effective_from})

        # Calculate embedding
        emb = get_embedding(definition)

        # Create new version
        new_version = ConceptVersion(
            concept_id=concept.id,
            version=version,
            definition=definition,
            effective_from=effective_from,
            effective_to=None,
            embedding=emb,
        )
        db.add(new_version)
        db.commit()
        db.refresh(concept)
        return concept

    @staticmethod
    def list_concepts(db: Session, project_id: UUID) -> list[Concept]:
        """List all concepts associated with a project.

        Args:
            db: SQLAlchemy database session.
            project_id: The unique identifier of the project.

        Returns:
            A list of Concept database instances.
        """
        return db.query(Concept).filter(Concept.project_id == project_id).all()

    @staticmethod
    def get_concept_at_time(
        db: Session,
        project_id: UUID,
        concept_key: str,
        as_of: datetime,
    ) -> ConceptVersion | None:
        """Retrieve the active version of a concept at a specific timestamp.

        Args:
            db: SQLAlchemy database session.
            project_id: The unique identifier of the project.
            concept_key: The key identifier for the concept.
            as_of: The timestamp at which to check for an active version.

        Returns:
            The active ConceptVersion at the given time, or None if not found.
        """
        concept = (
            db.query(Concept)
            .filter(
                Concept.project_id == project_id, Concept.concept_key == concept_key
            )
            .first()
        )

        if not concept:
            return None

        # Fetch version where effective_from <= as_of and (effective_to is None or effective_to > as_of)
        return (
            db.query(ConceptVersion)
            .filter(
                ConceptVersion.concept_id == concept.id,
                ConceptVersion.effective_from <= as_of,
                (
                    (ConceptVersion.effective_to.is_(None))
                    | (ConceptVersion.effective_to > as_of)
                ),
            )
            .order_by(ConceptVersion.effective_from.desc())
            .first()
        )
