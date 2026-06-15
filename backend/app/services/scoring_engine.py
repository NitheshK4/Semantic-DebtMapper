import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db_models import DetectorRun, Finding

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Engine responsible for computing the Semantic Debt Score (SDS).

    SDS is computed using a weighted average of the maximum severity of
    findings detected across five specific detectors: CMD, ESF, RMC, HMD, GFM.
    """

    SEVERITY_MAP = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.00}

    @staticmethod
    def compute_sds(db: Session, run_id: UUID) -> float:
        """Compute the Semantic Debt Score (SDS) for a given detector run.

        Fetches all findings for the specified run, maps their severities,
        determines the maximum severity score per detector, scales them by their
        respective weights, updates the run's SDS score/summary in the database,
        and returns the rounded score.

        Weights used:
        - Class Meaning Drift (CMD): 30%
        - Embedding Space Fracture (ESF): 25%
        - Rule-Model Conflict (RMC): 20%
        - Human-Model Divergence (HMD): 15%
        - Ghost Feature Misalignment (GFM): 10%

        Args:
            db: SQLAlchemy database session.
            run_id: Unique identifier of the detector run.

        Returns:
            The calculated SDS score rounded to 1 decimal place (0.0 to 100.0).
        """
        # Fetch findings for the run
        findings = db.query(Finding).filter(Finding.run_id == run_id).all()

        # Group by detector name and get max severity
        detector_max_severity = {
            "CMD": 0.0,
            "ESF": 0.0,
            "RMC": 0.0,
            "HMD": 0.0,
            "GFM": 0.0,
        }

        for f in findings:
            det = f.detector
            sev_str = f.severity.lower()
            sev_val = ScoringEngine.SEVERITY_MAP.get(sev_str, 0.0)
            if det in detector_max_severity:
                if sev_val > detector_max_severity[det]:
                    detector_max_severity[det] = sev_val

        # Compute SDS using weights from specification
        # SDS = 100 * (0.30 * CMD + 0.25 * ESF + 0.20 * RMC + 0.15 * HMD + 0.10 * GFM)
        sds = 100 * (
            0.30 * detector_max_severity["CMD"]
            + 0.25 * detector_max_severity["ESF"]
            + 0.20 * detector_max_severity["RMC"]
            + 0.15 * detector_max_severity["HMD"]
            + 0.10 * detector_max_severity["GFM"]
        )

        # Update the run score
        run = db.query(DetectorRun).filter(DetectorRun.id == run_id).first()
        if run:
            run.sds_score = round(sds, 1)
            # Add summary breakdown
            run.summary = {
                "breakdown": {
                    "CMD": detector_max_severity["CMD"],
                    "ESF": detector_max_severity["ESF"],
                    "RMC": detector_max_severity["RMC"],
                    "HMD": detector_max_severity["HMD"],
                    "GFM": detector_max_severity["GFM"],
                },
                "findings_count": len(findings),
            }
            db.commit()

        return round(sds, 1)
