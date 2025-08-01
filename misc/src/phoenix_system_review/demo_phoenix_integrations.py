#!/usr/bin/env python3
"""
Phoenix Hydra Integrations Demo

Demonstrates the comprehensive Phoenix Hydra specific integrations
including Podman, n8n, and Windmill analysis and coordination.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from phoenix_system_review.analysis.phoenix_hydra_integrator import PhoenixHydraIntegrator
from phoenix_system_review.models.data_models import Priority


def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection_header(title: str):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def format_completion_percentage(percentage: float) -> str:
    """Format completion percentage with color coding"""
    if percentage >= 80:
        return f"✅ {percentage:.1f}%"
    elif percentage >= 60:
        return f"⚠️  {percentage:.1f}%"
    else:
        return f"❌ {percentage:.1f}%"


def format_health_score(score: float) -> str:
    """Format health score with status indicator"""
    if score >= 0.8:
        return f"🟢 {score:.2f} (Healthy)"
    elif score >= 0.5:
        return f"🟡 {score:.2f} (Degraded)"
    else:
        return f"🔴 {score:.2f} (Critical)"


def format_issue_severity(severity: Priority) -> str:
    """Format issue severity with appropriate icon"""
    severity_icons = {
        Priority.CRITICAL: "🚨",
        Priority.HIGH: "⚠️",
        Priority.MEDIUM: "⚡",
        Priority.LOW: "ℹ️"
    }
    return f"{severity_icons.get(severity, '❓')} {severity.value.upper()}"


def demo_individual_analyzers(integrator: PhoenixHydraIntegrator):
    """Demonstrate individual analyzer capabilities"""
    print_section_header("INDIVIDUAL ANALYZER DEMONSTRATIONS")
    
    # Podman Analysis
    print_subsection_header("Podman Container Analysis")
    try:
        podman_result = integrator._analyze_podman_integration()
        print(f"Component: {podman_result.component.name}")
        print(f"Completion: {format_completion_percentage(podman_result.completion_percentage)}")
        print(f"Quality Score: {format_health_score(podman_result.quality_score)}")
        print(f"Criteria Met: {len(podman_result.criteria_met)}")
        print(f"Criteria Missing: {len(podman_result.criteria_missing)}")
        print(f"Issues Found: {len(podman_result.issues)}")
        
        if podman_result.criteria_met:
            print("\n✅ Met Criteria:")
            for criterion in podman_result.criteria_met[:5]:  # Show first 5
                print(f"  • {criterion}")
        
        if podman_result.issues:
            print(f"\n⚠️  Top Issues:")
            for issue in podman_result.issues[:3]:  # Show first 3
                print(f"  {format_issue_severity(issue.severity)} {issue.description}")
    
    except Exception as e:
        print(f"❌ Podman analysis failed: {e}")
    
    # n8n Analysis
    print_subsection_header("n8n Workflow Analysis")
    try:
        n8n_result = integrator._analyze_n8n_integration()
        print(f"Component: {n8n_result.component.name}")
        print(f"Completion: {format_completion_percentage(n8n_result.completion_percentage)}")
        print(f"Quality Score: {format_health_score(n8n_result.quality_score)}")
        print(f"Status: {n8n_result.component.status.value}")
        
        if n8n_result.criteria_met:
            print("\n✅ Met Criteria:")
            for criterion in n8n_result.criteria_met:
                print(f"  • {criterion}")
        
        if n8n_result.issues:
            print(f"\n⚠️  Issues:")
            for issue in n8n_result.issues[:3]:
                print(f"  {format_issue_severity(issue.severity)} {issue.description}")
    
    except Exception as e:
        print(f"❌ n8n analysis failed: {e}")
    
    # Windmill Analysis
    print_subsection_header("Windmill GitOps Analysis")
    try:
        windmill_result = integrator._analyze_windmill_integration()
        print(f"Component: {windmill_result.component.name}")
        print(f"Completion: {format_completion_percentage(windmill_result.completion_percentage)}")
        print(f"Quality Score: {format_health_score(windmill_result.quality_score)}")
        
        if windmill_result.criteria_met:
            print("\n✅ Met Criteria:")
            for criterion in windmill_result.criteria_met:
                print(f"  • {criterion}")
        
        if windmill_result.issues:
            print(f"\n⚠️  Issues:")
            for issue in windmill_result.issues[:3]:
                print(f"  {format_issue_severity(issue.severity)} {issue.description}")
    
    except Exception as e:
        print(f"❌ Windmill analysis failed: {e}")


def demo_comprehensive_integration(integrator: PhoenixHydraIntegrator):
    """Demonstrate comprehensive integration analysis"""
    print_section_header("COMPREHENSIVE INTEGRATION ANALYSIS")
    
    try:
        result = integrator.analyze_all_integrations()
        
        print(f"🎯 Overall Integration Health: {format_health_score(result.integration_health_score)}")
        print(f"📊 Cross-Integration Issues: {len(result.cross_integration_issues)}")
        print(f"💡 Integration Recommendations: {len(result.integration_recommendations)}")
        
        # Component Status Summary
        print_subsection_header("Component Status Summary")
        components = [
            ("Podman Infrastructure", result.podman_analysis),
            ("n8n Workflows", result.n8n_analysis),
            ("Windmill GitOps", result.windmill_analysis)
        ]
        
        for name, analysis in components:
            if analysis:
                print(f"{name:20} {format_completion_percentage(analysis.completion_percentage):15} "
                      f"{format_health_score(analysis.quality_score):20} "
                      f"Issues: {len(analysis.issues)}")
            else:
                print(f"{name:20} {'❌ Not Available':15}")
        
        # Cross-Integration Issues
        if result.cross_integration_issues:
            print_subsection_header("Cross-Integration Issues")
            for issue in result.cross_integration_issues:
                print(f"{format_issue_severity(issue.severity)} {issue.description}")
                if issue.recommendation:
                    print(f"   💡 {issue.recommendation}")
        
        # Top Recommendations
        if result.integration_recommendations:
            print_subsection_header("Top Integration Recommendations")
            for i, recommendation in enumerate(result.integration_recommendations[:5], 1):
                print(f"{i}. {recommendation}")
    
    except Exception as e:
        print(f"❌ Comprehensive integration analysis failed: {e}")


def demo_integration_summary(integrator: PhoenixHydraIntegrator):
    """Demonstrate integration summary functionality"""
    print_section_header("INTEGRATION SUMMARY REPORT")
    
    try:
        summary = integrator.get_integration_summary()
        
        print(f"🎯 Integration Health Score: {format_health_score(summary['integration_health_score'])}")
        print(f"📈 Integration Status: {summary['integration_status'].upper()}")
        print(f"🔍 Total Issues: {summary['total_issues']}")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        
        print_subsection_header("Component Analysis Status")
        for component, analyzed in summary['components_analyzed'].items():
            status = "✅ Analyzed" if analyzed else "❌ Not Analyzed"
            score = summary['component_scores'].get(component, 0.0)
            print(f"{component.capitalize():12} {status:15} Score: {format_completion_percentage(score)}")
        
        print_subsection_header("Top Recommendations")
        for i, rec in enumerate(summary['top_recommendations'], 1):
            print(f"{i}. {rec}")
    
    except Exception as e:
        print(f"❌ Integration summary failed: {e}")


def demo_specific_integration_features(integrator: PhoenixHydraIntegrator):
    """Demonstrate specific Phoenix Hydra integration features"""
    print_section_header("PHOENIX HYDRA SPECIFIC FEATURES")
    
    # Demonstrate Podman-specific features
    print_subsection_header("Podman Container Features")
    try:
        compose_analyses = integrator.podman_analyzer.analyze_compose_files()
        print(f"📁 Compose Files Found: {len(compose_analyses)}")
        
        for analysis in compose_analyses:
            print(f"  • {Path(analysis.file_path).name}: {len(analysis.services)} services, "
                  f"Health Score: {format_health_score(analysis.health_score)}")
        
        # Check container health
        container_status = integrator.podman_analyzer.check_container_health()
        if container_status:
            print(f"🐳 Container Status: {len(container_status)} containers detected")
            for name, status in list(container_status.items())[:3]:
                print(f"  • {name}: {status.value}")
        else:
            print("🐳 No running containers detected")
    
    except Exception as e:
        print(f"❌ Podman features demo failed: {e}")
    
    # Demonstrate n8n-specific features
    print_subsection_header("n8n Workflow Features")
    try:
        workflows = integrator.n8n_analyzer.analyze_workflow_files()
        print(f"🔄 Workflows Found: {len(workflows)}")
        
        for workflow in workflows:
            print(f"  • {workflow.name}: {len(workflow.nodes)} nodes, "
                  f"{len(workflow.connections)} connections")
        
        # Check n8n health
        n8n_healthy, n8n_version, health_issues = integrator.n8n_analyzer.check_n8n_health()
        health_status = "🟢 Healthy" if n8n_healthy else "🔴 Unhealthy"
        print(f"🏥 n8n Service: {health_status}")
        if n8n_version:
            print(f"📦 Version: {n8n_version}")
    
    except Exception as e:
        print(f"❌ n8n features demo failed: {e}")
    
    # Demonstrate Windmill-specific features
    print_subsection_header("Windmill GitOps Features")
    try:
        workspaces = integrator.windmill_analyzer.analyze_windmill_configurations()
        print(f"🏢 Workspaces Found: {len(workspaces)}")
        
        for workspace in workspaces:
            print(f"  • {workspace.name} (v{workspace.version}): "
                  f"{len(workspace.scripts)} scripts, {len(workspace.flows)} flows")
        
        # Check Windmill health
        windmill_healthy, windmill_version, health_issues = integrator.windmill_analyzer.check_windmill_health()
        health_status = "🟢 Healthy" if windmill_healthy else "🔴 Unhealthy"
        print(f"🏥 Windmill Service: {health_status}")
        if windmill_version:
            print(f"📦 Version: {windmill_version}")
    
    except Exception as e:
        print(f"❌ Windmill features demo failed: {e}")


def main():
    """Main demo function"""
    print("🚀 Phoenix Hydra Integrations Demo")
    print("=" * 60)
    
    # Initialize integrator
    project_root = Path.cwd()
    print(f"📁 Project Root: {project_root}")
    
    try:
        integrator = PhoenixHydraIntegrator(str(project_root))
        print("✅ Phoenix Hydra Integrator initialized successfully")
        
        # Run demonstrations
        demo_individual_analyzers(integrator)
        demo_comprehensive_integration(integrator)
        demo_integration_summary(integrator)
        demo_specific_integration_features(integrator)
        
        print_section_header("DEMO COMPLETED SUCCESSFULLY")
        print("🎉 All Phoenix Hydra integrations have been demonstrated!")
        print("📋 Check the output above for detailed analysis results.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure you're running this from the Phoenix Hydra project root")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())