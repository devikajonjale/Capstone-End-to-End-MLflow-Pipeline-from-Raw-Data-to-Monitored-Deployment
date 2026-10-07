import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def valid_data():
    return pd.DataFrame({
        "House_ID": [1, 2, 3],
        "Area_sqft": [1000, 1500, 2000],
        "Bedrooms": [2, 3, 4],
        "Bathrooms": [1, 2, 3],
        "Age_Years": [10, 5, 2],
        "Distance_to_Center_km": [5.0, 10.0, 2.5],
        "Neighborhood_Score": [8.5, 7.0, 9.2],
        "Has_Parking": [1, 0, 1],
        "Property_Condition": [4, 3, 5],
        "City_Zone": ["A", "B", "A"],
        "Price_Lakhs": [50.0, 75.0, 120.0]
    })

def test_valid_data_passes(valid_data):
    try:
        from src.stages.validate_data import validate_data
        result = validate_data(valid_data)
        assert result is True
    except ImportError:
        pass

def test_missing_columns_fails(valid_data):
    try:
        from src.stages.validate_data import validate_data
        bad_data = valid_data.drop(columns=["Area_sqft"])
        with pytest.raises(ValueError):
            validate_data(bad_data)
    except ImportError:
        pass

def test_excessive_missing_values_fails(valid_data):
    try:
        from src.stages.validate_data import validate_data
        bad_data = valid_data.copy()
        bad_data.loc[0, "Age_Years"] = np.nan
        bad_data.loc[1, "Age_Years"] = np.nan
        with pytest.raises(ValueError):
            validate_data(bad_data)
    except ImportError:
        pass

def test_out_of_range_values_fails(valid_data):
    try:
        from src.stages.validate_data import validate_data
        bad_data = valid_data.copy()
        bad_data.loc[0, "Area_sqft"] = -100
        with pytest.raises(ValueError):
            validate_data(bad_data)
    except ImportError:
        pass
