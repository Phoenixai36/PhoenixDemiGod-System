#!/usr/bin/env python3
"""
Phoenix Hydra Comprehensive System Review
Complete analysis of all Phoenix Hydra components with detailed TODO checklist
"""

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import subprocess

class ComponentStatus(Enum):
    COMPLETE = "✅ Complete"
    IN_PROGRESS = "🔄 In Progress" 
    NOT_STARTED = "❌ Not Started"
    MISSING = "⚠️ Missing"

class Priority(Enum):
    CRITICAL = "🔴 Critical"
    HIGH = "🟡 High"
    MEDIUM = "🟢 Medium"
    LOW = "⚪ Low"

@dataclass
class ComponentAnalysis:
    name: str
    category: str
    status: ComponentStatus
    completion_percentage: float
    issues: List[str]
    recommendations: List[str]
    files_checked: List[str]

@dataclass
class TODOItem:
    id: str
    title: str
    description: str
    category: str
    priority: Priority
    status: ComponentStatus
    effort_hours: int
    dependencies: List[str]
    acceptance_criteria: List[str]

class PhoenixHydraComprehensiveReviewer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.components = []
        self.todo_items = []
        
    def check_file_exists(self, path: str) -> bool:
        """Check if file exists relative to project root"""
        return (self.project_root / path).exists()
    
    def analyze_infrastructure(self) -> List[ComponentAnalysis]:
        """Comprehensive infrastructure analysis"""
        results = []
        
        # 1. Podman Container Stack
        compose_file = "infra/podman/compose.yaml"
        files_checked = [compose_file]
        
        if self.check_file_exists(compose_file):
            with open(self.project_root / compose_file, encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            expected_services = ['phoenix-core', 'nca-toolkit', 'n8n-phoenix', 'windmill-phoenix', 'revenue-db']
            
            service_score = len([s for s in expected_services if s in services]) / len(expected_services) * 100
            
            issues = []
            recommendations = []
            
            for service in expected_services:
                if service not in services:
                    issues.append(f"Missing service: {service}")
            
            # Check for health checks
            services_without_health = []
            for name, config in services.items():
                if 'healthcheck' not in config:
                    services_without_health.append(name)
            
            if services_without_health:
                recommendations.append(f"Add health checks to: {', '.join(services_without_health)}")
            
            results.append(ComponentAnalysis(
                name="Podman Container Stack",
                category="Infrastructure",
                status=ComponentStatus.COMPLETE if service_score > 80 else ComponentStatus.IN_PROGRESS,
                completion_percentage=service_score,
                issues=issues,
                recommendations=recommendations,
                files_checked=files_checked
            ))
        else:
            results.append(ComponentAnalysis(
                name="Podman Container Stack",
                category="Infrastructure",
                status=ComponentStatus.MISSING,
                completion_percentage=0.0,
                issues=["Podman compose file missing"],
                recommendations=["Create infra/podman/compose.yaml"],
                files_checked=files_checked
            ))
        
        # 2. NCA Toolkit Integration
        nca_files = ["configs/nginx-nca-toolkit.html"]
        nca_score = sum(1 for f in nca_files if self.check_file_exists(f)) / len(nca_files) * 100
        
        issues = []
        if nca_score < 100:
            issues.append("NCA Toolkit configuration incomplete")
        
        results.append(ComponentAnalysis(
            name="NCA Toolkit Integration",
            category="Infrastructure", 
            status=ComponentStatus.COMPLETE if nca_score > 80 else ComponentStatus.IN_PROGRESS,
            completion_percentage=nca_score,
            issues=issues,
            recommendations=["Verify NCA Toolkit API endpoints", "Add monitoring for NCA services"],
            files_checked=nca_files
        ))
        
        # 3. Database Configuration
        db_files = ["infra/podman/compose.yaml"]  # DB defined in compose
        db_issues = []
        db_recommendations = []
        
        if self.check_file_exists(compose_file):
            with open(self.project_root / compose_file, encoding='utf-8') as f:
                compose_data = yaml.safe_load(f)
            
            if 'revenue-db' in compose_data.get('services', {}):
                db_config = compose_data['services']['revenue-db']
                if 'volumes' not in db_config:
                    db_issues.append("Database persistence not configured")
                if 'environment' not in db_config:
                    db_issues.append("Database environment variables missing")
                else:
                    env = db_config['environment']
                    if 'POSTGRES_PASSWORD' in env and env['POSTGRES_PASSWORD'] == 'hydra2025_secure_password':
                        db_recommendations.append("Change default database password")
            else:
                db_issues.append("Revenue database service not found")
        
        db_score = 70.0 if not db_issues else 40.0
        
        results.append(ComponentAnalysis(
            name="Database Configuration",
            category="Infrastructure",
            status=ComponentStatus.IN_PROGRESS if db_issues else ComponentStatus.COMPLETE,
            completion_percentage=db_score,
            issues=db_issues,
            recommendations=db_recommendations,
            files_checked=db_files
        ))
        
        return results
    
    def analyze_monetization(self) -> List[ComponentAnalysis]:
        """Comprehensive monetization analysis"""
        results = []
        
        # 1. Affiliate Programs
        readme_file = "README.md"
        files_checked = [readme_file]
        
        if self.check_file_exists(readme_file):
            with open(self.project_root / readme_file, encoding='utf-8') as f:
                readme_content = f.read()
            
            affiliate_programs = {
                'digitalocean': 'digitalocean' in readme_content.lower(),
                'customgpt': 'customgpt' in readme_content.lower(),
                'cloudflare': 'cloudflare' in readme_content.lower(),
                'huggingface': 'huggingface' in readme_content.lower()
            }
            
            active_programs = sum(affiliate_programs.values())
            affiliate_score = (active_programs / len(affiliate_programs)) * 100
            
            issues = []
            for program, active in affiliate_programs.items():
                if not active:
                    issues.append(f"Missing {program} affiliate integration")
            
            results.append(ComponentAnalysis(
                name="Affiliate Programs",
                category="Monetization",
                status=ComponentStatus.COMPLETE if affiliate_score > 75 else ComponentStatus.IN_PROGRESS,
                completion_percentage=affiliate_score,
                issues=issues,
                recommendations=["Add tracking scripts", "Monitor conversion rates", "Implement A/B testing"],
                files_checked=files_checked
            ))
        
        # 2. Revenue Tracking
        revenue_files = ["scripts/revenue-tracking.js", "scripts/deploy-badges.js"]
        revenue_score = sum(1 for f in revenue_files if self.check_file_exists(f)) / len(revenue_files) * 100
        
        issues = []
        for file in revenue_files:
            if not self.check_file_exists(file):
                issues.append(f"Missing {file}")
        
        results.append(ComponentAnalysis(
            name="Revenue Tracking System",
            category="Monetization",
            status=ComponentStatus.COMPLETE if revenue_score == 100 else ComponentStatus.NOT_STARTED,
            completion_percentage=revenue_score,
            issues=issues,
            recommendations=["Implement automated reporting", "Add revenue alerts", "Create dashboard"],
            files_checked=revenue_files
        ))
        
        # 3. Grant Applications
        grant_files = ["scripts/neotec-generator.py", "src/scripts/neotec-generator.py"]
        grant_score = 0
        grant_issues = []
        
        for file in grant_files:
            if self.check_file_exists(file):
                grant_score = 80.0  # Found at least one generator
                break
        else:
            grant_issues.append("NEOTEC grant generator missing")
        
        # Check for grant documentation
        grant_docs = ["docs/grants/", "docs/neotec/"]
        if not any(self.check_file_exists(d) for d in grant_docs):
            grant_issues.append("Grant documentation missing")
        
        results.append(ComponentAnalysis(
            name="Grant Applications",
            category="Monetization",
            status=ComponentStatus.IN_PROGRESS if grant_score > 0 else ComponentStatus.NOT_STARTED,
            completion_percentage=grant_score,
            issues=grant_issues,
            recommendations=["Complete NEOTEC generator", "Add ENISA application", "Create grant tracking"],
            files_checked=grant_files + grant_docs
        ))
        
        return results
    
    def analyze_automation(self) -> List[ComponentAnalysis]:
        """Comprehensive automation analysis"""
        results = []
        
        # 1. VS Code Integration
        vscode_files = [".vscode/tasks.json", ".vscode/settings.json"]
        vscode_score = sum(1 for f in vscode_files if self.check_file_exists(f)) / len(vscode_files) * 100
        
        issues = []
        recommendations = []
        
        if self.check_file_exists(".vscode/tasks.json"):
            with open(self.project_root / ".vscode/tasks.json", encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            task_count = len(tasks_data.get('tasks', []))
            if task_count < 5:
                recommendations.append(f"Add more automation tasks (current: {task_count})")
        else:
            issues.append("VS Code tasks configuration missing")
        
        results.append(ComponentAnalysis(
            name="VS Code Integration",
            category="Automation",
            status=ComponentStatus.COMPLETE if vscode_score == 100 else ComponentStatus.IN_PROGRESS,
            completion_percentage=vscode_score,
            issues=issues,
            recommendations=recommendations,
            files_checked=vscode_files
        ))
        
        # 2. Deployment Scripts
        deployment_files = [
            "scripts/complete-phoenix-deployment.ps1",
            "scripts/complete-phoenix-deployment.sh"
        ]
        deployment_score = sum(1 for f in deployment_files if self.check_file_exists(f)) / len(deployment_files) * 100
        
        deployment_issues = []
        for file in deployment_files:
            if not self.check_file_exists(file):
                deployment_issues.append(f"Missing {file}")
        
        results.append(ComponentAnalysis(
            name="Deployment Scripts",
            category="Automation",
            status=ComponentStatus.COMPLETE if deployment_score > 50 else ComponentStatus.NOT_STARTED,
            completion_percentage=deployment_score,
            issues=deployment_issues,
            recommendations=["Add deployment validation", "Implement rollback capability"],
            files_checked=deployment_files
        ))
        
        # 3. Agent Hooks
        hooks_files = ["src/hooks/", ".kiro/hooks/"]
        hooks_score = 0
        hooks_issues = []
        
        for hooks_dir in hooks_files:
            if self.check_file_exists(hooks_dir):
                hooks_score = 60.0  # Basic hooks structure exists
                break
        else:
            hooks_issues.append("Agent hooks system not implemented")
        
        results.append(ComponentAnalysis(
            name="Agent Hooks System",
            category="Automation",
            status=ComponentStatus.IN_PROGRESS if hooks_score > 0 else ComponentStatus.NOT_STARTED,
            completion_percentage=hooks_score,
            issues=hooks_issues,
            recommendations=["Implement file watchers", "Add container event hooks", "Create revenue automation"],
            files_checked=hooks_files
        ))
        
        return results
    
    def analyze_documentation(self) -> List[ComponentAnalysis]:
        """Comprehensive documentation analysis"""
        results = []
        
        # Core documentation files
        doc_files = [
            "README.md",
            "docs/implementation-roadmap.md", 
            "PROJECT-COMPLETION-STATUS.md",
            "PHOENIX-HYDRA-STATUS-REPORT.md"
        ]
        
        doc_score = sum(1 for f in doc_files if self.check_file_exists(f)) / len(doc_files) * 100
        
        issues = []
        for file in doc_files:
            if not self.check_file_exists(file):
                issues.append(f"Missing {file}")
        
        results.append(ComponentAnalysis(
            name="Technical Documentation",
            category="Documentation",
            status=ComponentStatus.COMPLETE if doc_score > 75 else ComponentStatus.IN_PROGRESS,
            completion_percentage=doc_score,
            issues=issues,
            recommendations=["Add API documentation", "Create deployment guide", "Update architecture diagrams"],
            files_checked=doc_files
        ))
        
        return results
    
    def analyze_testing(self) -> List[ComponentAnalysis]:
        """Comprehensive testing analysis"""
        results = []
        
        # Test structure
        test_files = ["tests/", "src/test_", "pyproject.toml"]
        test_score = 0
        test_issues = []
        
        if self.check_file_exists("tests/"):
            test_score += 40
        if self.check_file_exists("pyproject.toml"):
            test_score += 30  # pytest configuration
        
        # Check for test files in src
        src_tests = list(self.project_root.glob("src/test_*.py"))
        if src_tests:
            test_score += 30
        
        if test_score < 50:
            test_issues.append("Insufficient test coverage")
        
        results.append(ComponentAnalysis(
            name="Testing Infrastructure",
            category="Testing",
            status=ComponentStatus.IN_PROGRESS if test_score > 30 else ComponentStatus.NOT_STARTED,
            completion_percentage=test_score,
            issues=test_issues,
            recommendations=["Add unit tests", "Implement integration tests", "Set up CI/CD testing"],
            files_checked=test_files
        ))
        
        return results
    
    def generate_comprehensive_todo(self, analyses: List[ComponentAnalysis]) -> List[TODOItem]:
        """Generate comprehensive TODO items"""
        todo_items = []
        
        for analysis in analyses:
            # Critical issues (missing core components)
            for i, issue in enumerate(analysis.issues):
                priority = Priority.CRITICAL if analysis.completion_percentage < 30 else Priority.HIGH
                effort = 8 if priority == Priority.CRITICAL else 4
                
                todo_items.append(TODOItem(
                    id=f"{analysis.category.lower()}_{analysis.name.lower().replace(' ', '_')}_issue_{i}",
                    title=f"Fix: {issue}",
                    description=f"Resolve {issue} in {analysis.name}",
                    category=analysis.category,
                    priority=priority,
                    status=ComponentStatus.NOT_STARTED,
                    effort_hours=effort,
                    dependencies=[],
                    acceptance_criteria=[f"{issue} is resolved", f"{analysis.name} passes validation"]
                ))
            
            # Enhancement recommendations
            for i, rec in enumerate(analysis.recommendations):
                todo_items.append(TODOItem(
                    id=f"{analysis.category.lower()}_{analysis.name.lower().replace(' ', '_')}_rec_{i}",
                    title=f"Enhance: {rec}",
                    description=f"Implement {rec} for {analysis.name}",
                    category=analysis.category,
                    priority=Priority.MEDIUM,
                    status=ComponentStatus.NOT_STARTED,
                    effort_hours=3,
                    dependencies=[],
                    acceptance_criteria=[f"{rec} is implemented", "Enhancement is tested and documented"]
                ))
        
        return todo_items
    
    def run_comprehensive_review(self) -> Dict:
        """Run complete comprehensive Phoenix Hydra system review"""
        print("🚀 Starting Phoenix Hydra Comprehensive System Review...")
        
        # Analyze all components
        infrastructure = self.analyze_infrastructure()
        monetization = self.analyze_monetization()
        automation = self.analyze_automation()
        documentation = self.analyze_documentation()
        testing = self.analyze_testing()
        
        all_analyses = infrastructure + monetization + automation + documentation + testing
        
        # Calculate weighted completion (infrastructure and monetization are more important)
        weights = {
            'Infrastructure': 0.35,
            'Monetization': 0.25,
            'Automation': 0.20,
            'Documentation': 0.10,
            'Testing': 0.10
        }
        
        weighted_completion = 0
        for analysis in all_analyses:
            weight = weights.get(analysis.category, 0.1)
            weighted_completion += analysis.completion_percentage * weight
        
        # Generate comprehensive TODO items
        todo_items = self.generate_comprehensive_todo(all_analyses)
        
        # Sort TODO items by priority and effort
        todo_items.sort(key=lambda x: (x.priority.name, -x.effort_hours))
        
        return {
            'overall_completion': weighted_completion,
            'component_analyses': all_analyses,
            'todo_items': todo_items,
            'summary': {
                'total_components': len(all_analyses),
                'complete_components': len([a for a in all_analyses if a.status == ComponentStatus.COMPLETE]),
                'in_progress_components': len([a for a in all_analyses if a.status == ComponentStatus.IN_PROGRESS]),
                'missing_components': len([a for a in all_analyses if a.status == ComponentStatus.MISSING]),
                'total_todo_items': len(todo_items),
                'critical_items': len([t for t in todo_items if t.priority == Priority.CRITICAL]),
                'high_priority_items': len([t for t in todo_items if t.priority == Priority.HIGH])
            },
            'categories': {
                category: {
                    'components': [a for a in all_analyses if a.category == category],
                    'avg_completion': sum(a.completion_percentage for a in all_analyses if a.category == category) / 
                                   len([a for a in all_analyses if a.category == category])
                }
                for category in set(a.category for a in all_analyses)
            }
        }
    
    def print_comprehensive_results(self, results: Dict):
        """Print comprehensive formatted results"""
        print(f"\n📊 PHOENIX HYDRA COMPREHENSIVE SYSTEM REVIEW")
        print(f"=" * 60)
        print(f"Overall Completion: {results['overall_completion']:.1f}%")
        print(f"Components Analyzed: {results['summary']['total_components']}")
        print(f"✅ Complete: {results['summary']['complete_components']}")
        print(f"🔄 In Progress: {results['summary']['in_progress_components']}")
        print(f"⚠️ Missing: {results['summary']['missing_components']}")
        print(f"📋 TODO Items: {results['summary']['total_todo_items']}")
        print(f"🔴 Critical: {results['summary']['critical_items']}")
        print(f"🟡 High Priority: {results['summary']['high_priority_items']}")
        
        print(f"\n🏗️ CATEGORY BREAKDOWN")
        print(f"-" * 40)
        for category, data in results['categories'].items():
            print(f"{category}: {data['avg_completion']:.1f}% avg completion")
            for component in data['components']:
                print(f"  {component.status.value} {component.name} ({component.completion_percentage:.1f}%)")
                if component.issues:
                    for issue in component.issues[:2]:  # Show first 2 issues
                        print(f"    ⚠️  {issue}")
        
        print(f"\n📋 PRIORITIZED TODO CHECKLIST")
        print(f"-" * 40)
        
        # Group by priority
        priority_groups = {}
        for todo in results['todo_items']:
            if todo.priority not in priority_groups:
                priority_groups[todo.priority] = []
            priority_groups[todo.priority].append(todo)
        
        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            if priority in priority_groups:
                items = priority_groups[priority][:5]  # Show top 5 per priority
                print(f"\n{priority.value} ({len(priority_groups[priority])} items)")
                for todo in items:
                    print(f"- [ ] {todo.title}")
                    print(f"      Category: {todo.category} | Effort: {todo.effort_hours}h")
                    print(f"      {todo.description}")
                    if todo.acceptance_criteria:
                        print(f"      Acceptance: {todo.acceptance_criteria[0]}")
                    print()
        
        print(f"\n🎯 RECOMMENDATIONS FOR 100% COMPLETION")
        print(f"-" * 40)
        
        # Calculate remaining effort
        total_effort = sum(todo.effort_hours for todo in results['todo_items'])
        critical_effort = sum(todo.effort_hours for todo in results['todo_items'] if todo.priority == Priority.CRITICAL)
        
        print(f"Total Remaining Effort: {total_effort} hours ({total_effort/8:.1f} days)")
        print(f"Critical Items Effort: {critical_effort} hours ({critical_effort/8:.1f} days)")
        print(f"Estimated Time to 100%: {total_effort/40:.1f} weeks (1 developer)")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Address all Critical items first ({critical_effort}h)")
        print(f"2. Focus on Infrastructure and Monetization categories")
        print(f"3. Implement missing scripts and configurations")
        print(f"4. Add comprehensive testing and documentation")
        print(f"5. Deploy and validate in production environment")

def main():
    """Main comprehensive review execution"""
    print("🔍 Phoenix Hydra Comprehensive System Review")
    print("Analyzing all components for 100% completion assessment...")
    
    reviewer = PhoenixHydraComprehensiveReviewer()
    results = reviewer.run_comprehensive_review()
    reviewer.print_comprehensive_results(results)
    
    print(f"\n✅ Comprehensive review completed!")
    print(f"💡 Use this analysis to achieve 100% Phoenix Hydra completion")

if __name__ == "__main__":
    main()