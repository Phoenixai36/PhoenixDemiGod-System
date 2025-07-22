"""
Configuration loader for metrics collectors.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .models import CollectorConfig


class ConfigLoader:
    """Loads and manages configuration for metrics collectors."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default config path
        if config_path is None:
            # Look for config in several locations
            possible_paths = [
                "config/resource_collectors.yaml",
                "config/resource_collectors.yml",
                "/etc/phoenix/resource_collectors.yaml",
                os.path.expanduser("~/.phoenix/resource_collectors.yaml")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
        
        self.config_path = config_path
        self.config_data = {}
        
        if self.config_path and os.path.exists(self.config_path):
            self.load_config()
        else:
            self.logger.warning(f"Config file not found at {config_path}, using defaults")
            self.config_data = self._get_default_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                self.config_data = yaml.safe_load(file)
            self.logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {str(e)}")
            self.config_data = self._get_default_config()
    
    def get_collector_config(self, collector_name: str) -> CollectorConfig:
        """
        Get configuration for a specific collector.
        
        Args:
            collector_name: Name of the collector
            
        Returns:
            CollectorConfig instance
        """
        collectors_config = self.config_data.get('collectors', {})
        collector_data = collectors_config.get(collector_name, {})
        
        # Get global defaults
        global_config = self.config_data.get('global', {})
        
        # Merge collector-specific config with global defaults
        config = CollectorConfig(
            name=collector_name,
            enabled=collector_data.get('enabled', True),
            collection_interval=collector_data.get(
                'collection_interval', 
                global_config.get('default_collection_interval', 30)
            ),
            timeout=collector_data.get(
                'timeout',
                global_config.get('default_timeout', 10)
            ),
            retry_attempts=collector_data.get(
                'retry_attempts',
                global_config.get('default_retry_attempts', 3)
            ),
            retry_delay=collector_data.get(
                'retry_delay',
                global_config.get('default_retry_delay', 5)
            ),
            custom_labels=collector_data.get('custom_labels', {}),
            parameters=collector_data.get('parameters', {})
        )
        
        return config
    
    def get_all_collector_configs(self) -> Dict[str, CollectorConfig]:
        """
        Get configurations for all defined collectors.
        
        Returns:
            Dictionary mapping collector names to CollectorConfig instances
        """
        collectors_config = self.config_data.get('collectors', {})
        configs = {}
        
        for collector_name in collectors_config.keys():
            configs[collector_name] = self.get_collector_config(collector_name)
        
        return configs
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration settings."""
        return self.config_data.get('global', {})
    
    def get_runtime_config(self) -> Dict[str, Any]:
        """Get container runtime configuration."""
        return self.config_data.get('runtime', {})
    
    def get_prometheus_config(self) -> Dict[str, Any]:
        """Get Prometheus integration configuration."""
        return self.config_data.get('prometheus', {})
    
    def get_thresholds_config(self) -> Dict[str, Any]:
        """Get alerting thresholds configuration."""
        return self.config_data.get('thresholds', {})
    
    def is_development_mode(self) -> bool:
        """Check if development mode is enabled."""
        dev_config = self.config_data.get('development', {})
        return dev_config.get('enabled', False)
    
    def get_development_config(self) -> Dict[str, Any]:
        """Get development configuration."""
        return self.config_data.get('development', {})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when no config file is found."""
        return {
            'collectors': {
                'cpu_collector': {
                    'enabled': True,
                    'type': 'cpu',
                    'collection_interval': 30,
                    'timeout': 10,
                    'custom_labels': {'priority': 'high', 'category': 'resource'}
                },
                'memory_collector': {
                    'enabled': True,
                    'type': 'memory',
                    'collection_interval': 30,
                    'timeout': 10,
                    'custom_labels': {'priority': 'high', 'category': 'resource'}
                },
                'network_collector': {
                    'enabled': True,
                    'type': 'network',
                    'collection_interval': 60,
                    'timeout': 15,
                    'custom_labels': {'priority': 'medium', 'category': 'resource'}
                },
                'disk_collector': {
                    'enabled': True,
                    'type': 'disk',
                    'collection_interval': 60,
                    'timeout': 15,
                    'custom_labels': {'priority': 'medium', 'category': 'resource'}
                }
            },
            'global': {
                'default_collection_interval': 30,
                'default_timeout': 10,
                'default_retry_attempts': 3,
                'default_retry_delay': 5,
                'log_level': 'INFO'
            },
            'runtime': {
                'preferred': 'auto'
            },
            'prometheus': {
                'enabled': True,
                'port': 8080,
                'path': '/metrics'
            }
        }
    
    def validate_config(self) -> bool:
        """
        Validate the loaded configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check required sections
            required_sections = ['collectors', 'global']
            for section in required_sections:
                if section not in self.config_data:
                    self.logger.error(f"Missing required config section: {section}")
                    return False
            
            # Validate collector configurations
            collectors = self.config_data.get('collectors', {})
            for name, config in collectors.items():
                if not isinstance(config, dict):
                    self.logger.error(f"Invalid collector config for {name}: must be a dictionary")
                    return False
                
                # Check required fields
                if 'type' not in config:
                    self.logger.error(f"Missing 'type' field in collector config for {name}")
                    return False
                
                # Validate numeric fields
                numeric_fields = ['collection_interval', 'timeout', 'retry_attempts', 'retry_delay']
                for field in numeric_fields:
                    if field in config and not isinstance(config[field], (int, float)):
                        self.logger.error(f"Invalid {field} in collector {name}: must be numeric")
                        return False
            
            # Validate global config
            global_config = self.config_data.get('global', {})
            numeric_global_fields = [
                'default_collection_interval', 'default_timeout', 
                'default_retry_attempts', 'default_retry_delay'
            ]
            for field in numeric_global_fields:
                if field in global_config and not isinstance(global_config[field], (int, float)):
                    self.logger.error(f"Invalid {field} in global config: must be numeric")
                    return False
            
            self.logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self.load_config()
            return self.validate_config()
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {str(e)}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_path: Optional path to save to, uses current path if None
            
        Returns:
            True if save successful, False otherwise
        """
        save_path = config_path or self.config_path
        if not save_path:
            self.logger.error("No config path specified for saving")
            return False
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as file:
                yaml.dump(self.config_data, file, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False


# Global config loader instance
_config_loader = None


def get_config_loader(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Get the global configuration loader instance.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None or config_path is not None:
        _config_loader = ConfigLoader(config_path)
    
    return _config_loader


def load_collector_configs() -> Dict[str, CollectorConfig]:
    """
    Load all collector configurations using the global config loader.
    
    Returns:
        Dictionary mapping collector names to CollectorConfig instances
    """
    loader = get_config_loader()
    return loader.get_all_collector_configs()