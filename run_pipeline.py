import argparse
import sys
import os

from src.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Run House Price Pipeline")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--batch-file", default=None, help="Path to a specific batch file for inference")
    parser.add_argument("--batch-number", type=int, default=None, help="Run a specific batch number (1, 2, or 3) sequentially if multiple")
    
    args = parser.parse_args()
    
    if args.batch_number is not None:
        batch_file = f"data/incoming/batch_{args.batch_number}.csv"
        print(f"Running pipeline for batch {args.batch_number} at {batch_file}...")
        summary = run_pipeline(config_path=args.config, batch_file=batch_file)
        print(f"Summary for batch {args.batch_number}: {summary}")
    elif args.batch_file is not None:
        print(f"Running pipeline for batch file {args.batch_file}...")
        summary = run_pipeline(config_path=args.config, batch_file=args.batch_file)
        print(f"Summary for batch {args.batch_file}: {summary}")
    else:
        print("Running full training pipeline...")
        summary = run_pipeline(config_path=args.config)
        print(f"Summary for full training: {summary}")

if __name__ == "__main__":
    main()
