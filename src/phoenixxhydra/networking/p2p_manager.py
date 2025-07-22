"""
P2P Network Manager for PHOENIXxHYDRA Rubik's Mesh System
Implements the core networking protocols for cellular communication
"""

import asyncio
import json
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..core.models import (
    CommunicationMessage, P2PNetworkNode, SystemEvent, EventType
)
from ..core.interfaces import IEventBus


class NodeRole(Enum):
    """Roles that nodes can play in the mesh"""
    PHOENIX_CELL = "phoenix_cell"
    HYDRA_HEAD = "hydra_head"
    PANTHEON_AGENT = "pantheon_agent"
    BRIDGE_NODE = "bridge_node"


class MessageType(Enum):
    """Types of P2P messages in the Rubik's mesh"""
    DISCOVERY = "discovery"
    HEARTBEAT = "heartbeat"
    DATA_SYNC = "data_sync"
    GENE_TRANSFER = "gene_transfer"
    CELL_SPAWN = "cell_spawn"
    CELL_DEATH = "cell_death"
    MESH_REORGANIZE = "mesh_reorganize"
    PANTHEON_COMMAND = "pantheon_command"
    TRUST_UPDATE = "trust_update"
    RESOURCE_REQUEST = "resource_request"
    CHAOS_TEST = "chaos_test"


@dataclass
class MeshTopology:
    """Represents the current mesh network topology"""
    nodes: Dict[str, P2PNetworkNode] = field(default_factory=dict)
    connections: Dict[str, Set[str]] = field(default_factory=dict)
    trust_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_connection(self, node1: str, node2: str):
        """Add bidirectional connection between nodes"""
        if node1 not in self.connections:
            self.connections[node1] = set()
        if node2 not in self.connections:
            self.connections[node2] = set()
        
        self.connections[node1].add(node2)
        self.connections[node2].add(node1)
        self.last_updated = datetime.now()
    
    def remove_connection(self, node1: str, node2: str):
        """Remove bidirectional connection between nodes"""
        if node1 in self.connections:
            self.connections[node1].discard(node2)
        if node2 in self.connections:
            self.connections[node2].discard(node1)
        self.last_updated = datetime.now()
    
    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get all neighbors of a node"""
        return self.connections.get(node_id, set())
    
    def update_trust(self, from_node: str, to_node: str, trust_score: float):
        """Update trust score between nodes"""
        if from_node not in self.trust_matrix:
            self.trust_matrix[from_node] = {}
        self.trust_matrix[from_node][to_node] = max(0.0, min(1.0, trust_score))


@dataclass
class RubikMeshState:
    """State of the Rubik's mesh reorganization"""
    current_configuration: str = "default"
    rotation_in_progress: bool = False
    target_configuration: Optional[str] = None
    rotation_start_time: Optional[datetime] = None
    affected_nodes: Set[str] = field(default_factory=set)
    
    def start_rotation(self, target: str, nodes: Set[str]):
        """Start a mesh rotation/reorganization"""
        self.rotation_in_progress = True
        self.target_configuration = target
        self.rotation_start_time = datetime.now()
        self.affected_nodes = nodes.copy()
    
    def complete_rotation(self):
        """Complete the mesh rotation"""
        if self.target_configuration:
            self.current_configuration = self.target_configuration
        self.rotation_in_progress = False
        self.target_configuration = None
        self.rotation_start_time = None
        self.affected_nodes.clear()


class P2PNetworkManager:
    """
    Advanced P2P Network Manager for PHOENIXxHYDRA Rubik's Mesh
    Supports cellular communication, mesh reorganization, and Pantheon coordination
    """
    
    def __init__(self, node_id: str, node_role: NodeRole, 
                 port: int = 8080, event_bus: Optional[IEventBus] = None):
        self.node_id = node_id
        self.node_role = node_role
        self.port = port
        self.event_bus = event_bus
        
        # Network state
        self.topology = MeshTopology()
        self.rubik_state = RubikMeshState()
        self.local_node = P2PNetworkNode(
            node_id=node_id,
            address="localhost",
            port=port,
            public_key=self._generate_public_key(),
            capabilities=self._get_node_capabilities()
        )
        
        # Communication
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.pending_messages: Dict[str, CommunicationMessage] = {}
        self.message_history: List[CommunicationMessage] = []
        
        # Security
        self.encryption_key = self._generate_encryption_key()
        self.trusted_nodes: Set[str] = set()
        
        # Mesh management
        self.discovery_interval = 30  # seconds
        self.heartbeat_interval = 10  # seconds
        self.mesh_reorganize_threshold = 0.7  # trigger reorganization
        
        # Async tasks
        self.running_tasks: List[asyncio.Task] = []
        self.is_running = False
        
        # Logging
        self.logger = logging.getLogger(f"P2PManager-{node_id}")
        
        # Register default message handlers
        self._register_default_handlers()
    
    def _generate_public_key(self) -> str:
        """Generate a public key for the node"""
        return hashlib.sha256(f"{self.node_id}_{time.time()}".encode()).hexdigest()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for secure communication"""
        password = f"{self.node_id}_secret".encode()
        salt = b"phoenixxhydra_salt"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def _get_node_capabilities(self) -> List[str]:
        """Get capabilities based on node role"""
        base_capabilities = ["mesh_communication", "discovery", "heartbeat"]
        
        if self.node_role == NodeRole.PHOENIX_CELL:
            return base_capabilities + ["gene_expression", "cell_division", "adaptation"]
        elif self.node_role == NodeRole.HYDRA_HEAD:
            return base_capabilities + ["cell_management", "task_coordination", "specialization"]
        elif self.node_role == NodeRole.PANTHEON_AGENT:
            return base_capabilities + ["orchestration", "system_control", "strategic_planning"]
        else:
            return base_capabilities + ["routing", "bridging"]
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers[MessageType.DISCOVERY] = self._handle_discovery
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
        self.message_handlers[MessageType.DATA_SYNC] = self._handle_data_sync
        self.message_handlers[MessageType.GENE_TRANSFER] = self._handle_gene_transfer
        self.message_handlers[MessageType.MESH_REORGANIZE] = self._handle_mesh_reorganize
        self.message_handlers[MessageType.PANTHEON_COMMAND] = self._handle_pantheon_command
        self.message_handlers[MessageType.TRUST_UPDATE] = self._handle_trust_update
    
    async def start(self):
        """Start the P2P network manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info(f"Starting P2P Network Manager for {self.node_id}")
        
        # Start background tasks
        self.running_tasks = [
            asyncio.create_task(self._discovery_loop()),
            asyncio.create_task(self._heartbeat_loop()),
            asyncio.create_task(self._mesh_maintenance_loop()),
            asyncio.create_task(self._message_processing_loop())
        ]
        
        # Register with topology
        self.topology.nodes[self.node_id] = self.local_node
        
        # Emit startup event
        if self.event_bus:
            event = SystemEvent(
                event_type=EventType.SYSTEM_ALERT,
                source_component=self.node_id,
                data={"action": "p2p_manager_started", "role": self.node_role.value}
            )
            await self.event_bus.publish(event)
    
    async def stop(self):
        """Stop the P2P network manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info(f"Stopping P2P Network Manager for {self.node_id}")
        
        # Cancel all running tasks
        for task in self.running_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.running_tasks, return_exceptions=True)
        self.running_tasks.clear()
        
        # Emit shutdown event
        if self.event_bus:
            event = SystemEvent(
                event_type=EventType.SYSTEM_ALERT,
                source_component=self.node_id,
                data={"action": "p2p_manager_stopped"}
            )
            await self.event_bus.publish(event)
    
    async def send_message(self, message: CommunicationMessage) -> bool:
        """Send a message to another node"""
        try:
            # Encrypt message if enabled
            if message.encrypted:
                message = self._encrypt_message(message)
            
            # Add to pending messages for delivery confirmation
            self.pending_messages[message.message_id] = message
            
            # Simulate network transmission (in real implementation, use actual networking)
            await self._simulate_network_send(message)
            
            # Add to message history
            self.message_history.append(message)
            if len(self.message_history) > 1000:  # Keep last 1000 messages
                self.message_history = self.message_history[-1000:]
            
            self.logger.debug(f"Sent message {message.message_id} to {message.receiver_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def receive_message(self) -> Optional[CommunicationMessage]:
        """Receive a message from the network"""
        # In real implementation, this would listen on network socket
        # For now, simulate message reception
        return await self._simulate_network_receive()
    
    async def discover_peers(self) -> List[P2PNetworkNode]:
        """Discover available peers in the mesh"""
        discovered_peers = []
        
        # Broadcast discovery message
        discovery_message = CommunicationMessage(
            sender_id=self.node_id,
            receiver_id="broadcast",
            message_type=MessageType.DISCOVERY.value,
            payload={
                "node_info": {
                    "node_id": self.node_id,
                    "role": self.node_role.value,
                    "capabilities": self.local_node.capabilities,
                    "public_key": self.local_node.public_key
                },
                "discovery_timestamp": datetime.now().isoformat()
            }
        )
        
        await self.send_message(discovery_message)
        
        # Return currently known peers
        for node in self.topology.nodes.values():
            if node.node_id != self.node_id:
                discovered_peers.append(node)
        
        return discovered_peers
    
    async def update_routing_table(self):
        """Update network routing table using Rubik's mesh algorithm"""
        if self.rubik_state.rotation_in_progress:
            self.logger.info("Mesh rotation in progress, deferring routing update")
            return
        
        # Calculate optimal routes using mesh topology
        routing_updates = {}
        
        for target_node in self.topology.nodes:
            if target_node == self.node_id:
                continue
            
            # Find best path considering trust scores and network performance
            best_path = await self._calculate_best_path(target_node)
            if best_path:
                routing_updates[target_node] = best_path
        
        # Apply routing updates
        self.logger.debug(f"Updated routing table with {len(routing_updates)} routes")
        
        # Trigger mesh reorganization if needed
        mesh_efficiency = await self._calculate_mesh_efficiency()
        if mesh_efficiency < self.mesh_reorganize_threshold:
            await self._trigger_mesh_reorganization()
    
    async def reorganize_mesh(self, target_configuration: str = "optimal"):
        """Reorganize the mesh network like a Rubik's cube"""
        if self.rubik_state.rotation_in_progress:
            self.logger.warning("Mesh reorganization already in progress")
            return
        
        self.logger.info(f"Starting mesh reorganization to '{target_configuration}'")
        
        # Determine affected nodes
        affected_nodes = set(self.topology.nodes.keys())
        
        # Start rotation
        self.rubik_state.start_rotation(target_configuration, affected_nodes)
        
        # Notify all nodes about reorganization
        reorganize_message = CommunicationMessage(
            sender_id=self.node_id,
            receiver_id="broadcast",
            message_type=MessageType.MESH_REORGANIZE.value,
            payload={
                "action": "start_reorganization",
                "target_configuration": target_configuration,
                "affected_nodes": list(affected_nodes),
                "coordinator": self.node_id
            }
        )
        
        await self.send_message(reorganize_message)
        
        # Perform reorganization steps
        await self._execute_mesh_reorganization(target_configuration)
        
        # Complete rotation
        self.rubik_state.complete_rotation()
        
        # Notify completion
        completion_message = CommunicationMessage(
            sender_id=self.node_id,
            receiver_id="broadcast",
            message_type=MessageType.MESH_REORGANIZE.value,
            payload={
                "action": "reorganization_complete",
                "new_configuration": target_configuration
            }
        )
        
        await self.send_message(completion_message)
        
        self.logger.info("Mesh reorganization completed")
    
    def register_message_handler(self, message_type: MessageType, 
                                handler: Callable[[CommunicationMessage], None]):
        """Register a custom message handler"""
        self.message_handlers[message_type] = handler
    
    def get_mesh_status(self) -> Dict[str, Any]:
        """Get current mesh network status"""
        return {
            "node_id": self.node_id,
            "node_role": self.node_role.value,
            "connected_peers": len(self.topology.nodes) - 1,
            "mesh_configuration": self.rubik_state.current_configuration,
            "rotation_in_progress": self.rubik_state.rotation_in_progress,
            "trust_relationships": len([
                trust for node_trusts in self.topology.trust_matrix.values()
                for trust in node_trusts.values() if trust > 0.5
            ]),
            "message_history_size": len(self.message_history),
            "capabilities": self.local_node.capabilities
        }
    
    # Private methods for internal operations
    
    async def _discovery_loop(self):
        """Background task for peer discovery"""
        while self.is_running:
            try:
                await self.discover_peers()
                await asyncio.sleep(self.discovery_interval)
            except Exception as e:
                self.logger.error(f"Discovery loop error: {e}")
                await asyncio.sleep(5)
    
    async def _heartbeat_loop(self):
        """Background task for sending heartbeats"""
        while self.is_running:
            try:
                heartbeat_message = CommunicationMessage(
                    sender_id=self.node_id,
                    receiver_id="broadcast",
                    message_type=MessageType.HEARTBEAT.value,
                    payload={
                        "timestamp": datetime.now().isoformat(),
                        "status": "alive",
                        "mesh_config": self.rubik_state.current_configuration
                    }
                )
                await self.send_message(heartbeat_message)
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)
    
    async def _mesh_maintenance_loop(self):
        """Background task for mesh maintenance"""
        while self.is_running:
            try:
                await self.update_routing_table()
                await self._cleanup_stale_nodes()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                self.logger.error(f"Mesh maintenance error: {e}")
                await asyncio.sleep(10)
    
    async def _message_processing_loop(self):
        """Background task for processing incoming messages"""
        while self.is_running:
            try:
                message = await self.receive_message()
                if message:
                    await self._process_message(message)
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, message: CommunicationMessage):
        """Process an incoming message"""
        try:
            # Decrypt if needed
            if message.encrypted:
                message = self._decrypt_message(message)
            
            # Get message type
            msg_type = MessageType(message.message_type)
            
            # Call appropriate handler
            if msg_type in self.message_handlers:
                await self.message_handlers[msg_type](message)
            else:
                self.logger.warning(f"No handler for message type: {msg_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message {message.message_id}: {e}")
    
    # Message handlers
    
    async def _handle_discovery(self, message: CommunicationMessage):
        """Handle discovery messages"""
        node_info = message.payload.get("node_info", {})
        if node_info.get("node_id") != self.node_id:
            # Add discovered node to topology
            discovered_node = P2PNetworkNode(
                node_id=node_info.get("node_id"),
                address="localhost",  # In real implementation, extract from message
                port=8080,
                public_key=node_info.get("public_key", ""),
                capabilities=node_info.get("capabilities", [])
            )
            self.topology.nodes[discovered_node.node_id] = discovered_node
            self.logger.info(f"Discovered new node: {discovered_node.node_id}")
    
    async def _handle_heartbeat(self, message: CommunicationMessage):
        """Handle heartbeat messages"""
        sender_id = message.sender_id
        if sender_id in self.topology.nodes:
            self.topology.nodes[sender_id].last_seen = datetime.now()
    
    async def _handle_data_sync(self, message: CommunicationMessage):
        """Handle data synchronization messages"""
        # Implement data sync logic based on message payload
        self.logger.debug(f"Handling data sync from {message.sender_id}")
    
    async def _handle_gene_transfer(self, message: CommunicationMessage):
        """Handle Gene Py transfer messages"""
        gene_data = message.payload.get("gene_data", {})
        self.logger.info(f"Received gene transfer: {gene_data.get('gene_id', 'unknown')}")
        
        # Emit gene transfer event
        if self.event_bus:
            event = SystemEvent(
                event_type=EventType.GENETIC_EVOLUTION,
                source_component=message.sender_id,
                target_component=self.node_id,
                data=gene_data
            )
            await self.event_bus.publish(event)
    
    async def _handle_mesh_reorganize(self, message: CommunicationMessage):
        """Handle mesh reorganization messages"""
        action = message.payload.get("action")
        if action == "start_reorganization":
            target_config = message.payload.get("target_configuration")
            self.logger.info(f"Participating in mesh reorganization to {target_config}")
            # Participate in reorganization
        elif action == "reorganization_complete":
            new_config = message.payload.get("new_configuration")
            self.rubik_state.current_configuration = new_config
            self.logger.info(f"Mesh reorganization completed: {new_config}")
    
    async def _handle_pantheon_command(self, message: CommunicationMessage):
        """Handle commands from Pantheon agents"""
        command = message.payload.get("command")
        agent = message.payload.get("agent")
        
        self.logger.info(f"Received Pantheon command from {agent}: {command}")
        
        # Emit Pantheon command event
        if self.event_bus:
            event = SystemEvent(
                event_type=EventType.SYSTEM_ALERT,
                source_component=message.sender_id,
                target_component=self.node_id,
                data={
                    "pantheon_agent": agent,
                    "command": command,
                    "payload": message.payload
                }
            )
            await self.event_bus.publish(event)
    
    async def _handle_trust_update(self, message: CommunicationMessage):
        """Handle trust score updates"""
        target_node = message.payload.get("target_node")
        trust_score = message.payload.get("trust_score", 0.5)
        
        if target_node:
            self.topology.update_trust(message.sender_id, target_node, trust_score)
            self.logger.debug(f"Updated trust: {message.sender_id} -> {target_node}: {trust_score}")
    
    # Utility methods
    
    def _encrypt_message(self, message: CommunicationMessage) -> CommunicationMessage:
        """Encrypt message payload"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_payload = fernet.encrypt(json.dumps(message.payload).encode())
            message.payload = {"encrypted_data": base64.b64encode(encrypted_payload).decode()}
            return message
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return message
    
    def _decrypt_message(self, message: CommunicationMessage) -> CommunicationMessage:
        """Decrypt message payload"""
        try:
            fernet = Fernet(self.encryption_key)
            encrypted_data = base64.b64decode(message.payload["encrypted_data"])
            decrypted_payload = fernet.decrypt(encrypted_data)
            message.payload = json.loads(decrypted_payload.decode())
            return message
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return message
    
    async def _simulate_network_send(self, message: CommunicationMessage):
        """Simulate network message sending"""
        # In real implementation, this would use actual networking (WebSockets, TCP, etc.)
        await asyncio.sleep(0.01)  # Simulate network latency
    
    async def _simulate_network_receive(self) -> Optional[CommunicationMessage]:
        """Simulate network message receiving"""
        # In real implementation, this would listen on network socket
        await asyncio.sleep(0.1)
        return None  # No messages for simulation
    
    async def _calculate_best_path(self, target_node: str) -> Optional[List[str]]:
        """Calculate best path to target node using trust and performance metrics"""
        # Simplified pathfinding - in real implementation, use Dijkstra or A*
        if target_node in self.topology.get_neighbors(self.node_id):
            return [self.node_id, target_node]
        return None
    
    async def _calculate_mesh_efficiency(self) -> float:
        """Calculate current mesh network efficiency"""
        if len(self.topology.nodes) < 2:
            return 1.0
        
        # Simple efficiency calculation based on connectivity
        total_possible_connections = len(self.topology.nodes) * (len(self.topology.nodes) - 1) / 2
        actual_connections = sum(len(neighbors) for neighbors in self.topology.connections.values()) / 2
        
        return actual_connections / total_possible_connections if total_possible_connections > 0 else 0.0
    
    async def _trigger_mesh_reorganization(self):
        """Trigger mesh reorganization when efficiency is low"""
        if not self.rubik_state.rotation_in_progress:
            await self.reorganize_mesh("efficiency_optimized")
    
    async def _execute_mesh_reorganization(self, target_configuration: str):
        """Execute the actual mesh reorganization steps"""
        # Simulate reorganization process
        reorganization_steps = [
            "analyzing_current_topology",
            "calculating_optimal_configuration",
            "updating_routing_tables",
            "redistributing_connections",
            "validating_new_topology"
        ]
        
        for step in reorganization_steps:
            self.logger.debug(f"Reorganization step: {step}")
            await asyncio.sleep(0.5)  # Simulate processing time
    
    async def _cleanup_stale_nodes(self):
        """Remove nodes that haven't been seen recently"""
        stale_threshold = timedelta(minutes=5)
        current_time = datetime.now()
        
        stale_nodes = []
        for node_id, node in self.topology.nodes.items():
            if node_id != self.node_id and (current_time - node.last_seen) > stale_threshold:
                stale_nodes.append(node_id)
        
        for node_id in stale_nodes:
            del self.topology.nodes[node_id]
            if node_id in self.topology.connections:
                del self.topology.connections[node_id]
            self.logger.info(f"Removed stale node: {node_id}")