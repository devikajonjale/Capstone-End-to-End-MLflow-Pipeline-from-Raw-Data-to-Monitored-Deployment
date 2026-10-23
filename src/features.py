"""Feature logic shared by training and serving.

Keeping this in one place means the model is trained on exactly the columns
it later sees at inference time. The scikit-learn preprocessing (imputation,
scaling, one-hot encoding) lives inside the model Pipeline, so these helpers
only deal with column selection and the derived features.

Derived features:
    rooms_total        total room count, a proxy for usable space.
    area_per_room      floor area divided by rooms, captures room size.
    bath_to_bed_ratio  bathrooms per bedroom, a proxy for amenity level.
    overall_desirability a composite neighbourhood-vs-distance score.
"""
import numpy as np
import pandas as pd

DERIVED_FEATURES = [
    "rooms_total",
    "area_per_room",
    "bath_to_bed_ratio",
    "overall_desirability",
]


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the four derived features without touching the original frame."""
    out = df.copy()
    if {"Bedrooms", "Bathrooms"}.issubset(out.columns):
        out["rooms_total"] = out["Bedrooms"] + out["Bathrooms"]
        # +1 in the denominator avoids division by zero and dampens the ratio
        # for very small listings.
        out["bath_to_bed_ratio"] = out["Bathrooms"] / (out["Bedrooms"] + 1.0)
    if {"Area_sqft", "rooms_total"}.issubset(out.columns):
        out["area_per_room"] = out["Area_sqft"] / out["rooms_total"].replace(0, np.nan)
    if {"Neighborhood_Score", "Distance_to_Center_km"}.issubset(out.columns):
        # Higher neighbourhood quality raises desirability; distance from the
        # city centre lowers it. The +1 keeps the score bounded near the
        # centre and prevents a 0 km listing from exploding the value.
        out["overall_desirability"] = (
            (out["Neighborhood_Score"] / 10.0)
            * (1.0 / (out["Distance_to_Center_km"].fillna(0) + 1.0))
        )
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
