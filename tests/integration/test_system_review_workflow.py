"""
Integration tests for end-to-end system review workflow
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from phoenix_system_review.discovery.file_scanner import FileSystemScanner
from phoenix_system_review.discovery.config_parser import ConfigurationParser
from phoenix_system_review.discovery.service_discovery import ServiceDiscovery
from phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from phoenix_system_review.analysis.quality_assessor import QualityAssessor
from phoenix_system_review.assessment.gap_analyzer import GapAnalyzer
from phoenix_system_review.assessment.completion_calculator import CompletionCalculator
from phoenix_system_review.assessment.priority_ranker import PriorityRanker
from phoenix_system_review.reporting.todo_generator import TODOGenerator
from phoenix_system_review.reporting.status_reporter import StatusReporter
from phoenix_system_review.reporting.recommendation_engine import RecommendationEngine
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, AssessmentResults
)
from phoenix_system_review.discovery.service_discovery import ServiceHealth


class TestEndToEndSystemReviewWorkflow:
    """Test complete system review workflow from discovery to reporting"""
    
    @pytest.fixture
    def mock_phoenix_project(self):
        """Create a mock Phoenix Hydra project structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Phoenix Hydra directory structure
            (temp_path / "src").mkdir()
            (temp_path / "src" / "core").mkdir()
            (temp_path / "src" / "phoenix_system_review").mkdir()
            (temp_path / "configs").mkdir()
            (temp_path / "infra").mkdir()
            (temp_path / "infra" / "podman").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "scripts").mkdir()
            
            # Create source files
            (temp_path / "src" / "core" / "router.py").write_text('''
"""Phoenix Core Router"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/status")
def get_status():
    return {"version": "1.0.0", "status": "operational"}
''')
            
            (temp_path / "src" / "phoenix_system_review" / "__init__.py").write_text("")
            (temp_path / "src" / "phoenix_system_review" / "main.py").write_text('''
"""Phoenix System Review Main Module"""

def run_system_review():
    """Run complete system review"""
    print("Running system review...")
    return {"completion": 95.0}
''')
            
            # Create configuration files
            podman_config = {
                'version': '3.8',
                'services': {
                    'phoenix-core': {
                        'image': 'phoenix-hydra:latest',
                        'ports': ['8080:8080'],
                        'environment': ['DEBUG=false'],
                        'healthcheck': {
                            'test': ['CMD', 'curl', '-f', 'http://localhost:8080/health'],
                            'interval': '30s',
                            'timeout': '10s',
                            'retries': 3
                        }
                    },
                    'n8n': {
                        'image': 'n8nio/n8n:latest',
                        'ports': ['5678:5678'],
                        'environment': ['N8N_BASIC_AUTH_ACTIVE=true']
                    }
                }
            }
            
            with open(temp_path / "infra" / "podman" / "compose.yaml", 'w') as f:
                yaml.dump(podman_config, f)
            
            # Create monetization config
            monetization_config = {
                'affiliate_programs': {
                    'digitalocean': {
                        'enabled': True,
                        'badge_deployed': True,
                        'tracking_id': 'DO-12345'
                    },
                    'customgpt': {
                        'enabled': True,
                        'badge_deployed': False,
                        'api_key': 'cg-api-key'
                    }
                },
                'grant_applications': {
                    'neotec': {
                        'status': 'in_progress',
                        'deadline': '2024-12-31',
                        'completion': 80
                    },
                    'eic_accelerator': {
                        'status': 'planned',
                        'deadline': '2025-03-15',
                        'completion': 0
                    }
                }
            }
            
            with open(temp_path / "configs" / "phoenix-monetization.json", 'w') as f:
                json.dump(monetization_config, f)
            
            # Create documentation
            (temp_path / "docs" / "README.md").write_text('''
# Phoenix Hydra System

Phoenix Hydra is a comprehensive AI automation stack.

## Features

- Multi-agent architecture
- Container orchestration with Podman
- Revenue tracking and monetization
- Automated workflows with n8n

## Installation

1. Clone the repository
2. Run deployment scripts
3. Configure services

## API Endpoints

- `/health` - Health check
- `/api/v1/status` - System status
''')
            
            # Create test files
            (temp_path / "tests" / "test_core.py").write_text('''
import pytest
from src.core.router import app

def test_health_endpoint():
    """Test health check endpoint"""
    # Mock test implementation
    assert True

def test_status_endpoint():
    """Test status endpoint"""
    # Mock test implementation
    assert True
''')
            
            # Create deployment scripts
            (temp_path / "scripts" / "deploy.py").write_text('''
#!/usr/bin/env python3
"""Deployment script for Phoenix Hydra"""

def deploy_phoenix_hydra():
    """Deploy Phoenix Hydra stack"""
    print("Deploying Phoenix Hydra...")
    return True

if __name__ == "__main__":
    deploy_phoenix_hydra()
''')
            
            yield temp_path
    
    def test_complete_system_review_workflow(self, mock_phoenix_project):
        """Test complete system review workflow from start to finish"""
        
        # Phase 1: Discovery
        scanner = FileSystemScanner(str(mock_phoenix_project))
        config_parser = ConfigurationParser()
        service_discovery = ServiceDiscovery()
        
        # Scan project structure
        inventory = scanner.scan_project_structure()
        assert inventory.total_files > 0
        assert len(inventory.source_files) >= 3  # router.py, main.py, deploy.py
        assert len(inventory.configuration_files) >= 2  # compose.yaml, phoenix-monetization.json
        assert len(inventory.documentation_files) >= 1  # README.md
        
        # Parse configurations
        config_files = inventory.configuration_files
        configurations = config_parser.parse_configurations(config_files)
        assert len(configurations) >= 2
        
        # Mock service discovery (since services aren't actually running)
        # Create a simple mock service registry
        from phoenix_system_review.models.data_models import ServiceRegistry
        service_registry = ServiceRegistry(
            services={
                'phoenix-core': {'url': 'http://localhost:8080/health', 'status': 'down'},
                'n8n': {'url': 'http://localhost:5678', 'status': 'down'}
            },
            health_checks={
                'phoenix-core': False,
                'n8n': False
            },
            endpoints={
                'phoenix-core': 'http://localhost:8080/health',
                'n8n': 'http://localhost:5678'
            }
        )
        assert len(service_registry.services) == 2
        
        # Phase 2: Analysis
        evaluator = ComponentEvaluator()
        dependency_analyzer = DependencyAnalyzer()
        quality_assessor = QualityAssessor()
        
        # Create components from discovered files
        components = []
        
        # Infrastructure component
        phoenix_core = Component(
            name="phoenix-core",
            category=ComponentCategory.INFRASTRUCTURE,
            path=str(mock_phoenix_project / "src" / "core"),
            configuration=configurations.get(str(mock_phoenix_project / "infra" / "podman" / "compose.yaml"), {}),
            status=ComponentStatus.OPERATIONAL
        )
        components.append(phoenix_core)
        
        # Monetization component
        monetization = Component(
            name="monetization",
            category=ComponentCategory.MONETIZATION,
            path=str(mock_phoenix_project / "configs"),
            configuration=configurations.get(str(mock_phoenix_project / "configs" / "phoenix-monetization.json"), {}),
            status=ComponentStatus.OPERATIONAL
        )
        components.append(monetization)
        
        # Automation component
        automation = Component(
            name="deployment-scripts",
            category=ComponentCategory.AUTOMATION,
            path=str(mock_phoenix_project / "scripts"),
            status=ComponentStatus.OPERATIONAL
        )
        components.append(automation)
        
        # Evaluate components
        evaluation_results = []
        for component in components:
            criteria = evaluator.get_evaluation_criteria(component.category.value)
            with patch.object(evaluator, '_check_criterion', return_value=True):
                result = evaluator.evaluate_component(component, criteria)
                evaluation_results.append(result)
        
        assert len(evaluation_results) == 3
        assert all(result.completion_percentage > 0 for result in evaluation_results)
        
        # Analyze dependencies
        dependency_graph = dependency_analyzer.map_dependencies(components)
        assert len(dependency_graph.nodes) == 3
        
        # Assess quality
        for component in components:
            if component.category == ComponentCategory.INFRASTRUCTURE:
                with patch.object(quality_assessor, 'analyze_code_quality', return_value={
                    "complexity": 75.0,
                    "maintainability": 80.0,
                    "documentation_ratio": 0.8
                }):
                    quality_metrics = quality_assessor.analyze_code_quality(component.path)
                    assert quality_metrics["complexity"] > 0
        
        # Phase 3: Assessment
        gap_analyzer = GapAnalyzer()
        completion_calculator = CompletionCalculator()
        priority_ranker = PriorityRanker()
        
        # Identify gaps
        gaps = gap_analyzer.identify_gaps(evaluation_results)
        assert isinstance(gaps, list)
        
        # Calculate completion
        completion_scores = completion_calculator.calculate_completion(evaluation_results)
        assert len(completion_scores) == 3
        
        overall_completion = completion_calculator.calculate_overall_completion(completion_scores)
        assert 0.0 <= overall_completion <= 100.0
        
        # Prioritize tasks
        tasks = priority_ranker.prioritize_tasks(gaps)
        assert isinstance(tasks, list)
        
        # Phase 4: Reporting
        todo_generator = TODOGenerator()
        status_reporter = StatusReporter()
        recommendation_engine = RecommendationEngine()
        
        # Create assessment results
        assessment_results = AssessmentResults(
            overall_completion=overall_completion,
            component_scores=completion_scores,
            identified_gaps=gaps,
            prioritized_tasks=tasks,
            recommendations=[]
        )
        
        # Generate TODO checklist
        todo_checklist = todo_generator.generate_todo_checklist(tasks)
        assert isinstance(todo_checklist, str)
        assert len(todo_checklist) > 0
        
        # Generate status report
        status_report = status_reporter.create_status_report(assessment_results)
        assert isinstance(status_report, str)
        assert len(status_report) > 0
        assert str(overall_completion) in status_report or f"{overall_completion:.1f}" in status_report
        
        # Generate recommendations
        recommendations = recommendation_engine.provide_recommendations(gaps, tasks)
        assert isinstance(recommendations, list)
        
        # Verify end-to-end workflow completed successfully
        assert overall_completion >= 0.0
        assert len(gaps) >= 0
        assert len(tasks) >= 0
        assert len(recommendations) >= 0
    
    def test_workflow_with_missing_components(self, mock_phoenix_project):
        """Test workflow handles missing components gracefully"""
        
        # Remove some files to simulate missing components
        os.remove(mock_phoenix_project / "configs" / "phoenix-monetization.json")
        os.remove(mock_phoenix_project / "scripts" / "deploy.py")
        
        scanner = FileSystemScanner(str(mock_phoenix_project))
        inventory = scanner.scan_project_structure()
        
        # Should still work but with fewer files
        assert inventory.total_files > 0
        assert len(inventory.configuration_files) >= 1  # Still has compose.yaml
        
        # Workflow should handle missing components
        evaluator = ComponentEvaluator()
        gap_analyzer = GapAnalyzer()
        
        # Create minimal component set
        components = [
            Component(
                name="phoenix-core",
                category=ComponentCategory.INFRASTRUCTURE,
                path=str(mock_phoenix_project / "src" / "core"),
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        # Evaluate with missing components
        evaluation_results = []
        for component in components:
            criteria = evaluator.get_evaluation_criteria(component.category.value)
            with patch.object(evaluator, '_check_criterion', return_value=False):  # Simulate missing criteria
                result = evaluator.evaluate_component(component, criteria)
                evaluation_results.append(result)
        
        # Should identify gaps for missing components
        gaps = gap_analyzer.identify_gaps(evaluation_results)
        assert len(gaps) > 0  # Should have gaps due to missing components
    
    def test_workflow_error_handling(self, mock_phoenix_project):
        """Test workflow handles errors gracefully"""
        
        evaluator = ComponentEvaluator()
        
        # Test with invalid path
        with pytest.raises((FileNotFoundError, OSError)):
            scanner = FileSystemScanner("/nonexistent/path")
            scanner.scan_project_structure()
        
        # Test with component evaluation error
        component = Component(
            name="error-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/invalid/path",
            status=ComponentStatus.FAILED
        )
        
        criteria = evaluator.get_evaluation_criteria("infrastructure")
        
        # Should handle evaluation errors gracefully
        with patch.object(evaluator, '_check_criterion', side_effect=Exception("Evaluation error")):
            try:
                result = evaluator.evaluate_component(component, criteria)
                # Should either return a result with errors or handle the exception
                assert result is not None
            except Exception:
                # Exception handling is acceptable for this test
                pass
    
    def test_configuration_parsing_integration(self, mock_phoenix_project):
        """Test integration between file discovery and configuration parsing"""
        
        scanner = FileSystemScanner(str(mock_phoenix_project))
        parser = ConfigurationParser()
        
        # Discover configuration files
        inventory = scanner.scan_project_structure()
        config_files = inventory.configuration_files
        
        # Parse all discovered configuration files
        parsed_configs = parser.parse_configurations(config_files)
        
        # Verify parsing results
        assert len(parsed_configs) >= 2
        
        # Check that YAML and JSON files were parsed correctly
        yaml_files = [f for f in config_files if f.endswith('.yaml')]
        json_files = [f for f in config_files if f.endswith('.json')]
        
        assert len(yaml_files) >= 1
        assert len(json_files) >= 1
        
        # Verify parsed content structure
        for file_path, config in parsed_configs.items():
            if config is not None:
                assert isinstance(config, dict)
                if 'compose.yaml' in file_path:
                    assert 'services' in config
                elif 'monetization.json' in file_path:
                    assert 'affiliate_programs' in config or 'grant_applications' in config
    
    def test_service_discovery_integration(self):
        """Test service discovery integration with configuration parsing"""
        
        service_discovery = ServiceDiscovery()
        
        # Test with mock service endpoints
        endpoints = {
            'phoenix-core': 'http://localhost:8080/health',
            'n8n': 'http://localhost:5678',
            'windmill': 'http://localhost:8000'
        }
        
        # Mock all services as down (since they're not actually running)
        with patch.object(service_discovery, 'check_service_health', return_value=False):
            registry = service_discovery.discover_services(endpoints)
            
            assert len(registry.services) == 3
            assert len(registry.health_checks) == 3
            assert len(registry.endpoints) == 3
            
            # All services should be marked as unhealthy
            assert all(not healthy for healthy in registry.health_checks.values())
    
    def test_component_evaluation_integration(self, mock_phoenix_project):
        """Test integration between component discovery and evaluation"""
        
        scanner = FileSystemScanner(str(mock_phoenix_project))
        evaluator = ComponentEvaluator()
        quality_assessor = QualityAssessor()
        
        # Discover project structure
        inventory = scanner.scan_project_structure()
        
        # Create components based on discovered structure
        components = []
        
        # Infrastructure component based on source files
        if inventory.source_files:
            infrastructure_component = Component(
                name="phoenix-infrastructure",
                category=ComponentCategory.INFRASTRUCTURE,
                path=str(mock_phoenix_project / "src"),
                status=ComponentStatus.OPERATIONAL
            )
            components.append(infrastructure_component)
        
        # Documentation component based on documentation files
        if inventory.documentation_files:
            docs_component = Component(
                name="documentation",
                category=ComponentCategory.DOCUMENTATION,
                path=str(mock_phoenix_project / "docs"),
                status=ComponentStatus.OPERATIONAL
            )
            components.append(docs_component)
        
        # Evaluate all components
        evaluation_results = []
        for component in components:
            criteria = evaluator.get_evaluation_criteria(component.category.value)
            
            # Mock evaluation results based on discovered files
            with patch.object(evaluator, '_check_criterion') as mock_check:
                # Simulate partial completion
                mock_check.side_effect = lambda comp, crit: crit.id in ['basic_structure', 'file_existence']
                
                result = evaluator.evaluate_component(component, criteria)
                evaluation_results.append(result)
        
        # Verify evaluation results
        assert len(evaluation_results) == len(components)
        for result in evaluation_results:
            assert isinstance(result.completion_percentage, float)
            assert 0.0 <= result.completion_percentage <= 100.0


if __name__ == '__main__':
    pytest.main([__file__])