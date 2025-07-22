"""
Configuration management for the Agent Hooks Enhancement system.

This module provides functionality for loading, validating, and managing
hook configurations and system settings.
"""

import json
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, cast

from pydantic import BaseModel, Field, validator
from enum import Enum

from src.agent_hooks.core.models import HookPriority, HookTrigger


class HookConfigurationError(Exception):
    """Exception raised for errors in hook configuration."""
    pass


class NotificationChannel(str, Enum):
    """Available notification channels."""
    IDE = "ide"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    TEAMS = "teams"


class ResourceLimits(BaseModel):
    """Resource limits for hook execution."""
    cpu_limit: Optional[float] = Field(None, description="CPU limit in cores")
    memory_limit: Optional[int] = Field(None, description="Memory limit in MB")
    execution_time_limit: Optional[int] = Field(None, description="Execution time limit in seconds")
    disk_io_limit: Optional[int] = Field(None, description="Disk IO limit in MB/s")
    network_io_limit: Optional[int] = Field(None, description="Network IO limit in MB/s")


class HookConfiguration(BaseModel):
    """Configuration for a single hook."""
    name: str = Field(..., description="Hook name")
    description: str = Field(..., description="Hook description")
    enabled: bool = Field(default=True)
    priority: HookPriority = Field(default=HookPriority.MEDIUM)
    triggers: List[HookTrigger] = Field(default_factory=list)
    
    # Execution settings
    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    
    # Trigger conditions
    file_patterns: List[str] = Field(default_factory=list)
    metric_thresholds: Dict[str, float] = Field(default_factory=dict)
    schedule: Optional[str] = Field(None, description="Cron expression for time-based triggers")
    
    # Dependencies and requirements
    required_tools: List[str] = Field(default_factory=list)
    required_services: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    
    # Notification settings
    notify_on_success: bool = Field(default=False)
    notify_on_failure: bool = Field(default=True)
    notification_channels: List[NotificationChannel] = Field(default_factory=list)
    
    @validator("schedule")
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        if v is not None:
            # Simple validation for cron expression format
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts")
        return v


class SystemSettings(BaseModel):
    """System-wide settings for the Agent Hooks Enhancement system."""
    enabled: bool = Field(default=True, description="Enable or disable the entire hook system")
    log_level: str = Field(default="INFO", description="Logging level")
    max_concurrent_hooks: int = Field(default=5, description="Maximum number of hooks to run concurrently")
    default_timeout_seconds: int = Field(default=30, description="Default timeout for hook execution")
    default_max_retries: int = Field(default=3, description="Default maximum number of retries")
    event_retention_days: int = Field(default=7, description="Number of days to retain event history")
    notification_settings: Dict[str, Any] = Field(default_factory=dict, description="Global notification settings")
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v


class ConfigManager:
    """
    Manager for loading and validating hook configurations and system settings.
    
    This class is responsible for loading configurations from files, validating them,
    and providing access to the loaded configurations.
    """
    def __init__(self, config_dir: Union[str, Path]):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.system_settings = SystemSettings()
        self.hook_configs: Dict[str, HookConfiguration] = {}
        
    def load_system_settings(self, filename: str = "system_settings.yaml") -> SystemSettings:
        """
        Load system settings from a YAML file.
        
        Args:
            filename: Name of the system settings file
            
        Returns:
            Loaded system settings
            
        Raises:
            FileNotFoundError: If the settings file does not exist
            HookConfigurationError: If the settings file is invalid
        """
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"System settings file not found: {file_path}")
        
        try:
            with open(file_path, "r") as f:
                if file_path.suffix.lower() == ".json":
                    settings_dict = json.load(f)
                else:
                    settings_dict = yaml.safe_load(f)
            
            self.system_settings = SystemSettings(**settings_dict)
            return self.system_settings
        
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise HookConfigurationError(f"Error parsing system settings file: {e}")
        except Exception as e:
            raise HookConfigurationError(f"Error loading system settings: {e}")
    
    def load_hook_configs(self, directory: str = "hooks") -> Dict[str, HookConfiguration]:
        """
        Load hook configurations from a directory.
        
        Args:
            directory: Directory containing hook configuration files
            
        Returns:
            Dictionary of hook configurations, keyed by hook name
        """
        hooks_dir = self.config_dir / directory
        
        if not hooks_dir.exists():
            os.makedirs(hooks_dir, exist_ok=True)
            return {}
        
        configs = {}
        
        for file_path in hooks_dir.glob("*.yaml"):
            try:
                with open(file_path, "r") as f:
                    config_dict = yaml.safe_load(f)
                
                config = HookConfiguration(**config_dict)
                configs[config.name] = config
            
            except Exception as e:
                print(f"Error loading hook configuration from {file_path}: {e}")
        
        for file_path in hooks_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    config_dict = json.load(f)
                
                config = HookConfiguration(**config_dict)
                configs[config.name] = config
            
            except Exception as e:
                print(f"Error loading hook configuration from {file_path}: {e}")
        
        self.hook_configs = configs
        return configs
    
    def save_hook_config(self, config: HookConfiguration, directory: str = "hooks") -> Path:
        """
        Save a hook configuration to a file.
        
        Args:
            config: Hook configuration to save
            directory: Directory to save the configuration in
            
        Returns:
            Path to the saved configuration file
        """
        hooks_dir = self.config_dir / directory
        os.makedirs(hooks_dir, exist_ok=True)
        
        file_path = hooks_dir / f"{config.name}.yaml"
        
        with open(file_path, "w") as f:
            yaml.dump(config.dict(), f)
        
        return file_path
    
    def save_system_settings(self, settings: Optional[SystemSettings] = None, filename: str = "system_settings.yaml") -> Path:
        """
        Save system settings to a file.
        
        Args:
            settings: System settings to save, or None to save the current settings
            filename: Name of the system settings file
            
        Returns:
            Path to the saved settings file
        """
        if settings is None:
            settings = self.system_settings
        
        file_path = self.config_dir / filename
        
        with open(file_path, "w") as f:
            yaml.dump(settings.dict(), f)
        
        return file_path
    
    def get_hook_config(self, name: str) -> Optional[HookConfiguration]:
        """
        Get a hook configuration by name.
        
        Args:
            name: Name of the hook
            
        Returns:
            Hook configuration, or None if not found
        """
        return self.hook_configs.get(name)
    
    def get_system_settings(self) -> SystemSettings:
        """
        Get the current system settings.
        
        Returns:
            Current system settings
        """
        return self.system_settings
