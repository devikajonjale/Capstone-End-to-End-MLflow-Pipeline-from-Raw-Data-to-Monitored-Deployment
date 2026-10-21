"""Stage 6: register and promote.

Registers the run's model in the MLflow Model Registry and moves it to the
Production stage. It also writes the pipeline and a lineage record into the
committed production folder so the serving container does not need a running
MLflow server. The lineage record is what Task 5 is demonstrated from: given
the deployed model you can read back the run, data version, config and commit.
"""
import json
import logging
import os
import pickle
import subprocess
from datetime import datetime, timezone

import mlflow
from mlflow.tracking import MlflowClient

logger = logging.getLogger(__name__)


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def register_model(model, run_id: str, metrics: dict, config: dict) -> str:
    mlflow_cfg = config["mlflow"]
    name = mlflow_cfg["model_name"]
    mlflow.set_tracking_uri(mlflow_cfg["tracking_uri"])

    logger.info("Registering run %s as %s", run_id, name)
    result = mlflow.register_model(f"runs:/{run_id}/model", name)
    version = result.version

    client = MlflowClient()
    try:
        client.transition_model_version_stage(
            name=name, version=version, stage="Production",
            archive_existing_versions=True,
        )
    except Exception as e:  # newer MLflow prefers aliases; fall back to one
        logger.warning("Stage transition unavailable (%s), setting alias", e)
        client.set_registered_model_alias(name, "production", version)

    # Write the self-contained production artifact and lineage record.
    prod_dir = config["registry"]["production_dir"]
    os.makedirs(prod_dir, exist_ok=True)
    with open(os.path.join(prod_dir, "model.pkl"), "wb") as f:
        pickle.dump(model, f)

    lineage = {
        "model_name": name,
        "registry_version": version,
        "mlflow_run_id": run_id,
        "git_commit": _git_commit(),
        "config_version": config["project"]["version"],
        "promoted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "holdout_metrics": {k: metrics[k] for k in ("rmse", "mae", "r2") if k in metrics},
    }
    with open(os.path.join(prod_dir, "lineage.json"), "w") as f:
        json.dump(lineage, f, indent=2)

    logger.info("Promoted version %s to Production", version)
    return version
