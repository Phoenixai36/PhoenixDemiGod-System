#!/usr/bin/env python3
"""
Demonstration script for Windmill GitOps Assessment

This script shows how to use the WindmillAnalyzer to assess
Windmill configurations in the Phoenix Hydra project.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.phoenix_system_review.analysis.windmill_analyzer import WindmillAnalyzer


def main():
    """Demonstrate Windmill GitOps assessment functionality"""
    
    print("Phoenix Hydra Windmill GitOps Assessment Demo")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = WindmillAnalyzer(str(project_root))
    
    print(f"Project root: {project_root}")
    print(f"Windmill directory: {analyzer.windmill_dir}")
    print()
    
    # Analyze Windmill configurations
    print("1. Analyzing Windmill configurations...")
    workspaces = analyzer.analyze_windmill_configurations()
    print(f"   Found {len(workspaces)} workspace(s)")
    
    for workspace in workspaces:
        print(f"   - {workspace.name} (v{workspace.version})")
        print(f"     Scripts: {len(workspace.scripts)}, Flows: {len(workspace.flows)}")
        print(f"     Resources: {len(workspace.resources)}, Variables: {len(workspace.variables)}")
    print()
    
    # Check Windmill health
    print("2. Checking Windmill instance health...")
    is_healthy, version, health_issues = analyzer.check_windmill_health()
    print(f"   Healthy: {is_healthy}")
    if version:
        print(f"   Version: {version}")
    if health_issues:
        print(f"   Issues: {len(health_issues)}")
        for issue in health_issues[:3]:  # Show first 3 issues
            print(f"     - {issue.severity.value}: {issue.description}")
    print()
    
    # Analyze script quality
    if workspaces:
        print("3. Analyzing script quality...")
        for workspace in workspaces[:2]:  # Analyze first 2 workspaces
            print(f"   Workspace: {workspace.name}")
            for script in workspace.scripts[:3]:  # Analyze first 3 scripts
                quality_metrics = analyzer.analyze_script_quality(script)
                print(f"     Script: {script.path}")
                print(f"       Language: {script.language.value}")
                print(f"       Lines of code: {quality_metrics.lines_of_code}")
                print(f"       Has error handling: {quality_metrics.has_error_handling}")
                print(f"       Has documentation: {quality_metrics.has_documentation}")
                print(f"       Maintainability score: {quality_metrics.maintainability_score:.2f}")
                if quality_metrics.security_issues:
                    print(f"       Security issues: {len(quality_metrics.security_issues)}")
        print()
    
    # Generate comprehensive evaluation
    print("4. Generating comprehensive evaluation...")
    evaluation_result = analyzer.generate_evaluation_result()
    print(f"   Component: {evaluation_result.component.name}")
    print(f"   Completion percentage: {evaluation_result.completion_percentage:.1%}")
    print(f"   Quality score: {evaluation_result.quality_score:.2f}")
    print(f"   Criteria met: {len(evaluation_result.criteria_met)}")
    print(f"   Criteria missing: {len(evaluation_result.criteria_missing)}")
    print(f"   Issues found: {len(evaluation_result.issues)}")
    print()
    
    # Show some criteria details
    if evaluation_result.criteria_met:
        print("   Criteria met:")
        for criterion in evaluation_result.criteria_met[:5]:
            print(f"     ✓ {criterion}")
    
    if evaluation_result.criteria_missing:
        print("   Criteria missing:")
        for criterion in evaluation_result.criteria_missing[:5]:
            print(f"     ✗ {criterion}")
    print()
    
    # Show critical issues
    critical_issues = [
        issue for issue in evaluation_result.issues 
        if issue.severity.value in ['critical', 'high']
    ]
    if critical_issues:
        print("   Critical/High priority issues:")
        for issue in critical_issues[:5]:
            print(f"     - {issue.severity.value.upper()}: {issue.description}")
            if issue.recommendation:
                print(f"       Recommendation: {issue.recommendation}")
    print()
    
    # Generate analysis report
    print("5. Generating analysis report...")
    analysis_report = analyzer.generate_analysis_report()
    print(f"   Total scripts: {analysis_report.total_scripts}")
    print(f"   Total flows: {analysis_report.total_flows}")
    print(f"   GitOps readiness: {analysis_report.gitops_readiness:.1%}")
    print(f"   Overall health score: {analysis_report.health_score:.2f}")
    print()
    
    print("Assessment completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()