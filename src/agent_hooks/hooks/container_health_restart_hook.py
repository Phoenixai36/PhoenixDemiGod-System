"""
Container Health Restart Hook for the Agent Hooks Automation system.

This hook monitors container health and automatically restarts unhealthy containers.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
import json
import subprocess

from src.agent_hooks.core.models import AgentHook, HookContext, HookResult, HookPriority, HookTrigger
from src.agent_hooks.events.models import EventType, SystemEvent
from src.agent_hooks.utils.logging import get_logger, ExecutionError


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
        
        # Internal state
        self.restart_attempts: Dict[str, int] = {}
        self.last_restart_time: Dict[str, float] = {}
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This hook executes when:
        1. It is enabled
        2. The event is a container health event
        3. The container is unhealthy
        4. The container is not in the excluded list
        5. We haven't exceeded the maximum restart attempts
        6. We're not in a cooldown period
        """
        if not self.enabled:
            return False
        
        # Check if this is a container health event
        event_type = context.trigger_event.get("type")
        if event_type != EventType.SERVICE_HEALTH.value:
            return False
        
        # Check if the container is unhealthy
        component = context.trigger_event.get("component", "")
        status = context.trigger_event.get("status", "")
        
        if not component.startswith("container:"):
            return False
        
        if status.lower() not in ("unhealthy", "failed", "error", "critical"):
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
            
            self.logger.info(
                f"Attempting to restart unhealthy container: {container_name}",
                {"container_name": container_name, "execution_id": context.execution_id}
            )
            
            # Update restart attempt counter
            self.restart_attempts[container_name] = self.restart_attempts.get(container_name, 0) + 1
            self.last_restart_time[container_name] = time.time()
            
            # Determine container runtime (podman or docker)
            container_runtime = await self._detect_container_runtime()
            
            # Restart the container
            restart_success, restart_output = await self._restart_container(container_runtime, container_name)
            
            if restart_success:
                # Wait for container to start
                await asyncio.sleep(2)
                
                # Check if container is now healthy
                health_status = await self._check_container_health(container_runtime, container_name)
                
                if health_status == "healthy":
                    message = f"Successfully restarted container {container_name}"
                    self.logger.info(
                        message,
                        {"container_name": container_name, "execution_id": context.execution_id}
                    )
                    
                    # Reset restart attempts if successful
                    if self.restart_attempts.get(container_name, 0) == self.max_restart_attempts:
                        self.restart_attempts[container_name] = 0
                    
                    # Send notification if configured
                    if self.notify_on_restart:
                        await self._send_notification(
                            f"Container {container_name} was successfully restarted",
                            {"container_name": container_name, "status": "healthy"}
                        )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=True,
                        message=message,
                        actions_taken=[f"Restarted container {container_name}"],
                        suggestions=[],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "restart_attempts": self.restart_attempts.get(container_name, 0)
                        },
                        execution_time_ms=execution_time_ms
                    )
                else:
                    message = f"Container {container_name} was restarted but is still unhealthy (status: {health_status})"
                    self.logger.warning(
                        message,
                        {"container_name": container_name, "status": health_status, "execution_id": context.execution_id}
                    )
                    
                    # Send notification if configured
                    if self.notify_on_failure:
                        await self._send_notification(
                            message,
                            {"container_name": container_name, "status": health_status}
                        )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=False,
                        message=message,
                        actions_taken=[f"Restarted container {container_name}"],
                        suggestions=[
                            "Check container logs for errors",
                            "Verify container configuration",
                            "Check dependent services"
                        ],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "restart_attempts": self.restart_attempts.get(container_name, 0)
                        },
                        execution_time_ms=execution_time_ms
                    )
            else:
                message = f"Failed to restart container {container_name}: {restart_output}"
                self.logger.error(
                    message,
                    {"container_name": container_name, "execution_id": context.execution_id}
                )
                
                # Send notification if configured
                if self.notify_on_failure:
                    await self._send_notification(
                        message,
                        {"container_name": container_name, "error": restart_output}
                    )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=False,
                    message=message,
                    actions_taken=[],
                    suggestions=[
                        "Check container runtime service",
                        "Verify container exists",
                        "Check for permission issues"
                    ],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "restart_attempts": self.restart_attempts.get(container_name, 0)
                    },
                    execution_time_ms=execution_time_ms,
                    error=ExecutionError(f"Failed to restart container: {restart_output}")
                )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing container health restart hook: {e}",
                {"execution_id": context.execution_id},
                e
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
            "cpu": 0.1,
            "memory_mb": 50,
            "disk_mb": 10,
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
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return "podman"
        except Exception:
            pass
        
        # Try docker as fallback
        try:
            process = await asyncio.create_subprocess_exec(
                "docker", "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return "docker"
        except Exception:
            pass
        
        raise ExecutionError("No container runtime (podman or docker) available")
    
    async def _restart_container(self, runtime: str, container_name: str) -> tuple[bool, str]:
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
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True, stdout.decode().strip()
            else:
                return False, stderr.decode().strip()
        except Exception as e:
            return False, str(e)
    
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
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return "unknown"
            
            # Parse JSON output
            container_info = json.loads(stdout.decode())
            
            # Extract health status
            if isinstance(container_info, list) and len(container_info) > 0:
                container_info = container_info[0]
            
            # Check if container has health check
            if "State" in container_info and "Health" in container_info["State"]:
                return container_info["State"]["Health"]["Status"].lower()
            
            # If no health check, check if container is running
            if "State" in container_info and "Status" in container_info["State"]:
                return container_info["State"]["Status"].lower()
            
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