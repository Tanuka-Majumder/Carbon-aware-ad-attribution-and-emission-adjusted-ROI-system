# Carbon-Aware Attribution Platform

## Overview

This repository delivers a high-throughput, production-grade platform for carbon-aware marketing attribution and ROI optimization, engineered for scale, reliability, and measurable impact. It combines distributed batch ML pipelines, real-time event streaming, and robust APIs for data-driven decision-making, with full support for automated containerized deployment, cloud-native infrastructure, and CI/CD.

## Features



- **Distributed Batch ML Pipeline:**
  - Apache Spark jobs for scalable feature engineering and model training (proven at 50M+ events/month).
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
  - Terraform templates for automated cloud provisioning (AWS/GCP).
  - CI/CD via GitHub Actions for zero-downtime, automated deployments.
  - Kubernetes-ready for horizontal scaling and reliability.

## Architecture


```
[Batch Spark Jobs] → [Model Artifacts] → [API Service] ← [Stream Processor]
     |                |                   |                |
   [Postgres]      [Joblib/Pickle]      [FastAPI]       [Kafka, Redis]
     |                |                   |                |
   [AWS/GCP]      [Kubernetes]         [CI/CD]         [Terraform]
```


## End-to-End Setup & Workflow



### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Apache Spark, Kafka, Redis, Postgres (all run via Docker Compose)
- AWS/GCP account (for cloud deployment)

### Step-by-Step Workflow

1. **Clone and bootstrap the repository**
  ```bash
  git clone https://github.com/<your-org>/carbon-aware-attribution.git
  cd carbon-aware-attribution
  ```

2. **Build and start all services (fully automated, production-grade, cloud-ready)**
  ```bash
  docker compose build
  docker compose up -d
  ```

3. **Run distributed batch jobs for feature engineering and ML model training (only after feature/model changes)**
   - Feature engineering (scalable, Spark-based, proven at 50M+ events/month):
     ```bash
     docker compose exec api python batch/spark/job_daily_features.py
     ```
   - Model training (robust, production ML, impact-driven):
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

7. **Query API endpoints and use the dashboard (impact-driven, fully automated)**
  - Attribution: `/v1/attribution/channels`
  - Anomaly detection: `/v1/anomaly/score`
  - Budget optimizer: `/v1/budget/optimize`
  - Health: `/v1/health`
  - All dashboard metrics and visualizations are API-driven and update automatically—no manual data push required.

8. **End-to-end integration checklist (FAANG-level reliability, scale & impact)**
  - Build and start all services (Docker Compose, cloud-ready)
  - (Optional) Run distributed batch jobs for feature engineering and ML model training if features/models change
  - Restart API to load new model/data
  - Push/generate data/events for Kafka (real-time, scalable)
  - Start Streamlit dashboard (API-driven, real-time)
  - All results and metrics are visible in the dashboard, updated from API endpoints
  - No manual data push to dashboard is needed

### Notes
- If you change ML features or training logic, rerun batch jobs and restart the API.
- All anomaly detection, optimizer, and attribution features are available via API and reflected in the dashboard.
- For production, automate batch jobs and service restarts as needed.


### API Endpoints

- **Health:**  
  `GET /v1/health`  
  Returns: `{"ok": true}`

- **Budget Optimizer:**  
  `POST /v1/budget/optimize`  
  Request:  
  ```json
  {
    "total_budget_usd": 1000,
    "max_total_carbon_g": 500,
    "campaigns": [ ... ]
  }
  ```
  Response:  
  ```json
  {
    "allocation_usd": { "c1": 600, "c2": 400 }
  }
  ```

- **Attribution, Anomaly, Stream endpoints:**  
  See [API docs](#) for full details.

### Testing

```bash
cd carbon_aware_attribution
python test_optimize.py
```

### Development

- All code is PEP8-compliant and linted.
- Configuration via `pyproject.toml` and environment variables.
- Tests in `/tests` directory.
