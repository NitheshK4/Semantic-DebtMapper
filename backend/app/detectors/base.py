from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session


class DetectorContext:
    """Context container passed to semantic debt detectors.

    Holds the database session, project identifier, and reference time
    to run the analysis against.
    """

    def __init__(self, db: Session, project_id: UUID, as_of: datetime):
        self.db = db
        self.project_id = project_id
        self.as_of = as_of


class DetectorFinding:
    """Represents a single detected semantic debt issue.

    Attributes:
        detector: Name code of the detector (CMD, ESF, RMC, HMD, GFM).
        severity: Severity level (low, medium, high, critical).
        target: Target identifier (e.g. class name, rule ID, feature name).
        payload: Context metadata outlining details of the mismatch.
    """

    def __init__(
        self, detector: str, severity: str, target: str, payload: Dict[str, Any]
    ):
        self.detector = detector
        self.severity = severity  # low, medium, high, critical
        self.target = target  # e.g. class_id, rule_id, feature_name, model_version
        self.payload = payload


class BaseDetector:
    """Abstract base class for all semantic debt detectors."""

    name: str = ""

    def run(self, ctx: DetectorContext) -> List[DetectorFinding]:
        """Execute the detection analysis.

        Args:
            ctx: The detector context containing DB session and time reference.

        Returns:
            A list of DetectorFinding objects.
        """
        raise NotImplementedError("Detectors must implement run()")
