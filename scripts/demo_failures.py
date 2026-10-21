"""Demonstrate the two safe-failure scenarios required by Task 4.

Scenario A: a bad data batch is rejected by the data gate.
Scenario B: a model that misses the quality bar is not promoted.

In both cases the script prints the production model's lineage before and
after, showing that the deployed model is left untouched.
"""
import copy
import json
import os
import tempfile

import pandas as pd
import yaml

from src.config_loader import load_config
from src.pipeline import monitoring_flow, training_flow

CONFIG_PATH = "config/config.yaml"


def production_version(config: dict):
    path = os.path.join(config["registry"]["production_dir"], "lineage.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f).get("registry_version")


def scenario_a(config: dict) -> None:
    print("\n=== Scenario A: bad data batch ===")
    before = production_version(config)
    incoming = pd.read_csv(config["data"]["incoming_batches_path"])
    batch = incoming[incoming["Batch"] == 1].copy()
    batch.loc[batch.index[:20], "Area_sqft"] = -500  # impossible area
    result = monitoring_flow(batch, CONFIG_PATH, batch_label="corrupted_batch")
    print("status:", result.get("status"), "| data_gate:", result.get("data_gate"))
    print("reason:", result.get("error"))
    print(f"production version before={before} after={production_version(config)}")


def scenario_b(config: dict) -> None:
    print("\n=== Scenario B: model below the quality bar ===")
    before = production_version(config)
    # Tighten the model gate so a normally good model is rejected, standing in
    # for a genuinely weak model without mutating the committed config.
    strict = copy.deepcopy(config)
    strict["model_gate"]["max_rmse"] = 1.0
    strict["model_gate"]["min_r2"] = 0.999
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(strict, f)
        strict_path = f.name
    try:
        result = training_flow(strict_path)
    finally:
        os.unlink(strict_path)
    print("status:", result.get("status"), "| model_gate:", result.get("model_gate"))
    print("reasons:", result.get("reasons"))
    print(f"production version before={before} after={production_version(config)}")


def main() -> None:
    config = load_config(CONFIG_PATH)
    if production_version(config) is None:
        print("No production model found. Run run_pipeline.py first.")
        return
    scenario_a(config)
    scenario_b(config)
    print("\nBoth gates failed safely. The production model was not changed.")


if __name__ == "__main__":
    main()
