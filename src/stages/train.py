"""Stage 4: train.

Builds a single scikit-learn Pipeline that carries preprocessing and the
RandomForest together, so the saved artifact can score raw listings directly.
Every run is logged to MLflow with its parameters, metrics and the data
version, which is what makes the lineage in Task 5 work.
"""
import hashlib
import logging
from typing import Tuple

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features import model_input_columns

logger = logging.getLogger(__name__)


def build_estimator(config: dict) -> Pipeline:
    """Assemble the preprocessing plus RandomForest pipeline from config."""
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
    pre = ColumnTransformer([
        ("num", numeric, cols["numeric"]),
        ("cat", categorical, cols["categorical"]),
    ])

    m = config["model"]
    rf = RandomForestRegressor(random_state=m["random_state"], **m["hyperparameters"])
    return Pipeline([("pre", pre), ("model", rf)])


def _data_version(X: pd.DataFrame, y: pd.Series) -> str:
    """A short content hash of the training data, recorded for lineage."""
    h = hashlib.sha256()
    h.update(pd.util.hash_pandas_object(X, index=True).values.tobytes())
    h.update(pd.util.hash_pandas_object(y, index=True).values.tobytes())
    return h.hexdigest()[:12]


def train_model(X: pd.DataFrame, y: pd.Series, config: dict) -> Tuple[Pipeline, dict, str]:
    m = config["model"]
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=m["test_size"], random_state=m["random_state"]
    )

    mlflow.set_tracking_uri(config["mlflow"]["tracking_uri"])
    mlflow.set_experiment(config["mlflow"]["experiment_name"])

    with mlflow.start_run() as run:
        pipe = build_estimator(config)
        logger.info("Training %s", m["model_type"])
        pipe.fit(X_tr, y_tr)

        pred = pipe.predict(X_val)
        metrics = {
            "rmse": float(root_mean_squared_error(y_val, pred)),
            "mae": float(mean_absolute_error(y_val, pred)),
            "r2": float(r2_score(y_val, pred)),
        }
        logger.info("Validation metrics: %s", metrics)

        mlflow.log_params(m["hyperparameters"])
        mlflow.log_param("model_type", m["model_type"])
        mlflow.log_param("test_size", m["test_size"])
        mlflow.log_param("data_version", _data_version(X, y))
        mlflow.log_param("config_version", config["project"]["version"])
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(pipe, name="model", serialization_format="cloudpickle")

        run_id = run.info.run_id
        logger.info("Logged MLflow run %s", run_id)

    return pipe, metrics, run_id
