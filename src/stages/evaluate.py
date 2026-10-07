import logging
import mlflow
from prefect import task
from src.config_loader import load_config

logger = logging.getLogger(__name__)

class ModelValidationError(Exception):
    pass

@task
def evaluate_model(model, X_val, y_val, config_path='config/config.yaml'):
    """MODEL GATE: Compare metrics against thresholds."""
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    config = load_config(config_path)
    gate_config = config.get('model_gate', {})
    
    logger.info("Evaluating model against thresholds...")
    
    y_pred = model.predict(X_val)
    rmse = mean_squared_error(y_val, y_pred, squared=False)
    mae = mean_absolute_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred)
    
    metrics = {'rmse': rmse, 'mae': mae, 'r2': r2}
    
    thresholds = gate_config.get('thresholds', {'r2': 0.6, 'rmse': 50.0})
    
    if metrics['r2'] < thresholds.get('r2', 0):
        msg = f"Model validation failed: R2 score {metrics['r2']:.4f} is below threshold {thresholds['r2']}"
        logger.error(msg)
        raise ModelValidationError(msg)
        
    if metrics['rmse'] > thresholds.get('rmse', 999999):
        msg = f"Model validation failed: RMSE {metrics['rmse']:.4f} is above threshold {thresholds['rmse']}"
        logger.error(msg)
        raise ModelValidationError(msg)
        
    logger.info("Model passed evaluation gates.")
    return metrics, True
