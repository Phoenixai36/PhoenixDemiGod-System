"""
Completion Calculator for Phoenix Hydra System Review Tool

Builds weighted completion percentage calculation logic and creates
component-level and system-level completion scoring with trend analysis.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import statistics

from ..models.data_models import Component, ComponentCategory, Priority
from ..analysis.component_evaluator import ComponentEvaluation, EvaluationStatus
from ..analysis.quality_assessor import QualityAssessmentResult, QualityLevel
from ..analysis.dependency_analyzer import DependencyAnalysisResult


class CompletionTier(Enum):
    """Completion tiers for categorizing components"""
    CRITICAL = "critical"      # Must be 100% complete for system operation
    ESSENTIAL = "essential"    # Should be 90%+ complete for production
    IMPORTANT = "important"    # Should be 70%+ complete for full functionality
    OPTIONAL = "optional"      # Nice to have, 50%+ acceptable


class TrendDirection(Enum):
    """Trend direction for completion analysis"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


@dataclass
class ComponentCompletionScore:
    """Completion score for a single component"""
    component: Component
    completion_percentage: float  # 0.0 to 100.0
    weighted_score: float        # Weighted by business importance
    tier: CompletionTier
    quality_factor: float        # Quality adjustment factor (0.0 to 1.0)
    dependency_factor: float     # Dependency health factor (0.0 to 1.0)
    business_impact_weight: float # Business importance weight
    technical_complexity_weight: float # Technical complexity weight
    adjusted_completion: float   # Final adjusted completion score
    confidence_level: float      # Confidence in the score (0.0 to 1.0)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class SystemCompletionScore:
    """Overall system completion score"""
    overall_completion: float    # 0.0 to 100.0
    weighted_completion: float   # Business-weighted completion
    category_scores: Dict[str, float] = field(default_factory=dict)
    tier_scores: Dict[str, float] = field(default_factory=dict)
    component_count: int = 0
    completed_components: int = 0
    critical_completion: float = 0.0
    essential_completion: float = 0.0
    quality_adjusted_completion: float = 0.0
    confidence_score: float = 0.0
    calculation_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompletionTrend:
    """Completion trend analysis"""
    component_name: str
    current_completion: float
    previous_completion: float
    trend_direction: TrendDirection
    change_rate: float           # Percentage points per day
    projected_completion_date: Optional[datetime]
    confidence_interval: Tuple[float, float]  # (min, max) completion range
    trend_period_days: int = 30


@dataclass
class CompletionAnalysisResult:
    """Complete completion analysis results"""
    system_score: SystemCompletionScore
    component_scores: List[ComponentCompletionScore] = field(default_factory=list)
    completion_trends: List[CompletionTrend] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    milestone_projections: Dict[str, datetime] = field(default_factory=dict)


class CompletionCalculator:
    """
    Calculates weighted completion percentages for Phoenix Hydra components.
    
    Provides component-level and system-level completion scoring with
    business impact weighting, quality adjustments, and trend analysis.
    """
    
    def __init__(self):
        """Initialize completion calculator"""
        self.logger = logging.getLogger(__name__)
        
        # Business impact weights by category
        self.category_weights = self._define_category_weights()
        
        # Component tier definitions
        self.component_tiers = self._define_component_tiers()
        
        # Completion thresholds
        self.completion_thresholds = self._define_completion_thresholds()
        
        # Historical completion data (in production, this would come from database)
        self.historical_data: Dict[str, List[Tuple[datetime, float]]] = {}
    
    def calculate_completion(self, 
                           component_evaluations: List[ComponentEvaluation],
                           quality_assessments: List[QualityAssessmentResult],
                           dependency_analysis: DependencyAnalysisResult) -> CompletionAnalysisResult:
        """
        Calculate comprehensive completion analysis.
        
        Args:
            component_evaluations: Results from component evaluation
            quality_assessments: Results from quality assessment
            dependency_analysis: Results from dependency analysis
            
        Returns:
            CompletionAnalysisResult with detailed completion analysis
        """
        try:
            # Calculate component-level completion scores
            component_scores = self._calculate_component_scores(
                component_evaluations, quality_assessments, dependency_analysis
            )
            
            # Calculate system-level completion score
            system_score = self._calculate_system_score(component_scores)
            
            # Analyze completion trends
            completion_trends = self._analyze_completion_trends(component_scores)
            
            # Generate recommendations
            recommendations = self._generate_completion_recommendations(
                system_score, component_scores, completion_trends
            )
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                system_score, component_scores, completion_trends
            )
            
            # Project milestone completion dates
            milestone_projections = self._project_milestone_dates(
                component_scores, completion_trends
            )
            
            return CompletionAnalysisResult(
                system_score=system_score,
                component_scores=component_scores,
                completion_trends=completion_trends,
                recommendations=recommendations,
                risk_factors=risk_factors,
                milestone_projections=milestone_projections
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating completion: {e}")
            return CompletionAnalysisResult(
                system_score=SystemCompletionScore(
                    overall_completion=0.0,
                    weighted_completion=0.0
                )
            )
    
    def _define_category_weights(self) -> Dict[ComponentCategory, float]:
        """Define business impact weights by category"""
        return {
            ComponentCategory.MONETIZATION: 2.0,      # Highest priority - revenue impact
            ComponentCategory.INFRASTRUCTURE: 1.5,    # Critical for system operation
            ComponentCategory.AUTOMATION: 1.0,        # Important for efficiency
            ComponentCategory.DOCUMENTATION: 0.5,     # Important but lower priority
            ComponentCategory.TESTING: 0.8,           # Important for quality
            ComponentCategory.SECURITY: 1.3           # Important for production
        }
    
    def _define_component_tiers(self) -> Dict[str, CompletionTier]:
        """Define completion tiers for specific components"""
        return {
            # Critical components
            "nca_toolkit": CompletionTier.CRITICAL,
            "database": CompletionTier.CRITICAL,
            "core_api": CompletionTier.CRITICAL,
            "authentication": CompletionTier.CRITICAL,
            "revenue_tracking": CompletionTier.CRITICAL,
            "affiliate_system": CompletionTier.CRITICAL,
            
            # Essential components
            "podman_stack": CompletionTier.ESSENTIAL,
            "minio_storage": CompletionTier.ESSENTIAL,
            "deployment_scripts": CompletionTier.ESSENTIAL,
            "monitoring": CompletionTier.ESSENTIAL,
            "grant_tracking": CompletionTier.ESSENTIAL,
            
            # Important components
            "automation": CompletionTier.IMPORTANT,
            "documentation": CompletionTier.IMPORTANT,
            "testing": CompletionTier.IMPORTANT,
            
            # Optional components
            "optimization": CompletionTier.OPTIONAL,
            "analytics": CompletionTier.OPTIONAL
        }
    
    def _define_completion_thresholds(self) -> Dict[CompletionTier, float]:
        """Define minimum completion thresholds by tier"""
        return {
            CompletionTier.CRITICAL: 100.0,    # Must be complete
            CompletionTier.ESSENTIAL: 90.0,    # Should be nearly complete
            CompletionTier.IMPORTANT: 70.0,    # Should be mostly complete
            CompletionTier.OPTIONAL: 50.0      # Can be partially complete
        }
    
    def _calculate_component_scores(self, 
                                  component_evaluations: List[ComponentEvaluation],
                                  quality_assessments: List[QualityAssessmentResult],
                                  dependency_analysis: DependencyAnalysisResult) -> List[ComponentCompletionScore]:
        """Calculate completion scores for individual components"""
        component_scores = []
        
        # Create lookup dictionaries for quality data
        quality_lookup = {qa.component.name: qa for qa in quality_assessments}
        
        for evaluation in component_evaluations:
            component = evaluation.component
            
            # Get base completion percentage from evaluation
            base_completion = evaluation.completion_percentage
            
            # Get quality assessment if available
            quality_assessment = quality_lookup.get(component.name)
            quality_factor = self._calculate_quality_factor(quality_assessment)
            
            # Calculate dependency factor
            dependency_factor = self._calculate_dependency_factor(
                component, dependency_analysis
            )
            
            # Determine component tier
            tier = self._determine_component_tier(component)
            
            # Calculate business impact weight
            business_weight = self._calculate_business_impact_weight(component, tier)
            
            # Calculate technical complexity weight
            complexity_weight = self._calculate_technical_complexity_weight(component)
            
            # Calculate weighted score
            weighted_score = base_completion * business_weight
            
            # Apply quality and dependency adjustments
            adjusted_completion = self._apply_adjustment_factors(
                base_completion, quality_factor, dependency_factor
            )
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                evaluation, quality_assessment, dependency_factor
            )
            
            component_score = ComponentCompletionScore(
                component=component,
                completion_percentage=base_completion,
                weighted_score=weighted_score,
                tier=tier,
                quality_factor=quality_factor,
                dependency_factor=dependency_factor,
                business_impact_weight=business_weight,
                technical_complexity_weight=complexity_weight,
                adjusted_completion=adjusted_completion,
                confidence_level=confidence_level
            )
            
            component_scores.append(component_score)
        
        return component_scores
    
    def _calculate_system_score(self, component_scores: List[ComponentCompletionScore]) -> SystemCompletionScore:
        """Calculate overall system completion score"""
        if not component_scores:
            return SystemCompletionScore(
                overall_completion=0.0,
                weighted_completion=0.0
            )
        
        # Calculate basic metrics
        total_completion = sum(cs.completion_percentage for cs in component_scores)
        overall_completion = total_completion / len(component_scores)
        
        # Calculate weighted completion
        total_weighted = sum(cs.weighted_score for cs in component_scores)
        total_weights = sum(cs.business_impact_weight for cs in component_scores)
        weighted_completion = total_weighted / total_weights if total_weights > 0 else 0.0
        
        # Calculate category scores
        category_scores = self._calculate_category_scores(component_scores)
        
        # Calculate tier scores
        tier_scores = self._calculate_tier_scores(component_scores)
        
        # Count completed components (>= 90% completion)
        completed_components = len([cs for cs in component_scores if cs.completion_percentage >= 90.0])
        
        # Calculate critical and essential completion
        critical_scores = [cs.completion_percentage for cs in component_scores if cs.tier == CompletionTier.CRITICAL]
        essential_scores = [cs.completion_percentage for cs in component_scores if cs.tier == CompletionTier.ESSENTIAL]
        
        critical_completion = statistics.mean(critical_scores) if critical_scores else 0.0
        essential_completion = statistics.mean(essential_scores) if essential_scores else 0.0
        
        # Calculate quality-adjusted completion
        quality_adjusted_scores = [cs.adjusted_completion for cs in component_scores]
        quality_adjusted_completion = statistics.mean(quality_adjusted_scores)
        
        # Calculate confidence score
        confidence_scores = [cs.confidence_level for cs in component_scores]
        confidence_score = statistics.mean(confidence_scores)
        
        return SystemCompletionScore(
            overall_completion=overall_completion,
            weighted_completion=weighted_completion,
            category_scores=category_scores,
            tier_scores=tier_scores,
            component_count=len(component_scores),
            completed_components=completed_components,
            critical_completion=critical_completion,
            essential_completion=essential_completion,
            quality_adjusted_completion=quality_adjusted_completion,
            confidence_score=confidence_score
        )
    
    # Placeholder methods - would be implemented with full functionality
    def _calculate_quality_factor(self, quality_assessment: Optional[QualityAssessmentResult]) -> float:
        """Calculate quality adjustment factor"""
        if not quality_assessment:
            return 0.8
        
        quality_factors = {
            QualityLevel.EXCELLENT: 1.0,
            QualityLevel.GOOD: 0.9,
            QualityLevel.FAIR: 0.7,
            QualityLevel.POOR: 0.5
        }
        
        return quality_factors.get(quality_assessment.quality_level, 0.8)
    
    def _calculate_dependency_factor(self, component: Component, 
                                   dependency_analysis: DependencyAnalysisResult) -> float:
        """Calculate dependency health factor"""
        return 1.0  # Simplified implementation
    
    def _determine_component_tier(self, component: Component) -> CompletionTier:
        """Determine the completion tier for a component"""
        component_name = component.name.lower()
        
        if any(critical in component_name for critical in ["nca", "database", "revenue", "affiliate"]):
            return CompletionTier.CRITICAL
        elif any(essential in component_name for essential in ["podman", "minio", "deployment", "monitoring"]):
            return CompletionTier.ESSENTIAL
        elif component.category == ComponentCategory.MONETIZATION:
            return CompletionTier.ESSENTIAL
        else:
            return CompletionTier.IMPORTANT
    
    def _calculate_business_impact_weight(self, component: Component, tier: CompletionTier) -> float:
        """Calculate business impact weight for a component"""
        category_weight = self.category_weights.get(component.category, 1.0)
        
        tier_multipliers = {
            CompletionTier.CRITICAL: 2.0,
            CompletionTier.ESSENTIAL: 1.5,
            CompletionTier.IMPORTANT: 1.0,
            CompletionTier.OPTIONAL: 0.5
        }
        
        tier_multiplier = tier_multipliers.get(tier, 1.0)
        return category_weight * tier_multiplier
    
    def _calculate_technical_complexity_weight(self, component: Component) -> float:
        """Calculate technical complexity weight"""
        return 1.0  # Simplified implementation
    
    def _apply_adjustment_factors(self, base_completion: float, 
                                quality_factor: float, dependency_factor: float) -> float:
        """Apply quality and dependency adjustment factors"""
        adjusted = base_completion * quality_factor * dependency_factor
        return max(base_completion * 0.5, min(base_completion * 1.1, adjusted))
    
    def _calculate_confidence_level(self, evaluation: ComponentEvaluation,
                                  quality_assessment: Optional[QualityAssessmentResult],
                                  dependency_factor: float) -> float:
        """Calculate confidence level in the completion score"""
        confidence_factors = []
        
        if evaluation.status == EvaluationStatus.PASSED:
            confidence_factors.append(0.9)
        elif evaluation.status == EvaluationStatus.WARNING:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)
        
        if quality_assessment:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)
        
        confidence_factors.append(dependency_factor)
        
        return statistics.mean(confidence_factors)
    
    def _calculate_category_scores(self, component_scores: List[ComponentCompletionScore]) -> Dict[str, float]:
        """Calculate completion scores by category"""
        category_scores = {}
        category_groups = {}
        
        for score in component_scores:
            category = score.component.category.value
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(score)
        
        for category, scores in category_groups.items():
            completions = [s.completion_percentage for s in scores]
            category_scores[category] = statistics.mean(completions)
        
        return category_scores
    
    def _calculate_tier_scores(self, component_scores: List[ComponentCompletionScore]) -> Dict[str, float]:
        """Calculate completion scores by tier"""
        tier_scores = {}
        tier_groups = {}
        
        for score in component_scores:
            tier = score.tier.value
            if tier not in tier_groups:
                tier_groups[tier] = []
            tier_groups[tier].append(score)
        
        for tier, scores in tier_groups.items():
            completions = [s.completion_percentage for s in scores]
            tier_scores[tier] = statistics.mean(completions)
        
        return tier_scores
    
    def _analyze_completion_trends(self, component_scores: List[ComponentCompletionScore]) -> List[CompletionTrend]:
        """Analyze completion trends for components"""
        trends = []
        
        for component_score in component_scores:
            trend = CompletionTrend(
                component_name=component_score.component.name,
                current_completion=component_score.completion_percentage,
                previous_completion=component_score.completion_percentage,
                trend_direction=TrendDirection.UNKNOWN,
                change_rate=0.0,
                projected_completion_date=None,
                confidence_interval=(component_score.completion_percentage, component_score.completion_percentage)
            )
            trends.append(trend)
        
        return trends
    
    def _generate_completion_recommendations(self, system_score: SystemCompletionScore,
                                           component_scores: List[ComponentCompletionScore],
                                           trends: List[CompletionTrend]) -> List[str]:
        """Generate recommendations for improving completion"""
        recommendations = []
        
        if system_score.overall_completion < 70.0:
            recommendations.append(f"System completion is {system_score.overall_completion:.1f}% - focus on critical components first")
        
        if system_score.critical_completion < 90.0:
            recommendations.append(f"Critical components at {system_score.critical_completion:.1f}% - these must reach 100% for production")
        
        return recommendations
    
    def _identify_risk_factors(self, system_score: SystemCompletionScore,
                             component_scores: List[ComponentCompletionScore],
                             trends: List[CompletionTrend]) -> List[str]:
        """Identify risk factors that could impact completion"""
        risk_factors = []
        
        critical_components = [cs for cs in component_scores if cs.tier == CompletionTier.CRITICAL]
        incomplete_critical = [cs for cs in critical_components if cs.completion_percentage < 90.0]
        
        if incomplete_critical:
            risk_factors.append(f"Risk: {len(incomplete_critical)} critical components incomplete")
        
        return risk_factors
    
    def _project_milestone_dates(self, component_scores: List[ComponentCompletionScore],
                               trends: List[CompletionTrend]) -> Dict[str, datetime]:
        """Project milestone completion dates"""
        return {}  # Simplified implementation