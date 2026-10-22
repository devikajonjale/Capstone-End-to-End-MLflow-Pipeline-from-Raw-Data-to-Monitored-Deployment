# Docker handover for Saachi

This file covers the part of the project that needs Docker, which is not
installed on the main development machine. Everything else (pipeline, training,
gates, MLflow tracking and registry, monitoring report, tests, CI config) is
already built and working. Your job is to bring the stack up in containers,
confirm the service and the monitoring dashboard work, capture the evidence,
and send it back so it can go into the report.

Please commit your work on a branch under your own name so your contributions
show up in the repository history, as the brief requires.

## 0. Before you start

Install Docker Desktop and make sure it is running:

```bash
docker --version
docker compose version
```

Clone the repository and check out a branch:

```bash
git clone https://github.com/devikajonjale/Capstone-End-to-End-MLflow-Pipeline-from-Raw-Data-to-Monitored-Deployment.git
cd Capstone-End-to-End-MLflow-Pipeline-from-Raw-Data-to-Monitored-Deployment
git checkout -b docker-saachi
```

The repository already contains a trained model in `models/production/`, so the
container can serve predictions straight away without retraining. If that folder
is empty for any reason, run `python run_pipeline.py` once first (needs the
Python setup from the README).

## 1. Bring up the whole stack

From the project root:

```bash
docker compose up --build -d
```

This starts four services:

| Service | URL | What it is |
|---------|-----|------------|
| app | http://localhost:8000 | the FastAPI prediction service |
| prometheus | http://localhost:9090 | scrapes metrics from the service |
| grafana | http://localhost:3000 | dashboard, log in with admin / admin |
| mlflow | http://localhost:5000 | tracking and registry UI |

Check the containers are healthy:

```bash
docker compose ps
```

## 2. Confirm the service works

```bash
curl http://localhost:8000/health
curl http://localhost:8000/lineage
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"Area_sqft\":1200,\"Bedrooms\":3,\"Bathrooms\":2,\"Age_Years\":10,\"Distance_to_Center_km\":5.0,\"Neighborhood_Score\":8.0,\"Has_Parking\":1,\"Property_Condition\":\"Good\",\"City_Zone\":\"North\"}"
```

`/health` should report `model_loaded: true`, and `/predict` should return a
predicted price in lakhs.

## 3. Generate some traffic so the dashboard has data

Run this a few dozen times so Prometheus has points to plot. On PowerShell:

```powershell
1..60 | ForEach-Object {
  $beds = Get-Random -Minimum 1 -Maximum 5
  curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"Area_sqft\":$((Get-Random -Minimum 500 -Maximum 2500)),\"Bedrooms\":$beds,\"Bathrooms\":2,\"Age_Years\":10,\"Distance_to_Center_km\":5.0,\"Neighborhood_Score\":7.0,\"Has_Parking\":1,\"Property_Condition\":\"Good\",\"City_Zone\":\"North\"}" | Out-Null
}
```

## 4. Check Prometheus and Grafana

- Open http://localhost:9090/targets and confirm the `house_price_api` target
  is **UP**.
- Open http://localhost:3000, log in (admin / admin), and open the **House
  Price API** dashboard. It is loaded automatically. You should see request
  rate, error rate, latency and the predicted price distribution filling in.

The full Grafana walkthrough is in `GRAFANA_SETUP.md` if anything is missing.

## 5. Test the rollback once (Task 6 asks for this)

Follow `ROLLBACK.md` end to end once, using whichever image tag you have built,
and note that the service came back up. A short note that you did this is enough.

## 6. What to capture and send back

Please collect the following and send them to me (Aditya) so I can put them in
the report. A shared folder or a zip is fine.

1. Screenshot of `docker compose ps` showing all four services running.
2. Screenshot of the Prometheus targets page with `house_price_api` UP.
3. Screenshot of the Grafana **House Price API** dashboard after you have sent
   some traffic, showing the four panels with data.
4. Screenshot of the MLflow UI at http://localhost:5000 showing the experiment
   runs and the registered model in the Production stage.
5. One or two sentences on the rollback test (which tag, that it worked).
6. The exact Docker and Docker Compose versions you used (`docker --version`,
   `docker compose version`), so the report can state the environment.

If any step fails, send me the output of `docker compose logs app` and
`docker compose logs grafana` and I will help debug.

## 7. Push your branch

```bash
git add -A
git commit -m "Docker stack brought up and verified, evidence captured"
git push origin docker-saachi
```

Then open a pull request so CI runs on it. That gives us a pull request in the
CI history as well.
