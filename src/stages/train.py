import os
import logging
import pickle
import mlflow
from prefect import task
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from src.config_loader import load_config

logger = logging.getLogger(__name__)

@task
def train_model(X, y, config_path='config/config.yaml'):
    """Train RandomForest, log to MLflow, and save model."""
    config = load_config(config_path)
    model_config = config.get('model', {})
    mlflow_config = config.get('mlflow', {})
    
    test_size = model_config.get('test_size', 0.2)
    random_state = model_config.get('random_state', 42)
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    params = model_config.get('params', {
        'n_estimators': 100,
        'max_depth': None,
        'min_samples_split': 2,
        'random_state': random_state
    })
    
    mlflow.set_tracking_uri(mlflow_config.get('tracking_uri', 'sqlite:///mlflow.db'))
    mlflow.set_experiment(mlflow_config.get('experiment_name', 'capstone_experiment'))
    
    with mlflow.start_run() as run:
        logger.info(f"Training RandomForestRegressor with params: {params}")
        model = RandomForestRegressor(**params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_val)
        rmse = mean_squared_error(y_val, y_pred, squared=False)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        metrics = {'rmse': rmse, 'mae': mae, 'r2': r2}
        logger.info(f"Validation metrics: {metrics}")
        
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model")
        
        artifacts_dir = "artifacts/models"
        os.makedirs(artifacts_dir, exist_ok=True)
        model_path = os.path.join(artifacts_dir, "model.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Saved model to {model_path}")
        
        return model, metrics, run.info.run_id
