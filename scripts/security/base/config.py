"""
Base configuration classes for Phoenix Hydra security management.
Provides centralized configuration management for security components.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class VulnerabilityThresholds:
    """Configuration for vulnerability severity thresholds."""
    critical_block_build: bool = True
    high_block_build: bool = True
    moderate_block_build: bool = False
    low_block_build: bool = False
    
    # Phoenix Hydra specific thresholds
    phoenix_core_escalation: bool = True  # Escalate severity for core components
    offline_compatibility_required: bool = True
    privacy_compliance_required: bool = True


@dataclass
class ScannerConfig:
    """Configuration for security scanners."""
    npm_audit_enabled: bool = True
    osv_database_enabled: bool = True
    snyk_enabled: bool = False  # Optional external integration
    
    # Local database settings
    vulnerability_db_path: str = ".phoenix-hydra/security/vulnerability-db.sqlite"
    cache_duration_hours: int = 24
    offline_mode: bool = False
    
    # Update intervals
    database_update_interval_hours: int = 6
    scan_interval_minutes: int = 30


@dataclass
class ValidatorConfig:
    """Configuration for Phoenix Hydra dependency validation."""
    # Phoenix Hydra specific validation rules
    require_offline_compatibility: bool = True
    require_privacy_compliance: bool = True
    require_rootless_container_support: bool = True
    
    # Package validation settings
    check_external_network_access: bool = True
    check_telemetry_tracking: bool = True
    check_license_compatibility: bool = True
    
    # Allowed/blocked packages
    allowed_packages: List[str] = None
    blocked_packages: List[str] = None
    
    def __post_init__(self):
        if self.allowed_packages is None:
            self.allowed_packages = []
        if self.blocked_packages is None:
            self.blocked_packages = []


@dataclass
class UpdateManagerConfig:
    """Configuration for automated update management."""
    # Update automation settings
    auto_apply_security_patches: bool = True
    auto_apply_patch_updates: bool = False
    auto_apply_minor_updates: bool = False
    auto_apply_major_updates: bool = False
    
    # Testing requirements
    require_tests_pass: bool = True
    require_manual_approval_major: bool = True
    
    # Emergency response settings
    emergency_update_timeout_minutes: int = 30
    emergency_rollback_enabled: bool = True
    
    # Rollback settings
    create_backup_before_update: bool = True
    rollback_timeout_minutes: int = 15


@dataclass
class AuditConfig:
    """Configuration for security audit logging."""
    # Logging settings
    audit_log_path: str = ".phoenix-hydra/security/audit-logs/"
    log_retention_days: int = 90
    log_rotation_size_mb: int = 100
    
    # Audit detail levels
    log_all_scans: bool = True
    log_all_updates: bool = True
    log_validation_failures: bool = True
    
    # Compliance settings
    generate_compliance_reports: bool = True
    compliance_report_interval_days: int = 7


@dataclass
class NotificationConfig:
    """Configuration for security notifications and alerting."""
    # Notification channels
    email_enabled: bool = False
    webhook_enabled: bool = False
    vs_code_notifications: bool = True
    
    # Notification thresholds
    notify_critical_vulnerabilities: bool = True
    notify_high_vulnerabilities: bool = True
    notify_update_failures: bool = True
    notify_emergency_responses: bool = True
    
    # Contact settings
    email_recipients: List[str] = None
    webhook_url: Optional[str] = None
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []


@dataclass
class SecurityConfig:
    """Main security configuration container."""
    vulnerability_thresholds: VulnerabilityThresholds
    scanner: ScannerConfig
    validator: ValidatorConfig
    update_manager: UpdateManagerConfig
    audit: AuditConfig
    notifications: NotificationConfig
    
    # Global settings
    environment: str = "development"  # development, staging, production
    debug_mode: bool = False
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'SecurityConfig':
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            return cls.create_default()
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(
            vulnerability_thresholds=VulnerabilityThresholds(**config_data.get('vulnerability_thresholds', {})),
            scanner=ScannerConfig(**config_data.get('scanner', {})),
            validator=ValidatorConfig(**config_data.get('validator', {})),
            update_manager=UpdateManagerConfig(**config_data.get('update_manager', {})),
            audit=AuditConfig(**config_data.get('audit', {})),
            notifications=NotificationConfig(**config_data.get('notifications', {})),
            environment=config_data.get('environment', 'development'),
            debug_mode=config_data.get('debug_mode', False)
        )
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        config_data = {
            'vulnerability_thresholds': asdict(self.vulnerability_thresholds),
            'scanner': asdict(self.scanner),
            'validator': asdict(self.validator),
            'update_manager': asdict(self.update_manager),
            'audit': asdict(self.audit),
            'notifications': asdict(self.notifications),
            'environment': self.environment,
            'debug_mode': self.debug_mode
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    @classmethod
    def create_default(cls) -> 'SecurityConfig':
        """Create default security configuration."""
        return cls(
            vulnerability_thresholds=VulnerabilityThresholds(),
            scanner=ScannerConfig(),
            validator=ValidatorConfig(),
            update_manager=UpdateManagerConfig(),
            audit=AuditConfig(),
            notifications=NotificationConfig()
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate paths exist or can be created
        db_path = Path(self.scanner.vulnerability_db_path).parent
        if not db_path.exists():
            try:
                db_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create vulnerability database directory: {e}")
        
        audit_path = Path(self.audit.audit_log_path)
        if not audit_path.exists():
            try:
                audit_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create audit log directory: {e}")
        
        # Validate notification settings
        if self.notifications.email_enabled and not self.notifications.email_recipients:
            issues.append("Email notifications enabled but no recipients configured")
        
        if self.notifications.webhook_enabled and not self.notifications.webhook_url:
            issues.append("Webhook notifications enabled but no URL configured")
        
        # Validate update manager settings
        if (self.update_manager.auto_apply_major_updates and 
            not self.update_manager.require_manual_approval_major):
            issues.append("Major updates set to auto-apply without manual approval - this is risky")
        
        return issues