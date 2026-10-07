import logging
import mlflow
from mlflow.tracking import MlflowClient
from prefect import task
from src.config_loader import load_config

logger = logging.getLogger(__name__)

@task
def register_model(run_id, config_path='config/config.yaml'):
    """Register model in MLflow Model Registry."""
    config = load_config(config_path)
    mlflow_config = config.get('mlflow', {})
    
    model_name = mlflow_config.get('model_name', 'capstone_rf_model')
    mlflow.set_tracking_uri(mlflow_config.get('tracking_uri', 'sqlite:///mlflow.db'))
    
    logger.info(f"Registering model from run {run_id} as {model_name}")
    
    result = mlflow.register_model(f"runs:/{run_id}/model", model_name)
    version = result.version
    
    client = MlflowClient()
    
    # Transition to Staging, then Production
    logger.info(f"Transitioning model {model_name} version {version} to Production")
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
        archive_existing_versions=True
    )
    
    return version
