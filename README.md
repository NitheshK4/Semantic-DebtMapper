# Semantic Debt Mapper (SDM)

Find where old AI meaning assumptions still control your production decisions.

Semantic Debt Mapper (SDM) is a production-grade AI reliability and governance platform that detects **semantic debt** across machine learning and LLM decision pipelines. 

Semantic debt refers to accumulated inconsistencies between what your pipeline elements *mean* today (revised policies, new prompts, new schemas) versus what they *meant* when legacy models or business rules were calibrated.

---

## 🏗️ System Architecture

SDM is structured as a full-stack system designed for high throughput log analysis and interactive lineage tracing:

```
[ Label Definitions ] ──> [ Models ] ──> [ Business Rules ] ──> [ Overrides ]
                                   \             /
                                    v           v
                          [ Semantic Lineage Graph (SLG) ]
                                         │
                                         v
                            [ Semantic Debt Detectors ]
                                         │
                                         v
                         [ Priority Remediation Actions ]
```

### Technical Stack
* **Backend:** Python FastAPI, SQLAlchemy ORM, SQLite (local development) / PostgreSQL (production with pgvector).
* **Detectors:** NumPy-based vector similarity calculation, statistical drift analysis, and boundary override detection.
* **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, React Flow (for interactive lineage graphing), Recharts (for trend analysis).
* **Testing:** Pytest (100% test passing coverage for ingestion, API endpoints, and detector heuristics).

---

## 🔍 Semantic Debt Detectors

SDM runs 5 specialized, deterministic detectors to audit pipeline components for meaning drift:

### 1. Class Meaning Drift (CMD)
* **Objective:** Detects when a classification label's semantic definition shifts between schema updates while historical data remains unaligned.
* **Mechanism:** 
  1. Computes the cosine similarity between sentence embeddings of consecutive label definitions.
  2. Measures the delta in reviewer override rates before and after the schema update.
  3. Triggers if definition similarity is $< 0.92$ and the segment override rate increases by $> 10\%$.

### 2. Embedding Space Fracture (ESF)
* **Objective:** Detects when retrieval/search indices run on legacy embedding representations while the querying model uses a newer geometry.
* **Mechanism:**
  1. Compares the active deployed model version with the index version metadata of the vector database.
  2. Flags a critical mismatch when the active model's embedding outputs do not match the indexing version geometry.

### 3. Rule-Model Conflict (RMC)
* **Objective:** Detects post-processing business rules or threshold overrides calibrated for legacy models that are still applied to new model predictions.
* **Mechanism:**
  1. Identifies rules referencing older model versions.
  2. Analyzes the model output score distribution near the decision boundary (threshold $\pm 0.05$).
  3. Measures the human override (flip) rate in that band. If the flip rate is $> 20\%$, RMC triggers.

### 4. Human-Model Divergence (HMD)
* **Objective:** Identifies segments of input space where reviewers consistently reject model predictions.
* **Mechanism:**
  1. Groups inferences and overrides by features/cohorts (e.g. `region=EU, channel=mobile`).
  2. Compares the segment override rate with the global baseline override rate for that class.
  3. Triggers if the segment override rate is $> 20\%$ and exceeds the baseline by $> 15\%$, extracting override themes using word-frequency analysis.

### 5. Ghost Feature Misalignment (GFM)
* **Objective:** Detects business rules referencing features that are stale, renamed, or modified in the current model schema.
* **Mechanism:**
  1. Inspects feature schemas across consecutive model versions.
  2. Scans rule expressions using regular expressions to find legacy feature dependencies.
  3. Flags rules utilizing features that are no longer actively produced or whose definitions have drifted.

---

## 🛠️ Configuration & Security

The API endpoints require an API Key passed via the `X-API-Key` HTTP header. 

### Environment Setup
Create a `.env` file in the root or set environment variables in your run shell:

#### Backend Settings (`backend/app/core/config.py`)
```env
DATABASE_URL=sqlite:///./sdm.db
API_KEY=your-secure-backend-api-key
```

#### Frontend Settings (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8005/api/v1
VITE_API_KEY=your-secure-backend-api-key
```

---

## 🚀 Getting Started

### Option 1: Running with Docker Compose (Recommended)
This starts FastAPI, Vite, PostgreSQL, and a background Redis queue:
```bash
docker compose up --build
```
* **Dashboard Portal:** `http://localhost:5173`
* **API Documentation (Swagger):** `http://localhost:8005/docs`

### Option 2: Running Locally (Development Mode)

#### 1. Start Backend API
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations/setup
export API_KEY=dev-key-123
export DATABASE_URL=sqlite:///./sdm.db
python3 -m uvicorn app.main:app --port 8005 --reload
```

#### 2. Start Frontend App
```bash
cd frontend
npm install

# Build or run development server
npm run dev
```

---

## 🧪 Verification & Testing

### Running Python Tests
We maintain 100% execution pass rates on the backend test suite:
```bash
cd backend
PYTHONPATH=. pytest tests/
```

### Running Frontend Quality Audits
Verify TypeScript compilation and ESLint compliance:
```bash
cd frontend
npm run lint
npm run build
```

---

## 📈 Interactive Walkthrough (Demo Dataset)
To immediately visualize semantic debt:
1. Start both servers.
2. Go to **Ingestion Center** in the sidebar.
3. Click **"Load Support Ticket Demo"**. This will ingest a simulated dataset with injected semantic drifts (CMD, ESF, RMC, HMD, GFM).
4. Navigate to the **Overview**, **Findings**, and **Lineage Graph** pages to inspect computed metrics.
