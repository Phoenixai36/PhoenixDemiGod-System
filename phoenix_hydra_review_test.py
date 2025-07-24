#!/usr/bin/env python3
"""
Phoenix Hydra System Review - Quick Test Implementation
Demonstrates the system review approach with actual Phoenix Hydra analysis
"""

import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

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

class PhoenixHydraReviewer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.components = []
        self.todo_items = []
        
    def analyze_infrastructure(self) -> List[ComponentAnalysis]:
        """Analyze core infrastructure components"""
        results = []
        
        # Analyze Podman Compose
        compose_file = self.project_root / "infra" / "podman" / "compose.yaml"
        if compose_file.exists():
            with open(compose_file) as f:
                compose_data = yaml.safe_load(f)
            
            services = compose_data.get('services', {})
            completion = 85.0 if len(services) >= 5 else 60.0
            
            issues = []
            if 'phoenix-core' not in services:
                issues.append("Phoenix Core service not defined")
            if 'revenue-db' not in services:
                issues.append("Revenue database not configured")
                
            results.append(ComponentAnalysis(
                name="Podman Container Stack",
                category="Infrastructure",
                status=ComponentStatus.COMPLETE if completion > 80 else ComponentStatus.IN_PROGRESS,
                completion_percentage=completion,
                issues=issues,
                recommendations=["Add health checks to all services", "Configure resource limits"]
            ))
        else:
            results.append(ComponentAnalysis(
                name="Podman Container Stack",
                category="Infrastructure", 
                status=ComponentStatus.MISSING,
                completion_percentage=0.0,
                issues=["Compose file not found"],
                recommendations=["Create Podman compose configuration"]
            ))
            
        # Analyze Python Project Structure
        pyproject_file = self.project_root / "pyproject.toml"
        if pyproject_file.exists():
            results.append(ComponentAnalysis(
                name="Python Project Configuration",
                category="Infrastructure",
                status=ComponentStatus.COMPLETE,
                completion_percentage=95.0,
                issues=[],
                recommendations=["Consider adding more dev dependencies"]
            ))
            
        return results
    
    def analyze_monetization(self) -> List[ComponentAnalysis]:
        """Analyze monetization components"""
        results = []
        
        # Check README for affiliate badges
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            with open(readme_file, encoding='utf-8') as f:
                readme_content = f.read()
            
            badges_found = 0
            if "digitalocean" in readme_content.lower():
                badges_found += 1
            if "customgpt" in readme_content.lower():
                badges_found += 1
            if "cloudflare" in readme_content.lower():
                badges_found += 1
                
            completion = (badges_found / 3) * 100
            
            results.append(ComponentAnalysis(
                name="Affiliate Program Integration",
                category="Monetization",
                status=ComponentStatus.COMPLETE if completion > 80 else ComponentStatus.IN_PROGRESS,
                completion_percentage=completion,
                issues=[] if badges_found >= 2 else ["Missing affiliate badges"],
                recommendations=["Add tracking scripts", "Monitor conversion rates"]
            ))
            
        # Check for revenue tracking scripts
        scripts_dir = self.project_root / "scripts"
        revenue_script_exists = (scripts_dir / "revenue-tracking.js").exists()
        
        results.append(ComponentAnalysis(
            name="Revenue Tracking System",
            category="Monetization",
            status=ComponentStatus.COMPLETE if revenue_script_exists else ComponentStatus.NOT_STARTED,
            completion_percentage=100.0 if revenue_script_exists else 0.0,
            issues=[] if revenue_script_exists else ["Revenue tracking script missing"],
            recommendations=["Implement automated reporting", "Add revenue alerts"]
        ))
        
        return results
    
    def analyze_automation(self) -> List[ComponentAnalysis]:
        """Analyze automation and DevOps components"""
        results = []
        
        # Check VS Code configuration
        vscode_dir = self.project_root / ".vscode"
        tasks_file = vscode_dir / "tasks.json"
        settings_file = vscode_dir / "settings.json"
        
        if tasks_file.exists() and settings_file.exists():
            with open(tasks_file) as f:
                tasks_data = json.load(f)
            
            task_count = len(tasks_data.get('tasks', []))
            completion = min(100.0, (task_count / 7) * 100)  # Expecting ~7 tasks
            
            results.append(ComponentAnalysis(
                name="VS Code Integration",
                category="Automation",
                status=ComponentStatus.COMPLETE if completion > 80 else ComponentStatus.IN_PROGRESS,
                completion_percentage=completion,
                issues=[] if task_count >= 5 else ["Missing automation tasks"],
                recommendations=["Add more automation hooks", "Integrate with Kiro agent"]
            ))
        else:
            results.append(ComponentAnalysis(
                name="VS Code Integration",
                category="Automation",
                status=ComponentStatus.NOT_STARTED,
                completion_percentage=0.0,
                issues=["VS Code configuration missing"],
                recommendations=["Create tasks.json and settings.json"]
            ))
            
        return results
    
    def generate_todo_items(self, analyses: List[ComponentAnalysis]) -> List[TODOItem]:
        """Generate TODO items from component analyses"""
        todo_items = []
        
        for analysis in analyses:
            if analysis.completion_percentage < 100:
                # Generate TODO items based on issues and recommendations
                for i, issue in enumerate(analysis.issues):
                    priority = Priority.CRITICAL if analysis.completion_percentage < 50 else Priority.HIGH
                    
                    todo_items.append(TODOItem(
                        id=f"{analysis.category.lower()}_{analysis.name.lower().replace(' ', '_')}_{i}",
                        title=f"Fix: {issue}",
                        description=f"Resolve {issue} in {analysis.name}",
                        category=analysis.category,
                        priority=priority,
                        status=ComponentStatus.NOT_STARTED,
                        effort_hours=4 if priority == Priority.CRITICAL else 2,
                        dependencies=[]
                    ))
                
                for i, rec in enumerate(analysis.recommendations):
                    todo_items.append(TODOItem(
                        id=f"{analysis.category.lower()}_{analysis.name.lower().replace(' ', '_')}_rec_{i}",
                        title=f"Enhance: {rec}",
                        description=f"Implement {rec} for {analysis.name}",
                        category=analysis.category,
                        priority=Priority.MEDIUM,
                        status=ComponentStatus.NOT_STARTED,
                        effort_hours=3,
                        dependencies=[]
                    ))
        
        return todo_items
    
    def run_complete_review(self) -> Dict:
        """Run complete Phoenix Hydra system review"""
        print("🚀 Starting Phoenix Hydra System Review...")
        
        # Analyze all components
        infrastructure = self.analyze_infrastructure()
        monetization = self.analyze_monetization()
        automation = self.analyze_automation()
        
        all_analyses = infrastructure + monetization + automation
        
        # Calculate overall completion
        total_completion = sum(a.completion_percentage for a in all_analyses) / len(all_analyses)
        
        # Generate TODO items
        todo_items = self.generate_todo_items(all_analyses)
        
        return {
            'overall_completion': total_completion,
            'component_analyses': all_analyses,
            'todo_items': todo_items,
            'summary': {
                'total_components': len(all_analyses),
                'complete_components': len([a for a in all_analyses if a.status == ComponentStatus.COMPLETE]),
                'total_todo_items': len(todo_items),
                'critical_items': len([t for t in todo_items if t.priority == Priority.CRITICAL])
            }
        }
    
    def print_results(self, results: Dict):
        """Print formatted results"""
        print(f"\n📊 PHOENIX HYDRA SYSTEM REVIEW RESULTS")
        print(f"=" * 50)
        print(f"Overall Completion: {results['overall_completion']:.1f}%")
        print(f"Components Analyzed: {results['summary']['total_components']}")
        print(f"Complete Components: {results['summary']['complete_components']}")
        print(f"TODO Items Generated: {results['summary']['total_todo_items']}")
        print(f"Critical Items: {results['summary']['critical_items']}")
        
        print(f"\n🔍 COMPONENT ANALYSIS")
        print(f"-" * 30)
        for analysis in results['component_analyses']:
            print(f"{analysis.status.value} {analysis.name} ({analysis.completion_percentage:.1f}%)")
            if analysis.issues:
                for issue in analysis.issues:
                    print(f"  ⚠️  {issue}")
        
        print(f"\n📋 TODO CHECKLIST (Top 10)")
        print(f"-" * 30)
        sorted_todos = sorted(results['todo_items'], 
                            key=lambda x: (x.priority.name, -x.effort_hours))[:10]
        
        for todo in sorted_todos:
            print(f"- [ ] {todo.priority.value} {todo.title}")
            print(f"      Category: {todo.category} | Effort: {todo.effort_hours}h")
            print(f"      {todo.description}")
            print()

def main():
    """Main test execution"""
    print("🧪 Phoenix Hydra System Review - Test Mode")
    
    reviewer = PhoenixHydraReviewer()
    results = reviewer.run_complete_review()
    reviewer.print_results(results)
    
    print(f"\n✅ Test completed successfully!")
    print(f"💡 This demonstrates the system review approach for Phoenix Hydra")

if __name__ == "__main__":
    main()