"""
Tests for Podman client.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.containers.podman_client import (
    PodmanClient, PodmanConfig, PodmanAPIError
)
from src.containers.models import Container, ContainerStatus, ContainerStats, ContainerEvent


class TestPodmanConfig:
    """Test cases for PodmanConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PodmanConfig()
        
        assert config.socket_path is None
        assert config.remote_url is None
        assert config.api_version == "v4.0.0"
        assert config.auto_detect is True
        assert config.fallback_to_docker is True
        assert config.connect_timeout == 10.0
        assert config.request_timeout == 30.0
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = PodmanConfig(
            socket_path="/custom/socket",
            remote_url="http://remote:8080",
            api_version="v3.0.0",
            connect_timeout=5.0,
            auto_detect=False
        )
        
        assert config.socket_path == "/custom/socket"
        assert config.remote_url == "http://remote:8080"
        assert config.api_version == "v3.0.0"
        assert config.connect_timeout == 5.0
        assert config.auto_detect is False


class TestPodmanClient:
    """Test cases for PodmanClient."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return PodmanConfig(
            socket_path="/test/socket",
            auto_detect=False,
            fallback_to_docker=False
        )
    
    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return PodmanClient(config)
    
    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock()
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={"test": "data"})
        response.text = AsyncMock(return_value="test response")
        response.content_type = "application/json"
        session.request.return_value.__aenter__.return_value = response
        return session
    
    def test_client_creation(self, client, config):
        """Test client creation."""
        assert client.config == config
        assert client._session is None
        assert client._base_url is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager."""
        with patch.object(client, 'connect') as mock_connect, \
             patch.object(client, 'close') as mock_close:
            
            async with client:
                mock_connect.assert_called_once()
            
            mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_with_socket(self, client):
        """Test connection with socket path."""
        with patch('os.path.exists', return_value=True), \
             patch('aiohttp.ClientSession') as mock_session_class, \
             patch.object(client, 'get_version', return_value={"version": "4.0.0"}):
            
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            await client.connect()
            
            assert client._base_url == "http://localhost/v4.0.0/libpod"
            assert client._session == mock_session
    
    @pytest.mark.asyncio
    async def test_connect_failure_with_fallback(self):
        """Test connection failure with Docker fallback."""
        config = PodmanConfig(fallback_to_docker=True, auto_detect=False)
        client = PodmanClient(config)
        
        with patch('os.path.exists', return_value=False), \
             patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('aiohttp.ClientSession') as mock_session_class:
            
            # Mock Docker version check
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Docker version 20.10.0", b"")
            mock_subprocess.return_value = mock_process
            
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock get_version to fail first (Podman) then succeed (Docker)
            with patch.object(client, 'get_version', side_effect=[
                PodmanAPIError("Connection failed"), 
                {"version": "1.41"}
            ]):
                await client.connect()
                
                assert "/var/run/docker.sock" in client.config.socket_path
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, client):
        """Test successful API request."""
        client._session = AsyncMock()
        client._base_url = "http://test"
        
        response = AsyncMock()
        response.status = 200
        response.json = AsyncMock(return_value={"result": "success"})
        response.content_type = "application/json"
        client._session.request.return_value.__aenter__.return_value = response
        
        result = await client._make_request("GET", "/test")
        
        assert result == {"result": "success"}
        client._session.request.assert_called_once_with("GET", "http://test/test")
    
    @pytest.mark.asyncio
    async def test_make_request_error(self, client):
        """Test API request error."""
        client._session = AsyncMock()
        client._base_url = "http://test"
        
        response = AsyncMock()
        response.status = 404
        response.text = AsyncMock(return_value='{"message": "Not found"}')
        client._session.request.return_value.__aenter__.return_value = response
        
        with pytest.raises(PodmanAPIError) as exc_info:
            await client._make_request("GET", "/test")
        
        assert exc_info.value.status_code == 404
        assert "Not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_version(self, client):
        """Test get version."""
        with patch.object(client, '_make_request', return_value={"version": "4.0.0"}):
            result = await client.get_version()
            assert result == {"version": "4.0.0"}
    
    @pytest.mark.asyncio
    async def test_list_containers(self, client):
        """Test list containers."""
        container_data = [{
            "Id": "abc123",
            "Names": ["/test-container"],
            "Image": "nginx:latest",
            "State": "running",
            "Created": 1600000000,
            "Ports": [{"PrivatePort": 80, "PublicPort": 8080, "Type": "tcp"}],
            "Labels": {"app": "test"}
        }]
        
        with patch.object(client, '_make_request', return_value=container_data):
            containers = await client.list_containers()
            
            assert len(containers) == 1
            container = containers[0]
            assert container.id == "abc123"
            assert container.name == "test-container"
            assert container.image == "nginx:latest"
            assert container.status == ContainerStatus.RUNNING
            assert "8080:80/tcp" in container.ports
            assert container.labels["app"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_container(self, client):
        """Test get container details."""
        container_data = {
            "Id": "abc123",
            "Name": "test-container",
            "Config": {"Image": "nginx:latest"},
            "State": {"Status": "running", "StartedAt": "2023-01-01T00:00:00Z"},
            "NetworkSettings": {"Ports": {"80/tcp": [{"HostPort": "8080"}]}},
            "Config": {"Labels": {"app": "test"}}
        }
        
        with patch.object(client, '_make_request', return_value=container_data):
            container = await client.get_container("abc123")
            
            assert container.id == "abc123"
    
    @pytest.mark.asyncio
    async def test_container_operations(self, client):
        """Test container start/stop/restart operations."""
        with patch.object(client, '_make_request', return_value={}):
            # Test start
            result = await client.start_container("abc123")
            assert result is True
            
            # Test stop
            result = await client.stop_container("abc123", timeout=5)
            assert result is True
            
            # Test restart
            result = await client.restart_container("abc123", timeout=5)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_container_stats(self, client):
        """Test container statistics."""
        stats_data = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000},
                "system_cpu_usage": 10000000
            },
            "memory_stats": {
                "usage": 1024000,
                "limit": 2048000
            },
            "networks": {
                "eth0": {"rx_bytes": 1000, "tx_bytes": 2000}
            },
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "Read", "value": 1024},
                    {"op": "Write", "value": 2048}
                ]
            }
        }
        
        with patch.object(client, '_make_request', return_value=stats_data):
            stats = await client.get_container_stats("abc123")
            
            assert isinstance(stats, ContainerStats)
            assert stats.cpu_percent == 10.0  # 1000000 / 10000000 * 100
            assert stats.memory_usage_bytes == 1024000
            assert stats.memory_percent == 50.0  # 1024000 / 2048000 * 100
            assert stats.network_rx_bytes == 1000
            assert stats.network_tx_bytes == 2000
            assert stats.block_read_bytes == 1024
            assert stats.block_write_bytes == 2048
    
    @pytest.mark.asyncio
    async def test_get_logs(self, client):
        """Test get container logs."""
        with patch.object(client, '_make_request', return_value={"data": "log line 1\nlog line 2"}):
            logs = await client.get_container_logs("abc123", tail=10)
            
            assert logs == "log line 1\nlog line 2"
    
    @pytest.mark.asyncio
    async def test_list_pods(self, client):
        """Test list pods (Podman-specific)."""
        pods_data = [
            {"Id": "pod123", "Name": "test-pod", "Status": "Running"}
        ]
        
        with patch.object(client, '_make_request', return_value=pods_data):
            pods = await client.list_pods()
            
            assert len(pods) == 1
            assert pods[0]["Name"] == "test-pod"
    
    @pytest.mark.asyncio
    async def test_parse_container_data(self, client):
        """Test container data parsing."""
        data = {
            "Id": "abc123def456",
            "Names": ["/test-container"],
            "Image": "nginx:latest",
            "State": "running",
            "Created": 1600000000,
            "Ports": [
                {"PrivatePort": 80, "PublicPort": 8080, "Type": "tcp"},
                {"PrivatePort": 443, "Type": "tcp"}
            ],
            "Labels": {"app": "test", "version": "1.0"}
        }
        
        container = client._parse_container_data(data)
        
        assert container.id == "abc123def456"
        assert container.name == "test-container"
        assert container.image == "nginx:latest"
        assert container.status == ContainerStatus.RUNNING
        assert container.created_at == datetime.fromtimestamp(1600000000)
        assert "8080:80/tcp" in container.ports
        assert "443/tcp" in container.ports
        assert container.labels["app"] == "test"
        assert container.labels["version"] == "1.0"
    
    @pytest.mark.asyncio
    async def test_parse_event_data(self, client):
        """Test event data parsing."""
        data = {
            "Type": "container",
            "Action": "start",
            "Actor": {
                "ID": "abc123",
                "Attributes": {
                    "name": "test-container",
                    "image": "nginx:latest"
                }
            },
            "time": 1600000000
        }
        
        event = client._parse_event_data(data)
        
        assert event is not None
        assert event.container_id == "abc123"
        assert event.container_name == "test-container"
        assert event.action == "start"
        assert event.image == "nginx:latest"
        assert event.timestamp == datetime.fromtimestamp(1600000000)
    
    @pytest.mark.asyncio
    async def test_parse_event_data_non_container(self, client):
        """Test event data parsing for non-container events."""
        data = {
            "Type": "image",
            "Action": "pull",
            "Actor": {"ID": "image123"}
        }
        
        event = client._parse_event_data(data)
        assert event is None  # Should ignore non-container events
    
    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close."""
        mock_session = AsyncMock()
        client._session = mock_session
        
        await client.close()
        
        mock_session.close.assert_called_once()
        assert client._session is None


class TestPodmanAPIError:
    """Test cases for PodmanAPIError."""
    
    def test_basic_error(self):
        """Test basic error creation."""
        error = PodmanAPIError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data is None
    
    def test_error_with_details(self):
        """Test error with status code and response data."""
        response_data = {"message": "Not found", "code": 404}
        error = PodmanAPIError("Not found", status_code=404, response_data=response_data)
        
        assert str(error) == "Not found"
        assert error.status_code == 404
        assert error.response_data == response_data


@pytest.mark.integration
class TestPodmanClientIntegration:
    """Integration tests for PodmanClient (require actual Podman/Docker)."""
    
    @pytest.fixture
    async def client(self):
        """Create client for integration tests."""
        config = PodmanConfig(auto_detect=True)
        client = PodmanClient(config)
        
        try:
            await client.connect()
            yield client
        except Exception as e:
            pytest.skip(f"Container runtime not available: {str(e)}")
        finally:
            if client:
                await client.close()
    
    @pytest.mark.asyncio
    async def test_real_connection(self, client):
        """Test real connection to container runtime."""
        version = await client.get_version()
        assert "version" in version or "Version" in version
    
    @pytest.mark.asyncio
    async def test_real_list_containers(self, client):
        """Test listing real containers."""
        containers = await client.list_containers()
        assert isinstance(containers, list)
        
        # Each container should be properly parsed
        for container in containers:
            assert isinstance(container, Container)
            assert container.id
            assert container.status in ContainerStatus
    
    @pytest.mark.asyncio
    async def test_real_system_info(self, client):
        """Test getting real system info."""
        info = await client.get_system_info()
        assert isinstance(info, dict)
        # Should contain some system information
        assert len(info) > 0