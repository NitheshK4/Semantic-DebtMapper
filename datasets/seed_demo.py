import json
import csv
import requests
import os
import sys
import time

BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("API_KEY", "your-api-key-here")

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": application/json
}

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def load_csv(filepath):
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def seed():
    print("=== Starting SDM Seeding Script ===")
    
    # 1. Create project
    proj_payload = {
        "name": "Support Ticket Classifier",
        "domain": "support_tickets"
    }
    print("Creating project...")
    res = requests.post(f"{BASE_URL}/projects", json=proj_payload, headers=headers)
    if res.status_code not in (200, 201):
        print(f"Failed to create project: {res.text}")
        sys.exit(1)
    
    project = res.json()
    project_id = project["id"]
    print(f"Project created with ID: {project_id}")

    # 2. Ingest concepts
    concepts = [
        {"key": "low", "def": "Ticket can be addressed within 48 hours per SLA."},
        {"key": "medium", "def": "Ticket should be addressed within 24 hours per SLA."},
        {"key": "urgent", "def": "Ticket requires response within 4 hours per SLA policy v3. Includes VIP escalations and payment failures."},
        {"key": "critical", "def": "System outage or security incident requiring response within 30 minutes."}
    ]
    for c in concepts:
        concept_payload = {
            "concept_key": c["key"],
            "version": "v1",
            "definition": c["def"],
            "effective_from": "2026-01-01T00:00:00Z"
        }
        print(f"Creating concept: {c['key']}...")
        requests.post(f"{BASE_URL}/projects/{project_id}/concepts", json=concept_payload, headers=headers)

    # 3. Ingest model versions
    model_versions = load_json("datasets/demo_support_tickets/model_versions.json")
    # Clean payload
    mv_payload = []
    for mv in model_versions:
        mv_payload.append({
            "endpoint_id": mv["endpoint_id"],
            "model_name": mv["model_name"],
            "model_version": mv["model_version"],
            "feature_schema_version": mv["metadata"].get("feature_schema_version"),
            "deployed_at": mv["deployed_at"],
            "metadata": mv["metadata"]
        })
    print("Ingesting model versions...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/model-versions", json=mv_payload, headers=headers)
    print(f"Ingested models: {res.json()}")

    # 4. Ingest label schemas
    label_schemas = load_json("datasets/demo_support_tickets/label_schemas.json")
    print("Ingesting label schemas...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/label-schemas", json=label_schemas, headers=headers)
    print(f"Ingested label schemas: {res.json()}")

    # 5. Ingest business rules
    rules = load_json("datasets/demo_support_tickets/rules.json")
    rules_payload = []
    for r in rules:
        rules_payload.append({
            "rule_id": r["rule_id"],
            "rule_version": r["rule_version"],
            "endpoint_id": r["endpoint_id"],
            "expression": r["expression"],
            "created_for_model_version": r["created_for_model_version"],
            "active_from": r["active_from"],
            "active_to": r.get("active_to")
        })
    print("Ingesting rules...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/rules", json=rules_payload, headers=headers)
    print(f"Ingested rules: {res.json()}")

    # 6. Ingest prompts
    prompts = load_json("datasets/demo_support_tickets/prompts.json")
    print("Ingesting prompts...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/prompts", json=prompts, headers=headers)
    print(f"Ingested prompts: {res.json()}")

    # 7. Ingest inferences
    inferences_csv = load_csv("datasets/demo_support_tickets/inference_logs.csv")
    inferences_payload = []
    for row in inferences_csv:
        inferences_payload.append({
            "inference_id": row["inference_id"],
            "timestamp": row["timestamp"],
            "endpoint_id": row["endpoint_id"],
            "model_version": row["model_version"],
            "input_features": {
                "customer_tier": row["customer_tier"],
                "ticket_age_hours": float(row["ticket_age_hours"]),
                "channel": row["channel"]
            },
            "model_output": {
                "score": float(row["score"]),
                "predicted_class": row["predicted_class"]
            },
            "rule_applied": ["threshold_urgent"],
            "final_decision": row["final_decision"],
            "segment": {
                "region": row["region"],
                "channel": row["channel"]
            }
        })
    print(f"Ingesting {len(inferences_payload)} inferences...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/inferences:batch", json=inferences_payload, headers=headers)
    print(f"Ingested inferences: {res.json()}")

    # 8. Ingest overrides
    overrides_csv = load_csv("datasets/demo_support_tickets/override_logs.csv")
    overrides_payload = []
    for row in overrides_csv:
        overrides_payload.append({
            "override_id": row["override_id"],
            "inference_id": row["inference_id"],
            "reviewer_id": row["reviewer_id"],
            "original_decision": row["original_decision"],
            "override_decision": row["override_decision"],
            "override_class": row["override_class"],
            "reason_code": row["reason_code"],
            "comment": row["comment"],
            "timestamp": row["timestamp"]
        })
    print(f"Ingesting {len(overrides_payload)} overrides...")
    res = requests.post(f"{BASE_URL}/projects/{project_id}/ingest/overrides:batch", json=overrides_payload, headers=headers)
    print(f"Ingested overrides: {res.json()}")

    # 9. Trigger semantic audit synchronously
    print("Triggering semantic audit run...")
    audit_trigger = {
        "as_of": "2026-06-15T00:00:00Z",
        "detectors": ["CMD", "ESF", "RMC", "HMD", "GFM"]
    }
    # Send request with sync=True
    res = requests.post(f"{BASE_URL}/projects/{project_id}/audits/run?sync=true", json=audit_trigger, headers=headers)
    if res.status_code not in (200, 202):
        print(f"Failed to run audit: {res.text}")
        sys.exit(1)
    
    audit_res = res.json()
    print(f"Audit response: {audit_res}")

    # 10. Fetch latest audit run results
    print("Fetching audit results...")
    res = requests.get(f"{BASE_URL}/projects/{project_id}/audits/latest", headers=headers)
    latest_run = res.json()
    
    print("\n========================================")
    print(f"Semantic Debt Score (SDS): {latest_run.get('sds_score')}/100")
    print(f"Audit Status: {latest_run.get('status')}")
    print(f"Total Findings Detected: {len(latest_run.get('findings', []))}")
    print(f"Total Recommendations Generated: {len(latest_run.get('action_cards', []))}")
    print("========================================\n")

    print("--- Findings ---")
    for f in latest_run.get("findings", []):
        print(f"- [{f.get('detector')}] Severity: {f.get('severity').upper()} | Target: {f.get('target')} | Rec: {f.get('payload', {}).get('recommendation')}")
        
    print("\n--- Action Cards ---")
    for c in latest_run.get("action_cards", []):
        print(f"- [{c.get('action_type')}] Title: {c.get('title')}")
        print("  Steps:")
        for s in c.get("steps", []):
            print(f"    * {s}")
            
    print("\n=== Seeding & Validation Completed Successfully ===")

if __name__ == "__main__":
    # Wait for API to be ready if running in docker
    time.sleep(2)
    seed()
