"""Stage 5: the MODEL GATE.

Scores the candidate pipeline on an untouched holdout and applies two tests:

* Absolute quality thresholds (RMSE, MAE, R squared, MAPE) from
  config.model_gate.
* Champion vs Challenger: the candidate must not be worse than the model
  already in production by more than a configurable RMSE tolerance.

A failure does not raise. The pipeline reads the pass flag and simply keeps
the previous model, so the running service is never interrupted by a bad
training run.
"""
import logging
import os
import pickle
from typing import Optional, Tuple

import mlflow
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)

logger = logging.getLogger(__name__)


class ModelValidationError(ValueError):
    pass


def _score(model, X: pd.DataFrame, y: pd.Series) -> dict:
    pred = model.predict(X)
    return {
        "rmse": float(root_mean_squared_error(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        "mape": float(mean_absolute_percentage_error(y, pred)),
    }


def _load_production_model(config: dict):
    path = os.path.join(config["registry"]["production_dir"], "model.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def evaluate_model(
    model, X_test: pd.DataFrame, y_test: pd.Series, config: dict,
    run_id: Optional[str] = None,
) -> Tuple[dict, bool]:
    gate = config["model_gate"]
    metrics = _score(model, X_test, y_test)
    logger.info("Holdout metrics: %s", metrics)

    reasons = []
    if metrics["rmse"] > gate["max_rmse"]:
        reasons.append(f"RMSE {metrics['rmse']:.2f} over limit {gate['max_rmse']}")
    if metrics["mae"] > gate["max_mae"]:
        reasons.append(f"MAE {metrics['mae']:.2f} over limit {gate['max_mae']}")
    if metrics["r2"] < gate["min_r2"]:
        reasons.append(f"R2 {metrics['r2']:.3f} under floor {gate['min_r2']}")
    if "max_mape" in gate and metrics["mape"] > gate["max_mape"]:
        reasons.append(f"MAPE {metrics['mape']:.3f} over limit {gate['max_mape']}")

    # Champion vs Challenger: compare against the incumbent on the same holdout.
    prod = _load_production_model(config)
    if prod is not None:
        prod_metrics = _score(prod, X_test, y_test)
        logger.info("Champion (production) metrics on same holdout: %s", prod_metrics)
        allowed = prod_metrics["rmse"] + gate["rmse_tolerance"]
        if metrics["rmse"] > allowed:
            reasons.append(
                f"Challenger RMSE {metrics['rmse']:.2f} worse than Champion "
                f"{prod_metrics['rmse']:.2f} beyond tolerance {gate['rmse_tolerance']}"
            )
        metrics["production_rmse"] = prod_metrics["rmse"]
        metrics["beat_champion"] = metrics["rmse"] <= prod_metrics["rmse"]

    passed = not reasons
    if run_id:
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metrics({f"gate_{k}": v for k, v in metrics.items()
                                if isinstance(v, (int, float))})
            mlflow.set_tag("gate_passed", str(passed))

    if passed:
        logger.info("Model gate passed")
    else:
        logger.warning("Model gate failed: %s", "; ".join(reasons))

    metrics["passed"] = passed
    metrics["reasons"] = reasons
    return metrics, passed
