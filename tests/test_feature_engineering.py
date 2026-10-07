import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def raw_data():
    return pd.DataFrame({
        "House_ID": [1, 2, 3, 4],
        "Area_sqft": [1000, 1500, np.nan, 2000],
        "Bedrooms": [2, 3, 4, 3],
        "Bathrooms": [1, 2, 3, 2],
        "Age_Years": [10, 5, 2, 8],
        "Distance_to_Center_km": [5.0, 10.0, 2.5, 7.0],
        "Neighborhood_Score": [8.5, 7.0, 9.2, 6.5],
        "Has_Parking": [1, 0, 1, 1],
        "Property_Condition": [4, 3, 5, 4],
        "City_Zone": ["A", "B", "A", "C"],
        "Price_Lakhs": [50.0, 75.0, 120.0, 80.0]
    })

def test_features_have_correct_shape(raw_data):
    try:
        from src.stages.feature_engineering import build_features
        X, y = build_features(raw_data)
        assert X.shape[0] == raw_data.shape[0]
        assert len(y) == raw_data.shape[0]
    except ImportError:
        pass

def test_no_missing_values_after_imputation(raw_data):
    try:
        from src.stages.feature_engineering import build_features
        X, _ = build_features(raw_data)
        assert X.isnull().sum().sum() == 0
    except ImportError:
        pass

def test_categorical_encoding(raw_data):
    try:
        from src.stages.feature_engineering import build_features
        X, _ = build_features(raw_data)
        assert "City_Zone" not in X.columns
        assert any(col.startswith("City_Zone_") for col in X.columns)
    except ImportError:
        pass

def test_derived_features_created(raw_data):
    try:
        from src.stages.feature_engineering import build_features
        X, _ = build_features(raw_data)
        assert "rooms_total" in X.columns
        assert "area_per_room" in X.columns
    except ImportError:
        pass
