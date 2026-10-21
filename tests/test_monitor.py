import numpy as np
import pandas as pd

from src.stages.monitor import monitor_batch, population_stability_index


def test_psi_zero_for_identical():
    s = pd.Series(np.arange(1000, dtype=float))
    assert population_stability_index(s, s.copy(), bins=10) < 0.01


def test_psi_high_for_shifted():
    rng = np.random.default_rng(0)
    base = pd.Series(rng.normal(1000, 100, 1000))
    shifted = pd.Series(rng.normal(1500, 100, 1000))
    assert population_stability_index(base, shifted, bins=10) > 0.2


def test_monitor_flags_drift(sample_df, config):
    drifted = sample_df.copy()
    drifted["Area_sqft"] = drifted["Area_sqft"] * 0.4  # shrink area sharply
    result = monitor_batch(sample_df, drifted, config, model=None, batch_label="t")
    assert "Area_sqft" in result["psi"]
    assert result["data_drift_alert"] is True
