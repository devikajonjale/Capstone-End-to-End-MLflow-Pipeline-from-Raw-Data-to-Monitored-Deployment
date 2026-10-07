import logging
import pandas as pd
from prefect import task
from src.config_loader import load_config

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    pass

@task
def validate_data(df, config_path='config/config.yaml'):
    """DATA GATE: Check schema, value ranges, missing value percentages."""
    config = load_config(config_path)
    gate_config = config.get('data_gate', {})
    
    logger.info("Starting data validation...")
    
    required_cols = gate_config.get('required_columns', [
        'House_ID', 'Area_sqft', 'Bedrooms', 'Bathrooms', 'Age_Years',
        'Distance_to_Center_km', 'Neighborhood_Score', 'Has_Parking',
        'Property_Condition', 'City_Zone', 'Price_Lakhs'
    ])
    
    # Check schema
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Data validation failed: Missing required columns: {missing_cols}"
        logger.error(msg)
        raise DataValidationError(msg)
        
    # Check missing value percentages
    max_missing_pct = gate_config.get('max_missing_pct', 20.0)
    for col in df.columns:
        pct_missing = (df[col].isnull().sum() / len(df)) * 100
        if pct_missing > max_missing_pct:
            msg = f"Data validation failed: Column {col} has {pct_missing:.2f}% missing values (exceeds {max_missing_pct}%)"
            logger.error(msg)
            raise DataValidationError(msg)
            
    # Check value ranges if specified
    value_ranges = gate_config.get('value_ranges', {
        'Area_sqft': {'min': 100, 'max': 20000},
        'Price_Lakhs': {'min': 0}
    })
    
    for col, ranges in value_ranges.items():
        if col in df.columns:
            if 'min' in ranges and df[col].min() < ranges['min']:
                msg = f"Data validation failed: Column {col} has values below minimum {ranges['min']}"
                logger.error(msg)
                raise DataValidationError(msg)
            if 'max' in ranges and df[col].max() > ranges['max']:
                msg = f"Data validation failed: Column {col} has values above maximum {ranges['max']}"
                logger.error(msg)
                raise DataValidationError(msg)
                
    logger.info("Data validation passed successfully.")
    return df
