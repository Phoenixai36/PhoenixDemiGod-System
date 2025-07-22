"""
Unit tests for core data models
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.phoenixxhydra.core.models import (
    SystemEvent, EventType, TaskResult, CommunicationMessage,
    CellStatus, HydraHeadType, P2PNetworkNode, InteractionResult
)


class TestSystemEvent:
    """Test SystemEvent data model"""
    
    def test_system_event_creation(self):
        """Test basic SystemEvent creation"""
        event = SystemEvent(
            event_type=EventType.CELL_SPAWN,
            source_component="test_component",
            data={"test": "data"}
        )
        
        assert event.event_type == EventType.CELL_SPAWN
        assert event.source_component == "test_component"
        assert event.data["test"] == "data"
        assert event.priority == 1  # default
        assert event.complexity_score == 1.0  # default
        assert isinstance(event.timestamp, datetime)
        assert len(event.event_id) > 0
    
    def test_system_event_with_custom_values(self):
        """Test SystemEvent with custom priority and complexity"""
        event = SystemEvent(
            event_type=EventType.SYSTEM_ALERT,
            source_component="critical_component",
            priority=5,
            complexity_score=8.5
        )
        
        assert event.priority == 5
        assert event.complexity_score == 8.5
    
    def test_event_types_enum(self):
        """Test all EventType enum values"""
        expected_types = [
            "cell_spawn", "cell_death", "cell_mutation",
            "network_partition", "network_heal", "system_alert",
            "performance_threshold", "genetic_evolution", "chaos_test"
        ]
        
        actual_types = [event_type.value for event_type in EventType]
        
        for expected in expected_types:
            assert expected in actual_types


class TestTaskResult:
    """Test TaskResult data model"""
    
    def test_successful_task_result(self):
        """Test successful task result creation"""
        result = TaskResult(
            task_id="test_task_123",
            success=True,
            result_data={"output": "success"},
            execution_time=1.5
        )
        
        assert result.task_id == "test_task_123"
        assert result.success is True
        assert result.result_data["output"] == "success"
        assert result.execution_time == 1.5
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)
    
    def test_failed_task_result(self):
        """Test failed task result creation"""
        result = TaskResult(
            task_id="failed_task_456",
            success=False,
            error_message="Task failed due to network error"
        )
        
        assert result.task_id == "failed_task_456"
        assert result.success is False
        assert result.error_message == "Task failed due to network error"
        assert result.result_data == {}  # default empty dict


class TestCommunicationMessage:
    """Test CommunicationMessage data model"""
    
    def test_communication_message_creation(self):
        """Test basic communication message creation"""
        message = CommunicationMessage(
            sender_id="cell_001",
            receiver_id="cell_002",
            message_type="genetic_data",
            payload={"genes": ["gene1", "gene2"]}
        )
        
        assert message.sender_id == "cell_001"
        assert message.receiver_id == "cell_002"
        assert message.message_type == "genetic_data"
        assert message.payload["genes"] == ["gene1", "gene2"]
        assert message.ttl == 300  # default
        assert message.encrypted is True  # default
        assert len(message.message_id) > 0
        assert isinstance(message.timestamp, datetime)
    
    def test_message_with_custom_ttl(self):
        """Test message with custom TTL"""
        message = CommunicationMessage(
            sender_id="cell_003",
            receiver_id="cell_004",
            ttl=600,
            encrypted=False
        )
        
        assert message.ttl == 600
        assert message.encrypted is False


class TestEnums:
    """Test enum definitions"""
    
    def test_cell_status_enum(self):
        """Test CellStatus enum values"""
        expected_statuses = [
            "initializing", "active", "idle", "stressed",
            "failing", "regenerating", "terminated"
        ]
        
        actual_statuses = [status.value for status in CellStatus]
        
        for expected in expected_statuses:
            assert expected in actual_statuses
    
    def test_hydra_head_type_enum(self):
        """Test HydraHeadType enum values"""
        expected_types = [
            "neurosymbolic", "genetic_evolution", "mcp_orchestration",
            "personalization", "knowledge_detection", "multimodal_analysis",
            "hybrid_strategy"
        ]
        
        actual_types = [head_type.value for head_type in HydraHeadType]
        
        for expected in expected_types:
            assert expected in actual_types
        
        # Ensure we have exactly 7 HYDRA heads
        assert len(actual_types) == 7


class TestP2PNetworkNode:
    """Test P2PNetworkNode data model"""
    
    def test_network_node_creation(self):
        """Test P2P network node creation"""
        node = P2PNetworkNode(
            node_id="node_001",
            address="192.168.1.100",
            port=8080,
            public_key="test_public_key_123",
            capabilities=["routing", "storage"]
        )
        
        assert node.node_id == "node_001"
        assert node.address == "192.168.1.100"
        assert node.port == 8080
        assert node.public_key == "test_public_key_123"
        assert node.capabilities == ["routing", "storage"]
        assert node.trust_score == 0.5  # default
        assert isinstance(node.last_seen, datetime)


class TestInteractionResult:
    """Test InteractionResult data model"""
    
    def test_successful_interaction(self):
        """Test successful interaction result"""
        interaction = InteractionResult(
            success=True,
            impact_score=10,
            trust_change=5,
            interaction_type="collaboration"
        )
        
        assert interaction.success is True
        assert interaction.neutral is False  # default
        assert interaction.impact_score == 10
        assert interaction.trust_change == 5
        assert interaction.interaction_type == "collaboration"
        assert isinstance(interaction.timestamp, datetime)
    
    def test_neutral_interaction(self):
        """Test neutral interaction result"""
        interaction = InteractionResult(
            success=False,
            neutral=True,
            impact_score=0,
            trust_change=0
        )
        
        assert interaction.success is False
        assert interaction.neutral is True
        assert interaction.impact_score == 0
        assert interaction.trust_change == 0
    
    def test_negative_interaction(self):
        """Test negative interaction result"""
        interaction = InteractionResult(
            success=False,
            impact_score=-5,
            trust_change=-10,
            interaction_type="conflict"
        )
        
        assert interaction.success is False
        assert interaction.impact_score == -5
        assert interaction.trust_change == -10
        assert interaction.interaction_type == "conflict"


# Mock implementations for testing abstract classes
class MockDigitalCell:
    """Mock implementation of DigitalCell for testing"""
    
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
    
    async def initialize(self) -> bool:
        self.status = CellStatus.ACTIVE
        return True
    
    async def process_task(self, task: dict) -> TaskResult:
        return TaskResult(task_id="mock_task", success=True)
    
    async def communicate(self, message: CommunicationMessage) -> bool:
        return True
    
    async def health_check(self) -> dict:
        return {"status": "healthy", "fitness": self.fitness_score}
    
    async def update_fitness_score(self, new_score: float):
        """Update cell fitness score"""
        self.fitness_score = new_score
        self.last_activity = datetime.now()


class TestMockDigitalCell:
    """Test mock digital cell implementation"""
    
    @pytest.mark.asyncio
    async def test_mock_cell_initialization(self):
        """Test mock cell initialization"""
        cell = MockDigitalCell("test_cell_001", HydraHeadType.NEUROSYMBOLIC)
        
        assert cell.cell_id == "test_cell_001"
        assert cell.head_type == HydraHeadType.NEUROSYMBOLIC
        assert cell.status == CellStatus.INITIALIZING
        
        # Test initialization
        result = await cell.initialize()
        assert result is True
        assert cell.status == CellStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_mock_cell_task_processing(self):
        """Test mock cell task processing"""
        cell = MockDigitalCell("test_cell_002", HydraHeadType.GENETIC_EVOLUTION)
        
        task = {"type": "test_task", "data": "test_data"}
        result = await cell.process_task(task)
        
        assert isinstance(result, TaskResult)
        assert result.success is True
        assert result.task_id == "mock_task"
    
    @pytest.mark.asyncio
    async def test_mock_cell_communication(self):
        """Test mock cell communication"""
        cell = MockDigitalCell("test_cell_003", HydraHeadType.PERSONALIZATION)
        
        message = CommunicationMessage(
            sender_id="other_cell",
            receiver_id=cell.cell_id,
            payload={"test": "message"}
        )
        
        result = await cell.communicate(message)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_mock_cell_health_check(self):
        """Test mock cell health check"""
        cell = MockDigitalCell("test_cell_004", HydraHeadType.KNOWLEDGE_DETECTION)
        cell.fitness_score = 0.85
        
        health = await cell.health_check()
        
        assert health["status"] == "healthy"
        assert health["fitness"] == 0.85
    
    @pytest.mark.asyncio
    async def test_fitness_score_update(self):
        """Test fitness score update"""
        cell = MockDigitalCell("test_cell_005", HydraHeadType.MULTIMODAL_ANALYSIS)
        
        initial_activity = cell.last_activity
        await cell.update_fitness_score(0.92)
        
        assert cell.fitness_score == 0.92
        assert cell.last_activity > initial_activity


if __name__ == "__main__":
    pytest.main([__file__])