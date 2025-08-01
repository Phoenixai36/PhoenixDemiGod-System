"""
Container restart tracking and analysis.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from .event_collector import ContainerEvent, ContainerEventType


@dataclass
class RestartPattern:
    """Represents a container restart pattern."""
    container_id: str
    container_name: str
    restart_count: int
    time_window: timedelta
    first_restart: datetime
    last_restart: datetime
    restart_intervals: List[float] = field(default_factory=list)  # seconds between restarts
    exit_codes: List[int] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    
    @property
    def restart_rate(self) -> float:
        """Calculate restarts per hour."""
        if self.time_window.total_seconds() == 0:
            return 0.0
        return (self.restart_count / self.time_window.total_seconds()) * 3600
    
    @property
    def average_interval(self) -> float:
        """Average time between restarts in seconds."""
        if not self.restart_intervals:
            return 0.0
        return sum(self.restart_intervals) / len(self.restart_intervals)
    
    @property
    def is_restart_loop(self) -> bool:
        """Determine if this represents a restart loop."""
        # Consider it a restart loop if:
        # 1. More than 3 restarts in 10 minutes
        # 2. Average interval is less than 2 minutes
        if self.restart_count >= 3 and self.time_window <= timedelta(minutes=10):
            return True
        
        if self.average_interval > 0 and self.average_interval < 120:  # 2 minutes
            return True
        
        return False
    
    @property
    def severity(self) -> str:
        """Get severity level of restart pattern."""
        if self.is_restart_loop:
            return "critical"
        elif self.restart_count >= 5:
            return "warning"
        elif self.restart_count >= 2:
            return "info"
        else:
            return "normal"


class RestartTracker:
    """Tracks and analyzes container restart patterns."""
    
    def __init__(self, analysis_window: timedelta = timedelta(hours=1)):
        self.logger = logging.getLogger(__name__)
        self.analysis_window = analysis_window
        self.restart_events: Dict[str, List[ContainerEvent]] = defaultdict(list)
        self.restart_patterns: Dict[str, RestartPattern] = {}
        self.restart_loop_callbacks = []
        
    def add_event(self, event: ContainerEvent) -> None:
        """Add a container event for restart analysis."""
        if event.event_type in [ContainerEventType.RESTART, ContainerEventType.START]:
            container_id = event.container_id
            
            # Add event to container's event list
            self.restart_events[container_id].append(event)
            
            # Clean old events outside analysis window
            cutoff_time = datetime.now() - self.analysis_window
            self.restart_events[container_id] = [
                e for e in self.restart_events[container_id] 
                if e.timestamp >= cutoff_time
            ]
            
            # Update restart pattern
            self._update_restart_pattern(container_id)
    
    def _update_restart_pattern(self, container_id: str) -> None:
        """Update restart pattern for a container."""
        events = self.restart_events[container_id]
        
        if len(events) < 2:
            # Need at least 2 events to establish a pattern
            if container_id in self.restart_patterns:
                del self.restart_patterns[container_id]
            return
        
        # Sort events by timestamp
        events = sorted(events, key=lambda e: e.timestamp)
        
        # Calculate restart intervals
        intervals = []
        for i in range(1, len(events)):
            interval = (events[i].timestamp - events[i-1].timestamp).total_seconds()
            intervals.append(interval)
        
        # Extract exit codes and signals
        exit_codes = [e.exit_code for e in events if e.exit_code is not None]
        signals = [e.signal for e in events if e.signal is not None]
        
        # Create or update restart pattern
        pattern = RestartPattern(
            container_id=container_id,
            container_name=events[0].container_name,
            restart_count=len(events),
            time_window=events[-1].timestamp - events[0].timestamp,
            first_restart=events[0].timestamp,
            last_restart=events[-1].timestamp,
            restart_intervals=intervals,
            exit_codes=exit_codes,
            signals=signals
        )
        
        # Check if this is a new restart loop
        old_pattern = self.restart_patterns.get(container_id)
        is_new_loop = (
            pattern.is_restart_loop and 
            (old_pattern is None or not old_pattern.is_restart_loop)
        )
        
        self.restart_patterns[container_id] = pattern
        
        # Notify callbacks if new restart loop detected
        if is_new_loop:
            self.logger.warning(
                f"Restart loop detected for container {pattern.container_name} "
                f"({container_id[:12]}): {pattern.restart_count} restarts in "
                f"{pattern.time_window}"
            )
            
            for callback in self.restart_loop_callbacks:
                try:
                    callback(pattern)
                except Exception as e:
                    self.logger.error(f"Error in restart loop callback: {str(e)}")
    
    def get_restart_pattern(self, container_id: str) -> Optional[RestartPattern]:
        """Get restart pattern for a container."""
        return self.restart_patterns.get(container_id)
    
    def get_all_patterns(self) -> Dict[str, RestartPattern]:
        """Get all restart patterns."""
        return self.restart_patterns.copy()
    
    def get_restart_loops(self) -> List[RestartPattern]:
        """Get all containers currently in restart loops."""
        return [
            pattern for pattern in self.restart_patterns.values()
            if pattern.is_restart_loop
        ]
    
    def get_problematic_containers(self, min_restarts: int = 3) -> List[RestartPattern]:
        """Get containers with high restart counts."""
        return [
            pattern for pattern in self.restart_patterns.values()
            if pattern.restart_count >= min_restarts
        ]
    
    def add_restart_loop_callback(self, callback) -> None:
        """Add callback to be called when restart loops are detected."""
        self.restart_loop_callbacks.append(callback)
    
    def remove_restart_loop_callback(self, callback) -> None:
        """Remove restart loop callback."""
        if callback in self.restart_loop_callbacks:
            self.restart_loop_callbacks.remove(callback)
    
    def get_restart_statistics(self) -> Dict[str, any]:
        """Get overall restart statistics."""
        if not self.restart_patterns:
            return {
                "total_containers": 0,
                "containers_with_restarts": 0,
                "restart_loops": 0,
                "total_restarts": 0
            }
        
        patterns = list(self.restart_patterns.values())
        
        stats = {
            "total_containers": len(patterns),
            "containers_with_restarts": len([p for p in patterns if p.restart_count > 1]),
            "restart_loops": len([p for p in patterns if p.is_restart_loop]),
            "total_restarts": sum(p.restart_count for p in patterns),
            "average_restarts_per_container": sum(p.restart_count for p in patterns) / len(patterns),
            "severity_breakdown": {
                "critical": len([p for p in patterns if p.severity == "critical"]),
                "warning": len([p for p in patterns if p.severity == "warning"]),
                "info": len([p for p in patterns if p.severity == "info"]),
                "normal": len([p for p in patterns if p.severity == "normal"])
            }
        }
        
        # Find most problematic container
        if patterns:
            most_restarts = max(patterns, key=lambda p: p.restart_count)
            stats["most_problematic_container"] = {
                "container_id": most_restarts.container_id,
                "container_name": most_restarts.container_name,
                "restart_count": most_restarts.restart_count,
                "restart_rate": most_restarts.restart_rate
            }
        
        return stats
    
    def analyze_restart_causes(self, container_id: str) -> Dict[str, any]:
        """Analyze potential causes of restarts for a container."""
        pattern = self.restart_patterns.get(container_id)
        if not pattern:
            return {"error": "No restart pattern found for container"}
        
        analysis = {
            "container_id": container_id,
            "container_name": pattern.container_name,
            "restart_count": pattern.restart_count,
            "time_window": str(pattern.time_window),
            "is_restart_loop": pattern.is_restart_loop,
            "severity": pattern.severity,
            "potential_causes": []
        }
        
        # Analyze exit codes
        if pattern.exit_codes:
            exit_code_counts = {}
            for code in pattern.exit_codes:
                exit_code_counts[code] = exit_code_counts.get(code, 0) + 1
            
            analysis["exit_codes"] = exit_code_counts
            
            # Common exit code meanings
            exit_code_meanings = {
                0: "Normal exit",
                1: "General error",
                2: "Misuse of shell builtins",
                125: "Docker daemon error",
                126: "Container command not executable",
                127: "Container command not found",
                128: "Invalid exit argument",
                130: "Container terminated by Ctrl+C",
                137: "Container killed (SIGKILL)",
                139: "Segmentation fault",
                143: "Container terminated (SIGTERM)"
            }
            
            for code, count in exit_code_counts.items():
                if code in exit_code_meanings:
                    analysis["potential_causes"].append(
                        f"Exit code {code} ({count} times): {exit_code_meanings[code]}"
                    )
        
        # Analyze signals
        if pattern.signals:
            signal_counts = {}
            for signal in pattern.signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            analysis["signals"] = signal_counts
            
            for signal, count in signal_counts.items():
                analysis["potential_causes"].append(
                    f"Signal {signal} ({count} times)"
                )
        
        # Analyze restart intervals
        if pattern.restart_intervals:
            avg_interval = pattern.average_interval
            min_interval = min(pattern.restart_intervals)
            max_interval = max(pattern.restart_intervals)
            
            analysis["restart_intervals"] = {
                "average_seconds": avg_interval,
                "min_seconds": min_interval,
                "max_seconds": max_interval
            }
            
            if avg_interval < 30:
                analysis["potential_causes"].append(
                    "Very short restart intervals suggest immediate failure on startup"
                )
            elif avg_interval < 300:  # 5 minutes
                analysis["potential_causes"].append(
                    "Short restart intervals suggest application crashes shortly after startup"
                )
        
        # General recommendations
        if pattern.is_restart_loop:
            analysis["recommendations"] = [
                "Check container logs for error messages",
                "Verify application configuration",
                "Check resource limits (CPU, memory)",
                "Verify dependencies are available",
                "Consider implementing health checks",
                "Review application startup sequence"
            ]
        
        return analysis
    
    def cleanup_old_data(self) -> None:
        """Clean up old restart data outside the analysis window."""
        cutoff_time = datetime.now() - self.analysis_window
        
        # Clean restart events
        for container_id in list(self.restart_events.keys()):
            self.restart_events[container_id] = [
                e for e in self.restart_events[container_id]
                if e.timestamp >= cutoff_time
            ]
            
            # Remove empty entries
            if not self.restart_events[container_id]:
                del self.restart_events[container_id]
        
        # Clean restart patterns for containers with no recent events
        for container_id in list(self.restart_patterns.keys()):
            if container_id not in self.restart_events:
                del self.restart_patterns[container_id]