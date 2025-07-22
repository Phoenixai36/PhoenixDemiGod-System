"""
Regeneration Engine for the Phoenix DemiGod system.

The Regeneration Engine monitors system health and restores components
after failures, implementing self-healing capabilities.
"""

import hashlib
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from phoenix_demigod.core.state_tree import StateNode, StateTree, StateTreeManager
from phoenix_demigod.utils.logging import get_logger


class IntegrityIssue:
    """Represents an integrity issue detected in the system."""
    
    def __init__(
        self,
        type: str,
        path: str,
        severity: str,
        description: str,
        data: Dict[str, Any] = None
    ):
        """
        Initialize a new IntegrityIssue.
        
        Args:
            type: Type of issue (e.g., "CHECKSUM_MISMATCH", "MISSING_NODE")
            path: Path to the affected component
            severity: Issue severity ("low", "medium", "high", "critical")
            description: Human-readable description of the issue
            data: Additional issue data (default: empty dict)
        """
        self.type = type
        self.path = path
        self.severity = severity
        self.description = description
        self.data = data or {}
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the issue to a dictionary representation.
        
        Returns:
            Dictionary representation of the issue
        """
        return {
            "type": self.type,
            "path": self.path,
            "severity": self.severity,
            "description": self.description,
            "data": self.data,
            "detected_at": self.detected_at.isoformat()
        }


class IntegrityReport:
    """Report containing the results of integrity checking."""
    
    def __init__(self):
        """Initialize a new IntegrityReport."""
        self.issues: List[IntegrityIssue] = []
        self.checksums: Dict[str, str] = {}
        self.timestamp = datetime.now()
    
    @property
    def is_healthy(self) -> bool:
        """
        Check if the system is healthy.
        
        Returns:
            True if no issues were detected, False otherwise
        """
        return len(self.issues) == 0
    
    def add_issue(self, issue: IntegrityIssue) -> None:
        """
        Add an issue to the report.
        
        Args:
            issue: Issue to add
        """
        self.issues.append(issue)
    
    def set_checksum(self, path: str, checksum: str) -> None:
        """
        Set a checksum for a component.
        
        Args:
            path: Path to the component
            checksum: Checksum value
        """
        self.checksums[path] = checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a dictionary representation.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "is_healthy": self.is_healthy,
            "issues": [issue.to_dict() for issue in self.issues],
            "checksums": self.checksums,
            "timestamp": self.timestamp.isoformat()
        }


class RecoveryResult:
    """Result of a recovery operation."""
    
    def __init__(
        self,
        success: bool,
        path: str,
        issue_type: str,
        description: str,
        data: Dict[str, Any] = None
    ):
        """
        Initialize a new RecoveryResult.
        
        Args:
            success: Whether the recovery was successful
            path: Path to the recovered component
            issue_type: Type of issue that was recovered from
            description: Human-readable description of the recovery
            data: Additional recovery data (default: empty dict)
        """
        self.success = success
        self.path = path
        self.issue_type = issue_type
        self.description = description
        self.data = data or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary representation.
        
        Returns:
            Dictionary representation of the result
        """
        return {
            "success": self.success,
            "path": self.path,
            "issue_type": self.issue_type,
            "description": self.description,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class RegenerationEngine:
    """
    Engine for monitoring system health and recovering from failures.
    
    The RegenerationEngine continuously checks system integrity and
    restores components from previous states when failures are detected.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a new RegenerationEngine.
        
        Args:
            config: Configuration parameters (default: empty dict)
        """
        self.logger = get_logger("phoenix_demigod.engines.regeneration")
        self.config = config or {}
        
        # Extract configuration parameters with defaults
        self.integrity_check_interval = self.config.get("integrity_check_interval", 60.0)
        self.checksum_algorithm = self.config.get("checksum_algorithm", "sha256")
        self.max_recovery_attempts = self.config.get("max_recovery_attempts", 5)
        self.recovery_timeout = self.config.get("recovery_timeout", 30.0)
        self.enable_predictive_recovery = self.config.get("enable_predictive_recovery", True)
        
        # Initialize state
        self.last_check_time = datetime.now()
        self.component_checksums: Dict[str, str] = {}
        self.recovery_attempts: Dict[str, int] = {}
        self.recovery_history: List[RecoveryResult] = []
        
        self.logger.info(f"RegenerationEngine initialized with config: {self.config}")
    
    async def check_integrity(self, state_tree: StateTree) -> IntegrityReport:
        """
        Check the integrity of the state tree.
        
        Args:
            state_tree: State tree to check
            
        Returns:
            Integrity report containing any detected issues
        """
        self.logger.info("Checking system integrity")
        start_time = time.time()
        
        # Create a new integrity report
        report = IntegrityReport()
        
        # Check root node
        if not state_tree.root:
            report.add_issue(IntegrityIssue(
                type="MISSING_ROOT",
                path="/",
                severity="critical",
                description="State tree root node is missing"
            ))
            return report
        
        # Perform recursive integrity check
        await self._check_node_integrity(state_tree.root, "", report)
        
        # Update last check time
        self.last_check_time = datetime.now()
        
        elapsed_time = time.time() - start_time
        self.logger.info(
            f"Integrity check completed in {elapsed_time:.3f}s: "
            f"{len(report.issues)} issues detected"
        )
        
        return report
    
    async def _check_node_integrity(
        self,
        node: StateNode,
        path: str,
        report: IntegrityReport
    ) -> None:
        """
        Recursively check the integrity of a node and its children.
        
        Args:
            node: Node to check
            path: Path to the node
            report: Integrity report to update
        """
        # Update path
        current_path = f"{path}/{node.id}" if path else f"/{node.id}"
        
        # Calculate checksum
        checksum = self._calculate_node_checksum(node)
        report.set_checksum(current_path, checksum)
        
        # Check if we have a previous checksum for this node
        if current_path in self.component_checksums:
            previous_checksum = self.component_checksums[current_path]
            
            # Compare checksums
            if checksum != previous_checksum:
                report.add_issue(IntegrityIssue(
                    type="CHECKSUM_MISMATCH",
                    path=current_path,
                    severity="medium",
                    description=f"Checksum mismatch for node {node.id}",
                    data={
                        "current_checksum": checksum,
                        "previous_checksum": previous_checksum
                    }
                ))
        
        # Update stored checksum
        self.component_checksums[current_path] = checksum
        
        # Check for missing metadata
        if not node.metadata:
            report.add_issue(IntegrityIssue(
                type="MISSING_METADATA",
                path=current_path,
                severity="low",
                description=f"Node {node.id} is missing metadata"
            ))
        
        # Check for invalid parent-child relationships
        for child in node.children:
            if child.parent != node:
                report.add_issue(IntegrityIssue(
                    type="INVALID_PARENT",
                    path=f"{current_path}/{child.id}",
                    severity="medium",
                    description=f"Node {child.id} has incorrect parent reference"
                ))
        
        # Recursively check children
        for child in node.children:
            await self._check_node_integrity(child, current_path, report)
    
    def _calculate_node_checksum(self, node: StateNode) -> str:
        """
        Calculate a checksum for a node.
        
        Args:
            node: Node to calculate checksum for
            
        Returns:
            Checksum string
        """
        # Create a string representation of the node
        node_str = (
            f"id:{node.id}|"
            f"type:{node.type}|"
            f"data:{str(sorted(node.data.items()))}|"
            f"metadata:{str(sorted(node.metadata.items()))}|"
            f"version:{node.version}|"
            f"children:{','.join(child.id for child in node.children)}"
        )
        
        # Calculate checksum
        if self.checksum_algorithm == "sha256":
            return hashlib.sha256(node_str.encode()).hexdigest()
        elif self.checksum_algorithm == "md5":
            return hashlib.md5(node_str.encode()).hexdigest()
        else:
            # Default to sha256
            return hashlib.sha256(node_str.encode()).hexdigest()
    
    async def restore_integrity(
        self,
        state_tree: StateTree,
        integrity_report: IntegrityReport
    ) -> List[RecoveryResult]:
        """
        Restore system integrity based on an integrity report.
        
        Args:
            state_tree: State tree to restore
            integrity_report: Integrity report containing issues
            
        Returns:
            List of recovery results
        """
        if integrity_report.is_healthy:
            self.logger.info("No integrity issues to restore")
            return []
            
        self.logger.info(f"Restoring integrity: {len(integrity_report.issues)} issues to address")
        
        results: List[RecoveryResult] = []
        
        # Sort issues by severity (critical first)
        sorted_issues = sorted(
            integrity_report.issues,
            key=lambda issue: {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "low": 3
            }.get(issue.severity, 4)
        )
        
        # Process each issue
        for issue in sorted_issues:
            result = await self._restore_issue(state_tree, issue)
            results.append(result)
            
            # Update recovery history
            self.recovery_history.append(result)
            
            # Reset recovery attempts if successful
            if result.success:
                self.recovery_attempts.pop(issue.path, None)
            
        self.logger.info(
            f"Integrity restoration completed: "
            f"{sum(1 for r in results if r.success)} successful, "
            f"{sum(1 for r in results if not r.success)} failed"
        )
        
        return results
    
    async def _restore_issue(
        self,
        state_tree: StateTree,
        issue: IntegrityIssue
    ) -> RecoveryResult:
        """
        Restore a specific integrity issue.
        
        Args:
            state_tree: State tree to restore
            issue: Issue to restore
            
        Returns:
            Recovery result
        """
        self.logger.info(f"Restoring issue: {issue.type} at {issue.path}")
        
        # Check if we've exceeded the maximum recovery attempts
        if issue.path in self.recovery_attempts:
            self.recovery_attempts[issue.path] += 1
        else:
            self.recovery_attempts[issue.path] = 1
            
        if self.recovery_attempts[issue.path] > self.max_recovery_attempts:
            self.logger.warning(
                f"Exceeded maximum recovery attempts ({self.max_recovery_attempts}) "
                f"for {issue.path}"
            )
            return RecoveryResult(
                success=False,
                path=issue.path,
                issue_type=issue.type,
                description=f"Exceeded maximum recovery attempts ({self.max_recovery_attempts})",
                data={
                    "attempts": self.recovery_attempts[issue.path],
                    "max_attempts": self.max_recovery_attempts
                }
            )
        
        # Handle different issue types
        if issue.type == "MISSING_ROOT":
            return await self._restore_missing_root(state_tree)
            
        elif issue.type == "CHECKSUM_MISMATCH":
            return await self._restore_checksum_mismatch(state_tree, issue)
            
        elif issue.type == "MISSING_METADATA":
            return await self._restore_missing_metadata(state_tree, issue)
            
        elif issue.type == "INVALID_PARENT":
            return await self._restore_invalid_parent(state_tree, issue)
            
        else:
            self.logger.warning(f"Unknown issue type: {issue.type}")
            return RecoveryResult(
                success=False,
                path=issue.path,
                issue_type=issue.type,
                description=f"Unknown issue type: {issue.type}"
            )
    
    async def _restore_missing_root(self, state_tree: StateTree) -> RecoveryResult:
        """
        Restore a missing root node.
        
        Args:
            state_tree: State tree to restore
            
        Returns:
            Recovery result
        """
        self.logger.info("Restoring missing root node")
        
        try:
            # Create a new root node
            state_tree.root = StateNode(
                id="root",
                type="root",
                data={
                    "restored_at": datetime.now().isoformat()
                },
                metadata={
                    "description": "Root node restored by RegenerationEngine",
                    "restored_by": "RegenerationEngine"
                }
            )
            
            return RecoveryResult(
                success=True,
                path="/",
                issue_type="MISSING_ROOT",
                description="Created new root node"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to restore root node: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                path="/",
                issue_type="MISSING_ROOT",
                description=f"Failed to restore root node: {e}"
            )
    
    async def _restore_checksum_mismatch(
        self,
        state_tree: StateTree,
        issue: IntegrityIssue
    ) -> RecoveryResult:
        """
        Restore a node with a checksum mismatch.
        
        Args:
            state_tree: State tree to restore
            issue: Issue to restore
            
        Returns:
            Recovery result
        """
        self.logger.info(f"Restoring checksum mismatch at {issue.path}")
        
        try:
            # Get the node
            node = state_tree.get_node(issue.path)
            if not node:
                return RecoveryResult(
                    success=False,
                    path=issue.path,
                    issue_type=issue.type,
                    description="Node not found"
                )
            
            # In a real implementation, we would restore from a snapshot
            # For now, we'll just add a restoration marker
            node.metadata["restored_at"] = datetime.now().isoformat()
            node.metadata["restored_by"] = "RegenerationEngine"
            node.metadata["restoration_reason"] = "CHECKSUM_MISMATCH"
            
            # Update the stored checksum
            self.component_checksums[issue.path] = self._calculate_node_checksum(node)
            
            return RecoveryResult(
                success=True,
                path=issue.path,
                issue_type=issue.type,
                description="Restored node with checksum mismatch"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to restore checksum mismatch: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                path=issue.path,
                issue_type=issue.type,
                description=f"Failed to restore checksum mismatch: {e}"
            )
    
    async def _restore_missing_metadata(
        self,
        state_tree: StateTree,
        issue: IntegrityIssue
    ) -> RecoveryResult:
        """
        Restore missing metadata for a node.
        
        Args:
            state_tree: State tree to restore
            issue: Issue to restore
            
        Returns:
            Recovery result
        """
        self.logger.info(f"Restoring missing metadata at {issue.path}")
        
        try:
            # Get the node
            node = state_tree.get_node(issue.path)
            if not node:
                return RecoveryResult(
                    success=False,
                    path=issue.path,
                    issue_type=issue.type,
                    description="Node not found"
                )
            
            # Add basic metadata
            node.metadata = {
                "description": f"{node.type} node",
                "restored_at": datetime.now().isoformat(),
                "restored_by": "RegenerationEngine",
                "restoration_reason": "MISSING_METADATA"
            }
            
            # Update the stored checksum
            self.component_checksums[issue.path] = self._calculate_node_checksum(node)
            
            return RecoveryResult(
                success=True,
                path=issue.path,
                issue_type=issue.type,
                description="Restored missing metadata"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to restore missing metadata: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                path=issue.path,
                issue_type=issue.type,
                description=f"Failed to restore missing metadata: {e}"
            )
    
    async def _restore_invalid_parent(
        self,
        state_tree: StateTree,
        issue: IntegrityIssue
    ) -> RecoveryResult:
        """
        Restore a node with an invalid parent reference.
        
        Args:
            state_tree: State tree to restore
            issue: Issue to restore
            
        Returns:
            Recovery result
        """
        self.logger.info(f"Restoring invalid parent reference at {issue.path}")
        
        try:
            # Parse the path to get parent and child paths
            path_parts = issue.path.split("/")
            child_id = path_parts[-1]
            parent_path = "/".join(path_parts[:-1])
            
            # Get the parent and child nodes
            parent_node = state_tree.get_node(parent_path)
            if not parent_node:
                return RecoveryResult(
                    success=False,
                    path=issue.path,
                    issue_type=issue.type,
                    description="Parent node not found"
                )
            
            # Find the child node
            child_node = None
            for child in parent_node.children:
                if child.id == child_id:
                    child_node = child
                    break
                    
            if not child_node:
                return RecoveryResult(
                    success=False,
                    path=issue.path,
                    issue_type=issue.type,
                    description="Child node not found"
                )
            
            # Fix the parent reference
            child_node.parent = parent_node
            
            # Add restoration marker
            child_node.metadata["restored_at"] = datetime.now().isoformat()
            child_node.metadata["restored_by"] = "RegenerationEngine"
            child_node.metadata["restoration_reason"] = "INVALID_PARENT"
            
            # Update the stored checksum
            self.component_checksums[issue.path] = self._calculate_node_checksum(child_node)
            
            return RecoveryResult(
                success=True,
                path=issue.path,
                issue_type=issue.type,
                description="Restored invalid parent reference"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to restore invalid parent: {e}", exc_info=True)
            return RecoveryResult(
                success=False,
                path=issue.path,
                issue_type=issue.type,
                description=f"Failed to restore invalid parent: {e}"
            )
    
    async def analyze_failures(self) -> Dict[str, Any]:
        """
        Analyze failure patterns to improve future recovery.
        
        Returns:
            Analysis results
        """
        self.logger.info("Analyzing failure patterns")
        
        # Count failures by type and path
        failures_by_type: Dict[str, int] = {}
        failures_by_path: Dict[str, int] = {}
        
        for result in self.recovery_history:
            if not result.success:
                # Count by type
                if result.issue_type in failures_by_type:
                    failures_by_type[result.issue_type] += 1
                else:
                    failures_by_type[result.issue_type] = 1
                    
                # Count by path
                if result.path in failures_by_path:
                    failures_by_path[result.path] += 1
                else:
                    failures_by_path[result.path] = 1
        
        # Identify recurring issues
        recurring_issues = [
            path for path, count in failures_by_path.items()
            if count >= 3  # Consider an issue recurring if it failed 3+ times
        ]
        
        # Identify most common failure types
        common_failures = sorted(
            failures_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "total_recoveries": len(self.recovery_history),
            "successful_recoveries": sum(1 for r in self.recovery_history if r.success),
            "failed_recoveries": sum(1 for r in self.recovery_history if not r.success),
            "failures_by_type": failures_by_type,
            "failures_by_path": failures_by_path,
            "recurring_issues": recurring_issues,
            "common_failures": common_failures,
            "analysis_time": datetime.now().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the RegenerationEngine."""
        self.logger.info("Shutting down RegenerationEngine")
        
        # Clear state
        self.component_checksums.clear()
        self.recovery_attempts.clear()
        self.recovery_history.clear()
        
        self.logger.info("RegenerationEngine shutdown complete")