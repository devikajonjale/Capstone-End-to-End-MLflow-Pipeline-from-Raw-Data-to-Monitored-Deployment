"""Prefect orchestration for the house price pipeline.

Two flows are defined:

* training_flow  - ingest, data gate, features, train, model gate, register.
* monitoring_flow - run the data gate and drift/performance monitoring on one
  incoming batch against the training reference.

Each stage is a thin Prefect task wrapping a plain function from src.stages,
so every stage can also be imported and re-run on its own, and the unit tests
call the plain functions directly. When a gate fails the flow records a
"failed_safe" status and returns without changing the production model.
"""
import logging
from typing import Any, Dict, Optional

import pandas as pd
from prefect import flow, task
from sklearn.model_selection import train_test_split

from src.config_loader import load_config
from src.stages.evaluate import evaluate_model
from src.stages.feature_engineering import build_features
from src.stages.ingest import ingest_data
from src.stages.monitor import monitor_batch
from src.stages.register import register_model
from src.stages.train import train_model
from src.stages.validate_data import DataValidationError, validate_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("pipeline")


# Stage tasks (thin wrappers so Prefect records a node per stage).
ingest_task = task(name="ingest")(ingest_data)
validate_task = task(name="data_gate")(validate_data)
features_task = task(name="build_features")(build_features)
train_task = task(name="train")(train_model)
evaluate_task = task(name="model_gate")(evaluate_model)
register_task = task(name="register")(register_model)
monitor_task = task(name="monitor")(monitor_batch)


@flow(name="house_price_training")
def training_flow(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    config = load_config(config_path)
    summary: Dict[str, Any] = {"stage_reached": "start"}

    try:
        df = ingest_task(config)
        summary["stage_reached"] = "ingest"
        summary["n_rows"] = int(len(df))

        validate_task(df, config)
        summary["stage_reached"] = "data_gate"
        summary["data_gate"] = "passed"
    except DataValidationError as e:
        logger.error("Data gate failed: %s", e)
        return {**summary, "status": "failed_safe", "stage_reached": "data_gate",
                "data_gate": "failed", "error": str(e)}

    X, y = features_task(df, config)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config["model"]["test_size"],
        random_state=config["model"]["random_state"],
    )

    model, train_metrics, run_id = train_task(X_train, y_train, config)
    summary["stage_reached"] = "train"
    summary["run_id"] = run_id

    metrics, passed = evaluate_task(model, X_test, y_test, config, run_id)
    summary["stage_reached"] = "model_gate"
    summary["holdout_metrics"] = {k: metrics[k] for k in ("rmse", "mae", "r2")}
    summary["model_gate"] = "passed" if passed else "failed"

    if not passed:
        logger.warning("Model gate failed, production model kept: %s", metrics["reasons"])
        return {**summary, "status": "failed_safe", "reasons": metrics["reasons"]}

    version = register_task(model, run_id, metrics, config)
    summary["stage_reached"] = "register"
    summary["registered_version"] = version
    return {**summary, "status": "success"}


@flow(name="house_price_monitoring")
def monitoring_flow(
    batch_df: pd.DataFrame, config_path: str = "config/config.yaml",
    batch_label: Optional[str] = None,
) -> Dict[str, Any]:
    import json
    import pickle
    import os

    config = load_config(config_path)
    reference = pd.read_csv(config["data"]["raw_train_path"])

    try:
        validate_task(batch_df, config)
        gate = "passed"
    except DataValidationError as e:
        logger.error("Batch rejected by data gate: %s", e)
        return {"batch": batch_label, "status": "rejected",
                "data_gate": "failed", "error": str(e)}

    model = None
    baseline_rmse = None
    prod_dir = config["registry"]["production_dir"]
    prod_path = os.path.join(prod_dir, "model.pkl")
    if os.path.exists(prod_path):
        with open(prod_path, "rb") as f:
            model = pickle.load(f)
    lineage_path = os.path.join(prod_dir, "lineage.json")
    if os.path.exists(lineage_path):
        with open(lineage_path) as f:
            baseline_rmse = json.load(f).get("holdout_metrics", {}).get("rmse")

    result = monitor_task(reference, batch_df, config, model, batch_label, baseline_rmse)
    result["data_gate"] = gate
    result["status"] = "processed"
    return result


# Backwards-compatible entry point used by run_pipeline.py.
def run_pipeline(config_path: str = "config/config.yaml", batch_file: Optional[str] = None):
    if batch_file is None:
        return training_flow(config_path)
    batch_df = pd.read_csv(batch_file)
    return monitoring_flow(batch_df, config_path, batch_label=batch_file)
