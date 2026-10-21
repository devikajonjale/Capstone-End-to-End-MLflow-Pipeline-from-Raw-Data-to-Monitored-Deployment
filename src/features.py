"""Feature logic shared by training and serving.

Keeping this in one place means the model is trained on exactly the columns
it later sees at inference time. The scikit-learn preprocessing (imputation,
scaling, one-hot encoding) lives inside the model Pipeline, so these helpers
only deal with column selection and the two derived features.
"""
import numpy as np
import pandas as pd

DERIVED_FEATURES = ["rooms_total", "area_per_room"]


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rooms_total and area_per_room without touching the original frame."""
    out = df.copy()
    if {"Bedrooms", "Bathrooms"}.issubset(out.columns):
        out["rooms_total"] = out["Bedrooms"] + out["Bathrooms"]
    if {"Area_sqft", "rooms_total"}.issubset(out.columns):
        out["area_per_room"] = out["Area_sqft"] / out["rooms_total"].replace(0, np.nan)
    return out


def model_input_columns(config: dict) -> dict:
    """Return the numeric and categorical column lists the model expects."""
    fe = config["feature_engineering"]
    numeric = list(fe["numeric_features"]) + DERIVED_FEATURES
    categorical = list(fe["categorical_features"])
    return {"numeric": numeric, "categorical": categorical}


def prepare_frame(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Drop id columns, add derived features and keep only model inputs.

    Used before predict() so the serving path and the training path produce
    identical column layouts.
    """
    cols = model_input_columns(config)
    enriched = add_derived_features(df)
    keep = cols["numeric"] + cols["categorical"]
    missing = [c for c in keep if c not in enriched.columns]
    for c in missing:
        enriched[c] = np.nan
    return enriched[keep]
