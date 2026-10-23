"""Stage 4: train.

Runs 5-fold cross-validation across several candidate algorithms, logs each
candidate as its own MLflow run, and returns the champion for the model gate
to evaluate. Candidates are declared in config.model.candidates; the champion
is picked by lowest mean CV RMSE. Every run records parameters, metrics (RMSE,
MAE, R squared, MAPE), the data version hash, and the serialised pipeline.
"""
import hashlib
import logging
from typing import Tuple

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features import model_input_columns

logger = logging.getLogger(__name__)


ESTIMATORS = {
    "ridge": Ridge,
    "random_forest": RandomForestRegressor,
    "gradient_boosting": GradientBoostingRegressor,
}


def _preprocessor(config: dict) -> ColumnTransformer:
    """Imputation + scaling + one-hot, shared across all candidate estimators."""
    cols = model_input_columns(config)
    imp = config["feature_engineering"]["imputation"]
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy=imp["strategy_numeric"])),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy=imp["strategy_categorical"])),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric, cols["numeric"]),
        ("cat", categorical, cols["categorical"]),
    ])


def _estimator_for(name: str, params: dict, random_state: int):
    cls = ESTIMATORS[name]
    kwargs = dict(params)
    if "random_state" in cls().get_params():
        kwargs.setdefault("random_state", random_state)
    return cls(**kwargs)


def build_estimator(config: dict, candidate: str = None) -> Pipeline:
    """Build the preprocessing + model pipeline for one named candidate.

    When `candidate` is omitted the first entry in `config.model.candidates`
    (or the legacy `model.model_type` fallback) is used, which keeps backward
    compatibility with earlier tests.
    """
    m = config["model"]
    name = candidate or m.get("candidates", [{"name": m.get("model_type", "random_forest")}])[0]["name"]
    cand_params = {}
    for c in m.get("candidates", []):
        if c["name"] == name:
            cand_params = c.get("hyperparameters", {})
            break
    if not cand_params:
        cand_params = m.get("hyperparameters", {})
    est = _estimator_for(name, cand_params, m["random_state"])
    return Pipeline([("pre", _preprocessor(config)), ("model", est)])


def _data_version(X: pd.DataFrame, y: pd.Series) -> str:
    h = hashlib.sha256()
    h.update(pd.util.hash_pandas_object(X, index=True).values.tobytes())
    h.update(pd.util.hash_pandas_object(y, index=True).values.tobytes())
    return h.hexdigest()[:12]


def _score_full(model, X: pd.DataFrame, y: pd.Series) -> dict:
    pred = model.predict(X)
    return {
        "rmse": float(root_mean_squared_error(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        "mape": float(mean_absolute_percentage_error(y, pred)),
    }


def train_model(X: pd.DataFrame, y: pd.Series, config: dict) -> Tuple[Pipeline, dict, str]:
    """Train all candidates with 5-fold CV, pick the champion by CV RMSE.

    Each candidate is logged as its own MLflow run under a shared parent so
    the registry retains a comparison trail. The champion is also re-fit on
    the held-out training split and returned.
    """
    m = config["model"]
    cv_cfg = m.get("cv", {})
    n_splits = int(cv_cfg.get("n_splits", 5))

    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=m["test_size"], random_state=m["random_state"]
    )

    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    candidates = m.get("candidates")
    if not candidates:
        # Legacy single-estimator config.
        candidates = [{"name": m.get("model_type", "random_forest"),
                       "hyperparameters": m.get("hyperparameters", {})}]

    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=m["random_state"])
    data_hash = _data_version(X, y)

    champion = {"name": None, "pipeline": None, "metrics": None, "run_id": None,
                "cv_rmse_mean": float("inf")}
    comparison = []

    with mlflow.start_run(run_name="train_candidates") as parent:
        mlflow.log_param("data_version", data_hash)
        mlflow.log_param("config_version", config["project"]["version"])
        mlflow.log_param("cv_splits", n_splits)

        for cand in candidates:
            name = cand["name"]
            params = cand.get("hyperparameters", {})
            with mlflow.start_run(run_name=f"train_{name}", nested=True) as run:
                pipe = Pipeline([("pre", _preprocessor(config)),
                                 ("model", _estimator_for(name, params, m["random_state"]))])
                logger.info("Training candidate %s with %s", name, params)

                # 5-fold CV on the training split, scored by negative RMSE.
                cv_neg = cross_val_score(pipe, X_tr, y_tr, cv=kfold,
                                         scoring="neg_root_mean_squared_error")
                cv_rmse = (-cv_neg).astype(float)
                cv_mean, cv_std = float(cv_rmse.mean()), float(cv_rmse.std())

                pipe.fit(X_tr, y_tr)
                val_metrics = _score_full(pipe, X_val, y_val)

                mlflow.log_params(params)
                mlflow.log_param("algorithm", name)
                mlflow.log_param("data_version", data_hash)
                mlflow.log_param("config_version", config["project"]["version"])
                mlflow.log_metrics({
                    "cv_rmse_mean": cv_mean,
                    "cv_rmse_std": cv_std,
                    **{f"val_{k}": v for k, v in val_metrics.items()},
                })
                mlflow.sklearn.log_model(pipe, name="model",
                                        serialization_format="cloudpickle")

                comparison.append({
                    "algorithm": name, "cv_rmse_mean": round(cv_mean, 3),
                    "cv_rmse_std": round(cv_std, 3),
                    **{f"val_{k}": round(v, 3) for k, v in val_metrics.items()},
                })

                if cv_mean < champion["cv_rmse_mean"]:
                    champion.update({
                        "name": name, "pipeline": pipe,
                        "metrics": val_metrics, "run_id": run.info.run_id,
                        "cv_rmse_mean": cv_mean,
                    })

        mlflow.log_param("champion_algorithm", champion["name"])
        mlflow.log_metric("champion_cv_rmse", champion["cv_rmse_mean"])

    logger.info("Champion: %s (CV RMSE %.3f)", champion["name"], champion["cv_rmse_mean"])
    logger.info("Candidate comparison: %s", comparison)

    # Expose the comparison for the pipeline summary.
    champion["comparison"] = comparison
    champion["metrics"]["champion_algorithm"] = champion["name"]
    return champion["pipeline"], champion["metrics"], champion["run_id"]
