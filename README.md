# MLOps Project End‑to‑End Pipeline

## Overview
This repository implements the full MLOps lifecycle for a real‑estate price prediction model.
- **Data ingestion, validation, feature engineering, training, evaluation, registration, deployment and monitoring** are orchestrated with **Prefect** in `src/pipeline.py`.
- Configuration lives in a single YAML file (`config/config.yaml`).
- Model tracking and registry are handled by **MLflow**.
- The serving API is built with **FastAPI** and containerised.
- **Prometheus** scrapes metrics from the API and Grafana visualises them.
- CI/CD is powered by **GitHub Actions** – tests run on every PR and a Docker image is built on merge.

## Quick start (local)
1. **Install dependencies** (user‑level to avoid permission issues on Windows)
   ```powershell
   python -m pip install --upgrade pip --user
   python -m pip install -r requirements.txt --user
   ```
2. **Run the test suite**
   ```powershell
   python -m pytest -q
   ```
3. **Start the services** with Docker Compose (requires Docker Desktop)
   ```powershell
   docker compose up -d
   ```
   This brings up:
   - `app` – the FastAPI serving container (http://localhost:8000)
   - `mlflow` – tracking server (http://localhost:5000)
   - `prometheus` – metrics store (http://localhost:9090)
   - `grafana` – dashboard UI (http://localhost:3000, default user/password `admin`/`admin`)
4. **Check the API**
   ```powershell
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"features\":{\"Area_sqft\":1200,\"Bedrooms\":3,\"Bathrooms\":2,\"Age_Years\":10,\"Distance_to_Center_km\":5.0,\"Neighborhood_Score\":8.0,\"Has_Parking\":1,\"Property_Condition\":\"Good\",\"City_Zone\":\"North\"}}"
   ```
5. **View metrics** at `http://localhost:9090` (Prometheus) and **Grafana** at `http://localhost:3000`.

## Grafana dashboard setup
1. Log in to Grafana (admin/admin).
2. Add a data source:
   - **Prometheus**, URL `http://prometheus:9090` (use the container name when running inside Docker, otherwise `http://localhost:9090`).
3. Import a dashboard JSON. Save the following as `grafana_dashboard.json` and import it via *Dashboard ➜ Import*:
   ```json
   {
     "annotations": {"list": []},
     "templating": {"list": []},
     "panels": [
       {
         "type": "graph",
         "title": "Prediction Requests",
         "targets": [{"expr": "prediction_requests_total", "legendFormat": "requests"}]
       },
       {
         "type": "graph",
         "title": "Prediction Latency",
         "targets": [{"expr": "prediction_latency_seconds", "legendFormat": "latency"}]
       },
       {
         "type": "graph",
         "title": "Predicted Price Distribution",
         "targets": [{"expr": "prediction_value", "legendFormat": "price"}]
       }
     ],
     "schemaVersion": 30,
     "version": 1
   }
   ```
   The panels display request count, latency and the distribution of predicted house prices.

## CI workflow (`.github/workflows/ci.yml`)
- Runs on every push and pull request.
- Installs dependencies, runs the full pytest suite, builds a Docker image and verifies it can import the package.

## Release workflow (`.github/workflows/release.yml`)
- Triggered when a Git tag matching `v*` is pushed.
- Builds the Docker image, tags it with the Git SHA and the version tag, and publishes a GitHub Release.
- The workflow also uploads the Docker image tarball as a release asset (no registry push to avoid secret handling).

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build Docker image
        run: |
          docker build -t mlops-project:${{ github.ref_name }} .
          docker save mlops-project:${{ github.ref_name }} -o mlops-project-${{ github.ref_name }}.tar

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          name: Release ${{ github.ref_name }}
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload Docker image artifact
        uses: softprops/action-gh-release@v1
        with:
          files: mlops-project-${{ github.ref_name }}.tar
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Git tags and releases
- After a successful merge to `main`, create a new tag locally:
  ```powershell
  git tag v1.0.0
  git push origin v1.0.0
  ```
- The `release.yml` workflow will automatically build the image and draft a GitHub Release.

## Project checklist
- [x] Configuration loader with validation (`src/config_loader.py`).
- [x] Complete Prefect pipeline (`src/pipeline.py`).
- [x] All stage modules present (`src/stages/*`).
- [x] FastAPI serving with Prometheus metrics (`src/serving/app.py`).
- [x] Dockerfile and `docker-compose.yml` to bring up app, MLflow, Prometheus and Grafana.
- [x] Test suite covering config, validation, feature engineering, gates and model training (`tests/*`).
- [x] CI workflow that runs tests and builds a Docker image.
- [x] Release workflow that creates a tag‑based release and uploads the image.
- [x] README with setup, run instructions and Grafana dashboard guide.
- [ ] **Documentation of rollback procedure** – currently described in the release workflow notes; a short `ROLLBACK.md` could be added.
- [ ] **Data drift monitoring logic** – `src/stages/monitor.py` exists but may need integration with Evidently; add a note to extend it.
- [ ] **Example Grafana dashboard JSON** – provided above for manual import.

### Next steps to reach 100 % completeness
1. Add a `ROLLBACK.md` file describing how to redeploy the previous Docker image (`docker load` the tarball from the release assets).
2. Flesh out `src/stages/monitor.py` to compute data drift with Evidently and expose metrics.
3. Add a small script `run_monitoring.py` that can be called from the pipeline for batch monitoring.
4. Record a short demo video of the full loop (code change → CI → Docker build → deployment → Grafana metrics) for the final presentation.

---
*Prepared by the Antigravity assistant.*
