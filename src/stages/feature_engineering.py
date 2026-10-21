"""Stage 3: build features.

Splits the frame into the model input X and target y. The heavy lifting
(imputation, scaling, encoding) is deferred to the scikit-learn Pipeline built
in the train stage, so X here still holds raw plus derived columns. This keeps
training and serving on the same footing.
"""
import logging
from typing import Tuple

import pandas as pd

from src.features import prepare_frame

logger = logging.getLogger(__name__)


def build_features(df: pd.DataFrame, config: dict) -> Tuple[pd.DataFrame, pd.Series]:
    target = config["feature_engineering"]["target"]
    logger.info("Building features, target column is %s", target)

    if target not in df.columns:
        raise KeyError(f"Target column {target} not present in data")

    y = df[target].astype(float)
    X = prepare_frame(df.drop(columns=[target]), config)
    logger.info("Feature matrix has %d rows and %d columns", X.shape[0], X.shape[1])
    return X, y
