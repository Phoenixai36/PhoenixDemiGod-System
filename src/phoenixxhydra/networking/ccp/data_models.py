"""
Data models for the Cellular Communication Protocol (CCP).

This module defines the core data structures used in the CCP system,
including message formats, routing information, and session management.
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MessageId(str):
    """Unique identifier for messages in the CCP system."""
    
    @classmethod
    def generate(cls) -> "MessageId":
        """Generate a new unique message ID."""
        return cls(str(uuid.uuid4()))


class MessagePriority(enum.Enum):
    """Priority levels for message transmission."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class MessageSensitivity(enum.Enum):
    """Sensitivity levels for message content."""
    CRITICAL = 0
    SENSITIVE = 1
    STANDARD = 2
    PUBLIC = 3


class EncryptionLevel(enum.Enum):
    """Encryption levels for message security."""
    QUANTUM = 0   # Quantum-resistant encryption
    MAXIMUM = 1   # Maximum security encryption
    HIGH = 2      # High security encryption
    STANDARD = 3  # Standard encryption
    MINIMAL = 4   # Minimal encryption for non-sensitive data
    NONE = 5      # No encryption (use with caution)


@dataclass
class ResonanceParameters:
    """
    Parameters for the cellular resonance mechanism.
    
    Resonance is a specialized communication mode that allows for
    enhanced message propagation across the cellular network.
    """
    amplitude: float = 1.0
    frequency: float = 1.0
    decay_rate: float = 0.1
    harmonic_factor: float = 0.5
    phase_shift: float = 0.0


@dataclass
class Route:
    """
    Routing information for message delivery.
    
    Defines the path a message should take through the cellular network.
    """
    hops: List[str] = field(default_factory=list)
    max_hops: int = 10
    preferred_path: Optional[List[str]] = None
    avoid_cells: List[str] = field(default_factory=list)
    is_direct: bool = False


@dataclass
class NetworkConditions:
    """Current network conditions affecting message transmission."""
    congestion_level: float = 0.0  # 0.0 to 1.0
    latency_ms: int = 0
    bandwidth_kbps: int = 1000
    packet_loss_percent: float = 0.0
    jitter_ms: int = 0


@dataclass
class Message:
    """
    A message in the CCP system.
    
    Represents a unit of communication between digital cells.
    """
    id: MessageId = field(default_factory=MessageId.generate)
    source_cell_id: str = ""
    target_cell_id: str = ""
    content: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MessagePriority = MessagePriority.NORMAL
    sensitivity: MessageSensitivity = MessageSensitivity.STANDARD
    metadata: Dict[str, Any] = field(default_factory=dict)
    route: Optional[Route] = None
    session_id: Optional[str] = None


@dataclass
class EncryptedMessage:
    """An encrypted message in the CCP system."""
    id: MessageId = field(default_factory=MessageId.generate)
    encrypted_content: bytes = field(default_factory=bytes)
    encryption_level: EncryptionLevel = EncryptionLevel.STANDARD
    source_cell_id: str = ""
    target_cell_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    route: Optional[Route] = None
    session_id: Optional[str] = None


@dataclass
class Session:
    """
    A communication session between digital cells.
    
    Sessions provide a context for ongoing communication between cells,
    enabling stateful interactions and optimized message delivery.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cell_id: str = ""
    established_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    encryption_level: EncryptionLevel = EncryptionLevel.STANDARD
    metadata: Dict[str, Any] = field(default_factory=dict)
    network_conditions: NetworkConditions = field(default_factory=NetworkConditions)
    is_active: bool = True
