"""
Podman Container Analysis for Phoenix Hydra System Review

Provides specialized analysis capabilities for Podman compose files,
container health checks, and systemd service definitions.
"""

import os
import yaml
import json
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..models.data_models import Component, ComponentStatus, Issue, Priority, EvaluationResult


class ContainerStatus(Enum):
    """Container status indicators"""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ContainerInfo:
    """Information about a container"""
    name: str
    image: str
    status: ContainerStatus
    ports: List[str]
    volumes: List[str]
    environment: Dict[str, str]
    health_check: Optional[Dict[str, Any]] = None
    restart_policy: Optional[str] = None


@dataclass
class ComposeAnalysis:
    """Analysis results for a compose file"""
    file_path: str
    services: Dict[str, ContainerInfo]
    networks: List[str]
    volumes: List[str]
    version: Optional[str]
    issues: List[Issue]
    health_score: float


@dataclass
class SystemdServiceInfo:
    """Information about a systemd service"""
    name: str
    file_path: str
    enabled: bool
    active: bool
    configuration: Dict[str, Any]
    dependencies: List[str]


class PodmanAnalyzer:
    """
    Analyzer for Podman container infrastructure in Phoenix Hydra.
    
    Provides comprehensive analysis of:
    - Podman compose file configurations
    - Container health and status
    - Systemd service definitions
    - Network and volume configurations
    """
    
    def __init__(self, project_root: str):
        """
        Initialize Podman analyzer.
        
        Args:
            project_root: Root directory of the Phoenix Hydra project
        """
        self.project_root = Path(project_root)
        self.podman_dir = self.project_root / "infra" / "podman"
        self.systemd_dir = self.podman_dir / "systemd"
        
        # Expected Phoenix Hydra services
        self.expected_services = {
            "phoenix-core": {
                "port": 8080,
                "health_endpoint": "/health",
                "required": True
            },
            "nca-toolkit": {
                "port": 8081,
                "health_endpoint": "/health",
                "required": True
            },
            "n8n-phoenix": {
                "port": 5678,
                "health_endpoint": "/healthz",
                "required": True
            },
            "windmill-phoenix": {
                "port": 8000,
                "health_endpoint": "/api/version",
                "required": True
            },
            "revenue-db": {
                "port": 5432,
                "health_endpoint": None,
                "required": True
            }
        }
    
    def analyze_compose_files(self) -> List[ComposeAnalysis]:
        """
        Analyze all Podman compose files in the infrastructure directory.
        
        Returns:
            List of ComposeAnalysis objects for each compose file
        """
        compose_files = []
        
        # Find all compose files
        for pattern in ["compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml"]:
            compose_files.extend(self.podman_dir.glob(pattern))
            compose_files.extend(self.podman_dir.glob(f"*{pattern}"))
        
        # Remove duplicates
        compose_files = list(set(compose_files))
        
        analyses = []
        for compose_file in compose_files:
            try:
                analysis = self._analyze_single_compose_file(compose_file)
                analyses.append(analysis)
            except Exception as e:
                # Create analysis with error
                analysis = ComposeAnalysis(
                    file_path=str(compose_file),
                    services={},
                    networks=[],
                    volumes=[],
                    version=None,
                    issues=[Issue(
                        severity=Priority.HIGH,
                        description=f"Failed to parse compose file: {str(e)}",
                        component="podman_compose",
                        file_path=str(compose_file)
                    )],
                    health_score=0.0
                )
                analyses.append(analysis)
        
        return analyses
    
    def _analyze_single_compose_file(self, compose_file: Path) -> ComposeAnalysis:
        """
        Analyze a single compose file.
        
        Args:
            compose_file: Path to the compose file
            
        Returns:
            ComposeAnalysis object with detailed analysis
        """
        with open(compose_file, 'r', encoding='utf-8') as f:
            compose_data = yaml.safe_load(f)
        
        services = {}
        issues = []
        
        # Analyze services
        if 'services' in compose_data:
            for service_name, service_config in compose_data['services'].items():
                container_info = self._parse_service_config(service_name, service_config)
                services[service_name] = container_info
                
                # Validate against expected services
                if service_name in self.expected_services:
                    service_issues = self._validate_service_config(
                        service_name, service_config, self.expected_services[service_name]
                    )
                    issues.extend(service_issues)
        
        # Check for missing required services
        for service_name, service_spec in self.expected_services.items():
            if service_spec["required"] and service_name not in services:
                issues.append(Issue(
                    severity=Priority.CRITICAL,
                    description=f"Required service '{service_name}' not found in compose file",
                    component="podman_compose",
                    file_path=str(compose_file)
                ))
        
        # Extract networks and volumes
        networks = list(compose_data.get('networks', {}).keys())
        volumes = list(compose_data.get('volumes', {}).keys())
        version = compose_data.get('version')
        
        # Calculate health score
        health_score = self._calculate_compose_health_score(services, issues)
        
        return ComposeAnalysis(
            file_path=str(compose_file),
            services=services,
            networks=networks,
            volumes=volumes,
            version=version,
            issues=issues,
            health_score=health_score
        )
    
    def _parse_service_config(self, service_name: str, service_config: Dict[str, Any]) -> ContainerInfo:
        """
        Parse service configuration into ContainerInfo.
        
        Args:
            service_name: Name of the service
            service_config: Service configuration from compose file
            
        Returns:
            ContainerInfo object
        """
        # Extract ports
        ports = []
        if 'ports' in service_config:
            for port_config in service_config['ports']:
                if isinstance(port_config, str):
                    ports.append(port_config)
                elif isinstance(port_config, dict):
                    target = port_config.get('target', '')
                    published = port_config.get('published', '')
                    ports.append(f"{published}:{target}")
        
        # Extract volumes
        volumes = []
        if 'volumes' in service_config:
            for volume_config in service_config['volumes']:
                if isinstance(volume_config, str):
                    volumes.append(volume_config)
                elif isinstance(volume_config, dict):
                    source = volume_config.get('source', '')
                    target = volume_config.get('target', '')
                    volumes.append(f"{source}:{target}")
        
        # Extract environment variables
        environment = {}
        if 'environment' in service_config:
            env_config = service_config['environment']
            if isinstance(env_config, list):
                for env_var in env_config:
                    if '=' in env_var:
                        key, value = env_var.split('=', 1)
                        environment[key] = value
            elif isinstance(env_config, dict):
                environment = env_config
        
        # Extract health check
        health_check = service_config.get('healthcheck')
        
        # Extract restart policy
        restart_policy = service_config.get('restart')
        
        return ContainerInfo(
            name=service_name,
            image=service_config.get('image', ''),
            status=ContainerStatus.UNKNOWN,  # Will be determined by runtime check
            ports=ports,
            volumes=volumes,
            environment=environment,
            health_check=health_check,
            restart_policy=restart_policy
        )
    
    def _validate_service_config(self, service_name: str, service_config: Dict[str, Any], 
                                expected_spec: Dict[str, Any]) -> List[Issue]:
        """
        Validate service configuration against expected specifications.
        
        Args:
            service_name: Name of the service
            service_config: Service configuration
            expected_spec: Expected service specification
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check if required port is exposed
        expected_port = expected_spec.get("port")
        if expected_port:
            ports = service_config.get('ports', [])
            port_found = False
            for port_config in ports:
                if isinstance(port_config, str) and str(expected_port) in port_config:
                    port_found = True
                    break
                elif isinstance(port_config, dict) and port_config.get('published') == expected_port:
                    port_found = True
                    break
            
            if not port_found:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description=f"Service '{service_name}' does not expose expected port {expected_port}",
                    component="podman_compose",
                    recommendation=f"Add port mapping for {expected_port}"
                ))
        
        # Check for health check configuration
        if 'healthcheck' not in service_config and expected_spec.get("health_endpoint"):
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Service '{service_name}' lacks health check configuration",
                component="podman_compose",
                recommendation="Add healthcheck configuration to compose file"
            ))
        
        # Check for restart policy
        if 'restart' not in service_config:
            issues.append(Issue(
                severity=Priority.LOW,
                description=f"Service '{service_name}' lacks restart policy",
                component="podman_compose",
                recommendation="Add restart policy (e.g., 'unless-stopped')"
            ))
        
        return issues
    
    def _calculate_compose_health_score(self, services: Dict[str, ContainerInfo], 
                                      issues: List[Issue]) -> float:
        """
        Calculate health score for compose configuration.
        
        Args:
            services: Dictionary of services
            issues: List of issues found
            
        Returns:
            Health score between 0.0 and 1.0
        """
        if not services:
            return 0.0
        
        # Base score from service completeness
        required_services = sum(1 for spec in self.expected_services.values() if spec["required"])
        found_services = sum(1 for name in services.keys() if name in self.expected_services)
        service_score = found_services / required_services if required_services > 0 else 0.0
        
        # Deduct points for issues
        issue_penalty = 0.0
        for issue in issues:
            if issue.severity == Priority.CRITICAL:
                issue_penalty += 0.3
            elif issue.severity == Priority.HIGH:
                issue_penalty += 0.2
            elif issue.severity == Priority.MEDIUM:
                issue_penalty += 0.1
            elif issue.severity == Priority.LOW:
                issue_penalty += 0.05
        
        return max(0.0, service_score - issue_penalty)
    
    def check_container_health(self) -> Dict[str, ContainerStatus]:
        """
        Check the health status of running containers.
        
        Returns:
            Dictionary mapping container names to their status
        """
        container_status = {}
        
        try:
            # Get list of containers
            result = subprocess.run(
                ["podman", "ps", "-a", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                containers = json.loads(result.stdout)
                for container in containers:
                    names = container.get('Names', [])
                    if names:
                        name = names[0] if isinstance(names, list) else names
                        state = container.get('State', '').lower()
                        
                        if state == 'running':
                            container_status[name] = ContainerStatus.RUNNING
                        elif state in ['stopped', 'exited']:
                            container_status[name] = ContainerStatus.STOPPED
                        elif state in ['failed', 'error']:
                            container_status[name] = ContainerStatus.FAILED
                        else:
                            container_status[name] = ContainerStatus.UNKNOWN
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            # If podman is not available or fails, return empty status
            pass
        
        return container_status
    
    def analyze_systemd_services(self) -> List[SystemdServiceInfo]:
        """
        Analyze systemd service definitions for Phoenix Hydra.
        
        Returns:
            List of SystemdServiceInfo objects
        """
        services = []
        
        if not self.systemd_dir.exists():
            return services
        
        # Find all systemd service files
        service_files = list(self.systemd_dir.glob("*.service"))
        service_files.extend(self.systemd_dir.glob("*.target"))
        service_files.extend(self.systemd_dir.glob("*.container"))
        service_files.extend(self.systemd_dir.glob("*.pod"))
        
        for service_file in service_files:
            try:
                service_info = self._parse_systemd_service(service_file)
                services.append(service_info)
            except Exception:
                # Skip files that can't be parsed
                continue
        
        return services
    
    def _parse_systemd_service(self, service_file: Path) -> SystemdServiceInfo:
        """
        Parse a systemd service file.
        
        Args:
            service_file: Path to the service file
            
        Returns:
            SystemdServiceInfo object
        """
        configuration = {}
        dependencies = []
        
        with open(service_file, 'r', encoding='utf-8') as f:
            current_section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    configuration[current_section] = {}
                elif '=' in line and current_section:
                    key, value = line.split('=', 1)
                    configuration[current_section][key] = value
                    
                    # Extract dependencies
                    if key.lower() in ['wants', 'requires', 'after', 'before']:
                        dependencies.extend(value.split())
        
        # Check if service is enabled/active (this would require systemctl access)
        service_name = service_file.stem
        enabled = False
        active = False
        
        try:
            # Try to check systemd status (may not work in all environments)
            result = subprocess.run(
                ["systemctl", "--user", "is-enabled", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            enabled = result.returncode == 0
            
            result = subprocess.run(
                ["systemctl", "--user", "is-active", service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            active = result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # systemctl not available or service not installed
            pass
        
        return SystemdServiceInfo(
            name=service_name,
            file_path=str(service_file),
            enabled=enabled,
            active=active,
            configuration=configuration,
            dependencies=dependencies
        )
    
    def validate_podman_installation(self) -> Tuple[bool, List[Issue]]:
        """
        Validate that Podman is properly installed and configured.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if podman command is available
        try:
            result = subprocess.run(
                ["podman", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                issues.append(Issue(
                    severity=Priority.CRITICAL,
                    description="Podman command failed to execute",
                    component="podman_installation",
                    recommendation="Install or reinstall Podman"
                ))
        except FileNotFoundError:
            issues.append(Issue(
                severity=Priority.CRITICAL,
                description="Podman command not found",
                component="podman_installation",
                recommendation="Install Podman container runtime"
            ))
        except subprocess.TimeoutExpired:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="Podman command timed out",
                component="podman_installation",
                recommendation="Check Podman installation and system resources"
            ))
        
        # Check if podman-compose is available
        try:
            result = subprocess.run(
                ["podman-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description="podman-compose command failed",
                    component="podman_installation",
                    recommendation="Install podman-compose or use 'podman compose'"
                ))
        except FileNotFoundError:
            # Try alternative podman compose command
            try:
                result = subprocess.run(
                    ["podman", "compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    issues.append(Issue(
                        severity=Priority.MEDIUM,
                        description="Neither podman-compose nor 'podman compose' available",
                        component="podman_installation",
                        recommendation="Install podman-compose or update Podman to version with compose support"
                    ))
            except (FileNotFoundError, subprocess.TimeoutExpired):
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description="No compose functionality available for Podman",
                    component="podman_installation",
                    recommendation="Install podman-compose or update Podman"
                ))
        
        return len(issues) == 0, issues
    
    def generate_evaluation_result(self) -> EvaluationResult:
        """
        Generate comprehensive evaluation result for Podman infrastructure.
        
        Returns:
            EvaluationResult with complete analysis
        """
        # Create component
        component = Component(
            name="podman_infrastructure",
            category="infrastructure",
            path=str(self.podman_dir),
            status=ComponentStatus.UNKNOWN
        )
        
        all_issues = []
        criteria_met = []
        criteria_missing = []
        
        # Analyze compose files
        compose_analyses = self.analyze_compose_files()
        if compose_analyses:
            criteria_met.append("compose_files_present")
            for analysis in compose_analyses:
                all_issues.extend(analysis.issues)
                if analysis.health_score >= 0.8:
                    criteria_met.append(f"compose_file_healthy_{Path(analysis.file_path).name}")
                else:
                    criteria_missing.append(f"compose_file_healthy_{Path(analysis.file_path).name}")
        else:
            criteria_missing.append("compose_files_present")
            all_issues.append(Issue(
                severity=Priority.CRITICAL,
                description="No Podman compose files found",
                component="podman_infrastructure",
                recommendation="Create compose.yaml file with Phoenix Hydra services"
            ))
        
        # Check container health
        container_status = self.check_container_health()
        if container_status:
            criteria_met.append("containers_discoverable")
            running_containers = sum(1 for status in container_status.values() 
                                   if status == ContainerStatus.RUNNING)
            if running_containers > 0:
                criteria_met.append("containers_running")
            else:
                criteria_missing.append("containers_running")
        else:
            criteria_missing.append("containers_discoverable")
        
        # Analyze systemd services
        systemd_services = self.analyze_systemd_services()
        if systemd_services:
            criteria_met.append("systemd_services_present")
            enabled_services = sum(1 for service in systemd_services if service.enabled)
            if enabled_services > 0:
                criteria_met.append("systemd_services_enabled")
            else:
                criteria_missing.append("systemd_services_enabled")
        else:
            criteria_missing.append("systemd_services_present")
        
        # Validate Podman installation
        podman_valid, podman_issues = self.validate_podman_installation()
        all_issues.extend(podman_issues)
        if podman_valid:
            criteria_met.append("podman_installation_valid")
        else:
            criteria_missing.append("podman_installation_valid")
        
        # Calculate completion percentage
        total_criteria = len(criteria_met) + len(criteria_missing)
        completion_percentage = len(criteria_met) / total_criteria if total_criteria > 0 else 0.0
        
        # Calculate quality score based on issues
        quality_score = max(0.0, 1.0 - (len([i for i in all_issues if i.severity in [Priority.CRITICAL, Priority.HIGH]]) * 0.2))
        
        return EvaluationResult(
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion_percentage,
            quality_score=quality_score,
            issues=all_issues
        )