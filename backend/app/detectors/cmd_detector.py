import logging

import numpy as np

from app.core.embeddings import get_embedding
from app.detectors.base import BaseDetector, DetectorContext, DetectorFinding
from app.models.db_models import InferenceLog, LabelSchema, OverrideLog

logger = logging.getLogger(__name__)


class CMDDetector(BaseDetector):
    """Class Meaning Drift (CMD) detector.

    Identifies instances where a class definition in the label schema has shifted
    semantically between schema updates, leading to a rise in human override rates.
    """

    name = "CMD"

    def run(self, ctx: DetectorContext) -> list[DetectorFinding]:
        """Run the CMD analysis.

        Compares consecutive label schema versions to evaluate semantic similarity
        of class definitions using sentence embeddings. Cross-references this with
        historical inference logs and human overrides to evaluate changes in override
        behavior post-update.

        Args:
            ctx: DetectorContext object containing the project and database state.

        Returns:
            A list of findings indicating drifted class meanings.
        """
        findings = []
        db = ctx.db

        # Fetch label schemas ordered by effective_from
        schemas = (
            db.query(LabelSchema)
            .filter(
                LabelSchema.project_id == ctx.project_id,
                LabelSchema.effective_from <= ctx.as_of,
            )
            .order_by(LabelSchema.effective_from.asc())
            .all()
        )

        if len(schemas) < 2:
            return findings

        # Group classes by schema_version
        schema_versions = {}
        for s in schemas:
            classes = s.payload.get("classes", [])
            schema_versions[s.schema_version] = {
                "effective_from": s.effective_from,
                "classes": {c["class_id"]: c for c in classes},
            }

        # Compare consecutive pairs of schemas
        for i in range(len(schemas) - 1):
            s1 = schemas[i]
            s2 = schemas[i + 1]

            v1_data = schema_versions[s1.schema_version]
            v2_data = schema_versions[s2.schema_version]

            t1 = v1_data["effective_from"]
            t2 = v2_data["effective_from"]
            t3 = ctx.as_of

            for class_id, cls_def2 in v2_data["classes"].items():
                if class_id not in v1_data["classes"]:
                    continue

                cls_def1 = v1_data["classes"][class_id]
                def1 = cls_def1.get("definition", "")
                def2 = cls_def2.get("definition", "")

                if not def1 or not def2:
                    continue

                # Embed definitions and compute cosine similarity
                emb1 = np.array(get_embedding(def1))
                emb2 = np.array(get_embedding(def2))

                norm1 = np.linalg.norm(emb1)
                norm2 = np.linalg.norm(emb2)
                if norm1 > 0 and norm2 > 0:
                    sim = float(np.dot(emb1, emb2) / (norm1 * norm2))
                else:
                    sim = 1.0

                # Compute override rate delta before vs after
                # Before: [t1, t2]
                # After: [t2, t3]
                def get_override_rate(start, end):
                    # Fetch inferences in time range
                    inferences = (
                        db.query(InferenceLog)
                        .filter(
                            InferenceLog.project_id == ctx.project_id,
                            InferenceLog.ts >= start,
                            InferenceLog.ts < end,
                        )
                        .all()
                    )

                    inf_count = sum(
                        1
                        for inf in inferences
                        if (inf.model_output or {}).get("predicted_class") == class_id
                    )

                    if inf_count == 0:
                        return 0.0

                    # Overridden from or to class_id
                    override_count = (
                        db.query(OverrideLog)
                        .filter(
                            OverrideLog.project_id == ctx.project_id,
                            OverrideLog.ts >= start,
                            OverrideLog.ts < end,
                            (
                                (OverrideLog.override_class == class_id)
                                | (OverrideLog.original_decision == class_id)
                            ),
                        )
                        .count()
                    )

                    return float(override_count) / inf_count

                rate_before = get_override_rate(t1, t2)
                rate_after = get_override_rate(t2, t3)
                override_delta = rate_after - rate_before

                # Trigger if similarity < 0.92 and override_delta > 0.10
                # If we have no inferences (delta = 0), but similarity is very low, we can still flag it
                # but to match spec: sim < 0.92 + override_delta > 0.10
                if sim < 0.92 and override_delta > 0.10:
                    severity = "high" if override_delta > 0.15 else "medium"
                    findings.append(
                        DetectorFinding(
                            detector=self.name,
                            severity=severity,
                            target=class_id,
                            payload={
                                "class_id": class_id,
                                "schema_from": s1.schema_version,
                                "schema_to": s2.schema_version,
                                "definition_similarity": round(sim, 2),
                                "override_rate_delta": round(override_delta, 2),
                                "override_rate_before": round(rate_before, 2),
                                "override_rate_after": round(rate_after, 2),
                                "recommendation": f"Relabel historical subset for class '{class_id}' between {t1.date()} and {t2.date()}",
                            },
                        )
                    )

        return findings
