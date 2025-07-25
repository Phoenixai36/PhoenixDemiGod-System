"""
Dependency Analyzer for Phoenix Hydra System Review Tool

Analyzes component dependencies, maps inter-component relationships,
and detects dependency conflicts in the Phoenix Hydra system.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

from ..models.data_models import Component, ComponentCategory, ComponentStatus


class DependencyType(Enum):
    """Types of dependencies between components"""
    DIRECT = "direct"
    TRANSITIVE = "transitive"
    CIRCULAR = "circular"
    OPTIONAL = "optional"
    RUNTIME = "runtime"
    BUILD = "build"


class ConflictSeverity(Enum):
    """Severity levels for dependency conflicts"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Dependency:
    """Represents a dependency relationship between components"""
    source: str  # Component that depends on target
    target: str  # Component being depended upon
    dependency_type: DependencyType
    required: bool = True
    version_constraint: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DependencyConflict:
    """Represents a conflict in dependency relationships"""
    conflict_type: str
    severity: ConflictSeverity
    components: List[str]
    description: str
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph"""
    nodes: Set[str] = field(default_factory=set)
    edges: List[Dependency] = field(default_factory=list)
    adjacency_list: Dict[str, List[str]] = field(default_factory=dict)
    reverse_adjacency_list: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class DependencyAnalysisResult:
    """Results from dependency analysis"""
    dependency_graph: DependencyGraph
    circular_dependencies: List[List[str]] = field(default_factory=list)
    missing_dependencies: List[str] = field(default_factory=list)
    conflicts: List[DependencyConflict] = field(default_factory=list)
    dependency_depth: Dict[str, int] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    orphaned_components: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """
    Analyzes dependencies between Phoenix Hydra components.
    
    Provides functionality to map dependencies, detect conflicts,
    analyze relationships, and generate dependency insights.
    """
    
    def __init__(self):
        """Initialize dependency analyzer"""
        self.logger = logging.getLogger(__name__)
        self.known_phoenix_dependencies = self._build_phoenix_dependency_map()
    
    def analyze_dependencies(self, components: List[Component]) -> DependencyAnalysisResult:
        """
        Analyze dependencies for a list of components.
        
        Args:
            components: List of components to analyze
            
        Returns:
            DependencyAnalysisResult with complete analysis
        """
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(components)
            
            # Detect circular dependencies
            circular_deps = self._detect_circular_dependencies(dependency_graph)
            
            # Find missing dependencies
            missing_deps = self._find_missing_dependencies(components, dependency_graph)
            
            # Detect conflicts
            conflicts = self._detect_dependency_conflicts(components, dependency_graph)
            
            # Calculate dependency depth
            dependency_depth = self._calculate_dependency_depth(dependency_graph)
            
            # Find critical path
            critical_path = self._find_critical_path(dependency_graph, dependency_depth)
            
            # Find orphaned components
            orphaned = self._find_orphaned_components(dependency_graph)
            
            return DependencyAnalysisResult(
                dependency_graph=dependency_graph,
                circular_dependencies=circular_deps,
                missing_dependencies=missing_deps,
                conflicts=conflicts,
                dependency_depth=dependency_depth,
                critical_path=critical_path,
                orphaned_components=orphaned
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}")
            return DependencyAnalysisResult(dependency_graph=DependencyGraph())
    
    def get_component_dependencies(self, component_name: str, dependency_graph: DependencyGraph) -> List[str]:
        """Get direct dependencies for a component"""
        return dependency_graph.adjacency_list.get(component_name, [])
    
    def get_component_dependents(self, component_name: str, dependency_graph: DependencyGraph) -> List[str]:
        """Get components that depend on this component"""
        return dependency_graph.reverse_adjacency_list.get(component_name, [])
    
    def get_transitive_dependencies(self, component_name: str, dependency_graph: DependencyGraph) -> Set[str]:
        """Get all transitive dependencies for a component"""
        visited = set()
        queue = deque([component_name])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            dependencies = dependency_graph.adjacency_list.get(current, [])
            for dep in dependencies:
                if dep not in visited:
                    queue.append(dep)
        
        visited.discard(component_name)  # Remove self
        return visited
    
    def calculate_impact_score(self, component_name: str, dependency_graph: DependencyGraph) -> float:
        """Calculate impact score based on dependency relationships"""
        # Components with more dependents have higher impact
        dependents = len(self.get_component_dependents(component_name, dependency_graph))
        dependencies = len(self.get_component_dependencies(component_name, dependency_graph))
        
        # Weight dependents more heavily than dependencies
        impact_score = (dependents * 2.0) + (dependencies * 0.5)
        
        # Normalize to 0-1 scale based on total components
        total_components = len(dependency_graph.nodes)
        if total_components > 1:
            max_possible_score = (total_components - 1) * 2.0 + (total_components - 1) * 0.5
            impact_score = min(impact_score / max_possible_score, 1.0)
        
        return impact_score
    
    def _build_dependency_graph(self, components: List[Component]) -> DependencyGraph:
        """Build dependency graph from components"""
        graph = DependencyGraph()
        
        # Add all components as nodes
        for component in components:
            graph.nodes.add(component.name)
            graph.adjacency_list[component.name] = []
            graph.reverse_adjacency_list[component.name] = []
        
        # Add dependencies from component definitions
        for component in components:
            for dep_name in component.dependencies:
                if dep_name in graph.nodes:
                    dependency = Dependency(
                        source=component.name,
                        target=dep_name,
                        dependency_type=DependencyType.DIRECT,
                        required=True
                    )
                    graph.edges.append(dependency)
                    graph.adjacency_list[component.name].append(dep_name)
                    graph.reverse_adjacency_list[dep_name].append(component.name)
        
        # Add Phoenix Hydra specific dependencies
        self._add_phoenix_specific_dependencies(components, graph)
        
        return graph
    
    def _add_phoenix_specific_dependencies(self, components: List[Component], graph: DependencyGraph):
        """Add Phoenix Hydra specific dependency relationships"""
        component_map = {comp.name: comp for comp in components}
        
        for component in components:
            # Infer dependencies based on Phoenix Hydra architecture
            inferred_deps = self._infer_phoenix_dependencies(component, component_map)
            
            for dep_name in inferred_deps:
                if dep_name in graph.nodes and dep_name not in graph.adjacency_list[component.name]:
                    dependency = Dependency(
                        source=component.name,
                        target=dep_name,
                        dependency_type=DependencyType.RUNTIME,
                        required=True,
                        description="Inferred Phoenix Hydra dependency"
                    )
                    graph.edges.append(dependency)
                    graph.adjacency_list[component.name].append(dep_name)
                    graph.reverse_adjacency_list[dep_name].append(component.name)
    
    def _infer_phoenix_dependencies(self, component: Component, component_map: Dict[str, Component]) -> List[str]:
        """Infer dependencies based on Phoenix Hydra architecture patterns"""
        dependencies = []
        component_name_lower = component.name.lower()
        
        # Infrastructure dependencies
        if component.category == ComponentCategory.INFRASTRUCTURE:
            if "nca" in component_name_lower or "toolkit" in component_name_lower:
                # NCA Toolkit depends on database and storage
                dependencies.extend(self._find_components_by_pattern(component_map, ["database", "postgres"]))
                dependencies.extend(self._find_components_by_pattern(component_map, ["minio", "storage"]))
            
            elif "podman" in component_name_lower or "container" in component_name_lower:
                # Podman stack is foundational - other services depend on it
                pass
            
            elif "grafana" in component_name_lower:
                # Grafana depends on Prometheus
                dependencies.extend(self._find_components_by_pattern(component_map, ["prometheus"]))
        
        # Monetization dependencies
        elif component.category == ComponentCategory.MONETIZATION:
            # Monetization components typically depend on database and analytics
            dependencies.extend(self._find_components_by_pattern(component_map, ["database", "postgres"]))
            dependencies.extend(self._find_components_by_pattern(component_map, ["analytics"]))
        
        # Automation dependencies
        elif component.category == ComponentCategory.AUTOMATION:
            if "deployment" in component_name_lower:
                # Deployment scripts depend on container infrastructure
                dependencies.extend(self._find_components_by_pattern(component_map, ["podman", "container"]))
            
            elif "monitoring" in component_name_lower:
                # Monitoring depends on Prometheus/Grafana
                dependencies.extend(self._find_components_by_pattern(component_map, ["prometheus", "grafana"]))
        
        # Remove self-dependencies
        dependencies = [dep for dep in dependencies if dep != component.name]
        
        return dependencies
    
    def _find_components_by_pattern(self, component_map: Dict[str, Component], patterns: List[str]) -> List[str]:
        """Find components matching name patterns"""
        matches = []
        for comp_name, component in component_map.items():
            comp_name_lower = comp_name.lower()
            if any(pattern in comp_name_lower for pattern in patterns):
                matches.append(comp_name)
        return matches
    
    def _detect_circular_dependencies(self, graph: DependencyGraph) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.adjacency_list.get(node, []):
                if dfs(neighbor, path):
                    # Continue to find all cycles
                    pass
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in graph.nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _find_missing_dependencies(self, components: List[Component], graph: DependencyGraph) -> List[str]:
        """Find dependencies that are referenced but not available"""
        missing = []
        available_components = {comp.name for comp in components}
        
        for component in components:
            for dep_name in component.dependencies:
                if dep_name not in available_components:
                    missing.append(f"{component.name} -> {dep_name}")
        
        return missing
    
    def _detect_dependency_conflicts(self, components: List[Component], graph: DependencyGraph) -> List[DependencyConflict]:
        """Detect various types of dependency conflicts"""
        conflicts = []
        
        # Detect circular dependency conflicts
        circular_deps = self._detect_circular_dependencies(graph)
        for cycle in circular_deps:
            conflict = DependencyConflict(
                conflict_type="circular_dependency",
                severity=ConflictSeverity.HIGH,
                components=cycle,
                description=f"Circular dependency detected: {' -> '.join(cycle)}",
                resolution_suggestions=[
                    "Break the circular dependency by introducing an interface or abstraction",
                    "Refactor components to remove direct circular references",
                    "Use dependency injection to decouple components"
                ]
            )
            conflicts.append(conflict)
        
        # Detect version conflicts (simplified - would need version info)
        conflicts.extend(self._detect_version_conflicts(components))
        
        # Detect architectural conflicts
        conflicts.extend(self._detect_architectural_conflicts(components, graph))
        
        return conflicts
    
    def _detect_version_conflicts(self, components: List[Component]) -> List[DependencyConflict]:
        """Detect version conflicts between components"""
        conflicts = []
        
        # Group components by type for version checking
        component_types = defaultdict(list)
        for component in components:
            if component.version:
                component_types[component.category].append(component)
        
        # Check for version mismatches within categories
        for category, comps in component_types.items():
            versions = {comp.version for comp in comps if comp.version}
            if len(versions) > 1:
                conflict = DependencyConflict(
                    conflict_type="version_mismatch",
                    severity=ConflictSeverity.MEDIUM,
                    components=[comp.name for comp in comps],
                    description=f"Multiple versions detected in {category.value}: {', '.join(versions)}",
                    resolution_suggestions=[
                        "Standardize on a single version across all components",
                        "Update components to use compatible versions",
                        "Document version compatibility requirements"
                    ]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _detect_architectural_conflicts(self, components: List[Component], graph: DependencyGraph) -> List[DependencyConflict]:
        """Detect architectural conflicts in Phoenix Hydra"""
        conflicts = []
        
        # Check for missing critical infrastructure dependencies
        infrastructure_components = [c for c in components if c.category == ComponentCategory.INFRASTRUCTURE]
        monetization_components = [c for c in components if c.category == ComponentCategory.MONETIZATION]
        
        # Monetization components should have database dependencies
        database_components = [c.name for c in infrastructure_components if "database" in c.name.lower() or "postgres" in c.name.lower()]
        
        if monetization_components and not database_components:
            conflict = DependencyConflict(
                conflict_type="missing_infrastructure",
                severity=ConflictSeverity.CRITICAL,
                components=[c.name for c in monetization_components],
                description="Monetization components require database infrastructure",
                resolution_suggestions=[
                    "Add PostgreSQL database component",
                    "Configure database connections for monetization components",
                    "Ensure database schema supports monetization features"
                ]
            )
            conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_dependency_depth(self, graph: DependencyGraph) -> Dict[str, int]:
        """Calculate dependency depth for each component"""
        depth = {}
        
        def calculate_depth(node: str, visited: Set[str]) -> int:
            if node in visited:
                return 0  # Circular dependency - return 0 to avoid infinite recursion
            if node in depth:
                return depth[node]
            
            visited.add(node)
            dependencies = graph.adjacency_list.get(node, [])
            
            if not dependencies:
                depth[node] = 0
            else:
                max_dep_depth = max(calculate_depth(dep, visited.copy()) for dep in dependencies)
                depth[node] = max_dep_depth + 1
            
            return depth[node]
        
        for node in graph.nodes:
            if node not in depth:
                calculate_depth(node, set())
        
        return depth
    
    def _find_critical_path(self, graph: DependencyGraph, dependency_depth: Dict[str, int]) -> List[str]:
        """Find the critical path (longest dependency chain)"""
        if not dependency_depth:
            return []
        
        # Find the component with maximum depth
        max_depth_component = max(dependency_depth.items(), key=lambda x: x[1])
        
        # Trace back the critical path
        critical_path = []
        current = max_depth_component[0]
        
        while current:
            critical_path.append(current)
            dependencies = graph.adjacency_list.get(current, [])
            
            if not dependencies:
                break
            
            # Find dependency with maximum depth
            next_component = max(dependencies, key=lambda x: dependency_depth.get(x, 0))
            if dependency_depth.get(next_component, 0) < dependency_depth.get(current, 0):
                current = next_component
            else:
                break
        
        return critical_path
    
    def _find_orphaned_components(self, graph: DependencyGraph) -> List[str]:
        """Find components with no dependencies and no dependents"""
        orphaned = []
        
        for node in graph.nodes:
            has_dependencies = len(graph.adjacency_list.get(node, [])) > 0
            has_dependents = len(graph.reverse_adjacency_list.get(node, [])) > 0
            
            if not has_dependencies and not has_dependents:
                orphaned.append(node)
        
        return orphaned
    
    def _build_phoenix_dependency_map(self) -> Dict[str, List[str]]:
        """Build known Phoenix Hydra dependency patterns"""
        return {
            "nca_toolkit": ["database", "minio_storage"],
            "grafana": ["prometheus"],
            "monetization": ["database", "analytics"],
            "deployment_scripts": ["podman_stack"],
            "monitoring": ["prometheus", "grafana"]
        }
    
    def generate_dependency_report(self, analysis_result: DependencyAnalysisResult) -> Dict[str, Any]:
        """Generate comprehensive dependency analysis report"""
        graph = analysis_result.dependency_graph
        
        # Calculate statistics
        total_components = len(graph.nodes)
        total_dependencies = len(graph.edges)
        avg_dependencies = total_dependencies / total_components if total_components > 0 else 0
        
        # Find most connected components
        component_connections = {}
        for node in graph.nodes:
            in_degree = len(graph.reverse_adjacency_list.get(node, []))
            out_degree = len(graph.adjacency_list.get(node, []))
            component_connections[node] = in_degree + out_degree
        
        most_connected = sorted(component_connections.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "summary": {
                "total_components": total_components,
                "total_dependencies": total_dependencies,
                "average_dependencies_per_component": round(avg_dependencies, 2),
                "circular_dependencies_count": len(analysis_result.circular_dependencies),
                "missing_dependencies_count": len(analysis_result.missing_dependencies),
                "conflicts_count": len(analysis_result.conflicts),
                "orphaned_components_count": len(analysis_result.orphaned_components)
            },
            "circular_dependencies": analysis_result.circular_dependencies,
            "missing_dependencies": analysis_result.missing_dependencies,
            "conflicts": [
                {
                    "type": conflict.conflict_type,
                    "severity": conflict.severity.value,
                    "components": conflict.components,
                    "description": conflict.description,
                    "suggestions": conflict.resolution_suggestions
                }
                for conflict in analysis_result.conflicts
            ],
            "dependency_depth": analysis_result.dependency_depth,
            "critical_path": analysis_result.critical_path,
            "orphaned_components": analysis_result.orphaned_components,
            "most_connected_components": [{"name": name, "connections": count} for name, count in most_connected],
            "analysis_timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reporting"""
        from datetime import datetime
        return datetime.now().isoformat()