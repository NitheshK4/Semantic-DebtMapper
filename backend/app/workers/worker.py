import asyncio
import logging
from datetime import datetime

from arq import cron

from app.core.config import settings
from app.core.db import SessionLocal
from app.detectors.base import DetectorContext
from app.detectors.cmd_detector import CMDDetector
from app.detectors.esf_detector import ESFDetector
from app.detectors.gfm_detector import GFMDetector
from app.detectors.hmd_detector import HMDDetector
from app.detectors.rmc_detector import RMCDetector
from app.models.db_models import DetectorRun, Finding
from app.services.lineage_builder import LineageBuilder
from app.services.recommendation_engine import RecommendationEngine
from app.services.scoring_engine import ScoringEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_audit_task(
    ctx: dict, project_id_str: str, detector_names: list, as_of_iso: str
) -> str:
    """
    Asynchronous task to run a semantic lineage audit.
    """
    logger.info(
        f"Starting async audit for project {project_id_str} with detectors {detector_names}"
    )
    db = SessionLocal()
    try:
        from uuid import UUID

        project_id = UUID(project_id_str)
        as_of = datetime.fromisoformat(as_of_iso) if as_of_iso else datetime.now()

        # 1. Create detector run in database
        run = DetectorRun(
            project_id=project_id, started_at=datetime.now(), status="running"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 2. Rebuild the lineage graph snapshot for this point in time
        logger.info(f"Rebuilding lineage graph snapshot for run {run.id}")
        LineageBuilder.build_graph(db, project_id, as_of)

        # 3. Instantiate and run selected detectors
        detector_classes = {
            "CMD": CMDDetector,
            "ESF": ESFDetector,
            "RMC": RMCDetector,
            "HMD": HMDDetector,
            "GFM": GFMDetector,
        }

        det_ctx = DetectorContext(db, project_id, as_of)
        findings_count = 0

        for name in detector_names:
            if name in detector_classes:
                logger.info(f"Running detector: {name}")
                detector = detector_classes[name]()
                try:
                    results = detector.run(det_ctx)
                    for r in results:
                        finding = Finding(
                            run_id=run.id,
                            detector=r.detector,
                            severity=r.severity,
                            target=r.target,
                            payload=r.payload,
                        )
                        db.add(finding)
                        findings_count += 1
                except Exception as ex:
                    logger.error(f"Error running detector {name}: {ex}", exc_info=True)

        db.commit()
        logger.info(f"Detectors completed. Total findings: {findings_count}")

        # 4. Compute composite score (SDS)
        logger.info("Computing Semantic Debt Score (SDS)...")
        ScoringEngine.compute_sds(db, run.id)

        # 5. Generate prioritized recommended actions (Action Cards)
        logger.info("Generating recommendation cards...")
        RecommendationEngine.generate_recommendations(db, run.id)

        # 6. Mark run as completed
        run.finished_at = datetime.now()
        run.status = "completed"
        db.commit()
        logger.info(f"Audit run {run.id} completed successfully.")
        return f"Completed run {run.id}"

    except Exception as e:
        logger.error(f"Audit run failed: {e}", exc_info=True)
        # Attempt to mark run as failed
        try:
            if "run" in locals():
                run.finished_at = datetime.now()
                run.status = "failed"
                db.commit()
        except Exception as rollback_ex:
            logger.error(f"Failed to write failure status: {rollback_ex}")
        return f"Failed: {e}"
    finally:
        db.close()


class WorkerSettings:
    """
    Settings for the arq background worker.
    """

    functions = [run_audit_task]
    redis_settings = None

    @classmethod
    def on_startup(cls, ctx):
        # Parse host/port from REDIS_URL
        # Default redis url: redis://redis:6379/0
        import urllib.parse

        from redis import Redis

        parsed = urllib.parse.urlparse(settings.REDIS_URL)
        host = parsed.hostname or "redis"
        port = parsed.port or 6379
        db = int(parsed.path.lstrip("/")) if parsed.path else 0
        cls.redis_settings = settings.REDIS_URL
        logger.info(f"Worker connected to Redis at {host}:{port}/{db}")
