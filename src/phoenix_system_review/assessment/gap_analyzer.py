"""
Gap Analyzer for Phoenix Hydra System Review Tool

Implements gap identification logic comparing current state vs completion criteria,
creates missing component detection functionality, and adds incomplete implementation identification.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
from pathlib import Path

from ..models.data_models import (
    Component, ComponentCategory, Gap, ImpactLevel, Priority, 
    EvaluationResult, ComponentStatus, TaskStatus
)
from ..analysis.component_evaluator import ComponentEvaluation, EvaluationStatus
from ..analysis.quality_assessor import QualityAssessmentResult, QualityLevel
from ..analysis.dependency_analyzer import DependencyAnalysisResult, DependencyStatus


class GapType(Enum):
    """Types of gaps that can be identified"""
    MISSING_COMPONENT = "missing_component"
    INCOMPLETE_IMPLEMENTATION = "incomplete_implementation"
    CONFIGURATION_GAP = "configuration_gap"
    DEPENDENCY_GAP = "dependency_gap"
    QUALITY_GAP = "quality_gap"
    INTEGRATION_GAP = "integration_gap"
    DOCUMENTATION_GAP = "documentation_gap"
    TESTING_GAP = "testing_gap"
    SECURITY_GAP = "security_gap"


class GapSeverity(Enum):
    """Severity levels for gaps"""
    CRITICAL = "critical"      # Blocks system operation
    HIGH = "high"             # Significantly impacts functionality
    MEDIUM = "medium"         # Moderate impact on functionality
    LOW = "low"               # Minor impact or nice-to-have


@dataclass
class IdentifiedGap:
    """Represents an identified gap in the system"""
    gap_id: str
    component_name: str
    gap_type: GapType
    severity: GapSeverity
    title: str
    description: str
    current_state: str
    expected_state: str
    impact_description: str
    effort_estimate_hours: int
    category: ComponentCategory
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    identified_date: datetime = field(default_factory=datetime.now)
    
    def to_gap_model(self) -> Gap:
        """Convert to Gap model for compatibility"""
        impact_mapping = {
            GapSeverity.CRITICAL: ImpactLevel.CRITICAL,
            GapSeverity.HIGH: ImpactLevel.HIGH,
            GapSeverity.MEDIUM: ImpactLevel.MEDIUM,
            GapSeverity.LOW: ImpactLevel.LOW
        }
        
        priority_mapping = {
            GapSeverity.CRITICAL: Priority.CRITICAL,
            GapSeverity.HIGH: Priority.HIGH,
            GapSeverity.MEDIUM: Priority.MEDIUM,
            GapSeverity.LOW: Priority.LOW
        }
        
        return Gap(
            component=self.component_name,
            description=self.description,
            impact=impact_mapping[self.severity],
            effort_estimate=self.effort_estimate_hours,
            dependencies=self.dependencies,
            acceptance_criteria=self.acceptance_criteria,
            category=self.category,
            priority=priority_mapping[self.severity]
        )


@dataclass
class GapAnalysisResult:
    """Results from gap analysis"""
    identified_gaps: List[IdentifiedGap] = field(default_factory=list)
    gap_summary: Dict[str, int] = field(default_factory=dict)
    critical_gaps: List[IdentifiedGap] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)
    incomplete_implementations: List[str] = field(default_factory=list)
    configuration_gaps: List[IdentifiedGap] = field(default_factory=list)
    total_effort_estimate: int = 0
    completion_blockers: List[IdentifiedGap] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class GapAnalyzer:
    """
    Analyzes gaps between current system state and completion criteria.
    
    Identifies missing components, incomplete implementations, configuration gaps,
    and other issues that prevent the Phoenix Hydra system from reaching 100% completion.
    """
    
    def __init__(self, project_root: str = "."):
        """Initialize gap analyzer"""
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        
        # Define expected components for Phoenix Hydra
        self.expected_components = self._define_expected_components()
        
        # Define completion criteria by category
        self.completion_criteria = self._define_completion_criteria()
        
        # Define critical thresholds
        self.critical_thresholds = self._define_critical_thresholds()
    
    def identify_gaps(self, 
                     component_evaluations: List[ComponentEvaluation],
                     quality_assessments: List[QualityAssessmentResult],
                     dependency_analysis: DependencyAnalysisResult,
                     discovered_components: List[Component]) -> GapAnalysisResult:
        """
        Identify all gaps in the Phoenix Hydra system.
        
        Args:
            component_evaluations: Results from component evaluation
            quality_assessments: Results from quality assessment
            dependency_analysis: Results from dependency analysis
            discovered_components: List of discovered components
            
        Returns:
            GapAnalysisResult with identified gaps and analysis
        """
        try:
            identified_gaps = []
            
            # 1. Identify missing components
            missing_component_gaps = self._identify_missing_components(discovered_components)
            identified_gaps.extend(missing_component_gaps)
            
            # 2. Identify incomplete implementations
            incomplete_impl_gaps = self._identify_incomplete_implementations(component_evaluations)
            identified_gaps.extend(incomplete_impl_gaps)
            
            # 3. Identify configuration gaps
            config_gaps = self._identify_configuration_gaps(component_evaluations, discovered_components)
            identified_gaps.extend(config_gaps)
            
            # 4. Identify dependency gaps
            dependency_gaps = self._identify_dependency_gaps(dependency_analysis)
            identified_gaps.extend(dependency_gaps)
            
            # 5. Identify quality gaps
            quality_gaps = self._identify_quality_gaps(quality_assessments)
            identified_gaps.extend(quality_gaps)
            
            # 6. Identify integration gaps
            integration_gaps = self._identify_integration_gaps(component_evaluations, dependency_analysis)
            identified_gaps.extend(integration_gaps)
            
            # 7. Identify documentation gaps
            documentation_gaps = self._identify_documentation_gaps(discovered_components)
            identified_gaps.extend(documentation_gaps)
            
            # 8. Identify testing gaps
            testing_gaps = self._identify_testing_gaps(discovered_components, quality_assessments)
            identified_gaps.extend(testing_gaps)
            
            # 9. Identify security gaps
            security_gaps = self._identify_security_gaps(discovered_components, component_evaluations)
            identified_gaps.extend(security_gaps)
            
            # Generate analysis results
            return self._generate_gap_analysis_result(identified_gaps)
            
        except Exception as e:
            self.logger.error(f"Error identifying gaps: {e}")
            return GapAnalysisResult()
    
    def _identify_missing_components(self, discovered_components: List[Component]) -> List[IdentifiedGap]:
        """Identify missing components that should exist in Phoenix Hydra"""
        gaps = []
        discovered_names = {comp.name.lower() for comp in discovered_components}
        
        for category, expected_comps in self.expected_components.items():
            for comp_name, comp_info in expected_comps.items():
                if comp_name.lower() not in discovered_names:
                    gap = IdentifiedGap(
                        gap_id=f"missing_{comp_name}",
                        component_name=comp_name,
                        gap_type=GapType.MISSING_COMPONENT,
                        severity=comp_info.get("severity", GapSeverity.MEDIUM),
                        title=f"Missing {comp_name} component",
                        description=f"The {comp_name} component is expected but not found in the system",
                        current_state="Component not found",
                        expected_state=comp_info.get("description", f"{comp_name} component should exist"),
                        impact_description=comp_info.get("impact", f"Missing {comp_name} affects system functionality"),
                        effort_estimate_hours=comp_info.get("effort_hours", 40),
                        category=category,
                        acceptance_criteria=comp_info.get("acceptance_criteria", []),
                        recommendations=[f"Implement {comp_name} component", f"Follow Phoenix Hydra architecture patterns"]
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _identify_incomplete_implementations(self, component_evaluations: List[ComponentEvaluation]) -> List[IdentifiedGap]:
        """Identify components with incomplete implementations"""
        gaps = []
        
        for evaluation in component_evaluations:
            component = evaluation.component
            
            # Check if component is significantly incomplete
            if evaluation.completion_percentage < self.critical_thresholds["minimum_completion"]:
                severity = self._determine_severity_from_completion(evaluation.completion_percentage)
                
                gap = IdentifiedGap(
                    gap_id=f"incomplete_{component.name}",
                    component_name=component.name,
                    gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                    severity=severity,
                    title=f"Incomplete implementation: {component.name}",
                    description=f"{component.name} is only {evaluation.completion_percentage:.1f}% complete",
                    current_state=f"Component at {evaluation.completion_percentage:.1f}% completion",
                    expected_state="Component should be at least 90% complete for production",
                    impact_description=f"Incomplete {component.name} may cause system instability",
                    effort_estimate_hours=self._estimate_completion_effort(evaluation),
                    category=component.category,
                    acceptance_criteria=self._generate_completion_criteria(evaluation),
                    recommendations=self._generate_completion_recommendations(evaluation)
                )
                gaps.append(gap)
            
            # Check for failed critical criteria
            if not evaluation.critical_criteria_passed:
                gap = IdentifiedGap(
                    gap_id=f"critical_criteria_{component.name}",
                    component_name=component.name,
                    gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                    severity=GapSeverity.CRITICAL,
                    title=f"Critical criteria failed: {component.name}",
                    description=f"{component.name} failed critical evaluation criteria",
                    current_state="Critical criteria not met",
                    expected_state="All critical criteria must pass",
                    impact_description="Failed critical criteria block production deployment",
                    effort_estimate_hours=self._estimate_critical_criteria_effort(evaluation),
                    category=component.category,
                    acceptance_criteria=["All critical criteria must pass evaluation"],
                    recommendations=["Address failed critical criteria immediately", "Review component architecture"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_configuration_gaps(self, 
                                   component_evaluations: List[ComponentEvaluation],
                                   discovered_components: List[Component]) -> List[IdentifiedGap]:
        """Identify configuration gaps in components"""
        gaps = []
        
        for component in discovered_components:
            # Check for missing configuration files
            config_gaps = self._check_configuration_completeness(component)
            gaps.extend(config_gaps)
            
            # Check for invalid configurations
            validation_gaps = self._check_configuration_validity(component)
            gaps.extend(validation_gaps)
        
        return gaps
    
    def _identify_dependency_gaps(self, dependency_analysis: DependencyAnalysisResult) -> List[IdentifiedGap]:
        """Identify dependency-related gaps"""
        gaps = []
        
        # Missing dependencies
        for missing_dep in dependency_analysis.missing_dependencies:
            gap = IdentifiedGap(
                gap_id=f"missing_dep_{missing_dep.source}_{missing_dep.target}",
                component_name=missing_dep.source,
                gap_type=GapType.DEPENDENCY_GAP,
                severity=GapSeverity.HIGH if missing_dep.dependency_type.value == "required" else GapSeverity.MEDIUM,
                title=f"Missing dependency: {missing_dep.target}",
                description=f"{missing_dep.source} requires {missing_dep.target} but it's not available",
                current_state=f"Dependency {missing_dep.target} is missing",
                expected_state=f"Dependency {missing_dep.target} should be available and functional",
                impact_description=f"Missing dependency affects {missing_dep.source} functionality",
                effort_estimate_hours=24,
                category=ComponentCategory.INFRASTRUCTURE,
                dependencies=[missing_dep.target],
                acceptance_criteria=[f"{missing_dep.target} is available and functional"],
                recommendations=[f"Install or implement {missing_dep.target}", "Verify dependency configuration"]
            )
            gaps.append(gap)
        
        # Circular dependencies
        for circular_deps in dependency_analysis.circular_dependencies:
            if len(circular_deps) > 1:
                gap = IdentifiedGap(
                    gap_id=f"circular_dep_{'_'.join(circular_deps)}",
                    component_name=circular_deps[0],
                    gap_type=GapType.DEPENDENCY_GAP,
                    severity=GapSeverity.HIGH,
                    title=f"Circular dependency: {' -> '.join(circular_deps)}",
                    description=f"Circular dependency detected between: {', '.join(circular_deps)}",
                    current_state="Components have circular dependencies",
                    expected_state="Dependencies should form a directed acyclic graph",
                    impact_description="Circular dependencies can cause initialization and update issues",
                    effort_estimate_hours=32,
                    category=ComponentCategory.INFRASTRUCTURE,
                    dependencies=circular_deps,
                    acceptance_criteria=["Remove circular dependencies", "Refactor component relationships"],
                    recommendations=["Refactor component architecture", "Introduce dependency injection", "Break circular references"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_quality_gaps(self, quality_assessments: List[QualityAssessmentResult]) -> List[IdentifiedGap]:
        """Identify quality-related gaps"""
        gaps = []
        
        for assessment in quality_assessments:
            if assessment.quality_level in [QualityLevel.POOR, QualityLevel.FAIR]:
                severity = GapSeverity.HIGH if assessment.quality_level == QualityLevel.POOR else GapSeverity.MEDIUM
                
                gap = IdentifiedGap(
                    gap_id=f"quality_{assessment.component.name}",
                    component_name=assessment.component.name,
                    gap_type=GapType.QUALITY_GAP,
                    severity=severity,
                    title=f"Quality issues: {assessment.component.name}",
                    description=f"{assessment.component.name} has {assessment.quality_level.value} code quality",
                    current_state=f"Code quality: {assessment.quality_level.value}",
                    expected_state="Code quality should be Good or Excellent",
                    impact_description="Poor code quality affects maintainability and reliability",
                    effort_estimate_hours=self._estimate_quality_improvement_effort(assessment),
                    category=assessment.component.category,
                    acceptance_criteria=["Code quality reaches Good or Excellent level", "All quality checks pass"],
                    recommendations=self._generate_quality_recommendations(assessment)
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_integration_gaps(self, 
                                 component_evaluations: List[ComponentEvaluation],
                                 dependency_analysis: DependencyAnalysisResult) -> List[IdentifiedGap]:
        """Identify integration gaps between components"""
        gaps = []
        
        # Check for components with low dependency health scores
        for comp_name, score in dependency_analysis.component_dependency_scores.items():
            if score < 0.7:  # Below acceptable threshold
                gap = IdentifiedGap(
                    gap_id=f"integration_{comp_name}",
                    component_name=comp_name,
                    gap_type=GapType.INTEGRATION_GAP,
                    severity=GapSeverity.MEDIUM,
                    title=f"Integration issues: {comp_name}",
                    description=f"{comp_name} has poor integration health (score: {score:.2f})",
                    current_state=f"Integration health score: {score:.2f}",
                    expected_state="Integration health score should be above 0.8",
                    impact_description="Poor integration affects system reliability and performance",
                    effort_estimate_hours=16,
                    category=ComponentCategory.INFRASTRUCTURE,
                    acceptance_criteria=["Integration health score above 0.8", "All integration tests pass"],
                    recommendations=["Review component interfaces", "Improve error handling", "Add integration tests"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_documentation_gaps(self, discovered_components: List[Component]) -> List[IdentifiedGap]:
        """Identify documentation gaps"""
        gaps = []
        
        for component in discovered_components:
            # Check for missing README files
            readme_path = self.project_root / component.path / "README.md"
            if not readme_path.exists():
                gap = IdentifiedGap(
                    gap_id=f"doc_readme_{component.name}",
                    component_name=component.name,
                    gap_type=GapType.DOCUMENTATION_GAP,
                    severity=GapSeverity.LOW,
                    title=f"Missing README: {component.name}",
                    description=f"{component.name} lacks README documentation",
                    current_state="No README file found",
                    expected_state="Component should have comprehensive README documentation",
                    impact_description="Missing documentation affects developer onboarding and maintenance",
                    effort_estimate_hours=4,
                    category=component.category,
                    related_files=[str(readme_path)],
                    acceptance_criteria=["README.md file exists", "Documentation covers component purpose and usage"],
                    recommendations=["Create comprehensive README.md", "Document API endpoints and configuration"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_testing_gaps(self, 
                             discovered_components: List[Component],
                             quality_assessments: List[QualityAssessmentResult]) -> List[IdentifiedGap]:
        """Identify testing gaps"""
        gaps = []
        
        # Create quality assessment lookup
        quality_lookup = {qa.component.name: qa for qa in quality_assessments}
        
        for component in discovered_components:
            quality_assessment = quality_lookup.get(component.name)
            
            # Check test coverage
            if quality_assessment and hasattr(quality_assessment, 'test_coverage'):
                if quality_assessment.test_coverage < 70:  # Below acceptable threshold
                    gap = IdentifiedGap(
                        gap_id=f"test_coverage_{component.name}",
                        component_name=component.name,
                        gap_type=GapType.TESTING_GAP,
                        severity=GapSeverity.MEDIUM,
                        title=f"Low test coverage: {component.name}",
                        description=f"{component.name} has {quality_assessment.test_coverage}% test coverage",
                        current_state=f"Test coverage: {quality_assessment.test_coverage}%",
                        expected_state="Test coverage should be at least 80%",
                        impact_description="Low test coverage increases risk of bugs and regressions",
                        effort_estimate_hours=self._estimate_testing_effort(quality_assessment.test_coverage),
                        category=component.category,
                        acceptance_criteria=["Test coverage above 80%", "All critical paths tested"],
                        recommendations=["Add unit tests for core functionality", "Implement integration tests", "Add edge case testing"]
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _identify_security_gaps(self, 
                              discovered_components: List[Component],
                              component_evaluations: List[ComponentEvaluation]) -> List[IdentifiedGap]:
        """Identify security gaps"""
        gaps = []
        
        # Check for security-critical components
        security_components = [comp for comp in discovered_components 
                             if any(keyword in comp.name.lower() 
                                   for keyword in ['auth', 'security', 'api', 'database'])]
        
        for component in security_components:
            # Check for security configuration
            if not self._has_security_configuration(component):
                gap = IdentifiedGap(
                    gap_id=f"security_config_{component.name}",
                    component_name=component.name,
                    gap_type=GapType.SECURITY_GAP,
                    severity=GapSeverity.HIGH,
                    title=f"Missing security configuration: {component.name}",
                    description=f"{component.name} lacks proper security configuration",
                    current_state="Security configuration missing or incomplete",
                    expected_state="Component should have comprehensive security configuration",
                    impact_description="Missing security configuration creates vulnerabilities",
                    effort_estimate_hours=16,
                    category=ComponentCategory.SECURITY,
                    acceptance_criteria=["Security configuration implemented", "Security audit passes"],
                    recommendations=["Implement authentication and authorization", "Add input validation", "Configure secure communication"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _generate_gap_analysis_result(self, identified_gaps: List[IdentifiedGap]) -> GapAnalysisResult:
        """Generate comprehensive gap analysis result"""
        # Categorize gaps
        critical_gaps = [gap for gap in identified_gaps if gap.severity == GapSeverity.CRITICAL]
        missing_components = [gap.component_name for gap in identified_gaps if gap.gap_type == GapType.MISSING_COMPONENT]
        incomplete_implementations = [gap.component_name for gap in identified_gaps if gap.gap_type == GapType.INCOMPLETE_IMPLEMENTATION]
        configuration_gaps = [gap for gap in identified_gaps if gap.gap_type == GapType.CONFIGURATION_GAP]
        
        # Calculate summary statistics
        gap_summary = {}
        for gap_type in GapType:
            gap_summary[gap_type.value] = len([gap for gap in identified_gaps if gap.gap_type == gap_type])
        
        # Calculate total effort
        total_effort = sum(gap.effort_estimate_hours for gap in identified_gaps)
        
        # Identify completion blockers (critical and high severity gaps)
        completion_blockers = [gap for gap in identified_gaps 
                             if gap.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]]
        
        # Generate recommendations
        recommendations = self._generate_gap_recommendations(identified_gaps, critical_gaps, completion_blockers)
        
        return GapAnalysisResult(
            identified_gaps=identified_gaps,
            gap_summary=gap_summary,
            critical_gaps=critical_gaps,
            missing_components=missing_components,
            incomplete_implementations=incomplete_implementations,
            configuration_gaps=configuration_gaps,
            total_effort_estimate=total_effort,
            completion_blockers=completion_blockers,
            recommendations=recommendations
        )
    
    # Helper methods
    def _define_expected_components(self) -> Dict[ComponentCategory, Dict[str, Dict[str, Any]]]:
        """Define expected components for Phoenix Hydra system"""
        return {
            ComponentCategory.INFRASTRUCTURE: {
                "nca_toolkit": {
                    "description": "NCA Toolkit API with 30+ multimedia processing endpoints",
                    "severity": GapSeverity.CRITICAL,
                    "effort_hours": 80,
                    "impact": "Core multimedia processing functionality",
                    "acceptance_criteria": ["API endpoints operational", "Health checks passing", "Documentation complete"]
                },
                "podman_stack": {
                    "description": "Podman container orchestration with compose files",
                    "severity": GapSeverity.CRITICAL,
                    "effort_hours": 40,
                    "impact": "Container deployment and management",
                    "acceptance_criteria": ["Compose files configured", "Services deployable", "Health monitoring active"]
                },
                "database": {
                    "description": "PostgreSQL database with schema and migrations",
                    "severity": GapSeverity.CRITICAL,
                    "effort_hours": 32,
                    "impact": "Data persistence and revenue tracking",
                    "acceptance_criteria": ["Database schema deployed", "Migrations working", "Backup strategy implemented"]
                },
                "minio_storage": {
                    "description": "Minio S3 storage for multimedia assets",
                    "severity": GapSeverity.HIGH,
                    "effort_hours": 24,
                    "impact": "Multimedia asset storage and retrieval",
                    "acceptance_criteria": ["Storage configured", "Access policies set", "Monitoring enabled"]
                }
            },
            ComponentCategory.MONETIZATION: {
                "revenue_tracking": {
                    "description": "Revenue tracking and metrics collection system",
                    "severity": GapSeverity.CRITICAL,
                    "effort_hours": 48,
                    "impact": "Business metrics and revenue optimization",
                    "acceptance_criteria": ["Tracking implemented", "Metrics collected", "Reporting functional"]
                },
                "affiliate_system": {
                    "description": "Affiliate program management and tracking",
                    "severity": GapSeverity.HIGH,
                    "effort_hours": 40,
                    "impact": "Revenue generation through partnerships",
                    "acceptance_criteria": ["Affiliate tracking active", "Badge deployment working", "Revenue attribution accurate"]
                },
                "grant_tracking": {
                    "description": "Grant application and tracking system",
                    "severity": GapSeverity.MEDIUM,
                    "effort_hours": 32,
                    "impact": "Funding acquisition and compliance",
                    "acceptance_criteria": ["Application generators working", "Tracking system operational", "Documentation complete"]
                }
            },
            ComponentCategory.AUTOMATION: {
                "deployment_scripts": {
                    "description": "Automated deployment scripts for Windows and Linux",
                    "severity": GapSeverity.HIGH,
                    "effort_hours": 24,
                    "impact": "Deployment automation and reliability",
                    "acceptance_criteria": ["Scripts functional", "Cross-platform support", "Error handling implemented"]
                },
                "agent_hooks": {
                    "description": "Kiro agent hooks for automation",
                    "severity": GapSeverity.MEDIUM,
                    "effort_hours": 16,
                    "impact": "Development workflow automation",
                    "acceptance_criteria": ["Hooks configured", "Event handling working", "Integration tested"]
                }
            }
        }
    
    def _define_completion_criteria(self) -> Dict[ComponentCategory, Dict[str, Any]]:
        """Define completion criteria by category"""
        return {
            ComponentCategory.INFRASTRUCTURE: {
                "minimum_completion": 95.0,
                "required_features": ["health_checks", "monitoring", "backup_strategy"],
                "critical_thresholds": {"availability": 99.0, "performance": 90.0}
            },
            ComponentCategory.MONETIZATION: {
                "minimum_completion": 90.0,
                "required_features": ["tracking", "reporting", "automation"],
                "critical_thresholds": {"accuracy": 99.5, "real_time": 95.0}
            },
            ComponentCategory.AUTOMATION: {
                "minimum_completion": 80.0,
                "required_features": ["error_handling", "logging", "monitoring"],
                "critical_thresholds": {"reliability": 95.0, "performance": 85.0}
            }
        }
    
    def _define_critical_thresholds(self) -> Dict[str, float]:
        """Define critical thresholds for gap identification"""
        return {
            "minimum_completion": 70.0,
            "critical_completion": 90.0,
            "quality_threshold": 0.7,
            "test_coverage_threshold": 70.0,
            "dependency_health_threshold": 0.7
        }
    
    def _determine_severity_from_completion(self, completion_percentage: float) -> GapSeverity:
        """Determine gap severity based on completion percentage"""
        if completion_percentage < 30:
            return GapSeverity.CRITICAL
        elif completion_percentage < 50:
            return GapSeverity.HIGH
        elif completion_percentage < 70:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _estimate_completion_effort(self, evaluation: ComponentEvaluation) -> int:
        """Estimate effort needed to complete component"""
        remaining_percentage = 100 - evaluation.completion_percentage
        base_effort = int(remaining_percentage * 2)  # 2 hours per percentage point
        
        # Adjust based on component complexity
        complexity_multiplier = 1.0
        if evaluation.component.category == ComponentCategory.INFRASTRUCTURE:
            complexity_multiplier = 1.5
        elif evaluation.component.category == ComponentCategory.MONETIZATION:
            complexity_multiplier = 1.3
        
        return max(8, int(base_effort * complexity_multiplier))
    
    def _estimate_critical_criteria_effort(self, evaluation: ComponentEvaluation) -> int:
        """Estimate effort to fix critical criteria failures"""
        failed_critical = len([ce for ce in evaluation.criterion_evaluations 
                             if ce.required and ce.status != EvaluationStatus.PASSED])
        return max(16, failed_critical * 8)
    
    def _estimate_quality_improvement_effort(self, assessment: QualityAssessmentResult) -> int:
        """Estimate effort to improve code quality"""
        if assessment.quality_level == QualityLevel.POOR:
            return 32
        elif assessment.quality_level == QualityLevel.FAIR:
            return 16
        else:
            return 8
    
    def _estimate_testing_effort(self, current_coverage: float) -> int:
        """Estimate effort to improve test coverage"""
        target_coverage = 80.0
        coverage_gap = target_coverage - current_coverage
        return max(8, int(coverage_gap * 0.5))  # 0.5 hours per percentage point
    
    def _generate_completion_criteria(self, evaluation: ComponentEvaluation) -> List[str]:
        """Generate acceptance criteria for completing component"""
        criteria = []
        
        if evaluation.completion_percentage < 90:
            criteria.append("Component completion reaches at least 90%")
        
        if not evaluation.critical_criteria_passed:
            criteria.append("All critical evaluation criteria pass")
        
        if not evaluation.meets_minimum_score:
            criteria.append("Component meets minimum quality score")
        
        criteria.extend([
            "All unit tests pass",
            "Integration tests implemented and passing",
            "Documentation updated and complete"
        ])
        
        return criteria
    
    def _generate_completion_recommendations(self, evaluation: ComponentEvaluation) -> List[str]:
        """Generate recommendations for completing component"""
        recommendations = []
        
        if evaluation.completion_percentage < 50:
            recommendations.append("Focus on core functionality implementation")
        
        if not evaluation.critical_criteria_passed:
            recommendations.append("Address critical criteria failures immediately")
        
        if len(evaluation.issues) > 0:
            recommendations.append("Resolve identified issues and warnings")
        
        recommendations.extend([
            "Add comprehensive unit tests",
            "Implement error handling and logging",
            "Update documentation and examples"
        ])
        
        return recommendations
    
    def _generate_quality_recommendations(self, assessment: QualityAssessmentResult) -> List[str]:
        """Generate recommendations for improving code quality"""
        recommendations = []
        
        if assessment.quality_level == QualityLevel.POOR:
            recommendations.extend([
                "Refactor code to improve readability",
                "Add proper error handling",
                "Implement comprehensive logging",
                "Add type hints and documentation"
            ])
        elif assessment.quality_level == QualityLevel.FAIR:
            recommendations.extend([
                "Improve code organization and structure",
                "Add more comprehensive tests",
                "Enhance error handling"
            ])
        
        recommendations.extend([
            "Run code quality tools (black, ruff, mypy)",
            "Add pre-commit hooks for quality checks",
            "Implement code review process"
        ])
        
        return recommendations
    
    def _generate_gap_recommendations(self, 
                                    identified_gaps: List[IdentifiedGap],
                                    critical_gaps: List[IdentifiedGap],
                                    completion_blockers: List[IdentifiedGap]) -> List[str]:
        """Generate overall recommendations based on identified gaps"""
        recommendations = []
        
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical gaps immediately - these block production deployment")
        
        if completion_blockers:
            recommendations.append(f"Focus on {len(completion_blockers)} completion blockers to reach 100% system completion")
        
        # Category-specific recommendations
        gap_by_category = {}
        for gap in identified_gaps:
            if gap.category not in gap_by_category:
                gap_by_category[gap.category] = []
            gap_by_category[gap.category].append(gap)
        
        for category, gaps in gap_by_category.items():
            if len(gaps) > 3:
                recommendations.append(f"Prioritize {category.value} improvements - {len(gaps)} gaps identified")
        
        # Effort-based recommendations
        total_effort = sum(gap.effort_estimate_hours for gap in identified_gaps)
        if total_effort > 200:
            recommendations.append(f"Plan for {total_effort} hours of development effort across all gaps")
        
        return recommendations
    
    def _check_configuration_completeness(self, component: Component) -> List[IdentifiedGap]:
        """Check if component has complete configuration"""
        gaps = []
        
        # Check for expected configuration files based on component type
        expected_configs = self._get_expected_config_files(component)
        
        for config_file, config_info in expected_configs.items():
            config_path = self.project_root / component.path / config_file
            if not config_path.exists():
                gap = IdentifiedGap(
                    gap_id=f"config_{component.name}_{config_file}",
                    component_name=component.name,
                    gap_type=GapType.CONFIGURATION_GAP,
                    severity=config_info.get("severity", GapSeverity.MEDIUM),
                    title=f"Missing configuration: {config_file}",
                    description=f"{component.name} is missing {config_file} configuration",
                    current_state=f"Configuration file {config_file} not found",
                    expected_state=f"Configuration file {config_file} should exist and be properly configured",
                    impact_description=config_info.get("impact", f"Missing {config_file} affects component functionality"),
                    effort_estimate_hours=config_info.get("effort_hours", 4),
                    category=component.category,
                    related_files=[str(config_path)],
                    acceptance_criteria=[f"{config_file} exists and is valid"],
                    recommendations=[f"Create {config_file} configuration", "Follow Phoenix Hydra configuration standards"]
                )
                gaps.append(gap)
        
        return gaps
    
    def _check_configuration_validity(self, component: Component) -> List[IdentifiedGap]:
        """Check if component configurations are valid"""
        gaps = []
        
        # This would implement actual configuration validation
        # For now, return empty list as placeholder
        
        return gaps
    
    def _get_expected_config_files(self, component: Component) -> Dict[str, Dict[str, Any]]:
        """Get expected configuration files for a component"""
        config_files = {}
        
        # Infrastructure components
        if component.category == ComponentCategory.INFRASTRUCTURE:
            if "podman" in component.name.lower():
                config_files["compose.yaml"] = {
                    "severity": GapSeverity.CRITICAL,
                    "effort_hours": 8,
                    "impact": "Container orchestration requires compose configuration"
                }
            elif "database" in component.name.lower():
                config_files["schema.sql"] = {
                    "severity": GapSeverity.HIGH,
                    "effort_hours": 16,
                    "impact": "Database requires schema definition"
                }
        
        # Monetization components
        elif component.category == ComponentCategory.MONETIZATION:
            config_files["config.json"] = {
                "severity": GapSeverity.HIGH,
                "effort_hours": 4,
                "impact": "Monetization components require configuration"
            }
        
        return config_files
    
    def _has_security_configuration(self, component: Component) -> bool:
        """Check if component has security configuration"""
        # This would implement actual security configuration checking
        # For now, return False as placeholder to identify security gaps
        return False