# Demo Dataset: Support Ticket Classifier

This dataset demonstrates intentional semantic debt events for the Semantic Debt Mapper MVP demo.

## Files

| File | Description |
|---|---|
| `model_versions.json` | Model deployment history (v3.1.0 → v4.2.0, embedding model upgrade) |
| `label_schemas.json` | Label schema v2 → v3 with changed "urgent" definition |
| `rules.json` | Business rules still calibrated for model v3.1.0 |
| `prompts.json` | Prompt taxonomy v1 → v2 mismatch |
| `inference_logs.csv` | 30 inference rows with EU/mobile segment focus |
| `override_logs.csv` | 18 override events showing human-model divergence |

## Injected Semantic Debt Events

1. **Label drift (CMD):** "urgent" redefined from SLA < 2h to SLA < 4h in schema v3
2. **Rule conflict (RMC):** `threshold_urgent` rule created for model v3.1.0, still active with v4.2.0
3. **Human divergence (HMD):** EU mobile reviewers override "medium" → "urgent" at 31% rate
4. **Ghost feature (GFM):** `customer_tier` definition changed in fs_v7 but rules still use old semantics
5. **Embedding fracture (ESF):** RAG index at emb_v3 while model deployed at emb_v5

## Expected Audit Output

- **Semantic Debt Score:** ~73 (High risk)
- **Top findings:**
  - CMD: urgent class definition similarity 0.63, override rate delta +19%
  - RMC: threshold_urgent flip rate 27% near threshold
  - HMD: EU/mobile override rate 31% vs baseline 11%
- **Top action:** Recalibrate threshold to 0.76 + retrain urgent class

## Usage

Load via ingestion API endpoints documented in `docs/api_examples.http`.

```bash
# After backend is running:
curl -X POST http://localhost:8000/api/v1/projects/{id}/ingest/model-versions \
  -H "Content-Type: application/json" \
  -d @datasets/demo_support_tickets/model_versions.json
```
