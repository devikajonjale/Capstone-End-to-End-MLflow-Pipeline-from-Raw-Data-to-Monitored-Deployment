"""Entry point for the training pipeline and single-batch runs.

Examples:
    python run_pipeline.py                     # full training and promotion
    python run_pipeline.py --batch-number 3    # run one incoming batch
    python run_pipeline.py --batch-file path.csv
"""
import argparse
import json

import pandas as pd

from src.config_loader import load_config
from src.pipeline import monitoring_flow, training_flow


def main() -> None:
    parser = argparse.ArgumentParser(description="House price MLOps pipeline")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--batch-file", default=None)
    parser.add_argument("--batch-number", type=int, default=None, choices=[1, 2, 3])
    args = parser.parse_args()

    if args.batch_number is not None:
        config = load_config(args.config)
        incoming = pd.read_csv(config["data"]["incoming_batches_path"])
        batch_df = incoming[incoming["Batch"] == args.batch_number].copy()
        result = monitoring_flow(batch_df, args.config, batch_label=f"batch_{args.batch_number}")
    elif args.batch_file is not None:
        batch_df = pd.read_csv(args.batch_file)
        result = monitoring_flow(batch_df, args.config, batch_label=args.batch_file)
    else:
        result = training_flow(args.config)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
