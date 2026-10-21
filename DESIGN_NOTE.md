# Design note: house price prediction pipeline

## Business objective

A real-estate analytics start-up quotes asking prices for property listings.
New batches of listings arrive regularly and today each retraining and release
is done by hand, with no record of which data or code produced which model. The
objective is one automated pipeline that turns raw listings into a live,
monitored prediction service and refuses to ship a model when the data or the
model is not good enough.

## Success metrics

The error metric is Root Mean Squared Error (RMSE) in lakhs of rupees, with Mean
Absolute Error (MAE) and R squared reported alongside it.

| Metric | Threshold | Plain-language meaning |
|--------|-----------|------------------------|
| RMSE | at most 18 lakhs | typical miss on a quote stays small relative to prices that run from about 20 to 150 lakhs |
| MAE | at most 13 lakhs | on an average listing the quote is off by less than the price of a small extra room |
| R squared | at least 0.65 | the model explains most of the price variation rather than guessing the average |

The thresholds are set from the price range in the data. Median price is near 60
lakhs, so an RMSE of 18 is under a third of a typical price, which is the worst
quote the founders said they would accept while still being useful. The model
built on the supplied data reaches RMSE near 9.6, MAE near 7.5 and R squared near
0.81 on a held-out set, comfortably inside the bar, which leaves headroom for
drift before quality falls below the threshold.

## Non-functional requirements

- Prediction latency under 200 ms per request at the service, which the single
  tree-ensemble model meets with room to spare.
- Model freshness: a new batch can be validated, scored and, if a retrain is
  warranted, promoted on the same day it arrives.
- Reproducibility: a fresh clone reproduces the reported metrics within a small
  tolerance because the data, code and config are all versioned and a data hash
  is recorded per run.
- Safety: only the pipeline changes the production model, and a failed gate
  leaves the running service untouched.

## Architecture and lifecycle mapping

```
raw CSV --> ingest --> data gate --> features --> train --> model gate --> register --> serve --> monitor
                                                                                  |                   |
                                                                             MLflow registry      Prometheus + Grafana
```

| Component | Lifecycle stage | Where in the repo |
|-----------|-----------------|-------------------|
| config.yaml and loader | problem framing, configuration | `config/`, `src/config_loader.py` |
| ingest | data collection | `src/stages/ingest.py` |
| data gate | data validation | `src/stages/validate_data.py` |
| feature build | feature engineering | `src/features.py`, `src/stages/feature_engineering.py` |
| train | model training and tuning | `src/stages/train.py` |
| model gate | model validation | `src/stages/evaluate.py` |
| register and promote | model registry and release | `src/stages/register.py` |
| FastAPI service | deployment and serving | `src/serving/app.py` |
| monitor | monitoring and drift | `src/stages/monitor.py`, `run_monitoring.py` |
| Prefect flows | orchestration | `src/pipeline.py` |
| GitHub Actions | CI/CD | `.github/workflows/` |

Every box in the architecture maps to a lifecycle stage and to a module, and
every stage can be re-run on its own.
