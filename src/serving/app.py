"""FastAPI serving layer for the production model.

Loads the self-contained pipeline from the committed production folder, adds
the derived features and scores a single listing. Operational metrics are
exposed at /metrics for Prometheus: request count, errors, latency and the
distribution of predicted prices. The /predict response includes a 95
percent confidence interval; for a RandomForest champion this is derived
from the standard deviation of per-tree predictions, which is a lightweight,
model-aware uncertainty signal.
"""
import json
import os
import pickle
import time

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel

from src.config_loader import load_config
from src.features import prepare_frame

app = FastAPI(title="House Price Prediction API", version="1.1.0")

REQUESTS = Counter("prediction_requests_total", "Total prediction requests")
ERRORS = Counter("prediction_errors_total", "Total prediction errors")
LATENCY = Histogram("prediction_latency_seconds", "Prediction latency in seconds")
PRICE = Histogram(
    "predicted_price_lakhs", "Distribution of predicted prices in lakhs",
    buckets=[20, 40, 60, 80, 100, 120, 150, 200],
)

app.mount("/metrics", make_asgi_app())

STATE: dict = {"model": None, "config": None, "lineage": {}}


class Listing(BaseModel):
    Area_sqft: float
    Bedrooms: int
    Bathrooms: int
    Age_Years: float
    Distance_to_Center_km: float
    Neighborhood_Score: float
    Has_Parking: int
    Property_Condition: str
    City_Zone: str


def _config_path() -> str:
    env = os.environ.get("CONFIG_PATH")
    if env:
        return env
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    candidate = os.path.join(root, "config", "config.yaml")
    return candidate if os.path.exists(candidate) else "config/config.yaml"


@app.on_event("startup")
def load_assets() -> None:
    config = load_config(_config_path())
    STATE["config"] = config
    prod_dir = config["registry"]["production_dir"]
    model_path = os.path.join(prod_dir, "model.pkl")
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            STATE["model"] = pickle.load(f)
    lineage_path = os.path.join(prod_dir, "lineage.json")
    if os.path.exists(lineage_path):
        with open(lineage_path) as f:
            STATE["lineage"] = json.load(f)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": STATE["model"] is not None,
            "model_version": STATE["lineage"].get("registry_version"),
            "champion_algorithm": STATE["lineage"].get("champion_algorithm")}


@app.get("/lineage")
def lineage() -> dict:
    """Expose the deployed model's lineage for the Task 5 demonstration.

    Returns the full chain: registry version, MLflow run id, champion
    algorithm, git commit, config version, raw training CSV SHA-256 and the
    holdout metrics the gate signed off on.
    """
    return STATE["lineage"]


def _predict_with_interval(pipeline, X: pd.DataFrame, z: float):
    """Return (point estimate, lower, upper, std) in lakhs.

    If the champion is a RandomForest, uses the per-tree spread of predictions
    for a tight, model-aware CI. Otherwise falls back to a conservative prior
    equal to the champion's holdout RMSE.
    """
    model = pipeline.named_steps["model"]
    pre = pipeline.named_steps["pre"]
    X_t = pre.transform(X)
    if hasattr(model, "estimators_") and hasattr(model.estimators_[0], "predict"):
        preds = np.array([est.predict(X_t) for est in model.estimators_])
        mean = float(preds.mean(axis=0)[0])
        std = float(preds.std(axis=0)[0])
    else:
        mean = float(pipeline.predict(X)[0])
        std = float(STATE["lineage"].get("holdout_metrics", {}).get("rmse", 5.0))
    return mean, mean - z * std, mean + z * std, std


@app.post("/predict")
def predict(listing: Listing) -> dict:
    REQUESTS.inc()
    if STATE["model"] is None:
        ERRORS.inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    start = time.perf_counter()
    try:
        df = pd.DataFrame([listing.model_dump()])
        X = prepare_frame(df, STATE["config"])
        z = STATE["config"].get("serving", {}).get("confidence_z", 1.96)
        value, lower, upper, std = _predict_with_interval(STATE["model"], X, z)
        PRICE.observe(value)
        return {
            "predicted_price_lakhs": round(value, 2),
            "confidence_interval_lakhs": {
                "lower": round(max(0.0, lower), 2),
                "upper": round(upper, 2),
                "level": 0.95,
            },
            "model_version": STATE["lineage"].get("registry_version"),
        }
    except Exception as e:
        ERRORS.inc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        LATENCY.observe(time.perf_counter() - start)
