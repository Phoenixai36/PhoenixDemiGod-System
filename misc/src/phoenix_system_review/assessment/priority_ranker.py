"""
Priority Ranker for Phoenix Hydra System Review Tool

Implements priority assignment based on business impact and technical complexity,
creates effort estimation algorithms, and adds dependency-based priority adjustment.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

from ..models.data_models import Component, ComponentCategory, Priority
from ..analysis.component_evaluator import ComponentEvaluation, EvaluationStatus
from ..analysis.quality_assessor import QualityAssessmentResult, QualityLevel
from ..analysis.dependency_analyzer import DependencyAnalysisResult
from .completion_calculator import ComponentCompletionScore, CompletionTier


class PriorityLevel(Enum):
    """Priority levels for components and tasks"""
    CRITICAL = "critical"      # Must be done immediately
    HIGH = "high"             # Should be done soon
    MEDIUM = "medium"         # Should be done eventually
    LOW = "low"               # Nice to have


class EffortLevel(Enum):
    """Effort estimation levels"""
    MINIMAL = "minimal"       # 1-2 days
    LOW = "low"              # 3-5 days
    MEDIUM = "medium"        # 1-2 weeks
    HIGH = "high"            # 2-4 weeks
    EXTENSIVE = "extensive"   # 1+ months


@dataclass
class PriorityScore:
    """Priority score for a component or task"""
    component_name: str
    priority_level: PriorityLevel
    priority_score: float        # 0.0 to 100.0
    business_impact_score: float # 0.0 to 100.0
    technical_complexity_score: float # 0.0 to 100.0
    dependency_urgency_score: float   # 0.0 to 100.0
    effort_estimate: EffortLevel
    effort_hours: int
    roi_score: float            # Return on investment score
    risk_factor: float          # Risk if not completed (0.0 to 1.0)
    completion_tier: CompletionTier
    justification: str
    dependencies: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)


@dataclass
class PriorityRankingResult:
    """Results from priority ranking analysis"""
    priority_scores: List[PriorityScore] = field(default_factory=list)
    priority_matrix: Dict[str, List[PriorityScore]] = field(default_factory=dict)
    effort_distribution: Dict[str, int] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    quick_wins: List[PriorityScore] = field(default_factory=list)
    high_impact_items: List[PriorityScore] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    total_estimated_effort: int = 0
    ranking_timestamp: datetime = field(default_factory=datetime.now)


class PriorityRanker:
    """
    Ranks components and tasks by priority based on business impact,
    technical complexity, and dependency relationships.
    
    Provides effort estimation and ROI analysis to guide development priorities.
    """
    
    def __init__(self):
        """Initialize priority ranker"""
        self.logger = logging.getLogger(__name__)
        
        # Business impact weights by category (Phoenix Hydra specific)
        self.business_impact_weights = self._define_business_impact_weights()
        
        # Technical complexity factors
        self.complexity_factors = self._define_complexity_factors()
        
        # Effort estimation mappings
        self.effort_mappings = self._define_effort_mappings()
        
        # ROI calculation parameters
        self.roi_parameters = self._define_roi_parameters()
    
    def rank_priorities(self, 
                       component_scores: List[ComponentCompletionScore],
                       component_evaluations: List[ComponentEvaluation],
                       quality_assessments: List[QualityAssessmentResult],
                       dependency_analysis: DependencyAnalysisResult) -> PriorityRankingResult:
        """
        Rank components by priority based on multiple factors.
        
        Args:
            component_scores: Completion scores from completion calculator
            component_evaluations: Results from component evaluation
            quality_assessments: Results from quality assessment
            dependency_analysis: Results from dependency analysis
            
        Returns:
            PriorityRankingResult with ranked priorities and analysis
        """
        try:
            # Calculate priority scores for each component
            priority_scores = self._calculate_priority_scores(
                component_scores, component_evaluations, quality_assessments, dependency_analysis
            )
            
            # Sort by priority score (highest first)
            priority_scores.sort(key=lambda x: x.priority_score, reverse=True)
            
            # Create priority matrix
            priority_matrix = self._create_priority_matrix(priority_scores)
            
            # Calculate effort distribution
            effort_distribution = self._calculate_effort_distribution(priority_scores)
            
            # Identify critical path
            critical_path = self._identify_critical_path(priority_scores, dependency_analysis)
            
            # Identify quick wins (high impact, low effort)
            quick_wins = self._identify_quick_wins(priority_scores)
            
            # Identify high impact items
            high_impact_items = self._identify_high_impact_items(priority_scores)
            
            # Generate recommendations
            recommendations = self._generate_priority_recommendations(
                priority_scores, critical_path, quick_wins
            )
            
            # Calculate total estimated effort
            total_effort = sum(score.effort_hours for score in priority_scores)
            
            return PriorityRankingResult(
                priority_scores=priority_scores,
                priority_matrix=priority_matrix,
                effort_distribution=effort_distribution,
                critical_path=critical_path,
                quick_wins=quick_wins,
                high_impact_items=high_impact_items,
                recommendations=recommendations,
                total_estimated_effort=total_effort
            )
            
        except Exception as e:
            self.logger.error(f"Error ranking priorities: {e}")
            return PriorityRankingResult()
    
    def _calculate_priority_scores(self, 
                                 component_scores: List[ComponentCompletionScore],
                                 component_evaluations: List[ComponentEvaluation],
                                 quality_assessments: List[QualityAssessmentResult],
                                 dependency_analysis: DependencyAnalysisResult) -> List[PriorityScore]:
        """Calculate priority scores for all components"""
        priority_scores = []
        
        # Create lookup dictionaries
        evaluation_lookup = {eval.component.name: eval for eval in component_evaluations}
        quality_lookup = {qa.component.name: qa for qa in quality_assessments}
        
        for comp_score in component_scores:
            component = comp_score.component
            evaluation = evaluation_lookup.get(component.name)
            quality_assessment = quality_lookup.get(component.name)
            
            # Calculate business impact score
            business_impact = self._calculate_business_impact_score(comp_score, evaluation)
            
            # Calculate technical complexity score
            technical_complexity = self._calculate_technical_complexity_score(
                component, evaluation, quality_assessment
            )
            
            # Calculate dependency urgency score
            dependency_urgency = self._calculate_dependency_urgency_score(
                component, dependency_analysis
            )
            
            # Calculate overall priority score
            overall_priority = self._calculate_overall_priority_score(
                business_impact, technical_complexity, dependency_urgency, comp_score
            )
            
            # Determine priority level
            priority_level = self._determine_priority_level(overall_priority, comp_score.tier)
            
            # Estimate effort
            effort_level, effort_hours = self._estimate_effort(
                component, evaluation, quality_assessment, comp_score.completion_percentage
            )
            
            # Calculate ROI score
            roi_score = self._calculate_roi_score(business_impact, effort_hours)
            
            # Calculate risk factor
            risk_factor = self._calculate_risk_factor(comp_score, dependency_analysis)
            
            # Generate justification
            justification = self._generate_justification(
                component, business_impact, technical_complexity, dependency_urgency, comp_score
            )
            
            # Identify dependencies and blockers
            dependencies, blockers = self._identify_dependencies_and_blockers(
                component, dependency_analysis
            )
            
            priority_score = PriorityScore(
                component_name=component.name,
                priority_level=priority_level,
                priority_score=overall_priority,
                business_impact_score=business_impact,
                technical_complexity_score=technical_complexity,
                dependency_urgency_score=dependency_urgency,
                effort_estimate=effort_level,
                effort_hours=effort_hours,
                roi_score=roi_score,
                risk_factor=risk_factor,
                completion_tier=comp_score.tier,
                justification=justification,
                dependencies=dependencies,
                blockers=blockers
            )
            
            priority_scores.append(priority_score)
        
        return priority_scores
    
    def _calculate_business_impact_score(self, 
                                       comp_score: ComponentCompletionScore,
                                       evaluation: Optional[ComponentEvaluation]) -> float:
        """Calculate business impact score (0-100)"""
        # Base score from category weight
        category_weight = self.business_impact_weights.get(comp_score.component.category, 1.0)
        base_score = category_weight * 20  # Scale to 0-100
        
        # Tier multiplier
        tier_multipliers = {
            CompletionTier.CRITICAL: 2.0,
            CompletionTier.ESSENTIAL: 1.5,
            CompletionTier.IMPORTANT: 1.0,
            CompletionTier.OPTIONAL: 0.5
        }
        
        tier_multiplier = tier_multipliers.get(comp_score.tier, 1.0)
        
        # Completion urgency (lower completion = higher urgency)
        completion_urgency = (100 - comp_score.completion_percentage) / 100
        
        # Calculate final score
        impact_score = base_score * tier_multiplier * (1 + completion_urgency)
        
        return min(100.0, impact_score)
    
    def _calculate_technical_complexity_score(self, 
                                            component: Component,
                                            evaluation: Optional[ComponentEvaluation],
                                            quality_assessment: Optional[QualityAssessmentResult]) -> float:
        """Calculate technical complexity score (0-100)"""
        complexity_score = 50.0  # Base complexity
        
        # Component type complexity
        component_name = component.name.lower()
        for factor, weight in self.complexity_factors.items():
            if factor in component_name:
                complexity_score += weight * 10
        
        # Quality-based complexity adjustment
        if quality_assessment:
            if quality_assessment.quality_level == QualityLevel.POOR:
                complexity_score += 20  # Poor quality increases complexity
            elif quality_assessment.quality_level == QualityLevel.EXCELLENT:
                complexity_score -= 10  # Good quality reduces complexity
        
        # Evaluation status complexity
        if evaluation:
            if evaluation.status == EvaluationStatus.FAILED:
                complexity_score += 15  # Failed evaluation increases complexity
            elif evaluation.status == EvaluationStatus.PASSED:
                complexity_score -= 5   # Passed evaluation reduces complexity
        
        return max(0.0, min(100.0, complexity_score))
    
    def _calculate_dependency_urgency_score(self, 
                                          component: Component,
                                          dependency_analysis: DependencyAnalysisResult) -> float:
        """Calculate dependency urgency score (0-100)"""
        urgency_score = 0.0
        
        # Count how many components depend on this one
        dependent_count = len([
            dep for dep in dependency_analysis.dependency_graph.dependencies
            if dep.target == component.name
        ])
        
        # Higher dependency count = higher urgency
        urgency_score += dependent_count * 15
        
        # Check if this component is in critical path
        if component.name in dependency_analysis.circular_dependencies:
            urgency_score += 30  # Circular dependencies are urgent
        
        # Check for missing dependencies
        missing_deps = [
            dep for dep in dependency_analysis.missing_dependencies
            if dep.source == component.name
        ]
        urgency_score += len(missing_deps) * 10
        
        return min(100.0, urgency_score)
    
    def _calculate_overall_priority_score(self, 
                                        business_impact: float,
                                        technical_complexity: float,
                                        dependency_urgency: float,
                                        comp_score: ComponentCompletionScore) -> float:
        """Calculate overall priority score (0-100)"""
        # Weighted combination of factors
        weights = {
            'business_impact': 0.4,      # 40% weight
            'dependency_urgency': 0.3,   # 30% weight
            'technical_complexity': 0.2, # 20% weight (inverse)
            'completion_gap': 0.1        # 10% weight
        }
        
        # Invert technical complexity (lower complexity = higher priority)
        complexity_factor = (100 - technical_complexity) / 100
        
        # Completion gap factor (lower completion = higher priority)
        completion_gap = (100 - comp_score.completion_percentage) / 100
        
        # Calculate weighted score
        priority_score = (
            business_impact * weights['business_impact'] +
            dependency_urgency * weights['dependency_urgency'] +
            complexity_factor * 100 * weights['technical_complexity'] +
            completion_gap * 100 * weights['completion_gap']
        )
        
        return min(100.0, priority_score)
    
    def _determine_priority_level(self, priority_score: float, tier: CompletionTier) -> PriorityLevel:
        """Determine priority level based on score and tier"""
        # Critical tier components get elevated priority
        if tier == CompletionTier.CRITICAL:
            if priority_score >= 70:
                return PriorityLevel.CRITICAL
            elif priority_score >= 50:
                return PriorityLevel.HIGH
            else:
                return PriorityLevel.MEDIUM
        
        # Standard priority determination
        if priority_score >= 80:
            return PriorityLevel.CRITICAL
        elif priority_score >= 60:
            return PriorityLevel.HIGH
        elif priority_score >= 40:
            return PriorityLevel.MEDIUM
        else:
            return PriorityLevel.LOW
    
    def _estimate_effort(self, 
                        component: Component,
                        evaluation: Optional[ComponentEvaluation],
                        quality_assessment: Optional[QualityAssessmentResult],
                        completion_percentage: float) -> Tuple[EffortLevel, int]:
        """Estimate effort required to complete component"""
        # Base effort based on completion percentage
        remaining_work = 100 - completion_percentage
        base_hours = int(remaining_work * 2)  # 2 hours per percentage point
        
        # Component type effort multiplier
        component_name = component.name.lower()
        effort_multiplier = 1.0
        
        for factor, multiplier in self.effort_mappings.items():
            if factor in component_name:
                effort_multiplier = max(effort_multiplier, multiplier)
        
        # Quality-based effort adjustment
        if quality_assessment:
            if quality_assessment.quality_level == QualityLevel.POOR:
                effort_multiplier *= 1.5  # Poor quality requires more effort
            elif quality_assessment.quality_level == QualityLevel.EXCELLENT:
                effort_multiplier *= 0.8  # Good quality requires less effort
        
        # Evaluation status effort adjustment
        if evaluation:
            if evaluation.status == EvaluationStatus.FAILED:
                effort_multiplier *= 1.3  # Failed evaluation requires more effort
        
        # Calculate final effort
        total_hours = int(base_hours * effort_multiplier)
        
        # Determine effort level
        if total_hours <= 16:  # 2 days
            effort_level = EffortLevel.MINIMAL
        elif total_hours <= 40:  # 5 days
            effort_level = EffortLevel.LOW
        elif total_hours <= 80:  # 2 weeks
            effort_level = EffortLevel.MEDIUM
        elif total_hours <= 160:  # 4 weeks
            effort_level = EffortLevel.HIGH
        else:
            effort_level = EffortLevel.EXTENSIVE
        
        return effort_level, max(8, total_hours)  # Minimum 8 hours
    
    def _calculate_roi_score(self, business_impact: float, effort_hours: int) -> float:
        """Calculate return on investment score"""
        # ROI = Business Impact / Effort (normalized)
        if effort_hours == 0:
            return 0.0
        
        # Normalize effort to 0-100 scale (assuming max 320 hours = 8 weeks)
        normalized_effort = min(100.0, (effort_hours / 320) * 100)
        
        # Calculate ROI (higher is better)
        roi = business_impact / max(1.0, normalized_effort)
        
        return min(100.0, roi * 10)  # Scale to 0-100
    
    def _calculate_risk_factor(self, 
                             comp_score: ComponentCompletionScore,
                             dependency_analysis: DependencyAnalysisResult) -> float:
        """Calculate risk factor if component is not completed"""
        risk_factor = 0.0
        
        # Tier-based risk
        tier_risks = {
            CompletionTier.CRITICAL: 0.9,
            CompletionTier.ESSENTIAL: 0.7,
            CompletionTier.IMPORTANT: 0.5,
            CompletionTier.OPTIONAL: 0.2
        }
        
        risk_factor += tier_risks.get(comp_score.tier, 0.5)
        
        # Dependency-based risk
        dependent_count = len([
            dep for dep in dependency_analysis.dependency_graph.dependencies
            if dep.target == comp_score.component.name
        ])
        
        # More dependents = higher risk
        dependency_risk = min(0.3, dependent_count * 0.05)
        risk_factor += dependency_risk
        
        return min(1.0, risk_factor)
    
    def _generate_justification(self, 
                              component: Component,
                              business_impact: float,
                              technical_complexity: float,
                              dependency_urgency: float,
                              comp_score: ComponentCompletionScore) -> str:
        """Generate justification for priority assignment"""
        justifications = []
        
        # Business impact justification
        if business_impact >= 80:
            justifications.append("High business impact")
        elif business_impact >= 60:
            justifications.append("Moderate business impact")
        
        # Completion urgency
        if comp_score.completion_percentage < 50:
            justifications.append("Low completion percentage")
        
        # Tier importance
        if comp_score.tier == CompletionTier.CRITICAL:
            justifications.append("Critical for system operation")
        elif comp_score.tier == CompletionTier.ESSENTIAL:
            justifications.append("Essential for production readiness")
        
        # Dependency urgency
        if dependency_urgency >= 60:
            justifications.append("High dependency urgency")
        
        # Technical complexity
        if technical_complexity >= 80:
            justifications.append("High technical complexity")
        elif technical_complexity <= 30:
            justifications.append("Low technical complexity")
        
        return "; ".join(justifications) if justifications else "Standard priority assignment"
    
    def _identify_dependencies_and_blockers(self, 
                                          component: Component,
                                          dependency_analysis: DependencyAnalysisResult) -> Tuple[List[str], List[str]]:
        """Identify dependencies and blockers for a component"""
        dependencies = []
        blockers = []
        
        # Find dependencies (what this component depends on)
        for dep in dependency_analysis.dependency_graph.dependencies:
            if dep.source == component.name:
                dependencies.append(dep.target)
        
        # Find blockers (missing dependencies)
        for missing_dep in dependency_analysis.missing_dependencies:
            if missing_dep.source == component.name:
                blockers.append(missing_dep.target)
        
        return dependencies, blockers
    
    def _create_priority_matrix(self, priority_scores: List[PriorityScore]) -> Dict[str, List[PriorityScore]]:
        """Create priority matrix organized by priority level"""
        matrix = {}
        
        for level in PriorityLevel:
            matrix[level.value] = [
                score for score in priority_scores 
                if score.priority_level == level
            ]
        
        return matrix
    
    def _calculate_effort_distribution(self, priority_scores: List[PriorityScore]) -> Dict[str, int]:
        """Calculate effort distribution by effort level"""
        distribution = {}
        
        for level in EffortLevel:
            count = len([
                score for score in priority_scores 
                if score.effort_estimate == level
            ])
            distribution[level.value] = count
        
        return distribution
    
    def _identify_critical_path(self, 
                              priority_scores: List[PriorityScore],
                              dependency_analysis: DependencyAnalysisResult) -> List[str]:
        """Identify critical path components"""
        critical_path = []
        
        # Start with critical tier components
        critical_components = [
            score.component_name for score in priority_scores 
            if score.completion_tier == CompletionTier.CRITICAL
        ]
        
        # Add components with high dependency urgency
        high_dependency_components = [
            score.component_name for score in priority_scores 
            if score.dependency_urgency_score >= 60
        ]
        
        # Combine and deduplicate
        critical_path = list(set(critical_components + high_dependency_components))
        
        # Sort by priority score
        critical_path.sort(key=lambda name: next(
            score.priority_score for score in priority_scores 
            if score.component_name == name
        ), reverse=True)
        
        return critical_path[:10]  # Limit to top 10
    
    def _identify_quick_wins(self, priority_scores: List[PriorityScore]) -> List[PriorityScore]:
        """Identify quick wins (high ROI, low effort)"""
        quick_wins = []
        
        for score in priority_scores:
            # High ROI and low effort
            if (score.roi_score >= 60 and 
                score.effort_estimate in [EffortLevel.MINIMAL, EffortLevel.LOW]):
                quick_wins.append(score)
        
        # Sort by ROI score
        quick_wins.sort(key=lambda x: x.roi_score, reverse=True)
        
        return quick_wins[:5]  # Top 5 quick wins
    
    def _identify_high_impact_items(self, priority_scores: List[PriorityScore]) -> List[PriorityScore]:
        """Identify high impact items regardless of effort"""
        high_impact = [
            score for score in priority_scores 
            if score.business_impact_score >= 70
        ]
        
        # Sort by business impact
        high_impact.sort(key=lambda x: x.business_impact_score, reverse=True)
        
        return high_impact[:10]  # Top 10 high impact items
    
    def _generate_priority_recommendations(self, 
                                         priority_scores: List[PriorityScore],
                                         critical_path: List[str],
                                         quick_wins: List[PriorityScore]) -> List[str]:
        """Generate priority-based recommendations"""
        recommendations = []
        
        # Critical priority recommendations
        critical_items = [s for s in priority_scores if s.priority_level == PriorityLevel.CRITICAL]
        if critical_items:
            recommendations.append(f"Address {len(critical_items)} critical priority items immediately")
        
        # Quick wins recommendations
        if quick_wins:
            recommendations.append(f"Start with {len(quick_wins)} quick wins for immediate ROI")
        
        # Critical path recommendations
        if critical_path:
            recommendations.append(f"Focus on critical path: {', '.join(critical_path[:3])}")
        
        # Effort distribution recommendations
        high_effort_items = [s for s in priority_scores if s.effort_estimate == EffortLevel.EXTENSIVE]
        if high_effort_items:
            recommendations.append(f"Plan carefully for {len(high_effort_items)} extensive effort items")
        
        # Risk-based recommendations
        high_risk_items = [s for s in priority_scores if s.risk_factor >= 0.8]
        if high_risk_items:
            recommendations.append(f"Mitigate risks for {len(high_risk_items)} high-risk components")
        
        return recommendations
    
    def _define_business_impact_weights(self) -> Dict[ComponentCategory, float]:
        """Define business impact weights by category"""
        return {
            ComponentCategory.MONETIZATION: 5.0,      # Highest impact - direct revenue
            ComponentCategory.INFRASTRUCTURE: 4.0,    # High impact - system foundation
            ComponentCategory.AUTOMATION: 3.0,        # Medium impact - efficiency
            ComponentCategory.SECURITY: 3.5,          # High impact - production requirement
            ComponentCategory.TESTING: 2.5,           # Medium impact - quality assurance
            ComponentCategory.DOCUMENTATION: 2.0      # Lower impact - support
        }
    
    def _define_complexity_factors(self) -> Dict[str, float]:
        """Define technical complexity factors"""
        return {
            "api": 2.0,           # APIs are complex
            "database": 2.5,      # Database work is very complex
            "integration": 2.2,   # Integrations are complex
            "security": 2.3,      # Security is complex
            "authentication": 2.4, # Auth is very complex
            "payment": 2.6,       # Payment systems are very complex
            "monitoring": 1.8,    # Monitoring is moderately complex
            "configuration": 1.2, # Configuration is less complex
            "documentation": 0.8, # Documentation is simple
            "testing": 1.5        # Testing is moderately complex
        }
    
    def _define_effort_mappings(self) -> Dict[str, float]:
        """Define effort estimation mappings"""
        return {
            "api": 1.5,           # APIs require more effort
            "database": 1.8,      # Database work requires significant effort
            "integration": 1.6,   # Integrations require more effort
            "security": 1.7,      # Security requires significant effort
            "authentication": 1.9, # Auth requires significant effort
            "payment": 2.0,       # Payment systems require most effort
            "monitoring": 1.3,    # Monitoring requires moderate effort
            "configuration": 1.0, # Configuration is standard effort
            "documentation": 0.7, # Documentation requires less effort
            "testing": 1.2        # Testing requires moderate effort
        }
    
    def _define_roi_parameters(self) -> Dict[str, float]:
        """Define ROI calculation parameters"""
        return {
            "revenue_multiplier": 2.0,      # Revenue components get 2x ROI
            "infrastructure_multiplier": 1.5, # Infrastructure gets 1.5x ROI
            "automation_multiplier": 1.3,   # Automation gets 1.3x ROI
            "quality_multiplier": 1.1,      # Quality gets 1.1x ROI
            "documentation_multiplier": 0.8  # Documentation gets 0.8x ROI
        }
    
    def get_priority_summary(self, ranking_result: PriorityRankingResult) -> Dict[str, Any]:
        """Get a summary of priority ranking results"""
        if not ranking_result.priority_scores:
            return {"error": "No priority scores available"}
        
        return {
            "total_components": len(ranking_result.priority_scores),
            "critical_priority_count": len(ranking_result.priority_matrix.get("critical", [])),
            "high_priority_count": len(ranking_result.priority_matrix.get("high", [])),
            "medium_priority_count": len(ranking_result.priority_matrix.get("medium", [])),
            "low_priority_count": len(ranking_result.priority_matrix.get("low", [])),
            "total_estimated_effort_hours": ranking_result.total_estimated_effort,
            "total_estimated_effort_weeks": ranking_result.total_estimated_effort / 40,
            "quick_wins_count": len(ranking_result.quick_wins),
            "high_impact_count": len(ranking_result.high_impact_items),
            "critical_path_length": len(ranking_result.critical_path),
            "effort_distribution": ranking_result.effort_distribution,
            "top_priorities": [
                {
                    "component": score.component_name,
                    "priority_level": score.priority_level.value,
                    "priority_score": score.priority_score,
                    "effort_estimate": score.effort_estimate.value,
                    "roi_score": score.roi_score,
                    "justification": score.justification
                }
                for score in ranking_result.priority_scores[:5]
            ],
            "recommendations": ranking_result.recommendations,
            "analysis_timestamp": ranking_result.ranking_timestamp.isoformat()
        }