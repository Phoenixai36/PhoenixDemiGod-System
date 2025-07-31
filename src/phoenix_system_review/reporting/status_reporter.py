"""
Status Reporter for Phoenix Hydra System Review Tool

Creates executive summary report generation, builds detailed component breakdown reporting,
and adds completion percentage visualization.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import json

from ..models.data_models import (
    AssessmentResults, CompletionScore, Component, ComponentCategory, 
    Priority, ImpactLevel
)
from ..assessment.gap_analyzer import GapAnalysisResult, IdentifiedGap, GapSeverity
from ..assessment.priority_ranker import PriorityRankingResult, PriorityScore, PriorityLevel
from ..assessment.completion_calculator import ComponentCompletionScore, CompletionTier


class ReportType(Enum):
    """Types of status reports"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_BREAKDOWN = "detailed_breakdown"
    COMPLETION_DASHBOARD = "completion_dashboard"
    GAP_ANALYSIS = "gap_analysis"
    PRIORITY_MATRIX = "priority_matrix"
    PROGRESS_TRACKING = "progress_tracking"


class ReportFormat(Enum):
    """Report output formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    TEXT = "text"


@dataclass
class StatusReport:
    """Complete status report with multiple sections"""
    report_type: ReportType
    title: str
    executive_summary: str
    detailed_sections: Dict[str, str] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    visualizations: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionVisualization:
    """Completion percentage visualization data"""
    overall_completion: float
    category_completion: Dict[str, float] = field(default_factory=dict)
    component_completion: Dict[str, float] = field(default_factory=dict)
    completion_trend: List[Tuple[datetime, float]] = field(default_factory=list)
    progress_bars: Dict[str, str] = field(default_factory=dict)
    completion_charts: Dict[str, str] = field(default_factory=dict)


class StatusReporter:
    """
    Generates comprehensive status reports for Phoenix Hydra system review.
    
    Creates executive summaries, detailed breakdowns, and completion visualizations
    to communicate system status to different stakeholders.
    """
    
    def __init__(self):
        """Initialize status reporter"""
        self.logger = logging.getLogger(__name__)
        
        # Report templates
        self.report_templates = self._define_report_templates()
        
        # Visualization settings
        self.visualization_settings = self._define_visualization_settings()
        
        # Stakeholder configurations
        self.stakeholder_configs = self._define_stakeholder_configs()
    
    def create_status_report(self, 
                           assessment_results: AssessmentResults,
                           gap_analysis: Optional[GapAnalysisResult] = None,
                           priority_ranking: Optional[PriorityRankingResult] = None,
                           report_type: ReportType = ReportType.EXECUTIVE_SUMMARY,
                           format_type: ReportFormat = ReportFormat.MARKDOWN) -> StatusReport:
        """
        Create comprehensive status report.
        
        Args:
            assessment_results: Complete assessment results
            gap_analysis: Optional gap analysis results
            priority_ranking: Optional priority ranking results
            report_type: Type of report to generate
            format_type: Output format for the report
            
        Returns:
            StatusReport with formatted content
        """
        try:
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Generate detailed sections based on report type
            detailed_sections = self._generate_detailed_sections(
                assessment_results, gap_analysis, priority_ranking, report_type
            )
            
            # Calculate metrics
            metrics = self._calculate_report_metrics(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Generate visualizations
            visualizations = self._generate_visualizations(
                assessment_results, gap_analysis, priority_ranking, format_type
            )
            
            # Generate recommendations
            recommendations = self._generate_report_recommendations(
                assessment_results, gap_analysis, priority_ranking
            )
            
            # Create metadata
            metadata = self._create_report_metadata(
                assessment_results, gap_analysis, priority_ranking, report_type
            )
            
            report = StatusReport(
                report_type=report_type,
                title=self._generate_report_title(report_type),
                executive_summary=executive_summary,
                detailed_sections=detailed_sections,
                metrics=metrics,
                visualizations=visualizations,
                recommendations=recommendations,
                metadata=metadata
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error creating status report: {e}")
            return self._create_error_report(str(e))
    
    def format_report(self, report: StatusReport, format_type: ReportFormat) -> str:
        """
        Format status report in specified format.
        
        Args:
            report: StatusReport to format
            format_type: Output format
            
        Returns:
            Formatted report string
        """
        try:
            if format_type == ReportFormat.MARKDOWN:
                return self._format_markdown_report(report)
            elif format_type == ReportFormat.HTML:
                return self._format_html_report(report)
            elif format_type == ReportFormat.JSON:
                return self._format_json_report(report)
            elif format_type == ReportFormat.TEXT:
                return self._format_text_report(report)
            else:
                return self._format_markdown_report(report)  # Default to markdown
                
        except Exception as e:
            self.logger.error(f"Error formatting report: {e}")
            return f"Error formatting report: {e}"
    
    def generate_executive_summary(self, assessment_results: AssessmentResults) -> str:
        """
        Generate executive summary for stakeholders.
        
        Args:
            assessment_results: Assessment results to summarize
            
        Returns:
            Executive summary string
        """
        try:
            return self._generate_executive_summary(assessment_results)
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            return f"Error generating executive summary: {e}"
    
    def create_completion_dashboard(self, 
                                  assessment_results: AssessmentResults,
                                  format_type: ReportFormat = ReportFormat.MARKDOWN) -> str:
        """
        Create completion percentage dashboard.
        
        Args:
            assessment_results: Assessment results
            format_type: Output format
            
        Returns:
            Formatted completion dashboard
        """
        try:
            # Create completion visualization
            visualization = self._create_completion_visualization(assessment_results)
            
            # Format dashboard based on format type
            if format_type == ReportFormat.MARKDOWN:
                return self._generate_completion_dashboard_section(assessment_results)
            elif format_type == ReportFormat.HTML:
                return self._generate_completion_dashboard_section(assessment_results)
            else:
                return self._generate_completion_dashboard_section(assessment_results)
                
        except Exception as e:
            self.logger.error(f"Error creating completion dashboard: {e}")
            return f"Error creating completion dashboard: {e}"
    
    def _generate_executive_summary(self, 
                                  assessment_results: AssessmentResults,
                                  gap_analysis: Optional[GapAnalysisResult] = None,
                                  priority_ranking: Optional[PriorityRankingResult] = None) -> str:
        """Generate executive summary section"""
        lines = []
        
        # Overall status
        overall_completion = assessment_results.overall_completion
        status_emoji = self._get_status_emoji(overall_completion)
        
        lines.append(f"## Executive Summary {status_emoji}")
        lines.append("")
        lines.append(f"**Overall System Completion: {overall_completion:.1f}%**")
        lines.append("")
        
        # Status assessment
        if overall_completion >= 95:
            lines.append("✅ **Status: Production Ready** - System is ready for deployment")
        elif overall_completion >= 85:
            lines.append("🟡 **Status: Near Completion** - Minor issues remain before production")
        elif overall_completion >= 70:
            lines.append("🟠 **Status: Development Phase** - Significant work remains")
        else:
            lines.append("🔴 **Status: Early Development** - Major components missing or incomplete")
        
        lines.append("")
        
        # Key metrics
        lines.append("### Key Metrics")
        lines.append("")
        
        # Component completion breakdown
        if assessment_results.component_scores:
            completed_components = sum(1 for score in assessment_results.component_scores.values() 
                                     if score.completion_percentage >= 90)
            total_components = len(assessment_results.component_scores)
            lines.append(f"- **Components Complete:** {completed_components}/{total_components} ({completed_components/total_components*100:.1f}%)")
        
        # Gap analysis summary
        if gap_analysis:
            critical_gaps = len(gap_analysis.critical_gaps)
            total_gaps = len(gap_analysis.identified_gaps)
            lines.append(f"- **Critical Issues:** {critical_gaps} critical gaps identified")
            lines.append(f"- **Total Gaps:** {total_gaps} gaps requiring attention")
            lines.append(f"- **Estimated Effort:** {gap_analysis.total_effort_estimate} hours ({gap_analysis.total_effort_estimate/8:.1f} days)")
        
        # Priority ranking summary
        if priority_ranking:
            critical_tasks = len([score for score in priority_ranking.priority_scores 
                                if score.priority_level == PriorityLevel.CRITICAL])
            lines.append(f"- **Critical Priority Tasks:** {critical_tasks}")
            lines.append(f"- **Quick Wins Available:** {len(priority_ranking.quick_wins)}")
        
        lines.append("")
        
        # Category breakdown
        lines.append("### Completion by Category")
        lines.append("")
        
        category_completion = self._calculate_category_completion(assessment_results)
        for category, completion in sorted(category_completion.items(), key=lambda x: x[1], reverse=True):
            progress_bar = self._create_progress_bar(completion)
            lines.append(f"- **{category}:** {completion:.1f}% {progress_bar}")
        
        lines.append("")
        
        # Critical issues
        if gap_analysis and gap_analysis.critical_gaps:
            lines.append("### Critical Issues Requiring Immediate Attention")
            lines.append("")
            for gap in gap_analysis.critical_gaps[:5]:  # Top 5 critical issues
                lines.append(f"- **{gap.component_name}:** {gap.title}")
            
            if len(gap_analysis.critical_gaps) > 5:
                lines.append(f"- *...and {len(gap_analysis.critical_gaps) - 5} more critical issues*")
            
            lines.append("")
        
        # Next steps
        lines.append("### Immediate Next Steps")
        lines.append("")
        
        if priority_ranking and priority_ranking.quick_wins:
            lines.append("**Quick Wins (Start Here):**")
            for task_id in priority_ranking.quick_wins[:3]:
                score = next((s for s in priority_ranking.priority_scores if s.component_name in task_id), None)
                if score:
                    lines.append(f"- {score.component_name} ({score.effort_hours}h)")
            lines.append("")
        
        if priority_ranking and priority_ranking.critical_path:
            lines.append("**Critical Path:**")
            for component in priority_ranking.critical_path[:3]:
                lines.append(f"- {component}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_detailed_sections(self, 
                                  assessment_results: AssessmentResults,
                                  gap_analysis: Optional[GapAnalysisResult],
                                  priority_ranking: Optional[PriorityRankingResult],
                                  report_type: ReportType) -> Dict[str, str]:
        """Generate detailed report sections"""
        sections = {}
        
        if report_type in [ReportType.DETAILED_BREAKDOWN, ReportType.EXECUTIVE_SUMMARY]:
            # Component breakdown
            sections["component_breakdown"] = self._generate_component_breakdown(assessment_results)
            
            # Gap analysis section
            if gap_analysis:
                sections["gap_analysis"] = self._generate_gap_analysis_section(gap_analysis)
            
            # Priority matrix
            if priority_ranking:
                sections["priority_matrix"] = self._generate_priority_matrix_section(priority_ranking)
        
        if report_type == ReportType.COMPLETION_DASHBOARD:
            sections["completion_dashboard"] = self._generate_completion_dashboard_section(assessment_results)
        
        if report_type == ReportType.GAP_ANALYSIS and gap_analysis:
            sections["detailed_gaps"] = self._generate_detailed_gap_section(gap_analysis)
        
        if report_type == ReportType.PRIORITY_MATRIX and priority_ranking:
            sections["detailed_priorities"] = self._generate_detailed_priority_section(priority_ranking)
        
        return sections
    
    def _generate_component_breakdown(self, assessment_results: AssessmentResults) -> str:
        """Generate detailed component breakdown"""
        lines = []
        lines.append("## Component Breakdown")
        lines.append("")
        
        # Group components by category
        components_by_category = {}
        for component_name, score in assessment_results.component_scores.items():
            # Determine category from component name since CompletionScore doesn't have component object
            category = self._determine_category_from_name(component_name)
            if category not in components_by_category:
                components_by_category[category] = []
            components_by_category[category].append((component_name, score))
        
        # Sort categories by importance
        category_order = [
            'infrastructure', 'monetization', 'security', 'automation', 'testing', 'documentation'
        ]
        
        for category in category_order:
            if category in components_by_category:
                lines.append(f"### {category.title()}")
                lines.append("")
                
                # Sort components by completion percentage (lowest first)
                category_components = sorted(
                    components_by_category[category],
                    key=lambda x: x[1].completion_percentage
                )
                
                for component_name, score in category_components:
                    completion = score.completion_percentage
                    status_icon = self._get_completion_icon(completion)
                    progress_bar = self._create_progress_bar(completion)
                    
                    lines.append(f"#### {status_icon} {component_name}")
                    lines.append(f"**Completion:** {completion:.1f}% {progress_bar}")
                    lines.append(f"**Quality Score:** {score.quality_score:.1f}/100")
                    lines.append(f"**Criteria Met:** {score.criteria_met}/{score.criteria_total}")
                    
                    if hasattr(score, 'tier'):
                        lines.append(f"**Priority Tier:** {score.tier.value.title()}")
                    
                    lines.append("")
        
        return "\n".join(lines)
    
    def _generate_gap_analysis_section(self, gap_analysis: GapAnalysisResult) -> str:
        """Generate gap analysis section"""
        lines = []
        lines.append("## Gap Analysis")
        lines.append("")
        
        # Summary statistics
        lines.append("### Summary")
        lines.append("")
        lines.append(f"- **Total Gaps:** {len(gap_analysis.identified_gaps)}")
        lines.append(f"- **Critical Gaps:** {len(gap_analysis.critical_gaps)}")
        lines.append(f"- **Missing Components:** {len(gap_analysis.missing_components)}")
        lines.append(f"- **Incomplete Implementations:** {len(gap_analysis.incomplete_implementations)}")
        lines.append(f"- **Total Effort Estimate:** {gap_analysis.total_effort_estimate} hours")
        lines.append("")
        
        # Gap breakdown by type
        lines.append("### Gaps by Type")
        lines.append("")
        for gap_type, count in gap_analysis.gap_summary.items():
            if count > 0:
                lines.append(f"- **{gap_type.replace('_', ' ').title()}:** {count}")
        lines.append("")
        
        # Critical gaps detail
        if gap_analysis.critical_gaps:
            lines.append("### Critical Gaps")
            lines.append("")
            for gap in gap_analysis.critical_gaps:
                lines.append(f"#### 🔴 {gap.title}")
                lines.append(f"**Component:** {gap.component_name}")
                lines.append(f"**Impact:** {gap.impact_description}")
                lines.append(f"**Effort:** {gap.effort_estimate_hours} hours")
                if gap.dependencies:
                    lines.append(f"**Dependencies:** {', '.join(gap.dependencies)}")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_priority_matrix_section(self, priority_ranking: PriorityRankingResult) -> str:
        """Generate priority matrix section"""
        lines = []
        lines.append("## Priority Matrix")
        lines.append("")
        
        # Priority distribution
        lines.append("### Priority Distribution")
        lines.append("")
        for priority_level, scores in priority_ranking.priority_matrix.items():
            if scores:
                lines.append(f"- **{priority_level.title()}:** {len(scores)} items")
        lines.append("")
        
        # Critical priority items
        critical_items = priority_ranking.priority_matrix.get("critical", [])
        if critical_items:
            lines.append("### Critical Priority Items")
            lines.append("")
            for score in critical_items:
                lines.append(f"#### 🔴 {score.component_name}")
                lines.append(f"**Priority Score:** {score.priority_score:.1f}/100")
                lines.append(f"**Business Impact:** {score.business_impact_score:.1f}/100")
                lines.append(f"**Effort:** {score.effort_hours} hours ({score.effort_estimate.value})")
                lines.append(f"**ROI Score:** {score.roi_score:.1f}/100")
                lines.append(f"**Justification:** {score.justification}")
                lines.append("")
        
        # Quick wins
        if priority_ranking.quick_wins:
            lines.append("### Quick Wins")
            lines.append("")
            lines.append("High impact, low effort items to start with:")
            lines.append("")
            for task_id in priority_ranking.quick_wins:
                score = next((s for s in priority_ranking.priority_scores if s.component_name in task_id), None)
                if score:
                    lines.append(f"- **{score.component_name}** ({score.effort_hours}h, ROI: {score.roi_score:.1f})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_completion_dashboard_section(self, assessment_results: AssessmentResults) -> str:
        """Generate completion dashboard section"""
        lines = []
        lines.append("## Completion Dashboard")
        lines.append("")
        
        # Overall completion
        overall = assessment_results.overall_completion
        lines.append(f"### Overall System Completion: {overall:.1f}%")
        lines.append("")
        lines.append(self._create_large_progress_bar(overall))
        lines.append("")
        
        # Category completion
        lines.append("### Completion by Category")
        lines.append("")
        
        category_completion = self._calculate_category_completion(assessment_results)
        for category, completion in sorted(category_completion.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"**{category}**")
            lines.append(self._create_large_progress_bar(completion))
            lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_report_metrics(self, 
                                assessment_results: AssessmentResults,
                                gap_analysis: Optional[GapAnalysisResult],
                                priority_ranking: Optional[PriorityRankingResult]) -> Dict[str, Any]:
        """Calculate report metrics"""
        metrics = {
            "overall_completion": assessment_results.overall_completion,
            "total_components": len(assessment_results.component_scores),
            "completed_components": sum(1 for score in assessment_results.component_scores.values() 
                                      if score.completion_percentage >= 90),
            "category_completion": self._calculate_category_completion(assessment_results),
            "assessment_timestamp": assessment_results.assessment_timestamp.isoformat()
        }
        
        if gap_analysis:
            metrics.update({
                "total_gaps": len(gap_analysis.identified_gaps),
                "critical_gaps": len(gap_analysis.critical_gaps),
                "total_effort_estimate": gap_analysis.total_effort_estimate,
                "missing_components": len(gap_analysis.missing_components),
                "incomplete_implementations": len(gap_analysis.incomplete_implementations)
            })
        
        if priority_ranking:
            metrics.update({
                "critical_priority_items": len(priority_ranking.priority_matrix.get("critical", [])),
                "quick_wins": len(priority_ranking.quick_wins),
                "high_impact_items": len(priority_ranking.high_impact_items),
                "total_estimated_effort": priority_ranking.total_estimated_effort
            })
        
        return metrics
    
    def _generate_visualizations(self, 
                               assessment_results: AssessmentResults,
                               gap_analysis: Optional[GapAnalysisResult],
                               priority_ranking: Optional[PriorityRankingResult],
                               format_type: ReportFormat) -> Dict[str, str]:
        """Generate visualizations for the report"""
        visualizations = {}
        
        # Completion visualization
        completion_viz = self._create_completion_visualization(assessment_results)
        visualizations["completion"] = self._format_completion_visualization(completion_viz, format_type)
        
        # Gap analysis visualization
        if gap_analysis:
            visualizations["gaps"] = self._create_gap_visualization(gap_analysis, format_type)
        
        # Priority matrix visualization
        if priority_ranking:
            visualizations["priorities"] = self._create_priority_visualization(priority_ranking, format_type)
        
        return visualizations
    
    def _generate_report_recommendations(self, 
                                       assessment_results: AssessmentResults,
                                       gap_analysis: Optional[GapAnalysisResult],
                                       priority_ranking: Optional[PriorityRankingResult]) -> List[str]:
        """Generate report recommendations"""
        recommendations = []
        
        # Overall completion recommendations
        overall = assessment_results.overall_completion
        if overall < 70:
            recommendations.append("Focus on completing core infrastructure components before adding new features")
        elif overall < 85:
            recommendations.append("Address critical gaps and security issues before production deployment")
        elif overall < 95:
            recommendations.append("Complete final testing and documentation for production readiness")
        else:
            recommendations.append("System is ready for production deployment")
        
        # Gap-based recommendations
        if gap_analysis:
            if gap_analysis.critical_gaps:
                recommendations.append(f"Immediately address {len(gap_analysis.critical_gaps)} critical gaps blocking production")
            
            if gap_analysis.missing_components:
                recommendations.append(f"Implement {len(gap_analysis.missing_components)} missing components")
            
            if gap_analysis.total_effort_estimate > 320:  # More than 8 weeks
                recommendations.append("Consider breaking down large tasks and prioritizing based on business impact")
        
        # Priority-based recommendations
        if priority_ranking:
            if priority_ranking.quick_wins:
                recommendations.append(f"Start with {len(priority_ranking.quick_wins)} quick wins for immediate progress")
            
            if priority_ranking.critical_path:
                recommendations.append("Focus development resources on critical path components")
        
        return recommendations
    
    def _create_completion_visualization(self, assessment_results: AssessmentResults) -> CompletionVisualization:
        """Create completion visualization data"""
        return CompletionVisualization(
            overall_completion=assessment_results.overall_completion,
            category_completion=self._calculate_category_completion(assessment_results),
            component_completion={
                name: score.completion_percentage 
                for name, score in assessment_results.component_scores.items()
            }
        )
    
    def _format_markdown_report(self, report: StatusReport) -> str:
        """Format report as markdown"""
        lines = []
        
        # Title and metadata
        lines.append(f"# {report.title}")
        lines.append("")
        lines.append(f"*Generated: {report.generated_timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        
        # Executive summary
        lines.append(report.executive_summary)
        lines.append("")
        
        # Detailed sections
        for section_name, section_content in report.detailed_sections.items():
            lines.append(section_content)
            lines.append("")
        
        # Visualizations
        if report.visualizations:
            lines.append("## Visualizations")
            lines.append("")
            for viz_name, viz_content in report.visualizations.items():
                lines.append(f"### {viz_name.title()}")
                lines.append("")
                lines.append(viz_content)
                lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, recommendation in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {recommendation}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_html_report(self, report: StatusReport) -> str:
        """Format report as HTML"""
        # Convert markdown to HTML (simplified)
        markdown_content = self._format_markdown_report(report)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .progress-bar {{ background: #f0f0f0; border-radius: 10px; padding: 3px; }}
                .progress-fill {{ background: #4CAF50; height: 20px; border-radius: 7px; }}
                .critical {{ color: #f44336; }}
                .high {{ color: #ff9800; }}
                .medium {{ color: #ffeb3b; }}
                .low {{ color: #4caf50; }}
            </style>
        </head>
        <body>
            <pre>{markdown_content}</pre>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_json_report(self, report: StatusReport) -> str:
        """Format report as JSON"""
        report_dict = {
            "report_type": report.report_type.value,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "detailed_sections": report.detailed_sections,
            "metrics": report.metrics,
            "recommendations": report.recommendations,
            "generated_timestamp": report.generated_timestamp.isoformat(),
            "metadata": report.metadata
        }
        
        return json.dumps(report_dict, indent=2, default=str)
    
    def _format_text_report(self, report: StatusReport) -> str:
        """Format report as plain text"""
        # Remove markdown formatting
        markdown_content = self._format_markdown_report(report)
        
        # Simple markdown to text conversion
        text_content = markdown_content
        text_content = text_content.replace("# ", "")
        text_content = text_content.replace("## ", "")
        text_content = text_content.replace("### ", "")
        text_content = text_content.replace("**", "")
        text_content = text_content.replace("*", "")
        
        return text_content
    
    # Helper methods
    def _calculate_category_completion(self, assessment_results: AssessmentResults) -> Dict[str, float]:
        """Calculate completion percentage by category"""
        category_scores = {}
        category_counts = {}
        
        for component_name, score in assessment_results.component_scores.items():
            # Determine category from component name since CompletionScore doesn't have component object
            category = self._determine_category_from_name(component_name)
            
            if category not in category_scores:
                category_scores[category] = 0
                category_counts[category] = 0
            
            category_scores[category] += score.completion_percentage
            category_counts[category] += 1
        
        # Calculate averages
        category_completion = {}
        for category, total_score in category_scores.items():
            category_completion[category] = total_score / category_counts[category]
        
        return category_completion
    
    def _get_status_emoji(self, completion: float) -> str:
        """Get status emoji based on completion percentage"""
        if completion >= 95:
            return "✅"
        elif completion >= 85:
            return "🟡"
        elif completion >= 70:
            return "🟠"
        else:
            return "🔴"
    
    def _get_completion_icon(self, completion: float) -> str:
        """Get completion icon based on percentage"""
        if completion >= 90:
            return "✅"
        elif completion >= 70:
            return "🟡"
        elif completion >= 50:
            return "🟠"
        else:
            return "🔴"
    
    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create ASCII progress bar"""
        filled = int(percentage / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    def _create_large_progress_bar(self, percentage: float, width: int = 40) -> str:
        """Create large ASCII progress bar"""
        filled = int(percentage / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    def _generate_report_title(self, report_type: ReportType) -> str:
        """Generate report title based on type"""
        titles = {
            ReportType.EXECUTIVE_SUMMARY: "Phoenix Hydra System Status - Executive Summary",
            ReportType.DETAILED_BREAKDOWN: "Phoenix Hydra System Status - Detailed Breakdown",
            ReportType.COMPLETION_DASHBOARD: "Phoenix Hydra Completion Dashboard",
            ReportType.GAP_ANALYSIS: "Phoenix Hydra Gap Analysis Report",
            ReportType.PRIORITY_MATRIX: "Phoenix Hydra Priority Matrix",
            ReportType.PROGRESS_TRACKING: "Phoenix Hydra Progress Tracking Report"
        }
        return titles.get(report_type, "Phoenix Hydra System Status Report")
    
    def _create_report_metadata(self, 
                              assessment_results: AssessmentResults,
                              gap_analysis: Optional[GapAnalysisResult],
                              priority_ranking: Optional[PriorityRankingResult],
                              report_type: ReportType) -> Dict[str, Any]:
        """Create report metadata"""
        return {
            "report_type": report_type.value,
            "assessment_timestamp": assessment_results.assessment_timestamp.isoformat(),
            "overall_completion": assessment_results.overall_completion,
            "total_components": len(assessment_results.component_scores),
            "has_gap_analysis": gap_analysis is not None,
            "has_priority_ranking": priority_ranking is not None,
            "generator": "Phoenix Hydra System Review Tool",
            "version": "1.0.0"
        }
    
    def _create_error_report(self, error_message: str) -> StatusReport:
        """Create error report when generation fails"""
        return StatusReport(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            title="Error Report",
            executive_summary=f"Error generating report: {error_message}",
            metadata={"error": True, "error_message": error_message}
        )
    
    def _format_completion_visualization(self, viz: CompletionVisualization, format_type: ReportFormat) -> str:
        """Format completion visualization"""
        if format_type == ReportFormat.MARKDOWN:
            lines = []
            lines.append(f"**Overall Completion:** {viz.overall_completion:.1f}%")
            lines.append(self._create_large_progress_bar(viz.overall_completion))
            lines.append("")
            
            lines.append("**By Category:**")
            for category, completion in sorted(viz.category_completion.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {category}: {self._create_progress_bar(completion)}")
            
            return "\n".join(lines)
        else:
            return f"Overall completion: {viz.overall_completion:.1f}%"
    
    def _create_gap_visualization(self, gap_analysis: GapAnalysisResult, format_type: ReportFormat) -> str:
        """Create gap analysis visualization"""
        if format_type == ReportFormat.MARKDOWN:
            lines = []
            lines.append("**Gap Distribution:**")
            for gap_type, count in gap_analysis.gap_summary.items():
                if count > 0:
                    lines.append(f"- {gap_type.replace('_', ' ').title()}: {count}")
            return "\n".join(lines)
        else:
            return f"Total gaps: {len(gap_analysis.identified_gaps)}"
    
    def _create_priority_visualization(self, priority_ranking: PriorityRankingResult, format_type: ReportFormat) -> str:
        """Create priority matrix visualization"""
        if format_type == ReportFormat.MARKDOWN:
            lines = []
            lines.append("**Priority Distribution:**")
            for priority_level, scores in priority_ranking.priority_matrix.items():
                lines.append(f"- {priority_level.title()}: {len(scores)} items")
            return "\n".join(lines)
        else:
            return f"Total priority items: {len(priority_ranking.priority_scores)}"
    
    def _define_report_templates(self) -> Dict[ReportType, Dict[str, Any]]:
        """Define report templates"""
        return {
            ReportType.EXECUTIVE_SUMMARY: {
                "sections": ["executive_summary", "component_breakdown", "recommendations"],
                "stakeholder": "executive",
                "detail_level": "high_level"
            },
            ReportType.DETAILED_BREAKDOWN: {
                "sections": ["executive_summary", "component_breakdown", "gap_analysis", "priority_matrix"],
                "stakeholder": "technical",
                "detail_level": "detailed"
            },
            ReportType.COMPLETION_DASHBOARD: {
                "sections": ["completion_dashboard", "visualizations"],
                "stakeholder": "project_manager",
                "detail_level": "visual"
            }
        }
    
    def _define_visualization_settings(self) -> Dict[str, Any]:
        """Define visualization settings"""
        return {
            "progress_bar_width": 20,
            "large_progress_bar_width": 40,
            "color_scheme": {
                "critical": "#f44336",
                "high": "#ff9800", 
                "medium": "#ffeb3b",
                "low": "#4caf50",
                "complete": "#2196f3"
            }
        }
    
    def _define_stakeholder_configs(self) -> Dict[str, Dict[str, Any]]:
        """Define stakeholder-specific configurations"""
        return {
            "executive": {
                "focus": ["overall_completion", "critical_issues", "timeline"],
                "detail_level": "summary",
                "metrics": ["completion_percentage", "critical_gaps", "estimated_timeline"]
            },
            "technical": {
                "focus": ["component_details", "technical_gaps", "implementation_tasks"],
                "detail_level": "detailed",
                "metrics": ["code_quality", "test_coverage", "technical_debt"]
            },
            "project_manager": {
                "focus": ["progress_tracking", "resource_allocation", "timeline"],
                "detail_level": "operational",
                "metrics": ["task_completion", "effort_estimates", "dependencies"]
            }
        }
    
    def _determine_category_from_name(self, component_name: str) -> str:
        """Determine component category from component name"""
        component_lower = component_name.lower()
        
        # Category keywords mapping
        category_keywords = {
            'infrastructure': ['api', 'database', 'storage', 'container', 'podman', 'service', 'nca', 'toolkit'],
            'monetization': ['revenue', 'affiliate', 'grant', 'payment', 'marketplace', 'monetization'],
            'automation': ['workflow', 'script', 'deployment', 'ci', 'cd', 'automation', 'windmill'],
            'security': ['auth', 'security', 'ssl', 'certificate', 'encryption', 'authentication'],
            'testing': ['test', 'coverage', 'quality', 'validation', 'testing'],
            'documentation': ['doc', 'readme', 'guide', 'manual', 'documentation']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in component_lower for keyword in keywords):
                return category
        
        return 'infrastructure'  # Default category