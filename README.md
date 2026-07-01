# 🗺️ Semantic Debt Mapper (SDM)

<p align="center">
  <img src="./docs/animated_banner.svg" alt="Semantic Debt Mapper Banner" width="100%" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-FastAPI%20%2B%20React-indigo" alt="FastAPI React Stack" />
  <img src="https://img.shields.io/badge/Reliability-Production%20Grade-emerald" alt="Production Grade" />
  <img src="https://img.shields.io/badge/Engine-Semantic%20Drift-sky" alt="Semantic Drift Engine" />
  <img src="https://img.shields.io/badge/OS-mac%20%7C%20linux-neutral" alt="OS Support" />
</p>

---

> [!NOTE]  
> **Semantic debt** represents the hidden misalignment between the *active meaning* of schema elements (revised guidelines, policy shifts, updated label definitions) and the *legacy calibrations* under which downstream business logic, machine learning models, or human override thresholds were originally configured.

**Semantic Debt Mapper (SDM)** is a production-ready reliability and governance platform that ingests your pipelines, models, and override logs to map, flag, and remediate these meaning drifts.

---

## 🏗️ System Architecture & Data Flow

SDM links data definitions, classification models, override rules, and human-in-the-loop decisions into a unified dependency model:

```mermaid
graph TD
    %% Styling
    classDef source fill:#1e1b4b,stroke:#4f46e5,stroke-width:1.8px,color:#e0e7ff;
    classDef ingest fill:#18181b,stroke:#3f3f46,stroke-width:1.8px,color:#f4f4f5;
    classDef engine fill:#0c4a6e,stroke:#0284c7,stroke-width:1.8px,color:#e0f2fe;
    classDef detector fill:#1c1917,stroke:#d97706,stroke-width:1.8px,color:#fffbeb;
    classDef output fill:#064e3b,stroke:#059669,stroke-width:1.8px,color:#ecfdf5;

    %% Nodes
    A1["Label Definitions & Schemas"]:::source
    A2["Model Inferences & Predictions"]:::source
    A3["Business Rules & Thresholds"]:::source
    A4["Reviewer Overrides & Logs"]:::source

    B["Ingestion Engine (FastAPI)"]:::ingest
    
    C1["Semantic Lineage Builder"]:::engine
    C2["Scoring & Trend Engine"]:::engine

    subgraph Detectors ["Semantic Debt Detectors"]
        D1["Class Meaning Drift (CMD)"]:::detector
        D2["Embedding Space Fracture (ESF)"]:::detector
        D3["Rule-Model Conflict (RMC)"]:::detector
        D4["Human-Model Divergence (HMD)"]:::detector
        D5["Ghost Feature Misalignment (GFM)"]:::detector
    end

    E1["Interactive Lineage Graph"]:::output
    E2["Action Center & Remediation"]:::output
    E3["PDF Audit Reports"]:::output

    %% Connections
    A1 & A2 & A3 & A4 --> B
    B --> C1 & C2
    C1 & C2 --> Detectors
    D1 & D2 & D3 & D4 & D5 --> E1 & E2 & E3
```

### 💻 Technical Stack
* **Backend:** Python FastAPI, SQLAlchemy ORM, SQLite / PostgreSQL (with `pgvector` support).
* **Detectors:** NumPy-based vector similarity calculation, statistical drift analysis, and boundary override detection.
* **Frontend:** React 19, TypeScript, Vite, Vanilla CSS custom styling, React Flow (interactive lineage graphs), Recharts (trends and data analysis).
* **Testing:** Pytest (ingestion, API endpoints, and detector heuristics).

---

## 🔍 Core Detectors

SDM continuously audits ML pipelines using 5 specialized, deterministic detectors:

| Detector | Target Risk | Mechanism | Trigger Threshold |
| :--- | :--- | :--- | :--- |
| **1. Class Meaning Drift (CMD)** | Shifted schema definitions with outdated legacy data references. | Calculates Cosine Similarity between vector embeddings of consecutive definition versions and measures reviewer override delta. | Similarity $< 0.92$ & override increase $> 10\%$ |
| **2. Embedding Space Fracture (ESF)** | Legacy indices read by updated model query vectors. | Compares deployed model geometry with index version metadata in the vector DB. | Embedding dimension mismatch / tag discrepancy |
| **3. Rule-Model Conflict (RMC)** | Stale rules/overrides calibrated on legacy models acting on new score distributions. | Scans active rules pointing to old model tags and measures override rate at decision boundaries. | Override rate in threshold band $> 20\%$ |
| **4. Human-Model Divergence (HMD)** | Systemic prediction failures in specific cohorts. | Cohort grouping comparison against global override rates; extracts failure patterns via NLP. | Override rate $> 20\%$ & delta from baseline $> 15\%$ |
| **5. Ghost Feature Misalignment (GFM)** | Rules referencing stale or deleted schema attributes. | Scans AST/regex patterns of active rule expressions against historical vs. active model features. | Active rule uses inactive/renamed feature |

---

## 🛠️ Configuration & Security

The API endpoints require an API Key passed via the `X-API-Key` HTTP header.

### 📁 Environment Setup
Create a `.env` file in the root directory (or use `.env.example` templates):

#### **Backend (`backend/.env`)**
```env
DATABASE_URL=sqlite:///./sdm.db
API_KEY=your-secure-backend-api-key
```

#### **Frontend (`frontend/.env`)**
```env
VITE_API_URL=http://localhost:8005/api/v1
VITE_API_KEY=your-secure-backend-api-key
```

---

## 🚀 Getting Started

### **Option 1: Running with Docker Compose (Recommended)**
Spin up PostgreSQL, Redis, FastAPI backend, Vite dev server, and worker containers:
```bash
docker compose up --build
```
* **Dashboard Interface:** `http://localhost:5173`
* **API Documentation (Swagger):** `http://localhost:8005/docs`

### **Option 2: Running Locally (Development Mode)**

#### **1. Start Backend API**
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

#### **2. Start Frontend App**
```bash
cd frontend
npm install
npm run dev
```

---

## 📊 Extended API & UI Features

We have extended the platform with several production-ready capabilities:

1. **API Pagination & Filtering**:
   - `/projects/{project_id}/findings` supports optional query filters:
     - `limit` (default: 100) and `offset` (default: 0) for result pagination.
     - `detector` to filter by engine codes (`CMD`, `ESF`, `RMC`, `HMD`, `GFM`).
   - `/projects/{project_id}/actions` supports query filters:
     - `limit` (default: 100) and `offset` (default: 0) for result pagination.

2. **JSON Export Endpoint**:
   - `/projects/{project_id}/findings/export` provides a structured snapshot of a project's metadata, active Semantic Debt Score (SDS), and computed findings for compliance registries and audits.

3. **Concurrency Locks**:
   - Attempts to trigger audits while a previous run is `pending` or `running` are locked and rejected with `409 Conflict` to prevent state collision or SQLite locking.

4. **UI Improvements**:
   - Embedded interactive **Pagination Controls** (5 items per page) in the **Findings Explorer** registry list.
   - Built a custom **"Export JSON"** download button in the overview dashboard, enabling rapid offline compliance audits.
   - **Modern Animations**: Integrated a breathing radial glow behind the main SDS circular gauge and added elegant interactive hover translation effects on all dashboard cards.

---

## 🧪 Verification & Testing

### **Running Python Tests**
We maintain comprehensive unit and integration test coverage:
```bash
cd backend
export API_KEY=dev-key-123
export DATABASE_URL=sqlite:///./sdm.db
PYTHONPATH=. pytest tests/
```

### **Running Frontend Quality Audits**
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
3. Click **"Load Support Ticket Demo"**. This will ingest a simulated dataset with injected semantic drifts (`CMD`, `ESF`, `RMC`, `HMD`, `GFM`).
4. Navigate to the **Overview**, **Findings**, and **Lineage Graph** pages to inspect computed metrics and trace semantic failures.

---

## 🧹 Code Cleanups & Linter Quality Checks

A series of developer quality checks and cleanups were successfully completed to resolve linting warnings/errors and improve code health:
- **Frontend Quality**: Fixed React state cascading render warnings inside `FindingsExplorer` and removed unused ESLint directives.
- **Backend Quality**: Removed unused imports across background workers and services, and refactored redundant f-strings to static format strings.
- **PEP8 Alignment**: Formatted services according to PEP8 guidelines and configured standard 88-character line limits in `.flake8` configuration.
