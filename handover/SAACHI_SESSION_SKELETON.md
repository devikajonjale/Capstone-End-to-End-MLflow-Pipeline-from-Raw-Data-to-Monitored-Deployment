# 🏗️ Capstone MLOps Pipeline — Saachi's Session Guide
**Project 4 | Group 5 | Devika Jonjale (B045) + Saachi Shinde (B048)**
**Branch:** `saachis-development`
**Repo:** `Capstone-End-to-End-MLflow-Pipeline-from-Raw-Data-to-Monitored-Deployment`

**Docker version (verified):** 28.0.4  
**Docker Compose version (verified):** v2.34.0-desktop.1

---

## 📋 What This Project Is

A full end-to-end MLOps pipeline for **House Price Prediction** (price in lakhs of rupees).
- **Model:** Gradient-boosted ensemble on 9 features (area, bedrooms, bathrooms, age, distance-to-center, neighborhood score, parking, condition, zone)
- **Success metrics:** RMSE ≤ 18 lakhs, MAE ≤ 13 lakhs, R² ≥ 0.65 (current model: RMSE ~9.59, R² ~0.81 — well within bar)
- **Key concept:** Two quality gates protect production — a **data gate** and a **model gate**. If either fails, the old model stays live untouched.

---

## ✅ What Devika Has Already Built (DO NOT REDO)

| Component | Location | Status |
|-----------|----------|--------|
| Config system (`config.yaml` + loader) | `config/`, `src/config_loader.py` | ✅ Done |
| Data ingestion stage | `src/stages/ingest.py` | ✅ Done |
| Data validation gate | `src/stages/validate_data.py` | ✅ Done |
| Feature engineering | `src/features.py`, `src/stages/feature_engineering.py` | ✅ Done |
| Model training stage | `src/stages/train.py` | ✅ Done |
| Model evaluation gate | `src/stages/evaluate.py` | ✅ Done |
| Model registration + promotion | `src/stages/register.py` | ✅ Done |
| FastAPI serving app (with `/metrics`, `/health`, `/lineage`, `/predict`) | `src/serving/app.py` | ✅ Done |
| Prefect orchestration flows | `src/pipeline.py` | ✅ Done |
| Monitoring (drift + performance) | `src/stages/monitor.py`, `run_monitoring.py` | ✅ Done |
| Trained model in production | `models/production/model.pkl` + `lineage.json` | ✅ Present |
| Drift/perf monitoring report | `data/results/monitoring_report.md` | ✅ Generated |
| Unit tests (7 test files) | `tests/` | ✅ Done |
| CI workflow (tests + pipeline + docker build) | `.github/workflows/ci.yml` | ✅ Done |
| Release workflow (image + GitHub Release tarball) | `.github/workflows/release.yml` | ✅ Done |
| Safe-failure demo script | `scripts/demo_failures.py` | ✅ Done |
| Rollback procedure | `ROLLBACK.md` | ✅ Documented |
| Dockerfile | `Dockerfile` | ✅ Done |
| docker-compose.yml (4 services) | `docker-compose.yml` | ✅ Done |
| Grafana provisioning files | `monitoring/grafana/provisioning/` | ✅ Done |
| Grafana dashboard JSON | `monitoring/grafana/dashboards/house_price.json` | ✅ Done |
| Prometheus config | `monitoring/prometheus.yml` | ✅ Done |
| Project report (draft) | `handover/PROJECT_REPORT_FINAL.docx` | ✅ Draft exists |

> The model is **already trained and in `models/production/`**. You do NOT need to retrain anything. The container can serve predictions immediately.

---

## 🎯 Saachi's Remaining Tasks

### TASK 1 — Prerequisite: Docker Desktop
**✅ VERIFIED** — Docker 28.0.4, Compose v2.34.0-desktop.1

---

### TASK 2 — Bring Up the Full Docker Stack
From the repo root:
```powershell
docker compose up --build -d
```

This builds 4 services:
| Service | URL | Purpose |
|---------|-----|---------|
| `app` | http://localhost:8000 | FastAPI prediction API |
| `prometheus` | http://localhost:9090 | Metrics scraper |
| `grafana` | http://localhost:3000 | Dashboard (login: `admin` / `admin`) |
| `mlflow` | http://localhost:5000 | Experiment tracking + registry UI |

Verify:
```powershell
docker compose ps
```

📸 **Evidence:** Screenshot of `docker compose ps` showing all 4 services healthy.

---

### TASK 3 — Verify the Prediction Service Works
```powershell
curl http://localhost:8000/health
curl http://localhost:8000/lineage
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{\"Area_sqft\":1200,\"Bedrooms\":3,\"Bathrooms\":2,\"Age_Years\":10,\"Distance_to_Center_km\":5.0,\"Neighborhood_Score\":8.0,\"Has_Parking\":1,\"Property_Condition\":\"Good\",\"City_Zone\":\"North\"}'
```

Expected:
- `/health` → `{"status": "ok", "model_loaded": true}`
- `/predict` → a price in lakhs

---

### TASK 4 — Generate Traffic for Dashboard Data
```powershell
1..60 | ForEach-Object {
  $beds = Get-Random -Minimum 1 -Maximum 5
  curl -s -X POST http://localhost:8000/predict `
    -H "Content-Type: application/json" `
    -d "{`"Area_sqft`":$((Get-Random -Minimum 500 -Maximum 2500)),`"Bedrooms`":$beds,`"Bathrooms`":2,`"Age_Years`":10,`"Distance_to_Center_km`":5.0,`"Neighborhood_Score`":7.0,`"Has_Parking`":1,`"Property_Condition`":`"Good`",`"City_Zone`":`"North`"}" | Out-Null
}
```

---

### TASK 5 — Verify Prometheus
- Open http://localhost:9090/targets
- Confirm `house_price_api` target is **UP**

📸 **Evidence:** Screenshot of Prometheus targets page.

---

### TASK 6 — Verify Grafana Dashboard
- Open http://localhost:3000 → login `admin` / `admin`
- Navigate to **Dashboards → House Price API**
- 4 panels should show data: Requests/sec, Error rate, Latency p95, Price distribution

📸 **Evidence:** Screenshot of Grafana dashboard with all 4 panels showing data.

---

### TASK 7 — Verify MLflow UI
- Open http://localhost:5000
- Check experiment runs are visible
- Check **Models** tab → `house_price_model` in **Production** stage

📸 **Evidence:** Screenshot of MLflow UI.

---

### TASK 8 — Rollback Test
```powershell
docker compose down
docker tag house-price-api:local house-price-api:rollback-test
docker compose up -d
curl http://localhost:8000/health
curl http://localhost:8000/lineage
```
Note which tag was used and that service came back up.

---

### TASK 9 — Commit + Open PR
```powershell
git add -A
git commit -m "Docker stack verified: all 4 services up, Grafana dashboard with data, rollback tested"
git push origin saachis-development
```
Then open a Pull Request from `saachis-development` → `main` on GitHub.

---

## 🏗️ Architecture Reference

```
Raw CSV datasets
    │
    ▼
[ingest] ──► [data gate] ──fail──► STOP (old model stays live)
                 │ pass
                 ▼
         [feature engineering]
                 │
                 ▼
            [train model]
                 │
                 ▼
         [model gate] ──fail──► STOP (old model stays live)
                 │ pass
                 ▼
       [register + promote to Production]  ──► MLflow Registry (:5000)
                 │
                 ▼
        [FastAPI service on :8000]
         ├── /health
         ├── /predict
         ├── /lineage
         └── /metrics  ◄─── Prometheus (:9090) scrapes every 10s
                                  │
                                  ▼
                          Grafana (:3000) — House Price API dashboard

        [drift + perf monitor] ← run_monitoring.py
```

---

## 🐳 Docker Architecture

```
docker-compose.yml
├── app          → builds from Dockerfile (python:3.11-slim)
│                  bundles: src/, config/, models/, datasets/
│                  CMD: uvicorn src.serving.app:app --host 0.0.0.0 --port 8000
├── prometheus   → prom/prometheus:v2.54.1
│                  config: monitoring/prometheus.yml
├── grafana      → grafana/grafana:11.2.0
│                  auto-provisioned datasource + dashboard from monitoring/grafana/
└── mlflow       → ghcr.io/mlflow/mlflow:v2.17.2
                   backend: sqlite mlflow.db
```

**Prometheus metrics exposed by FastAPI:**
| Metric | Type |
|--------|------|
| `prediction_requests_total` | counter |
| `prediction_errors_total` | counter |
| `prediction_latency_seconds` | histogram |
| `predicted_price_lakhs` | histogram |

---

## 📊 Current Monitoring Report

| Batch | Rows | Drifted Features | Alert? |
|-------|------|-----------------|--------|
| batch_1 | 500 | none | ❌ No |
| batch_2 | 500 | none | ❌ No |
| batch_3 | 500 | Area_sqft, Bedrooms, City_Zone | ✅ YES (RMSE 18.07 > 1.25× ref 9.59) |

Batch 3 triggered the drift alert — demonstrating monitoring works correctly.

---

## 🔧 Troubleshooting Quick Reference

| Problem | Fix |
|---------|-----|
| Container exited | `docker compose logs app` |
| `/health` returns `model_loaded: false` | Run `python run_pipeline.py` first |
| Grafana panels say "No data" | Send more traffic; wait 30s for scrape |
| Prometheus target DOWN | Check app container is running |
| Grafana data source fails | URL inside Docker must be `http://prometheus:9090` |
| Port conflict | Something else using :8000/:9090/:3000/:5000 |

---

## ✅ Session Completion Checklist

- [x] Docker Desktop installed and running (v28.0.4)
- [x] `docker compose up --build -d` succeeds
- [x] `docker compose ps` shows all 4 containers healthy
- [x] `/health` returns `model_loaded: true`
- [x] `/predict` returns a valid price
- [x] Prometheus target `house_price_api` is UP
- [x] Traffic generated (60+ requests)
- [x] Grafana dashboard shows data in all 4 panels
- [x] MLflow UI verified running
- [x] Rollback test completed + note written
- [x] Docker versions recorded: Docker 28.0.4 / Compose v2.34.0-desktop.1
- [x] Code committed to `saachis-development`
- [ ] PR opened to `main`
- [x] Evidence documented in `SAACHI_EVIDENCE_RECORD.md`
