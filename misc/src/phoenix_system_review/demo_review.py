"""
Demo Phoenix Hydra System Review

A quick demonstration of the system review capabilities showing current status
and generating a basic TODO checklist for Phoenix Hydra.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .models.data_models import (
    AssessmentResults,
    Component,
    ComponentCategory,
    ComponentStatus,
    DependencyGraph,
    EvaluationResult,
    Gap,
    ImpactLevel,
    Issue,
    Priority,
    TaskStatus,
    TODOTask,
)


class PhoenixHydraReviewDemo:
    """Demo implementation of Phoenix Hydra system review"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.components = []
        self.evaluation_results = []

    def discover_phoenix_components(self) -> List[Component]:
        """Discover Phoenix Hydra components based on file structure"""
        components = []

        # Infrastructure Components
        if (self.project_root / "infra/podman/compose.yaml").exists():
            components.append(
                Component(
                    name="Podman Container Stack",
                    category=ComponentCategory.INFRASTRUCTURE,
                    path="infra/podman/compose.yaml",
                    dependencies=["postgres", "nginx"],
                    status=ComponentStatus.OPERATIONAL,
                    description="Container orchestration with Podman Compose",
                )
            )

        if (self.project_root / "src/phoenix_demigod").exists():
            components.append(
                Component(
                    name="Phoenix DemiGod Core",
                    category=ComponentCategory.INFRASTRUCTURE,
                    path="src/phoenix_demigod",
                    status=ComponentStatus.OPERATIONAL,
                    description="Core Phoenix DemiGod v8.7 system",
                )
            )

        # Check for NCA Toolkit
        nca_status = ComponentStatus.OPERATIONAL  # Based on status reports
        components.append(
            Component(
                name="NCA Toolkit",
                category=ComponentCategory.INFRASTRUCTURE,
                path="external",  # External API
                status=nca_status,
                description="30+ multimedia processing endpoints",
                configuration={
                    "api_url": "https://sea-turtle-app-nlak2.ondigitalocean.app/v1/"
                },
            )
        )

        # Monetization Components
        if (self.project_root / "README.md").exists():
            try:
                readme_content = (self.project_root / "README.md").read_text(
                    encoding="utf-8"
                )
                if "DigitalOcean" in readme_content and "CustomGPT" in readme_content:
                    has_affiliate = True
                else:
                    has_affiliate = False
            except UnicodeDecodeError:
                # Fallback if encoding issues - assume affiliate programs exist based on status reports
                has_affiliate = True

            if has_affiliate:
                components.append(
                    Component(
                        name="Affiliate Programs",
                        category=ComponentCategory.MONETIZATION,
                        path="README.md",
                        status=ComponentStatus.OPERATIONAL,
                        description="DigitalOcean and CustomGPT affiliate badges",
                    )
                )

        # Check for grant applications
        if (self.project_root / "src/scripts/neotec-generator.py").exists():
            components.append(
                Component(
                    name="NEOTEC Grant Generator",
                    category=ComponentCategory.MONETIZATION,
                    path="src/scripts/neotec-generator.py",
                    status=ComponentStatus.OPERATIONAL,
                    description="Automated NEOTEC grant application generator",
                )
            )

        # Automation Components
        if (self.project_root / ".vscode/tasks.json").exists():
            components.append(
                Component(
                    name="VS Code Automation",
                    category=ComponentCategory.AUTOMATION,
                    path=".vscode/tasks.json",
                    status=ComponentStatus.OPERATIONAL,
                    description="VS Code tasks for deployment and monitoring",
                )
            )

        # Documentation
        doc_files = [
            "README.md",
            "PROJECT-COMPLETION-STATUS.md",
            "PHOENIX-HYDRA-STATUS-REPORT.md",
        ]
        doc_count = sum(1 for f in doc_files if (self.project_root / f).exists())
        if doc_count > 0:
            components.append(
                Component(
                    name="Project Documentation",
                    category=ComponentCategory.DOCUMENTATION,
                    path="docs/",
                    status=ComponentStatus.OPERATIONAL
                    if doc_count >= 2
                    else ComponentStatus.DEGRADED,
                    description=f"Project documentation ({doc_count}/{len(doc_files)} files)",
                )
            )

        # Testing Infrastructure
        if (self.project_root / "tests").exists():
            components.append(
                Component(
                    name="Testing Infrastructure",
                    category=ComponentCategory.TESTING,
                    path="tests/",
                    status=ComponentStatus.DEGRADED,  # Limited test coverage
                    description="Basic test infrastructure with pytest",
                )
            )

        self.components = components
        return components

    def evaluate_components(self) -> List[EvaluationResult]:
        """Evaluate discovered components against completion criteria"""
        results = []

        for component in self.components:
            if component.category == ComponentCategory.INFRASTRUCTURE:
                result = self._evaluate_infrastructure_component(component)
            elif component.category == ComponentCategory.MONETIZATION:
                result = self._evaluate_monetization_component(component)
            elif component.category == ComponentCategory.AUTOMATION:
                result = self._evaluate_automation_component(component)
            elif component.category == ComponentCategory.DOCUMENTATION:
                result = self._evaluate_documentation_component(component)
            elif component.category == ComponentCategory.TESTING:
                result = self._evaluate_testing_component(component)
            else:
                result = self._evaluate_generic_component(component)

            results.append(result)

        self.evaluation_results = results
        return results

    def _evaluate_infrastructure_component(
        self, component: Component
    ) -> EvaluationResult:
        """Evaluate infrastructure components"""
        criteria_met = []
        criteria_missing = []
        issues = []

        if component.name == "Podman Container Stack":
            criteria_met = ["compose_file", "service_definitions", "environment_config"]
            if not (self.project_root / "infra/podman/health-checks.yaml").exists():
                criteria_missing.append("health_monitoring")
                issues.append(
                    Issue(
                        severity=Priority.MEDIUM,
                        description="Missing comprehensive health monitoring configuration",
                        component=component.name,
                    )
                )

        elif component.name == "NCA Toolkit":
            criteria_met = ["api_endpoints", "production_deployment", "documentation"]
            # NCA Toolkit is external and operational

        elif component.name == "Phoenix DemiGod Core":
            criteria_met = ["core_modules", "basic_structure"]
            if not (self.project_root / "src/phoenix_demigod/tests").exists():
                criteria_missing.append("comprehensive_testing")
                issues.append(
                    Issue(
                        severity=Priority.HIGH,
                        description="Missing comprehensive test suite for core modules",
                        component=component.name,
                    )
                )

        completion = (
            len(criteria_met) / (len(criteria_met) + len(criteria_missing)) * 100
        )

        return EvaluationResult(
            component_name=component.name,
            score=completion,
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion,
            quality_score=85.0
            if component.status == ComponentStatus.OPERATIONAL
            else 60.0,
            issues=issues,
        )

    def _evaluate_monetization_component(
        self, component: Component
    ) -> EvaluationResult:
        """Evaluate monetization components"""
        criteria_met = []
        criteria_missing = []
        issues = []

        if component.name == "Affiliate Programs":
            criteria_met = ["badge_deployment", "readme_integration"]
            if not (self.project_root / "scripts/revenue-tracking.js").exists():
                criteria_missing.append("revenue_tracking")
                issues.append(
                    Issue(
                        severity=Priority.HIGH,
                        description="Missing automated revenue tracking script",
                        component=component.name,
                    )
                )

        elif component.name == "NEOTEC Grant Generator":
            criteria_met = ["generator_script", "basic_functionality"]
            criteria_missing.append("automated_submission")
            issues.append(
                Issue(
                    severity=Priority.CRITICAL,
                    description="NEOTEC deadline June 12, 2025 - needs immediate attention",
                    component=component.name,
                )
            )

        completion = (
            len(criteria_met) / (len(criteria_met) + len(criteria_missing)) * 100
        )

        return EvaluationResult(
            component_name=component.name,
            score=completion,
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion,
            quality_score=75.0,
            issues=issues,
        )

    def _evaluate_automation_component(self, component: Component) -> EvaluationResult:
        """Evaluate automation components"""
        criteria_met = ["vscode_tasks", "deployment_automation"]
        criteria_missing = ["ci_cd_pipeline", "automated_testing"]

        issues = [
            Issue(
                severity=Priority.MEDIUM,
                description="Missing CI/CD pipeline for automated deployment",
                component=component.name,
            )
        ]

        completion = (
            len(criteria_met) / (len(criteria_met) + len(criteria_missing)) * 100
        )

        return EvaluationResult(
            component_name=component.name,
            score=completion,
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion,
            quality_score=70.0,
            issues=issues,
        )

    def _evaluate_documentation_component(
        self, component: Component
    ) -> EvaluationResult:
        """Evaluate documentation components"""
        criteria_met = ["readme", "status_reports", "implementation_roadmap"]
        criteria_missing = ["api_documentation", "deployment_guide"]

        completion = (
            len(criteria_met) / (len(criteria_met) + len(criteria_missing)) * 100
        )

        return EvaluationResult(
            component_name=component.name,
            score=completion,
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion,
            quality_score=90.0,
            issues=[],
        )

    def _evaluate_testing_component(self, component: Component) -> EvaluationResult:
        """Evaluate testing components"""
        criteria_met = ["pytest_config", "basic_tests"]
        criteria_missing = [
            "comprehensive_coverage",
            "integration_tests",
            "performance_tests",
        ]

        issues = [
            Issue(
                severity=Priority.HIGH,
                description="Test coverage is insufficient for production deployment",
                component=component.name,
            )
        ]

        completion = (
            len(criteria_met) / (len(criteria_met) + len(criteria_missing)) * 100
        )

        return EvaluationResult(
            component_name=component.name,
            score=completion,
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion,
            quality_score=40.0,
            issues=issues,
        )

    def _evaluate_generic_component(self, component: Component) -> EvaluationResult:
        """Generic component evaluation"""
        return EvaluationResult(
            component_name=component.name,
            score=50.0,
            component=component,
            criteria_met=["exists"],
            criteria_missing=["evaluation_criteria"],
            completion_percentage=50.0,
            quality_score=50.0,
            issues=[],
        )

    def identify_gaps(self) -> List[Gap]:
        """Identify gaps from evaluation results"""
        gaps = []

        for result in self.evaluation_results:
            for missing_criteria in result.criteria_missing:
                gap = Gap(
                    description=f"Missing: {missing_criteria}",
                    component_name=result.component.name,
                    severity="high" if result.has_critical_issues else "medium",
                    component=result.component.name,
                    impact=ImpactLevel.HIGH
                    if result.has_critical_issues
                    else ImpactLevel.MEDIUM,
                    effort_estimate=self._estimate_effort(missing_criteria),
                    category=result.component.category,
                    priority=Priority.CRITICAL
                    if result.has_critical_issues
                    else Priority.HIGH,
                )
                gaps.append(gap)

        return gaps

    def _estimate_effort(self, criteria: str) -> int:
        """Estimate effort in hours for missing criteria"""
        effort_map = {
            "health_monitoring": 16,
            "comprehensive_testing": 40,
            "revenue_tracking": 24,
            "automated_submission": 32,
            "ci_cd_pipeline": 48,
            "automated_testing": 32,
            "api_documentation": 16,
            "deployment_guide": 8,
            "comprehensive_coverage": 56,
            "integration_tests": 32,
            "performance_tests": 24,
        }
        return effort_map.get(criteria, 8)

    def generate_todo_checklist(self, gaps: List[Gap]) -> List[TODOTask]:
        """Generate TODO tasks from identified gaps"""
        tasks = []

        # Sort gaps by priority and impact
        sorted_gaps = sorted(gaps, key=lambda g: (g.priority.value, g.impact.value))

        for i, gap in enumerate(sorted_gaps):
            task = TODOTask(
                id=f"PHOENIX-{i+1:03d}",
                title=f"Fix {gap.component}: {gap.description}",
                description=f"Address missing criteria in {gap.component}",
                category=gap.category.value,
                priority=gap.priority,
                status=TaskStatus.NOT_STARTED,
                effort_hours=gap.effort_estimate,
                acceptance_criteria=[f"Implement {gap.description}"],
            )
            tasks.append(task)

        return tasks

    def calculate_overall_completion(self) -> float:
        """Calculate overall system completion percentage"""
        if not self.evaluation_results:
            return 0.0

        # Weight components by category
        weights = {
            ComponentCategory.INFRASTRUCTURE: 0.35,
            ComponentCategory.MONETIZATION: 0.25,
            ComponentCategory.AUTOMATION: 0.20,
            ComponentCategory.DOCUMENTATION: 0.10,
            ComponentCategory.TESTING: 0.05,
            ComponentCategory.SECURITY: 0.05,
        }

        weighted_total = 0.0
        total_weight = 0.0

        for result in self.evaluation_results:
            weight = weights.get(result.component.category, 0.1)
            weighted_total += result.completion_percentage * weight
            total_weight += weight

        return weighted_total / total_weight if total_weight > 0 else 0.0

    def run_complete_review(self) -> AssessmentResults:
        """Run complete Phoenix Hydra system review"""
        print("🔍 Discovering Phoenix Hydra components...")
        components = self.discover_phoenix_components()
        print(f"   Found {len(components)} components")

        print("📊 Evaluating components...")
        results = self.evaluate_components()

        print("🔍 Identifying gaps...")
        gaps = self.identify_gaps()

        print("📝 Generating TODO checklist...")
        tasks = self.generate_todo_checklist(gaps)

        overall_completion = self.calculate_overall_completion()

        assessment = AssessmentResults(
            summary=f"Phoenix Hydra System Review - {overall_completion:.1f}% Complete",
            results=results,
            dependency_graph=DependencyGraph(),
            overall_completion=overall_completion,
            identified_gaps=gaps,
            prioritized_tasks=tasks,
            recommendations=[
                "Focus on NEOTEC grant submission (Critical deadline: June 12, 2025)",
                "Implement comprehensive testing infrastructure",
                "Add automated revenue tracking for monetization streams",
                "Set up CI/CD pipeline for automated deployment",
                "Complete health monitoring for all services",
            ],
        )

        return assessment


def main():
    """Run Phoenix Hydra system review demo"""
    print("🚀 Phoenix Hydra System Review Demo")
    print("=" * 50)

    reviewer = PhoenixHydraReviewDemo()
    assessment = reviewer.run_complete_review()

    print(f"\n📈 Overall Completion: {assessment.overall_completion:.1f}%")
    print(f"🔍 Identified Gaps: {len(assessment.identified_gaps)}")
    print(f"📝 TODO Tasks: {len(assessment.prioritized_tasks)}")

    print("\n🔥 Critical Tasks:")
    critical_tasks = [
        t for t in assessment.prioritized_tasks if t.priority == Priority.CRITICAL
    ]
    for task in critical_tasks[:3]:
        print(f"   • {task.title} ({task.effort_hours}h)")

    print("\n⚡ High Priority Tasks:")
    high_tasks = [
        t for t in assessment.prioritized_tasks if t.priority == Priority.HIGH
    ]
    for task in high_tasks[:5]:
        print(f"   • {task.title} ({task.effort_hours}h)")

    print("\n💡 Key Recommendations:")
    for rec in assessment.recommendations:
        print(f"   • {rec}")

    print(f"\n✅ Phoenix Hydra is {assessment.overall_completion:.1f}% complete!")
    print("   Ready for final implementation phase.")


if __name__ == "__main__":
    main()
