"""
CLI Configuration Management

Handles configuration loading, validation, and management for the
Phoenix Hydra System Review CLI application.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging


@dataclass
class ProjectConfig:
    """Project configuration settings."""
    name: str = "Phoenix Hydra"
    version: str = "1.0.0"
    description: str = "Phoenix Hydra System Review Configuration"


@dataclass
class AnalysisConfig:
    """Analysis configuration settings."""
    components: List[str] = field(default_factory=lambda: [
                                  'podman', 'n8n', 'windmill', 'phoenix-core', 'nca-toolkit'])
    skip_tests: bool = False
    deep_scan: bool = False
    performance_monitoring: bool = False
    security_checks: bool = False
    compliance_checks: bool = False


@dataclass
class ReportingConfig:
    """Reporting configuration settings."""
    default_format: str = "text"
    include_recommendations: bool = True
    include_metrics: bool = False
    generate_charts: bool = False
    executive_summary: bool = False


@dataclass
class HealthCheckConfig:
    """Health check configuration settings."""
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class AutomationConfig:
    """Automation configuration settings."""
    scheduled_reviews: bool = False
    alert_thresholds: Dict[str, Any] = field(default_factory=lambda: {
        'completion_percentage': 80,
        'critical_issues': 5
    })


@dataclass
class CLIConfig:
    """Complete CLI configuration."""
    project: ProjectConfig = field(default_factory=ProjectConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    health_checks: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    automation: Optional[AutomationConfig] = None


class ConfigManager:
    """
    Manages CLI configuration loading, validation, and defaults.
    """

    DEFAULT_CONFIG_NAMES = [
        '.phoenix-review.yaml',
        '.phoenix-review.yml',
        '.phoenix-review.json',
        'phoenix-review.yaml',
        'phoenix-review.yml',
        'phoenix-review.json'
    ]

    def __init__(self, project_root: str = '.'):
        """
        Initialize configuration manager.

        Args:
            project_root: Root directory to search for configuration files
        """
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[CLIConfig] = None

    def load_config(self, config_path: Optional[str] = None) -> CLIConfig:
        """
        Load configuration from file or use defaults.

        Args:
            config_path: Specific configuration file path

        Returns:
            CLIConfig: Loaded configuration
        """
        if config_path:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {config_path}")
        else:
            config_file = self._find_config_file()

        if config_file:
            self.logger.info(f"Loading configuration from {config_file}")
            config_data = self._load_config_file(config_file)
            self._config = self._parse_config_data(config_data)
        else:
            self.logger.info("No configuration file found, using defaults")
            self._config = CLIConfig()

        return self._config

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in project root."""
        for config_name in self.DEFAULT_CONFIG_NAMES:
            config_path = self.project_root / config_name
            if config_path.exists():
                return config_path
        return None

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration data from file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:  # YAML
                    return yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(
                f"Failed to load configuration from {config_path}: {e}")

    def _parse_config_data(self, data: Dict[str, Any]) -> CLIConfig:
        """Parse configuration data into CLIConfig object."""
        try:
            # Parse project config
            project_data = data.get('project', {})
            project_config = ProjectConfig(
                name=project_data.get('name', 'Phoenix Hydra'),
                version=project_data.get('version', '1.0.0'),
                description=project_data.get(
                    'description', 'Phoenix Hydra System Review Configuration')
            )

            # Parse analysis config
            analysis_data = data.get('analysis', {})
            analysis_config = AnalysisConfig(
                components=analysis_data.get(
                    'components', ['podman', 'n8n', 'windmill', 'phoenix-core', 'nca-toolkit']),
                skip_tests=analysis_data.get('skip_tests', False),
                deep_scan=analysis_data.get('deep_scan', False),
                performance_monitoring=analysis_data.get(
                    'performance_monitoring', False),
                security_checks=analysis_data.get('security_checks', False),
                compliance_checks=analysis_data.get('compliance_checks', False)
            )

            # Parse reporting config
            reporting_data = data.get('reporting', {})
            reporting_config = ReportingConfig(
                default_format=reporting_data.get('default_format', 'text'),
                include_recommendations=reporting_data.get(
                    'include_recommendations', True),
                include_metrics=reporting_data.get('include_metrics', False),
                generate_charts=reporting_data.get('generate_charts', False),
                executive_summary=reporting_data.get(
                    'executive_summary', False)
            )

            # Parse health check config
            health_data = data.get('health_checks', {})
            health_config = HealthCheckConfig(
                timeout=health_data.get('timeout', 30),
                retry_attempts=health_data.get('retry_attempts', 3)
            )

            # Parse automation config (optional)
            automation_config = None
            if 'automation' in data:
                automation_data = data['automation']
                automation_config = AutomationConfig(
                    scheduled_reviews=automation_data.get(
                        'scheduled_reviews', False),
                    alert_thresholds=automation_data.get('alert_thresholds', {
                        'completion_percentage': 80,
                        'critical_issues': 5
                    })
                )

            return CLIConfig(
                project=project_config,
                analysis=analysis_config,
                reporting=reporting_config,
                health_checks=health_config,
                automation=automation_config
            )

        except Exception as e:
            raise ValueError(f"Failed to parse configuration data: {e}")

    def save_config(self, config: CLIConfig, config_path: str, format_type: str = 'yaml') -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            config_path: Path to save configuration
            format_type: Format to save in ('yaml' or 'json')
        """
        config_data = self._config_to_dict(config)

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if format_type.lower() == 'json':
                    json.dump(config_data, f, indent=2)
                else:  # YAML
                    yaml.dump(config_data, f, default_flow_style=False)

            self.logger.info(f"Configuration saved to {config_path}")

        except Exception as e:
            raise ValueError(
                f"Failed to save configuration to {config_path}: {e}")

    def _config_to_dict(self, config: CLIConfig) -> Dict[str, Any]:
        """Convert CLIConfig to dictionary."""
        data = {
            'project': {
                'name': config.project.name,
                'version': config.project.version,
                'description': config.project.description
            },
            'analysis': {
                'components': config.analysis.components,
                'skip_tests': config.analysis.skip_tests,
                'deep_scan': config.analysis.deep_scan,
                'performance_monitoring': config.analysis.performance_monitoring,
                'security_checks': config.analysis.security_checks,
                'compliance_checks': config.analysis.compliance_checks
            },
            'reporting': {
                'default_format': config.reporting.default_format,
                'include_recommendations': config.reporting.include_recommendations,
                'include_metrics': config.reporting.include_metrics,
                'generate_charts': config.reporting.generate_charts,
                'executive_summary': config.reporting.executive_summary
            },
            'health_checks': {
                'timeout': config.health_checks.timeout,
                'retry_attempts': config.health_checks.retry_attempts
            }
        }

        if config.automation:
            data['automation'] = {
                'scheduled_reviews': config.automation.scheduled_reviews,
                'alert_thresholds': config.automation.alert_thresholds
            }

        return data

    def validate_config(self, config: CLIConfig) -> List[str]:
        """
        Validate configuration and return list of issues.

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages
        """
        issues = []

        # Validate project config
        if not config.project.name:
            issues.append("Project name cannot be empty")

        if not config.project.version:
            issues.append("Project version cannot be empty")

        # Validate analysis config
        if not config.analysis.components:
            issues.append(
                "At least one component must be specified for analysis")

        valid_components = ['podman', 'n8n',
                            'windmill', 'phoenix-core', 'nca-toolkit']
        for component in config.analysis.components:
            if component not in valid_components:
                issues.append(
                    f"Invalid component '{component}'. Valid components: {', '.join(valid_components)}")

        # Validate reporting config
        valid_formats = ['json', 'yaml', 'markdown', 'text', 'html']
        if config.reporting.default_format not in valid_formats:
            issues.append(
                f"Invalid default format '{config.reporting.default_format}'. Valid formats: {', '.join(valid_formats)}")

        # Validate health check config
        if config.health_checks.timeout <= 0:
            issues.append("Health check timeout must be positive")

        if config.health_checks.retry_attempts < 0:
            issues.append("Health check retry attempts cannot be negative")

        # Validate automation config
        if config.automation:
            thresholds = config.automation.alert_thresholds
            if 'completion_percentage' in thresholds:
                if not 0 <= thresholds['completion_percentage'] <= 100:
                    issues.append(
                        "Completion percentage threshold must be between 0 and 100")

            if 'critical_issues' in thresholds:
                if thresholds['critical_issues'] < 0:
                    issues.append(
                        "Critical issues threshold cannot be negative")

        return issues

    def get_config(self) -> CLIConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config
