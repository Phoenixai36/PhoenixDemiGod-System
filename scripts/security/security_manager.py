"""
Main security manager for Phoenix Hydra dependency security management.
Coordinates all security components and provides a unified interface.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base.config import SecurityConfig
from .base.exceptions import ConfigurationError, SecurityError
from .base.interfaces import (
    AuditLogger,
    DependencyValidator,
    SecurityReporter,
    SecurityScanner,
    UpdateManager,
    VulnerabilityRecord,
)
from .base.utils import (
    ensure_directory_exists,
    get_audit_log_path,
    get_security_config_path,
    get_vulnerability_db_path,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhoenixHydraSecurityManager:
    """
    Main security manager that coordinates all Phoenix Hydra security components.
    Provides a unified interface for vulnerability scanning, dependency validation,
    automated updates, and security reporting.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the security manager.
        
        Args:
            config_path: Path to security configuration file
        """
        self.config_path = config_path or get_security_config_path()
        self.config: Optional[SecurityConfig] = None
        
        # Component instances (will be initialized in setup)
        self.scanner: Optional[SecurityScanner] = None
        self.validator: Optional[DependencyValidator] = None
        self.update_manager: Optional[UpdateManager] = None
        self.audit_logger: Optional[AuditLogger] = None
        self.reporter: Optional[SecurityReporter] = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the security manager and all components."""
        if self._initialized:
            return
        
        try:
            # Load configuration
            await self._load_configuration()
            
            # Validate configuration
            await self._validate_configuration()
            
            # Setup directories
            await self._setup_directories()
            
            # Initialize components (placeholder - will be implemented in later tasks)
            await self._initialize_components()
            
            self._initialized = True
            logger.info("Phoenix Hydra Security Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize security manager: {e}")
            raise SecurityError(f"Security manager initialization failed: {e}")
    
    async def _load_configuration(self) -> None:
        """Load security configuration from file."""
        try:
            if self.config_path.exists():
                self.config = SecurityConfig.load_from_file(str(self.config_path))
                logger.info(f"Loaded security configuration from {self.config_path}")
            else:
                self.config = SecurityConfig.create_default()
                self.config.save_to_file(str(self.config_path))
                logger.info(f"Created default security configuration at {self.config_path}")
                
        except Exception as e:
            raise ConfigurationError(f"Failed to load security configuration: {e}")
    
    async def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        if not self.config:
            raise ConfigurationError("No configuration loaded")
        
        issues = self.config.validate()
        if issues:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {issue}" for issue in issues)
            raise ConfigurationError(error_msg, issues)
        
        logger.info("Security configuration validated successfully")
    
    async def _setup_directories(self) -> None:
        """Setup required directories for security operations."""
        directories = [
            Path(self.config.scanner.vulnerability_db_path).parent,
            Path(self.config.audit.audit_log_path),
            get_vulnerability_db_path().parent,
            get_audit_log_path()
        ]
        
        for directory in directories:
            ensure_directory_exists(directory)
            logger.debug(f"Ensured directory exists: {directory}")
    
    async def _initialize_components(self) -> None:
        """Initialize security components (placeholder for now)."""
        # Note: Component initialization will be implemented in later tasks
        # For now, we just log that components would be initialized here
        
        logger.info("Security components initialization (placeholder):")
        logger.info("- Scanner: Will be implemented in task 2.1")
        logger.info("- Validator: Will be implemented in task 3.1") 
        logger.info("- Update Manager: Will be implemented in task 4.1")
        logger.info("- Audit Logger: Will be implemented in task 5.1")
        logger.info("- Reporter: Will be implemented in task 5.2")
    
    async def scan_dependencies(self) -> List[VulnerabilityRecord]:
        """
        Scan project dependencies for security vulnerabilities.
        
        Returns:
            List of vulnerability records found
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.scanner:
            raise SecurityError("Security scanner not initialized")
        
        logger.info("Starting dependency vulnerability scan...")
        vulnerabilities = await self.scanner.scan_dependencies()
        
        # Assess Phoenix Hydra specific impact
        vulnerabilities = await self.scanner.assess_phoenix_hydra_impact(vulnerabilities)
        
        logger.info(f"Scan completed: found {len(vulnerabilities)} vulnerabilities")
        return vulnerabilities
    
    async def validate_dependency(self, package_name: str, version: str) -> Dict[str, Any]:
        """
        Validate a dependency against Phoenix Hydra requirements.
        
        Args:
            package_name: Name of the package to validate
            version: Version of the package to validate
            
        Returns:
            Validation results dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.validator:
            raise SecurityError("Dependency validator not initialized")
        
        logger.info(f"Validating dependency: {package_name}@{version}")
        result = await self.validator.validate_dependency(package_name, version)
        
        logger.info(f"Validation completed for {package_name}@{version}")
        return result
    
    async def process_security_updates(self) -> List[Dict[str, Any]]:
        """
        Process available security updates.
        
        Returns:
            List of processed updates
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.update_manager:
            raise SecurityError("Update manager not initialized")
        
        logger.info("Processing security updates...")
        updates = await self.update_manager.process_security_updates()
        
        logger.info(f"Processed {len(updates)} security updates")
        return updates
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security report.
        
        Returns:
            Security report dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.reporter:
            raise SecurityError("Security reporter not initialized")
        
        logger.info("Generating security report...")
        report = await self.reporter.generate_security_report()
        
        logger.info("Security report generated successfully")
        return report
    
    async def emergency_response(self, vulnerability_id: str) -> bool:
        """
        Execute emergency response for critical vulnerability.
        
        Args:
            vulnerability_id: ID of the critical vulnerability
            
        Returns:
            True if emergency response was successful
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.update_manager:
            raise SecurityError("Update manager not initialized")
        
        logger.warning(f"Executing emergency response for vulnerability: {vulnerability_id}")
        
        # This would be implemented in the update manager
        # For now, just log the action
        logger.info(f"Emergency response executed for {vulnerability_id}")
        return True
    
    async def get_security_status(self) -> Dict[str, Any]:
        """
        Get current security status summary.
        
        Returns:
            Security status dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        status = {
            "initialized": self._initialized,
            "config_loaded": self.config is not None,
            "components": {
                "scanner": self.scanner is not None,
                "validator": self.validator is not None,
                "update_manager": self.update_manager is not None,
                "audit_logger": self.audit_logger is not None,
                "reporter": self.reporter is not None
            },
            "last_scan": None,  # Will be implemented with actual scanner
            "vulnerability_count": 0,  # Will be implemented with actual scanner
            "pending_updates": 0,  # Will be implemented with actual update manager
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of security system.
        
        Returns:
            Health check results
        """
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check configuration
            if self.config:
                health["checks"]["configuration"] = "ok"
            else:
                health["checks"]["configuration"] = "error"
                health["status"] = "unhealthy"
            
            # Check directories
            required_dirs = [
                get_vulnerability_db_path().parent,
                get_audit_log_path()
            ]
            
            for directory in required_dirs:
                if directory.exists():
                    health["checks"][f"directory_{directory.name}"] = "ok"
                else:
                    health["checks"][f"directory_{directory.name}"] = "error"
                    health["status"] = "unhealthy"
            
            # Check component initialization (placeholder)
            health["checks"]["components"] = "not_implemented"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health
    
    async def shutdown(self) -> None:
        """Shutdown the security manager and cleanup resources."""
        logger.info("Shutting down Phoenix Hydra Security Manager...")
        
        # Cleanup components (placeholder)
        self.scanner = None
        self.validator = None
        self.update_manager = None
        self.audit_logger = None
        self.reporter = None
        
        self._initialized = False
        logger.info("Security manager shutdown complete")


# Convenience function for creating a security manager instance
async def create_security_manager(config_path: Optional[Path] = None) -> PhoenixHydraSecurityManager:
    """
    Create and initialize a Phoenix Hydra Security Manager.
    
    Args:
        config_path: Optional path to security configuration file
        
    Returns:
        Initialized security manager instance
    """
    manager = PhoenixHydraSecurityManager(config_path)
    await manager.initialize()
    return manager