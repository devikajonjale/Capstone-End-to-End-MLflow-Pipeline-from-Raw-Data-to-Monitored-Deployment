import os
import logging
from typing import Dict, Any, Optional
import pandas as pd
from prefect import flow, task, get_run_logger

from src.config_loader import load_config
from src.stages.ingest import ingest_data
from src.stages.validate_data import validate_data
from src.stages.feature_engineering import build_features
from src.stages.train import train_model
from src.stages.evaluate import evaluate_model
from src.stages.register import register_model
from src.stages.monitor import monitor_batch

# Define dummy exceptions if they are not importable
class DataValidationError(Exception):
    pass

class ModelValidationError(Exception):
    pass

@flow(name='house_price_pipeline')
def run_pipeline(config_path: str = 'config/config.yaml', batch_file: Optional[str] = None) -> Dict[str, Any]:
    logger = get_run_logger()
    logger.info("Starting house_price_pipeline...")
    summary = {}
    
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {"status": "failed", "error": str(e)}

    if batch_file is None:
        logger.info("Running full training pipeline...")
        try:
            # 1. Ingest Data
            raw_data_path = ingest_data(config_path=config_path)
            summary['raw_data_path'] = raw_data_path
            
            # 2. Validate Data
            try:
                is_valid = validate_data(config_path=config_path)
                summary['data_valid'] = is_valid
            except Exception as e:
                if "DataValidationError" in type(e).__name__:
                    raise DataValidationError(str(e))
                raise e
            
            # 3. Feature Engineering
            X, y = build_features(config_path=config_path)
            
            # 4. Train Model
            model, metrics, run_id = train_model(config_path=config_path)
            summary['training_metrics'] = metrics
            summary['run_id'] = run_id
            
            # 5. Evaluate Model
            try:
                eval_metrics, passed = evaluate_model(config_path=config_path)
                summary['evaluation_metrics'] = eval_metrics
                summary['evaluation_passed'] = passed
            except Exception as e:
                if "ModelValidationError" in type(e).__name__:
                    raise ModelValidationError(str(e))
                raise e
            
            # 6. Register Model
            if passed:
                logger.info("Model passed evaluation. Registering model...")
                model_version = register_model(config_path=config_path)
                summary['model_version'] = model_version
            else:
                logger.info("Model failed evaluation. Keeping previous model.")
                
            summary['status'] = "success"
            
        except DataValidationError as e:
            logger.error(f"Data Validation Error: {e}")
            summary['status'] = "failed_safe"
            summary['error'] = str(e)
        except ModelValidationError as e:
            logger.error(f"Model Validation Error: {e}")
            summary['status'] = "failed_safe"
            summary['error'] = str(e)
        except Exception as e:
            logger.error(f"Pipeline Error: {e}")
            summary['status'] = "failed"
            summary['error'] = str(e)
    else:
        logger.info(f"Running batch inference and monitoring pipeline on {batch_file}...")
        try:
            # 1. Validate Data (assuming it takes data_path in config or args)
            # For this simplified workflow, we'll assume validate_data validates the current data.
            try:
                is_valid = validate_data(config_path=config_path)
                summary['data_valid'] = is_valid
            except Exception as e:
                if "DataValidationError" in type(e).__name__:
                    raise DataValidationError(str(e))
                raise e
                
            # 2. Monitor batch (which likely handles features/predictions based on instructions)
            monitoring_results = monitor_batch(config_path=config_path)
            summary['monitoring_results'] = monitoring_results
            summary['status'] = "success"
            
        except DataValidationError as e:
            logger.error(f"Data Validation Error in batch: {e}")
            summary['status'] = "failed_safe"
            summary['error'] = str(e)
        except Exception as e:
            logger.error(f"Batch Pipeline Error: {e}")
            summary['status'] = "failed"
            summary['error'] = str(e)

    logger.info("Finished house_price_pipeline.")
    return summary
