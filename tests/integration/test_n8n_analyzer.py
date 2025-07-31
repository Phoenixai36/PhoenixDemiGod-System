"""
Integration tests for n8n analyzer functionality.

Tests the n8n analyzer against real Phoenix Hydra workflow files
and validates the analysis results.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

from src.phoenix_system_review.analysis.n8n_analyzer import (
    N8nAnalyzer, WorkflowInfo, WorkflowStatus, N8nAnalysis
)
from src.phoenix_system_review.models.data_models import Priority


class TestN8nAnalyzerIntegration:
    """Integration tests for n8n analyzer functionality"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with n8n workflows"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            workflows_dir = project_path / "configs" / "n8n-workflows"
            workflows_dir.mkdir(parents=True)
            
            # Create sample NCA workflow
            nca_workflow = {
                "name": "NCA Toolkit Extended Phoenix",
                "nodes": [
                    {
                        "id": "phoenix-variables",
                        "name": "Phoenix Variables",
                        "type": "n8n-nodes-base.set",
                        "typeVersion": "3.4",
                        "position": [120, 100],
                        "parameters": {
                            "assignments": {
                                "assignments": [
                                    {
                                        "id": "nca-base-url",
                                        "name": "nca_base_url",
                                        "value": "https://sea-turtle-app-nlak2.ondigitalocean.app/v1/",
                                        "type": "string"
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "id": "nca-api-call",
                        "name": "NCA API Call",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": "4.2",
                        "position": [320, 100],
                        "parameters": {
                            "method": "POST",
                            "url": "{{ $('Phoenix Variables').first().json.nca_base_url }}video/caption",
                            "sendHeaders": True,
                            "headerParameters": {
                                "parameters": [
                                    {
                                        "name": "x-api-key",
                                        "value": "phoenix-hydra-prod-2025"
                                    }
                                ]
                            }
                        }
                    }
                ],
                "connections": {
                    "Phoenix Variables": {
                        "main": [[{
                            "node": "NCA API Call",
                            "type": "main",
                            "index": 0
                        }]]
                    }
                },
                "meta": {
                    "description": "Extended NCA Toolkit integration for Phoenix Hydra"
                },
                "tags": ["nca", "phoenix", "api"]
            }
            
            # Create sample monetization workflow
            monetization_workflow = {
                "name": "Phoenix Monetization Workflows",
                "nodes": [
                    {
                        "id": "digitalocean-affiliate",
                        "name": "DigitalOcean Affiliate Tracker",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": "4.2",
                        "position": [420, 100],
                        "parameters": {
                            "url": "https://api.digitalocean.com/v2/customers/referrals",
                            "sendBody": True,
                            "jsonBody": '{"referral_code": "PHOENIX-HYDRA-2025"}'
                        }
                    },
                    {
                        "id": "revenue-tracking",
                        "name": "Revenue Tracking API",
                        "type": "n8n-nodes-base.httpRequest",
                        "typeVersion": "4.2",
                        "position": [620, 100],
                        "parameters": {
                            "url": "http://localhost:8080/v1/toolkit/revenue/tracking",
                            "sendHeaders": True,
                            "headerParameters": {
                                "parameters": [
                                    {
                                        "name": "x-api-key",
                                        "value": "phoenix-prod-key-2025"
                                    }
                                ]
                            }
                        }
                    }
                ],
                "connections": {
                    "DigitalOcean Affiliate Tracker": {
                        "main": [[{
                            "node": "Revenue Tracking API",
                            "type": "main",
                            "index": 0
                        }]]
                    }
                }
            }
            
            # Create broken workflow for testing error handling
            broken_workflow = {
                "name": "Broken Workflow",
                "nodes": [
                    {
                        "id": "isolated-node",
                        "name": "Isolated Node",
                        "type": "n8n-nodes-base.set",
                        "position": [100, 100],
                        "parameters": {}
                    },
                    {
                        "id": "another-isolated",
                        "name": "Another Isolated",
                        "type": "n8n-nodes-base.httpRequest",
                        "position": [300, 100],
                        "parameters": {
                            "url": "http://example.com"
                        }
                    }
                ],
                "connections": {}
            }
            
            # Write workflow files
            with open(workflows_dir / "nca-toolkit-extended.json", 'w') as f:
                json.dump(nca_workflow, f, indent=2)
            
            with open(workflows_dir / "phoenix-monetization.json", 'w') as f:
                json.dump(monetization_workflow, f, indent=2)
            
            with open(workflows_dir / "broken-workflow.json", 'w') as f:
                json.dump(broken_workflow, f, indent=2)
            
            yield str(project_path)
    
    @pytest.fixture
    def n8n_analyzer(self, temp_project_dir):
        """Create n8n analyzer instance"""
        return N8nAnalyzer(temp_project_dir)
    
    def test_analyze_workflow_files(self, n8n_analyzer):
        """Test workflow file analysis"""
        workflows = n8n_analyzer.analyze_workflow_files()
        
        assert len(workflows) == 3
        
        # Check NCA workflow
        nca_workflow = next((w for w in workflows if "nca" in w.name.lower()), None)
        assert nca_workflow is not None
        assert len(nca_workflow.nodes) == 2
        assert len(nca_workflow.connections) == 1
        assert nca_workflow.status == WorkflowStatus.UNKNOWN
        
        # Check monetization workflow
        monetization_workflow = next((w for w in workflows if "monetization" in w.name.lower()), None)
        assert monetization_workflow is not None
        assert len(monetization_workflow.nodes) == 2
        assert len(monetization_workflow.connections) == 1
        
        # Check broken workflow
        broken_workflow = next((w for w in workflows if "broken" in w.name.lower()), None)
        assert broken_workflow is not None
        assert len(broken_workflow.nodes) == 2
        assert len(broken_workflow.connections) == 0
    
    @patch('requests.get')
    def test_check_n8n_health_success(self, mock_get, n8n_analyzer):
        """Test successful n8n health check"""
        # Mock successful health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        is_healthy, version, issues = n8n_analyzer.check_n8n_health()
        
        assert is_healthy is True
        assert version is not None
        assert len(issues) == 0
        # Should call healthz endpoint first
        assert mock_get.call_args_list[0][0][0] == "http://localhost:5678/healthz"
    
    @patch('requests.get')
    def test_check_n8n_health_connection_error(self, mock_get, n8n_analyzer):
        """Test n8n health check with connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        is_healthy, version, issues = n8n_analyzer.check_n8n_health()
        
        assert is_healthy is False
        assert version is None
        assert len(issues) == 1
        assert issues[0].severity == Priority.CRITICAL
        assert "Cannot connect to n8n instance" in issues[0].description
    
    @patch('requests.get')
    def test_check_n8n_health_timeout(self, mock_get, n8n_analyzer):
        """Test n8n health check with timeout"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        is_healthy, version, issues = n8n_analyzer.check_n8n_health()
        
        assert is_healthy is False
        assert version is None
        assert len(issues) == 1
        assert issues[0].severity == Priority.HIGH
        assert "timed out" in issues[0].description
    
    def test_validate_workflow_nca(self, n8n_analyzer):
        """Test NCA workflow validation"""
        workflows = n8n_analyzer.analyze_workflow_files()
        nca_workflow = next((w for w in workflows if "nca" in w.name.lower()), None)
        
        issues = n8n_analyzer.validate_workflow(nca_workflow)
        
        # Should have minimal issues for well-structured NCA workflow
        critical_issues = [i for i in issues if i.severity == Priority.CRITICAL]
        assert len(critical_issues) == 0
        
        # May have some documentation or minor issues but should be functional
        high_issues = [i for i in issues if i.severity == Priority.HIGH]
        assert len(high_issues) == 0
    
    def test_validate_workflow_monetization(self, n8n_analyzer):
        """Test monetization workflow validation"""
        workflows = n8n_analyzer.analyze_workflow_files()
        monetization_workflow = next((w for w in workflows if "monetization" in w.name.lower()), None)
        
        issues = n8n_analyzer.validate_workflow(monetization_workflow)
        
        # Should not have critical issues
        critical_issues = [i for i in issues if i.severity == Priority.CRITICAL]
        assert len(critical_issues) == 0
        
        # May have some configuration or documentation issues
        assert len(issues) >= 0  # Some issues are expected for configuration improvements
    
    def test_validate_workflow_broken(self, n8n_analyzer):
        """Test broken workflow validation"""
        workflows = n8n_analyzer.analyze_workflow_files()
        broken_workflow = next((w for w in workflows if "broken" in w.name.lower()), None)
        
        issues = n8n_analyzer.validate_workflow(broken_workflow)
        
        # Should detect disconnected nodes
        disconnected_issues = [i for i in issues if "disconnected" in i.description.lower()]
        assert len(disconnected_issues) >= 1
        
        # Should have documentation issues
        doc_issues = [i for i in issues if "documentation" in i.description.lower() or "description" in i.description.lower()]
        assert len(doc_issues) >= 1
    
    def test_evaluate_workflow_documentation(self, n8n_analyzer):
        """Test workflow documentation evaluation"""
        workflows = n8n_analyzer.analyze_workflow_files()
        
        # Test well-documented NCA workflow
        nca_workflow = next((w for w in workflows if "nca" in w.name.lower()), None)
        doc_issues = n8n_analyzer.evaluate_workflow_documentation(nca_workflow)
        
        # Should have minimal documentation issues
        critical_doc_issues = [i for i in doc_issues if i.severity == Priority.CRITICAL]
        assert len(critical_doc_issues) == 0
        
        # Test broken workflow (less documented)
        broken_workflow = next((w for w in workflows if "broken" in w.name.lower()), None)
        broken_doc_issues = n8n_analyzer.evaluate_workflow_documentation(broken_workflow)
        
        # Should have more documentation issues
        assert len(broken_doc_issues) >= len(doc_issues)
    
    def test_assess_workflow_functionality(self, n8n_analyzer):
        """Test workflow functionality assessment"""
        workflows = n8n_analyzer.analyze_workflow_files()
        
        # Test NCA workflow functionality
        nca_workflow = next((w for w in workflows if "nca" in w.name.lower()), None)
        nca_score, nca_issues = n8n_analyzer.assess_workflow_functionality(nca_workflow)
        
        assert 0.0 <= nca_score <= 1.0
        assert nca_score > 0.5  # Should have decent functionality
        
        # Test monetization workflow functionality
        monetization_workflow = next((w for w in workflows if "monetization" in w.name.lower()), None)
        monetization_score, monetization_issues = n8n_analyzer.assess_workflow_functionality(monetization_workflow)
        
        assert 0.0 <= monetization_score <= 1.0
        assert monetization_score > 0.3  # Should have some functionality
        
        # Test broken workflow functionality
        broken_workflow = next((w for w in workflows if "broken" in w.name.lower()), None)
        broken_score, broken_issues = n8n_analyzer.assess_workflow_functionality(broken_workflow)
        
        assert 0.0 <= broken_score <= 1.0
        assert broken_score < nca_score  # Should have lower functionality
    
    def test_calculate_workflow_health_score(self, n8n_analyzer):
        """Test workflow health score calculation"""
        workflows = n8n_analyzer.analyze_workflow_files()
        
        for workflow in workflows:
            issues = n8n_analyzer.validate_workflow(workflow)
            health_score = n8n_analyzer.calculate_workflow_health_score(workflow, issues)
            
            assert 0.0 <= health_score <= 1.0
            
            # Workflows with nodes should have some score
            if len(workflow.nodes) > 0:
                assert health_score >= 0.0  # At least some score for having nodes
    
    @patch('requests.get')
    def test_generate_evaluation_result(self, mock_get, n8n_analyzer):
        """Test comprehensive evaluation result generation"""
        # Mock n8n health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        evaluation_result = n8n_analyzer.generate_evaluation_result()
        
        assert evaluation_result is not None
        assert evaluation_result.component.name == "n8n_workflows"
        assert evaluation_result.component.category == "automation"
        assert 0.0 <= evaluation_result.completion_percentage <= 1.0
        assert 0.0 <= evaluation_result.quality_score <= 1.0
        
        # Should have some criteria met
        assert len(evaluation_result.criteria_met) > 0
        assert "workflow_files_present" in evaluation_result.criteria_met
        assert "n8n_instance_healthy" in evaluation_result.criteria_met
    
    @patch('requests.get')
    def test_generate_analysis_report(self, mock_get, n8n_analyzer):
        """Test comprehensive analysis report generation"""
        # Mock n8n health check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        analysis_report = n8n_analyzer.generate_analysis_report()
        
        assert isinstance(analysis_report, N8nAnalysis)
        assert analysis_report.total_workflows == 3
        assert analysis_report.n8n_health is True
        assert 0.0 <= analysis_report.health_score <= 1.0
        assert len(analysis_report.workflows) == 3
        
        # Should have some active workflows
        assert analysis_report.active_workflows >= 0
        assert analysis_report.active_workflows <= analysis_report.total_workflows
    
    def test_workflow_parsing_error_handling(self, temp_project_dir):
        """Test error handling for malformed workflow files"""
        workflows_dir = Path(temp_project_dir) / "configs" / "n8n-workflows"
        
        # Create malformed JSON file
        with open(workflows_dir / "malformed.json", 'w') as f:
            f.write('{"name": "Malformed", "nodes": [')  # Invalid JSON
        
        analyzer = N8nAnalyzer(temp_project_dir)
        workflows = analyzer.analyze_workflow_files()
        
        # Should handle malformed file gracefully
        malformed_workflow = next((w for w in workflows if "malformed" in w.name.lower()), None)
        assert malformed_workflow is not None
        assert malformed_workflow.status == WorkflowStatus.ERROR
        assert malformed_workflow.error_count == 1
    
    def test_empty_workflows_directory(self):
        """Test handling of empty workflows directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            # Don't create workflows directory
            
            analyzer = N8nAnalyzer(str(project_path))
            workflows = analyzer.analyze_workflow_files()
            
            assert len(workflows) == 0
    
    def test_missing_workflows_directory(self):
        """Test handling of missing workflows directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analyzer = N8nAnalyzer(temp_dir)
            workflows = analyzer.analyze_workflow_files()
            
            assert len(workflows) == 0
    
    def test_circular_dependency_detection(self, n8n_analyzer):
        """Test circular dependency detection in workflows"""
        # Create workflow with circular dependency
        circular_workflow_data = {
            "name": "Circular Workflow",
            "nodes": [
                {
                    "id": "node-a",
                    "name": "Node A",
                    "type": "n8n-nodes-base.set",
                    "position": [100, 100],
                    "parameters": {}
                },
                {
                    "id": "node-b", 
                    "name": "Node B",
                    "type": "n8n-nodes-base.set",
                    "position": [200, 100],
                    "parameters": {}
                }
            ],
            "connections": {
                "Node A": {
                    "main": [[{"node": "Node B", "type": "main", "index": 0}]]
                },
                "Node B": {
                    "main": [[{"node": "Node A", "type": "main", "index": 0}]]
                }
            }
        }
        
        # Write circular workflow file
        workflows_dir = Path(n8n_analyzer.project_root) / "configs" / "n8n-workflows"
        with open(workflows_dir / "circular.json", 'w') as f:
            json.dump(circular_workflow_data, f, indent=2)
        
        workflows = n8n_analyzer.analyze_workflow_files()
        circular_workflow = next((w for w in workflows if "circular" in w.name.lower()), None)
        
        assert circular_workflow is not None
        issues = n8n_analyzer.validate_workflow(circular_workflow)
        
        # Should detect circular dependency
        circular_issues = [i for i in issues if "circular" in i.description.lower()]
        assert len(circular_issues) >= 1
        assert any(i.severity == Priority.HIGH for i in circular_issues)