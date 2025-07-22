"""
Traversal Engine for the Phoenix DemiGod system.

The Traversal Engine analyzes the state tree to identify patterns,
detect gaps, and inform the differentiation process.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from phoenix_demigod.core.state_tree import StateNode, StateTree
from phoenix_demigod.utils.logging import get_logger


class Pattern:
    """Represents a detected pattern in the state tree."""
    
    def __init__(
        self,
        type: str,
        path: str,
        confidence: float,
        data: Dict[str, Any] = None
    ):
        """
        Initialize a new Pattern.
        
        Args:
            type: Type of pattern (e.g., "REPETITION", "STRUCTURE", "TREND")
            path: Path to the node where the pattern was detected
            confidence: Confidence score (0.0-1.0)
            data: Additional pattern data (default: empty dict)
        """
        self.type = type
        self.path = path
        self.confidence = confidence
        self.data = data or {}
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the pattern to a dictionary representation.
        
        Returns:
            Dictionary representation of the pattern
        """
        return {
            "type": self.type,
            "path": self.path,
            "confidence": self.confidence,
            "data": self.data,
            "detected_at": self.detected_at.isoformat()
        }


class Gap:
    """Represents a detected gap or need in the state tree."""
    
    def __init__(
        self,
        type: str,
        path: str,
        priority: float,
        description: str,
        data: Dict[str, Any] = None
    ):
        """
        Initialize a new Gap.
        
        Args:
            type: Type of gap (e.g., "MISSING_FUNCTIONALITY", "OPTIMIZATION")
            path: Path to the node where the gap was detected
            priority: Priority score (0.0-1.0)
            description: Human-readable description of the gap
            data: Additional gap data (default: empty dict)
        """
        self.type = type
        self.path = path
        self.priority = priority
        self.description = description
        self.data = data or {}
        self.detected_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the gap to a dictionary representation.
        
        Returns:
            Dictionary representation of the gap
        """
        return {
            "type": self.type,
            "path": self.path,
            "priority": self.priority,
            "description": self.description,
            "data": self.data,
            "detected_at": self.detected_at.isoformat()
        }


class Recommendation:
    """Represents a recommendation based on analysis."""
    
    def __init__(
        self,
        type: str,
        path: str,
        priority: float,
        description: str,
        action: str,
        data: Dict[str, Any] = None
    ):
        """
        Initialize a new Recommendation.
        
        Args:
            type: Type of recommendation (e.g., "OPTIMIZATION", "RESTRUCTURE")
            path: Path to the node the recommendation applies to
            priority: Priority score (0.0-1.0)
            description: Human-readable description of the recommendation
            action: Suggested action to take
            data: Additional recommendation data (default: empty dict)
        """
        self.type = type
        self.path = path
        self.priority = priority
        self.description = description
        self.action = action
        self.data = data or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the recommendation to a dictionary representation.
        
        Returns:
            Dictionary representation of the recommendation
        """
        return {
            "type": self.type,
            "path": self.path,
            "priority": self.priority,
            "description": self.description,
            "action": self.action,
            "data": self.data,
            "created_at": self.created_at.isoformat()
        }


class AnalysisReport:
    """Report containing the results of state tree analysis."""
    
    def __init__(self):
        """Initialize a new AnalysisReport."""
        self.patterns: List[Pattern] = []
        self.gaps: List[Gap] = []
        self.recommendations: List[Recommendation] = []
        self.complexity_metrics: Dict[str, float] = {}
        self.timestamp = datetime.now()
    
    def add_pattern(self, pattern: Pattern) -> None:
        """
        Add a pattern to the report.
        
        Args:
            pattern: Pattern to add
        """
        self.patterns.append(pattern)
    
    def add_gap(self, gap: Gap) -> None:
        """
        Add a gap to the report.
        
        Args:
            gap: Gap to add
        """
        self.gaps.append(gap)
    
    def add_recommendation(self, recommendation: Recommendation) -> None:
        """
        Add a recommendation to the report.
        
        Args:
            recommendation: Recommendation to add
        """
        self.recommendations.append(recommendation)
    
    def set_complexity_metric(self, name: str, value: float) -> None:
        """
        Set a complexity metric.
        
        Args:
            name: Metric name
            value: Metric value
        """
        self.complexity_metrics[name] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a dictionary representation.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "gaps": [g.to_dict() for g in self.gaps],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "complexity_metrics": self.complexity_metrics,
            "timestamp": self.timestamp.isoformat()
        }


class TraversalEngine:
    """
    Engine for analyzing the state tree.
    
    The TraversalEngine performs depth-first traversal of the state tree
    to identify patterns, detect gaps, and generate recommendations.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a new TraversalEngine.
        
        Args:
            config: Configuration parameters (default: empty dict)
        """
        self.logger = get_logger("phoenix_demigod.engines.traversal")
        self.config = config or {}
        
        # Extract configuration parameters with defaults
        self.pattern_confidence_threshold = self.config.get("pattern_confidence_threshold", 0.7)
        self.complexity_threshold = self.config.get("complexity_threshold", 5.0)
        self.gap_detection_sensitivity = self.config.get("gap_detection_sensitivity", 0.5)
        self.max_traversal_time = self.config.get("max_traversal_time", 30.0)
        self.parallel_processing = self.config.get("parallel_processing", True)
        self.cache_results = self.config.get("cache_results", True)
        
        # Initialize cache
        self.pattern_cache: Dict[str, List[Pattern]] = {}
        self.gap_cache: Dict[str, List[Gap]] = {}
        
        self.logger.info(f"TraversalEngine initialized with config: {self.config}")
    
    async def traverse(self, root_node: StateNode) -> AnalysisReport:
        """
        Perform a complete traversal of the state tree.
        
        Args:
            root_node: Root node of the state tree
            
        Returns:
            Analysis report containing patterns, gaps, and recommendations
        """
        self.logger.info("Starting state tree traversal")
        start_time = time.time()
        
        # Create a new analysis report
        report = AnalysisReport()
        
        # Track visited nodes to avoid cycles
        visited: Set[str] = set()
        
        # Perform depth-first traversal
        await self._traverse_node(root_node, "", report, visited, depth=0)
        
        # Calculate overall complexity metrics
        self._calculate_complexity_metrics(root_node, report)
        
        # Generate recommendations based on patterns and gaps
        self._generate_recommendations(report)
        
        elapsed_time = time.time() - start_time
        self.logger.info(
            f"Traversal completed in {elapsed_time:.3f}s: "
            f"{len(report.patterns)} patterns, "
            f"{len(report.gaps)} gaps, "
            f"{len(report.recommendations)} recommendations"
        )
        
        return report
    
    async def _traverse_node(
        self,
        node: StateNode,
        path: str,
        report: AnalysisReport,
        visited: Set[str],
        depth: int
    ) -> None:
        """
        Recursively traverse a node and its children.
        
        Args:
            node: Current node
            path: Path to the current node
            report: Analysis report to update
            visited: Set of visited node IDs
            depth: Current depth in the tree
        """
        # Check if we've already visited this node
        if node.id in visited:
            return
            
        # Check if we've exceeded the maximum traversal time
        if time.time() - report.timestamp.timestamp() > self.max_traversal_time:
            self.logger.warning(f"Traversal time limit exceeded ({self.max_traversal_time}s)")
            return
            
        # Mark as visited
        visited.add(node.id)
        
        # Update path
        current_path = f"{path}/{node.id}" if path else f"/{node.id}"
        
        # Detect patterns in this node
        patterns = await self._detect_patterns(node, current_path)
        for pattern in patterns:
            report.add_pattern(pattern)
        
        # Detect gaps in this node
        gaps = await self._detect_gaps(node, current_path)
        for gap in gaps:
            report.add_gap(gap)
        
        # Recursively traverse children
        for child in node.children:
            await self._traverse_node(child, current_path, report, visited, depth + 1)
    
    async def _detect_patterns(self, node: StateNode, path: str) -> List[Pattern]:
        """
        Detect patterns in a node.
        
        Args:
            node: Node to analyze
            path: Path to the node
            
        Returns:
            List of detected patterns
        """
        patterns: List[Pattern] = []
        
        # Check cache if enabled
        if self.cache_results and path in self.pattern_cache:
            return self.pattern_cache[path]
        
        # Example pattern detection: Repetitive structure
        if len(node.children) > 2:
            # Check if children have similar structure
            child_types = [child.type for child in node.children]
            unique_types = set(child_types)
            
            if len(unique_types) == 1 and len(child_types) >= 3:
                # All children have the same type
                confidence = min(1.0, 0.7 + 0.05 * len(child_types))
                
                if confidence >= self.pattern_confidence_threshold:
                    patterns.append(Pattern(
                        type="REPETITION",
                        path=path,
                        confidence=confidence,
                        data={
                            "child_type": list(unique_types)[0],
                            "count": len(child_types)
                        }
                    ))
        
        # Example pattern detection: Temporal trend
        if "updated_at" in node.data and isinstance(node.data.get("updated_at"), str):
            try:
                # Check if this node is updated frequently
                updated_at = datetime.fromisoformat(node.data["updated_at"])
                age_seconds = (datetime.now() - updated_at).total_seconds()
                
                if age_seconds < 300:  # Updated in the last 5 minutes
                    patterns.append(Pattern(
                        type="FREQUENT_UPDATES",
                        path=path,
                        confidence=0.8,
                        data={
                            "age_seconds": age_seconds,
                            "updated_at": node.data["updated_at"]
                        }
                    ))
            except (ValueError, TypeError):
                pass
        
        # Example pattern detection: Data growth
        if isinstance(node.data.get("size"), (int, float)) and node.version > 1:
            size = node.data["size"]
            if size > 1000:
                patterns.append(Pattern(
                    type="LARGE_DATA",
                    path=path,
                    confidence=0.75,
                    data={
                        "size": size,
                        "version": node.version
                    }
                ))
        
        # Cache results if enabled
        if self.cache_results:
            self.pattern_cache[path] = patterns
            
        return patterns
    
    async def _detect_gaps(self, node: StateNode, path: str) -> List[Gap]:
        """
        Detect gaps in a node.
        
        Args:
            node: Node to analyze
            path: Path to the node
            
        Returns:
            List of detected gaps
        """
        gaps: List[Gap] = []
        
        # Check cache if enabled
        if self.cache_results and path in self.gap_cache:
            return self.gap_cache[path]
        
        # Example gap detection: Missing metadata
        if not node.metadata:
            gaps.append(Gap(
                type="MISSING_METADATA",
                path=path,
                priority=0.6,
                description=f"Node {node.id} is missing metadata",
                data={
                    "node_type": node.type
                }
            ))
        
        # Example gap detection: Incomplete data
        if node.type == "branch" and not node.children:
            gaps.append(Gap(
                type="EMPTY_BRANCH",
                path=path,
                priority=0.7,
                description=f"Branch node {node.id} has no children",
                data={
                    "node_type": node.type
                }
            ))
        
        # Example gap detection: Optimization opportunity
        if len(node.children) > 10:
            gaps.append(Gap(
                type="OPTIMIZATION",
                path=path,
                priority=0.5,
                description=f"Node {node.id} has many children ({len(node.children)})",
                data={
                    "child_count": len(node.children)
                }
            ))
        
        # Cache results if enabled
        if self.cache_results:
            self.gap_cache[path] = gaps
            
        return gaps
    
    def _calculate_complexity_metrics(self, root_node: StateNode, report: AnalysisReport) -> None:
        """
        Calculate complexity metrics for the state tree.
        
        Args:
            root_node: Root node of the state tree
            report: Analysis report to update
        """
        # Calculate tree depth
        max_depth = self._calculate_max_depth(root_node)
        report.set_complexity_metric("max_depth", max_depth)
        
        # Calculate total node count
        node_count = self._count_nodes(root_node)
        report.set_complexity_metric("node_count", node_count)
        
        # Calculate average branching factor
        if node_count > 1:
            avg_branching = self._calculate_avg_branching(root_node)
            report.set_complexity_metric("avg_branching", avg_branching)
        
        # Calculate complexity score
        complexity_score = (max_depth * 0.4) + (node_count * 0.01) + (len(report.patterns) * 0.1)
        report.set_complexity_metric("complexity_score", complexity_score)
    
    def _calculate_max_depth(self, node: StateNode, current_depth: int = 0) -> int:
        """
        Calculate the maximum depth of the tree.
        
        Args:
            node: Current node
            current_depth: Current depth
            
        Returns:
            Maximum depth of the tree
        """
        if not node.children:
            return current_depth
            
        return max(
            self._calculate_max_depth(child, current_depth + 1)
            for child in node.children
        )
    
    def _count_nodes(self, node: StateNode) -> int:
        """
        Count the number of nodes in the tree.
        
        Args:
            node: Root node
            
        Returns:
            Number of nodes in the tree
        """
        count = 1  # Count this node
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    def _calculate_avg_branching(self, node: StateNode) -> float:
        """
        Calculate the average branching factor of the tree.
        
        Args:
            node: Root node
            
        Returns:
            Average branching factor
        """
        total_children = 0
        non_leaf_nodes = 0
        
        def count_children(n: StateNode) -> None:
            nonlocal total_children, non_leaf_nodes
            
            if n.children:
                non_leaf_nodes += 1
                total_children += len(n.children)
                
                for child in n.children:
                    count_children(child)
        
        count_children(node)
        
        if non_leaf_nodes == 0:
            return 0.0
            
        return total_children / non_leaf_nodes
    
    def _generate_recommendations(self, report: AnalysisReport) -> None:
        """
        Generate recommendations based on patterns and gaps.
        
        Args:
            report: Analysis report to update
        """
        # Process patterns
        for pattern in report.patterns:
            if pattern.type == "REPETITION" and pattern.confidence > 0.8:
                report.add_recommendation(Recommendation(
                    type="STRUCTURE_OPTIMIZATION",
                    path=pattern.path,
                    priority=0.7,
                    description=f"Optimize repetitive structure at {pattern.path}",
                    action="Create a specialized handler for this pattern",
                    data={
                        "pattern_type": pattern.type,
                        "pattern_data": pattern.data
                    }
                ))
            elif pattern.type == "FREQUENT_UPDATES" and pattern.confidence > 0.7:
                report.add_recommendation(Recommendation(
                    type="CACHING",
                    path=pattern.path,
                    priority=0.8,
                    description=f"Implement caching for frequently updated node at {pattern.path}",
                    action="Add a caching layer to reduce update frequency",
                    data={
                        "pattern_type": pattern.type,
                        "pattern_data": pattern.data
                    }
                ))
            elif pattern.type == "LARGE_DATA" and pattern.confidence > 0.7:
                report.add_recommendation(Recommendation(
                    type="DATA_OPTIMIZATION",
                    path=pattern.path,
                    priority=0.6,
                    description=f"Optimize large data storage at {pattern.path}",
                    action="Implement data compression or pagination",
                    data={
                        "pattern_type": pattern.type,
                        "pattern_data": pattern.data
                    }
                ))
        
        # Process gaps
        for gap in report.gaps:
            if gap.type == "MISSING_METADATA" and gap.priority > 0.5:
                report.add_recommendation(Recommendation(
                    type="METADATA_ENHANCEMENT",
                    path=gap.path,
                    priority=0.5,
                    description=f"Add metadata to node at {gap.path}",
                    action="Generate metadata based on node type and context",
                    data={
                        "gap_type": gap.type,
                        "gap_data": gap.data
                    }
                ))
            elif gap.type == "EMPTY_BRANCH" and gap.priority > 0.6:
                report.add_recommendation(Recommendation(
                    type="STRUCTURE_COMPLETION",
                    path=gap.path,
                    priority=0.7,
                    description=f"Populate empty branch at {gap.path}",
                    action="Generate child nodes based on branch purpose",
                    data={
                        "gap_type": gap.type,
                        "gap_data": gap.data
                    }
                ))
            elif gap.type == "OPTIMIZATION" and gap.priority > 0.4:
                report.add_recommendation(Recommendation(
                    type="PERFORMANCE_OPTIMIZATION",
                    path=gap.path,
                    priority=0.6,
                    description=f"Optimize node with many children at {gap.path}",
                    action="Implement pagination or hierarchical organization",
                    data={
                        "gap_type": gap.type,
                        "gap_data": gap.data
                    }
                ))
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the TraversalEngine."""
        self.logger.info("Shutting down TraversalEngine")
        
        # Clear caches
        self.pattern_cache.clear()
        self.gap_cache.clear()
        
        self.logger.info("TraversalEngine shutdown complete")