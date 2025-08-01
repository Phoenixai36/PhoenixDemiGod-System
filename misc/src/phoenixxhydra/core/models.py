"""
Core data models for the PHOENIXxHYDRA system
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
import asyncio


class EventType(Enum):
    """System event types"""
    CELL_SPAWN = "cell_spawn"
    CELL_DEATH = "cell_death"
    CELL_MUTATION = "cell_mutation"
    NETWORK_PARTITION = "network_partition"
    NETWORK_HEAL = "network_heal"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_THRESHOLD = "performance_threshold"
    GENETIC_EVOLUTION = "genetic_evolution"
    CHAOS_TEST = "chaos_test"


class CellStatus(Enum):
    """Digital cell status states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    STRESSED = "stressed"
    FAILING = "failing"
    REGENERATING = "regenerating"
    TERMINATED = "terminated"


class HydraHeadType(Enum):
    """Types of HYDRA heads"""
    NEUROSYMBOLIC = "neurosymbolic"
    GENETIC_EVOLUTION = "genetic_evolution"
    MCP_ORCHESTRATION = "mcp_orchestration"
    PERSONALIZATION = "personalization"
    KNOWLEDGE_DETECTION = "knowledge_detection"
    MULTIMODAL_ANALYSIS = "multimodal_analysis"
    HYBRID_STRATEGY = "hybrid_strategy"


@dataclass
class SystemEvent:
    """Base system event structure"""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.SYSTEM_ALERT
    timestamp: datetime = field(default_factory=datetime.now)
    source_component: str = ""
    target_component: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1=low, 5=critical
    complexity_score: float = 1.0


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CommunicationMessage:
    """P2P communication message structure"""
    message_id: str = field(default_factory=lambda: str(uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: str = "data"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 300  # Time to live in seconds
    encrypted: bool = True


class DigitalCell(ABC):
    """Abstract base class for digital cells"""
    
    def __init__(self, cell_id: str, head_type: HydraHeadType):
        self.cell_id = cell_id
        self.head_type = head_type
        self.status = CellStatus.INITIALIZING
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.performance_metrics = {}
        self.genes = []
        self.personality_matrix = None
        self.trust_relationships = {}
        self.fitness_score = 0.0
        self.buffs = []
        self.debuffs = []
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the cell"""
        pass
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process a task assigned to this cell"""
        pass
    
    @abstractmethod
    async def communicate(self, message: CommunicationMessage) -> bool:
        """Handle incoming communication"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return cell health status"""
        pass
    
    async def update_fitness_score(self, new_score: float):
        """Update cell fitness score"""
        self.fitness_score = new_score
        self.last_activity = datetime.now()


class HydraHead(ABC):
    """Abstract base class for HYDRA heads"""
    
    def __init__(self, head_type: HydraHeadType, max_cells: int = 100):
        self.head_type = head_type
        self.head_id = f"{head_type.value}_{uuid4()}"
        self.max_cells = max_cells
        self.cells: Dict[str, DigitalCell] = {}
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.performance_metrics = {}
        
    @abstractmethod
    async def spawn_cell(self) -> DigitalCell:
        """Spawn a new cell under this head"""
        pass
    
    @abstractmethod
    async def process_event(self, event: SystemEvent) -> TaskResult:
        """Process system event"""
        pass
    
    @abstractmethod
    async def coordinate_cells(self, task: Dict[str, Any]) -> List[TaskResult]:
        """Coordinate task execution across cells"""
        pass
    
    async def register_cell(self, cell: DigitalCell):
        """Register a cell with this head"""
        self.cells[cell.cell_id] = cell
        self.last_activity = datetime.now()
    
    async def remove_cell(self, cell_id: str):
        """Remove a cell from this head"""
        if cell_id in self.cells:
            del self.cells[cell_id]
            self.last_activity = datetime.now()
    
    async def get_active_cells(self) -> List[DigitalCell]:
        """Get all active cells"""
        return [cell for cell in self.cells.values() 
                if cell.status == CellStatus.ACTIVE]


class PhoenixCore(ABC):
    """Abstract base class for Phoenix Core orchestrator"""
    
    def __init__(self):
        self.core_id = f"phoenix_core_{uuid4()}"
        self.hydra_heads: Dict[HydraHeadType, HydraHead] = {}
        self.event_queue = asyncio.Queue()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.system_state = {}
        
    @abstractmethod
    async def register_hydra_head(self, head: HydraHead):
        """Register a HYDRA head with the core"""
        pass
    
    @abstractmethod
    async def process_system_event(self, event: SystemEvent) -> TaskResult:
        """Process system-wide events"""
        pass
    
    @abstractmethod
    async def coordinate_heads(self, event: SystemEvent) -> List[TaskResult]:
        """Coordinate response across HYDRA heads"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        pass


@dataclass
class P2PNetworkNode:
    """P2P network node information"""
    node_id: str
    address: str
    port: int
    public_key: str
    last_seen: datetime = field(default_factory=datetime.now)
    trust_score: float = 0.5
    capabilities: List[str] = field(default_factory=list)


class P2PNetworkManager(ABC):
    """Abstract base class for P2P network management"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.peers: Dict[str, P2PNetworkNode] = {}
        self.routing_table = {}
        
    @abstractmethod
    async def discover_peers(self) -> List[P2PNetworkNode]:
        """Discover available peers"""
        pass
    
    @abstractmethod
    async def send_message(self, message: CommunicationMessage) -> bool:
        """Send message to peer"""
        pass
    
    @abstractmethod
    async def receive_message(self) -> Optional[CommunicationMessage]:
        """Receive message from peer"""
        pass
    
    @abstractmethod
    async def update_routing_table(self):
        """Update network routing table"""
        pass


class CellLifecycleManager(ABC):
    """Abstract base class for cell lifecycle management"""
    
    @abstractmethod
    async def spawn_cell(self, head_type: HydraHeadType, 
                        gene_combination: List[Any]) -> DigitalCell:
        """Spawn a new cell with genetic traits"""
        pass
    
    @abstractmethod
    async def regenerate_cell(self, failed_cell_id: str, 
                             improvement_data: Dict[str, Any]) -> DigitalCell:
        """Regenerate a failed cell with improvements"""
        pass
    
    @abstractmethod
    async def monitor_cell_health(self, cell: DigitalCell) -> Dict[str, Any]:
        """Monitor cell health and performance"""
        pass
    
    @abstractmethod
    async def terminate_cell(self, cell_id: str, reason: str) -> bool:
        """Terminate a cell"""
        pass


@dataclass
class InteractionResult:
    """Result of cell-to-cell interaction"""
    success: bool
    neutral: bool = False
    impact_score: int = 0
    trust_change: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    interaction_type: str = "general"