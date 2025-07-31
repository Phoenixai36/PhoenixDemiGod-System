"""
Integration tests for Phoenix Hydra specific integrations.

Tests the coordination between Podman, n8n, and Windmill analyzers
and validates the overall integration functionality.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.phoenix_system_review.analysis.phoenix_hydra_integrator import (
    PhoenixHydraIntegrator,
    PhoenixHydraIntegrationResult
)
from src.phoenix_system_review.analysis.podman_analyzer import PodmanAnalyzer
from src.phoenix_system_review.analysis.n8n_analyzer import N8nAnalyzer
from src.phoenix_system_review.analysis.windmill_analyzer import WindmillAnalyzer
from src.phoenix_system_review.models.data_models import Priority, ComponentStatus, Issue


class TestPhoenixHydraIntegrations:
    """Test suite for Phoenix Hydra integrations"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with Phoenix Hydra structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            (project_root / "infra" / "podman").mkdir(parents=True)
            (project_root / "configs" / "n8n-workflows").mkdir(parents=True)
            (project_root / "windmill-scripts").mkdir(parents=True)
            
            # Create sample Podman compose file
            compose_content = {
                "version": "3.8",
                "services": {
                    "phoenix-core": {
                        "image": "phoenix-hydra/core:latest",
                        "ports": ["8080:8080"],
                        "healthcheck": {
                            "test": ["CMD", "curl", "-f", "http://localhost:8080/health"],
                            "interval": "30s",
                            "timeout": "10s",
                            "retries": 3
                        },
                        "restart": "unless-stopped"
                    },
                    "n8n-phoenix": {
                        "image": "n8nio/n8n:latest",
                        "ports": ["5678:5678"],
                        "environment": {
                            "N8N_HOST": "localhost",
                            "N8N_PORT": "5678"
                        },
                        "restart": "unless-stopped"
                    },
                    "windmill-phoenix": {
                        "image": "windmill/windmill:latest",
                        "ports": ["8000:8000"],
                        "environment": {
                            "WINDMILL_BASE_URL": "http://localhost:8000"
                        },
                        "restart": "unless-stopped"
                    }
                },
                "networks": {
                    "phoenix-network": {
                        "driver": "bridge"
                    }
                }
            }
            
            with open(project_root / "infra" / "podman" / "compose.yaml", "w") as f:
                yaml.dump(compose_content, f)
            
            # Create sample n8n workflow
            n8n_workflow = {
                "name": "Phoenix Monetization Tracker",
                "nodes": [
                    {
                        "id": "start",
                        "name": "Start",
                        "type": "n8n-nodes-base.start",
                        "position": [100, 100],
                        "parameters": {}
                    },
                    {
                        "id": "http_request",
                        "name": "Phoenix API Call",
                        "type": "n8n-nodes-base.httpRequest",
                        "position": [300, 100],
                        "parameters": {
                            "url": "http://localhost:8080/api/revenue",
                            "method": "GET",
                            "headerParameters": {
                                "parameters": [
                                    {"name": "x-api-key", "value": "{{$env.PHOENIX_API_KEY}}"}
                                ]
                            }
                        }
                    }
                ],
                "connections": {
                    "start": {
                        "main": [[{"node": "http_request", "type": "main", "index": 0}]]
                    }
                }
            }
            
            with open(project_root / "configs" / "n8n-workflows" / "phoenix-monetization.json", "w") as f:
                json.dump(n8n_workflow, f)
            
            # Create sample Windmill configuration
            windmill_config = {
                "name": "phoenix-hydra-workspace",
                "version": "1.2.0",
                "scripts": [
                    {
                        "path": "monetization/affiliate_badges",
                        "language": "typescript",
                        "summary": "Manage affiliate program badges",
                        "content": """
export async function main() {
    const phoenixApi = 'http://localhost:8080';
    const response = await fetch(`${phoenixApi}/api/affiliates`);
    return await response.json();
}
                        """.strip()
                    }
                ],
                "flows": [
                    {
                        "path": "automation/revenue_tracking",
                        "summary": "Automated revenue tracking flow",
                        "value": {
                            "modules": [
                                {
                                    "id": "a",
                                    "value": {
                                        "type": "script",
                                        "path": "monetization/affiliate_badges"
                                    }
                                }
                            ]
                        }
                    }
                ],
                "resources": [
                    {
                        "path": "phoenix_api",
                        "resource_type": "http",
                        "value": {
                            "base_url": "http://localhost:8080"
                        }
                    }
                ]
            }
            
            with open(project_root / "windmill-scripts" / "windmill-phoenix-config.json", "w") as f:
                json.dump(windmill_config, f)
            
            yield str(project_root)
    
    def test_integrator_initialization(self, temp_project_dir):
        """Test that the integrator initializes all analyzers correctly"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        assert isinstance(integrator.podman_analyzer, PodmanAnalyzer)
        assert isinstance(integrator.n8n_analyzer, N8nAnalyzer)
        assert isinstance(integrator.windmill_analyzer, WindmillAnalyzer)
        
        assert integrator.project_root == Path(temp_project_dir)
        assert "service_connectivity" in integrator.integration_rules
        assert "configuration_consistency" in integrator.integration_rules
        assert "workflow_integration" in integrator.integration_rules
    
    def test_podman_integration_analysis(self, temp_project_dir):
        """Test Podman integration analysis"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Mock subprocess calls for Podman
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'  # Empty container list
            
            result = integrator._analyze_podman_integration()
            
            assert result is not None
            assert result.component.name == "podman_infrastructure"
            assert "compose_files_present" in result.criteria_met
    
    def test_n8n_integration_analysis(self, temp_project_dir):
        """Test n8n integration analysis"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Mock requests for n8n health check
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = integrator._analyze_n8n_integration()
            
            assert result is not None
            assert result.component.name == "n8n_workflows"
            assert "workflows_present" in result.criteria_met
    
    def test_windmill_integration_analysis(self, temp_project_dir):
        """Test Windmill integration analysis"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Mock requests for Windmill health check
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"windmill_version": "1.0.0"}
            mock_get.return_value = mock_response
            
            result = integrator._analyze_windmill_integration()
            
            assert result is not None
            assert result.component.name == "windmill_gitops"
    
    @patch('subprocess.run')
    @patch('requests.get')
    def test_comprehensive_integration_analysis(self, mock_requests, mock_subprocess, temp_project_dir):
        """Test comprehensive integration analysis"""
        # Mock subprocess for Podman
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '[]'
        
        # Mock requests for health checks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"windmill_version": "1.0.0"}
        mock_requests.return_value = mock_response
        
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        result = integrator.analyze_all_integrations()
        
        assert isinstance(result, PhoenixHydraIntegrationResult)
        assert result.podman_analysis is not None
        assert result.n8n_analysis is not None
        assert result.windmill_analysis is not None
        assert isinstance(result.integration_health_score, float)
        assert 0.0 <= result.integration_health_score <= 1.0
        assert isinstance(result.cross_integration_issues, list)
        assert isinstance(result.integration_recommendations, list)
    
    def test_cross_integration_validation(self, temp_project_dir):
        """Test cross-integration validation logic"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Create mock evaluation results
        from src.phoenix_system_review.models.data_models import Component, EvaluationResult
        
        podman_component = Component(
            name="podman_infrastructure",
            category="infrastructure",
            path="/infra/podman",
            status=ComponentStatus.OPERATIONAL
        )
        podman_result = EvaluationResult(
            component=podman_component,
            criteria_met=["compose_files_present", "containers_running"],
            criteria_missing=[],
            completion_percentage=85.0,
            quality_score=0.8,
            issues=[]
        )
        
        n8n_component = Component(
            name="n8n_workflows",
            category="automation",
            path="/configs/n8n-workflows",
            status=ComponentStatus.OPERATIONAL
        )
        n8n_result = EvaluationResult(
            component=n8n_component,
            criteria_met=["workflows_present", "n8n_service_healthy"],
            criteria_missing=[],
            completion_percentage=75.0,
            quality_score=0.7,
            issues=[]
        )
        
        windmill_component = Component(
            name="windmill_gitops",
            category="automation",
            path="/windmill-scripts",
            status=ComponentStatus.OPERATIONAL
        )
        windmill_result = EvaluationResult(
            component=windmill_component,
            criteria_met=["windmill_configs_present"],
            criteria_missing=["windmill_service_healthy"],
            completion_percentage=60.0,
            quality_score=0.6,
            issues=[]
        )
        
        cross_issues = integrator._analyze_cross_integrations(
            podman_result, n8n_result, windmill_result
        )
        
        assert isinstance(cross_issues, list)
        # Should have at least one issue due to Windmill service not being healthy
        assert len(cross_issues) > 0
    
    def test_integration_health_score_calculation(self, temp_project_dir):
        """Test integration health score calculation"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Create mock evaluation results with different scores
        from src.phoenix_system_review.models.data_models import Component, EvaluationResult, Issue
        
        podman_result = EvaluationResult(
            component=Component("podman", "infrastructure", "/podman", ComponentStatus.OPERATIONAL),
            criteria_met=[], criteria_missing=[], completion_percentage=80.0, quality_score=0.8, issues=[]
        )
        
        n8n_result = EvaluationResult(
            component=Component("n8n", "automation", "/n8n", ComponentStatus.OPERATIONAL),
            criteria_met=[], criteria_missing=[], completion_percentage=70.0, quality_score=0.7, issues=[]
        )
        
        windmill_result = EvaluationResult(
            component=Component("windmill", "automation", "/windmill", ComponentStatus.DEGRADED),
            criteria_met=[], criteria_missing=[], completion_percentage=60.0, quality_score=0.6, issues=[]
        )
        
        # Test with no cross-integration issues
        score = integrator._calculate_integration_health_score(
            podman_result, n8n_result, windmill_result, []
        )
        
        # Should be weighted average: 0.4*0.8 + 0.3*0.7 + 0.3*0.6 = 0.71
        assert 0.70 <= score <= 0.72
        
        # Test with critical cross-integration issues
        critical_issues = [
            Issue(Priority.CRITICAL, "Critical integration failure", "test", "Fix it")
        ]
        
        score_with_issues = integrator._calculate_integration_health_score(
            podman_result, n8n_result, windmill_result, critical_issues
        )
        
        # Should be lower due to penalty
        assert score_with_issues < score
        assert score_with_issues >= 0.0
    
    def test_integration_recommendations_generation(self, temp_project_dir):
        """Test integration recommendations generation"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Create mock results with various completion levels
        from src.phoenix_system_review.models.data_models import Component, EvaluationResult, Issue
        
        low_completion_result = EvaluationResult(
            component=Component("test", "infrastructure", "/test", ComponentStatus.DEGRADED),
            criteria_met=[], criteria_missing=[], completion_percentage=50.0, quality_score=0.5, issues=[]
        )
        
        cross_issues = [
            Issue(Priority.CRITICAL, "Critical issue", "test", "Critical recommendation"),
            Issue(Priority.HIGH, "High issue", "test", "High recommendation"),
            Issue(Priority.MEDIUM, "Medium issue", "test", "Medium recommendation")
        ]
        
        recommendations = integrator._generate_integration_recommendations(
            low_completion_result, low_completion_result, low_completion_result, cross_issues
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should have critical recommendations first
        critical_recs = [r for r in recommendations if "CRITICAL:" in r]
        assert len(critical_recs) > 0
        
        # Should have component-specific recommendations
        component_recs = [r for r in recommendations if "Improve" in r or "Enhance" in r]
        assert len(component_recs) > 0
    
    def test_integration_summary(self, temp_project_dir):
        """Test integration summary generation"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Mock the analyze_all_integrations method
        with patch.object(integrator, 'analyze_all_integrations') as mock_analyze:
            mock_result = PhoenixHydraIntegrationResult()
            mock_result.integration_health_score = 0.75
            mock_result.cross_integration_issues = [
                Issue(Priority.HIGH, "Test issue", "test", "Test recommendation")
            ]
            mock_result.integration_recommendations = ["Test recommendation 1", "Test recommendation 2"]
            
            # Mock individual results
            from src.phoenix_system_review.models.data_models import Component, EvaluationResult
            mock_result.podman_analysis = EvaluationResult(
                component=Component("podman", "infrastructure", "/podman", ComponentStatus.OPERATIONAL),
                criteria_met=[], criteria_missing=[], completion_percentage=80.0, quality_score=0.8, issues=[]
            )
            mock_result.n8n_analysis = EvaluationResult(
                component=Component("n8n", "automation", "/n8n", ComponentStatus.OPERATIONAL),
                criteria_met=[], criteria_missing=[], completion_percentage=70.0, quality_score=0.7, issues=[]
            )
            mock_result.windmill_analysis = EvaluationResult(
                component=Component("windmill", "automation", "/windmill", ComponentStatus.OPERATIONAL),
                criteria_met=[], criteria_missing=[], completion_percentage=60.0, quality_score=0.6, issues=[]
            )
            
            mock_analyze.return_value = mock_result
            
            summary = integrator.get_integration_summary()
            
            assert isinstance(summary, dict)
            assert "integration_health_score" in summary
            assert "components_analyzed" in summary
            assert "component_scores" in summary
            assert "total_issues" in summary
            assert "integration_status" in summary
            
            assert summary["integration_health_score"] == 0.75
            assert summary["components_analyzed"]["podman"] is True
            assert summary["components_analyzed"]["n8n"] is True
            assert summary["components_analyzed"]["windmill"] is True
            assert summary["integration_status"] == "degraded"  # 0.75 is between 0.5 and 0.8
    
    def test_error_handling_in_integration_analysis(self, temp_project_dir):
        """Test error handling during integration analysis"""
        integrator = PhoenixHydraIntegrator(temp_project_dir)
        
        # Mock analyzers to raise exceptions
        with patch.object(integrator.podman_analyzer, 'generate_evaluation_result', side_effect=Exception("Podman error")):
            with patch.object(integrator.n8n_analyzer, 'analyze_workflow_files', side_effect=Exception("n8n error")):
                with patch.object(integrator.windmill_analyzer, 'generate_evaluation_result', side_effect=Exception("Windmill error")):
                    
                    result = integrator.analyze_all_integrations()
                    
                    # Should still return a result object
                    assert isinstance(result, PhoenixHydraIntegrationResult)
                    
                    # Should have fallback evaluation results with errors
                    assert result.podman_analysis is not None
                    assert len(result.podman_analysis.issues) > 0
                    assert "Podman error" in str(result.podman_analysis.issues[0].description)
                    
                    assert result.n8n_analysis is not None
                    assert len(result.n8n_analysis.issues) > 0
                    assert "n8n error" in str(result.n8n_analysis.issues[0].description)
                    
                    assert result.windmill_analysis is not None
                    assert len(result.windmill_analysis.issues) > 0
                    assert "Windmill error" in str(result.windmill_analysis.issues[0].description)
                    
                    # Health score should be low due to errors
                    assert result.integration_health_score < 0.5


if __name__ == "__main__":
    pytest.main([__file__])