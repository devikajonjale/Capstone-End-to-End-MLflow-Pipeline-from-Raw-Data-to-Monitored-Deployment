import yaml
import os

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass

def load_and_validate_config(config_path: str) -> dict:
    """Loads and validates the YAML configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    validate_config(config)
    return config

def validate_config(config: dict):
    """Validates required keys and ranges in the configuration."""
    required_sections = [
        "data", "feature_engineering", "model", 
        "data_gate", "model_gate", "monitoring", 
        "mlflow", "serving"
    ]
    for section in required_sections:
        if section not in config:
            raise ConfigValidationError(f"Missing required section in config: {section}")
            
    # Validate specific values
    data_gate = config.get("data_gate", {})
    if "max_missing_pct" in data_gate:
        pct = data_gate["max_missing_pct"]
        if not (0 <= pct <= 1):
            raise ConfigValidationError(f"data_gate.max_missing_pct must be between 0 and 1, got {pct}")
            
    if "value_ranges" not in data_gate:
        raise ConfigValidationError("Missing value_ranges in data_gate configuration")
        
    print("Configuration successfully validated.")


def load_config(config_path: str = 'config/config.yaml') -> dict:
    """Convenient wrapper to load and validate configuration.

    Args:
        config_path: Path to the YAML configuration file.
    Returns:
        dict: Validated configuration dictionary.
    """
    return load_and_validate_config(config_path)
