"""Tests for the multi-algorithm training stage.

These tests use a tiny subset of the sample data to run quickly while still
exercising the real cross-validation and champion selection code paths.
"""
import copy

import pytest

from src.stages.feature_engineering import build_features
from src.stages.train import ESTIMATORS, build_estimator, train_model


def test_all_candidates_are_registered(config):
    for cand in config["model"]["candidates"]:
        assert cand["name"] in ESTIMATORS, (
            f"candidate {cand['name']} has no estimator class registered"
        )


def test_build_estimator_for_each_candidate(sample_df, config):
    X, y = build_features(sample_df, config)
    for cand in config["model"]["candidates"]:
        pipe = build_estimator(config, candidate=cand["name"])
        pipe.fit(X, y)
        preds = pipe.predict(X)
        assert len(preds) == len(y)


def test_train_model_picks_a_champion_and_logs_comparison(sample_df, config, tmp_path):
    cfg = copy.deepcopy(config)
    cfg["mlflow"]["tracking_uri"] = f"sqlite:///{tmp_path / 'mlflow.db'}"
    cfg["mlflow"]["experiment_name"] = "test_multi_algo"
    cfg["model"]["cv"]["n_splits"] = 3  # keep fast
    X, y = build_features(sample_df, cfg)
    champion_pipe, metrics, run_id = train_model(X, y, cfg)
    assert champion_pipe is not None
    assert run_id
    assert "champion_algorithm" in metrics
    assert metrics["champion_algorithm"] in {c["name"] for c in cfg["model"]["candidates"]}
