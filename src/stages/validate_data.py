"""Stage 2: the DATA GATE.

Checks schema, missing-value share and value ranges against the thresholds in
config.data_gate. If any check fails it raises DataValidationError, which the
pipeline catches so the run stops cleanly and the production model is left
untouched.
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidationError(ValueError):
    """Raised when an incoming batch or the training data fails the gate."""
    pass


def validate_data(df: pd.DataFrame, config: dict) -> bool:
    gate = config["data_gate"]
    logger.info("Running data gate on %d rows", len(df))

    required = gate["required_columns"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")

    max_missing = gate["max_missing_pct"]
    for col in required:
        share = df[col].isnull().mean()
        if share > max_missing:
            raise DataValidationError(
                f"Column {col} is {share:.1%} missing, over the "
                f"{max_missing:.0%} limit"
            )

    for col, bounds in gate["value_ranges"].items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        if "min" in bounds and series.min() < bounds["min"]:
            raise DataValidationError(
                f"Column {col} has a value below the minimum of {bounds['min']}"
            )
        if "max" in bounds and series.max() > bounds["max"]:
            raise DataValidationError(
                f"Column {col} has a value above the maximum of {bounds['max']}"
            )

    logger.info("Data gate passed")
    return True
