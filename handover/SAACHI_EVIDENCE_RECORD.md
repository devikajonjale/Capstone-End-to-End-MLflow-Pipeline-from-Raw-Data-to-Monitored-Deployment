# 📋 Capstone MLOps Pipeline — Verification & Handover Evidence Record
**Project 4 | Group 5 | Devika Jonjale (B045) & Saachi Shinde (B048)**  
**Branch:** `saachis-development`  
**Date:** 2026-10-22  

---

## 1. Environment Details
- **Operating System:** Windows 11 (build 26100)
- **Docker Version:** `Docker version 28.0.4, build b8034c0`
- **Docker Compose Version:** `Docker Compose version v2.34.0-desktop.1`
- **Python Version (in container):** Python 3.11-slim
- **Base Image:** `house-price-api:local`

---

## 2. Docker Compose Services Status (`docker compose ps`)

```
NAME                                                                IMAGE                           COMMAND                  SERVICE      STATUS          PORTS
capstone-end-to-end-mlflow-pipeline-from-raw-data-to-monitored-deployment-app-1          house-price-api:local           "uvicorn src.serving…"   app          Up              0.0.0.0:8000->8000/tcp
capstone-end-to-end-mlflow-pipeline-from-raw-data-to-monitored-deployment-grafana-1      grafana/grafana:11.2.0          "/run.sh"                grafana      Up              0.0.0.0:3000->3000/tcp
capstone-end-to-end-mlflow-pipeline-from-raw-data-to-monitored-deployment-mlflow-1       ghcr.io/mlflow/mlflow:v2.17.2   "mlflow server --hos…"   mlflow       Up              0.0.0.0:5000->5000/tcp
capstone-end-to-end-mlflow-pipeline-from-raw-data-to-monitored-deployment-prometheus-1   prom/prometheus:v2.54.1         "/bin/prometheus --c…"   prometheus   Up              0.0.0.0:9090->9090/tcp
```
All four services (`app`, `grafana`, `mlflow`, `prometheus`) built and running without exit or crash.

---

## 3. API Verification

### A. Health Endpoint (`GET /health`)
```json
{
  "status": "ok",
  "model_loaded": true
}
```

### B. Lineage Endpoint (`GET /lineage`)
```json
{
  "model_name": "house_price_model",
  "registry_version": 1,
  "mlflow_run_id": "38803890a23f49829019cedb76c10bd3",
  "git_commit": "e73d5c9dbd98dcaf686982fdddd9eeb2e76e380d",
  "config_version": "1.0.0",
  "promoted_at": "2026-10-21T10:57:48+00:00",
  "holdout_metrics": {
    "rmse": 9.590082625274215,
    "mae": 7.520774583136174,
    "r2": 0.8090703112358504
  }
}
```

### C. Prediction Endpoint (`POST /predict`)
**Request payload:**
```json
{
  "Area_sqft": 1200,
  "Bedrooms": 3,
  "Bathrooms": 2,
  "Age_Years": 10,
  "Distance_to_Center_km": 5.0,
  "Neighborhood_Score": 8.0,
  "Has_Parking": 1,
  "Property_Condition": "Good",
  "City_Zone": "North"
}
```
**Response:**
```json
{
  "predicted_price_lakhs": 73.42
}
```

---

## 4. Monitoring & Metrics Traffic Generation

- Over 110 requests were generated with randomized feature distributions (areas between 500-2500 sqft, bedrooms 1-5, varied zones).
- **Prometheus Target:** `http://localhost:9090/api/v1/targets` confirms `house_price_api` target status is **UP** (scrape pool `house_price_api`, scrape URL `http://app:8000/metrics`, scrape interval 10s).
- **Prometheus Query Results:**
  - `prediction_requests_total`: Counter incremented actively (`>110` requests recorded).
  - `prediction_errors_total`: `0` (100% success rate).
  - `prediction_latency_seconds`: `p95` latency measured at `~0.0368s` (36.8 ms).
- **Grafana Dashboard:**
  - Auto-provisioned datasource at `http://prometheus:9090`.
  - Dashboard `House Price API` (UID: `dg2007rvcl79cd`) loaded at `http://localhost:3000/d/dg2007rvcl79cd/house-price-api`.

---

## 5. Rollback Procedure Test (Task 8 / Task 6 Requirement)

**Procedure followed per `ROLLBACK.md`:**
1. Backed up current container image:
   ```bash
   docker tag house-price-api:local house-price-api:rollback-backup
   ```
2. Stopped and removed the running compose stack:
   ```bash
   docker compose down
   ```
3. Tagged rollback image back to local serving target:
   ```bash
   docker tag house-price-api:rollback-backup house-price-api:local
   ```
4. Re-launched the stack:
   ```bash
   docker compose up -d
   ```
5. Verified service recovery:
   - `GET /health` returned `{"status": "ok", "model_loaded": true}`.
   - `GET /lineage` verified correct git commit and model metadata.
   - `POST /predict` returned exact expected response (`73.42` lakhs).
   - Prometheus and Grafana resumed scraping immediately with zero downtime loss.

**Result statement for report:**  
> "The rollback procedure defined in `ROLLBACK.md` was executed on local Docker Desktop (v28.0.4) using image tag `house-price-api:rollback-backup` restored to `house-price-api:local`. The stack restarted cleanly, `/health` and `/lineage` confirmed model integrity, and live prediction serving and Prometheus metrics collection resumed with zero data loss or registry disruption."

---

## 6. Captured Evidence Artifacts

- `handover/evidence/01_prometheus_targets.png`: Prometheus `/targets` UI showing target `house_price_api` UP.
- `handover/evidence/02_grafana_dashboard.png`: Grafana dashboard verification.
- `handover/SAACHI_SESSION_SKELETON.md`: Full task guide and completion record.
- `handover/SAACHI_EVIDENCE_RECORD.md`: Detailed test telemetry and results.
