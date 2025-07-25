"""
Dependency Analyzer for Phoenix Hydra System Review Tool

Analyzes inter-component relationships, validates dependencies,
and detects dependency conflicts in the Phoenix Hydra system.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

from ..models.data_models import Component, ComponentCategory, ComponentStatus
from ..criteria.infrastructure_criteria import InfrastructureComponent
from ..criteria.monetization_criteria import MonetizationComponent
from ..criteria.automation_criteria import AutomationComponentType


class DependencyType(Enum):
    """Types of dependencies between components"""
    REQUIRED = "required"  # Hard dependency - component cannot function without it
    OPTIONAL = "optional"  # Soft dependency - component has reduced functionality without it
    CIRCULAR = "circular"  # Circular dependency - mutual dependency
    CONFLICTING = "conflicting"  # Conflicting dependency - components cannot coexist


class DependencyStatus(Enum):
    """Status of a dependency relationship"""
    SATISFIED = "satisfied"  # Dependency is met
    MISSING = "missing"  # Required dependency is not available
    DEGRADED = "degraded"  # Dependency is available but not fully functional
    CONFLICTED = "conflicted"  # Dependency creates a conflict


@dataclass
class Dependency:
    """Represents a dependency relationship between components"""
    source: str  # Component that has the dependency
    target: str  # Component that is depended upon
    dependency_type: DependencyType
    status: DependencyStatus
    description: str
    version_requirement: Optional[str] = None
    configuration_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph of the system"""
    components: Dict[str, Component] = field(default_factory=dict)
    dependencies: List[Dependency] = field(default_factory=list)
    adjacency_list: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    reverse_adjacency_list: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))


@dataclass
class DependencyAnalysisResult:
    """Results from dependency analysis"""
    dependency_graph: DependencyGraph
    circular_dependencies: List[List[str]] = field(default_factory=list)
    missing_dependencies: List[Dependency] = field(default_factory=list)
    conflicting_dependencies: List[Tuple[Dependency, Dependency]] = field(default_factory=list)
    dependency_violations: List[str] = field(default_factory=list)
    component_dependency_scores: Dict[str, float] = field(default_factory=dict)
    overall_dependency_health: float = 0.0


class DependencyAnalyzer:
    """
    Analyzes dependencies between Phoenix Hydra components.
    
    Provides functionality to map dependencies, validate relationships,
    detect conflicts, and analyze the overall dependency health of the system.
    """
    
    def __init__(self):
        """Initialize dependency analyzer"""
        self.logger = logging.getLogger(__name__)
        self.known_dependencies = self._build_known_dependencies()
    
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
            missing_deps = self._find_missing_dependencies(dependency_graph)
            
            # Detect conflicting dependencies
            conflicting_deps = self._detect_conflicting_dependencies(dependency_graph)
            
            # Identify dependency violations
            violations = self._identify_dependency_violations(dependency_graph)
            
            # Calculate dependency scores
            component_scores = self._calculate_dependency_scores(dependency_graph, missing_deps, conflicting_deps)
            
            # Calculate overall dependency health
            overall_health = self._calculate_overall_dependency_health(component_scores, circular_deps, missing_deps, conflicting_deps)
            
            return DependencyAnalysisResult(
                dependency_graph=dependency_graph,
                circular_dependencies=circular_deps,
                missing_dependencies=missing_deps,
                conflicting_dependencies=conflicting_deps,
                dependency_violations=violations,
                component_dependency_scores=component_scores,
                overall_dependency_health=overall_health
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing dependencies: {e}")
            return DependencyAnalysisResult(
                dependency_graph=DependencyGraph(),
                overall_dependency_health=0.0
            )
    
    def _build_dependency_graph(self, components: List[Component]) -> DependencyGraph:
        """Build a dependency graph from components"""
        graph = DependencyGraph()
        
        # Add components to graph
        for component in components:
            graph.components[component.name] = component
        
        # Build dependencies based on known relationships and component analysis
        for component in components:
            dependencies = self._extract_component_dependencies(component, graph.components)
            
            for dep in dependencies:
                graph.dependencies.append(dep)
                graph.adjacency_list[dep.source].append(dep.target)
                graph.reverse_adjacency_list[dep.target].append(dep.source)
        
        return graph
    
    def _extract_component_dependencies(self, component: Component, all_components: Dict[str, Component]) -> List[Dependency]:
        """Extract dependencies for a specific component"""
        dependencies = []
        
        # Check explicit dependencies from component configuration
        if hasattr(component, 'dependencies') and component.dependencies:
            for dep_name in component.dependencies:
                if dep_name in all_components:
                    dependencies.append(Dependency(
                        source=component.name,
                        target=dep_name,
                        dependency_type=DependencyType.REQUIRED,
                        status=self._determine_dependency_status(component, all_components[dep_name]),
                        description=f"Explicit dependency from {component.name} to {dep_name}"
                    ))
                else:
                    # Missing explicit dependency
                    dependencies.append(Dependency(
                        source=component.name,
                        target=dep_name,
                        dependency_type=DependencyType.REQUIRED,
                        status=DependencyStatus.MISSING,
                        description=f"Missing explicit dependency from {component.name} to {dep_name}"
                    ))
        
        # Infer dependencies based on component type and known patterns
        inferred_deps = self._infer_component_dependencies(component, all_components)
        dependencies.extend(inferred_deps)
        
        return dependencies
    
    def _infer_component_dependencies(self, component: Component, all_components: Dict[str, Component]) -> List[Dependency]:
        """Infer dependencies based on component type and Phoenix Hydra patterns"""
        dependencies = []
        component_type = self._get_component_type(component)
        
        if component_type in self.known_dependencies:
            for dep_pattern in self.known_dependencies[component_type]:
                # Find matching components
                matching_components = self._find_matching_components(dep_pattern["target_pattern"], all_components)
                
                for target_component in matching_components:
                    dependencies.append(Dependency(
                        source=component.name,
                        target=target_component.name,
                        dependency_type=DependencyType(dep_pattern["type"]),
                        status=self._determine_dependency_status(component, target_component),
                        description=dep_pattern["description"],
                        configuration_requirements=dep_pattern.get("config_requirements", {})
                    ))
        
        return dependencies
    
    def _get_component_type(self, component: Component) -> str:
        """Get the component type for dependency analysis"""
        name_lower = component.name.lower()
        
        # Infrastructure components
        if "nca" in name_lower or "toolkit" in name_lower:
            return "nca_toolkit"
        elif "podman" in name_lower or "container" in name_lower:
            return "podman_stack"
        elif "database" in name_lower or "postgres" in name_lower:
            return "database"
        elif "minio" in name_lower or "s3" in name_lower:
            return "minio_storage"
        elif "prometheus" in name_lower:
            return "prometheus"
        elif "grafana" in name_lower:
            return "grafana"
        
        # Monetization components
        elif "affiliate" in name_lower:
            return "affiliate_marketing"
        elif "grant" in name_lower:
            return "grant_tracking"
        elif "revenue" in name_lower:
            return "revenue_streams"
        
        # Automation components
        elif "vscode" in name_lower or "ide" in name_lower or "vs code" in name_lower:
            return "vscode_integration"
        elif "deployment" in name_lower and "script" in name_lower:
            return "deployment_scripts"
        elif "hook" in name_lower or "kiro" in name_lower:
            return "kiro_agent_hooks"
        
        return "unknown"
    
    def _find_matching_components(self, pattern: str, all_components: Dict[str, Component]) -> List[Component]:
        """Find components matching a dependency pattern"""
        matching = []
        
        for component in all_components.values():
            if self._component_matches_pattern(component, pattern):
                matching.append(component)
        
        return matching
    
    def _component_matches_pattern(self, component: Component, pattern: str) -> bool:
        """Check if a component matches a dependency pattern"""
        name_lower = component.name.lower()
        pattern_lower = pattern.lower()
        
        # Direct name match
        if pattern_lower in name_lower:
            return True
        
        # Category match
        if pattern_lower == component.category.value:
            return True
        
        # Path-based match
        if hasattr(component, 'path') and pattern_lower in component.path.lower():
            return True
        
        return False
    
    def _determine_dependency_status(self, source: Component, target: Component) -> DependencyStatus:
        """Determine the status of a dependency relationship"""
        if target.status == ComponentStatus.OPERATIONAL:
            return DependencyStatus.SATISFIED
        elif target.status == ComponentStatus.DEGRADED:
            return DependencyStatus.DEGRADED
        elif target.status == ComponentStatus.FAILED:
            return DependencyStatus.MISSING
        else:
            return DependencyStatus.MISSING
    
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
                dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
            return False
        
        for component in graph.components:
            if component not in visited:
                dfs(component, [])
        
        return cycles
    
    def _find_missing_dependencies(self, graph: DependencyGraph) -> List[Dependency]:
        """Find dependencies that are missing or not satisfied"""
        missing = []
        
        for dependency in graph.dependencies:
            if dependency.status in [DependencyStatus.MISSING, DependencyStatus.CONFLICTED]:
                missing.append(dependency)
            elif dependency.dependency_type == DependencyType.REQUIRED and dependency.target not in graph.components:
                # Required dependency component doesn't exist
                missing.append(Dependency(
                    source=dependency.source,
                    target=dependency.target,
                    dependency_type=DependencyType.REQUIRED,
                    status=DependencyStatus.MISSING,
                    description=f"Required component {dependency.target} is missing"
                ))
        
        return missing
    
    def _detect_conflicting_dependencies(self, graph: DependencyGraph) -> List[Tuple[Dependency, Dependency]]:
        """Detect conflicting dependencies"""
        conflicts = []
        
        # Check for components that have conflicting requirements
        for component_name, component in graph.components.items():
            component_deps = [dep for dep in graph.dependencies if dep.source == component_name]
            
            # Check for version conflicts
            target_versions = defaultdict(list)
            for dep in component_deps:
                if dep.version_requirement:
                    target_versions[dep.target].append(dep)
            
            for target, deps in target_versions.items():
                if len(deps) > 1:
                    # Multiple version requirements for the same target
                    for i in range(len(deps)):
                        for j in range(i + 1, len(deps)):
                            if deps[i].version_requirement != deps[j].version_requirement:
                                conflicts.append((deps[i], deps[j]))
        
        return conflicts
    
    def _identify_dependency_violations(self, graph: DependencyGraph) -> List[str]:
        """Identify dependency architecture violations"""
        violations = []
        
        # Check for violations of Phoenix Hydra architecture principles
        for dependency in graph.dependencies:
            source_component = graph.components.get(dependency.source)
            target_component = graph.components.get(dependency.target)
            
            if source_component and target_component:
                # Check layer violations (e.g., infrastructure depending on monetization)
                if self._is_layer_violation(source_component, target_component):
                    violations.append(
                        f"Layer violation: {source_component.category.value} component "
                        f"'{source_component.name}' depends on {target_component.category.value} "
                        f"component '{target_component.name}'"
                    )
        
        return violations
    
    def _is_layer_violation(self, source: Component, target: Component) -> bool:
        """Check if dependency represents a layer violation"""
        # Define allowed dependency directions in Phoenix Hydra architecture
        allowed_dependencies = {
            ComponentCategory.MONETIZATION: [ComponentCategory.INFRASTRUCTURE, ComponentCategory.AUTOMATION],
            ComponentCategory.AUTOMATION: [ComponentCategory.INFRASTRUCTURE],
            ComponentCategory.INFRASTRUCTURE: []  # Infrastructure should not depend on higher layers
        }
        
        if source.category in allowed_dependencies:
            return target.category not in allowed_dependencies[source.category]
        
        return False
    
    def _calculate_dependency_scores(self, graph: DependencyGraph, missing_deps: List[Dependency], 
                                   conflicting_deps: List[Tuple[Dependency, Dependency]]) -> Dict[str, float]:
        """Calculate dependency health scores for each component"""
        scores = {}
        
        for component_name in graph.components:
            # Get all dependencies for this component
            component_deps = [dep for dep in graph.dependencies if dep.source == component_name]
            
            if not component_deps:
                scores[component_name] = 1.0  # No dependencies = perfect score
                continue
            
            satisfied_count = 0
            total_weight = 0
            
            for dep in component_deps:
                weight = 1.0 if dep.dependency_type == DependencyType.REQUIRED else 0.5
                total_weight += weight
                
                if dep.status == DependencyStatus.SATISFIED:
                    satisfied_count += weight
                elif dep.status == DependencyStatus.DEGRADED:
                    satisfied_count += weight * 0.5
                # Missing or conflicted dependencies contribute 0
            
            # Calculate base score
            base_score = satisfied_count / total_weight if total_weight > 0 else 1.0
            
            # Apply penalties for missing or conflicting dependencies
            missing_penalty = len([dep for dep in missing_deps if dep.source == component_name]) * 0.1
            conflict_penalty = len([conf for conf in conflicting_deps 
                                  if conf[0].source == component_name or conf[1].source == component_name]) * 0.15
            
            final_score = max(0.0, base_score - missing_penalty - conflict_penalty)
            scores[component_name] = final_score
        
        return scores
    
    def _calculate_overall_dependency_health(self, component_scores: Dict[str, float], 
                                           circular_deps: List[List[str]], 
                                           missing_deps: List[Dependency],
                                           conflicting_deps: List[Tuple[Dependency, Dependency]]) -> float:
        """Calculate overall system dependency health"""
        if not component_scores:
            return 0.0
        
        # Base score is average of component scores
        base_score = sum(component_scores.values()) / len(component_scores)
        
        # Apply penalties for system-level issues
        circular_penalty = len(circular_deps) * 0.1
        missing_penalty = len(missing_deps) * 0.05
        conflict_penalty = len(conflicting_deps) * 0.1
        
        final_score = max(0.0, base_score - circular_penalty - missing_penalty - conflict_penalty)
        return min(1.0, final_score)
    
    def _build_known_dependencies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build known dependency patterns for Phoenix Hydra components"""
        return {
            "nca_toolkit": [
                {
                    "target_pattern": "database",
                    "type": "required",
                    "description": "NCA Toolkit requires database for storing processing results",
                    "config_requirements": {"connection_string": "required"}
                },
                {
                    "target_pattern": "minio",
                    "type": "required", 
                    "description": "NCA Toolkit requires S3 storage for multimedia files",
                    "config_requirements": {"s3_endpoint": "required", "access_key": "required"}
                }
            ],
            "grafana": [
                {
                    "target_pattern": "prometheus",
                    "type": "required",
                    "description": "Grafana requires Prometheus as data source",
                    "config_requirements": {"prometheus_url": "required"}
                }
            ],
            "affiliate_marketing": [
                {
                    "target_pattern": "database",
                    "type": "required",
                    "description": "Affiliate marketing requires database for tracking",
                    "config_requirements": {"connection_string": "required"}
                },
                {
                    "target_pattern": "nca_toolkit",
                    "type": "optional",
                    "description": "Affiliate marketing may integrate with NCA Toolkit APIs"
                }
            ],
            "revenue_streams": [
                {
                    "target_pattern": "database",
                    "type": "required",
                    "description": "Revenue tracking requires database for metrics storage"
                },
                {
                    "target_pattern": "affiliate_marketing",
                    "type": "optional",
                    "description": "Revenue streams may include affiliate marketing data"
                }
            ],
            "deployment_scripts": [
                {
                    "target_pattern": "podman",
                    "type": "required",
                    "description": "Deployment scripts require container orchestration"
                }
            ],
            "kiro_agent_hooks": [
                {
                    "target_pattern": "vscode",
                    "type": "optional",
                    "description": "Agent hooks integrate with VS Code for automation"
                }
            ]
        }
    
    def get_dependency_recommendations(self, analysis_result: DependencyAnalysisResult) -> List[str]:
        """Generate recommendations based on dependency analysis"""
        recommendations = []
        
        # Recommendations for circular dependencies
        if analysis_result.circular_dependencies:
            recommendations.append(
                f"Resolve {len(analysis_result.circular_dependencies)} circular dependencies "
                "by introducing interfaces or breaking dependency cycles"
            )
        
        # Recommendations for missing dependencies
        if analysis_result.missing_dependencies:
            for dep in analysis_result.missing_dependencies[:5]:  # Top 5
                recommendations.append(
                    f"Implement missing dependency: {dep.target} required by {dep.source}"
                )
        
        # Recommendations for conflicting dependencies
        if analysis_result.conflicting_dependencies:
            recommendations.append(
                f"Resolve {len(analysis_result.conflicting_dependencies)} dependency conflicts "
                "by standardizing versions or using dependency injection"
            )
        
        # Recommendations for low-scoring components
        low_score_components = [
            name for name, score in analysis_result.component_dependency_scores.items() 
            if score < 0.7
        ]
        if low_score_components:
            recommendations.append(
                f"Improve dependency health for components: {', '.join(low_score_components[:3])}"
            )
        
        return recommendations
    
    def generate_dependency_report(self, analysis_result: DependencyAnalysisResult) -> Dict[str, Any]:
        """Generate comprehensive dependency analysis report"""
        return {
            "overall_health": analysis_result.overall_dependency_health,
            "total_components": len(analysis_result.dependency_graph.components),
            "total_dependencies": len(analysis_result.dependency_graph.dependencies),
            "circular_dependencies_count": len(analysis_result.circular_dependencies),
            "missing_dependencies_count": len(analysis_result.missing_dependencies),
            "conflicting_dependencies_count": len(analysis_result.conflicting_dependencies),
            "dependency_violations_count": len(analysis_result.dependency_violations),
            "component_scores": analysis_result.component_dependency_scores,
            "recommendations": self.get_dependency_recommendations(analysis_result),
            "circular_dependencies": analysis_result.circular_dependencies,
            "missing_dependencies": [
                {
                    "source": dep.source,
                    "target": dep.target,
                    "type": dep.dependency_type.value,
                    "description": dep.description
                }
                for dep in analysis_result.missing_dependencies
            ],
            "dependency_violations": analysis_result.dependency_violations
        }