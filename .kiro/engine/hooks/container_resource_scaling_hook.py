"""
Container Resource Scaling Hook for the Agent Hooks Enhancement system.

This hook monitors container resource usage and automatically scales resources
based on usage patterns to prevent resource exhaustion.
"""

import time
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
import statistics

from ..core.models import AgentHook, HookContext, HookResult
from ..events.models import EventType, MetricEvent
from ..utils.logging import get_logger, ExecutionError


class ContainerResourceScalingHook(AgentHook):
    """
    Hook that automatically scales container resources based on usage patterns.
    
    This hook monitors container resource usage metrics and automatically adjusts
    resource limits to prevent resource exhaustion while maintaining efficient
    resource utilization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the container resource scaling hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        
        # Load configuration
        self.cpu_high_threshold = config.get("cpu_high_threshold", 80)  # percentage
        self.cpu_low_threshold = config.get("cpu_low_threshold", 20)    # percentage
        self.memory_high_threshold = config.get("memory_high_threshold", 80)  # percentage
        self.memory_low_threshold = config.get("memory_low_threshold", 20)    # percentage
        self.scaling_cooldown_seconds = config.get("scaling_cooldown_seconds", 300)  # 5 minutes
        self.cpu_scaling_increment = config.get("cpu_scaling_increment", 0.5)  # cores
        self.memory_scaling_increment = config.get("memory_scaling_increment", 512)  # MB
        self.max_cpu_limit = config.get("max_cpu_limit", 8)  # cores
        self.max_memory_limit = config.get("max_memory_limit", 16384)  # MB (16GB)
        self.min_cpu_limit = config.get("min_cpu_limit", 0.1)  # cores
        self.min_memory_limit = config.get("min_memory_limit", 128)  # MB
        self.excluded_containers = config.get("excluded_containers", [])
        self.observation_window_seconds = config.get("observation_window_seconds", 600)  # 10 minutes
        self.min_data_points = config.get("min_data_points", 5)
        
        # Internal state
        self.resource_metrics: Dict[str, Dict[str, List[Tuple[float, float]]]] = {}  # container -> metric -> [(timestamp, value)]
        self.last_scaling_time: Dict[str, float] = {}  # container -> timestamp
        self.scaling_history: Dict[str, List[Dict[str, Any]]] = {}  # container -> [scaling_events]
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This hook executes when:
        1. It is enabled
        2. The event is a resource usage metric event
        3. The metric is for a container (metric name starts with "container.")
        4. The container is not in the excluded list
        5. We're not in a cooldown period
        6. We have enough metrics to make a scaling decision
        """
        if not self.enabled:
            return False
        
        # Check if this is a resource usage metric event
        event_type = context.trigger_event.get("type")
        if event_type != EventType.RESOURCE_USAGE.value:
            return False
        
        # Extract container name and metric information
        metric_name = context.trigger_event.get("metric_name", "")
        if not metric_name.startswith("container."):
            return False
        
        # Extract container name from tags or data
        tags = context.trigger_event.get("tags", {})
        data = context.trigger_event.get("data", {})
        container_name = tags.get("container_name") or data.get("container_name", "")
        
        if not container_name:
            return False
        
        # Check if the container is excluded
        if container_name in self.excluded_containers:
            return False
        
        # Check if we're in a cooldown period
        last_scaling = self.last_scaling_time.get(container_name, 0)
        if time.time() - last_scaling < self.scaling_cooldown_seconds:
            return False
        
        # Store the metric for later analysis
        metric_value = context.trigger_event.get("value", 0)
        self._store_metric(container_name, metric_name, metric_value)
        
        # Check if we have enough metrics to make a scaling decision
        if not self._has_sufficient_metrics(container_name):
            return False
        
        # Check if any metric exceeds thresholds
        cpu_usage = self._get_average_metric(container_name, "container.cpu.usage_percent")
        memory_usage = self._get_average_metric(container_name, "container.memory.usage_percent")
        
        return (cpu_usage is not None and (cpu_usage > self.cpu_high_threshold or cpu_usage < self.cpu_low_threshold)) or \
               (memory_usage is not None and (memory_usage > self.memory_high_threshold or memory_usage < self.memory_low_threshold))
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook to scale container resources.
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        start_time = time.time()
        
        try:
            # Extract container name from tags or data
            tags = context.trigger_event.get("tags", {})
            data = context.trigger_event.get("data", {})
            container_name = tags.get("container_name") or data.get("container_name", "")
            
            self.logger.info(
                f"Analyzing resource usage for container: {container_name}",
                {"container_name": container_name, "execution_id": context.execution_id}
            )
            
            # Get current resource limits
            runtime = await self._detect_container_runtime()
            current_cpu_limit, current_memory_limit = await self._get_container_resource_limits(runtime, container_name)
            
            # Get average resource usage
            cpu_usage = self._get_average_metric(container_name, "container.cpu.usage_percent")
            memory_usage = self._get_average_metric(container_name, "container.memory.usage_percent")
            
            # Determine if scaling is needed
            scaling_decisions = []
            new_cpu_limit = current_cpu_limit
            new_memory_limit = current_memory_limit
            
            # CPU scaling logic
            if cpu_usage is not None:
                if cpu_usage > self.cpu_high_threshold:
                    # Scale up CPU
                    new_cpu_limit = min(current_cpu_limit + self.cpu_scaling_increment, self.max_cpu_limit)
                    if new_cpu_limit > current_cpu_limit:
                        scaling_decisions.append({
                            "resource": "cpu",
                            "action": "scale_up",
                            "old_limit": current_cpu_limit,
                            "new_limit": new_cpu_limit,
                            "usage": cpu_usage,
                            "threshold": self.cpu_high_threshold
                        })
                elif cpu_usage < self.cpu_low_threshold:
                    # Scale down CPU
                    new_cpu_limit = max(current_cpu_limit - self.cpu_scaling_increment, self.min_cpu_limit)
                    if new_cpu_limit < current_cpu_limit:
                        scaling_decisions.append({
                            "resource": "cpu",
                            "action": "scale_down",
                            "old_limit": current_cpu_limit,
                            "new_limit": new_cpu_limit,
                            "usage": cpu_usage,
                            "threshold": self.cpu_low_threshold
                        })
            
            # Memory scaling logic
            if memory_usage is not None:
                if memory_usage > self.memory_high_threshold:
                    # Scale up memory
                    new_memory_limit = min(current_memory_limit + self.memory_scaling_increment, self.max_memory_limit)
                    if new_memory_limit > current_memory_limit:
                        scaling_decisions.append({
                            "resource": "memory",
                            "action": "scale_up",
                            "old_limit": current_memory_limit,
                            "new_limit": new_memory_limit,
                            "usage": memory_usage,
                            "threshold": self.memory_high_threshold
                        })
                elif memory_usage < self.memory_low_threshold:
                    # Scale down memory
                    new_memory_limit = max(current_memory_limit - self.memory_scaling_increment, self.min_memory_limit)
                    if new_memory_limit < current_memory_limit:
                        scaling_decisions.append({
                            "resource": "memory",
                            "action": "scale_down",
                            "old_limit": current_memory_limit,
                            "new_limit": new_memory_limit,
                            "usage": memory_usage,
                            "threshold": self.memory_low_threshold
                        })
            
            # Apply scaling if needed
            if scaling_decisions:
                self.last_scaling_time[container_name] = time.time()
                
                # Record scaling event
                scaling_event = {
                    "timestamp": time.time(),
                    "decisions": scaling_decisions,
                    "cpu_usage": cpu_usage,
                    "memory_usage": memory_usage
                }
                
                if container_name not in self.scaling_history:
                    self.scaling_history[container_name] = []
                self.scaling_history[container_name].append(scaling_event)
                
                # Update container resource limits
                success, output = await self._update_container_resources(
                    runtime, container_name, new_cpu_limit, new_memory_limit
                )
                
                actions_taken = [f"{decision['action'].replace('_', ' ').title()} {decision['resource']} from {decision['old_limit']} to {decision['new_limit']}" for decision in scaling_decisions]
                
                if success:
                    message = f"Successfully scaled resources for container {container_name}"
                    self.logger.info(
                        message,
                        {
                            "container_name": container_name,
                            "scaling_decisions": scaling_decisions,
                            "execution_id": context.execution_id
                        }
                    )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=True,
                        message=message,
                        actions_taken=actions_taken,
                        suggestions=[],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "cpu_usage_percent": cpu_usage,
                            "memory_usage_percent": memory_usage,
                            "new_cpu_limit": new_cpu_limit,
                            "new_memory_limit": new_memory_limit,
                            "scaling_decisions": scaling_decisions
                        },
                        execution_time_ms=execution_time_ms
                    )
                else:
                    message = f"Failed to scale resources for container {container_name}: {output}"
                    self.logger.error(
                        message,
                        {"container_name": container_name, "execution_id": context.execution_id}
                    )
                    
                    execution_time_ms = (time.time() - start_time) * 1000
                    return HookResult(
                        success=False,
                        message=message,
                        actions_taken=[],
                        suggestions=[
                            "Check container runtime permissions",
                            "Verify container supports resource updates",
                            "Check for container runtime issues",
                            "Review scaling limits configuration"
                        ],
                        metrics={
                            "execution_time_ms": execution_time_ms,
                            "cpu_usage_percent": cpu_usage,
                            "memory_usage_percent": memory_usage,
                            "scaling_decisions": scaling_decisions
                        },
                        execution_time_ms=execution_time_ms,
                        error=ExecutionError(f"Failed to scale container resources: {output}")
                    )
            else:
                message = f"No resource scaling needed for container {container_name}"
                self.logger.info(
                    message,
                    {
                        "container_name": container_name,
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "execution_id": context.execution_id
                    }
                )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=True,
                    message=message,
                    actions_taken=[],
                    suggestions=[],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "cpu_usage_percent": cpu_usage,
                        "memory_usage_percent": memory_usage,
                        "cpu_limit": current_cpu_limit,
                        "memory_limit": current_memory_limit
                    },
                    execution_time_ms=execution_time_ms
                )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing container resource scaling hook: {e}",
                {"execution_id": context.execution_id}
            )
            
            return HookResult(
                success=False,
                message=f"Error executing container resource scaling hook: {e}",
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
            "memory_mb": 150,
            "disk_mb": 30,
            "network": False
        }
    
    def _store_metric(self, container_name: str, metric_name: str, value: float) -> None:
        """
        Store a metric value for later analysis.
        
        Args:
            container_name: Name of the container
            metric_name: Name of the metric
            value: Metric value
        """
        now = time.time()
        
        # Initialize container metrics if needed
        if container_name not in self.resource_metrics:
            self.resource_metrics[container_name] = {}
        
        # Initialize metric list if needed
        if metric_name not in self.resource_metrics[container_name]:
            self.resource_metrics[container_name][metric_name] = []
        
        # Add metric value with timestamp
        self.resource_metrics[container_name][metric_name].append((now, value))
        
        # Remove old metrics
        cutoff_time = now - self.observation_window_seconds
        self.resource_metrics[container_name][metric_name] = [
            (ts, val) for ts, val in self.resource_metrics[container_name][metric_name]
            if ts >= cutoff_time
        ]
    
    def _has_sufficient_metrics(self, container_name: str) -> bool:
        """
        Check if we have sufficient metrics to make a scaling decision.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if we have sufficient metrics, False otherwise
        """
        if container_name not in self.resource_metrics:
            return False
        
        # Check if we have CPU and memory metrics
        cpu_metrics = self.resource_metrics[container_name].get("container.cpu.usage_percent", [])
        memory_metrics = self.resource_metrics[container_name].get("container.memory.usage_percent", [])
        
        # We need at least min_data_points for each metric
        return len(cpu_metrics) >= self.min_data_points or len(memory_metrics) >= self.min_data_points
    
    def _get_average_metric(self, container_name: str, metric_name: str) -> Optional[float]:
        """
        Get the average value of a metric over the observation window.
        
        Args:
            container_name: Name of the container
            metric_name: Name of the metric
            
        Returns:
            Average metric value, or None if no metrics are available
        """
        if container_name not in self.resource_metrics:
            return None
        
        metrics = self.resource_metrics[container_name].get(metric_name, [])
        if len(metrics) < self.min_data_points:
            return None
        
        # Calculate average of metric values
        values = [val for _, val in metrics]
        return statistics.mean(values)
    
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
    
    async def _get_container_resource_limits(self, runtime: str, container_name: str) -> Tuple[float, int]:
        """
        Get current resource limits for a container.
        
        Args:
            runtime: Container runtime to use ("podman" or "docker")
            container_name: Name of the container
            
        Returns:
            Tuple of (cpu_limit, memory_limit_mb)
            
        Raises:
            ExecutionError: If the container information cannot be retrieved
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
                raise ExecutionError(f"Failed to inspect container: {stderr.decode().strip()}")
            
            # Parse JSON output
            container_info = json.loads(stdout.decode())
            
            # Extract resource limits
            if isinstance(container_info, list) and len(container_info) > 0:
                container_info = container_info[0]
            
            # Get CPU limit
            cpu_limit = 1.0  # Default to 1 core
            if "HostConfig" in container_info and "NanoCpus" in container_info["HostConfig"]:
                # NanoCpus is in billionths of a CPU
                nano_cpus = container_info["HostConfig"]["NanoCpus"]
                if nano_cpus > 0:
                    cpu_limit = nano_cpus / 1_000_000_000
            elif "HostConfig" in container_info and "CpuQuota" in container_info["HostConfig"] and "CpuPeriod" in container_info["HostConfig"]:
                # CpuQuota and CpuPeriod can be used to calculate CPU limit
                cpu_quota = container_info["HostConfig"]["CpuQuota"]
                cpu_period = container_info["HostConfig"]["CpuPeriod"]
                if cpu_quota > 0 and cpu_period > 0:
                    cpu_limit = cpu_quota / cpu_period
            
            # Get memory limit
            memory_limit_mb = 1024  # Default to 1GB
            if "HostConfig" in container_info and "Memory" in container_info["HostConfig"]:
                memory_bytes = container_info["HostConfig"]["Memory"]
                if memory_bytes > 0:
                    memory_limit_mb = memory_bytes / (1024 * 1024)
            
            return cpu_limit, int(memory_limit_mb)
        
        except Exception as e:
            if not isinstance(e, ExecutionError):
                raise ExecutionError(f"Error getting container resource limits: {e}")
            raise
    
    async def _update_container_resources(self, runtime: str, container_name: str, cpu_limit: float, memory_limit_mb: int) -> Tuple[bool, str]:
        """
        Update resource limits for a container.
        
        Args:
            runtime: Container runtime to use ("podman" or "docker")
            container_name: Name of the container
            cpu_limit: New CPU limit in cores
            memory_limit_mb: New memory limit in MB
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Convert limits to the format expected by the container runtime
            memory_bytes = memory_limit_mb * 1024 * 1024  # Convert to bytes
            
            # Update container resources using the update command
            update_process = await asyncio.create_subprocess_exec(
                runtime, "update", "--cpus", str(cpu_limit), "--memory", f"{memory_bytes}b", container_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            update_stdout, update_stderr = await update_process.communicate()
            
            if update_process.returncode == 0:
                return True, "Container resources updated successfully"
            else:
                return False, f"Failed to update container resources: {update_stderr.decode().strip()}"
        
        except Exception as e:
            return False, str(e)
    
    def get_scaling_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about scaling operations.
        
        Returns:
            Dictionary containing scaling statistics
        """
        total_containers = len(self.scaling_history)
        total_scaling_events = sum(len(events) for events in self.scaling_history.values())
        
        scaling_by_type = {"scale_up": 0, "scale_down": 0}
        scaling_by_resource = {"cpu": 0, "memory": 0}
        
        for container_events in self.scaling_history.values():
            for event in container_events:
                for decision in event["decisions"]:
                    scaling_by_type[decision["action"]] += 1
                    scaling_by_resource[decision["resource"]] += 1
        
        return {
            "total_containers_scaled": total_containers,
            "total_scaling_events": total_scaling_events,
            "scaling_by_type": scaling_by_type,
            "scaling_by_resource": scaling_by_resource,
            "containers_monitored": len(self.resource_metrics),
            "containers_in_cooldown": len([
                name for name, last_scaling in self.last_scaling_time.items()
                if time.time() - last_scaling < self.scaling_cooldown_seconds
            ])
        }
    
    def get_container_scaling_history(self, container_name: str) -> Dict[str, Any]:
        """
        Get scaling history for a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Dictionary containing scaling history
        """
        history = self.scaling_history.get(container_name, [])
        current_metrics = {}
        
        if container_name in self.resource_metrics:
            for metric_name, values in self.resource_metrics[container_name].items():
                if values:
                    current_metrics[metric_name] = {
                        "current_value": values[-1][1],
                        "average_value": statistics.mean([v for _, v in values]),
                        "data_points": len(values)
                    }
        
        return {
            "container_name": container_name,
            "scaling_events": len(history),
            "last_scaling_time": self.last_scaling_time.get(container_name),
            "is_excluded": container_name in self.excluded_containers,
            "is_in_cooldown": (
                time.time() - self.last_scaling_time.get(container_name, 0) < self.scaling_cooldown_seconds
                if container_name in self.last_scaling_time else False
            ),
            "current_metrics": current_metrics,
            "scaling_history": history[-10:]  # Last 10 events
        }