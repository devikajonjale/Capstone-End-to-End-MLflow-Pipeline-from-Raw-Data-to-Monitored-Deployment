"""Stage 1: ingest.

Reads the raw training CSV named in the config, records basic statistics
and writes a copy into the processed directory so later stages and the DVC
cache have a stable input to work from.
"""
import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)


def ingest_data(config: dict) -> pd.DataFrame:
    path = config["data"]["raw_train_path"]
    logger.info("Ingesting training data from %s", path)
    df = pd.read_csv(path)
    logger.info("Loaded %d rows and %d columns", df.shape[0], df.shape[1])

    processed_dir = config["data"]["processed_dir"]
    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, "train_ingested.csv")
    df.to_csv(out_path, index=False)
    logger.info("Wrote ingested copy to %s", out_path)
    return df
