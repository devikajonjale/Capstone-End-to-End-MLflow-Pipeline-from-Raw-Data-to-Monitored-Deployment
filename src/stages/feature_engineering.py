import os
import logging
import pickle
import pandas as pd
import numpy as np
from prefect import task
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.config_loader import load_config

logger = logging.getLogger(__name__)

@task
def build_features(df, config_path='config/config.yaml'):
    """Feature engineering, imputation, derived features, and encoding."""
    config = load_config(config_path)
    logger.info("Starting feature engineering...")
    
    df_processed = df.copy()
    
    # Separate target
    target_col = config.get('feature_engineering', {}).get('target_column', 'Price_Lakhs')
    y = None
    if target_col in df_processed.columns:
        y = df_processed[target_col]
        df_processed = df_processed.drop(columns=[target_col])
        
    # Drop House_ID, Batch
    cols_to_drop = ['House_ID', 'Batch']
    df_processed = df_processed.drop(columns=[c for c in cols_to_drop if c in df_processed.columns])
    
    # Derived features
    # rooms_total = Bedrooms + Bathrooms
    if 'Bedrooms' in df_processed.columns and 'Bathrooms' in df_processed.columns:
        df_processed['rooms_total'] = df_processed['Bedrooms'] + df_processed['Bathrooms']
        
    # area_per_room = Area_sqft / rooms_total
    if 'Area_sqft' in df_processed.columns and 'rooms_total' in df_processed.columns:
        df_processed['area_per_room'] = df_processed['Area_sqft'] / df_processed['rooms_total'].replace(0, np.nan)
        
    # Setup scikit-learn preprocessing pipeline
    numeric_features = df_processed.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = df_processed.select_dtypes(include=['object', 'category']).columns.tolist()
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # Fit and transform
    X = preprocessor.fit_transform(df_processed)
    
    # Get feature names if possible
    try:
        cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
        cat_features = cat_encoder.get_feature_names_out(categorical_features)
        all_features = numeric_features + list(cat_features)
        X = pd.DataFrame(X, columns=all_features)
    except Exception as e:
        logger.warning(f"Could not extract feature names: {e}. Returning numpy array.")
        
    # Save preprocessor
    artifacts_dir = "artifacts/features"
    os.makedirs(artifacts_dir, exist_ok=True)
    prep_path = os.path.join(artifacts_dir, "preprocessor.pkl")
    with open(prep_path, 'wb') as f:
        pickle.dump(preprocessor, f)
    logger.info(f"Saved feature preprocessor to {prep_path}")
    
    if y is not None:
        return X, y
    return X
