"""
Configuration validator for Phoenix Hydra System

This module validates that all required configurations and secrets are properly
set up for the Phoenix Hydra system to function correctly.
"""

import os
import requests
import psutil
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from .secrets_manager import get_secrets_manager
from .logging_system import get_logger


@dataclass
class ValidationResult:
    """Result of a configuration validation check"""
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    severity: str = "error"  # error, warning, info


class ConfigValidator:
    """Validates Phoenix Hydra system configuration"""
    
    def __init__(self):
        self.logger = get_logger()
        self.results: List[ValidationResult] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        self.results.clear()
        
        # Core validation checks
        self._validate_secrets()
        self._validate_environment()
        self._validate_file_structure()
        self._validate_dependencies()
        self._validate_services()
        self._validate_network_connectivity()
        self._validate_permissions()
        
        # Generate summary
        return self._generate_summary()
    
    def _validate_secrets(self):
        """Validate secrets configuration"""
        try:
            secrets_manager = get_secrets_manager()
            validation = secrets_manager.validate_secrets()
            
            if validation["valid"]:
                self.results.append(ValidationResult(
                    name="secrets_configuration",
                    passed=True,
                    message=f"All required secrets configured ({validation['configured_secrets']}/{validation['total_secrets']})",
                    details=validation
                ))
            else:
                self.results.append(ValidationResult(
                    name="secrets_configuration",
                    passed=False,
                    message=f"Missing required secrets: {', '.join(validation['missing_required'])}",
                    details=validation
                ))
            
            # Validate n8n credentials specifically
            try:
                n8n_creds = secrets_manager.get_n8n_credentials()
                if n8n_creds["user"] and n8n_creds["password"]:
                    self.results.append(ValidationResult(
                        name="n8n_credentials",
                        passed=True,
                        message="n8n credentials are configured",
                        details={"user": n8n_creds["user"][:10] + "..."}
                    ))
                else:
                    self.results.append(ValidationResult(
                        name="n8n_credentials",
                        passed=False,
                        message="n8n credentials are missing or incomplete"
                    ))
            except Exception as e:
                self.results.append(ValidationResult(
                    name="n8n_credentials",
                    passed=False,
                    message=f"Failed to retrieve n8n credentials: {e}"
                ))
                
        except Exception as e:
            self.results.append(ValidationResult(
                name="secrets_configuration",
                passed=False,
                message=f"Secrets manager initialization failed: {e}"
            ))
    
    def _validate_environment(self):
        """Validate environment variables"""
        required_env_vars = [
            "PHOENIX_MASTER_KEY"
        ]
        
        optional_env_vars = [
            "N8N_USER",
            "N8N_PASSWORD",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "MINIO_ACCESS_KEY",
            "MINIO_SECRET_KEY"
        ]
        
        # Check required environment variables
        missing_required = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        if missing_required:
            self.results.append(ValidationResult(
                name="environment_variables",
                passed=False,
                message=f"Missing required environment variables: {', '.join(missing_required)}"
            ))
        else:
            self.results.append(ValidationResult(
                name="environment_variables",
                passed=True,
                message="All required environment variables are set"
            ))
        
        # Check optional environment variables
        available_optional = []
        for var in optional_env_vars:
            if os.getenv(var):
                available_optional.append(var)
        
        self.results.append(ValidationResult(
            name="optional_environment_variables",
            passed=True,
            message=f"Optional environment variables available: {len(available_optional)}/{len(optional_env_vars)}",
            details={"available": available_optional},
            severity="info"
        ))
    
    def _validate_file_structure(self):
        """Validate required file structure"""
        required_files = [
            "src/phoenix_system_review/__init__.py",
            "src/phoenix_system_review/core/secrets_manager.py",
            "src/phoenix_system_review/core/logging_system.py",
            "src/phoenix_system_review/core/error_handler.py",
            "scripts/setup_secrets.py",
            "infra/podman/compose.secrets.yaml"
        ]
        
        required_directories = [
            "src/phoenix_system_review",
            "src/phoenix_system_review/core",
            "scripts",
            "infra/podman",
            "tests"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        missing_dirs = []
        for dir_path in required_directories:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_files or missing_dirs:
            self.results.append(ValidationResult(
                name="file_structure",
                passed=False,
                message=f"Missing files/directories: {len(missing_files + missing_dirs)}",
                details={"missing_files": missing_files, "missing_directories": missing_dirs}
            ))
        else:
            self.results.append(ValidationResult(
                name="file_structure",
                passed=True,
                message="All required files and directories exist"
            ))
        
        # Check secrets directory
        secrets_dir = Path(".secrets")
        if secrets_dir.exists():
            self.results.append(ValidationResult(
                name="secrets_directory",
                passed=True,
                message="Secrets directory exists",
                severity="info"
            ))
        else:
            self.results.append(ValidationResult(
                name="secrets_directory",
                passed=False,
                message="Secrets directory not found (will be created automatically)",
                severity="warning"
            ))
    
    def _validate_dependencies(self):
        """Validate Python dependencies"""
        required_packages = [
            "cryptography",
            "keyring",
            "psutil",
            "requests"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.results.append(ValidationResult(
                name="python_dependencies",
                passed=False,
                message=f"Missing Python packages: {', '.join(missing_packages)}"
            ))
        else:
            self.results.append(ValidationResult(
                name="python_dependencies",
                passed=True,
                message="All required Python packages are installed"
            ))
        
        # Check for Podman/Docker
        container_runtime = None
        try:
            subprocess.run(["podman", "--version"], capture_output=True, check=True)
            container_runtime = "podman"
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(["docker", "--version"], capture_output=True, check=True)
                container_runtime = "docker"
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        if container_runtime:
            self.results.append(ValidationResult(
                name="container_runtime",
                passed=True,
                message=f"Container runtime available: {container_runtime}",
                details={"runtime": container_runtime}
            ))
        else:
            self.results.append(ValidationResult(
                name="container_runtime",
                passed=False,
                message="No container runtime (Podman/Docker) found"
            ))
    
    def _validate_services(self):
        """Validate service configurations"""
        services_to_check = [
            {"name": "n8n", "url": "http://localhost:5678", "required": True},
            {"name": "postgres", "url": "http://localhost:5432", "required": True},
            {"name": "minio", "url": "http://localhost:9000", "required": True},
            {"name": "prometheus", "url": "http://localhost:9090", "required": False},
            {"name": "grafana", "url": "http://localhost:3000", "required": False}
        ]
        
        for service in services_to_check:
            try:
                response = requests.get(service["url"], timeout=5)
                self.results.append(ValidationResult(
                    name=f"service_{service['name']}",
                    passed=True,
                    message=f"{service['name']} service is responding",
                    details={"status_code": response.status_code},
                    severity="info"
                ))
            except requests.exceptions.RequestException:
                severity = "error" if service["required"] else "warning"
                self.results.append(ValidationResult(
                    name=f"service_{service['name']}",
                    passed=not service["required"],
                    message=f"{service['name']} service is not responding",
                    severity=severity
                ))
    
    def _validate_network_connectivity(self):
        """Validate network connectivity"""
        # Check internet connectivity
        try:
            response = requests.get("https://httpbin.org/status/200", timeout=10)
            self.results.append(ValidationResult(
                name="internet_connectivity",
                passed=True,
                message="Internet connectivity is available",
                severity="info"
            ))
        except requests.exceptions.RequestException:
            self.results.append(ValidationResult(
                name="internet_connectivity",
                passed=False,
                message="Internet connectivity is not available",
                severity="warning"
            ))
        
        # Check local network ports
        used_ports = []
        for conn in psutil.net_connections():
            if conn.laddr and conn.status == 'LISTEN':
                used_ports.append(conn.laddr.port)
        
        required_ports = [5678, 5432, 9000, 9090, 3000]
        conflicting_ports = [port for port in required_ports if port in used_ports]
        
        if conflicting_ports:
            self.results.append(ValidationResult(
                name="port_conflicts",
                passed=False,
                message=f"Required ports already in use: {conflicting_ports}",
                details={"conflicting_ports": conflicting_ports},
                severity="warning"
            ))
        else:
            self.results.append(ValidationResult(
                name="port_conflicts",
                passed=True,
                message="No port conflicts detected",
                severity="info"
            ))
    
    def _validate_permissions(self):
        """Validate file permissions"""
        # Check if we can write to required directories
        write_test_dirs = [
            ".",
            "logs",
            ".secrets"
        ]
        
        permission_issues = []
        for dir_path in write_test_dirs:
            dir_path = Path(dir_path)
            try:
                # Create directory if it doesn't exist
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Test write permission
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                
            except (PermissionError, OSError) as e:
                permission_issues.append(f"{dir_path}: {e}")
        
        if permission_issues:
            self.results.append(ValidationResult(
                name="file_permissions",
                passed=False,
                message=f"Permission issues detected: {len(permission_issues)}",
                details={"issues": permission_issues}
            ))
        else:
            self.results.append(ValidationResult(
                name="file_permissions",
                passed=True,
                message="File permissions are correct"
            ))
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary"""
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results if result.passed)
        failed_checks = total_checks - passed_checks
        
        errors = [r for r in self.results if not r.passed and r.severity == "error"]
        warnings = [r for r in self.results if not r.passed and r.severity == "warning"]
        
        summary = {
            "overall_status": "PASS" if failed_checks == 0 else "FAIL",
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return summary
    
    def print_summary(self, summary: Optional[Dict[str, Any]] = None):
        """Print validation summary to console"""
        if summary is None:
            summary = self._generate_summary()
        
        print("\n🔍 Phoenix Hydra Configuration Validation")
        print("=" * 50)
        
        # Overall status
        status_color = "🟢" if summary["overall_status"] == "PASS" else "🔴"
        print(f"\n{status_color} Overall Status: {summary['overall_status']}")
        print(f"📊 Checks: {summary['passed_checks']}/{summary['total_checks']} passed")
        
        if summary["error_count"] > 0:
            print(f"❌ Errors: {summary['error_count']}")
        
        if summary["warning_count"] > 0:
            print(f"⚠️  Warnings: {summary['warning_count']}")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        print("-" * 30)
        
        for result in summary["results"]:
            if result["passed"]:
                icon = "✅"
            elif result["severity"] == "warning":
                icon = "⚠️ "
            else:
                icon = "❌"
            
            print(f"{icon} {result['name']}: {result['message']}")
            
            if result["details"] and not result["passed"]:
                for key, value in result["details"].items():
                    if isinstance(value, list) and value:
                        print(f"   {key}: {', '.join(map(str, value))}")
                    elif value:
                        print(f"   {key}: {value}")
        
        # Recommendations
        if summary["overall_status"] == "FAIL":
            print("\n🎯 Recommendations:")
            print("-" * 20)
            
            for result in summary["results"]:
                if not result["passed"] and result["severity"] == "error":
                    if "secrets" in result["name"]:
                        print("• Run: python scripts/setup_secrets.py")
                    elif "dependencies" in result["name"]:
                        print("• Run: pip install -r requirements.txt")
                    elif "container_runtime" in result["name"]:
                        print("• Install Podman or Docker")
                    elif "environment" in result["name"]:
                        print("• Set required environment variables")


def main():
    """Main validation function"""
    validator = ConfigValidator()
    summary = validator.validate_all()
    validator.print_summary(summary)
    
    # Return appropriate exit code
    return 0 if summary["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())