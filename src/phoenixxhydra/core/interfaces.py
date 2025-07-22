"""
Core interfaces for the PHOENIXxHYDRA system
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from .models import (
    SystemEvent, TaskResult, DigitalCell, HydraHead, 
    CommunicationMessage, InteractionResult, HydraHeadType
)


class IEventBus(ABC):
    """Interface for system event bus"""
    
    @abstractmethod
    async def publish(self, event: SystemEvent) -> bool:
        """Publish an event to the bus"""
        pass
    
    @abstractmethod
    async def subscribe(self, event_types: List[str], 
                      callback: callable) -> str:
        """Subscribe to specific event types"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        pass
    
    @abstractmethod
    async def get_event_history(self, limit: int = 100) -> List[SystemEvent]:
        """Get recent event history"""
        pass


class IGenePool(ABC):
    """Interface for genetic algorithm gene pool"""
    
    @abstractmethod
    async def generate_combination(self, count: int, base: int = 20) -> List[Any]:
        """Generate a combination of genes"""
        pass
    
    @abstractmethod
    async def mutate_genes(self, genes: List[Any], 
                          mutation_rate: float = 0.1) -> List[Any]:
        """Apply mutation to genes"""
        pass
    
    @abstractmethod
    async def crossover_genes(self, parent1: List[Any], 
                             parent2: List[Any]) -> List[Any]:
        """Perform genetic crossover"""
        pass
    
    @abstractmethod
    async def evaluate_fitness(self, genes: List[Any], 
                              performance_data: Dict[str, Any]) -> float:
        """Evaluate genetic fitness"""
        pass


class IPersonalityMatrix(ABC):
    """Interface for Rubik personality matrix"""
    
    @abstractmethod
    async def generate_personality(self, base: int = 20) -> Dict[str, Any]:
        """Generate personality matrix"""
        pass
    
    @abstractmethod
    async def calculate_mood(self, personality: Dict[str, Any], 
                           recent_interactions: List[InteractionResult]) -> str:
        """Calculate current mood"""
        pass
    
    @abstractmethod
    async def determine_archetype(self, personality: Dict[str, Any]) -> str:
        """Determine personality archetype"""
        pass
    
    @abstractmethod
    async def generate_astrological_profile(self) -> Dict[str, Any]:
        """Generate astrological influence profile"""
        pass


class IRelationshipManager(ABC):
    """Interface for Sims-style relationship management"""
    
    @abstractmethod
    async def update_relationship(self, cell_id: str, other_cell_id: str, 
                                 interaction: InteractionResult) -> float:
        """Update relationship score between cells"""
        pass
    
    @abstractmethod
    async def get_relationship_score(self, cell_id: str, 
                                   other_cell_id: str) -> float:
        """Get relationship score between cells"""
        pass
    
    @abstractmethod
    async def calculate_trust_level(self, relationship_score: float) -> str:
        """Calculate trust level from relationship score"""
        pass
    
    @abstractmethod
    async def get_trusted_cells(self, cell_id: str, 
                              min_trust: float = 0.7) -> List[str]:
        """Get list of trusted cells"""
        pass


class ICellRegistry(ABC):
    """Interface for cell registry and management"""
    
    @abstractmethod
    async def register_cell(self, cell: DigitalCell) -> bool:
        """Register a cell in the system"""
        pass
    
    @abstractmethod
    async def unregister_cell(self, cell_id: str) -> bool:
        """Unregister a cell from the system"""
        pass
    
    @abstractmethod
    async def get_cell(self, cell_id: str) -> Optional[DigitalCell]:
        """Get cell by ID"""
        pass
    
    @abstractmethod
    async def get_cells_by_head(self, head_type: HydraHeadType) -> List[DigitalCell]:
        """Get all cells belonging to a specific head"""
        pass
    
    @abstractmethod
    async def get_active_cells(self) -> List[DigitalCell]:
        """Get all active cells in the system"""
        pass
    
    @abstractmethod
    async def get_cell_count_by_head(self) -> Dict[HydraHeadType, int]:
        """Get cell count for each head"""
        pass


class IOrchestrationAgent(ABC):
    """Interface for orchestrating agents"""
    
    @abstractmethod
    async def process_event(self, event: SystemEvent) -> TaskResult:
        """Process a system event"""
        pass
    
    @abstractmethod
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        pass
    
    @abstractmethod
    async def configure_agent(self, config: Dict[str, Any]) -> bool:
        """Configure agent parameters"""
        pass


class INickOrchestrator(IOrchestrationAgent):
    """Interface for Nick - Tesla-inspired orchestrator"""
    
    @abstractmethod
    async def calculate_resonance_frequency(self, event: SystemEvent) -> float:
        """Calculate optimal Tesla coil resonance frequency"""
        pass
    
    @abstractmethod
    async def apply_sacred_geometry(self, resources: List[Any], 
                                   capacity_needed: float) -> Dict[str, Any]:
        """Apply sacred geometry for resource distribution"""
        pass
    
    @abstractmethod
    async def create_orchestration_plan(self, event: SystemEvent) -> Dict[str, Any]:
        """Create consciousness-driven orchestration plan"""
        pass


class IKaiAgent(IOrchestrationAgent):
    """Interface for Kai - Chaos engineering agent"""
    
    @abstractmethod
    async def create_chaos_scenario(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create targeted chaos scenario"""
        pass
    
    @abstractmethod
    async def setup_debate_arena(self, cells: List[DigitalCell]) -> Dict[str, Any]:
        """Setup debate arena for cell improvement"""
        pass
    
    @abstractmethod
    async def analyze_system_vulnerabilities(self, 
                                           system_state: Dict[str, Any]) -> List[str]:
        """Analyze system for potential weak points"""
        pass


class IThanatosAgent(IOrchestrationAgent):
    """Interface for Thanatos - Digital natural selection agent"""
    
    @abstractmethod
    async def evaluate_cell_fitness(self, cells: List[DigitalCell]) -> Dict[str, float]:
        """Evaluate fitness of cell population"""
        pass
    
    @abstractmethod
    async def apply_selection_pressure(self, 
                                     fitness_scores: Dict[str, float]) -> List[str]:
        """Apply selection pressure and return cells for elimination"""
        pass
    
    @abstractmethod
    async def track_evolution_progress(self, generation_data: Dict[str, Any]) -> bool:
        """Track evolutionary progress over generations"""
        pass


class INisoAgent(IOrchestrationAgent):
    """Interface for NISO - Economic module agent"""
    
    @abstractmethod
    async def allocate_resources(self, cells: List[DigitalCell], 
                               available_resources: Dict[str, float]) -> Dict[str, float]:
        """Allocate computational resources to cells"""
        pass
    
    @abstractmethod
    async def distribute_rewards(self, performance_data: Dict[str, float]) -> Dict[str, float]:
        """Distribute rewards based on performance"""
        pass
    
    @abstractmethod
    async def calculate_economic_metrics(self) -> Dict[str, Any]:
        """Calculate system economic metrics"""
        pass


class IMapEAgent(IOrchestrationAgent):
    """Interface for MAP-E - Natural language interface agent"""
    
    @abstractmethod
    async def process_natural_language_query(self, query: str) -> str:
        """Process natural language query about the system"""
        pass
    
    @abstractmethod
    async def generate_system_report(self, report_type: str) -> str:
        """Generate human-readable system report"""
        pass
    
    @abstractmethod
    async def translate_technical_data(self, data: Dict[str, Any]) -> str:
        """Translate technical data to natural language"""
        pass


class ISecurityManager(ABC):
    """Interface for security and trust management"""
    
    @abstractmethod
    async def encrypt_message(self, message: CommunicationMessage) -> bytes:
        """Encrypt a communication message"""
        pass
    
    @abstractmethod
    async def decrypt_message(self, encrypted_data: bytes) -> CommunicationMessage:
        """Decrypt a communication message"""
        pass
    
    @abstractmethod
    async def verify_cell_identity(self, cell_id: str, 
                                  credentials: Dict[str, Any]) -> bool:
        """Verify cell identity and credentials"""
        pass
    
    @abstractmethod
    async def detect_malicious_behavior(self, 
                                      behavior_data: Dict[str, Any]) -> bool:
        """Detect potentially malicious behavior"""
        pass


class IPerformanceMonitor(ABC):
    """Interface for performance monitoring"""
    
    @abstractmethod
    async def collect_metrics(self, component_id: str) -> Dict[str, Any]:
        """Collect performance metrics from component"""
        pass
    
    @abstractmethod
    async def analyze_performance_trends(self, 
                                       metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends"""
        pass
    
    @abstractmethod
    async def detect_performance_anomalies(self, 
                                         current_metrics: Dict[str, Any]) -> List[str]:
        """Detect performance anomalies"""
        pass
    
    @abstractmethod
    async def generate_optimization_recommendations(self, 
                                                  analysis_data: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        pass


class IConfigurationManager(ABC):
    """Interface for system configuration management"""
    
    @abstractmethod
    async def load_configuration(self, config_path: str) -> Dict[str, Any]:
        """Load system configuration"""
        pass
    
    @abstractmethod
    async def save_configuration(self, config: Dict[str, Any], 
                               config_path: str) -> bool:
        """Save system configuration"""
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return errors"""
        pass
    
    @abstractmethod
    async def get_default_configuration(self) -> Dict[str, Any]:
        """Get default system configuration"""
        pass