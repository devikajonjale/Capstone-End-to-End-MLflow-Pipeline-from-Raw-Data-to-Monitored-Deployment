import os
import joblib
import pandas as pd
import mlflow
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from prometheus_client import Counter, Histogram, make_asgi_app

from src.config_loader import load_config

app = FastAPI(title="Real Estate Price Prediction API")

# Prometheus Metrics
REQUEST_COUNT = Counter('prediction_requests_total', 'Total number of prediction requests')
LATENCY = Histogram('prediction_latency_seconds', 'Latency of prediction requests')
PREDICTION_VALUE = Histogram('prediction_value', 'Predicted house prices')

# Add prometheus asgi middleware
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Globals
model = None
preprocessor = None
config = None

class HouseFeatures(BaseModel):
    features: Dict[str, Any]

@app.on_event("startup")
def load_assets():
    global model, preprocessor, config
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.yaml')
    if os.path.exists(config_path):
        config = load_config(config_path)
    else:
        config = load_config('config/config.yaml')
    
    # Load Preprocessor
    preprocessor_path = os.path.join('artifacts', 'features', 'preprocessor.pkl')
    if os.path.exists(preprocessor_path):
        preprocessor = joblib.load(preprocessor_path)
    else:
        print(f"Warning: Preprocessor not found at {preprocessor_path}")

    # Load Model
    model_name = config.get('mlflow', {}).get('model_name', 'HousePriceModel') if config else 'HousePriceModel'
    try:
        model_uri = f"models:/{model_name}/Production"
        model = mlflow.sklearn.load_model(model_uri)
    except Exception as e:
        print(f"Failed to load model from MLflow: {e}. Trying local fallback.")
        local_model_path = os.path.join('artifacts', 'models', 'model.pkl')
        if os.path.exists(local_model_path):
            model = joblib.load(local_model_path)
        else:
            print("Failed to load local model as well.")

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model is not None, "preprocessor_loaded": preprocessor is not None}

@app.post("/predict")
@LATENCY.time()
def predict(data: HouseFeatures):
    REQUEST_COUNT.inc()
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    
    try:
        df = pd.DataFrame([data.features])
        
        if preprocessor is not None:
            processed_data = preprocessor.transform(df)
        else:
            processed_data = df

        prediction = model.predict(processed_data)[0]
        PREDICTION_VALUE.observe(prediction)
        
        return {"prediction": float(prediction)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
