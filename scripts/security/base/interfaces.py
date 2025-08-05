"""
Base interfaces for Phoenix Hydra security components.
Defines contracts for vulnerability scanning, dependency validation, and update management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels aligned with Phoenix Hydra impact assessment."""
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class PhoenixHydraImpact(Enum):
    """Phoenix Hydra specific impact levels for vulnerabilities."""
    BLOCKING = "blocking"  # Blocks builds/deployments
    WARNING = "warning"    # Generates warnings but allows continuation
    INFO = "info"         # Informational only


class UpdateType(Enum):
    """Types of dependency updates."""
    SECURITY = "security"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


@dataclass
class VulnerabilityRecord:
    """Represents a security vulnerability in a dependency."""
    id: str
    package_name: str
    version: str
    severity: VulnerabilitySeverity
    cve: Optional[str]
    description: str
    phoenix_hydra_impact: PhoenixHydraImpact
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "open"  # open, resolved, mitigated, accepted
    remediation_steps: List[str] = None
    
    def __post_init__(self):
        if self.remediation_steps is None:
            self.remediation_steps = []


@dataclass
class DependencyUpdate:
    """Represents a proposed dependency update."""
    id: str
    package_name: str
    from_version: str
    to_version: str
    update_type: UpdateType
    phoenix_hydra_compatible: bool
    approval_required: bool
    applied_at: Optional[datetime] = None
    rollback_plan: List[str] = None
    test_results: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.rollback_plan is None:
            self.rollback_plan = []
        if self.test_results is None:
            self.test_results = []


@dataclass
class SecurityAuditEntry:
    """Represents an entry in the security audit trail."""
    id: str
    timestamp: datetime
    action: str  # scan, update, resolve, mitigate
    package_name: str
    details: str
    developer: str
    phoenix_hydra_impact: str
    verification_steps: List[str] = None
    
    def __post_init__(self):
        if self.verification_steps is None:
            self.verification_steps = []


class SecurityScanner(ABC):
    """Abstract base class for security vulnerability scanners."""
    
    @abstractmethod
    async def scan_dependencies(self) -> List[VulnerabilityRecord]:
        """Scan project dependencies for security vulnerabilities."""
        pass
    
    @abstractmethod
    async def assess_phoenix_hydra_impact(self, vulnerabilities: List[VulnerabilityRecord]) -> List[VulnerabilityRecord]:
        """Assess the impact of vulnerabilities on Phoenix Hydra components."""
        pass
    
    @abstractmethod
    async def update_vulnerability_database(self) -> bool:
        """Update the local vulnerability database."""
        pass


class DependencyValidator(ABC):
    """Abstract base class for Phoenix Hydra dependency validation."""
    
    @abstractmethod
    async def validate_dependency(self, package_name: str, version: str) -> Dict[str, Any]:
        """Validate a dependency against Phoenix Hydra requirements."""
        pass
    
    @abstractmethod
    async def check_offline_compatibility(self, package_name: str, version: str) -> bool:
        """Check if a dependency supports offline operation."""
        pass
    
    @abstractmethod
    async def check_privacy_compliance(self, package_name: str, version: str) -> bool:
        """Check if a dependency complies with Phoenix Hydra privacy requirements."""
        pass
    
    @abstractmethod
    async def check_container_compatibility(self, package_name: str, version: str) -> bool:
        """Check if a dependency works in rootless containers."""
        pass


class UpdateManager(ABC):
    """Abstract base class for automated dependency update management."""
    
    @abstractmethod
    async def process_security_updates(self) -> List[DependencyUpdate]:
        """Process available security updates."""
        pass
    
    @abstractmethod
    async def apply_update(self, update: DependencyUpdate) -> bool:
        """Apply a dependency update."""
        pass
    
    @abstractmethod
    async def rollback_update(self, update: DependencyUpdate) -> bool:
        """Rollback a failed dependency update."""
        pass
    
    @abstractmethod
    async def emergency_update(self, vulnerability: VulnerabilityRecord) -> bool:
        """Apply emergency security update for critical vulnerabilities."""
        pass


class AuditLogger(ABC):
    """Abstract base class for security audit logging."""
    
    @abstractmethod
    async def log_security_action(self, entry: SecurityAuditEntry) -> None:
        """Log a security-related action to the audit trail."""
        pass
    
    @abstractmethod
    async def get_audit_entries(self, days: int = 30) -> List[SecurityAuditEntry]:
        """Retrieve audit entries from the specified number of days."""
        pass
    
    @abstractmethod
    async def generate_audit_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive audit report for the specified date range."""
        pass


class SecurityReporter(ABC):
    """Abstract base class for security reporting and dashboard generation."""
    
    @abstractmethod
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security status report."""
        pass
    
    @abstractmethod
    async def get_security_metrics(self) -> Dict[str, Any]:
        """Get current security metrics and trends."""
        pass
    
    @abstractmethod
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate Phoenix Hydra compliance report."""
        pass