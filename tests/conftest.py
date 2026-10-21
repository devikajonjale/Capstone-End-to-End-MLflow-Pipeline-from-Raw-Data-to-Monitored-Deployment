import numpy as np
import pandas as pd
import pytest

from src.config_loader import load_config

ZONES = ["North", "South", "East", "West", "Central"]
CONDITIONS = ["Poor", "Fair", "Good", "Excellent"]


@pytest.fixture
def config():
    return load_config("config/config.yaml")


@pytest.fixture
def sample_df():
    """A small, valid frame shaped like the training data."""
    rng = np.random.default_rng(42)
    n = 120
    area = rng.integers(400, 2500, n)
    beds = rng.integers(1, 5, n)
    baths = rng.integers(1, 4, n)
    df = pd.DataFrame({
        "House_ID": [f"HS-{i:06d}" for i in range(n)],
        "Area_sqft": area,
        "Bedrooms": beds,
        "Bathrooms": baths,
        "Age_Years": rng.integers(0, 60, n).astype(float),
        "Distance_to_Center_km": rng.uniform(1, 30, n).round(1),
        "Neighborhood_Score": rng.uniform(2, 9, n).round(1),
        "Has_Parking": rng.integers(0, 2, n),
        "Property_Condition": rng.choice(CONDITIONS, n),
        "City_Zone": rng.choice(ZONES, n),
    })
    # price loosely driven by area and rooms so a model can learn something
    df["Price_Lakhs"] = (area * 0.04 + (beds + baths) * 3
                         + rng.normal(0, 3, n)).round(2)
    return df
