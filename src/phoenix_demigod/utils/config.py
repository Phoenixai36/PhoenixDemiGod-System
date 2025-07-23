"""
Configuration management for the Phoenix DemiGod system.
"""

from typing import Any, Dict

import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        dict: Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class ConfigManager:
    """
    Configuration manager for the Phoenix DemiGod system.
    """

    def __init__(self, config_path: str):
        """
        Initialize the ConfigManager.

        Args:
            config_path: Path to the configuration file
        """
        self.config = load_config(config_path)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key is not found

        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
