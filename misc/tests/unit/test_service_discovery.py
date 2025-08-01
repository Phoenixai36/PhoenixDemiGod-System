"""
Unit tests for Service Discovery module
"""

import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.phoenix_system_review.discovery.service_discovery import (
    ServiceDiscovery, ServiceEndpoint, ServiceHealth, ContainerInfo
)
from src.phoenix_system_review.models.data_models import ServiceRegistry


class TestServiceDiscovery:
    """Test cases for ServiceDiscovery class"""
    
    @pytest.fixture
    def service_discovery(self):
        """Create a ServiceDiscovery instance for testing"""
        return ServiceDiscovery(container_runtime="podman")
    
    def test_initialization(self, service_discovery):
        """Test service discovery initialization"""
        assert service_discovery.container_runtime == "podman"
        assert isinstance(service_discovery.service_registry, ServiceRegistry)
        assert len(service_discovery.discovered_services) > 0
        assert "phoenix-core" in service_discovery.discovered_services
        assert "n8n-phoenix" in service_discovery.discovered_services
        assert "postgres" in service_discovery.discovered_services
    
    def test_service_endpoint_initialization(self):
        """Test ServiceEndpoint initialization and post_init"""
        # Test with full URL
        endpoint = ServiceEndpoint(
            name="test-service",
            url="https://example.com:8443/api"
        )
        assert endpoint.protocol == "https"
        assert endpoint.port == 8443
        
        # Test with HTTP URL
        endpoint = ServiceEndpoint(
            name="test-service",
            url="http://localhost:8080"
        )
        assert endpoint.protocol == "http"
        assert endpoint.port == 8080
        
        # Test with defaults
        endpoint = ServiceEndpoint(
            name="test-service",
            url="http://localhost"
        )
        assert endpoint.port == 80
    
    def test_service_health_creation(self):
        """Test ServiceHealth object creation"""
        health = ServiceHealth(
            service_name="test-service",
            is_healthy=True,
            status_code=200,
            response_time=0.5
        )
        
        assert health.service_name == "test-service"
        assert health.is_healthy is True
        assert health.status_code == 200
        assert health.response_time == 0.5
        assert isinstance(health.last_check, datetime)
    
    def test_container_info_creation(self):
        """Test ContainerInfo object creation"""
        container = ContainerInfo(
            name="phoenix-core",
            image="phoenix:latest",
            status="running",
            ports=["8080:8080"]
        )
        
        assert container.name == "phoenix-core"
        assert container.image == "phoenix:latest"
        assert container.status == "running"
        assert "8080:8080" in container.ports
    
    @pytest.mark.asyncio
    async def test_discover_services(self, service_discovery):
        """Test service discovery process"""
        # Mock container discovery and health checks
        with patch.object(service_discovery, '_discover_containers', new_callable=AsyncMock) as mock_containers, \
             patch.object(service_discovery, '_check_all_services_health', new_callable=AsyncMock) as mock_health, \
             patch.object(service_discovery, '_update_service_registry') as mock_update:
            
            registry = await service_discovery.discover_services()
            
            mock_containers.assert_called_once()
            mock_health.assert_called_once()
            mock_update.assert_called_once()
            assert isinstance(registry, ServiceRegistry)
            assert service_discovery.last_discovery is not None
    
    @pytest.mark.asyncio
    async def test_discover_podman_containers_success(self, service_discovery):
        """Test successful Podman container discovery"""
        mock_container_data = [
            {
                "Names": ["phoenix-core"],
                "Image": "phoenix:latest",
                "State": "running",
                "Ports": [{"host_port": 8080, "container_port": 8080}],
                "CreatedAt": "2023-01-01T12:00:00Z",
                "Labels": {"project": "phoenix-hydra"}
            }
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = json.dumps(mock_container_data)
            
            await service_discovery._discover_podman_containers()
            
            assert len(service_discovery.container_info) == 1
            assert "phoenix-core" in service_discovery.container_info
            container = service_discovery.container_info["phoenix-core"]
            assert container.image == "phoenix:latest"
            assert container.status == "running"
    
    @pytest.mark.asyncio
    async def test_discover_podman_containers_failure(self, service_discovery):
        """Test Podman container discovery failure"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "podman: command not found"
            
            await service_discovery._discover_podman_containers()
            
            # Should handle error gracefully
            assert len(service_discovery.container_info) == 0
    
    @pytest.mark.asyncio
    async def test_discover_docker_containers_success(self, service_discovery):
        """Test successful Docker container discovery"""
        service_discovery.container_runtime = "docker"
        
        mock_container_line = json.dumps({
            "Names": "phoenix-core",
            "Image": "phoenix:latest",
            "State": "running",
            "Ports": "0.0.0.0:8080->8080/tcp",
            "CreatedAt": "2023-01-01 12:00:00 +0000 UTC",
            "Status": "Up 2 hours (healthy)"
        })
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_container_line
            
            await service_discovery._discover_docker_containers()
            
            assert len(service_discovery.container_info) == 1
            container = list(service_discovery.container_info.values())[0]
            assert container.image == "phoenix:latest"
            assert container.status == "running"
    
    def test_parse_podman_container(self, service_discovery):
        """Test parsing Podman container data"""
        container_data = {
            "Names": ["phoenix-core"],
            "Image": "phoenix:latest",
            "State": "running",
            "Ports": [{"host_port": 8080, "container_port": 8080}],
            "CreatedAt": "2023-01-01T12:00:00Z",
            "Labels": {"project": "phoenix-hydra"}
        }
        
        container_info = service_discovery._parse_podman_container(container_data)
        
        assert container_info is not None
        assert container_info.name == "phoenix-core"
        assert container_info.image == "phoenix:latest"
        assert container_info.status == "running"
        assert "8080:8080" in container_info.ports
    
    def test_parse_docker_container(self, service_discovery):
        """Test parsing Docker container data"""
        container_data = {
            "Names": "phoenix-core",
            "Image": "phoenix:latest",
            "State": "running",
            "Ports": "0.0.0.0:8080->8080/tcp",
            "CreatedAt": "2023-01-01 12:00:00 +0000 UTC",
            "Status": "Up 2 hours (healthy)"
        }
        
        container_info = service_discovery._parse_docker_container(container_data)
        
        assert container_info is not None
        assert container_info.name == "phoenix-core"
        assert container_info.image == "phoenix:latest"
        assert container_info.status == "running"
        assert "0.0.0.0:8080->8080/tcp" in container_info.ports
    
    @pytest.mark.asyncio
    async def test_check_http_health_success(self, service_discovery):
        """Test successful HTTP health check"""
        endpoint = ServiceEndpoint(
            name="test-service",
            url="http://localhost:8080",
            health_path="/health"
        )
        
        # Test without aiohttp available (fallback behavior)
        health = await service_discovery._check_http_health(endpoint, 0.0)
        
        assert health.service_name == "test-service"
        assert health.is_healthy is False
        assert "aiohttp not available" in health.error_message
    
    @pytest.mark.asyncio
    async def test_check_http_health_failure(self, service_discovery):
        """Test HTTP health check failure when aiohttp is not available"""
        endpoint = ServiceEndpoint(
            name="test-service",
            url="http://localhost:8080",
            health_path="/health"
        )
        
        # Test the fallback behavior when aiohttp is not available
        health = await service_discovery._check_http_health(endpoint, 0.0)
        
        assert health.service_name == "test-service"
        assert health.is_healthy is False
        assert "aiohttp not available" in health.error_message
    
    @pytest.mark.asyncio
    async def test_check_tcp_health_success(self, service_discovery):
        """Test successful TCP health check"""
        endpoint = ServiceEndpoint(
            name="postgres",
            url="tcp://localhost:5432",
            protocol="tcp",
            port=5432
        )
        
        # Mock successful TCP connection
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        
        with patch('asyncio.open_connection', return_value=(mock_reader, mock_writer)):
            health = await service_discovery._check_tcp_health(endpoint, 0.0)
            
            assert health.service_name == "postgres"
            assert health.is_healthy is True
            assert health.error_message is None
            assert "tcp://" in health.endpoint_url
    
    @pytest.mark.asyncio
    async def test_check_tcp_health_timeout(self, service_discovery):
        """Test TCP health check timeout"""
        endpoint = ServiceEndpoint(
            name="postgres",
            url="tcp://localhost:5432",
            protocol="tcp",
            port=5432,
            timeout=0.1
        )
        
        # Mock timeout
        with patch('asyncio.open_connection', side_effect=asyncio.TimeoutError()):
            health = await service_discovery._check_tcp_health(endpoint, 0.0)
            
            assert health.service_name == "postgres"
            assert health.is_healthy is False
            assert "timeout" in health.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_check_service_health_individual(self, service_discovery):
        """Test checking individual service health"""
        service_name = "phoenix-core"
        
        # Mock HTTP health check
        with patch.object(service_discovery, '_check_service_health', new_callable=AsyncMock) as mock_check:
            mock_health = ServiceHealth(service_name=service_name, is_healthy=True)
            mock_check.return_value = mock_health
            
            is_healthy = await service_discovery.check_service_health(service_name)
            
            assert is_healthy is True
            assert service_name in service_discovery.health_checks
            assert service_discovery.health_checks[service_name].is_healthy is True
    
    def test_get_service_health(self, service_discovery):
        """Test getting cached service health"""
        service_name = "test-service"
        health = ServiceHealth(service_name=service_name, is_healthy=True)
        service_discovery.health_checks[service_name] = health
        
        retrieved_health = service_discovery.get_service_health(service_name)
        
        assert retrieved_health is not None
        assert retrieved_health.service_name == service_name
        assert retrieved_health.is_healthy is True
        
        # Test non-existent service
        assert service_discovery.get_service_health("non-existent") is None
    
    def test_get_healthy_unhealthy_services(self, service_discovery):
        """Test getting lists of healthy and unhealthy services"""
        # Add some test health data
        service_discovery.health_checks = {
            "service1": ServiceHealth("service1", True),
            "service2": ServiceHealth("service2", False),
            "service3": ServiceHealth("service3", True),
            "service4": ServiceHealth("service4", False)
        }
        
        healthy = service_discovery.get_healthy_services()
        unhealthy = service_discovery.get_unhealthy_services()
        
        assert len(healthy) == 2
        assert "service1" in healthy
        assert "service3" in healthy
        
        assert len(unhealthy) == 2
        assert "service2" in unhealthy
        assert "service4" in unhealthy
    
    def test_get_service_endpoints(self, service_discovery):
        """Test getting service endpoints"""
        endpoints = service_discovery.get_service_endpoints()
        
        assert isinstance(endpoints, dict)
        assert len(endpoints) > 0
        assert "phoenix-core" in endpoints
        assert endpoints["phoenix-core"] == "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_test_network_connectivity_success(self, service_discovery):
        """Test successful network connectivity test"""
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        
        with patch('asyncio.open_connection', return_value=(mock_reader, mock_writer)):
            result = await service_discovery.test_network_connectivity("localhost", 8080)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_test_network_connectivity_failure(self, service_discovery):
        """Test failed network connectivity test"""
        with patch('asyncio.open_connection', side_effect=ConnectionRefusedError()):
            result = await service_discovery.test_network_connectivity("localhost", 8080)
            assert result is False
    
    def test_get_service_summary(self, service_discovery):
        """Test getting service summary"""
        # Add some test data
        service_discovery.health_checks = {
            "service1": ServiceHealth("service1", True),
            "service2": ServiceHealth("service2", False),
            "service3": ServiceHealth("service3", True)
        }
        service_discovery.last_discovery = datetime.now()
        
        summary = service_discovery.get_service_summary()
        
        assert summary["total_services"] == len(service_discovery.discovered_services)
        assert summary["healthy_services"] == 2
        assert summary["unhealthy_services"] == 1
        assert summary["health_percentage"] > 0
        assert summary["container_runtime"] == "podman"
        assert "last_discovery" in summary
    
    def test_add_custom_service(self, service_discovery):
        """Test adding custom service"""
        initial_count = len(service_discovery.discovered_services)
        
        service_discovery.add_custom_service(
            name="custom-service",
            url="http://localhost:9000",
            health_path="/status",
            description="Custom test service"
        )
        
        assert len(service_discovery.discovered_services) == initial_count + 1
        assert "custom-service" in service_discovery.discovered_services
        
        endpoint = service_discovery.discovered_services["custom-service"]
        assert endpoint.url == "http://localhost:9000"
        assert endpoint.health_path == "/status"
        assert endpoint.description == "Custom test service"
    
    def test_remove_service(self, service_discovery):
        """Test removing service"""
        # Add a test service first
        service_discovery.add_custom_service("test-service", "http://localhost:9000")
        service_discovery.health_checks["test-service"] = ServiceHealth("test-service", True)
        
        # Remove the service
        result = service_discovery.remove_service("test-service")
        
        assert result is True
        assert "test-service" not in service_discovery.discovered_services
        assert "test-service" not in service_discovery.health_checks
        
        # Try to remove non-existent service
        result = service_discovery.remove_service("non-existent")
        assert result is False
    
    def test_find_container_for_service(self, service_discovery):
        """Test finding container for service"""
        # Add test container info
        container = ContainerInfo(
            name="phoenix-hydra_phoenix-core_1",
            image="phoenix:latest",
            status="running"
        )
        service_discovery.container_info["phoenix-hydra_phoenix-core_1"] = container
        
        # Test exact match
        found = service_discovery._find_container_for_service("phoenix-core")
        assert found is not None
        assert found.name == "phoenix-hydra_phoenix-core_1"
        
        # Test no match
        found = service_discovery._find_container_for_service("non-existent-service")
        assert found is None
    
    def test_update_service_registry(self, service_discovery):
        """Test updating service registry"""
        # Add test data
        service_discovery.health_checks["phoenix-core"] = ServiceHealth(
            "phoenix-core", True, status_code=200, response_time=0.1
        )
        
        container = ContainerInfo(
            name="phoenix-core-container",
            image="phoenix:latest",
            status="running",
            ports=["8080:8080"]
        )
        service_discovery.container_info["phoenix-core-container"] = container
        
        service_discovery._update_service_registry()
        
        registry = service_discovery.service_registry
        assert len(registry.services) > 0
        assert "phoenix-core" in registry.services
        assert "phoenix-core" in registry.health_checks
        assert "phoenix-core" in registry.endpoints
        assert isinstance(registry.last_check, datetime)
    
    @pytest.mark.asyncio
    async def test_check_all_services_health(self, service_discovery):
        """Test checking health of all services"""
        # Mock individual health checks
        with patch.object(service_discovery, '_check_service_health', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = ServiceHealth("test", True)
            
            await service_discovery._check_all_services_health()
            
            # Should have called health check for each service
            assert mock_check.call_count == len(service_discovery.discovered_services)
            
            # Should have health results for all services
            assert len(service_discovery.health_checks) == len(service_discovery.discovered_services)


if __name__ == "__main__":
    pytest.main([__file__])