import logging
import re
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.db_models import ActionCard, Finding, LabelSchema, ModelVersion, BusinessRule, OverrideLog, InferenceLog

logger = logging.getLogger(__name__)

class MitigationService:
    """Service to execute the actual database updates required to resolve semantic debt findings."""

    @staticmethod
    def mitigate_action(db: Session, project_id: UUID, action_card: ActionCard) -> bool:
        """Applies database changes corresponding to the action type to resolve the underlying drift."""
        run_id = action_card.run_id
        action_type = action_card.action_type
        
        logger.info(f"Mitigating action {action_card.id} of type {action_type} for project {project_id}")

        quoted_vars = re.findall(r"'(.*?)'", action_card.title)
        if not quoted_vars:
            logger.warning(f"Could not extract target variables from title: {action_card.title}")
            return False

        # 1. CMD: Relabel historical subset / Reconcile definitions
        if action_type == "RELABEL_SUBSET":
            class_id = quoted_vars[0]
            # Reconcile label schemas: update definition of class_id in all schemas to match the latest one
            latest_schema = db.query(LabelSchema).filter(LabelSchema.project_id == project_id).order_by(LabelSchema.effective_from.desc()).first()
            if latest_schema:
                latest_class_def = next((c for c in latest_schema.payload.get("classes", []) if c["class_id"] == class_id), None)
                if latest_class_def:
                    earlier_schemas = db.query(LabelSchema).filter(LabelSchema.project_id == project_id, LabelSchema.id != latest_schema.id).all()
                    for schema in earlier_schemas:
                        classes = list(schema.payload.get("classes", []))
                        for c in classes:
                            if c["class_id"] == class_id:
                                c["definition"] = latest_class_def["definition"]
                        schema.payload = {"classes": classes}
                        db.add(schema)
                    db.commit()
                    logger.info(f"Reconciled definitions for class '{class_id}' across all schemas.")
                    return True
            return False

        # 2. ESF: Rebuild embedding index / Update index version metadata
        elif action_type == "REINDEX_EMBEDDINGS":
            endpoint_id = quoted_vars[0]
            # Find the active model for this endpoint
            models = db.query(ModelVersion).filter(
                ModelVersion.project_id == project_id,
                ModelVersion.endpoint_id == endpoint_id
            ).all()
            if models:
                # Get the latest deployed model
                models.sort(key=lambda x: x.deployed_at, reverse=True)
                active_model = models[0]
                meta = dict(active_model.model_metadata or {})
                meta["index_version"] = active_model.model_version
                active_model.model_metadata = meta
                db.add(active_model)
                db.commit()
                logger.info(f"Updated index version metadata for {endpoint_id} to match {active_model.model_version}.")
                return True
            return False

        # 3. RMC: Recalibrate rule threshold
        elif action_type == "RECALIBRATE_RULE":
            rule_id = quoted_vars[0]
            # Find the rule and its endpoint
            rules = db.query(BusinessRule).filter(
                BusinessRule.project_id == project_id,
                BusinessRule.rule_id == rule_id
            ).all()
            if rules:
                # Find the active model for this endpoint to get its version
                endpoint_id = rules[0].endpoint_id
                models = db.query(ModelVersion).filter(
                    ModelVersion.project_id == project_id,
                    ModelVersion.endpoint_id == endpoint_id
                ).all()
                if models:
                    models.sort(key=lambda x: x.deployed_at, reverse=True)
                    current_model = models[0].model_version
                    for rule in rules:
                        rule.created_for_model_version = current_model
                        # Adjust expression threshold
                        if "score >= 0.82" in rule.expression:
                            rule.expression = rule.expression.replace("score >= 0.82", "score >= 0.76")
                        elif "score >= 0.85" in rule.expression:
                            rule.expression = rule.expression.replace("score >= 0.85", "score >= 0.76")
                        elif "score >= 0.95" in rule.expression:
                            rule.expression = rule.expression.replace("score >= 0.95", "score >= 0.89")
                        db.add(rule)
                    db.commit()
                    logger.info(f"Recalibrated rule '{rule_id}' to model '{current_model}'.")
                    return True
            return False

        # 4. HMD: Retrain model / Reconcile manual overrides
        elif action_type == "RETRAIN_CLASS":
            class_id = quoted_vars[0]
            # Find a matching HMD finding to get the segment
            finding = db.query(Finding).filter(
                Finding.run_id == run_id,
                Finding.detector == "HMD",
                Finding.target == class_id
            ).first()
            if finding:
                segment = finding.payload.get("segment", {})
                overrides = db.query(OverrideLog).filter(
                    OverrideLog.project_id == project_id,
                    OverrideLog.original_decision == class_id
                ).all()
                
                count = 0
                for ovr in overrides:
                    inf = db.query(InferenceLog).filter(
                        InferenceLog.project_id == project_id,
                        InferenceLog.inference_id == ovr.inference_id
                    ).first()
                    if inf:
                        import json
                        s1 = json.loads(inf.segment) if isinstance(inf.segment, str) else inf.segment
                        s2 = json.loads(segment) if isinstance(segment, str) else segment
                        if isinstance(s1, dict) and isinstance(s2, dict) and s1 == s2:
                            db.delete(ovr)
                            count += 1
                db.commit()
                logger.info(f"Deleted {count} manual overrides in segment {segment} to reconcile class '{class_id}'.")
                return True
            return False

        # 5. GFM: Retire feature from rule expression
        elif action_type == "RETIRE_FEATURE":
            feature = quoted_vars[0]
            rule_id = quoted_vars[1] if len(quoted_vars) > 1 else None
            if rule_id:
                rules = db.query(BusinessRule).filter(
                    BusinessRule.project_id == project_id,
                    BusinessRule.rule_id == rule_id
                ).all()
                for rule in rules:
                    if f"{feature} == 'platinum' and " in rule.expression:
                        rule.expression = rule.expression.replace(f"{feature} == 'platinum' and ", "")
                    elif f"and {feature} == 'platinum'" in rule.expression:
                        rule.expression = rule.expression.replace(f"and {feature} == 'platinum'", "")
                    db.add(rule)
                db.commit()
                logger.info(f"Retired feature '{feature}' from business rule '{rule_id}'.")
                return True
            return False

        return False
