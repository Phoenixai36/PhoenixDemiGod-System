"""
Podman API client for container management.

This module provides a comprehensive interface to the Podman API,
supporting both local and remote Podman instances.
"""

import asyncio
import json
import logging
import aiohttp
import subprocess
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, field

from .models import Container, ContainerStatus, ContainerEvent, ContainerStats


@dataclass
class PodmanConfig:
    """Configuration for Podman client."""
    # Connection settings
    socket_path: Optional[str] = None  # Unix socket path
    remote_url: Optional[str] = None   # Remote Podman URL
    api_version: str = "v4.0.0"        # Podman API version
    
    # Authentication (for remote connections)
    username: Optional[str] = None
    password: Optional[str] = None
    identity_file: Optional[str] = None  # SSH key file
    
    # Timeouts
    connect_timeout: float = 10.0
    request_timeout: float = 30.0
    
    # Behavior
    auto_detect: bool = True           # Auto-detect Podman installation
    fallback_to_docker: bool = True    # Fallback to Docker if Podman unavailable
    use_cli_fallback: bool = True      # Use CLI if API unavailable


class PodmanAPIError(Exception):
    """Exception raised for Podman API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PodmanClient:
    """
    Podman API client with support for both local and remote connections.
    
    Podman advantages over Docker:
    - Daemonless architecture (no background daemon required)
    - Rootless containers (better security)
    - Pod support (Kubernetes-like pod management)
    - Better systemd integration
    - OCI compliant
    - No single point of failure
    """
    
    def __init__(self, config: PodmanConfig = None):
        self.config = config or PodmanConfig()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url: Optional[str] = None
        self._is_remote = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self) -> None:
        """Establish connection to Podman API."""
        if self._session:
            return
        
        # Auto-detect Podman if enabled
        if self.config.auto_detect:
            await self._auto_detect_podman()
        
        # Determine connection method
        if self.config.remote_url:
            self._base_url = f"{self.config.remote_url}/v{self.config.api_version}/libpod"
            self._is_remote = True
        elif self.config.socket_path:
            self._base_url = f"http://localhost/v{self.config.api_version}/libpod"
        else:
            # Default socket paths
            socket_paths = [
                f"/run/user/{os.getuid()}/podman/podman.sock",  # Rootless
                "/run/podman/podman.sock"  # Rootful
            ]
            
            for socket_path in socket_paths:
                if os.path.exists(socket_path):
                    self.config.socket_path = socket_path
                    self._base_url = f"http://localhost/v{self.config.api_version}/libpod"
                    break
        
        if not self._base_url:
            raise PodmanAPIError("Could not determine Podman API endpoint")
        
        # Create HTTP session
        connector = None
        if self.config.socket_path and not self._is_remote:
            connector = aiohttp.UnixConnector(path=self.config.socket_path)
        
        timeout = aiohttp.ClientTimeout(
            connect=self.config.connect_timeout,
            total=self.config.request_timeout
        )
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Test connection
        try:
            await self.get_version()
            self.logger.info(f"Connected to Podman API at {self._base_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Podman API: {str(e)}")
            if self.config.fallback_to_docker:
                self.logger.info("Attempting to fallback to Docker...")
                await self._setup_docker_fallback()
            else:
                raise PodmanAPIError(f"Failed to connect to Podman: {str(e)}")
    
    async def close(self) -> None:
        """Close the connection."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _auto_detect_podman(self) -> None:
        """Auto-detect Podman installation and configuration."""
        try:
            # Check if podman command is available
            result = await asyncio.create_subprocess_exec(
                "podman", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip()
                self.logger.info(f"Detected Podman: {version}")
                
                # Try to get system info to detect socket
                info_result = await asyncio.create_subprocess_exec(
                    "podman", "system", "info", "--format", "json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                info_stdout, _ = await info_result.communicate()
                
                if info_result.returncode == 0:
                    info = json.loads(info_stdout.decode())
                    # Extract socket information if available
                    if "host" in info and "remoteSocket" in info["host"]:
                        socket_info = info["host"]["remoteSocket"]
                        if socket_info.get("path"):
                            self.config.socket_path = socket_info["path"]
            else:
                self.logger.warning("Podman not found in PATH")
                
        except Exception as e:
            self.logger.warning(f"Failed to auto-detect Podman: {str(e)}")
    
    async def _setup_docker_fallback(self) -> None:
        """Setup Docker as fallback if Podman is unavailable."""
        try:
            # Check if Docker is available
            result = await asyncio.create_subprocess_exec(
                "docker", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.logger.info("Using Docker as fallback")
                # Update configuration for Docker
                self.config.socket_path = "/var/run/docker.sock"
                self._base_url = f"http://localhost/v1.41"  # Docker API version
                
                # Recreate session with Docker socket
                if self._session:
                    await self._session.close()
                
                connector = aiohttp.UnixConnector(path=self.config.socket_path)
                timeout = aiohttp.ClientTimeout(
                    connect=self.config.connect_timeout,
                    total=self.config.request_timeout
                )
                
                self._session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                )
            else:
                raise PodmanAPIError("Neither Podman nor Docker is available")
                
        except Exception as e:
            raise PodmanAPIError(f"Docker fallback failed: {str(e)}")
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Podman API."""
        if not self._session:
            await self.connect()
        
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self._session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    try:
                        error_data = json.loads(error_text)
                    except json.JSONDecodeError:
                        error_data = {"message": error_text}
                    
                    raise PodmanAPIError(
                        f"API request failed: {error_data.get('message', 'Unknown error')}",
                        status_code=response.status,
                        response_data=error_data
                    )
                
                if response.content_type == 'application/json':
                    return await response.json()
                else:
                    return {"data": await response.text()}
                    
        except aiohttp.ClientError as e:
            raise PodmanAPIError(f"Connection error: {str(e)}")
    
    async def get_version(self) -> Dict[str, Any]:
        """Get Podman version information."""
        return await self._make_request("GET", "/version")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return await self._make_request("GET", "/info")
    
    async def list_containers(self, all_containers: bool = True, filters: Optional[Dict[str, str]] = None) -> List[Container]:
        """
        List containers.
        
        Args:
            all_containers: Include stopped containers
            filters: Filter containers (e.g., {"status": "running"})
        """
        params = {"all": str(all_containers).lower()}
        
        if filters:
            # Convert filters to Podman API format
            filter_params = []
            for key, value in filters.items():
                filter_params.append(f"{key}={value}")
            if filter_params:
                params["filters"] = json.dumps({k: [v] for k, v in filters.items()})
        
        response = await self._make_request("GET", "/containers/json", params=params)
        
        containers = []
        for container_data in response:
            container = self._parse_container_data(container_data)
            containers.append(container)
        
        return containers
    
    async def get_container(self, container_id: str) -> Container:
        """Get detailed information about a specific container."""
        response = await self._make_request("GET", f"/containers/{container_id}/json")
        return self._parse_container_data(response)
    
    async def get_container_stats(self, container_id: str, stream: bool = False) -> Union[ContainerStats, AsyncGenerator[ContainerStats, None]]:
        """
        Get container resource usage statistics.
        
        Args:
            container_id: Container ID or name
            stream: If True, return async generator for streaming stats
        """
        if stream:
            return self._stream_container_stats(container_id)
        else:
            params = {"stream": "false"}
            response = await self._make_request("GET", f"/containers/{container_id}/stats", params=params)
            return self._parse_stats_data(response)
    
    async def _stream_container_stats(self, container_id: str) -> AsyncGenerator[ContainerStats, None]:
        """Stream container statistics."""
        if not self._session:
            await self.connect()
        
        url = f"{self._base_url}/containers/{container_id}/stats"
        params = {"stream": "true"}
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status >= 400:
                    raise PodmanAPIError(f"Failed to stream stats: HTTP {response.status}")
                
                async for line in response.content:
                    if line:
                        try:
                            stats_data = json.loads(line.decode().strip())
                            yield self._parse_stats_data(stats_data)
                        except json.JSONDecodeError:
                            continue
                            
        except aiohttp.ClientError as e:
            raise PodmanAPIError(f"Stats streaming error: {str(e)}")
    
    async def start_container(self, container_id: str) -> bool:
        """Start a container."""
        try:
            await self._make_request("POST", f"/containers/{container_id}/start")
            return True
        except PodmanAPIError as e:
            if e.status_code == 304:  # Already started
                return True
            raise
    
    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container."""
        try:
            params = {"t": timeout}
            await self._make_request("POST", f"/containers/{container_id}/stop", params=params)
            return True
        except PodmanAPIError as e:
            if e.status_code == 304:  # Already stopped
                return True
            raise
    
    async def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """Restart a container."""
        params = {"t": timeout}
        await self._make_request("POST", f"/containers/{container_id}/restart", params=params)
        return True
    
    async def remove_container(self, container_id: str, force: bool = False, volumes: bool = False) -> bool:
        """Remove a container."""
        params = {
            "force": str(force).lower(),
            "v": str(volumes).lower()
        }
        await self._make_request("DELETE", f"/containers/{container_id}", params=params)
        return True
    
    async def get_container_logs(self, container_id: str, tail: int = 100, follow: bool = False) -> Union[str, AsyncGenerator[str, None]]:
        """
        Get container logs.
        
        Args:
            container_id: Container ID or name
            tail: Number of lines to return from the end
            follow: If True, return async generator for streaming logs
        """
        params = {
            "stdout": "true",
            "stderr": "true",
            "tail": str(tail)
        }
        
        if follow:
            params["follow"] = "true"
            return self._stream_container_logs(container_id, params)
        else:
            response = await self._make_request("GET", f"/containers/{container_id}/logs", params=params)
            return response.get("data", "")
    
    async def _stream_container_logs(self, container_id: str, params: Dict[str, str]) -> AsyncGenerator[str, None]:
        """Stream container logs."""
        if not self._session:
            await self.connect()
        
        url = f"{self._base_url}/containers/{container_id}/logs"
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status >= 400:
                    raise PodmanAPIError(f"Failed to stream logs: HTTP {response.status}")
                
                async for line in response.content:
                    if line:
                        yield line.decode().strip()
                        
        except aiohttp.ClientError as e:
            raise PodmanAPIError(f"Log streaming error: {str(e)}")
    
    async def list_pods(self) -> List[Dict[str, Any]]:
        """List pods (Podman-specific feature)."""
        try:
            return await self._make_request("GET", "/pods/json")
        except PodmanAPIError:
            # Pods not supported (likely Docker fallback)
            return []
    
    async def get_events(self, since: Optional[datetime] = None, until: Optional[datetime] = None) -> AsyncGenerator[ContainerEvent, None]:
        """
        Stream container events.
        
        Args:
            since: Only events after this time
            until: Only events before this time
        """
        params = {}
        if since:
            params["since"] = str(int(since.timestamp()))
        if until:
            params["until"] = str(int(until.timestamp()))
        
        if not self._session:
            await self.connect()
        
        url = f"{self._base_url}/events"
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status >= 400:
                    raise PodmanAPIError(f"Failed to stream events: HTTP {response.status}")
                
                async for line in response.content:
                    if line:
                        try:
                            event_data = json.loads(line.decode().strip())
                            event = self._parse_event_data(event_data)
                            if event:
                                yield event
                        except json.JSONDecodeError:
                            continue
                            
        except aiohttp.ClientError as e:
            raise PodmanAPIError(f"Event streaming error: {str(e)}")
    
    def _parse_container_data(self, data: Dict[str, Any]) -> Container:
        """Parse container data from API response."""
        # Handle both Podman and Docker API formats
        container_id = data.get("Id", "")
        names = data.get("Names", [])
        name = names[0].lstrip("/") if names else ""
        
        # Parse status
        state = data.get("State", "")
        status_map = {
            "running": ContainerStatus.RUNNING,
            "exited": ContainerStatus.STOPPED,
            "stopped": ContainerStatus.STOPPED,
            "paused": ContainerStatus.PAUSED,
            "created": ContainerStatus.CREATED,
            "dead": ContainerStatus.DEAD
        }
        status = status_map.get(state.lower(), ContainerStatus.UNKNOWN)
        
        # Parse timestamps
        created_at = None
        if "Created" in data:
            try:
                created_at = datetime.fromtimestamp(data["Created"])
            except (ValueError, TypeError):
                pass
        
        # Parse image
        image = data.get("Image", "")
        
        # Parse ports
        ports = []
        port_data = data.get("Ports", [])
        for port in port_data:
            if isinstance(port, dict):
                private_port = port.get("PrivatePort", 0)
                public_port = port.get("PublicPort")
                port_type = port.get("Type", "tcp")
                
                port_mapping = f"{private_port}/{port_type}"
                if public_port:
                    port_mapping = f"{public_port}:{port_mapping}"
                ports.append(port_mapping)
        
        # Parse labels
        labels = data.get("Labels") or {}
        
        return Container(
            id=container_id,
            name=name,
            image=image,
            status=status,
            created_at=created_at,
            ports=ports,
            labels=labels,
            raw_data=data
        )
    
    def _parse_stats_data(self, data: Dict[str, Any]) -> ContainerStats:
        """Parse container statistics data."""
        # Handle both Podman and Docker stats formats
        cpu_stats = data.get("cpu_stats", {})
        memory_stats = data.get("memory_stats", {})
        network_stats = data.get("networks", {})
        blkio_stats = data.get("blkio_stats", {})
        
        # Calculate CPU percentage
        cpu_percent = 0.0
        if "cpu_usage" in cpu_stats and "system_cpu_usage" in cpu_stats:
            cpu_usage = cpu_stats["cpu_usage"].get("total_usage", 0)
            system_usage = cpu_stats.get("system_cpu_usage", 0)
            if system_usage > 0:
                cpu_percent = (cpu_usage / system_usage) * 100.0
        
        # Memory usage
        memory_usage = memory_stats.get("usage", 0)
        memory_limit = memory_stats.get("limit", 0)
        memory_percent = 0.0
        if memory_limit > 0:
            memory_percent = (memory_usage / memory_limit) * 100.0
        
        # Network I/O
        network_rx = 0
        network_tx = 0
        for interface_stats in network_stats.values():
            if isinstance(interface_stats, dict):
                network_rx += interface_stats.get("rx_bytes", 0)
                network_tx += interface_stats.get("tx_bytes", 0)
        
        # Block I/O
        block_read = 0
        block_write = 0
        io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
        for io_stat in io_service_bytes:
            if isinstance(io_stat, dict):
                if io_stat.get("op") == "Read":
                    block_read += io_stat.get("value", 0)
                elif io_stat.get("op") == "Write":
                    block_write += io_stat.get("value", 0)
        
        return ContainerStats(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_usage_bytes=memory_usage,
            memory_limit_bytes=memory_limit,
            memory_percent=memory_percent,
            network_rx_bytes=network_rx,
            network_tx_bytes=network_tx,
            block_read_bytes=block_read,
            block_write_bytes=block_write,
            raw_data=data
        )
    
    def _parse_event_data(self, data: Dict[str, Any]) -> Optional[ContainerEvent]:
        """Parse container event data."""
        event_type = data.get("Type", "")
        action = data.get("Action", "")
        
        # Only process container events
        if event_type.lower() != "container":
            return None
        
        actor = data.get("Actor", {})
        container_id = actor.get("ID", "")
        attributes = actor.get("Attributes", {})
        
        timestamp = None
        if "time" in data:
            try:
                timestamp = datetime.fromtimestamp(data["time"])
            except (ValueError, TypeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        return ContainerEvent(
            timestamp=timestamp,
            container_id=container_id,
            container_name=attributes.get("name", ""),
            action=action,
            image=attributes.get("image", ""),
            labels=attributes,
            raw_data=data
        )


# Import os for socket path detection
import os