"""
Configuration classes for the Agent Hooks system.

This module defines configuration structures for various components
of the Phoenix DemiGod Agent Hooks automation system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FileWatcherConfig:
    """Configuration for the file system watcher."""
    
    # Paths to watch for changes
    watch_paths: List[str] = field(default_factory=lambda: [
        ".",  # Current directory
        "src/",
        "config/",
        "scripts/",
        "infra/terraform/",
        "infra/windmill-scripts/",
        "docker/",
        "monitoring/",
    ])
    
    # File patterns to include (glob patterns)
    include_patterns: List[str] = field(default_factory=list)
    
    # File patterns to exclude (glob patterns)
    exclude_patterns: List[str] = field(default_factory=list)
    
    # Whether to watch subdirectories recursively
    recursive: bool = True
    
    # Debounce delay in seconds to avoid duplicate events
    debounce_delay: float = 0.5
    
    # Maximum number of events to queue
    max_queue_size: int = 1000
    
    # Enable content hash verification
    enable_hash_verification: bool = True


@dataclass
class ContainerMonitorConfig:
    """Configuration for container monitoring."""
    
    # Container runtime to use (podman, docker)
    runtime: str = "podman"
    
    # Containers to monitor (empty = all)
    container_names: List[str] = field(default_factory=list)
    
    # Container labels to filter by
    container_labels: Dict[str, str] = field(default_factory=dict)
    
    # Health check interval in seconds
    health_check_interval: float = 30.0
    
    # Resource monitoring interval in seconds
    resource_check_interval: float = 60.0
    
    # Log monitoring settings
    enable_log_monitoring: bool = True
    log_tail_lines: int = 100
    
    # Thresholds for alerts
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 90.0
    disk_threshold_percent: float = 85.0

@dataclass
class ContainerLogAnalysisConfig:
    """Configuration for container log analysis."""

    # Log levels to analyze
    log_levels: List[str] = field(default_factory=lambda: ["ERROR", "WARNING"])

    # Patterns to search for in log messages
    patterns: List[str] = field(default_factory=list)

@dataclass
class APIMonitorConfig:
    """Configuration for API and service monitoring."""
    
    # Endpoints to monitor
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    # Default timeout for HTTP requests
    request_timeout: float = 30.0
    
    # Check interval in seconds
    check_interval: float = 60.0
    
    # Number of retries for failed requests
    max_retries: int = 3
    
    # Expected response codes (empty = any 2xx)
    expected_status_codes: List[int] = field(default_factory=list)
    
    # Response time threshold in seconds
    response_time_threshold: float = 5.0


@dataclass
class DataPipelineConfig:
    """Configuration for data pipeline monitoring."""
    
    # Data directories to monitor
    data_paths: List[str] = field(default_factory=lambda: [
        "data/",
        "models/",
        "training/",
        "empirical_data/",
    ])
    
    # File patterns for data files
    data_file_patterns: List[str] = field(default_factory=lambda: [
        "*.csv",
        "*.json",
        "*.parquet",
        "*.h5",
        "*.pkl",
        "*.joblib",
    ])
    
    # Schema validation settings
    enable_schema_validation: bool = True
    schema_files_path: str = "schemas/"
    
    # Data quality thresholds
    min_data_quality_score: float = 0.8
    max_missing_values_percent: float = 10.0


@dataclass
class HookExecutionConfig:
    """Configuration for hook execution."""
    
    # Maximum execution time in seconds
    max_execution_time: int = 300
    
    # Maximum number of retries
    max_retries: int = 3
    
    # Retry delay in seconds
    retry_delay: float = 5.0
    
    # Enable parallel execution
    enable_parallel_execution: bool = True
    
    # Maximum concurrent executions
    max_concurrent_executions: int = 10
    
    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0


@dataclass
class EventBusConfig:
    """Configuration for the event bus."""
    
    # Event queue size
    max_queue_size: int = 10000
    
    # Event persistence settings
    enable_persistence: bool = True
    persistence_path: str = "data/events/"
    
    # Event retention in hours
    event_retention_hours: int = 168  # 1 week
    
    # Batch processing settings
    batch_size: int = 100
    batch_timeout: float = 5.0


@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    
    # Notification channels
    channels: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Default notification settings
    default_channel: str = "console"
    enable_rate_limiting: bool = True
    rate_limit_window: int = 300  # 5 minutes
    max_notifications_per_window: int = 10


@dataclass
class AgentHooksConfig:
    """Main configuration for the Agent Hooks system."""

    # Component configurations
    file_watcher: FileWatcherConfig = field(default_factory=FileWatcherConfig)
    container_monitor: ContainerMonitorConfig = field(
        default_factory=ContainerMonitorConfig)
    container_log_analysis: ContainerLogAnalysisConfig = field(
        default_factory=ContainerLogAnalysisConfig)
    api_monitor: APIMonitorConfig = field(default_factory=APIMonitorConfig)
    data_pipeline: DataPipelineConfig = field(default_factory=DataPipelineConfig)
    hook_execution: HookExecutionConfig = field(default_factory=HookExecutionConfig)
    event_bus: EventBusConfig = field(default_factory=EventBusConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    
    # Global settings
    enable_debug_logging: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Integration settings
    enable_windmill_integration: bool = True
    windmill_base_url: str = "http://localhost:8000"
    windmill_token: Optional[str] = None
    
    enable_terraform_integration: bool = True
    terraform_workspace_path: str = "infra/terraform/"
    terraform_state_backend: str = "local"
    
    # Kiro integration settings
    enable_kiro_integration: bool = True
    kiro_hooks_path: str = ".kiro/hooks/"
    kiro_steering_path: str = ".kiro/steering/"


def load_config_from_file(config_path: str) -> AgentHooksConfig:
    """Load configuration from a YAML or TOML file."""
    from pathlib import Path

    import yaml
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        if config_file.suffix.lower() in ['.yaml', '.yml']:
            config_data = yaml.safe_load(f)
        elif config_file.suffix.lower() == '.toml':
            import tomli
            config_data = tomli.load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_file.suffix}")
    
    # Convert dict to config object
    return AgentHooksConfig(**config_data)


def create_default_config() -> AgentHooksConfig:
    """Create a default configuration for the Phoenix DemiGod system."""
    config = AgentHooksConfig()
    
    # Configure file watcher for Phoenix DemiGod specific paths
    config.file_watcher.watch_paths = [
        "src/",
        "config/",
        "scripts/",
        "infra/terraform/",
        "infra/windmill-scripts/",
        "docker/",
        "monitoring/",
        "agents/",
        "phase-1-prototype/",
        "phase-2-specialization/",
        "phase-3-scaling/",
        "phase-4-commercialization/",
        ".kiro/",
    ]
    
    # Configure container monitoring for Phoenix containers
    config.container_monitor.container_labels = {
        "project": "phoenix-demigod",
        "component": "agent"
    }
    
    # Configure API monitoring for Phoenix services
    config.api_monitor.endpoints = [
        {
            "name": "DemiGod Agent API",
            "url": "http://localhost:8000/health",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Chaos Agent API",
            "url": "http://localhost:8001/health",
            "method": "GET",
            "expected_status": 200
        },
        {
            "name": "Windmill API",
            "url": "http://localhost:8000/api/version",
            "method": "GET",
            "expected_status": 200
        }
    ]

    # Configure container log analysis
    config.container_log_analysis.log_levels = ["ERROR", "WARNING"]
    config.container_log_analysis.patterns = ["Exception", "Error", "Warning"]

    # Configure notifications
    config.notifications.channels = {
        "console": {
            "type": "console",
            "enabled": True
        },
        "file": {
            "type": "file",
            "enabled": True,
            "path": "logs/notifications.log"
        },
        "webhook": {
            "type": "webhook",
            "enabled": False,
            "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        }
    }
    
    return config