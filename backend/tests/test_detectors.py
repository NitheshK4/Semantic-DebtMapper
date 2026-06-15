import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from app.detectors.base import DetectorContext
from app.detectors.cmd_detector import CMDDetector
from app.detectors.esf_detector import ESFDetector
from app.detectors.gfm_detector import GFMDetector
from app.detectors.hmd_detector import HMDDetector
from app.detectors.rmc_detector import RMCDetector
from app.models.db_models import (BusinessRule, Finding, LabelSchema,
                                  ModelVersion)
from app.services.scoring_engine import ScoringEngine


class TestDetectors(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()
        self.project_id = uuid4()
        self.as_of = datetime.now()
        self.ctx = DetectorContext(self.db, self.project_id, self.as_of)

    def test_cmd_detector(self):
        # 1. Setup mock schemas
        schema1 = MagicMock(spec=LabelSchema)
        schema1.schema_version = "v2"
        schema1.effective_from = self.as_of - timedelta(days=30)
        schema1.payload = {
            "classes": [
                {
                    "class_id": "urgent",
                    "display_name": "Urgent",
                    "definition": "Respond in 2h",
                }
            ]
        }

        schema2 = MagicMock(spec=LabelSchema)
        schema2.schema_version = "v3"
        schema2.effective_from = self.as_of - timedelta(days=10)
        schema2.payload = {
            "classes": [
                {
                    "class_id": "urgent",
                    "display_name": "Urgent",
                    "definition": "Respond in 4h. Outdated SLA definition now relaxed.",
                }
            ]
        }

        self.db.query().filter().order_by().all.return_value = [schema1, schema2]

        # Create mock inference logs
        mock_inferences_before = [
            MagicMock(model_output={"predicted_class": "urgent"}) for _ in range(100)
        ]
        mock_inferences_after = [
            MagicMock(model_output={"predicted_class": "urgent"}) for _ in range(100)
        ]
        self.db.query().filter().all.side_effect = [
            mock_inferences_before,
            mock_inferences_after,
        ]

        # Mock override counts
        self.db.query().filter().count.side_effect = [
            5,  # overrides before
            25,  # overrides after (spike!)
        ]

        detector = CMDDetector()
        findings = detector.run(self.ctx)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].detector, "CMD")
        self.assertEqual(findings[0].target, "urgent")
        self.assertEqual(findings[0].severity, "high")
        self.assertLess(findings[0].payload["definition_similarity"], 0.75)

    def test_esf_detector(self):
        model = MagicMock(spec=ModelVersion)
        model.endpoint_id = "support_rag"
        model.model_version = "emb_v5"
        model.deployed_at = self.as_of - timedelta(days=15)
        model.metadata = {"index_version": "emb_v3"}  # lags version

        self.db.query().filter().all.return_value = [model]

        detector = ESFDetector()
        findings = detector.run(self.ctx)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].detector, "ESF")
        self.assertEqual(findings[0].target, "support_rag")
        self.assertEqual(findings[0].severity, "critical")

    def test_rmc_detector(self):
        rule = MagicMock(spec=BusinessRule)
        rule.rule_id = "threshold_urgent"
        rule.endpoint_id = "ticket_classifier"
        rule.created_for_model_version = "v3.1.0"
        rule.expression = "if score >= 0.82 then decision='urgent'"
        rule.active_from = self.as_of - timedelta(days=40)
        rule.active_to = None

        model = MagicMock(spec=ModelVersion)
        model.endpoint_id = "ticket_classifier"
        model.model_version = "v4.2.0"  # drift version
        model.deployed_at = self.as_of - timedelta(days=10)

        self.db.query().filter().all.side_effect = [
            [rule],  # rules
            [model],  # models
            [],  # inferences (triggers mock fallback of 0.27)
        ]

        detector = RMCDetector()
        findings = detector.run(self.ctx)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].detector, "RMC")
        self.assertEqual(findings[0].target, "threshold_urgent")
        self.assertEqual(findings[0].severity, "high")
        self.assertEqual(findings[0].payload["flip_rate_near_threshold"], 0.27)

    def test_scoring_engine(self):
        f1 = Finding(detector="CMD", severity="high")
        f2 = Finding(detector="ESF", severity="critical")
        self.db.query().filter().all.return_value = [f1, f2]

        run = MagicMock()
        self.db.query().filter().first.return_value = run

        score = ScoringEngine.compute_sds(self.db, uuid4())
        # Score calculation: 100 * (0.30 * 0.75 + 0.25 * 1.0) = 47.5
        self.assertEqual(score, 47.5)
        self.assertEqual(run.sds_score, 47.5)


if __name__ == "__main__":
    unittest.main()
