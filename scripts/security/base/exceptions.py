"""
Custom exceptions for Phoenix Hydra security management.
Provides specific error types for different security scenarios.
"""


class SecurityError(Exception):
    """Base exception for all security-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class VulnerabilityDetectionError(SecurityError):
    """Raised when vulnerability detection fails."""
    pass


class DependencyValidationError(SecurityError):
    """Raised when dependency validation fails."""
    
    def __init__(self, message: str, package_name: str, version: str, validation_failures: list = None):
        super().__init__(message)
        self.package_name = package_name
        self.version = version
        self.validation_failures = validation_failures or []


class PhoenixHydraComplianceError(DependencyValidationError):
    """Raised when a dependency fails Phoenix Hydra compliance checks."""
    pass


class OfflineCompatibilityError(PhoenixHydraComplianceError):
    """Raised when a dependency requires internet connectivity."""
    pass


class PrivacyComplianceError(PhoenixHydraComplianceError):
    """Raised when a dependency violates privacy requirements."""
    pass


class ContainerCompatibilityError(PhoenixHydraComplianceError):
    """Raised when a dependency is incompatible with rootless containers."""
    pass


class UpdateError(SecurityError):
    """Base exception for dependency update errors."""
    
    def __init__(self, message: str, package_name: str, from_version: str, to_version: str):
        super().__init__(message)
        self.package_name = package_name
        self.from_version = from_version
        self.to_version = to_version


class UpdateApplicationError(UpdateError):
    """Raised when applying a dependency update fails."""
    pass


class UpdateRollbackError(UpdateError):
    """Raised when rolling back a failed update fails."""
    pass


class EmergencyUpdateError(UpdateError):
    """Raised when emergency security update fails."""
    pass


class AuditError(SecurityError):
    """Raised when security audit operations fail."""
    pass


class ConfigurationError(SecurityError):
    """Raised when security configuration is invalid."""
    
    def __init__(self, message: str, config_issues: list = None):
        super().__init__(message)
        self.config_issues = config_issues or []


class DatabaseError(SecurityError):
    """Raised when vulnerability database operations fail."""
    pass


class ReportGenerationError(SecurityError):
    """Raised when security report generation fails."""
    pass