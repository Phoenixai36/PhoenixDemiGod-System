"""
Container uptime tracking and analysis.
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from .event_collector import ContainerEvent, ContainerEventType


@dataclass
class UptimeRecord:
    """Represents a container uptime record."""
    container_id: str
    container_name: str
    image: str
    start_time: datetime
    end_time: Optional[datetime] = None
    uptime_seconds: Optional[float] = None
    
    @property
    def is_running(self) -> bool:
        """Check if container is currently running."""
        return self.end_time is None
    
    @property
    def current_uptime(self) -> float:
        """Get current uptime in seconds."""
        if self.is_running:
            return (datetime.now() - self.start_time).total_seconds()
        elif self.uptime_seconds is not None:
            return self.uptime_seconds
        else:
            return 0.0
    
    def finalize(self, end_time: datetime) -> None:
        """Finalize the uptime record when container stops."""
        self.end_time = end_time
        self.uptime_seconds = (end_time - self.start_time).total_seconds()


@dataclass
class UptimeStatistics:
    """Container uptime statistics."""
    container_id: str
    container_name: str
    total_uptime_seconds: float
    total_downtime_seconds: float
    uptime_sessions: int
    average_session_duration: float
    longest_session_duration: float
    shortest_session_duration: float
    current_uptime_seconds: float
    uptime_percentage: float
    last_start_time: Optional[datetime] = None
    last_stop_time: Optional[datetime] = None
    
    @property
    def availability_score(self) -> str:
        """Get availability score based on uptime percentage."""
        if self.uptime_percentage >= 99.9:
            return "excellent"
        elif self.uptime_percentage >= 99.0:
            return "good"
        elif self.uptime_percentage >= 95.0:
            return "fair"
        else:
            return "poor"


class UptimeTracker:
    """Tracks container uptime and availability."""
    
    def __init__(self, tracking_window: timedelta = timedelta(days=7)):
        self.logger = logging.getLogger(__name__)
        self.tracking_window = tracking_window
        self.active_sessions: Dict[str, UptimeRecord] = {}
        self.completed_sessions: Dict[str, List[UptimeRecord]] = {}
        self.uptime_callbacks = []
        
    def add_event(self, event: ContainerEvent) -> None:
        """Process a container event for uptime tracking."""
        container_id = event.container_id
        
        if event.event_type == ContainerEventType.START:
            self._handle_start_event(event)
        elif event.event_type in [ContainerEventType.STOP, ContainerEventType.DIE]:
            self._handle_stop_event(event)
        elif event.event_type == ContainerEventType.RESTART:
            # Restart is essentially a stop followed by a start
            self._handle_stop_event(event)
            self._handle_start_event(event)
    
    def _handle_start_event(self, event: ContainerEvent) -> None:
        """Handle container start event."""
        container_id = event.container_id
        
        # End any existing active session (shouldn't happen, but be safe)
        if container_id in self.active_sessions:
            self.logger.warning(
                f"Container {event.container_name} started but already had active session"
            )
            self._finalize_session(container_id, event.timestamp)
        
        # Start new uptime session
        self.active_sessions[container_id] = UptimeRecord(
            container_id=container_id,
            container_name=event.container_name,
            image=event.image,
            start_time=event.timestamp
        )
        
        self.logger.info(
            f"Started uptime tracking for {event.container_name} ({container_id[:12]})"
        )
    
    def _handle_stop_event(self, event: ContainerEvent) -> None:
        """Handle container stop event."""
        container_id = event.container_id
        
        if container_id in self.active_sessions:
            self._finalize_session(container_id, event.timestamp)
        else:
            self.logger.warning(
                f"Container {event.container_name} stopped but had no active session"
            )
    
    def _finalize_session(self, container_id: str, end_time: datetime) -> None:
        """Finalize an uptime session."""
        if container_id not in self.active_sessions:
            return
        
        session = self.active_sessions[container_id]
        session.finalize(end_time)
        
        # Move to completed sessions
        if container_id not in self.completed_sessions:
            self.completed_sessions[container_id] = []
        
        self.completed_sessions[container_id].append(session)
        del self.active_sessions[container_id]
        
        # Clean old sessions
        self._cleanup_old_sessions(container_id)
        
        self.logger.info(
            f"Finalized uptime session for {session.container_name}: "
            f"{session.uptime_seconds:.1f} seconds"
        )
        
        # Notify callbacks
        for callback in self.uptime_callbacks:
            try:
                callback(session)
            except Exception as e:
                self.logger.error(f"Error in uptime callback: {str(e)}")
    
    def _cleanup_old_sessions(self, container_id: str) -> None:
        """Clean up old uptime sessions outside tracking window."""
        if container_id not in self.completed_sessions:
            return
        
        cutoff_time = datetime.now() - self.tracking_window
        
        self.completed_sessions[container_id] = [
            session for session in self.completed_sessions[container_id]
            if session.start_time >= cutoff_time
        ]
        
        # Remove empty entries
        if not self.completed_sessions[container_id]:
            del self.completed_sessions[container_id]
    
    def get_current_uptime(self, container_id: str) -> Optional[float]:
        """Get current uptime for a running container in seconds."""
        if container_id in self.active_sessions:
            return self.active_sessions[container_id].current_uptime
        return None
    
    def is_container_running(self, container_id: str) -> bool:
        """Check if container is currently running."""
        return container_id in self.active_sessions
    
    def get_uptime_statistics(self, container_id: str) -> Optional[UptimeStatistics]:
        """Get comprehensive uptime statistics for a container."""
        # Get all sessions (active + completed)
        all_sessions = []
        
        if container_id in self.completed_sessions:
            all_sessions.extend(self.completed_sessions[container_id])
        
        if container_id in self.active_sessions:
            all_sessions.append(self.active_sessions[container_id])
        
        if not all_sessions:
            return None
        
        # Calculate statistics
        total_uptime = 0.0
        session_durations = []
        current_uptime = 0.0
        last_start_time = None
        last_stop_time = None
        
        for session in all_sessions:
            if session.is_running:
                current_uptime = session.current_uptime
                total_uptime += current_uptime
                last_start_time = session.start_time
            else:
                total_uptime += session.uptime_seconds
                session_durations.append(session.uptime_seconds)
                if last_stop_time is None or session.end_time > last_stop_time:
                    last_stop_time = session.end_time
                if last_start_time is None or session.start_time > last_start_time:
                    last_start_time = session.start_time
        
        # Calculate total time window
        earliest_start = min(session.start_time for session in all_sessions)
        latest_time = max(
            (session.end_time or datetime.now()) for session in all_sessions
        )
        total_window = (latest_time - earliest_start).total_seconds()
        
        # Calculate downtime
        total_downtime = max(0, total_window - total_uptime)
        
        # Calculate uptime percentage
        uptime_percentage = (total_uptime / total_window * 100) if total_window > 0 else 0
        
        # Session statistics
        if session_durations:
            avg_duration = sum(session_durations) / len(session_durations)
            longest_duration = max(session_durations)
            shortest_duration = min(session_durations)
        else:
            avg_duration = current_uptime
            longest_duration = current_uptime
            shortest_duration = current_uptime
        
        return UptimeStatistics(
            container_id=container_id,
            container_name=all_sessions[0].container_name,
            total_uptime_seconds=total_uptime,
            total_downtime_seconds=total_downtime,
            uptime_sessions=len(all_sessions),
            average_session_duration=avg_duration,
            longest_session_duration=longest_duration,
            shortest_session_duration=shortest_duration,
            current_uptime_seconds=current_uptime,
            uptime_percentage=uptime_percentage,
            last_start_time=last_start_time,
            last_stop_time=last_stop_time
        )
    
    def get_all_running_containers(self) -> List[UptimeRecord]:
        """Get all currently running containers."""
        return list(self.active_sessions.values())
    
    def get_uptime_summary(self) -> Dict[str, any]:
        """Get summary of all container uptimes."""
        all_containers = set()
        all_containers.update(self.active_sessions.keys())
        all_containers.update(self.completed_sessions.keys())
        
        if not all_containers:
            return {
                "total_containers": 0,
                "running_containers": 0,
                "stopped_containers": 0
            }
        
        running_count = len(self.active_sessions)
        total_count = len(all_containers)
        
        # Calculate overall statistics
        total_uptime = 0.0
        total_sessions = 0
        uptime_percentages = []
        
        for container_id in all_containers:
            stats = self.get_uptime_statistics(container_id)
            if stats:
                total_uptime += stats.total_uptime_seconds
                total_sessions += stats.uptime_sessions
                uptime_percentages.append(stats.uptime_percentage)
        
        summary = {
            "total_containers": total_count,
            "running_containers": running_count,
            "stopped_containers": total_count - running_count,
            "total_uptime_hours": total_uptime / 3600,
            "total_sessions": total_sessions,
            "average_uptime_percentage": sum(uptime_percentages) / len(uptime_percentages) if uptime_percentages else 0
        }
        
        # Find best and worst performers
        if uptime_percentages:
            best_uptime = max(uptime_percentages)
            worst_uptime = min(uptime_percentages)
            
            summary["best_uptime_percentage"] = best_uptime
            summary["worst_uptime_percentage"] = worst_uptime
            
            # Availability distribution
            excellent = sum(1 for p in uptime_percentages if p >= 99.9)
            good = sum(1 for p in uptime_percentages if 99.0 <= p < 99.9)
            fair = sum(1 for p in uptime_percentages if 95.0 <= p < 99.0)
            poor = sum(1 for p in uptime_percentages if p < 95.0)
            
            summary["availability_distribution"] = {
                "excellent": excellent,
                "good": good,
                "fair": fair,
                "poor": poor
            }
        
        return summary
    
    def add_uptime_callback(self, callback) -> None:
        """Add callback to be called when uptime sessions end."""
        self.uptime_callbacks.append(callback)
    
    def remove_uptime_callback(self, callback) -> None:
        """Remove uptime callback."""
        if callback in self.uptime_callbacks:
            self.uptime_callbacks.remove(callback)
    
    def cleanup_old_data(self) -> None:
        """Clean up old uptime data outside tracking window."""
        for container_id in list(self.completed_sessions.keys()):
            self._cleanup_old_sessions(container_id)
    
    def get_containers_by_availability(self, threshold: float = 95.0) -> Tuple[List[str], List[str]]:
        """
        Get containers above and below availability threshold.
        
        Returns:
            Tuple of (high_availability_containers, low_availability_containers)
        """
        high_availability = []
        low_availability = []
        
        all_containers = set()
        all_containers.update(self.active_sessions.keys())
        all_containers.update(self.completed_sessions.keys())
        
        for container_id in all_containers:
            stats = self.get_uptime_statistics(container_id)
            if stats:
                if stats.uptime_percentage >= threshold:
                    high_availability.append(container_id)
                else:
                    low_availability.append(container_id)
        
        return high_availability, low_availability