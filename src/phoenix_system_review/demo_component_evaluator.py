#!/usr/bin/env python3
"""
Demo script for the enhanced Component Evaluator functionality.
Shows the improved scoring algorithms, issue detection, and reporting capabilities.
"""

from src.phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from src.phoenix_system_review.models.data_models import Component, ComponentCategory, ComponentStatus
import json


def demo_component_evaluator():
    """Demonstrate the enhanced component evaluator functionality"""
    print("=== Phoenix Hydra Component Evaluator Demo ===\n")
    
    # Initialize evaluator
    evaluator = ComponentEvaluator('.')
    
    # Create test components
    test_components = [
        Component(
            name="VS Code Tasks",
            category=ComponentCategory.AUTOMATION,
            path=".vscode/",
            status=ComponentStatus.OPERATIONAL,
            description="VS Code task automation"
        ),
        Component(
            name="Deployment Scripts",
            category=ComponentCategory.AUTOMATION,
            path="scripts/",
            status=ComponentStatus.DEGRADED,
            description="Deployment automation scripts"
        ),
        Component(
            name="NCA Toolkit",
            category=ComponentCategory.INFRASTRUCTURE,
            path="src/core/",
            status=ComponentStatus.OPERATIONAL,
            description="NCA Toolkit API endpoints"
        )
    ]
    
    # Evaluate components
    evaluations = []
    for component in test_components:
        print(f"Evaluating: {component.name}")
        evaluation = evaluator.evaluate_component(component)
        evaluations.append(evaluation)
        
        print(f"  Status: {evaluation.status.value}")
        print(f"  Completion: {evaluation.completion_percentage:.1f}%")
        print(f"  Score: {evaluation.overall_score:.3f}")
        print(f"  Issues: {len(evaluation.issues)}")
        print(f"  Recommendations: {len(evaluation.recommendations)}")
        
        # Show issue categorization
        if evaluation.issues:
            issue_categories = evaluator.detect_component_issues(evaluation)
            if issue_categories:
                print(f"  Issue Categories: {list(issue_categories.keys())}")
        
        print()
    
    # Calculate system-wide metrics
    print("=== System-Wide Analysis ===")
    system_metrics = evaluator.calculate_system_completion(evaluations)
    print(f"Overall Completion: {system_metrics['overall_completion']:.1f}%")
    print(f"Total Components: {system_metrics['total_components']}")
    print(f"Evaluated Components: {system_metrics['evaluated_components']}")
    print(f"Passed Components: {system_metrics['passed_components']}")
    print(f"Failed Components: {system_metrics['failed_components']}")
    print(f"Critical Issues: {system_metrics['critical_issues']}")
    
    # Show category breakdown
    print("\n=== Category Breakdown ===")
    for category, metrics in system_metrics['category_completion'].items():
        print(f"{category.title()}: {metrics['completion']:.1f}% "
              f"({metrics['passed']}/{metrics['components']} passed)")
    
    # Calculate completion trends
    print("\n=== Completion Trends ===")
    trend_data = evaluator.calculate_completion_trend(evaluations)
    print(f"Overall Trend: {trend_data['trend']}")
    print(f"Average Score: {trend_data['overall_average']:.1f}%")
    
    if trend_data['patterns']:
        print("Patterns Detected:")
        for pattern in trend_data['patterns']:
            print(f"  - {pattern}")
    
    # Generate comprehensive report
    print("\n=== Generating Comprehensive Report ===")
    report = evaluator.generate_evaluation_report(evaluations)
    
    print(f"Report generated with {len(report['component_evaluations']['passed'])} passed, "
          f"{len(report['component_evaluations']['failed'])} failed, "
          f"and {len(report['component_evaluations']['warnings'])} warning components")
    
    print(f"Top Issues: {len(report['top_issues'])}")
    print(f"Top Recommendations: {len(report['top_recommendations'])}")
    
    return evaluations, report


if __name__ == "__main__":
    try:
        evaluations, report = demo_component_evaluator()
        print("\n✅ Component Evaluator demo completed successfully!")
        print(f"Evaluated {len(evaluations)} components with enhanced scoring and issue detection.")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()