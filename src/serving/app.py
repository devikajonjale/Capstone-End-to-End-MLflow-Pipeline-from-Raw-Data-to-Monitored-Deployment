"""FastAPI serving layer for the production model.

Loads the self-contained pipeline from the committed production folder, adds
the derived features and scores a single listing. Operational metrics are
exposed at /metrics for Prometheus: request count, errors, latency and the
distribution of predicted prices.
"""
import json
import os
import pickle
import time

import pandas as pd
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel

from src.config_loader import load_config
from src.features import prepare_frame

app = FastAPI(title="House Price Prediction API", version="1.0.0")

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
    return {"status": "ok", "model_loaded": STATE["model"] is not None}


@app.get("/lineage")
def lineage() -> dict:
    """Expose the deployed model's lineage for the Task 5 demonstration."""
    return STATE["lineage"]


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
        value = float(STATE["model"].predict(X)[0])
        PRICE.observe(value)
        return {"predicted_price_lakhs": round(value, 2)}
    except Exception as e:
        ERRORS.inc()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        LATENCY.observe(time.perf_counter() - start)
