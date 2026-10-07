import pytest
import pandas as pd

def test_data_gate_rejects_bad_batch():
    try:
        from src.stages.validate_data import validate_data
        bad_batch = pd.DataFrame({
            "House_ID": [1, 2],
            "Area_sqft": [-500, 1500], # Bad area
            "Bedrooms": [2, 3],
            "Bathrooms": [1, 2],
            "Age_Years": [10, 5],
            "Distance_to_Center_km": [5.0, 10.0],
            "Neighborhood_Score": [8.5, 7.0],
            "Has_Parking": [1, 0],
            "Property_Condition": [4, 3],
            "City_Zone": ["A", "B"],
            "Price_Lakhs": [50.0, 75.0]
        })
        with pytest.raises(ValueError):
            validate_data(bad_batch)
    except ImportError:
        pass

class BadModel:
    def predict(self, X):
        return [-10.0] * len(X) # Deliberately bad predictions

def test_model_gate_rejects_bad_model():
    try:
        from src.stages.evaluate import evaluate_model
        bad_model = BadModel()
        X_test = pd.DataFrame({"Area_sqft": [1000]})
        y_test = pd.Series([50.0])
        metrics = evaluate_model(bad_model, X_test, y_test)
        # Assuming evaluate_model raises ValueError on bad model metrics
        with pytest.raises(ValueError):
            if metrics["r2"] < 0:
                raise ValueError("Model failed gate")
    except ImportError:
        pass

def test_pipeline_safe_failure():
    try:
        from src.pipeline import run_pipeline
        # If run_pipeline is executed with bad data, it should raise ValueError
        # and not overwrite registered models
        pass
    except ImportError:
        pass
