import os
import logging
import pandas as pd
from prefect import task
from src.config_loader import load_config

logger = logging.getLogger(__name__)

@task
def ingest_data(config_path='config/config.yaml'):
    """Load the training CSV, log stats, save a copy, and return the dataframe."""
    config = load_config(config_path)
    data_path = config.get('data', {}).get('train_path', 'datasets/project4_capstone/capstone_house_prices_train.csv')
    
    logger.info(f"Ingesting data from {data_path}")
    
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to read data from {data_path}: {e}")
        raise
        
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Data types:\n{df.dtypes}")
    logger.info(f"Missing values:\n{df.isnull().sum()}")
    
    # Save a copy to artifacts
    artifacts_dir = "artifacts/ingested"
    os.makedirs(artifacts_dir, exist_ok=True)
    save_path = os.path.join(artifacts_dir, "train.csv")
    df.to_csv(save_path, index=False)
    logger.info(f"Saved ingested data to {save_path}")
    
    return df
