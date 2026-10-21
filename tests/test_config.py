import pytest

from src.config_loader import ConfigValidationError, load_config, validate_config


def test_real_config_loads():
    config = load_config("config/config.yaml")
    for section in ("data", "feature_engineering", "model", "data_gate",
                    "model_gate", "monitoring", "mlflow", "registry", "serving"):
        assert section in config


def test_missing_section_rejected():
    with pytest.raises(ConfigValidationError):
        validate_config({"data": {}})


def test_bad_missing_pct_rejected():
    config = load_config("config/config.yaml")
    config["data_gate"]["max_missing_pct"] = 5.0  # must be a fraction
    with pytest.raises(ConfigValidationError):
        validate_config(config)


def test_paths_are_relative():
    config = load_config("config/config.yaml")
    train = config["data"]["raw_train_path"]
    assert not train.startswith("/") and not train[1:3] == ":\\"
