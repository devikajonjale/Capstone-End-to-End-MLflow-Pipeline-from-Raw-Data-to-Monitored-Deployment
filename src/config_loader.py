"""Load and validate the single YAML configuration.

The whole pipeline reads its settings from one file so that a run can be
reproduced from the config alone. Validation happens on load so a broken
config fails fast instead of halfway through training.
"""
import os
import yaml


class ConfigValidationError(ValueError):
    """Raised when the configuration is missing keys or holds bad values."""
    pass


REQUIRED_SECTIONS = [
    "project", "data", "feature_engineering", "model",
    "data_gate", "model_gate", "monitoring", "mlflow", "registry", "serving",
]


def validate_config(config: dict) -> None:
    """Check that the required sections and a few critical values are sane."""
    if not isinstance(config, dict):
        raise ConfigValidationError("Configuration must be a mapping")

    for section in REQUIRED_SECTIONS:
        if section not in config:
            raise ConfigValidationError(f"Missing required section: {section}")

    gate = config["data_gate"]
    pct = gate.get("max_missing_pct")
    if pct is None or not (0 <= pct <= 1):
        raise ConfigValidationError(
            f"data_gate.max_missing_pct must be between 0 and 1, got {pct}"
        )
    if "value_ranges" not in gate:
        raise ConfigValidationError("data_gate.value_ranges is required")

    mg = config["model_gate"]
    if mg.get("min_r2") is None or not (0 <= mg["min_r2"] <= 1):
        raise ConfigValidationError("model_gate.min_r2 must be between 0 and 1")
    for key in ("max_rmse", "max_mae"):
        if mg.get(key) is None or mg[key] <= 0:
            raise ConfigValidationError(f"model_gate.{key} must be positive")

    mon = config["monitoring"]
    if mon.get("psi_alert") is None or mon["psi_alert"] <= 0:
        raise ConfigValidationError("monitoring.psi_alert must be positive")


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Read the YAML file, validate it and return it as a dictionary."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    validate_config(config)
    return config


# Kept for backward compatibility with earlier imports.
load_and_validate_config = load_config
