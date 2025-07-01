import configparser
from pathlib import Path


class ConfigError(Exception):
    """Custom exception for configuration validation errors."""
    pass

# Default config filename
DEFAULT_CONFIG_NAME = "changeme.txt"


def load_config(path: Path) -> configparser.ConfigParser:
    """
    Load and validate the configuration file.

    Args:
        path: Path to the INI-format config file.

    Returns:
        A validated ConfigParser instance.

    Raises:
        ConfigError: If the file is missing or invalid.
    """
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    cfg = configparser.ConfigParser()
    # preserve case of keys
    cfg.optionxform = str
    with path.open(encoding="utf-8", errors="ignore") as f:
        cfg.read_file(f)

    validate_config(cfg)
    return cfg


def load_default_config() -> configparser.ConfigParser:
    """
    Load and validate the default config file 'changeme.txt' located
    in the same directory as this module or the current working directory.

    Returns:
        A validated ConfigParser instance.

    Raises:
        ConfigError: If the file is missing or invalid.
    """
    # look alongside this file first
    base_dir = Path(__file__).resolve().parent
    default_path = base_dir / DEFAULT_CONFIG_NAME
    if not default_path.exists():
        # fallback to cwd
        default_path = Path.cwd() / DEFAULT_CONFIG_NAME
    return load_config(default_path)


def validate_config(cfg: configparser.ConfigParser) -> None:
    """
    Ensure that all required sections and keys are present in the config.
    'Cell' under USER is optional and may be empty.

    Raises:
        ConfigError: If any required section or key is missing or empty.
    """
    required = {
        'USER': ['Name', 'Email', 'Title'],  # Cell is optional
        'PATHS': ['ResultsDir', 'DownloadFolder'],
        'COLORS': ['CONDUIT', 'AERIAL', 'UNDERGROUND', 'BRIDGE', 'WORK_AREA'],
        'WEIGHTS': ['CONDUIT', 'FIBER', 'WORK_AREA'],
        'LEGEND': [],
        'SHAPEFILES': [],
    }

    errors = []
    for section, keys in required.items():
        if section not in cfg:
            errors.append(f"Missing required section: '{section}'")
        else:
            for key in keys:
                val = cfg[section].get(key, '').strip()
                if not val:
                    errors.append(f"Missing or empty required key '{key}' in section '{section}'")

    if errors:
        msg = "Invalid configuration:\n" + "\n".join(errors)
        raise ConfigError(msg)

# Example usage:
# from pathlib import Path
# cfg = load_default_config()  # loads 'changeme.txt'
