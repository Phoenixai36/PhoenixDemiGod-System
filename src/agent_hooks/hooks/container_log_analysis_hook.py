"""
Container Log Analysis Hook for the Agent Hooks Automation system.

This hook analyzes container logs for error patterns and triggers appropriate
remediation actions.
"""

import time
import asyncio
import re
from typing import Dict, Any, List, Optional, Pattern, Set, Tuple
from datetime import datetime, timedelta

from src.agent_hooks.core.models import AgentHook, HookContext, HookResult, HookPriority, HookTrigger
from src.agent_hooks.events.models import EventType, SystemEvent
from src.agent_hooks.utils.logging import get_logger, ExecutionError


class LogPattern:
    """Pattern to match in container logs."""
    
    def __init__(
        self,
        name: str,
        pattern: str,
        severity: str,
        description: str,
        remediation_action: Optional[str] = None,
        remediation_args: Optional[Dict[str, Any]] = None,
        cooldown_seconds: int = 300
    ):
        """
        Initialize a log pattern.
        
        Args:
            name: Pattern name
            pattern: Regular expression pattern to match
            severity: Severity of the pattern (critical, high, medium, low, info)
            description: Description of the pattern
            remediation_action: Action to take when the pattern is matched
            remediation_args: Arguments for the remediation action
            cooldown_seconds: Cooldown period between remediation actions
        """
        self.name = name
        self.pattern = re.compile(pattern)
        self.severity = severity
        self.description = description
        self.remediation_action = remediation_action
        self.remediation_args = remediation_args or {}
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered: Dict[str, float] = {}  # container_name -> timestamp
    
    def matches(self, log_line: str) -> bool:
        """
        Check if the pattern matches a log line.
        
        Args:
            log_line: Log line to check
            
        Returns:
            True if the pattern matches, False otherwise
        """
        return bool(self.pattern.search(log_line))
    
    def can_trigger(self, container_name: str) -> bool:
        """
        Check if the pattern can trigger for a container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if the pattern can trigger, False if in cooldown
        """
        last_triggered = self.last_triggered.get(container_name, 0)
        return time.time() - last_triggered >= self.cooldown_seconds
    
    def mark_triggered(self, container_name: str) -> None:
        """
        Mark the pattern as triggered for a container.
        
        Args:
            container_name: Name of the container
        """
        self.last_triggered[container_name] = time.time()


class ContainerLogAnalysisHook(AgentHook):
    """
    Hook that analyzes container logs for error patterns.
    
    This hook monitors container logs for specific error patterns and triggers
    appropriate remediation actions when patterns are matched.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the container log analysis hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        
        # Load configuration
        self.max_log_lines = config.get("max_log_lines", 100)
        self.excluded_containers = config.get("excluded_containers", [])
        self.log_patterns = self._load_log_patterns(config.get("log_patterns", []))
        self.analysis_interval_seconds = config.get("analysis_interval_seconds", 300)  # 5 minutes
        
        # Internal state
        self.last_analysis_time: Dict[str, float] = {}  # container_name -> timestamp
        self.container_logs: Dict[str, List[str]] = {}  # container_name -> [log_lines]
    
    def _load_log_patterns(self, patterns_config: List[Dict[str, Any]]) -> List[LogPattern]:
        """
        Load log patterns from configuration.
        
        Args:
            patterns_config: List of pattern configurations
            
        Returns:
            List of LogPattern objects
        """
        patterns = []
        
        # Add default patterns
        default_patterns = [
            LogPattern(
                name="out_of_memory",
                pattern=r"(Out of memory|Killed|Cannot allocate memory|MemoryError)",
                severity="critical",
                description="Container is running out of memory",
                remediation_action="restart_container",
                remediation_args={"with_increased_memory": True}
            ),
            LogPattern(
                name="database_connection_failure",
                pattern=r"(Connection refused|Could not connect to|Connection timed out|Unable to connect to database)",
                severity="high",
                description="Database connection failure",
                remediation_action="check_database_service"
            ),
            LogPattern(
                name="disk_space_error",
                pattern=r"(No space left on device|Disk quota exceeded|Insufficient disk space)",
                severity="critical",
                description="Disk space issue",
                remediation_action="cleanup_disk_space"
            ),
            LogPattern(
                name="permission_denied",
                pattern=r"(Permission denied|Access denied|Forbidden|unauthorized)",
                severity="high",
                description="Permission or access issue",
                remediation_action="check_permissions"
            ),
            LogPattern(
                name="fatal_error",
                pattern=r"(FATAL ERROR|FATAL EXCEPTION|FATAL:|Segmentation fault|core dumped)",
                severity="critical",
                description="Fatal application error",
                remediation_action="restart_container"
            )
        ]
        
        patterns.extend(default_patterns)
        
        # Add custom patterns from configuration
        for pattern_config in patterns_config:
            pattern = LogPattern(
                name=pattern_config["name"],
                pattern=pattern_config["pattern"],
                severity=pattern_config.get("severity", "medium"),
                description=pattern_config.get("description", ""),
                remediation_action=pattern_config.get("remediation_action"),
                remediation_args=pattern_config.get("remediation_args", {}),
                cooldown_seconds=pattern_config.get("cooldown_seconds", 300)
            )
            patterns.append(pattern)
        
        return patterns
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This hook executes when:
        1. It is enabled
        2. The event is a container log event
        3. The container is not in the excluded list
        4. We haven't analyzed logs for this container recently
        """
        if not self.enabled:
            return False
        
        # Check if this is a container log event
        event_type = context.trigger_event.get("type")
        if event_type != "container_log":  # Custom event type for container logs
            return False
        
        # Extract container name
        container_name = context.trigger_event.get("component", "").split(":", 1)[1] if ":" in context.trigger_event.get("component", "") else ""
        if not container_name:
            return False
        
        # Check if the container is excluded
        if container_name in self.excluded_containers:
            return False
        
        # Store log lines for later analysis
        log_line = context.trigger_event.get("data", {}).get("log_line", "")
        if log_line:
            if container_name not in self.container_logs:
                self.container_logs[container_name] = []
            
            self.container_logs[container_name].append(log_line)
            
            # Limit the number of stored log lines
            if len(self.container_logs[container_name]) > self.max_log_lines:
                self.container_logs[container_name] = self.container_logs[container_name][-self.max_log_lines:]
        
        # Check if we should analyze logs for this container
        last_analysis = self.last_analysis_time.get(container_name, 0)
        return time.time() - last_analysis >= self.analysis_interval_seconds
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook to analyze container logs.
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        start_time = time.time()
        
        try:
            # Extract container name
            container_name = context.trigger_event.get("component", "").split(":", 1)[1] if ":" in context.trigger_event.get("component", "") else ""
            
            self.logger.info(
                f"Analyzing logs for container: {container_name}",
                {"container_name": container_name, "execution_id": context.execution_id}
            )
            
            # Update last analysis time
            self.last_analysis_time[container_name] = time.time()
            
            # Get logs for the container
            logs = self.container_logs.get(container_name, [])
            if not logs:
                message = f"No logs available for container {container_name}"
                self.logger.info(
                    message,
                    {"container_name": container_name, "execution_id": context.execution_id}
                )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=True,
                    message=message,
                    actions_taken=[],
                    suggestions=["Check container logging configuration"],
                    metrics={"execution_time_ms": execution_time_ms},
                    execution_time_ms=execution_time_ms
                )
            
            # Analyze logs for patterns
            matched_patterns = []
            for log_line in logs:
                for pattern in self.log_patterns:
                    if pattern.matches(log_line) and pattern.can_trigger(container_name):
                        matched_patterns.append((pattern, log_line))
                        pattern.mark_triggered(container_name)
            
            if not matched_patterns:
                message = f"No error patterns detected in logs for container {container_name}"
                self.logger.info(
                    message,
                    {"container_name": container_name, "execution_id": context.execution_id}
                )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=True,
                    message=message,
                    actions_taken=[],
                    suggestions=[],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "logs_analyzed": len(logs)
                    },
                    execution_time_ms=execution_time_ms
                )
            
            # Take remediation actions for matched patterns
            actions_taken = []
            for pattern, log_line in matched_patterns:
                self.logger.warning(
                    f"Detected log pattern '{pattern.name}' in container {container_name}: {log_line}",
                    {
                        "container_name": container_name,
                        "pattern_name": pattern.name,
                        "pattern_severity": pattern.severity,
                        "execution_id": context.execution_id
                    }
                )
                
                # Take remediation action if configured
                if pattern.remediation_action:
                    action_result = await self._take_remediation_action(
                        container_name, pattern.remediation_action, pattern.remediation_args
                    )
                    
                    if action_result[0]:
                        actions_taken.append(f"Took action '{pattern.remediation_action}' for pattern '{pattern.name}'")
                    else:
                        actions_taken.append(f"Failed to take action '{pattern.remediation_action}' for pattern '{pattern.name}': {action_result[1]}")
            
            message = f"Detected {len(matched_patterns)} error patterns in logs for container {container_name}"
            self.logger.info(
                message,
                {
                    "container_name": container_name,
                    "patterns_detected": len(matched_patterns),
                    "execution_id": context.execution_id
                }
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            return HookResult(
                success=True,
                message=message,
                actions_taken=actions_taken,
                suggestions=[
                    "Review container logs for recurring issues",
                    "Check application error handling",
                    "Consider updating error patterns configuration"
                ],
                metrics={
                    "execution_time_ms": execution_time_ms,
                    "logs_analyzed": len(logs),
                    "patterns_detected": len(matched_patterns)
                },
                execution_time_ms=execution_time_ms
            )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing container log analysis hook: {e}",
                {"execution_id": context.execution_id},
                e
            )
            
            return HookResult(
                success=False,
                message=f"Error executing container log analysis hook: {e}",
                actions_taken=[],
                suggestions=["Check hook configuration"],
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
            "memory_mb": 150,
            "disk_mb": 10,
            "network": False
        }
    
    async def _take_remediation_action(self, container_name: str, action: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Take a remediation action for a container.
        
        Args:
            container_name: Name of the container
            action: Action to take
            args: Arguments for the action
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if action == "restart_container":
                return await self._restart_container(container_name, args.get("with_increased_memory", False))
            elif action == "check_database_service":
                return await self._check_database_service(container_name)
            elif action == "cleanup_disk_space":
                return await self._cleanup_disk_space(container_name)
            elif action == "check_permissions":
                return await self._check_permissions(container_name)
            else:
                return False, f"Unknown remediation action: {action}"
        except Exception as e:
            return False, str(e)
    
    async def _restart_container(self, container_name: str, with_increased_memory: bool) -> Tuple[bool, str]:
        """
        Restart a container, optionally with increased memory.
        
        Args:
            container_name: Name of the container
            with_increased_memory: Whether to increase memory limit
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Detect container runtime
            runtime = await self._detect_container_runtime()
            
            # If increasing memory, update container resources
            if with_increased_memory:
                # Get current memory limit
                process = await asyncio.create_subprocess_exec(
                    runtime, "inspect", "--format", "{{.HostConfig.Memory}}", container_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    try:
                        current_memory = int(stdout.decode().strip())
                        # Increase memory by 25%
                        new_memory = int(current_memory * 1.25)
                        
                        # Update container memory limit
                        update_process = await asyncio.create_subprocess_exec(
                            runtime, "update", "--memory", str(new_memory), container_name,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        update_stdout, update_stderr = await update_process.communicate()
                        
                        if update_process.returncode != 0:
                            self.logger.warning(
                                f"Failed to increase memory for container {container_name}: {update_stderr.decode().strip()}",
                                {"container_name": container_name}
                            )
                    except (ValueError, TypeError):
                        self.logger.warning(
                            f"Failed to parse current memory limit for container {container_name}",
                            {"container_name": container_name}
                        )
            
            # Restart the container
            restart_process = await asyncio.create_subprocess_exec(
                runtime, "restart", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            restart_stdout, restart_stderr = await restart_process.communicate()
            
            if restart_process.returncode == 0:
                return True, f"Container {container_name} restarted successfully"
            else:
                return False, f"Failed to restart container {container_name}: {restart_stderr.decode().strip()}"
        
        except Exception as e:
            return False, f"Error restarting container: {e}"
    
    async def _check_database_service(self, container_name: str) -> Tuple[bool, str]:
        """
        Check database service health.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Tuple of (success, message)
        """
        # This would integrate with a database health check system
        # For now, we just log the action
        self.logger.info(
            f"Checking database service for container {container_name}",
            {"container_name": container_name, "action": "check_database_service"}
        )
        return True, "Database service check initiated"
    
    async def _cleanup_disk_space(self, container_name: str) -> Tuple[bool, str]:
        """
        Clean up disk space.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Detect container runtime
            runtime = await self._detect_container_runtime()
            
            # Clean up container logs
            prune_process = await asyncio.create_subprocess_exec(
                runtime, "container", "prune", "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            prune_stdout, prune_stderr = await prune_process.communicate()
            
            # Clean up unused images
            image_prune_process = await asyncio.create_subprocess_exec(
                runtime, "image", "prune", "--force",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            image_prune_stdout, image_prune_stderr = await image_prune_process.communicate()
            
            return True, "Disk space cleanup initiated"
        
        except Exception as e:
            return False, f"Error cleaning up disk space: {e}"
    
    async def _check_permissions(self, container_name: str) -> Tuple[bool, str]:
        """
        Check container permissions.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Tuple of (success, message)
        """
        # This would integrate with a permission checking system
        # For now, we just log the action
        self.logger.info(
            f"Checking permissions for container {container_name}",
            {"container_name": container_name, "action": "check_permissions"}
        )
        return True, "Permission check initiated"
    
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