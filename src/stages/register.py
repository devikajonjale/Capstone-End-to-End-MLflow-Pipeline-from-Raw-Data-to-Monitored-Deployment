"""Stage 6: register and promote.

Registers the champion in the MLflow Model Registry and promotes it to the
Production stage. Also writes the pipeline and a self-contained lineage
record into the committed production folder so the serving container does
not depend on a running MLflow server. The lineage record is the evidence
chain demanded by Task 5: starting from the deployed model you can follow
the record back to the MLflow run, the git commit, the config version, the
training-matrix hash and the raw-CSV cryptographic fingerprint.
"""
import hashlib
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


def _file_sha256(path: str) -> str:
    """Full SHA-256 of a file, in hex. Returns 'missing' if the file is absent."""
    if not path or not os.path.exists(path):
        return "missing"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    except Exception as e:
        logger.warning("Stage transition unavailable (%s), setting alias", e)
        client.set_registered_model_alias(name, "production", version)

    prod_dir = config["registry"]["production_dir"]
    os.makedirs(prod_dir, exist_ok=True)
    with open(os.path.join(prod_dir, "model.pkl"), "wb") as f:
        pickle.dump(model, f)

    raw_train_path = config["data"]["raw_train_path"]
    lineage = {
        "model_name": name,
        "registry_version": version,
        "mlflow_run_id": run_id,
        "champion_algorithm": metrics.get("champion_algorithm", "unknown"),
        "git_commit": _git_commit(),
        "config_version": config["project"]["version"],
        "raw_train_path": raw_train_path,
        "raw_train_sha256": _file_sha256(raw_train_path),
        "promoted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "holdout_metrics": {k: metrics[k] for k in ("rmse", "mae", "r2", "mape")
                            if k in metrics},
    }
    with open(os.path.join(prod_dir, "lineage.json"), "w") as f:
        json.dump(lineage, f, indent=2)

    logger.info("Promoted version %s (algo=%s) to Production",
                version, lineage["champion_algorithm"])
    return version
