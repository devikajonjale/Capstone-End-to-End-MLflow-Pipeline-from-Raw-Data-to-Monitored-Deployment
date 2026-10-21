"""Stage 7: monitor.

Measures drift between a reference set (the training data) and an incoming
batch. Feature drift uses the Population Stability Index (PSI); performance
drift uses the batch RMSE of the production model against the training RMSE,
which is possible here because the batches carry the true price.

PSI is used instead of Evidently so the monitoring logic is transparent,
dependency-light and easy to explain in the demonstration. The thresholds and
their interpretation live in config.monitoring.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import root_mean_squared_error

from src.features import prepare_frame

logger = logging.getLogger(__name__)


def population_stability_index(expected: pd.Series, actual: pd.Series, bins: int) -> float:
    """PSI for one column. Numeric columns are binned by quantile; categorical
    columns compare category shares. Small epsilon avoids divide-by-zero."""
    expected = expected.dropna()
    actual = actual.dropna()
    if expected.empty or actual.empty:
        return 0.0
    eps = 1e-6

    if pd.api.types.is_numeric_dtype(expected):
        quantiles = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
        if len(quantiles) < 3:
            return 0.0
        quantiles[0], quantiles[-1] = -np.inf, np.inf
        e = np.histogram(expected, bins=quantiles)[0] / len(expected)
        a = np.histogram(actual, bins=quantiles)[0] / len(actual)
    else:
        cats = expected.astype(str).unique()
        e = np.array([(expected.astype(str) == c).mean() for c in cats])
        a = np.array([(actual.astype(str) == c).mean() for c in cats])

    e = np.clip(e, eps, None)
    a = np.clip(a, eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def monitor_batch(
    reference_df: pd.DataFrame, batch_df: pd.DataFrame, config: dict,
    model=None, batch_label: Optional[str] = None,
    baseline_rmse: Optional[float] = None,
) -> dict:
    mon = config["monitoring"]
    fe = config["feature_engineering"]
    target = fe["target"]
    features = fe["numeric_features"] + fe["categorical_features"]
    label = batch_label or "batch"
    logger.info("Monitoring %s (%d rows)", label, len(batch_df))

    psi_scores = {}
    for col in features:
        if col in reference_df.columns and col in batch_df.columns:
            psi_scores[col] = round(
                population_stability_index(reference_df[col], batch_df[col], mon["bins"]), 4
            )

    drifted = [c for c, v in psi_scores.items() if v >= mon["psi_alert"]]
    watch = [c for c, v in psi_scores.items() if mon["psi_warn"] <= v < mon["psi_alert"]]

    result = {
        "batch": label,
        "n_rows": int(len(batch_df)),
        "psi": psi_scores,
        "drifted_features": drifted,
        "watch_features": watch,
        "data_drift_alert": len(drifted) > 0,
    }

    # Performance drift, only possible because the batch has true prices.
    if model is not None and target in batch_df.columns:
        pred = model.predict(prepare_frame(batch_df, config))
        batch_rmse = float(root_mean_squared_error(batch_df[target], pred))
        # Baseline is the model's validated holdout RMSE (from lineage) rather
        # than an in-sample score, which would be optimistically low.
        if baseline_rmse is not None:
            ref_rmse = float(baseline_rmse)
        else:
            ref_pred = model.predict(prepare_frame(reference_df, config))
            ref_rmse = float(root_mean_squared_error(reference_df[target], ref_pred))
        ratio = batch_rmse / ref_rmse if ref_rmse else float("inf")
        result["batch_rmse"] = round(batch_rmse, 3)
        result["reference_rmse"] = round(ref_rmse, 3)
        result["rmse_ratio"] = round(ratio, 3)
        result["performance_alert"] = ratio > mon["performance_alert_ratio"]

    result["alert"] = result["data_drift_alert"] or result.get("performance_alert", False)
    if result["alert"]:
        logger.warning("ALERT on %s: drifted=%s perf=%s",
                       label, drifted, result.get("performance_alert"))
    else:
        logger.info("%s within thresholds", label)
    return result
