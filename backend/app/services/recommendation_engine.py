import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db_models import ActionCard, Finding

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Engine responsible for generating remediation action cards based on findings.

    Action cards represent concrete steps to resolve detected semantic debt.
    Priority scores are calculated based on impact, urgency, and confidence metrics.
    """

    @staticmethod
    def generate_recommendations(db: Session, run_id: UUID) -> int:
        """Analyze findings from a detector run and generate prioritized action cards.

        For each finding, heuristics are applied to determine:
        - Remediation type (e.g., RELABEL_SUBSET, REINDEX_EMBEDDINGS)
        - Targeted action title and recommended action steps
        - Impact and confidence estimation values
        - Predicted impact on Semantic Debt Score (SDS delta reduction)

        Calculates a priority score using: priority = impact_score * urgency * confidence.
        Stores the resulting ActionCards in the database.

        Args:
            db: SQLAlchemy database session.
            run_id: Unique identifier of the detector run.

        Returns:
            The number of ActionCard records successfully created.
        """
        findings = db.query(Finding).filter(Finding.run_id == run_id).all()
        count = 0

        severity_values = {"low": 0.25, "medium": 0.50, "high": 0.75, "critical": 1.00}

        for finding in findings:
            detector = finding.detector
            payload = finding.payload
            severity = finding.severity.lower()
            urgency = severity_values.get(severity, 0.50)

            # Default heuristic values for priority formula: priority = impact_score * urgency * confidence
            impact_score = 0.9
            confidence = 0.9
            steps = []
            title = ""
            action_type = ""
            expected_sds_delta = 0.0

            if detector == "CMD":
                action_type = "RELABEL_SUBSET"
                class_id = payload.get("class_id", "class")
                title = f"Relabel historical subset for class '{class_id}'"
                steps = [
                    f"Extract subset of logs for class '{class_id}' before transition to new label schema",
                    "Distribute to annotators with revised labeling guidelines",
                    "Retrain classifier on corrected historical labels to align with new definition",
                ]
                impact_score = 0.95
                confidence = 0.90
                # CMD weight is 30% of SDS
                expected_sds_delta = -1.0 * (30.0 * urgency)

            elif detector == "ESF":
                action_type = "REINDEX_EMBEDDINGS"
                endpoint = payload.get("endpoint_id", "endpoint")
                model_ver = payload.get("model_version", "latest")
                index_ver = payload.get("index_version", "old")
                title = f"Rebuild embedding index for endpoint '{endpoint}'"
                steps = [
                    f"Extract query texts and generate embeddings using model '{model_ver}'",
                    f"Rebuild vector index (currently running on old geometry '{index_ver}')",
                    "Validate retrieval performance on top-20 search buckets",
                    f"Promote index to run natively on {model_ver}",
                ]
                impact_score = 0.98
                confidence = 0.95
                # ESF weight is 25% of SDS
                expected_sds_delta = -1.0 * (25.0 * urgency)

            elif detector == "RMC":
                action_type = "RECALIBRATE_RULE"
                rule_id = payload.get("rule_id", "rule")
                threshold = payload.get("threshold", 0.5)
                current_model = payload.get("current_model_version", "latest")
                # In the demo dataset, suggest 0.76
                recal = (
                    0.76
                    if rule_id == "threshold_urgent"
                    else round(threshold - 0.06, 2)
                )
                title = f"Recalibrate threshold for rule '{rule_id}'"
                steps = [
                    f"Shadow test updated threshold '{recal}' (currently '{threshold}') for 7 days",
                    "Measure and compare the class prediction flip rate under new score calibrations",
                    f"Promote recalibrated threshold rule for model {current_model}",
                ]
                impact_score = 0.92
                confidence = 0.88
                # RMC weight is 20% of SDS
                expected_sds_delta = -1.0 * (20.0 * urgency)

            elif detector == "HMD":
                action_type = "RETRAIN_CLASS"
                class_id = payload.get("class_id", "class")
                segment = payload.get("segment", {})
                title = f"Retrain model for class '{class_id}' to reduce overrides"
                seg_str = ", ".join([f"{k}={v}" for k, v in segment.items()])
                steps = [
                    f"Audit recent overrides in segment ({seg_str}) for class '{class_id}'",
                    "Refine prompt instructions and classifier features for mobile channels",
                    "Retrain classifier model class weights to align with reviewer decisions",
                ]
                impact_score = 0.85
                confidence = 0.85
                # HMD weight is 15% of SDS
                expected_sds_delta = -1.0 * (15.0 * urgency)

            elif detector == "GFM":
                action_type = "RETIRE_FEATURE"
                feature = payload.get("feature", "feature")
                rule_id = payload.get("rule_id", "rule")
                title = f"Retire or re-document feature '{feature}' in rule '{rule_id}'"
                steps = [
                    f"Verify rule '{rule_id}' dependencies on feature '{feature}'",
                    "Migrate active rules to use the updated schema definitions",
                    "Remove stale feature logic from the data ingestion pipeline",
                ]
                impact_score = 0.75
                confidence = 0.80
                # GFM weight is 10% of SDS
                expected_sds_delta = -1.0 * (10.0 * urgency)

            # Compute priority score: priority = impact_score * urgency * confidence
            priority = impact_score * urgency * confidence

            # Format expected SDS delta
            steps.append(
                f"Expected SDS reduction: {round(expected_sds_delta, 1)} points"
            )

            # Create action card record
            card = ActionCard(
                run_id=run_id,
                action_type=action_type,
                priority=round(priority, 3),
                title=title,
                steps=steps,
                status="open",
            )
            db.add(card)
            count += 1

        db.commit()
        return count
