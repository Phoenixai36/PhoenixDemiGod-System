"""
Tests for the Cellular Communication Protocol core functionality.
"""

import asyncio
import pytest
import uuid

from src.phoenixxhydra.networking.ccp.core import CCPCore, CCPConfig, MessageOptions
from src.phoenixxhydra.networking.ccp.data_models import (
    Message, MessageId, MessagePriority, MessageSensitivity
)


class MockCell:
    """Mock cell for testing."""
    
    def __init__(self, cell_id=None):
        """Initialize mock cell."""
        self.cell_id = cell_id or str(uuid.uuid4())
        self.tesla_affinity = 0.7
        self.genes = []


@pytest.mark.asyncio
async def test_ccp_core_initialization():
    """Test CCP core initialization."""
    # Create a mock cell
    cell = MockCell("test-cell-1")
    
    # Create CCP core
    ccp = CCPCore(cell)
    
    # Verify initialization
    assert ccp.cell.cell_id == "test-cell-1"
    assert isinstance(ccp.config, CCPConfig)
    assert ccp.session_manager is not None


@pytest.mark.asyncio
async def test_message_serialization():
    """Test message serialization and deserialization."""
    # Create a message
    original_message = Message(
        type="test",
        content={"key": "value"},
        metadata={"meta": "data"},
        priority=MessagePriority.HIGH,
        sensitivity=MessageSensitivity.CONFIDENTIAL
    )
    
    # Serialize
    serialized = original_message.serialize()
    
    # Deserialize
    deserialized = Message.deserialize(serialized)
    
    # Verify
    assert deserialized.id.value == original_message.id.value
    assert deserialized.type == "test"
    assert deserialized.content == {"key": "value"}
    assert deserialized.metadata == {"meta": "data"}
    assert deserialized.priority == MessagePriority.HIGH
    assert deserialized.sensitivity == MessageSensitivity.CONFIDENTIAL


@pytest.mark.asyncio
async def test_message_handler_registration():
    """Test message handler registration."""
    # Create a mock cell
    cell = MockCell("test-cell-2")
    
    # Create CCP core
    ccp = CCPCore(cell)
    
    # Create a mock handler
    async def mock_handler(message):
        return message
    
    # Register handler
    await ccp.register_message_handler("test_type", mock_handler)
    
    # Verify registration
    assert "test_type" in ccp.message_handlers
    assert mock_handler in ccp.message_handlers["test_type"]


@pytest.mark.asyncio
async def test_session_management():
    """Test session management."""
    # Create a mock cell
    cell = MockCell("test-cell-3")
    
    # Create CCP core
    ccp = CCPCore(cell)
    
    # Get a session
    session = await ccp.session_manager.get_or_create_session("target-cell-1")
    
    # Verify session
    assert session.remote_cell_id == "target-cell-1"
    assert session.trust_level == 0  # Default trust level
    
    # Update session
    updated_session = await ccp.session_manager.update_session(
        "target-cell-1",
        trust_level=1,
        genetic_compatibility=0.8
    )
    
    # Verify update
    assert updated_session.trust_level == 1
    assert updated_session.genetic_compatibility == 0.8
    
    # Close session
    await ccp.session_manager.close_session("target-cell-1")
    
    # Verify session is closed (will create a new one)
    new_session = await ccp.session_manager.get_or_create_session("target-cell-1")
    assert new_session.session_id != session.session_id