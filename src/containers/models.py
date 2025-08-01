from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class HealthCheckConfig:
    command: List[str]
    interval: int
    retries: int


@dataclass
class RestartPolicy:
    name: str
    max_retries: int


@dataclass
class ServiceConfig:
    name: str
    image: str
    ports: List[str]
    environment: Dict[str, str]
    volumes: List[str]
    depends_on: List[str]
    health_check: Optional[HealthCheckConfig]
    restart_policy: RestartPolicy


@dataclass
class SecretsConfig:
    provider: str
    config: Dict[str, Any]


@dataclass
class ResourceLimits:
    cpus: float
    memory: str


@dataclass
class MonitoringConfig:
    enabled: bool
    metrics_port: Optional[int]


@dataclass
class EnvironmentConfig:
    name: str
    compose_files: List[str]
    environment_variables: Dict[str, str]
    secrets_config: Optional[SecretsConfig]
    resource_limits: Optional[ResourceLimits]
    monitoring_config: MonitoringConfig


@dataclass
class HealthStatus:
    service_name: str
    status: str  # healthy, unhealthy, starting, stopped
    last_check: datetime
    response_time: Optional[float]
    error_message: Optional[str]
    restart_count: int
    uptime: timedelta


# Result Models for interfaces
class ComposeResult:
    success: bool
    message: str


class ValidationResult:
    is_valid: bool
    errors: List[str]


class ServiceStatus:
    name: str
    status: str
    uptime: str


class TaskResult:
    success: bool
    output: str


class RestartResult:
    service_name: str
    success: bool