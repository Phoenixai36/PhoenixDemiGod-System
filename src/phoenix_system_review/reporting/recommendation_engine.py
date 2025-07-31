"""
Recommendation Engine for Phoenix Hydra System Review Tool

Implements strategic recommendation generation based on gaps and priorities,
creates resource allocation suggestions, and adds risk assessment for production deployment.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta

from ..models.data_models import (
    AssessmentResults, Gap, Priority, ComponentCategory, ImpactLevel
)
from ..assessment.gap_analyzer import GapAnalysisResult, IdentifiedGap, GapSeverity, GapType
from ..assessment.priority_ranker import PriorityRankingResult, PriorityScore, PriorityLevel, EffortLevel
from ..assessment.completion_calculator import CompletionTier


class RecommendationType(Enum):
    """Types of recommendations"""
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_MITIGATION = "risk_mitigation"
    QUICK_WIN = "quick_win"
    CRITICAL_PATH = "critical_path"


class RecommendationPriority(Enum):
    """Priority levels for recommendations"""
    IMMEDIATE = "immediate"      # Must be done now
    HIGH = "high"               # Should be done soon
    MEDIUM = "medium"           # Should be done eventually
    LOW = "low"                 # Nice to have


class RiskLevel(Enum):
    """Risk levels for production deployment"""
    CRITICAL = "critical"       # Cannot deploy to production
    HIGH = "high"              # High risk deployment
    MEDIUM = "medium"          # Moderate risk deployment
    LOW = "low"                # Low risk deployment
    MINIMAL = "minimal"        # Very low risk deployment


@dataclass
class Recommendation:
    """Individual recommendation with context and rationale"""
    id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    rationale: str
    impact_description: str
    effort_estimate_hours: int
    affected_components: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    risks_if_ignored: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    resources_required: List[str] = field(default_factory=list)
    timeline_estimate: Optional[str] = None
    business_value: str = ""
    technical_complexity: str = ""
    created_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceAllocation:
    """Resource allocation recommendation"""
    resource_type: str
    allocation_percentage: float
    justification: str
    components: List[str] = field(default_factory=list)
    timeline: str = ""
    skills_required: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Production deployment risk assessment"""
    overall_risk_level: RiskLevel
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    deployment_readiness_score: float = 0.0
    critical_blockers: List[str] = field(default_factory=list)
    recommended_deployment_timeline: Optional[datetime] = None
    rollback_plan: List[str] = field(default_factory=list)
    monitoring_requirements: List[str] = field(default_factory=list)


@dataclass
class RecommendationReport:
    """Complete recommendation report"""
    strategic_recommendations: List[Recommendation] = field(default_factory=list)
    tactical_recommendations: List[Recommendation] = field(default_factory=list)
    operational_recommendations: List[Recommendation] = field(default_factory=list)
    quick_wins: List[Recommendation] = field(default_factory=list)
    critical_path_recommendations: List[Recommendation] = field(default_factory=list)
    resource_allocation: List[ResourceAllocation] = field(default_factory=list)
    risk_assessment: Optional[RiskAssessment] = None
    executive_summary: str = ""
    implementation_roadmap: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    generated_timestamp: datetime = field(default_factory=datetime.now)


class RecommendationEngine:
    """
    Generates strategic recommendations for Phoenix Hydra system completion.
    
    Analyzes gaps, priorities, and system state to provide actionable recommendations
    for achieving 100% completion and production readiness.
    """
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.logger = logging.getLogger(__name__)
        
        # Recommendation templates
        self.recommendation_templates = self._define_recommendation_templates()
        
        # Risk assessment criteria
        self.risk_criteria = self._define_risk_criteria()
        
        # Resource allocation models
        self.resource_models = self._define_resource_models()
        
        # Business impact weights
        self.business_weights = self._define_business_weights()
    
    def generate_recommendations(self, 
                               assessment_results: AssessmentResults,
                               gap_analysis: GapAnalysisResult,
                               priority_ranking: PriorityRankingResult) -> RecommendationReport:
        """
        Generate comprehensive recommendations based on system analysis.
        
        Args:
            assessment_results: Complete assessment results
            gap_analysis: Gap analysis results
            priority_ranking: Priority ranking results
            
        Returns:
            RecommendationReport with strategic recommendations
        """
        try:
            # Generate strategic recommendations
            strategic_recs = self._generate_strategic_recommendations(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Generate tactical recommendations
            tactical_recs = self._generate_tactical_recommendations(
                gap_analysis, priority_ranking
            )
            
            # Generate operational recommendations
            operational_recs = self._generate_operational_recommendations(
                assessment_results, gap_analysis
            )
            
            # Identify quick wins
            quick_wins = self._identify_quick_wins(priority_ranking, gap_analysis)
            
            # Generate critical path recommendations
            critical_path_recs = self._generate_critical_path_recommendations(
                priority_ranking, gap_analysis
            )
            
            # Generate resource allocation recommendations
            resource_allocation = self._generate_resource_allocation(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Perform risk assessment
            risk_assessment = self._perform_risk_assessment(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                strategic_recs, tactical_recs, quick_wins, risk_assessment
            )
            
            # Create implementation roadmap
            implementation_roadmap = self._create_implementation_roadmap(
                strategic_recs, tactical_recs, operational_recs, priority_ranking
            )
            
            # Define success metrics
            success_metrics = self._define_success_metrics(
                assessment_results, gap_analysis
            )
            
            return RecommendationReport(
                strategic_recommendations=strategic_recs,
                tactical_recommendations=tactical_recs,
                operational_recommendations=operational_recs,
                quick_wins=quick_wins,
                critical_path_recommendations=critical_path_recs,
                resource_allocation=resource_allocation,
                risk_assessment=risk_assessment,
                executive_summary=executive_summary,
                implementation_roadmap=implementation_roadmap,
                success_metrics=success_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return RecommendationReport(
                executive_summary=f"Error generating recommendations: {e}"
            )
    
    def format_recommendations_markdown(self, report: RecommendationReport) -> str:
        """
        Format recommendations as markdown report.
        
        Args:
            report: RecommendationReport to format
            
        Returns:
            Formatted markdown string
        """
        try:
            lines = []
            
            # Header
            lines.append("# Phoenix Hydra System Recommendations")
            lines.append("")
            lines.append(f"*Generated: {report.generated_timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
            lines.append("")
            
            # Executive summary
            lines.append("## Executive Summary")
            lines.append("")
            lines.append(report.executive_summary)
            lines.append("")
            
            # Risk assessment
            if report.risk_assessment:
                lines.append("## Risk Assessment")
                lines.append("")
                lines.append(f"**Overall Risk Level:** {self._get_risk_emoji(report.risk_assessment.overall_risk_level)} {report.risk_assessment.overall_risk_level.value.title()}")
                lines.append(f"**Deployment Readiness Score:** {report.risk_assessment.deployment_readiness_score:.1f}%")
                lines.append("")
                
                if report.risk_assessment.critical_blockers:
                    lines.append("### Critical Blockers")
                    for blocker in report.risk_assessment.critical_blockers:
                        lines.append(f"- 🚫 {blocker}")
                    lines.append("")
                
                if report.risk_assessment.risk_factors:
                    lines.append("### Risk Factors")
                    for factor in report.risk_assessment.risk_factors:
                        lines.append(f"- ⚠️ {factor}")
                    lines.append("")
                
                if report.risk_assessment.mitigation_strategies:
                    lines.append("### Mitigation Strategies")
                    for strategy in report.risk_assessment.mitigation_strategies:
                        lines.append(f"- ✅ {strategy}")
                    lines.append("")
            
            # Strategic recommendations
            if report.strategic_recommendations:
                lines.append("## Strategic Recommendations")
                lines.append("")
                for rec in report.strategic_recommendations:
                    lines.append(self._format_recommendation_markdown(rec))
                    lines.append("")
            
            # Quick wins
            if report.quick_wins:
                lines.append("## Quick Wins")
                lines.append("")
                lines.append("High-impact, low-effort recommendations to start with:")
                lines.append("")
                for rec in report.quick_wins:
                    lines.append(self._format_recommendation_markdown(rec))
                    lines.append("")
            
            # Critical path
            if report.critical_path_recommendations:
                lines.append("## Critical Path")
                lines.append("")
                lines.append("Essential recommendations that block other work:")
                lines.append("")
                for rec in report.critical_path_recommendations:
                    lines.append(self._format_recommendation_markdown(rec))
                    lines.append("")
            
            # Implementation roadmap
            if report.implementation_roadmap:
                lines.append("## Implementation Roadmap")
                lines.append("")
                for i, phase in enumerate(report.implementation_roadmap, 1):
                    lines.append(f"{i}. {phase}")
                lines.append("")
            
            # Success metrics
            if report.success_metrics:
                lines.append("## Success Metrics")
                lines.append("")
                for metric in report.success_metrics:
                    lines.append(f"- {metric}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting recommendations: {e}")
            return f"Error formatting recommendations: {e}"
    
    def _generate_strategic_recommendations(self, 
                                          assessment_results: AssessmentResults,
                                          gap_analysis: GapAnalysisResult,
                                          priority_ranking: PriorityRankingResult) -> List[Recommendation]:
        """Generate strategic-level recommendations"""
        recommendations = []
        
        # Overall completion strategy
        overall_completion = assessment_results.overall_completion
        
        if overall_completion < 70:
            rec = Recommendation(
                id="strategic_foundation",
                title="Focus on Foundation Components",
                description="Prioritize core infrastructure and essential components before adding features",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.IMMEDIATE,
                rationale=f"System is at {overall_completion:.1f}% completion, requiring foundational work",
                impact_description="Establishes stable foundation for future development",
                effort_estimate_hours=160,
                success_criteria=[
                    "Core infrastructure components > 80% complete",
                    "Critical dependencies resolved",
                    "System stability improved"
                ],
                business_value="Reduces technical debt and enables faster feature development",
                technical_complexity="High - requires architectural decisions"
            )
            recommendations.append(rec)
        
        elif overall_completion < 85:
            rec = Recommendation(
                id="strategic_integration",
                title="Focus on Integration and Quality",
                description="Integrate components and improve overall system quality",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.HIGH,
                rationale=f"System at {overall_completion:.1f}% needs integration focus",
                impact_description="Improves system reliability and user experience",
                effort_estimate_hours=120,
                success_criteria=[
                    "Component integration > 90% complete",
                    "Quality metrics improved",
                    "User acceptance criteria met"
                ],
                business_value="Improves product quality and reduces support burden",
                technical_complexity="Medium - requires coordination across components"
            )
            recommendations.append(rec)
        
        elif overall_completion < 95:
            rec = Recommendation(
                id="strategic_production_prep",
                title="Prepare for Production Deployment",
                description="Focus on production readiness, security, and monitoring",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.HIGH,
                rationale=f"System at {overall_completion:.1f}% needs production preparation",
                impact_description="Enables safe production deployment",
                effort_estimate_hours=80,
                success_criteria=[
                    "Security audit passed",
                    "Monitoring implemented",
                    "Deployment automation complete"
                ],
                business_value="Enables revenue generation and market entry",
                technical_complexity="Medium - requires operational expertise"
            )
            recommendations.append(rec)
        
        # Monetization strategy
        monetization_gaps = [gap for gap in gap_analysis.identified_gaps 
                           if gap.category == ComponentCategory.MONETIZATION]
        
        if monetization_gaps:
            rec = Recommendation(
                id="strategic_monetization",
                title="Accelerate Monetization Implementation",
                description="Prioritize revenue-generating components to achieve €400k+ target",
                recommendation_type=RecommendationType.STRATEGIC,
                priority=RecommendationPriority.IMMEDIATE,
                rationale="Monetization gaps directly impact revenue targets",
                impact_description="Enables revenue generation and business sustainability",
                effort_estimate_hours=sum(gap.effort_estimate_hours for gap in monetization_gaps),
                affected_components=[gap.component_name for gap in monetization_gaps],
                success_criteria=[
                    "Revenue tracking operational",
                    "Affiliate programs active",
                    "Grant applications submitted"
                ],
                business_value="Direct revenue impact - €400k+ target",
                technical_complexity="Medium - requires business logic implementation"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_tactical_recommendations(self, 
                                         gap_analysis: GapAnalysisResult,
                                         priority_ranking: PriorityRankingResult) -> List[Recommendation]:
        """Generate tactical-level recommendations"""
        recommendations = []
        
        # Critical gaps
        if gap_analysis.critical_gaps:
            rec = Recommendation(
                id="tactical_critical_gaps",
                title="Address Critical Gaps Immediately",
                description=f"Resolve {len(gap_analysis.critical_gaps)} critical gaps blocking progress",
                recommendation_type=RecommendationType.TACTICAL,
                priority=RecommendationPriority.IMMEDIATE,
                rationale="Critical gaps block system functionality and deployment",
                impact_description="Removes blockers and enables continued development",
                effort_estimate_hours=sum(gap.effort_estimate_hours for gap in gap_analysis.critical_gaps),
                affected_components=[gap.component_name for gap in gap_analysis.critical_gaps],
                success_criteria=["All critical gaps resolved", "System functionality restored"],
                risks_if_ignored=["System instability", "Deployment blocked", "Technical debt accumulation"],
                business_value="Unblocks development and reduces risk",
                technical_complexity="High - requires immediate attention"
            )
            recommendations.append(rec)
        
        # Missing components
        if gap_analysis.missing_components:
            rec = Recommendation(
                id="tactical_missing_components",
                title="Implement Missing Components",
                description=f"Develop {len(gap_analysis.missing_components)} missing system components",
                recommendation_type=RecommendationType.TACTICAL,
                priority=RecommendationPriority.HIGH,
                rationale="Missing components prevent system completion",
                impact_description="Completes system architecture and functionality",
                effort_estimate_hours=200,  # Estimated based on typical component complexity
                affected_components=gap_analysis.missing_components,
                success_criteria=["All required components implemented", "Integration tests passing"],
                implementation_steps=[
                    "Prioritize components by business impact",
                    "Design component interfaces",
                    "Implement core functionality",
                    "Add integration tests",
                    "Deploy and validate"
                ],
                business_value="Enables full system functionality",
                technical_complexity="High - requires new development"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_operational_recommendations(self, 
                                            assessment_results: AssessmentResults,
                                            gap_analysis: GapAnalysisResult) -> List[Recommendation]:
        """Generate operational-level recommendations"""
        recommendations = []
        
        # Testing and quality
        testing_gaps = [gap for gap in gap_analysis.identified_gaps 
                       if gap.gap_type == GapType.TESTING_GAP]
        
        if testing_gaps:
            rec = Recommendation(
                id="operational_testing",
                title="Improve Testing Coverage",
                description="Increase test coverage and implement quality gates",
                recommendation_type=RecommendationType.OPERATIONAL,
                priority=RecommendationPriority.MEDIUM,
                rationale="Testing gaps increase deployment risk",
                impact_description="Improves system reliability and reduces bugs",
                effort_estimate_hours=sum(gap.effort_estimate_hours for gap in testing_gaps),
                success_criteria=["Test coverage > 80%", "Quality gates implemented"],
                business_value="Reduces support costs and improves reliability",
                technical_complexity="Medium - requires testing expertise"
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _identify_quick_wins(self, 
                           priority_ranking: PriorityRankingResult,
                           gap_analysis: GapAnalysisResult) -> List[Recommendation]:
        """Identify quick win recommendations"""
        recommendations = []
        
        # From priority ranking quick wins
        for task_id in priority_ranking.quick_wins[:3]:  # Top 3 quick wins
            score = next((s for s in priority_ranking.priority_scores 
                         if s.component_name in task_id), None)
            if score:
                rec = Recommendation(
                    id=f"quick_win_{score.component_name}",
                    title=f"Quick Win: {score.component_name}",
                    description=f"High-impact, low-effort improvement for {score.component_name}",
                    recommendation_type=RecommendationType.QUICK_WIN,
                    priority=RecommendationPriority.HIGH,
                    rationale=f"High ROI: {score.roi_score:.1f}/100",
                    impact_description=f"Business impact: {score.business_impact_score:.1f}/100",
                    effort_estimate_hours=score.effort_hours,
                    affected_components=[score.component_name],
                    success_criteria=[f"{score.component_name} improvement delivered"],
                    business_value=f"ROI: {score.roi_score:.1f}/100",
                    technical_complexity=f"Effort: {score.effort_estimate.value}"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_critical_path_recommendations(self, 
                                              priority_ranking: PriorityRankingResult,
                                              gap_analysis: GapAnalysisResult) -> List[Recommendation]:
        """Generate critical path recommendations"""
        recommendations = []
        
        # Critical path components
        for component in priority_ranking.critical_path[:3]:  # Top 3 critical path items
            score = next((s for s in priority_ranking.priority_scores 
                         if s.component_name == component), None)
            if score:
                rec = Recommendation(
                    id=f"critical_path_{component}",
                    title=f"Critical Path: {component}",
                    description=f"Essential component that blocks other work: {component}",
                    recommendation_type=RecommendationType.CRITICAL_PATH,
                    priority=RecommendationPriority.IMMEDIATE,
                    rationale="Blocks other components and system progress",
                    impact_description="Unblocks dependent components and enables parallel work",
                    effort_estimate_hours=score.effort_hours,
                    affected_components=[component],
                    prerequisites=score.dependencies,
                    success_criteria=[f"{component} completed and integrated"],
                    risks_if_ignored=["Blocks dependent work", "Delays overall completion"],
                    business_value="Unblocks development pipeline",
                    technical_complexity=f"Complexity: {score.technical_complexity_score:.1f}/100"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_resource_allocation(self, 
                                    assessment_results: AssessmentResults,
                                    gap_analysis: GapAnalysisResult,
                                    priority_ranking: PriorityRankingResult) -> List[ResourceAllocation]:
        """Generate resource allocation recommendations"""
        allocations = []
        
        total_effort = gap_analysis.total_effort_estimate
        
        if total_effort > 0:
            # Development resources
            dev_effort = sum(gap.effort_estimate_hours for gap in gap_analysis.identified_gaps 
                            if gap.gap_type in [GapType.MISSING_COMPONENT, GapType.INCOMPLETE_IMPLEMENTATION])
            
            if dev_effort > 0:
                allocation = ResourceAllocation(
                    resource_type="Development Team",
                    allocation_percentage=(dev_effort / total_effort) * 100,
                    justification="Core development work for missing and incomplete components",
                    timeline="2-4 weeks",
                    skills_required=["Python", "JavaScript", "System Architecture", "API Development"]
                )
                allocations.append(allocation)
        
        return allocations
    
    def _perform_risk_assessment(self, 
                                assessment_results: AssessmentResults,
                                gap_analysis: GapAnalysisResult,
                                priority_ranking: PriorityRankingResult) -> RiskAssessment:
        """Perform production deployment risk assessment"""
        risk_factors = []
        mitigation_strategies = []
        critical_blockers = []
        
        # Overall completion risk
        overall_completion = assessment_results.overall_completion
        if overall_completion < 70:
            risk_factors.append(f"Low overall completion ({overall_completion:.1f}%)")
            mitigation_strategies.append("Focus on core infrastructure completion")
        
        # Critical gaps risk
        if gap_analysis.critical_gaps:
            critical_count = len(gap_analysis.critical_gaps)
            risk_factors.append(f"{critical_count} critical gaps identified")
            critical_blockers.extend([gap.title for gap in gap_analysis.critical_gaps])
            mitigation_strategies.append("Resolve all critical gaps before deployment")
        
        # Determine overall risk level
        if overall_completion < 70 or len(gap_analysis.critical_gaps) > 3:
            risk_level = RiskLevel.CRITICAL
        elif overall_completion < 85 or len(gap_analysis.critical_gaps) > 1:
            risk_level = RiskLevel.HIGH
        elif overall_completion < 95:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Calculate deployment readiness score
        readiness_score = min(100.0, overall_completion - (len(gap_analysis.critical_gaps) * 10))
        
        # Recommended deployment timeline
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            deployment_timeline = datetime.now() + timedelta(weeks=4)
        elif risk_level == RiskLevel.MEDIUM:
            deployment_timeline = datetime.now() + timedelta(weeks=2)
        else:
            deployment_timeline = datetime.now() + timedelta(weeks=1)
        
        return RiskAssessment(
            overall_risk_level=risk_level,
            risk_factors=risk_factors,
            mitigation_strategies=mitigation_strategies,
            deployment_readiness_score=readiness_score,
            critical_blockers=critical_blockers,
            recommended_deployment_timeline=deployment_timeline,
            rollback_plan=[
                "Maintain previous version deployment",
                "Database backup and restore procedures",
                "Configuration rollback scripts"
            ],
            monitoring_requirements=[
                "Application performance monitoring",
                "Error rate and exception tracking",
                "Resource utilization monitoring"
            ]
        )
    
    def _generate_executive_summary(self, 
                                  strategic_recs: List[Recommendation],
                                  tactical_recs: List[Recommendation],
                                  quick_wins: List[Recommendation],
                                  risk_assessment: RiskAssessment) -> str:
        """Generate executive summary of recommendations"""
        lines = []
        
        # Overall assessment
        lines.append(f"**Risk Level:** {risk_assessment.overall_risk_level.value.title()}")
        lines.append(f"**Deployment Readiness:** {risk_assessment.deployment_readiness_score:.1f}%")
        lines.append("")
        
        # Key recommendations
        lines.append("**Key Recommendations:**")
        
        # Strategic priorities
        if strategic_recs:
            top_strategic = strategic_recs[0]
            lines.append(f"- **Strategic Priority:** {top_strategic.title}")
        
        # Quick wins
        if quick_wins:
            lines.append(f"- **Quick Wins:** {len(quick_wins)} high-impact, low-effort opportunities identified")
        
        # Critical blockers
        if risk_assessment.critical_blockers:
            lines.append(f"- **Critical Blockers:** {len(risk_assessment.critical_blockers)} items must be resolved before deployment")
        
        lines.append("")
        
        # Timeline
        if risk_assessment.recommended_deployment_timeline:
            timeline = risk_assessment.recommended_deployment_timeline.strftime('%Y-%m-%d')
            lines.append(f"**Recommended Deployment Timeline:** {timeline}")
        
        return "\n".join(lines)
    
    def _create_implementation_roadmap(self, 
                                     strategic_recs: List[Recommendation],
                                     tactical_recs: List[Recommendation],
                                     operational_recs: List[Recommendation],
                                     priority_ranking: PriorityRankingResult) -> List[str]:
        """Create implementation roadmap"""
        roadmap = []
        
        # Phase 1: Critical and Strategic
        phase1_items = []
        if strategic_recs:
            phase1_items.extend([rec.title for rec in strategic_recs 
                               if rec.priority == RecommendationPriority.IMMEDIATE])
        if tactical_recs:
            phase1_items.extend([rec.title for rec in tactical_recs 
                               if rec.priority == RecommendationPriority.IMMEDIATE])
        
        if phase1_items:
            roadmap.append(f"**Phase 1 (Immediate):** {', '.join(phase1_items[:3])}")
        
        # Phase 2: High Priority
        phase2_items = []
        if strategic_recs:
            phase2_items.extend([rec.title for rec in strategic_recs 
                               if rec.priority == RecommendationPriority.HIGH])
        if tactical_recs:
            phase2_items.extend([rec.title for rec in tactical_recs 
                               if rec.priority == RecommendationPriority.HIGH])
        
        if phase2_items:
            roadmap.append(f"**Phase 2 (High Priority):** {', '.join(phase2_items[:3])}")
        
        return roadmap
    
    def _define_success_metrics(self, 
                              assessment_results: AssessmentResults,
                              gap_analysis: GapAnalysisResult) -> List[str]:
        """Define success metrics for recommendations"""
        return [
            f"Overall system completion > 95% (currently {assessment_results.overall_completion:.1f}%)",
            f"Critical gaps resolved (currently {len(gap_analysis.critical_gaps)})",
            "All security vulnerabilities addressed",
            "Test coverage > 80%",
            "Production deployment successful",
            "Revenue tracking operational"
        ]
    
    # Helper methods
    def _format_recommendation_markdown(self, rec: Recommendation) -> str:
        """Format individual recommendation as markdown"""
        lines = []
        
        priority_emoji = self._get_priority_emoji(rec.priority)
        lines.append(f"### {priority_emoji} {rec.title}")
        lines.append("")
        lines.append(f"**Description:** {rec.description}")
        lines.append(f"**Rationale:** {rec.rationale}")
        lines.append(f"**Impact:** {rec.impact_description}")
        lines.append(f"**Effort:** {rec.effort_estimate_hours} hours")
        
        if rec.business_value:
            lines.append(f"**Business Value:** {rec.business_value}")
        
        if rec.affected_components:
            lines.append(f"**Affected Components:** {', '.join(rec.affected_components)}")
        
        if rec.success_criteria:
            lines.append("**Success Criteria:**")
            for criterion in rec.success_criteria:
                lines.append(f"- {criterion}")
        
        if rec.risks_if_ignored:
            lines.append("**Risks if Ignored:**")
            for risk in rec.risks_if_ignored:
                lines.append(f"- ⚠️ {risk}")
        
        return "\n".join(lines)
    
    def _get_priority_emoji(self, priority: RecommendationPriority) -> str:
        """Get emoji for recommendation priority"""
        emojis = {
            RecommendationPriority.IMMEDIATE: "🔴",
            RecommendationPriority.HIGH: "🟠",
            RecommendationPriority.MEDIUM: "🟡",
            RecommendationPriority.LOW: "🟢"
        }
        return emojis.get(priority, "⚪")
    
    def _get_risk_emoji(self, risk_level: RiskLevel) -> str:
        """Get emoji for risk level"""
        emojis = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
            RiskLevel.MINIMAL: "✅"
        }
        return emojis.get(risk_level, "⚪")
    
    def _define_recommendation_templates(self) -> Dict[str, Dict[str, Any]]:
        """Define recommendation templates"""
        return {
            "foundation": {
                "title": "Strengthen System Foundation",
                "description": "Focus on core infrastructure and essential components",
                "type": RecommendationType.STRATEGIC,
                "priority": RecommendationPriority.IMMEDIATE
            },
            "integration": {
                "title": "Improve System Integration",
                "description": "Enhance component integration and system cohesion",
                "type": RecommendationType.STRATEGIC,
                "priority": RecommendationPriority.HIGH
            }
        }
    
    def _define_risk_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Define risk assessment criteria"""
        return {
            "completion_thresholds": {
                "critical": 70,
                "high": 85,
                "medium": 95
            },
            "gap_thresholds": {
                "critical_gaps": 3,
                "security_gaps": 1,
                "testing_gaps": 5
            }
        }
    
    def _define_resource_models(self) -> Dict[str, Dict[str, Any]]:
        """Define resource allocation models"""
        return {
            "development": {
                "skills": ["Python", "JavaScript", "API Development"],
                "capacity_hours_per_week": 40,
                "efficiency_factor": 0.8
            }
        }
    
    def _define_business_weights(self) -> Dict[ComponentCategory, float]:
        """Define business impact weights by category"""
        return {
            ComponentCategory.MONETIZATION: 5.0,
            ComponentCategory.INFRASTRUCTURE: 4.0,
            ComponentCategory.SECURITY: 3.5,
            ComponentCategory.AUTOMATION: 3.0,
            ComponentCategory.TESTING: 2.5,
            ComponentCategory.DOCUMENTATION: 2.0
        }