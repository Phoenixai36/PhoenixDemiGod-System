"""
Core interfaces for the Phoenix DemiGod system.

These interfaces define the contracts that all components must follow
to ensure modularity and interoperability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Health status enumeration for system components."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Health:
    """Health information for a component."""
    
    def __init__(self, status: HealthStatus, message: str = "", details: Dict = None):
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class Message:
    """Message for inter-component communication."""
    
    def __init__(self, message_type: str, payload: Any, sender: str = "", 
                 recipients: List[str] = None, priority: int = 0, ttl: int = 3600):
        self.id = f"{datetime.now().timestamp()}_{sender}_{message_type}"
        self.message_type = message_type
        self.payload = payload
        self.sender = sender
        self.recipients = recipients or []
        self.priority = priority
        self.ttl = ttl
        self.timestamp = datetime.now()


class Subsystem(ABC):
    """Interface for all subsystems in the Phoenix DemiGod system."""
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """Initialize the subsystem with configuration."""
        pass
        
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input data and return results."""
        pass
        
    @abstractmethod
    def get_health(self) -> Health:
        """Get the current health status of the subsystem."""
        pass
        
    @abstractmethod
    def shutdown(self) -> None:
        """Gracefully shutdown the subsystem."""
        pass


class CommunicationChannel(ABC):
    """Interface for communication between nodes."""
    
    @abstractmethod
    async def send_message(self, target: str, message: Message) -> bool:
        """Send a message to a target node."""
        pass
        
    @abstractmethod
    async def receive_message(self) -> Optional[Message]:
        """Receive a message from any node."""
        pass
        
    @abstractmethod
    async def broadcast(self, message: Message) -> bool:
        """Broadcast a message to all nodes."""
        pass


class StateObserver(ABC):
    """Interface for observing state changes."""
    
    @abstractmethod
    def on_state_changed(self, node_path: str, old_value: Any, new_value: Any) -> None:
        """Called when a state node changes."""
        pass


class PatternDetector(ABC):
    """Interface for pattern detection algorithms."""
    
    @abstractmethod
    def detect_patterns(self, data: Any) -> List[Dict]:
        """Detect patterns in the provided data."""
        pass


class SubsystemTemplate(ABC):
    """Interface for subsystem templates."""
    
    @abstractmethod
    def generate(self, parameters: Dict) -> str:
        """Generate subsystem code from template and parameters."""
        pass
        
    @abstractmethod
    def validate(self, generated_code: str) -> bool:
        """Validate the generated subsystem code."""
        pass