"""
State Tree implementation for the Phoenix DemiGod system.

The State Tree is a hierarchical data structure that represents the entire
system state with immutable history through snapshots.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from phoenix_demigod.utils.logging import get_logger


class StateNode:
    """
    A node in the state tree.
    
    Each node has:
    - A unique identifier
    - A type descriptor
    - Data payload
    - Metadata for additional information
    - Parent-child relationships
    - Version tracking
    """
    
    def __init__(
        self,
        id: str,
        type: str,
        data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        parent: Optional['StateNode'] = None,
        version: int = 1
    ):
        """
        Initialize a new StateNode.
        
        Args:
            id: Unique identifier for the node
            type: Type descriptor for the node
            data: Data payload (default: empty dict)
            metadata: Additional metadata (default: empty dict)
            parent: Parent node (default: None)
            version: Node version (default: 1)
        """
        self.id = id
        self.type = type
        self.data = data or {}
        self.metadata = metadata or {}
        self.parent = parent
        self.children: List[StateNode] = []
        self.version = version
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_child(self, child: 'StateNode') -> None:
        """
        Add a child node to this node.
        
        Args:
            child: The child node to add
        """
        child.parent = self
        self.children.append(child)
        self.updated_at = datetime.now()
    
    def remove_child(self, child_id: str) -> Optional['StateNode']:
        """
        Remove a child node by ID.
        
        Args:
            child_id: ID of the child to remove
            
        Returns:
            The removed child node, or None if not found
        """
        for i, child in enumerate(self.children):
            if child.id == child_id:
                removed = self.children.pop(i)
                removed.parent = None
                self.updated_at = datetime.now()
                return removed
        return None
    
    def get_child(self, child_id: str) -> Optional['StateNode']:
        """
        Get a child node by ID.
        
        Args:
            child_id: ID of the child to get
            
        Returns:
            The child node, or None if not found
        """
        for child in self.children:
            if child.id == child_id:
                return child
        return None
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """
        Update the node's data.
        
        Args:
            data: New data to merge with existing data
        """
        self.data.update(data)
        self.version += 1
        self.updated_at = datetime.now()
    
    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        """
        Convert the node to a dictionary representation.
        
        Args:
            include_children: Whether to include children (default: True)
            
        Returns:
            Dictionary representation of the node
        """
        result = {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if include_children:
            result["children"] = [child.to_dict() for child in self.children]
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], parent: Optional['StateNode'] = None) -> 'StateNode':
        """
        Create a node from a dictionary representation.
        
        Args:
            data: Dictionary representation of the node
            parent: Parent node (default: None)
            
        Returns:
            New StateNode instance
        """
        node = cls(
            id=data["id"],
            type=data["type"],
            data=data["data"],
            metadata=data["metadata"],
            parent=parent,
            version=data["version"]
        )
        
        # Parse timestamps
        node.created_at = datetime.fromisoformat(data["created_at"])
        node.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Recursively create children
        if "children" in data:
            for child_data in data["children"]:
                child = cls.from_dict(child_data, node)
                node.children.append(child)
                
        return node
    
    def clone(self, include_children: bool = True) -> 'StateNode':
        """
        Create a deep copy of this node.
        
        Args:
            include_children: Whether to clone children (default: True)
            
        Returns:
            New StateNode instance that is a copy of this node
        """
        # Create a new node with the same properties
        clone_node = StateNode(
            id=self.id,
            type=self.type,
            data=self.data.copy(),
            metadata=self.metadata.copy(),
            version=self.version
        )
        
        clone_node.created_at = self.created_at
        clone_node.updated_at = self.updated_at
        
        # Recursively clone children if requested
        if include_children:
            for child in self.children:
                child_clone = child.clone(include_children=True)
                child_clone.parent = clone_node
                clone_node.children.append(child_clone)
                
        return clone_node


class StateTree:
    """
    Hierarchical state tree for the Phoenix DemiGod system.
    
    The StateTree maintains a tree of StateNodes representing the entire
    system state, with support for traversal, modification, and snapshots.
    """
    
    def __init__(self, root: Optional[StateNode] = None):
        """
        Initialize a new StateTree.
        
        Args:
            root: Root node (default: create a new root node)
        """
        self.root = root or StateNode(
            id="root",
            type="root",
            data={},
            metadata={"created_at": datetime.now().isoformat()}
        )
        self.logger = get_logger("phoenix_demigod.state_tree")
        
    def add_node(self, node: StateNode, parent_id: str) -> bool:
        """
        Add a node to the tree under the specified parent.
        
        Args:
            node: Node to add
            parent_id: ID of the parent node
            
        Returns:
            True if the node was added, False otherwise
        """
        parent = self.find_node(parent_id)
        if parent:
            parent.add_child(node)
            return True
        return False
    
    def remove_node(self, node_id: str) -> Optional[StateNode]:
        """
        Remove a node from the tree.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            The removed node, or None if not found
        """
        # Can't remove the root node
        if node_id == self.root.id:
            return None
            
        # Find the parent of the node to remove
        parent = self._find_parent(node_id)
        if parent:
            return parent.remove_child(node_id)
            
        return None
    
    def _find_parent(self, node_id: str) -> Optional[StateNode]:
        """
        Find the parent of a node.
        
        Args:
            node_id: ID of the node to find the parent for
            
        Returns:
            The parent node, or None if not found
        """
        def search(node: StateNode) -> Optional[StateNode]:
            for child in node.children:
                if child.id == node_id:
                    return node
                result = search(child)
                if result:
                    return result
            return None
            
        return search(self.root)
    
    def find_node(self, node_id: str) -> Optional[StateNode]:
        """
        Find a node by ID.
        
        Args:
            node_id: ID of the node to find
            
        Returns:
            The node, or None if not found
        """
        def search(node: StateNode) -> Optional[StateNode]:
            if node.id == node_id:
                return node
            for child in node.children:
                result = search(child)
                if result:
                    return result
            return None
            
        return search(self.root)
    
    def get_node(self, path: str) -> Optional[StateNode]:
        """
        Get a node by path.
        
        Args:
            path: Path to the node (e.g., "/root/branch1/leaf1")
            
        Returns:
            The node, or None if not found
        """
        # Handle root path
        if path == "/" or path == "":
            return self.root
            
        # Split path into components
        components = path.strip("/").split("/")
        
        # Start at root
        current = self.root
        
        # Traverse the path
        for component in components:
            if component == "":
                continue
                
            # Find child with matching ID
            found = False
            for child in current.children:
                if child.id == component:
                    current = child
                    found = True
                    break
                    
            if not found:
                return None
                
        return current
    
    def update_node(self, node_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a node's data.
        
        Args:
            node_id: ID of the node to update
            data: New data to merge with existing data
            
        Returns:
            True if the node was updated, False otherwise
        """
        node = self.find_node(node_id)
        if node:
            node.update_data(data)
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tree to a dictionary representation.
        
        Returns:
            Dictionary representation of the tree
        """
        return {
            "root": self.root.to_dict(),
            "metadata": {
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateTree':
        """
        Create a tree from a dictionary representation.
        
        Args:
            data: Dictionary representation of the tree
            
        Returns:
            New StateTree instance
        """
        root = StateNode.from_dict(data["root"])
        return cls(root=root)
    
    def clone(self) -> 'StateTree':
        """
        Create a deep copy of this tree.
        
        Returns:
            New StateTree instance that is a copy of this tree
        """
        cloned_root = self.root.clone()
        return StateTree(root=cloned_root)


class Snapshot:
    """Represents a point-in-time snapshot of the state tree."""
    
    def __init__(self, id: str, state_tree: StateTree, metadata: Dict[str, Any] = None):
        """
        Initialize a new Snapshot.
        
        Args:
            id: Unique identifier for the snapshot
            state_tree: The state tree to snapshot
            metadata: Additional metadata (default: empty dict)
        """
        self.id = id
        self.state_tree = state_tree.clone()
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the snapshot to a dictionary representation.
        
        Returns:
            Dictionary representation of the snapshot
        """
        return {
            "id": self.id,
            "state_tree": self.state_tree.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """
        Create a snapshot from a dictionary representation.
        
        Args:
            data: Dictionary representation of the snapshot
            
        Returns:
            New Snapshot instance
        """
        state_tree = StateTree.from_dict(data["state_tree"])
        snapshot = cls(
            id=data["id"],
            state_tree=state_tree,
            metadata=data["metadata"]
        )
        snapshot.created_at = datetime.fromisoformat(data["created_at"])
        return snapshot


class StateTreeManager:
    """
    Manager for state tree operations and snapshots.
    
    The StateTreeManager handles loading, saving, and managing snapshots
    of the state tree.
    """
    
    def __init__(self):
        """Initialize a new StateTreeManager."""
        self.logger = get_logger("phoenix_demigod.state_tree_manager")
        self.snapshots: Dict[str, Snapshot] = {}
        
    async def load_state(self, path: str) -> StateTree:
        """
        Load a state tree from a file.
        
        Args:
            path: Path to the state tree file
            
        Returns:
            Loaded StateTree instance
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file contains invalid data
        """
        self.logger.info(f"Loading state tree from {path}")
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            state_tree = StateTree.from_dict(data)
            self.logger.info(f"Loaded state tree with {self._count_nodes(state_tree.root)} nodes")
            return state_tree
            
        except FileNotFoundError:
            self.logger.error(f"State tree file not found: {path}")
            raise
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in state tree file: {e}")
            raise ValueError(f"Invalid JSON in state tree file: {e}")
            
        except Exception as e:
            self.logger.error(f"Error loading state tree: {e}", exc_info=True)
            raise
    
    async def save_state(self, state_tree: StateTree, path: str) -> None:
        """
        Save a state tree to a file.
        
        Args:
            state_tree: StateTree to save
            path: Path to save the state tree to
            
        Raises:
            IOError: If the file cannot be written
        """
        self.logger.info(f"Saving state tree to {path}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Convert to dictionary and save as JSON
            data = state_tree.to_dict()
            
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved state tree with {self._count_nodes(state_tree.root)} nodes")
            
        except Exception as e:
            self.logger.error(f"Error saving state tree: {e}", exc_info=True)
            raise
    
    async def save_snapshot(self, state_tree: StateTree) -> str:
        """
        Create a snapshot of the current state tree.
        
        Args:
            state_tree: StateTree to snapshot
            
        Returns:
            ID of the created snapshot
        """
        snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        self.logger.info(f"Creating snapshot {snapshot_id}")
        
        snapshot = Snapshot(
            id=snapshot_id,
            state_tree=state_tree,
            metadata={
                "node_count": self._count_nodes(state_tree.root),
                "created_by": "StateTreeManager"
            }
        )
        
        self.snapshots[snapshot_id] = snapshot
        
        self.logger.info(f"Created snapshot {snapshot_id} with {snapshot.metadata['node_count']} nodes")
        
        return snapshot_id
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[StateTree]:
        """
        Load a state tree from a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to load
            
        Returns:
            The state tree from the snapshot, or None if not found
        """
        if snapshot_id in self.snapshots:
            self.logger.info(f"Loading snapshot {snapshot_id}")
            return self.snapshots[snapshot_id].state_tree.clone()
            
        self.logger.warning(f"Snapshot not found: {snapshot_id}")
        return None
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to delete
            
        Returns:
            True if the snapshot was deleted, False otherwise
        """
        if snapshot_id in self.snapshots:
            self.logger.info(f"Deleting snapshot {snapshot_id}")
            del self.snapshots[snapshot_id]
            return True
            
        self.logger.warning(f"Cannot delete: Snapshot not found: {snapshot_id}")
        return False
    
    async def list_snapshots(self) -> List[Snapshot]:
        """
        Get a list of all snapshots.
        
        Returns:
            List of all snapshots
        """
        return list(self.snapshots.values())
    
    def _count_nodes(self, node: StateNode) -> int:
        """
        Count the number of nodes in a tree.
        
        Args:
            node: Root node of the tree
            
        Returns:
            Number of nodes in the tree
        """
        count = 1  # Count this node
        for child in node.children:
            count += self._count_nodes(child)
        return count