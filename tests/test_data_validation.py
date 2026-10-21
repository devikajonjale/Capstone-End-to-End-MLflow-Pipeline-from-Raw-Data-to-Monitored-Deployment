import numpy as np
import pytest

from src.stages.validate_data import DataValidationError, validate_data


def test_valid_data_passes(sample_df, config):
    assert validate_data(sample_df, config) is True


def test_missing_column_fails(sample_df, config):
    bad = sample_df.drop(columns=["Area_sqft"])
    with pytest.raises(DataValidationError):
        validate_data(bad, config)


def test_excess_missing_values_fails(sample_df, config):
    bad = sample_df.copy()
    bad.loc[bad.index[:30], "Age_Years"] = np.nan  # 25 percent, over the 10 percent gate
    with pytest.raises(DataValidationError):
        validate_data(bad, config)


def test_out_of_range_fails(sample_df, config):
    bad = sample_df.copy()
    bad.loc[bad.index[0], "Area_sqft"] = -100
    with pytest.raises(DataValidationError):
        validate_data(bad, config)
