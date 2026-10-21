import copy

import pandas as pd
import pytest

from src.stages.evaluate import evaluate_model
from src.stages.feature_engineering import build_features
from src.stages.train import build_estimator
from src.stages.validate_data import DataValidationError, validate_data


def test_data_gate_rejects_out_of_range_batch(sample_df, config):
    bad = sample_df.copy()
    bad.loc[bad.index[:5], "Area_sqft"] = -50
    with pytest.raises(DataValidationError):
        validate_data(bad, config)


def test_model_gate_passes_good_model(sample_df, config, tmp_path):
    cfg = copy.deepcopy(config)
    cfg["registry"]["production_dir"] = str(tmp_path)  # no incumbent model
    X, y = build_features(sample_df, cfg)
    est = build_estimator(cfg)
    est.fit(X, y)
    metrics, passed = evaluate_model(est, X, y, cfg)
    assert passed is True
    assert metrics["r2"] >= cfg["model_gate"]["min_r2"]


class ConstantModel:
    def predict(self, X):
        return pd.Series([0.0] * len(X)).values


def test_model_gate_rejects_bad_model(sample_df, config, tmp_path):
    cfg = copy.deepcopy(config)
    cfg["registry"]["production_dir"] = str(tmp_path)
    X, y = build_features(sample_df, cfg)
    metrics, passed = evaluate_model(ConstantModel(), X, y, cfg)
    assert passed is False
    assert metrics["reasons"]
