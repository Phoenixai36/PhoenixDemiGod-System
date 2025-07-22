"""
Unit tests for the NucleusManager.
"""

import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from phoenix_demigod.core.nucleus import NucleusManager
from phoenix_demigod.core.state_tree import StateNode, StateTree


@pytest.fixture
def config_file():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        config = {
            "system": {
                "name": "phoenix-demigod-test",
                "version": "1.0.0",
                "environment": "test"
            },
            "nucleus": {
                "cycle_interval": 0.1,
                "max_subsystems": 10,
                "resource_limit": 0.8,
                "max_tree_depth": 5,
                "snapshot_interval": 0.5,
                "max_snapshots": 5
            },
            "traversal": {
                "pattern_confidence_threshold": 0.7,
                "complexity_threshold": 5.0,
                "gap_detection_sensitivity": 0.5
            },
            "differentiation": {
                "template_directory": "templates/",
                "validation_timeout": 1.0,
                "max_generation_attempts": 2
            },
            "regeneration": {
                "integrity_check_interval": 0.5,
                "checksum_algorithm": "sha256",
                "max_recovery_attempts": 3
            }
        }
        yaml.dump(config, f)
        config_path = f.name
    
    yield config_path
    
    # Clean up
    os.unlink(config_path)


@pytest.fixture
def nucleus():
    """Create a NucleusManager instance for testing."""
    return NucleusManager()


@pytest.mark.asyncio
async def test_initialize(nucleus, config_file):
    """Test initializing the NucleusManager."""
    # Initialize the nucleus
    result = await nucleus.initialize(config_file)
    
    # Check the result
    assert result is True
    assert nucleus.is_initialized is True
    assert nucleus.is_running is False
    
    # Check that the state tree was created
    assert nucleus.state_tree is not None
    assert nucleus.state_tree.root is not None
    assert nucleus.state_tree.root.id == "root"
    
    # Check that the engines were created
    assert nucleus.traversal_engine is not None
    assert nucleus.differentiation_engine is not None
    assert nucleus.regeneration_engine is not None


@pytest.mark.asyncio
async def test_initialize_missing_config(nucleus):
    """Test initializing with a missing configuration file."""
    # Try to initialize with a non-existent file
    result = await nucleus.initialize("nonexistent.yaml")
    
    # Check the result
    assert result is False
    assert nucleus.is_initialized is False


@pytest.mark.asyncio
async def test_start_stop(nucleus, config_file):
    """Test starting and stopping the NucleusManager."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Start the nucleus
    await nucleus.start()
    
    # Check that it's running
    assert nucleus.is_running is True
    assert nucleus.should_stop is False
    
    # Let it run for a short time
    await asyncio.sleep(0.2)
    
    # Stop the nucleus
    await nucleus.shutdown()
    
    # Check that it's stopped
    assert nucleus.is_running is False
    assert nucleus.should_stop is True


@pytest.mark.asyncio
async def test_get_stats(nucleus, config_file):
    """Test getting statistics from the NucleusManager."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Get stats
    stats = nucleus.get_stats()
    
    # Check the stats
    assert "start_time" in stats
    assert "uptime_seconds" in stats
    assert "cycle_count" in stats
    assert stats["cycle_count"] == 0
    assert stats["is_running"] is False


@pytest.mark.asyncio
async def test_update_resource_usage(nucleus, config_file):
    """Test updating resource usage."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Update resource usage
    await nucleus._update_resource_usage()
    
    # Check that the resource usage was updated
    resource_node = nucleus.state_tree.get_node("/runtime_state/resource_usage")
    assert resource_node is not None
    assert "cpu" in resource_node.data
    assert "memory" in resource_node.data
    assert "disk" in resource_node.data
    assert "network" in resource_node.data
    assert "updated_at" in resource_node.data


@pytest.mark.asyncio
async def test_update_performance_metrics(nucleus, config_file):
    """Test updating performance metrics."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Update a performance metric
    nucleus._update_performance_metrics("cycle_time", 0.123)
    
    # Check that the metric was updated
    metrics_node = nucleus.state_tree.get_node("/runtime_state/performance_metrics")
    assert metrics_node is not None
    assert metrics_node.data["cycle_time"] == 0.123


@pytest.mark.asyncio
async def test_main_loop_with_mocks(nucleus, config_file):
    """Test the main processing loop with mocked engines."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Mock the engines
    nucleus.traversal_engine.traverse = AsyncMock()
    nucleus.differentiation_engine.process_analysis = AsyncMock()
    nucleus.regeneration_engine.check_integrity = AsyncMock()
    nucleus.regeneration_engine.restore_integrity = AsyncMock()
    
    # Set up mock return values
    mock_analysis_report = MagicMock()
    mock_integrity_report = MagicMock()
    mock_integrity_report.is_healthy = True
    
    nucleus.traversal_engine.traverse.return_value = mock_analysis_report
    nucleus.differentiation_engine.process_analysis.return_value = MagicMock()
    nucleus.regeneration_engine.check_integrity.return_value = mock_integrity_report
    
    # Start the nucleus
    await nucleus.start()
    
    # Let it run for a short time
    await asyncio.sleep(0.2)
    
    # Stop the nucleus
    await nucleus.shutdown()
    
    # Check that the engines were called
    nucleus.traversal_engine.traverse.assert_called()
    nucleus.differentiation_engine.process_analysis.assert_called_with(
        mock_analysis_report, nucleus.state_tree
    )
    nucleus.regeneration_engine.check_integrity.assert_called_with(nucleus.state_tree)
    
    # Check that restore_integrity was not called (since is_healthy=True)
    nucleus.regeneration_engine.restore_integrity.assert_not_called()


@pytest.mark.asyncio
async def test_main_loop_with_unhealthy_report(nucleus, config_file):
    """Test the main processing loop with an unhealthy integrity report."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Mock the engines
    nucleus.traversal_engine.traverse = AsyncMock()
    nucleus.differentiation_engine.process_analysis = AsyncMock()
    nucleus.regeneration_engine.check_integrity = AsyncMock()
    nucleus.regeneration_engine.restore_integrity = AsyncMock()
    
    # Set up mock return values
    mock_analysis_report = MagicMock()
    mock_integrity_report = MagicMock()
    mock_integrity_report.is_healthy = False
    mock_integrity_report.issues = ["Test issue"]
    
    nucleus.traversal_engine.traverse.return_value = mock_analysis_report
    nucleus.differentiation_engine.process_analysis.return_value = MagicMock()
    nucleus.regeneration_engine.check_integrity.return_value = mock_integrity_report
    
    # Start the nucleus
    await nucleus.start()
    
    # Let it run for a short time
    await asyncio.sleep(0.2)
    
    # Stop the nucleus
    await nucleus.shutdown()
    
    # Check that restore_integrity was called
    nucleus.regeneration_engine.restore_integrity.assert_called_with(
        nucleus.state_tree, mock_integrity_report
    )


@pytest.mark.asyncio
async def test_snapshot_loop(nucleus, config_file):
    """Test the snapshot loop."""
    # Initialize the nucleus
    await nucleus.initialize(config_file)
    
    # Mock the state tree manager
    nucleus.state_tree_manager.save_snapshot = AsyncMock()
    nucleus.state_tree_manager.list_snapshots = AsyncMock(return_value=[])
    
    # Start the nucleus
    await nucleus.start()
    
    # Let it run for a short time (longer than snapshot_interval)
    await asyncio.sleep(0.6)
    
    # Stop the nucleus
    await nucleus.shutdown()
    
    # Check that save_snapshot was called
    nucleus.state_tree_manager.save_snapshot.assert_called_with(nucleus.state_tree)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])