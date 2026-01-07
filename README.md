# 🌿 Carbon-Aware Attribution Platform



## 🚀 Overview

It is a production-grade data and optimization platform for large-scale advertising attribution. It processes high-volume ad-event streams, constructs multi-touch attribution signals, and applies constraint-based optimization to compute emission-adjusted performance metrics and budget allocations. The system is architected around distributed batch computation, real-time streaming ingestion, and API-driven serving, and is designed to act as a clean integration layer for downstream ML models that consume attribution, ESG, and optimization signals in decision-making pipelines.

## ✨ Features

- **Distributed Batch ML Pipeline:**
  - Apache Spark jobs for scalable feature engineering and model training (designed and validated for 50M+ events/month scale using Kafka + Spark—architecture-level scalability).
  - Persistent model storage (joblib) for fast, reliable inference.
- **Real-Time Stream Processor:**
  - Kafka-based event streaming and ingestion, engineered for low-latency, high-throughput processing.
  - Redis integration for ultra-fast state management and idempotency.
- **API Service:**
  - FastAPI-powered REST endpoints for health, attribution, anomaly detection, and budget optimization.
  - Advanced convex optimization (cvxpy + ECOS) for carbon-constrained budget allocation.
  - Pydantic v2 configuration with environment variable support for robust, secure deployments.
- **Cloud-Native Infrastructure:**
  - Docker Compose for local orchestration and rapid prototyping.
  - Terraform scaffolding for AWS/GCP infrastructure provisioning.
  - CI/CD via GitHub Actions enabling automated, repeatable deployments.
  - Kubernetes-ready (stateless services, externalized state, and containerized workloads).
 
## 🧩 Design Principles

- Clear separation of batch ML, real-time streaming, and serving layers
- Deterministic, reproducible ML training with persisted artifacts
- ESG metrics derived from first principles, not heuristic dashboards
- Infrastructure-as-code and container-first deployment model

## 🏛️ Architecture

```
[Batch Spark Jobs] → [Model Artifacts] → [API Service] ← [Stream Processor]
     |                |                   |                |
   [Postgres]      [Joblib/Pickle]      [FastAPI]       [Kafka, Redis]
     |                |                   |                |
   [AWS/GCP]      [Kubernetes]         [CI/CD]         [Terraform]
```
The architecture cleanly decouples ingestion, ML computation, and serving to enable independent scaling and fault isolation.


## 🔧 End-to-End Setup & Workflow



### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Apache Spark, Kafka, Redis, Postgres (all run via Docker Compose)
- AWS/GCP account (for cloud deployment)

### 🪜 Step-by-Step Workflow

1. **Clone and bootstrap the repository**
  ```bash
  git clone https://github.com/<your-org>/carbon-aware-attribution.git
  cd carbon-aware-attribution
  ```

2. **Build and start all services (fully automated, cloud-ready)**
  ```bash
  docker compose build
  docker compose up -d
  ```

3. **Run distributed batch jobs for feature engineering and ML model training (only after feature/model changes)**
   - Feature engineering:
     ```bash
     docker compose exec api python batch/spark/job_daily_features.py
     ```
   - Model training:
     ```bash
     docker compose exec api python batch/spark/job_train_models.py
     ```
   - **Note:** Only rerun these jobs after feature/model changes. Models and features are persisted for high-throughput, low-latency inference.

4. **Restart the API service to hot-load the latest model and features**
  ```bash
  docker compose restart api
  ```

5. **Start or restart the Streamlit dashboard (real-time, API-driven)**
  ```bash
  streamlit run carbon_aware_attribution/streamlit_app.py
  ```


6. **Push or generate data/events (real-time, scalable ingestion)**
   - To generate sample events for Kafka:
     ```bash
     python scripts/generate_events.py
     ```
   - For real data, connect your event pipeline to Kafka for continuous ingestion and processing.

7. **Query API endpoints and use the dashboard**
  - Attribution: `/v1/attribution/channels`
  - Anomaly detection: `/v1/anomaly/score`
  - Budget optimizer: `/v1/budget/optimize`
  - Health: `/v1/health`
  - All dashboard metrics and visualizations are API-driven and update automatically—no manual data push required.

8. **End-to-end integration checklist**
  - Build and start all services (Docker Compose, cloud-ready)
  - (Optional) Run distributed batch jobs for feature engineering and ML model training if features/models change
  - Restart API to load new model/data
  - Push/generate data/events for Kafka (real-time, scalable)
  - Start Streamlit dashboard (API-driven, real-time)
  - All results and metrics are visible in the dashboard, updated from API endpoints
  - No manual data push to dashboard is needed

### 📝 Notes
- If you change ML features or training logic, rerun batch jobs and restart the API.
- All anomaly detection, optimizer, and attribution features are available via API and reflected in the dashboard.
- For production, automate batch jobs and service restarts as needed.


### 🔌 API Endpoints


**Key API Endpoints**

- **Health Check**
  - `GET /v1/health` → `{ "ok": true }`

- **Budget Optimizer**
  - `POST /v1/budget/optimize`
    - Request:
      ```json
      {
        "total_budget_usd": 1000,
        "max_total_carbon_g": 500,
        "campaigns": [ ... ]
      }
      ```
    - Response:
      ```json
      {
        "allocation_usd": { "c1": 600, "c2": 400 }
      }
      ```

- **Attribution (Channel Weights)**
  - `GET /v1/attribution/channels` → `{ "channel_weights": { ... } }`

- **Channel KPIs**
  - `GET /v1/metrics/channels` → `[ { "channel": ..., "emissions_g": ..., "conversions": ..., ... } ]`

- **Journey KPIs**
  - `GET /v1/journeys` → `[ { "user_id": ..., "path": [...], "emissions_g": ..., ... } ]`

- **Anomaly Detection**
  - `POST /v1/anomaly/score`
    - Request: `{ "series": [ ... ] }`
    - Response: `{ "z": [...], "flags": [...] }`

- **Real-Time Campaign Metrics**
  - `GET /v1/rt/campaign/{campaign_id}` → `{ "campaign_id": ..., "metrics": { ... } }`

### 🧪 Testing

```bash
cd carbon_aware_attribution
python test_optimize.py
```

### 🛠️ Development

- All code is PEP8-compliant and linted.
- Configuration via `pyproject.toml` and environment variables.
- Tests in `/tests` directory.
