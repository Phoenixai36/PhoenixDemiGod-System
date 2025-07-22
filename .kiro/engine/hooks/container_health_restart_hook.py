"""
Container Health Restart Hook for the Agent Hooks Enhancement system.

This hook monitors container health and automatically restarts unhealthy containers
with configurable retry limits and cooldown periods.
"""

import time
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple

from ..core.models import AgentHook, HookContext, HookResult
from ..events.models import EventType, SystemEvent
from ..utils.logging import get_logger, ExecutionError


class ContainerHealthRestartHook(AgentHook):
    """
    Hook that automatically restarts unhealthy containers.
    
    This hook monitors container health events and automatically restarts
    containers that are reported as unhealthy, with configurable retry limits
    and notification options.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the container health restart hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        
        # Load configuration
        self.max_restart_attempts = config.get("max_restart_attempts", 3)
        self.restart_cooldown_seconds = config.get("restart_cooldown_seconds", 60)
        self.notify_on_restart = config.get("notify_on_restart", True)
        self.notify_on_failure = config.get("notify_on_failure", True)
        self.excluded_containers = config.get("excluded_containers", [])
        self.health_check_timeout = config.get("health_check_timeout", 30)
        self.restart_timeout = config.get("restart_timeout", 60)
        
        # Internal state
        self.restart_attempts: Dict[str, int] = {}
        self.last_restart_time: Dict[str, float] = {}
        self.container_status_cache: Dict[str, str] = {}
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This hook executes when:
        1. It is enabled
        2. The event is a service health event
        3. The component is a container (starts with "container:")
        4. The container status indicates it's unhealthy
        5. The container is not in the excluded list
        6. We haven't exceeded the maximum restart attempts
        7. We're not in a cooldown period
        """
        if not self.enabled:
            return False
        
        # Check if this is a service health event
        event_type = context.trigger_event.get("type")
        if event_type != EventType.SERVICE_HEALTH.value:
            return False
        
        # Check if the component is a container
        component = context.trigger_event.get("component", "")
        if not component.startswith("container:"):
            return False
        
        # Check if the container status indicates it's unhealthy
        status = context.trigger_event.get("status", "").lower()
        unhealthy_statuses = {"unhealthy", "failed", "error", "critical"}
        if status not in unhealthy_statuses:
            return False
        
        # Extract container name from component
        container_name = component.split(":", 1)[1] if ":" in component else component
        
        # Check if the container is excluded
        if container_name in self.excluded_containers:
            self.logger.info(
                f"Container {container_name} is excluded from automatic restart",
                {"container_name": container_name}
            )
            return False
        
        # Check if we've exceeded the maximum restart attempts
        if self.restart_attempts.get(container_name, 0) >= self.max_restart_attempts:
            self.logger.warning(
                f"Maximum restart attempts ({self.max_restart_attempts}) reached for container {container_name}",
                {"container_name": container_name, "restart_attempts": self.restart_attempts.get(container_name, 0)}
            )
            return False
        
        # Check if we're in a cooldown period
        last_restart = self.last_restart_time.get(container_name, 0)
        if time.time() - last_restart < self.restart_cooldown_seconds:
            self.logger.info(
                f"Container {container_name} is in cooldown period, skipping restart",
                {"container_name": container_name, "cooldown_seconds": self.restart_cooldown_seconds}
            )
            return False
        
        return True
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook to restart an unhealthy container.
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        start_time = time.time()
        
        try:
            # Extract container information from the event
            component = context.trigger_event.get("component", "")
            container_name = component.split(":", 1)[1] if ":" in component else component
            status = context.trigger_event.get("status", "")
            
            self.logger.info(
                f"Attempting to restart unhealthy container: {container_name} (status: {status})",
                {"container_name": container_name, "status": status, "execution_id": context.execution_id}
            )
            
            # Update restart attempt counter
            self.restart_attempts[container_name] = self.restart_attempts.get(container_name, 0) + 1
            self.last_restart_time[container_name] = time.time()
            
            # Determine container runtime (podman or docker)
            container_runtime = await self._detect_container_runtime()
            
            # Get current container status before restart
            pre_restart_status = await self._get_container_status(container_runtime, container_name)
            
            # Restart the container
            restart_success, restart_output = await self._restart_container(container_runtime, container_name)
            
            if restart_success:
                # Wait for container to start
                await asyncio.sleep(3)
                
                # Check if container is now healthy
                health_status = await self._check_container_health(container_runtime, container_name)
                
                if health_status in ("healthy", "running"):
                    message = f"Successfully restarted container {container_name}"
                    self.logger.info(
                        message,
                        {"container_name": container_name, "new_status": health_status, "execution_id": context.execution_id}
                    )
                    
                    # Reset restart attempts if successful
                    self.restart_attempts[container_name] = 0
                    self.container_status_cache[container_name] = health_status
                    
                    # Send notification if configured
                    if self.notify_on_restart:
                        await self._send_notification(
                            f"Container {container_name} was successfully restarted",
                            {"container_name": container_name, "status": health_status, "attempts": self.restart_attempts[container_name]}
                        )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=True,
                        message=message,
                        actions_taken=[
                            f"Restarted container {container_name}",
                            f"Container status changed from {pre_restart_status} to {health_status}"
                        ],
                        suggestions=[],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "restart_attempts": self.restart_attempts.get(container_name, 0),
                            "pre_restart_status": pre_restart_status,
                            "post_restart_status": health_status
                        },
                        execution_time_ms=execution_time_ms
                    )
                else:
                    message = f"Container {container_name} was restarted but is still unhealthy (status: {health_status})"
                    self.logger.warning(
                        message,
                        {"container_name": container_name, "status": health_status, "execution_id": context.execution_id}
                    )
                    
                    self.container_status_cache[container_name] = health_status
                    
                    # Send notification if configured
                    if self.notify_on_failure:
                        await self._send_notification(
                            message,
                            {"container_name": container_name, "status": health_status, "attempts": self.restart_attempts[container_name]}
                        )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=False,
                        message=message,
                        actions_taken=[f"Restarted container {container_name}"],
                        suggestions=[
                            "Check container logs for errors",
                            "Verify container configuration",
                            "Check dependent services",
                            "Review container resource limits"
                        ],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "restart_attempts": self.restart_attempts.get(container_name, 0),
                            "pre_restart_status": pre_restart_status,
                            "post_restart_status": health_status
                        },
                        execution_time_ms=execution_time_ms
                    )
            else:
                message = f"Failed to restart container {container_name}: {restart_output}"
                self.logger.error(
                    message,
                    {"container_name": container_name, "error": restart_output, "execution_id": context.execution_id}
                )
                
                # Send notification if configured
                if self.notify_on_failure:
                    await self._send_notification(
                        message,
                        {"container_name": container_name, "error": restart_output, "attempts": self.restart_attempts[container_name]}
                    )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=False,
                    message=message,
                    actions_taken=[],
                    suggestions=[
                        "Check container runtime service",
                        "Verify container exists",
                        "Check for permission issues",
                        "Review container runtime logs"
                    ],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "restart_attempts": self.restart_attempts.get(container_name, 0),
                        "pre_restart_status": pre_restart_status
                    },
                    execution_time_ms=execution_time_ms,
                    error=ExecutionError(f"Failed to restart container: {restart_output}")
                )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing container health restart hook: {e}",
                {"execution_id": context.execution_id}
            )
            
            return HookResult(
                success=False,
                message=f"Error executing container health restart hook: {e}",
                actions_taken=[],
                suggestions=["Check hook configuration", "Verify container runtime is available"],
                metrics={"execution_time_ms": execution_time_ms},
                execution_time_ms=execution_time_ms,
                error=ExecutionError(str(e))
            )
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Get resource requirements for this hook.
        
        Returns:
            Dictionary of resource requirements
        """
        return {
            "cpu": 0.2,
            "memory_mb": 100,
            "disk_mb": 20,
            "network": False
        }
    
    async def _detect_container_runtime(self) -> str:
        """
        Detect the available container runtime.
        
        Returns:
            Name of the container runtime ("podman" or "docker")
            
        Raises:
            ExecutionError: If no container runtime is available
        """
        # Try podman first (preferred)
        try:
            process = await asyncio.create_subprocess_exec(
                "podman", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            
            if process.returncode == 0:
                self.logger.debug("Detected podman container runtime")
                return "podman"
        except (Exception, asyncio.TimeoutError):
            pass
        
        # Try docker as fallback
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
            
            if process.returncode == 0:
                self.logger.debug("Detected docker container runtime")
                return "docker"
        except (Exception, asyncio.TimeoutError):
            pass
        
        raise ExecutionError("No container runtime (podman or docker) available")
    
    async def _get_container_status(self, runtime: str, container_name: str) -> str:
        """
        Get the current status of a container.
        
        Args:
            runtime: Container runtime to use ("podman" or "docker")
            container_name: Name of the container
            
        Returns:
            Current status of the container
        """
        try:
            process = await asyncio.create_subprocess_exec(
                runtime, "inspect", "--format", "{{.State.Status}}", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            
            if process.returncode == 0:
                return stdout.decode().strip().lower()
            else:
                self.logger.warning(f"Failed to get container status: {stderr.decode().strip()}")
                return "unknown"
        except (Exception, asyncio.TimeoutError) as e:
            self.logger.warning(f"Error getting container status: {e}")
            return "unknown"
    
    async def _restart_container(self, runtime: str, container_name: str) -> Tuple[bool, str]:
        """
        Restart a container using the specified runtime.
        
        Args:
            runtime: Container runtime to use ("podman" or "docker")
            container_name: Name of the container to restart
            
        Returns:
            Tuple of (success, output)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                runtime, "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.restart_timeout
            )
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                self.logger.info(f"Container {container_name} restarted successfully")
                return True, output
            else:
                error_output = stderr.decode().strip()
                self.logger.error(f"Failed to restart container {container_name}: {error_output}")
                return False, error_output
        except asyncio.TimeoutError:
            error_msg = f"Container restart timed out after {self.restart_timeout} seconds"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error restarting container: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    async def _check_container_health(self, runtime: str, container_name: str) -> str:
        """
        Check the health status of a container.
        
        Args:
            runtime: Container runtime to use ("podman" or "docker")
            container_name: Name of the container to check
            
        Returns:
            Health status of the container
        """
        try:
            # Get container info in JSON format
            process = await asyncio.create_subprocess_exec(
                runtime, "inspect", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.health_check_timeout
            )
            
            if process.returncode != 0:
                self.logger.warning(f"Failed to inspect container: {stderr.decode().strip()}")
                return "unknown"
            
            # Parse JSON output
            container_info = json.loads(stdout.decode())
            
            # Extract health status
            if isinstance(container_info, list) and len(container_info) > 0:
                container_info = container_info[0]
            
            # Check if container has health check
            if "State" in container_info and "Health" in container_info["State"]:
                health_status = container_info["State"]["Health"]["Status"].lower()
                self.logger.debug(f"Container {container_name} health status: {health_status}")
                return health_status
            
            # If no health check, check if container is running
            if "State" in container_info and "Status" in container_info["State"]:
                status = container_info["State"]["Status"].lower()
                self.logger.debug(f"Container {container_name} status: {status}")
                return status
            
            return "unknown"
        except asyncio.TimeoutError:
            self.logger.warning(f"Health check timed out for container {container_name}")
            return "timeout"
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse container inspect output: {e}")
            return "unknown"
        except Exception as e:
            self.logger.error(f"Error checking container health: {e}")
            return "unknown"
    
    async def _send_notification(self, message: str, context: Dict[str, Any]) -> None:
        """
        Send a notification about container restart.
        
        Args:
            message: Notification message
            context: Additional context for the notification
        """
        # This would integrate with a notification system
        # For now, we just log the notification
        self.logger.info(
            f"NOTIFICATION: {message}",
            {"notification_type": "container_restart", **context}
        )
        
        # In a real implementation, this could send notifications via:
        # - Email
        # - Slack/Teams
        # - PagerDuty
        # - Custom webhook
        # - System events
    
    def get_container_stats(self) -> Dict[str, Any]:
        """
        Get statistics about container restart operations.
        
        Returns:
            Dictionary containing restart statistics
        """
        total_containers = len(self.restart_attempts)
        total_attempts = sum(self.restart_attempts.values())
        containers_at_max_attempts = sum(1 for attempts in self.restart_attempts.values() if attempts >= self.max_restart_attempts)
        
        return {
            "total_containers_monitored": total_containers,
            "total_restart_attempts": total_attempts,
            "containers_at_max_attempts": containers_at_max_attempts,
            "average_attempts_per_container": total_attempts / total_containers if total_containers > 0 else 0,
            "containers_in_cooldown": len([
                name for name, last_restart in self.last_restart_time.items()
                if time.time() - last_restart < self.restart_cooldown_seconds
            ])
        }
    
    def reset_container_attempts(self, container_name: str) -> bool:
        """
        Reset restart attempts for a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if reset was successful, False if container not found
        """
        if container_name in self.restart_attempts:
            self.restart_attempts[container_name] = 0
            self.logger.info(f"Reset restart attempts for container {container_name}")
            return True
        return False
    
    def get_container_restart_history(self, container_name: str) -> Dict[str, Any]:
        """
        Get restart history for a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Dictionary containing restart history
        """
        return {
            "container_name": container_name,
            "restart_attempts": self.restart_attempts.get(container_name, 0),
            "last_restart_time": self.last_restart_time.get(container_name),
            "current_status": self.container_status_cache.get(container_name, "unknown"),
            "is_excluded": container_name in self.excluded_containers,
            "is_in_cooldown": (
                time.time() - self.last_restart_time.get(container_name, 0) < self.restart_cooldown_seconds
                if container_name in self.last_restart_time else False
            ),
            "at_max_attempts": self.restart_attempts.get(container_name, 0) >= self.max_restart_attempts
        }