"""
Nucleus Core for the Phoenix DemiGod system.

The Nucleus is the central component that coordinates the self-evolution
process, manages the system lifecycle, and orchestrates the various engines.
"""

import asyncio
import logging
import os
import signal
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field

from phoenix_demigod.core.state_tree import StateNode, StateTree, StateTreeManager
from phoenix_demigod.engines.differentiation import DifferentiationEngine
from phoenix_demigod.engines.regeneration import RegenerationEngine
from phoenix_demigod.engines.traversal import TraversalEngine
from phoenix_demigod.utils.logging import get_logger
from phoenixxhydra.core.event_routing import EventRouter, DefaultPatternMatcher, InMemoryEventQueue


class NucleusConfig(BaseModel):
    """Configuration for the Nucleus Core."""
    
    cycle_interval: float = Field(5.0, description="Seconds between analysis cycles")
    max_subsystems: int = Field(50, description="Maximum number of active subsystems")
    resource_limit: float = Field(0.8, description="Maximum resource utilization (0.0-1.0)")
    max_tree_depth: int = Field(10, description="Maximum depth of the state tree")
    snapshot_interval: int = Field(300, description="Seconds between automatic snapshots")
    max_snapshots: int = Field(100, description="Maximum number of snapshots to retain")


class NucleusStats(BaseModel):
    """Statistics for the Nucleus Core."""
    
    start_time: datetime = Field(default_factory=datetime.now)
    last_cycle_time: Optional[datetime] = None
    cycle_count: int = Field(0, description="Number of analysis cycles completed")
    last_cycle_duration: float = Field(0.0, description="Duration of the last cycle in seconds")
    avg_cycle_duration: float = Field(0.0, description="Average cycle duration in seconds")
    active_subsystems: int = Field(0, description="Number of active subsystems")
    last_snapshot_time: Optional[datetime] = None
    snapshot_count: int = Field(0, description="Number of snapshots created")
    error_count: int = Field(0, description="Number of errors encountered")
    recovery_count: int = Field(0, description="Number of successful recoveries")


class NucleusManager:
    """
    Central manager for the Phoenix DemiGod system.
    
    The NucleusManager coordinates the self-evolution process by:
    1. Managing the system lifecycle (initialization, cycles, shutdown)
    2. Orchestrating the traversal, differentiation, and regeneration engines
    3. Maintaining the state tree and handling snapshots
    4. Managing resources and subsystems
    """
    
    def __init__(self):
        """Initialize the NucleusManager."""
        self.logger = get_logger("phoenix_demigod.nucleus")
        self.config = NucleusConfig(cycle_interval=5.0, max_subsystems=50, resource_limit=0.8, max_tree_depth=10, snapshot_interval=300, max_snapshots=100)
        self.stats = NucleusStats(cycle_count=0, last_cycle_duration=0.0, avg_cycle_duration=0.0, active_subsystems=0, snapshot_count=0, error_count=0, recovery_count=0)
        
        self.state_tree_manager: Optional[StateTreeManager] = None
        self.state_tree: Optional[StateTree] = None
        self.traversal_engine: Optional[TraversalEngine] = None
        self.differentiation_engine: Optional[DifferentiationEngine] = None
        self.regeneration_engine: Optional[RegenerationEngine] = None
        
        self.event_router: Optional[EventRouter] = None
        
        self.is_initialized = False
        self.is_running = False
        self.should_stop = False
        self._main_task = None
        self._snapshot_task = None
        
    async def initialize(self, config_path: str) -> bool:
        """
        Initialize the Nucleus Core from configuration.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing Phoenix DemiGod Nucleus from {config_path}")
            
            # Load configuration
            if not os.path.exists(config_path):
                self.logger.error(f"Configuration file not found: {config_path}")
                return False
                
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract nucleus configuration
            nucleus_config = config_data.get('nucleus', {})
            self.config = NucleusConfig(**nucleus_config)
            self.logger.info(f"Loaded nucleus configuration: {self.config}")
            
            # Initialize state tree
            self.logger.info("Initializing state tree")
            self.state_tree_manager = StateTreeManager()
            
            # Try to load existing state tree or create a new one
            state_tree_path = os.path.join(os.path.dirname(config_path), "state_tree.json")
            if os.path.exists(state_tree_path):
                self.state_tree = await self.state_tree_manager.load_state(state_tree_path)
                self.logger.info(f"Loaded existing state tree from {state_tree_path}")
            else:
                self.state_tree = StateTree(
                    root=StateNode(
                        id="root",
                        type="root",
                        data={
                            "system_name": config_data.get('system', {}).get('name', 'phoenix-demigod'),
                            "version": config_data.get('system', {}).get('version', '1.0.0'),
                            "environment": config_data.get('system', {}).get('environment', 'development'),
                            "initialized_at": datetime.now().isoformat()
                        },
                        metadata={
                            "created_at": datetime.now().isoformat(),
                            "creator": "NucleusManager"
                        }
                    )
                )
                self.logger.info("Created new state tree")
                
                # Add initial structure
                self._initialize_state_tree_structure()
            
            # Initialize engines with their respective configurations
            self.logger.info("Initializing engines")
            self.traversal_engine = TraversalEngine(config_data.get('traversal', {}))
            self.differentiation_engine = DifferentiationEngine(config_data.get('differentiation', {}))
            self.regeneration_engine = RegenerationEngine(config_data.get('regeneration', {}))
            
            # Initialize event router
            self.logger.info("Initializing event router")
            self.event_router = EventRouter(
                pattern_matcher=DefaultPatternMatcher(),
                event_queue=InMemoryEventQueue()
            )
            
            # Register signal handlers for graceful shutdown
            self._register_signal_handlers()
            
            self.is_initialized = True
            self.logger.info("Phoenix DemiGod Nucleus initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Phoenix DemiGod Nucleus: {e}", exc_info=True)
            return False
    
    def _initialize_state_tree_structure(self) -> None:
        """Initialize the basic structure of the state tree."""
        # Create main branches
        configuration = StateNode(
            id="configuration",
            type="branch",
            data={},
            metadata={"description": "System configuration parameters"}
        )
        
        runtime_state = StateNode(
            id="runtime_state",
            type="branch",
            data={},
            metadata={"description": "Current runtime state"}
        )
        
        snapshots = StateNode(
            id="snapshots",
            type="branch",
            data={},
            metadata={"description": "System state snapshots"}
        )
        
        # Add to root
        if self.state_tree:
            self.state_tree.add_node(configuration, parent_id="root")
            self.state_tree.add_node(runtime_state, parent_id="root")
            self.state_tree.add_node(snapshots, parent_id="root")
        
        # Add sub-branches to runtime_state
        active_subsystems = StateNode(
            id="active_subsystems",
            type="branch",
            data={},
            metadata={"description": "Currently active subsystems"}
        )
        
        resource_usage = StateNode(
            id="resource_usage",
            type="branch",
            data={
                "cpu": 0.0,
                "memory": 0.0,
                "disk": 0.0,
                "network": 0.0
            },
            metadata={"description": "Current resource usage"}
        )
        
        performance_metrics = StateNode(
            id="performance_metrics",
            type="branch",
            data={
                "cycle_time": 0.0,
                "traversal_time": 0.0,
                "differentiation_time": 0.0,
                "regeneration_time": 0.0
            },
            metadata={"description": "Performance metrics"}
        )
        
        # Add to runtime_state
        if self.state_tree:
            self.state_tree.add_node(active_subsystems, parent_id="runtime_state")
            self.state_tree.add_node(resource_usage, parent_id="runtime_state")
            self.state_tree.add_node(performance_metrics, parent_id="runtime_state")
    
    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        def handle_signal(sig, frame):
            self.logger.info(f"Received signal {sig}, initiating graceful shutdown")
            self.should_stop = True
            
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    
    async def start(self) -> None:
        """
        Start the Nucleus Core and begin the self-evolution cycle.
        
        This method starts the main processing loop and snapshot task.
        """
        if not self.is_initialized:
            self.logger.error("Cannot start: Nucleus not initialized")
            return
            
        if self.is_running:
            self.logger.warning("Nucleus is already running")
            return
            
        self.logger.info("Starting Phoenix DemiGod Nucleus")
        self.is_running = True
        self.should_stop = False
        self.stats.start_time = datetime.now()
        
        # Start main processing loop and snapshot task
        self._main_task = asyncio.create_task(self._main_loop())
        self._snapshot_task = asyncio.create_task(self._snapshot_loop())
        
        self.logger.info("Phoenix DemiGod Nucleus started successfully")
    
    async def _main_loop(self) -> None:
        """Main processing loop for the self-evolution cycle."""
        self.logger.info("Starting main processing loop")
        
        while not self.should_stop:
            try:
                cycle_start = time.time()
                self.stats.last_cycle_time = datetime.now()
                
                # 1. Update resource usage
                await self._update_resource_usage()
                
                # 2. Perform traversal to analyze the state tree
                self.logger.debug("Starting traversal analysis")
                traversal_start = time.time()
                analysis_report = None
                if self.traversal_engine and self.state_tree:
                    analysis_report = await self.traversal_engine.traverse(self.state_tree.root)
                traversal_time = time.time() - traversal_start
                
                # Update performance metrics
                self._update_performance_metrics("traversal_time", traversal_time)
                
                # 3. Process analysis results with differentiation engine
                self.logger.debug("Processing analysis results")
                diff_start = time.time()
                if self.differentiation_engine and self.state_tree and analysis_report:
                    diff_results = await self.differentiation_engine.process_analysis(
                        analysis_report, self.state_tree
                    )
                diff_time = time.time() - diff_start
                
                # Update performance metrics
                self._update_performance_metrics("differentiation_time", diff_time)
                
                # 4. Check system integrity with regeneration engine
                self.logger.debug("Checking system integrity")
                regen_start = time.time()
                if self.regeneration_engine and self.state_tree:
                    integrity_report = await self.regeneration_engine.check_integrity(self.state_tree)
                    
                    if not integrity_report.is_healthy:
                        self.logger.warning(f"Integrity issues detected: {integrity_report.issues}")
                        await self.regeneration_engine.restore_integrity(
                            self.state_tree, integrity_report
                        )
                        self.stats.recovery_count += 1
                    
                regen_time = time.time() - regen_start
                
                # Update performance metrics
                self._update_performance_metrics("regeneration_time", regen_time)
                
                # 5. Update cycle statistics
                cycle_time = time.time() - cycle_start
                self.stats.last_cycle_duration = cycle_time
                self.stats.cycle_count += 1
                
                # Update running average
                if self.stats.cycle_count == 1:
                    self.stats.avg_cycle_duration = cycle_time
                else:
                    self.stats.avg_cycle_duration = (
                        (self.stats.avg_cycle_duration * (self.stats.cycle_count - 1) + cycle_time) / 
                        self.stats.cycle_count
                    )
                
                self._update_performance_metrics("cycle_time", cycle_time)
                
                self.logger.debug(
                    f"Cycle {self.stats.cycle_count} completed in {cycle_time:.3f}s "
                    f"(avg: {self.stats.avg_cycle_duration:.3f}s)"
                )
                
                # Sleep until next cycle
                await asyncio.sleep(max(0.1, self.config.cycle_interval - cycle_time))
                
            except asyncio.CancelledError:
                self.logger.info("Main loop cancelled")
                break
                
            except Exception as e:
                self.logger.error(f"Error in main processing loop: {e}", exc_info=True)
                self.stats.error_count += 1
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _snapshot_loop(self) -> None:
        """Periodic task for creating state snapshots."""
        self.logger.info("Starting snapshot loop")
        
        while not self.should_stop:
            try:
                await asyncio.sleep(self.config.snapshot_interval)
                
                if self.should_stop:
                    break
                    
                self.logger.debug("Creating state snapshot")
                snapshot_id = None
                if self.state_tree_manager and self.state_tree:
                    snapshot_id = await self.state_tree_manager.save_snapshot(self.state_tree)
                
                # Update snapshot statistics
                self.stats.last_snapshot_time = datetime.now()
                self.stats.snapshot_count += 1
                
                self.logger.debug(f"Created snapshot {snapshot_id}")
                
                # Prune old snapshots if we have too many
                await self._prune_old_snapshots()
                
            except asyncio.CancelledError:
                self.logger.info("Snapshot loop cancelled")
                break
                
            except Exception as e:
                self.logger.error(f"Error in snapshot loop: {e}", exc_info=True)
                await asyncio.sleep(10)  # Longer pause for snapshot errors
    
    async def _prune_old_snapshots(self) -> None:
        """Remove old snapshots if we have more than the configured maximum."""
        try:
            if self.state_tree_manager:
                snapshots = await self.state_tree_manager.list_snapshots()
            else:
                snapshots = []

            if len(snapshots) > self.config.max_snapshots:
                # Sort by creation time (oldest first)
                snapshots.sort(key=lambda s: s.created_at)
                
                # Remove oldest snapshots
                to_remove = snapshots[:len(snapshots) - self.config.max_snapshots]
                
                for snapshot in to_remove:
                    self.logger.debug(f"Removing old snapshot {snapshot.id}")
                    if self.state_tree_manager:
                        await self.state_tree_manager.delete_snapshot(snapshot.id)
                    
        except Exception as e:
            self.logger.error(f"Error pruning old snapshots: {e}", exc_info=True)
    
    async def _update_resource_usage(self) -> None:
        """Update resource usage statistics in the state tree."""
        try:
            # In a real implementation, this would use system APIs to get actual resource usage
            # For now, we'll use placeholder values
            cpu_usage = 0.2  # 20% CPU usage
            memory_usage = 0.3  # 30% memory usage
            disk_usage = 0.1  # 10% disk usage
            network_usage = 0.05  # 5% network usage
            
            # Update the state tree
            resource_node = None
            if self.state_tree:
                resource_node = self.state_tree.get_node("/runtime_state/resource_usage")
            if resource_node:
                resource_node.data.update({
                    "cpu": cpu_usage,
                    "memory": memory_usage,
                    "disk": disk_usage,
                    "network": network_usage,
                    "updated_at": datetime.now().isoformat()
                })
                
            # Check resource limits
            if cpu_usage > self.config.resource_limit or memory_usage > self.config.resource_limit:
                self.logger.warning(
                    f"Resource usage exceeding limits: CPU={cpu_usage:.2f}, Memory={memory_usage:.2f}"
                )
                
        except Exception as e:
            self.logger.error(f"Error updating resource usage: {e}", exc_info=True)
    
    def _update_performance_metrics(self, metric_name: str, value: float) -> None:
        """Update performance metrics in the state tree."""
        try:
            metrics_node = None
            if self.state_tree:
                metrics_node = self.state_tree.get_node("/runtime_state/performance_metrics")
            if metrics_node and metric_name in metrics_node.data:
                metrics_node.data[metric_name] = value
                metrics_node.data["updated_at"] = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}", exc_info=True)
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the Nucleus Core.
        
        This method stops all tasks, saves the current state, and releases resources.
        """
        if not self.is_running:
            self.logger.warning("Nucleus is not running")
            return
            
        self.logger.info("Shutting down Phoenix DemiGod Nucleus")
        self.should_stop = True
        
        # Cancel running tasks
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
                
        if self._snapshot_task:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass
        
        # Save final state snapshot
        try:
            self.logger.info("Saving final state snapshot")
            if self.state_tree_manager and self.state_tree:
                await self.state_tree_manager.save_snapshot(self.state_tree)
        except Exception as e:
            self.logger.error(f"Error saving final state snapshot: {e}", exc_info=True)
        
        # Shutdown engines
        self.logger.info("Shutting down engines")
        if self.traversal_engine:
            await self.traversal_engine.shutdown()
            
        if self.differentiation_engine:
            await self.differentiation_engine.shutdown()
            
        if self.regeneration_engine:
            await self.regeneration_engine.shutdown()
        
        self.is_running = False
        self.logger.info("Phoenix DemiGod Nucleus shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics for the Nucleus Core."""
        return {
            "start_time": self.stats.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.stats.start_time).total_seconds(),
            "cycle_count": self.stats.cycle_count,
            "last_cycle_time": self.stats.last_cycle_time.isoformat() if self.stats.last_cycle_time else None,
            "last_cycle_duration": self.stats.last_cycle_duration,
            "avg_cycle_duration": self.stats.avg_cycle_duration,
            "active_subsystems": self.stats.active_subsystems,
            "snapshot_count": self.stats.snapshot_count,
            "last_snapshot_time": self.stats.last_snapshot_time.isoformat() if self.stats.last_snapshot_time else None,
            "error_count": self.stats.error_count,
            "recovery_count": self.stats.recovery_count,
            "is_running": self.is_running
        }
    
    async def get_subsystems(self) -> List[Dict[str, Any]]:
        """Get information about all active subsystems."""
        subsystems = []
        
        try:
            subsystems_node = None
            if self.state_tree:
                subsystems_node = self.state_tree.get_node("/runtime_state/active_subsystems")
            if subsystems_node:
                for child in subsystems_node.children:
                    subsystems.append({
                        "id": child.id,
                        "type": child.type,
                        "data": child.data,
                        "metadata": child.metadata
                    })
                    
        except Exception as e:
            self.logger.error(f"Error getting subsystems: {e}", exc_info=True)
            
        return subsystems
