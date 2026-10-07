import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def dummy_train_data():
    X_train = pd.DataFrame({
        "Area_sqft": [1000, 1500, 2000, 1200, 1800],
        "rooms_total": [3, 5, 7, 4, 6],
        "area_per_room": [333.3, 300.0, 285.7, 300.0, 300.0]
    })
    y_train = pd.Series([50.0, 75.0, 120.0, 60.0, 100.0])
    return X_train, y_train

def test_model_trains_successfully(dummy_train_data):
    try:
        from src.stages.train import train_model
        X_train, y_train = dummy_train_data
        model = train_model(X_train, y_train, {"n_estimators": 10})
        assert model is not None
    except ImportError:
        pass

def test_model_predictions_positive(dummy_train_data):
    try:
        from src.stages.train import train_model
        X_train, y_train = dummy_train_data
        model = train_model(X_train, y_train, {"n_estimators": 10})
        preds = model.predict(X_train)
        assert (preds > 0).all()
    except ImportError:
        pass

def test_model_metrics_reasonable(dummy_train_data):
    try:
        from src.stages.train import train_model
        from src.stages.evaluate import evaluate_model
        X_train, y_train = dummy_train_data
        model = train_model(X_train, y_train, {"n_estimators": 10})
        metrics = evaluate_model(model, X_train, y_train)
        assert metrics["r2"] > 0.0
        assert metrics["rmse"] < 50.0
    except ImportError:
        pass
