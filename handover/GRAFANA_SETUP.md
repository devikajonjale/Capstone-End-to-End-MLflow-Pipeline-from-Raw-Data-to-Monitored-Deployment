# Grafana setup for this project

Grafana shows the operational metrics of the prediction service: how many
requests arrive, how many fail, how fast responses are, and the spread of
predicted prices. It reads those metrics from Prometheus, which scrapes the
`/metrics` endpoint the FastAPI service exposes.

With `docker compose up` this is all wired automatically. This guide explains
the automatic setup, and then how to build the same thing by hand in case you
want to understand or recreate it.

## How the pieces connect

```
FastAPI /metrics  -->  Prometheus (scrapes every 10s)  -->  Grafana (queries Prometheus)
```

The metrics the service publishes are:

| Metric | Type | Meaning |
|--------|------|---------|
| `prediction_requests_total` | counter | number of prediction requests |
| `prediction_errors_total` | counter | number of failed requests |
| `prediction_latency_seconds` | histogram | request latency |
| `predicted_price_lakhs` | histogram | distribution of predicted prices |

## The automatic setup (recommended)

1. From the project root, start everything:

   ```bash
   docker compose up --build -d
   ```

2. Open http://localhost:3000 and log in with `admin` / `admin`.

3. The Prometheus data source and the **House Price API** dashboard are already
   there. They come from the files under `monitoring/grafana/provisioning`,
   which Grafana reads on start:
   - `provisioning/datasources/datasource.yml` adds Prometheus at
     `http://prometheus:9090`.
   - `provisioning/dashboards/dashboard.yml` tells Grafana to load any
     dashboard JSON in `/var/lib/grafana/dashboards`.
   - `monitoring/grafana/dashboards/house_price.json` is that dashboard.

4. Send some traffic to the service so the panels have data (see
   `HANDOVER_DOCKER.md` section 3), then watch the dashboard update.

## Building it by hand

If you are not using the provisioning files, or want to recreate the dashboard
in a fresh Grafana:

1. Log in to Grafana (admin / admin).

2. Add the data source: **Connections** then **Data sources** then **Add data
   source**, choose **Prometheus**. Set the URL to `http://prometheus:9090` if
   Grafana runs in the same compose network, or `http://localhost:9090` if you
   run Grafana outside Docker. Click **Save and test**; it should say the data
   source is working.

3. Create a dashboard: **Dashboards** then **New** then **Import**, and upload
   `monitoring/grafana/dashboards/house_price.json`. When asked, pick the
   Prometheus data source you just added.

4. If you would rather add panels one at a time, create a new panel for each of
   these queries:

   | Panel | Prometheus query |
   |-------|------------------|
   | Requests per second | `sum(rate(prediction_requests_total[1m]))` |
   | Errors per second | `sum(rate(prediction_errors_total[1m]))` |
   | Total predictions | `sum(prediction_requests_total)` |
   | Latency p95 | `histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket[5m])) by (le))` |
   | Predicted price spread | `sum by (le) (predicted_price_lakhs_bucket)` |

## Alerts

The project defines two alert conditions for the batch monitoring, both in
`config/config.yaml` under `monitoring`:

- a feature is flagged when its Population Stability Index crosses 0.2,
- performance is flagged when a batch RMSE is more than 1.25 times the model's
  validated RMSE.

These are evaluated in `run_monitoring.py` and written to
`data/results/monitoring_report.md`. If you want the same thresholds as live
Grafana alerts on the serving metrics, add an alert rule on the latency panel
(for example p95 latency over 200 ms for 5 minutes) and on the error rate panel
(error rate above zero for 5 minutes). When an alert fires the on-call response
is to hold the current model, inspect the drifted features in the monitoring
report, and decide whether to retrain, which the pipeline will only promote if
the new model clears the model gate.

## Troubleshooting

- Dashboard panels say "No data": send some prediction requests first, and
  check the Prometheus target at http://localhost:9090/targets is UP.
- Data source test fails: check the URL. Inside Docker it must be the service
  name `http://prometheus:9090`, not `localhost`.
- Grafana did not load the dashboard: confirm the `monitoring/grafana` folders
  are mounted (see the volumes in `docker-compose.yml`).
