"""
Service Discovery module for Phoenix Hydra System Review Tool

Provides health check functionality for Phoenix Hydra services, service registry
and status tracking, and network connectivity testing for service endpoints.
"""

import asyncio
import socket
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Optional aiohttp import for HTTP health checks
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False

from ..models.data_models import ServiceRegistry, ComponentStatus, Issue, Priority


@dataclass
class ServiceEndpoint:
    """Information about a service endpoint"""
    name: str
    url: str
    health_path: str = "/health"
    expected_status: int = 200
    timeout: float = 5.0
    protocol: str = "http"
    port: int = 80
    description: Optional[str] = None
    
    def __post_init__(self):
        """Extract port and protocol from URL if not provided"""
        if self.url:
            parsed = urlparse(self.url)
            if parsed.scheme and self.protocol == "http":  # Only update if default
                self.protocol = parsed.scheme
            if parsed.port and self.port in [80, 443]:  # Only update if default
                self.port = parsed.port
            elif not parsed.port and self.port in [80, 443]:
                self.port = 443 if self.protocol == "https" else 80


@dataclass
class ServiceHealth:
    """Health status information for a service"""
    service_name: str
    is_healthy: bool
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)
    endpoint_url: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContainerInfo:
    """Information about a container"""
    name: str
    image: str
    status: str
    ports: List[str] = field(default_factory=list)
    health_status: Optional[str] = None
    created: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)


class ServiceDiscovery:
    """
    Service discovery and health checking for Phoenix Hydra services.
    
    Provides functionality to discover running services, check their health status,
    test network connectivity, and maintain a service registry.
    """
    
    # Phoenix Hydra service definitions
    PHOENIX_SERVICES = {
        "phoenix-core": {
            "url": "http://localhost:8080",
            "health_path": "/health",
            "description": "Phoenix Core API service"
        },
        "nca-toolkit": {
            "url": "http://localhost:8081", 
            "health_path": "/health",
            "description": "NCA Toolkit multimedia processing service"
        },
        "n8n-phoenix": {
            "url": "http://localhost:5678",
            "health_path": "/healthz",
            "description": "n8n workflow automation service"
        },
        "windmill": {
            "url": "http://localhost:8000",
            "health_path": "/api/version",
            "description": "Windmill GitOps workflow service"
        },
        "postgres": {
            "url": "http://localhost:5432",
            "health_path": None,  # Database connection check
            "description": "PostgreSQL database service",
            "protocol": "tcp"
        },
        "minio": {
            "url": "http://localhost:9000",
            "health_path": "/minio/health/live",
            "description": "MinIO S3-compatible object storage"
        },
        "prometheus": {
            "url": "http://localhost:9090",
            "health_path": "/-/healthy",
            "description": "Prometheus metrics collection service"
        },
        "grafana": {
            "url": "http://localhost:3000",
            "health_path": "/api/health",
            "description": "Grafana monitoring dashboard"
        }
    }
    
    def __init__(self, container_runtime: str = "podman"):
        """
        Initialize the service discovery module.
        
        Args:
            container_runtime: Container runtime to use ("podman" or "docker")
        """
        self.container_runtime = container_runtime
        self.service_registry = ServiceRegistry()
        self.discovered_services: Dict[str, ServiceEndpoint] = {}
        self.health_checks: Dict[str, ServiceHealth] = {}
        self.container_info: Dict[str, ContainerInfo] = {}
        self.last_discovery: Optional[datetime] = None
        
        # Initialize service endpoints
        self._initialize_service_endpoints()
    
    def _initialize_service_endpoints(self) -> None:
        """Initialize service endpoints from Phoenix service definitions"""
        for service_name, config in self.PHOENIX_SERVICES.items():
            endpoint = ServiceEndpoint(
                name=service_name,
                url=config["url"],
                health_path=config.get("health_path", "/health"),
                description=config.get("description"),
                protocol=config.get("protocol", "http")
            )
            self.discovered_services[service_name] = endpoint
    
    async def discover_services(self) -> ServiceRegistry:
        """
        Discover all Phoenix Hydra services and their status.
        
        Returns:
            ServiceRegistry with discovered services and their health status
        """
        print("Discovering Phoenix Hydra services...")
        
        # Discover containers
        await self._discover_containers()
        
        # Check service health
        await self._check_all_services_health()
        
        # Update service registry
        self._update_service_registry()
        
        self.last_discovery = datetime.now()
        return self.service_registry
    
    async def _discover_containers(self) -> None:
        """Discover running containers using the configured container runtime"""
        try:
            if self.container_runtime == "podman":
                await self._discover_podman_containers()
            else:
                await self._discover_docker_containers()
        except Exception as e:
            print(f"Error discovering containers: {e}")
    
    async def _discover_podman_containers(self) -> None:
        """Discover containers using Podman"""
        try:
            # Get container list in JSON format
            result = subprocess.run(
                ["podman", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                containers_data = json.loads(result.stdout)
                for container_data in containers_data:
                    container_info = self._parse_podman_container(container_data)
                    if container_info:
                        self.container_info[container_info.name] = container_info
            else:
                print(f"Podman command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Podman command timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Podman JSON output: {e}")
        except FileNotFoundError:
            print("Podman not found. Is it installed?")
        except Exception as e:
            print(f"Error running Podman command: {e}")
    
    async def _discover_docker_containers(self) -> None:
        """Discover containers using Docker"""
        try:
            # Get container list in JSON format
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Docker ps --format json returns one JSON object per line
                for line in result.stdout.strip().split('\n'):
                    if line:
                        container_data = json.loads(line)
                        container_info = self._parse_docker_container(container_data)
                        if container_info:
                            self.container_info[container_info.name] = container_info
            else:
                print(f"Docker command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Docker command timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Docker JSON output: {e}")
        except FileNotFoundError:
            print("Docker not found. Is it installed?")
        except Exception as e:
            print(f"Error running Docker command: {e}")
    
    def _parse_podman_container(self, container_data: Dict[str, Any]) -> Optional[ContainerInfo]:
        """Parse Podman container data into ContainerInfo"""
        try:
            # Extract port mappings
            ports = []
            if "Ports" in container_data and container_data["Ports"]:
                for port_info in container_data["Ports"]:
                    if "host_port" in port_info and "container_port" in port_info:
                        ports.append(f"{port_info['host_port']}:{port_info['container_port']}")
            
            # Parse creation time
            created = None
            if "CreatedAt" in container_data:
                try:
                    created = datetime.fromisoformat(container_data["CreatedAt"].replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            return ContainerInfo(
                name=container_data.get("Names", ["unknown"])[0] if isinstance(container_data.get("Names"), list) else container_data.get("Names", "unknown"),
                image=container_data.get("Image", "unknown"),
                status=container_data.get("State", "unknown"),
                ports=ports,
                health_status=container_data.get("Healthcheck", {}).get("Status"),
                created=created,
                labels=container_data.get("Labels", {})
            )
        except Exception as e:
            print(f"Error parsing Podman container data: {e}")
            return None
    
    def _parse_docker_container(self, container_data: Dict[str, Any]) -> Optional[ContainerInfo]:
        """Parse Docker container data into ContainerInfo"""
        try:
            # Extract port mappings from Ports field
            ports = []
            ports_str = container_data.get("Ports", "")
            if ports_str:
                # Parse port mappings like "0.0.0.0:8080->8080/tcp"
                port_parts = ports_str.split(", ")
                for port_part in port_parts:
                    if "->" in port_part:
                        ports.append(port_part.strip())
            
            # Parse creation time
            created = None
            created_str = container_data.get("CreatedAt", "")
            if created_str:
                try:
                    # Docker format: "2023-01-01 12:00:00 +0000 UTC"
                    created = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S %z %Z")
                except ValueError:
                    pass
            
            return ContainerInfo(
                name=container_data.get("Names", "unknown"),
                image=container_data.get("Image", "unknown"),
                status=container_data.get("State", "unknown"),
                ports=ports,
                health_status=container_data.get("Status", "").split("(")[1].split(")")[0] if "(" in container_data.get("Status", "") else None,
                created=created,
                labels={}  # Docker ps --format json doesn't include labels by default
            )
        except Exception as e:
            print(f"Error parsing Docker container data: {e}")
            return None
    
    async def _check_all_services_health(self) -> None:
        """Check health of all discovered services"""
        health_check_tasks = []
        
        for service_name, endpoint in self.discovered_services.items():
            task = asyncio.create_task(self._check_service_health(endpoint))
            health_check_tasks.append(task)
        
        # Wait for all health checks to complete
        health_results = await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(health_results):
            service_name = list(self.discovered_services.keys())[i]
            if isinstance(result, ServiceHealth):
                self.health_checks[service_name] = result
            elif isinstance(result, Exception):
                # Create failed health check
                self.health_checks[service_name] = ServiceHealth(
                    service_name=service_name,
                    is_healthy=False,
                    error_message=str(result)
                )
    
    async def _check_service_health(self, endpoint: ServiceEndpoint) -> ServiceHealth:
        """
        Check health of a single service endpoint.
        
        Args:
            endpoint: Service endpoint to check
            
        Returns:
            ServiceHealth object with health status
        """
        start_time = time.time()
        
        try:
            if endpoint.protocol == "tcp" or endpoint.health_path is None:
                # TCP connection check (for databases)
                return await self._check_tcp_health(endpoint, start_time)
            else:
                # HTTP health check
                return await self._check_http_health(endpoint, start_time)
                
        except Exception as e:
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message=str(e),
                response_time=time.time() - start_time,
                endpoint_url=endpoint.url
            )
    
    async def _check_tcp_health(self, endpoint: ServiceEndpoint, start_time: float) -> ServiceHealth:
        """Check TCP connectivity to a service"""
        try:
            parsed_url = urlparse(endpoint.url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or endpoint.port
            
            # Test TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=endpoint.timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=True,
                response_time=time.time() - start_time,
                endpoint_url=f"tcp://{host}:{port}",
                additional_info={"connection_type": "tcp"}
            )
            
        except asyncio.TimeoutError:
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message="Connection timeout",
                response_time=time.time() - start_time,
                endpoint_url=endpoint.url
            )
        except Exception as e:
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message=f"TCP connection failed: {str(e)}",
                response_time=time.time() - start_time,
                endpoint_url=endpoint.url
            )
    
    async def _check_http_health(self, endpoint: ServiceEndpoint, start_time: float) -> ServiceHealth:
        """Check HTTP health endpoint"""
        if not AIOHTTP_AVAILABLE:
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message="aiohttp not available for HTTP health checks",
                response_time=time.time() - start_time,
                endpoint_url=endpoint.url
            )
        
        health_url = endpoint.url.rstrip('/') + endpoint.health_path
        
        try:
            timeout = aiohttp.ClientTimeout(total=endpoint.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(health_url) as response:
                    response_time = time.time() - start_time
                    
                    # Try to get response body for additional info
                    additional_info = {}
                    try:
                        if response.content_type == 'application/json':
                            additional_info = await response.json()
                        else:
                            text = await response.text()
                            if len(text) < 1000:  # Only store short responses
                                additional_info["response_body"] = text
                    except:
                        pass  # Ignore response parsing errors
                    
                    return ServiceHealth(
                        service_name=endpoint.name,
                        is_healthy=response.status == endpoint.expected_status,
                        status_code=response.status,
                        response_time=response_time,
                        endpoint_url=health_url,
                        additional_info=additional_info,
                        error_message=None if response.status == endpoint.expected_status else f"Unexpected status code: {response.status}"
                    )
                    
        except asyncio.TimeoutError:
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message="Request timeout",
                response_time=time.time() - start_time,
                endpoint_url=health_url
            )
        except Exception as e:
            # Handle both aiohttp.ClientError and other exceptions
            return ServiceHealth(
                service_name=endpoint.name,
                is_healthy=False,
                error_message=f"HTTP health check failed: {str(e)}",
                response_time=time.time() - start_time,
                endpoint_url=health_url
            )
    
    def _update_service_registry(self) -> None:
        """Update the service registry with discovered services and health status"""
        services = {}
        health_checks = {}
        endpoints = {}
        
        for service_name, endpoint in self.discovered_services.items():
            # Service information
            services[service_name] = {
                "url": endpoint.url,
                "description": endpoint.description,
                "protocol": endpoint.protocol,
                "port": endpoint.port,
                "health_path": endpoint.health_path
            }
            
            # Add container information if available
            container_info = self._find_container_for_service(service_name)
            if container_info:
                services[service_name].update({
                    "container_name": container_info.name,
                    "container_image": container_info.image,
                    "container_status": container_info.status,
                    "container_ports": container_info.ports,
                    "container_health": container_info.health_status
                })
            
            # Health check results
            health = self.health_checks.get(service_name)
            if health:
                health_checks[service_name] = health.is_healthy
                services[service_name].update({
                    "last_health_check": health.last_check.isoformat(),
                    "response_time": health.response_time,
                    "status_code": health.status_code,
                    "health_error": health.error_message
                })
            else:
                health_checks[service_name] = False
            
            # Endpoint URLs
            endpoints[service_name] = endpoint.url
        
        # Update service registry
        self.service_registry.services = services
        self.service_registry.health_checks = health_checks
        self.service_registry.endpoints = endpoints
        self.service_registry.last_check = datetime.now()
    
    def _find_container_for_service(self, service_name: str) -> Optional[ContainerInfo]:
        """Find container information for a service"""
        # Try exact match first
        for container_name, container_info in self.container_info.items():
            if service_name in container_name.lower() or container_name.lower() in service_name:
                return container_info
        
        # Try partial matches
        service_keywords = service_name.replace("-", "_").split("_")
        for container_name, container_info in self.container_info.items():
            container_name_lower = container_name.lower()
            if any(keyword in container_name_lower for keyword in service_keywords):
                return container_info
        
        return None
    
    async def check_service_health(self, service_name: str) -> bool:
        """
        Check health of a specific service.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is healthy, False otherwise
        """
        if service_name not in self.discovered_services:
            return False
        
        endpoint = self.discovered_services[service_name]
        health = await self._check_service_health(endpoint)
        self.health_checks[service_name] = health
        
        return health.is_healthy
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """
        Get cached health information for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            ServiceHealth object or None if not found
        """
        return self.health_checks.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """
        Get health information for all services.
        
        Returns:
            Dictionary mapping service names to ServiceHealth objects
        """
        return self.health_checks.copy()
    
    def get_healthy_services(self) -> List[str]:
        """
        Get list of healthy service names.
        
        Returns:
            List of service names that are currently healthy
        """
        return [name for name, health in self.health_checks.items() if health.is_healthy]
    
    def get_unhealthy_services(self) -> List[str]:
        """
        Get list of unhealthy service names.
        
        Returns:
            List of service names that are currently unhealthy
        """
        return [name for name, health in self.health_checks.items() if not health.is_healthy]
    
    def get_service_endpoints(self) -> Dict[str, str]:
        """
        Get all service endpoints.
        
        Returns:
            Dictionary mapping service names to endpoint URLs
        """
        return {name: endpoint.url for name, endpoint in self.discovered_services.items()}
    
    async def test_network_connectivity(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """
        Test network connectivity to a specific host and port.
        
        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    def get_service_summary(self) -> Dict[str, Any]:
        """
        Get a summary of service discovery results.
        
        Returns:
            Dictionary with service discovery summary
        """
        total_services = len(self.discovered_services)
        healthy_services = len(self.get_healthy_services())
        unhealthy_services = len(self.get_unhealthy_services())
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "last_discovery": self.last_discovery.isoformat() if self.last_discovery else None,
            "container_runtime": self.container_runtime,
            "discovered_containers": len(self.container_info)
        }
    
    def add_custom_service(self, name: str, url: str, health_path: str = "/health", 
                          description: str = None) -> None:
        """
        Add a custom service to monitor.
        
        Args:
            name: Service name
            url: Service URL
            health_path: Health check endpoint path
            description: Service description
        """
        endpoint = ServiceEndpoint(
            name=name,
            url=url,
            health_path=health_path,
            description=description
        )
        self.discovered_services[name] = endpoint
    
    def remove_service(self, name: str) -> bool:
        """
        Remove a service from monitoring.
        
        Args:
            name: Service name to remove
            
        Returns:
            True if service was removed, False if not found
        """
        if name in self.discovered_services:
            del self.discovered_services[name]
            if name in self.health_checks:
                del self.health_checks[name]
            return True
        return False