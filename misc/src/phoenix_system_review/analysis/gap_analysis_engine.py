"""
Gap Analysis Engine for Phoenix Hydra System Review Tool

Identifies missing components, incomplete implementations, and prioritizes
improvements based on Phoenix Hydra requirements and business objectives.
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

from ..models.data_models import Component, ComponentCategory, ComponentStatus, Priority
from .component_evaluator import ComponentEvaluation, EvaluationStatus
from .dependency_analyzer import DependencyAnalysisResult, DependencyStatus
from .quality_assessor import QualityAssessmentResult, QualityLevel


class GapType(Enum):
    """Types of gaps that can be identified"""
    MISSING_COMPONENT = "missing_component"
    INCOMPLETE_IMPLEMENTATION = "incomplete_implementation"
    QUALITY_GAP = "quality_gap"
    DEPENDENCY_GAP = "dependency_gap"
    DOCUMENTATION_GAP = "documentation_gap"
    TEST_COVERAGE_GAP = "test_coverage_gap"
    CONFIGURATION_GAP = "configuration_gap"


class GapSeverity(Enum):
    """Severity levels for identified gaps"""
    CRITICAL = "critical"    # Blocks core functionality
    HIGH = "high"           # Significantly impacts functionality
    MEDIUM = "medium"       # Moderate impact on functionality
    LOW = "low"             # Minor impact or nice-to-have


class ImprovementCategory(Enum):
    """Categories for improvement recommendations"""
    INFRASTRUCTURE = "infrastructure"
    MONETIZATION = "monetization"
    AUTOMATION = "automation"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


@dataclass
class Gap:
    """Represents an identified gap in the system"""
    id: str
    gap_type: GapType
    severity: GapSeverity
    category: ImprovementCategory
    title: str
    description: str
    affected_components: List[str] = field(default_factory=list)
    impact_description: str = ""
    estimated_effort: str = ""  # e.g., "1-2 days", "1 week", "1 month"
    business_value: str = ""    # Business justification
    prerequisites: List[str] = field(default_factory=list)
    related_gaps: List[str] = field(default_factory=list)


@dataclass
class ImprovementRecommendation:
    """Represents a prioritized improvement recommendation"""
    id: str
    title: str
    description: str
    category: ImprovementCategory
    priority_score: float  # 0.0 to 1.0
    estimated_effort: str
    business_value: str
    implementation_steps: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    related_gaps: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class GapAnalysisResult:
    """Results from gap analysis"""
    identified_gaps: List[Gap] = field(default_factory=list)
    improvement_recommendations: List[ImprovementRecommendation] = field(default_factory=list)
    gap_summary: Dict[str, int] = field(default_factory=dict)
    priority_matrix: Dict[str, List[Gap]] = field(default_factory=dict)
    implementation_roadmap: List[Dict[str, Any]] = field(default_factory=list)
    overall_completeness: float = 0.0
    analysis_timestamp: str = ""


class GapAnalysisEngine:
    """
    Analyzes system gaps and generates prioritized improvement recommendations.
    
    Combines results from component evaluation, dependency analysis, and quality
    assessment to identify missing components, incomplete implementations, and
    areas for improvement.
    """
    
    def __init__(self):
        """Initialize gap analysis engine"""
        self.logger = logging.getLogger(__name__)
        
        # Phoenix Hydra specific requirements
        self.required_components = self._define_required_components()
        self.quality_standards = self._define_quality_standards()
        self.business_priorities = self._define_business_priorities()
    
    def analyze_gaps(self, 
                    component_evaluations: List[ComponentEvaluation],
                    dependency_analysis: DependencyAnalysisResult,
                    quality_assessments: List[QualityAssessmentResult]) -> GapAnalysisResult:
        """
        Perform comprehensive gap analysis.
        
        Args:
            component_evaluations: Results from component evaluation
            dependency_analysis: Results from dependency analysis
            quality_assessments: Results from quality assessment
            
        Returns:
            GapAnalysisResult with identified gaps and recommendations
        """
        try:
            # Identify different types of gaps
            missing_component_gaps = self._identify_missing_components(component_evaluations)
            implementation_gaps = self._identify_implementation_gaps(component_evaluations)
            quality_gaps = self._identify_quality_gaps(quality_assessments)
            dependency_gaps = self._identify_dependency_gaps(dependency_analysis)
            documentation_gaps = self._identify_documentation_gaps(quality_assessments)
            test_coverage_gaps = self._identify_test_coverage_gaps(quality_assessments)
            
            # Combine all gaps
            all_gaps = (
                missing_component_gaps + implementation_gaps + quality_gaps +
                dependency_gaps + documentation_gaps + test_coverage_gaps
            )
            
            # Generate improvement recommendations
            recommendations = self._generate_improvement_recommendations(all_gaps)
            
            # Create gap summary
            gap_summary = self._create_gap_summary(all_gaps)
            
            # Create priority matrix
            priority_matrix = self._create_priority_matrix(all_gaps)
            
            # Generate implementation roadmap
            roadmap = self._generate_implementation_roadmap(recommendations)
            
            # Calculate overall completeness
            completeness = self._calculate_overall_completeness(
                component_evaluations, dependency_analysis, quality_assessments
            )
            
            return GapAnalysisResult(
                identified_gaps=all_gaps,
                improvement_recommendations=recommendations,
                gap_summary=gap_summary,
                priority_matrix=priority_matrix,
                implementation_roadmap=roadmap,
                overall_completeness=completeness,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error performing gap analysis: {e}")
            return GapAnalysisResult(
                analysis_timestamp=datetime.now().isoformat()
            )
    
    def _identify_missing_components(self, evaluations: List[ComponentEvaluation]) -> List[Gap]:
        """Identify missing required components"""
        gaps = []
        
        # Get list of existing components
        existing_components = {eval.component.name.lower() for eval in evaluations}
        
        # Check for missing required components
        for category, required_comps in self.required_components.items():
            for comp_name, comp_info in required_comps.items():
                if comp_name.lower() not in existing_components:
                    gap = Gap(
                        id=f"missing_{comp_name.lower().replace(' ', '_')}",
                        gap_type=GapType.MISSING_COMPONENT,
                        severity=GapSeverity(comp_info.get('severity', 'medium')),
                        category=ImprovementCategory(category),
                        title=f"Missing {comp_name}",
                        description=comp_info.get('description', f"{comp_name} is required but not found"),
                        impact_description=comp_info.get('impact', "May impact system functionality"),
                        estimated_effort=comp_info.get('effort', "Unknown"),
                        business_value=comp_info.get('business_value', "Required for system completeness")
                    )
                    gaps.append(gap)
        
        return gaps
    
    def _identify_implementation_gaps(self, evaluations: List[ComponentEvaluation]) -> List[Gap]:
        """Identify incomplete implementations"""
        gaps = []
        
        for evaluation in evaluations:
            if evaluation.status == EvaluationStatus.FAILED:
                gap = Gap(
                    id=f"incomplete_{evaluation.component.name.lower().replace(' ', '_')}",
                    gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                    severity=self._determine_implementation_gap_severity(evaluation),
                    category=self._map_component_category_to_improvement(evaluation.component.category),
                    title=f"Incomplete Implementation: {evaluation.component.name}",
                    description=f"Component {evaluation.component.name} failed evaluation criteria",
                    affected_components=[evaluation.component.name],
                    impact_description=f"Component completion: {evaluation.completion_percentage:.1f}%",
                    estimated_effort=self._estimate_implementation_effort(evaluation),
                    business_value=self._assess_business_value(evaluation.component)
                )
                gaps.append(gap)
            
            elif evaluation.status == EvaluationStatus.WARNING and evaluation.completion_percentage < 80:
                gap = Gap(
                    id=f"partial_{evaluation.component.name.lower().replace(' ', '_')}",
                    gap_type=GapType.INCOMPLETE_IMPLEMENTATION,
                    severity=GapSeverity.MEDIUM,
                    category=self._map_component_category_to_improvement(evaluation.component.category),
                    title=f"Partial Implementation: {evaluation.component.name}",
                    description=f"Component {evaluation.component.name} needs improvement",
                    affected_components=[evaluation.component.name],
                    impact_description=f"Component completion: {evaluation.completion_percentage:.1f}%",
                    estimated_effort=self._estimate_improvement_effort(evaluation),
                    business_value=self._assess_business_value(evaluation.component)
                )
                gaps.append(gap)
        
        return gaps    
    
def _identify_quality_gaps(self, quality_assessments: List[QualityAssessmentResult]) -> List[Gap]:
        """Identify quality-related gaps"""
        gaps = []
        
        for assessment in quality_assessments:
            if assessment.quality_level in [QualityLevel.POOR, QualityLevel.FAIR]:
                gap = Gap(
                    id=f"quality_{assessment.component.name.lower().replace(' ', '_')}",
                    gap_type=GapType.QUALITY_GAP,
                    severity=GapSeverity.HIGH if assessment.quality_level == QualityLevel.POOR else GapSeverity.MEDIUM,
                    category=ImprovementCategory.QUALITY,
                    title=f"Quality Issues: {assessment.component.name}",
                    description=f"Component has {assessment.quality_level.value} quality level",
                    affected_components=[assessment.component.name],
                    impact_description=f"Quality score: {assessment.overall_quality_score:.2f}",
                    estimated_effort=self._estimate_quality_improvement_effort(assessment),
                    business_value="Improved code maintainability and reliability"
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_dependency_gaps(self, dependency_analysis: DependencyAnalysisResult) -> List[Gap]:
        """Identify dependency-related gaps"""
        gaps = []
        
        # Missing dependencies
        for missing_dep in dependency_analysis.missing_dependencies:
            gap = Gap(
                id=f"missing_dep_{missing_dep.target.lower().replace(' ', '_')}",
                gap_type=GapType.DEPENDENCY_GAP,
                severity=GapSeverity.HIGH if missing_dep.dependency_type.value == "required" else GapSeverity.MEDIUM,
                category=ImprovementCategory.INFRASTRUCTURE,
                title=f"Missing Dependency: {missing_dep.target}",
                description=f"Component {missing_dep.source} requires {missing_dep.target}",
                affected_components=[missing_dep.source],
                impact_description=missing_dep.description,
                estimated_effort="1-3 days",
                business_value="Ensures proper component functionality"
            )
            gaps.append(gap)
        
        # Circular dependencies
        for i, circular_dep in enumerate(dependency_analysis.circular_dependencies):
            gap = Gap(
                id=f"circular_dep_{i}",
                gap_type=GapType.DEPENDENCY_GAP,
                severity=GapSeverity.HIGH,
                category=ImprovementCategory.INFRASTRUCTURE,
                title=f"Circular Dependency: {' -> '.join(circular_dep[:3])}",
                description="Circular dependency detected in component relationships",
                affected_components=circular_dep,
                impact_description="May cause initialization or runtime issues",
                estimated_effort="2-5 days",
                business_value="Improves system architecture and reliability"
            )
            gaps.append(gap)
        
        return gaps
    
    def _identify_documentation_gaps(self, quality_assessments: List[QualityAssessmentResult]) -> List[Gap]:
        """Identify documentation gaps"""
        gaps = []
        
        for assessment in quality_assessments:
            doc_score = assessment.documentation.documentation_score
            if doc_score < 0.8:  # Less than 80% documented
                severity = GapSeverity.HIGH if doc_score < 0.5 else GapSeverity.MEDIUM
                
                gap = Gap(
                    id=f"docs_{assessment.component.name.lower().replace(' ', '_')}",
                    gap_type=GapType.DOCUMENTATION_GAP,
                    severity=severity,
                    category=ImprovementCategory.DOCUMENTATION,
                    title=f"Documentation Gap: {assessment.component.name}",
                    description=f"Component has {doc_score:.1%} documentation coverage",
                    affected_components=[assessment.component.name],
                    impact_description=f"Missing docs: {len(assessment.documentation.missing_docs)} items",
                    estimated_effort=self._estimate_documentation_effort(assessment.documentation),
                    business_value="Improves code maintainability and developer onboarding"
                )
                gaps.append(gap)
        
        return gaps
    
    def _identify_test_coverage_gaps(self, quality_assessments: List[QualityAssessmentResult]) -> List[Gap]:
        """Identify test coverage gaps"""
        gaps = []
        
        for assessment in quality_assessments:
            coverage = assessment.test_coverage.coverage_percentage
            if coverage < 80:  # Less than 80% test coverage
                severity = GapSeverity.HIGH if coverage < 50 else GapSeverity.MEDIUM
                
                gap = Gap(
                    id=f"tests_{assessment.component.name.lower().replace(' ', '_')}",
                    gap_type=GapType.TEST_COVERAGE_GAP,
                    severity=severity,
                    category=ImprovementCategory.TESTING,
                    title=f"Test Coverage Gap: {assessment.component.name}",
                    description=f"Component has {coverage:.1f}% test coverage",
                    affected_components=[assessment.component.name],
                    impact_description=f"Test files: {assessment.test_coverage.test_files_count}",
                    estimated_effort=self._estimate_testing_effort(assessment.test_coverage),
                    business_value="Reduces bugs and improves code reliability"
                )
                gaps.append(gap)
        
        return gaps
    
    def _generate_improvement_recommendations(self, gaps: List[Gap]) -> List[ImprovementRecommendation]:
        """Generate prioritized improvement recommendations from gaps"""
        recommendations = []
        
        # Group gaps by category and severity
        gap_groups = self._group_gaps_by_priority(gaps)
        
        for category, category_gaps in gap_groups.items():
            if not category_gaps:
                continue
            
            # Create recommendation for this category
            rec = ImprovementRecommendation(
                id=f"improve_{category.value}",
                title=f"Improve {category.value.title()}",
                description=f"Address {len(category_gaps)} {category.value} gaps",
                category=category,
                priority_score=self._calculate_priority_score(category_gaps),
                estimated_effort=self._aggregate_effort_estimates(category_gaps),
                business_value=self._aggregate_business_value(category_gaps),
                implementation_steps=self._generate_implementation_steps(category_gaps),
                success_criteria=self._generate_success_criteria(category_gaps),
                related_gaps=[gap.id for gap in category_gaps]
            )
            recommendations.append(rec)
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        return recommendations
    
    def _create_gap_summary(self, gaps: List[Gap]) -> Dict[str, int]:
        """Create summary statistics for identified gaps"""
        summary = {
            "total_gaps": len(gaps),
            "critical_gaps": len([g for g in gaps if g.severity == GapSeverity.CRITICAL]),
            "high_gaps": len([g for g in gaps if g.severity == GapSeverity.HIGH]),
            "medium_gaps": len([g for g in gaps if g.severity == GapSeverity.MEDIUM]),
            "low_gaps": len([g for g in gaps if g.severity == GapSeverity.LOW])
        }
        
        # Add gap type breakdown
        for gap_type in GapType:
            summary[f"{gap_type.value}_count"] = len([g for g in gaps if g.gap_type == gap_type])
        
        # Add category breakdown
        for category in ImprovementCategory:
            summary[f"{category.value}_gaps"] = len([g for g in gaps if g.category == category])
        
        return summary
    
    def _create_priority_matrix(self, gaps: List[Gap]) -> Dict[str, List[Gap]]:
        """Create priority matrix organizing gaps by severity and category"""
        matrix = {}
        
        for severity in GapSeverity:
            matrix[severity.value] = [g for g in gaps if g.severity == severity]
        
        return matrix
    
    def _generate_implementation_roadmap(self, recommendations: List[ImprovementRecommendation]) -> List[Dict[str, Any]]:
        """Generate implementation roadmap with phases"""
        roadmap = []
        
        # Phase 1: Critical and High Priority (0-3 months)
        phase1_recs = [r for r in recommendations if r.priority_score >= 0.8]
        if phase1_recs:
            roadmap.append({
                "phase": "Phase 1: Critical Improvements",
                "timeline": "0-3 months",
                "focus": "Address critical gaps and high-priority improvements",
                "recommendations": [{
                    "id": r.id,
                    "title": r.title,
                    "priority_score": r.priority_score,
                    "estimated_effort": r.estimated_effort
                } for r in phase1_recs]
            })
        
        # Phase 2: Medium Priority (3-6 months)
        phase2_recs = [r for r in recommendations if 0.5 <= r.priority_score < 0.8]
        if phase2_recs:
            roadmap.append({
                "phase": "Phase 2: Quality Improvements",
                "timeline": "3-6 months",
                "focus": "Improve code quality, documentation, and testing",
                "recommendations": [{
                    "id": r.id,
                    "title": r.title,
                    "priority_score": r.priority_score,
                    "estimated_effort": r.estimated_effort
                } for r in phase2_recs]
            })
        
        # Phase 3: Low Priority (6+ months)
        phase3_recs = [r for r in recommendations if r.priority_score < 0.5]
        if phase3_recs:
            roadmap.append({
                "phase": "Phase 3: Enhancement & Optimization",
                "timeline": "6+ months",
                "focus": "Nice-to-have improvements and optimizations",
                "recommendations": [{
                    "id": r.id,
                    "title": r.title,
                    "priority_score": r.priority_score,
                    "estimated_effort": r.estimated_effort
                } for r in phase3_recs]
            })
        
        return roadmap
    
    def _calculate_overall_completeness(self, 
                                      component_evaluations: List[ComponentEvaluation],
                                      dependency_analysis: DependencyAnalysisResult,
                                      quality_assessments: List[QualityAssessmentResult]) -> float:
        """Calculate overall system completeness percentage"""
        if not component_evaluations:
            return 0.0
        
        # Component completeness (40% weight)
        component_scores = [eval.completion_percentage for eval in component_evaluations]
        avg_component_completion = sum(component_scores) / len(component_scores) if component_scores else 0
        
        # Dependency health (30% weight)
        dependency_health = dependency_analysis.overall_dependency_health * 100
        
        # Quality health (30% weight)
        if quality_assessments:
            quality_scores = [qa.overall_quality_score * 100 for qa in quality_assessments]
            avg_quality = sum(quality_scores) / len(quality_scores)
        else:
            avg_quality = 0
        
        # Weighted average
        overall_completeness = (
            avg_component_completion * 0.4 +
            dependency_health * 0.3 +
            avg_quality * 0.3
        )
        
        return overall_completeness    
  
  def _define_required_components(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Define required components for Phoenix Hydra system"""
        return {
            "infrastructure": {
                "NCA Toolkit": {
                    "description": "Core multimedia processing API toolkit",
                    "severity": "critical",
                    "effort": "2-3 weeks",
                    "business_value": "Essential for Phoenix Hydra's core functionality",
                    "impact": "Blocks multimedia processing capabilities"
                },
                "PostgreSQL Database": {
                    "description": "Primary database for data storage",
                    "severity": "critical",
                    "effort": "1 week",
                    "business_value": "Required for data persistence",
                    "impact": "No data storage capability"
                },
                "Minio S3 Storage": {
                    "description": "Object storage for multimedia files",
                    "severity": "high",
                    "effort": "3-5 days",
                    "business_value": "Required for file storage",
                    "impact": "Cannot store multimedia files"
                },
                "Prometheus Monitoring": {
                    "description": "System monitoring and metrics collection",
                    "severity": "medium",
                    "effort": "1 week",
                    "business_value": "System observability",
                    "impact": "Limited system monitoring"
                },
                "Grafana Dashboard": {
                    "description": "Monitoring dashboard and visualization",
                    "severity": "medium",
                    "effort": "3-5 days",
                    "business_value": "System visibility",
                    "impact": "No monitoring dashboard"
                }
            },
            "monetization": {
                "Affiliate Marketing System": {
                    "description": "Affiliate program management for revenue generation",
                    "severity": "high",
                    "effort": "2-3 weeks",
                    "business_value": "Direct revenue impact - €400k+ target",
                    "impact": "Cannot generate affiliate revenue"
                },
                "Revenue Tracking": {
                    "description": "Revenue analytics and tracking system",
                    "severity": "high",
                    "effort": "1-2 weeks",
                    "business_value": "Revenue optimization and reporting",
                    "impact": "No revenue visibility"
                },
                "Grant Application Tracker": {
                    "description": "Grant management and compliance tracking",
                    "severity": "medium",
                    "effort": "1-2 weeks",
                    "business_value": "Grant funding opportunities",
                    "impact": "Manual grant management"
                }
            },
            "automation": {
                "VS Code Integration": {
                    "description": "Development environment integration",
                    "severity": "medium",
                    "effort": "1 week",
                    "business_value": "Developer productivity",
                    "impact": "Reduced development efficiency"
                },
                "Deployment Scripts": {
                    "description": "Automated deployment and infrastructure scripts",
                    "severity": "high",
                    "effort": "1-2 weeks",
                    "business_value": "Deployment automation",
                    "impact": "Manual deployment processes"
                },
                "CI/CD Pipeline": {
                    "description": "Continuous integration and deployment pipeline",
                    "severity": "medium",
                    "effort": "2-3 weeks",
                    "business_value": "Development workflow automation",
                    "impact": "Manual testing and deployment"
                }
            }
        }
    
    def _define_quality_standards(self) -> Dict[str, float]:
        """Define quality standards for Phoenix Hydra"""
        return {
            "minimum_code_quality": 0.8,
            "minimum_documentation": 0.8,
            "minimum_test_coverage": 80.0,
            "maximum_complexity": 10.0,
            "minimum_maintainability": 0.7
        }
    
    def _define_business_priorities(self) -> Dict[str, float]:
        """Define business priority weights for different categories"""
        return {
            "monetization": 1.0,      # Highest priority - revenue impact
            "infrastructure": 0.9,    # Critical for system operation
            "automation": 0.7,        # Important for efficiency
            "quality": 0.6,           # Important for maintainability
            "documentation": 0.5,     # Important for onboarding
            "testing": 0.6            # Important for reliability
        }
    
    def _determine_implementation_gap_severity(self, evaluation: ComponentEvaluation) -> GapSeverity:
        """Determine severity of implementation gap based on evaluation"""
        if not evaluation.critical_criteria_passed:
            return GapSeverity.CRITICAL
        elif evaluation.completion_percentage < 30:
            return GapSeverity.HIGH
        elif evaluation.completion_percentage < 60:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW
    
    def _map_component_category_to_improvement(self, category: ComponentCategory) -> ImprovementCategory:
        """Map component category to improvement category"""
        mapping = {
            ComponentCategory.INFRASTRUCTURE: ImprovementCategory.INFRASTRUCTURE,
            ComponentCategory.MONETIZATION: ImprovementCategory.MONETIZATION,
            ComponentCategory.AUTOMATION: ImprovementCategory.AUTOMATION
        }
        return mapping.get(category, ImprovementCategory.INFRASTRUCTURE)
    
    def _estimate_implementation_effort(self, evaluation: ComponentEvaluation) -> str:
        """Estimate effort required to complete implementation"""
        completion = evaluation.completion_percentage
        
        if completion < 30:
            return "2-3 weeks"
        elif completion < 60:
            return "1-2 weeks"
        elif completion < 80:
            return "3-5 days"
        else:
            return "1-2 days"
    
    def _estimate_improvement_effort(self, evaluation: ComponentEvaluation) -> str:
        """Estimate effort required for improvement"""
        completion = evaluation.completion_percentage
        
        if completion < 50:
            return "1-2 weeks"
        elif completion < 70:
            return "3-5 days"
        else:
            return "1-2 days"
    
    def _estimate_quality_improvement_effort(self, assessment: QualityAssessmentResult) -> str:
        """Estimate effort to improve quality"""
        score = assessment.overall_quality_score
        
        if score < 0.3:
            return "2-3 weeks"
        elif score < 0.5:
            return "1-2 weeks"
        elif score < 0.7:
            return "3-5 days"
        else:
            return "1-2 days"
    
    def _estimate_documentation_effort(self, doc_assessment) -> str:
        """Estimate effort to improve documentation"""
        missing_count = len(doc_assessment.missing_docs)
        
        if missing_count > 10:
            return "1-2 weeks"
        elif missing_count > 5:
            return "3-5 days"
        else:
            return "1-2 days"
    
    def _estimate_testing_effort(self, test_coverage) -> str:
        """Estimate effort to improve test coverage"""
        coverage = test_coverage.coverage_percentage
        
        if coverage < 30:
            return "2-3 weeks"
        elif coverage < 50:
            return "1-2 weeks"
        elif coverage < 70:
            return "3-5 days"
        else:
            return "1-2 days"
    
    def _assess_business_value(self, component: Component) -> str:
        """Assess business value of component improvement"""
        category_value = {
            ComponentCategory.MONETIZATION: "Direct revenue impact - critical for €400k+ target",
            ComponentCategory.INFRASTRUCTURE: "Essential for system operation and scalability",
            ComponentCategory.AUTOMATION: "Improves development efficiency and reduces manual work"
        }
        
        return category_value.get(component.category, "Improves system functionality")
    
    def _group_gaps_by_priority(self, gaps: List[Gap]) -> Dict[ImprovementCategory, List[Gap]]:
        """Group gaps by improvement category"""
        groups = {}
        
        for category in ImprovementCategory:
            groups[category] = [gap for gap in gaps if gap.category == category]
        
        return groups
    
    def _calculate_priority_score(self, gaps: List[Gap]) -> float:
        """Calculate priority score for a group of gaps"""
        if not gaps:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            GapSeverity.CRITICAL: 1.0,
            GapSeverity.HIGH: 0.8,
            GapSeverity.MEDIUM: 0.6,
            GapSeverity.LOW: 0.4
        }
        
        # Weight by business priority
        business_weights = self.business_priorities
        
        total_score = 0.0
        for gap in gaps:
            severity_weight = severity_weights.get(gap.severity, 0.5)
            business_weight = business_weights.get(gap.category.value, 0.5)
            gap_score = severity_weight * business_weight
            total_score += gap_score
        
        # Normalize by number of gaps
        return min(total_score / len(gaps), 1.0)
    
    def _aggregate_effort_estimates(self, gaps: List[Gap]) -> str:
        """Aggregate effort estimates for multiple gaps"""
        effort_mapping = {
            "1-2 days": 1.5,
            "3-5 days": 4,
            "1 week": 7,
            "1-2 weeks": 10.5,
            "2-3 weeks": 17.5,
            "1 month": 30
        }
        
        total_days = 0
        for gap in gaps:
            total_days += effort_mapping.get(gap.estimated_effort, 7)  # Default to 1 week
        
        if total_days <= 2:
            return "1-2 days"
        elif total_days <= 5:
            return "3-5 days"
        elif total_days <= 7:
            return "1 week"
        elif total_days <= 14:
            return "1-2 weeks"
        elif total_days <= 21:
            return "2-3 weeks"
        else:
            return "1+ months"
    
    def _aggregate_business_value(self, gaps: List[Gap]) -> str:
        """Aggregate business value for multiple gaps"""
        if not gaps:
            return "No specific business value"
        
        # Prioritize monetization gaps
        monetization_gaps = [g for g in gaps if g.category == ImprovementCategory.MONETIZATION]
        if monetization_gaps:
            return "Direct revenue impact - critical for business success"
        
        # Then infrastructure
        infrastructure_gaps = [g for g in gaps if g.category == ImprovementCategory.INFRASTRUCTURE]
        if infrastructure_gaps:
            return "Essential for system operation and reliability"
        
        # Then automation
        automation_gaps = [g for g in gaps if g.category == ImprovementCategory.AUTOMATION]
        if automation_gaps:
            return "Improves development efficiency and reduces operational overhead"
        
        return "Improves overall system quality and maintainability"
    
    def _generate_implementation_steps(self, gaps: List[Gap]) -> List[str]:
        """Generate implementation steps for addressing gaps"""
        steps = []
        
        # Group by gap type
        gap_types = {}
        for gap in gaps:
            if gap.gap_type not in gap_types:
                gap_types[gap.gap_type] = []
            gap_types[gap.gap_type].append(gap)
        
        # Generate steps based on gap types
        if GapType.MISSING_COMPONENT in gap_types:
            steps.append("1. Identify and implement missing components")
            steps.append("2. Set up basic component structure and interfaces")
        
        if GapType.INCOMPLETE_IMPLEMENTATION in gap_types:
            steps.append("3. Complete partial implementations")
            steps.append("4. Implement missing functionality")
        
        if GapType.DEPENDENCY_GAP in gap_types:
            steps.append("5. Resolve dependency issues")
            steps.append("6. Update component relationships")
        
        if GapType.QUALITY_GAP in gap_types:
            steps.append("7. Improve code quality and maintainability")
            steps.append("8. Refactor problematic code sections")
        
        if GapType.DOCUMENTATION_GAP in gap_types:
            steps.append("9. Add missing documentation")
            steps.append("10. Update existing documentation")
        
        if GapType.TEST_COVERAGE_GAP in gap_types:
            steps.append("11. Write missing unit tests")
            steps.append("12. Add integration tests")
        
        return steps[:8]  # Limit to 8 steps for readability
    
    def _generate_success_criteria(self, gaps: List[Gap]) -> List[str]:
        """Generate success criteria for addressing gaps"""
        criteria = []
        
        # Count gaps by type
        gap_counts = {}
        for gap in gaps:
            gap_counts[gap.gap_type] = gap_counts.get(gap.gap_type, 0) + 1
        
        if GapType.MISSING_COMPONENT in gap_counts:
            criteria.append(f"All {gap_counts[GapType.MISSING_COMPONENT]} missing components implemented")
        
        if GapType.INCOMPLETE_IMPLEMENTATION in gap_counts:
            criteria.append(f"All {gap_counts[GapType.INCOMPLETE_IMPLEMENTATION]} incomplete implementations completed")
        
        if GapType.QUALITY_GAP in gap_counts:
            criteria.append("Code quality score above 0.8 for all components")
        
        if GapType.DOCUMENTATION_GAP in gap_counts:
            criteria.append("Documentation coverage above 80% for all components")
        
        if GapType.TEST_COVERAGE_GAP in gap_counts:
            criteria.append("Test coverage above 80% for all components")
        
        if GapType.DEPENDENCY_GAP in gap_counts:
            criteria.append("All dependency issues resolved")
        
        # Add overall criteria
        criteria.append("System completeness above 90%")
        criteria.append("All critical and high-severity gaps addressed")
        
        return criteria