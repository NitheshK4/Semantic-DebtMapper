import logging
import re

from app.detectors.base import BaseDetector, DetectorContext, DetectorFinding
from app.models.db_models import BusinessRule, InferenceLog, ModelVersion

logger = logging.getLogger(__name__)


class GFMDetector(BaseDetector):
    """Ghost Feature Misalignment (GFM) detector.

    Detects scenarios where active post-processing business rules reference input
    features whose semantic definitions or availability have changed in newer model versions.
    """

    name = "GFM"

    def run(self, ctx: DetectorContext) -> list[DetectorFinding]:
        """Run the GFM analysis.

        Compares active rules with historical model versions to identify rules
        created for legacy models, then parses features referenced in rule expressions
        and checks if the feature schema has migrated, flagging inconsistencies.

        Args:
            ctx: DetectorContext object containing the project and database state.

        Returns:
            A list of findings indicating feature definition mismatches.
        """
        findings = []
        db = ctx.db

        # 1. Fetch active model versions
        models = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.project_id == ctx.project_id,
                ModelVersion.deployed_at <= ctx.as_of,
            )
            .all()
        )

        active_models = {}
        for m in models:
            if m.endpoint_id not in active_models:
                active_models[m.endpoint_id] = m
            elif m.deployed_at > active_models[m.endpoint_id].deployed_at:
                active_models[m.endpoint_id] = m

        # 2. Fetch active rules
        rules = (
            db.query(BusinessRule)
            .filter(
                BusinessRule.project_id == ctx.project_id,
                BusinessRule.active_from <= ctx.as_of,
                (
                    (BusinessRule.active_to.is_(None))
                    | (BusinessRule.active_to > ctx.as_of)
                ),
            )
            .all()
        )

        # Check for each endpoint
        for endpoint_id, active_model in active_models.items():
            current_schema = active_model.feature_schema_version
            if not current_schema:
                continue

            # Look for older model versions of this endpoint to see if feature schema has drifted
            older_models = [
                m
                for m in models
                if m.endpoint_id == endpoint_id
                and m.model_version != active_model.model_version
            ]
            if not older_models:
                continue

            # Sort older models to find the previous one
            older_models.sort(key=lambda x: x.deployed_at, reverse=True)
            prev_model = older_models[0]
            prev_schema = prev_model.feature_schema_version

            if prev_schema and prev_schema != current_schema:
                # Feature schema version drift occurred (e.g. fs_v5 to fs_v7)
                # Let's inspect rules for this endpoint that were created for the previous model version
                for rule in rules:
                    if rule.endpoint_id != endpoint_id:
                        continue
                    if rule.created_for_model_version == prev_model.model_version:
                        # Find which features from inference logs are referenced in the rule expression
                        # Query a sample inference log to get the available input features
                        sample_log = (
                            db.query(InferenceLog)
                            .filter(
                                InferenceLog.project_id == ctx.project_id,
                                InferenceLog.endpoint_id == endpoint_id,
                                InferenceLog.model_version
                                == active_model.model_version,
                            )
                            .first()
                        )

                        if sample_log and sample_log.input_features:
                            for feature in sample_log.input_features.keys():
                                # Check if the feature is in the rule expression
                                # Using word boundary matching to avoid substrings
                                if re.search(
                                    r"\b" + re.escape(feature) + r"\b", rule.expression
                                ):
                                    # Flag this feature as a misalignment candidate
                                    findings.append(
                                        DetectorFinding(
                                            detector=self.name,
                                            severity="medium",
                                            target=feature,
                                            payload={
                                                "feature": feature,
                                                "feature_schema_from": prev_schema,
                                                "feature_schema_to": current_schema,
                                                "rule_id": rule.rule_id,
                                                "definition_changed": True,
                                                "recommendation": f"Update the rule '{rule.rule_id}' to use new semantics for '{feature}', or retire the old feature definition in {current_schema}",
                                            },
                                        )
                                    )

        return findings
