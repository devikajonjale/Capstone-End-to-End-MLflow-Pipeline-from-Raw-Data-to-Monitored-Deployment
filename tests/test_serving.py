"""Tests for the FastAPI serving layer, including confidence intervals."""
from fastapi.testclient import TestClient


def _valid_payload():
    return {
        "Area_sqft": 1200,
        "Bedrooms": 3,
        "Bathrooms": 2,
        "Age_Years": 10,
        "Distance_to_Center_km": 5.0,
        "Neighborhood_Score": 8.0,
        "Has_Parking": 1,
        "Property_Condition": "Good",
        "City_Zone": "North",
    }


def _client():
    from src.serving.app import app
    return TestClient(app)


def test_health_endpoint_includes_version():
    with _client() as c:
        r = c.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "model_version" in body


def test_predict_returns_confidence_interval():
    with _client() as c:
        r = c.post("/predict", json=_valid_payload())
        assert r.status_code == 200
        body = r.json()
        assert "predicted_price_lakhs" in body
        ci = body["confidence_interval_lakhs"]
        assert ci["lower"] < body["predicted_price_lakhs"] < ci["upper"]
        assert 0.9 <= ci["level"] <= 1.0


def test_predict_rejects_bad_payload():
    with _client() as c:
        r = c.post("/predict", json={"Area_sqft": "oops"})
        assert r.status_code == 422


def test_lineage_endpoint_exposes_core_fields():
    with _client() as c:
        r = c.get("/lineage")
        assert r.status_code == 200
        body = r.json()
        # The core lineage keys the brief wants demonstrable from a running
        # service.
        for key in ("registry_version", "mlflow_run_id", "git_commit",
                    "config_version", "holdout_metrics"):
            assert key in body, f"missing lineage key {key}"
