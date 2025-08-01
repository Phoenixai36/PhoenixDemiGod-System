"""
Unit tests for n8n analyzer functionality.

Tests individual methods and components of the n8n analyzer
in isolation with mocked dependencies.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import requests

from src.phoenix_system_review.analysis.n8n_analyzer import (
    N8nAnalyzer, WorkflowInfo, WorkflowStatus, WorkflowNode, WorkflowConnection,
    NodeType, N8nAnalysis
)
from src.phoenix_system_review.models.data_models import Priority, Issue


class TestN8nAnalyzer:
    """Unit tests for N8nAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return N8nAnalyzer("/test/project", "http://test:5678")
    
    @pytest.fixture
    def sample_workflow(self):
        """Create sample workflow for testing"""
        nodes = [
            WorkflowNode(
                id="node1",
                name="Test Node",
                type="n8n-nodes-base.set",
                parameters={"test": "value"},
                position=[100, 100]
            ),
            WorkflowNode(
                id="node2", 
                name="HTTP Node",
                type="n8n-nodes-base.httpRequest",
                parameters={
                    "url": "https://sea-turtle-app-nlak2.ondigitalocean.app/api",
                    "headerParameters": {
                        "parameters": [{"name": "x-api-key", "value": "test-key"}]
                    }
                },
                position=[200, 100]
            )
        ]
        
        connections = [
            WorkflowConnection(
                source_node="Test Node",
                target_node="HTTP Node",
                connection_type="main",
                index=0
            )
        ]
        
        return WorkflowInfo(
            name="Test Workflow",
            file_path="/test/workflow.json",
            nodes=nodes,
            connections=connections,
            status=WorkflowStatus.UNKNOWN
        )
    
    def test_init(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.project_root == Path("/test/project")
        assert analyzer.n8n_url == "http://test:5678"
        assert analyzer.workflows_dir == Path("/test/project/configs/n8n-workflows")
        assert "nca-toolkit-extended" in analyzer.expected_workflows
        assert "phoenix-monetization" in analyzer.expected_workflows
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_analyze_workflow_files_no_directory(self, mock_glob, mock_exists, analyzer):
        """Test workflow analysis when directory doesn't exist"""
        mock_exists.return_value = False
        
        workflows = analyzer.analyze_workflow_files()
        
        assert workflows == []
        mock_glob.assert_not_called()
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_analyze_workflow_files_empty_directory(self, mock_glob, mock_exists, analyzer):
        """Test workflow analysis with empty directory"""
        mock_exists.return_value = True
        mock_glob.return_value = []
        
        workflows = analyzer.analyze_workflow_files()
        
        assert workflows == []
        mock_glob.assert_called_once_with("*.json")
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"name": "Test", "nodes": [], "connections": {}}')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_analyze_workflow_files_success(self, mock_glob, mock_exists, mock_file, analyzer):
        """Test successful workflow file analysis"""
        mock_exists.return_value = True
        mock_file_path = MagicMock()
        mock_file_path.stem = "test-workflow"
        mock_glob.return_value = [mock_file_path]
        
        workflows = analyzer.analyze_workflow_files()
        
        assert len(workflows) == 1
        assert workflows[0].name == "Test"
        assert workflows[0].nodes == []
        assert workflows[0].connections == []
    
    @patch('builtins.open', side_effect=Exception("File error"))
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_analyze_workflow_files_error_handling(self, mock_glob, mock_exists, mock_file, analyzer):
        """Test error handling in workflow file analysis"""
        mock_exists.return_value = True
        mock_file_path = MagicMock()
        mock_file_path.stem = "broken-workflow"
        mock_glob.return_value = [mock_file_path]
        
        workflows = analyzer.analyze_workflow_files()
        
        assert len(workflows) == 1
        assert workflows[0].name == "broken-workflow"
        assert workflows[0].status == WorkflowStatus.ERROR
        assert workflows[0].error_count == 1
    
    def test_parse_workflow_file_complete(self, analyzer):
        """Test parsing complete workflow file"""
        workflow_data = {
            "name": "Complete Workflow",
            "nodes": [
                {
                    "id": "node1",
                    "name": "Set Node",
                    "type": "n8n-nodes-base.set",
                    "typeVersion": "3.4",
                    "position": [100, 100],
                    "parameters": {"assignments": {"assignments": []}}
                }
            ],
            "connections": {
                "Set Node": {
                    "main": [[{"node": "Target Node", "type": "main", "index": 0}]]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(workflow_data, f)
            temp_path = Path(f.name)
        
        try:
            workflow_info = analyzer._parse_workflow_file(temp_path)
            
            assert workflow_info.name == "Complete Workflow"
            assert len(workflow_info.nodes) == 1
            assert workflow_info.nodes[0].name == "Set Node"
            assert workflow_info.nodes[0].type == "n8n-nodes-base.set"
            assert len(workflow_info.connections) == 1
            assert workflow_info.connections[0].source_node == "Set Node"
            assert workflow_info.connections[0].target_node == "Target Node"
        finally:
            temp_path.unlink()
    
    @patch('requests.get')
    def test_check_n8n_health_success(self, mock_get, analyzer):
        """Test successful n8n health check"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        is_healthy, version, issues = analyzer.check_n8n_health()
        
        assert is_healthy is True
        assert version is not None
        assert len(issues) == 0
        # Should call healthz endpoint first
        assert mock_get.call_args_list[0][0][0] == "http://test:5678/healthz"
    
    @patch('requests.get')
    def test_check_n8n_health_failure(self, mock_get, analyzer):
        """Test failed n8n health check"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        is_healthy, version, issues = analyzer.check_n8n_health()
        
        assert is_healthy is False
        assert version is None
        assert len(issues) == 1
        assert issues[0].severity == Priority.HIGH
    
    @patch('requests.get')
    def test_check_n8n_health_connection_error(self, mock_get, analyzer):
        """Test n8n health check connection error"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        is_healthy, version, issues = analyzer.check_n8n_health()
        
        assert is_healthy is False
        assert version is None
        assert len(issues) == 1
        assert issues[0].severity == Priority.CRITICAL
        assert "Cannot connect" in issues[0].description
    
    def test_validate_workflow_empty(self, analyzer):
        """Test validation of empty workflow"""
        empty_workflow = WorkflowInfo(
            name="Empty",
            file_path="/test/empty.json",
            nodes=[],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        issues = analyzer.validate_workflow(empty_workflow)
        
        assert len(issues) == 1
        assert issues[0].severity == Priority.HIGH
        assert "no nodes" in issues[0].description
    
    def test_validate_phoenix_integration(self, analyzer, sample_workflow):
        """Test Phoenix integration validation"""
        issues = []
        analyzer._validate_phoenix_integration(sample_workflow, issues)
        
        # Should not have Phoenix integration issues since it uses Phoenix endpoint
        phoenix_issues = [i for i in issues if "phoenix" in i.description.lower()]
        assert len(phoenix_issues) == 0
    
    def test_validate_api_configurations(self, analyzer, sample_workflow):
        """Test API configuration validation"""
        issues = []
        analyzer._validate_api_configurations(sample_workflow, issues)
        
        # Should not have auth header issues since x-api-key is present
        auth_issues = [i for i in issues if "authentication" in i.description.lower()]
        assert len(auth_issues) == 0
    
    def test_validate_workflow_structure_disconnected(self, analyzer):
        """Test validation of workflow with disconnected nodes"""
        disconnected_workflow = WorkflowInfo(
            name="Disconnected",
            file_path="/test/disconnected.json",
            nodes=[
                WorkflowNode("node1", "Node 1", "n8n-nodes-base.set", {}, [100, 100]),
                WorkflowNode("node2", "Node 2", "n8n-nodes-base.set", {}, [200, 100])
            ],
            connections=[],  # No connections
            status=WorkflowStatus.UNKNOWN
        )
        
        issues = []
        analyzer._validate_workflow_structure(disconnected_workflow, issues)
        
        disconnected_issues = [i for i in issues if "disconnected" in i.description.lower()]
        assert len(disconnected_issues) == 1
        assert disconnected_issues[0].severity == Priority.LOW
    
    def test_has_circular_dependencies_true(self, analyzer):
        """Test circular dependency detection - positive case"""
        circular_workflow = WorkflowInfo(
            name="Circular",
            file_path="/test/circular.json",
            nodes=[
                WorkflowNode("node1", "Node A", "n8n-nodes-base.set", {}, [100, 100]),
                WorkflowNode("node2", "Node B", "n8n-nodes-base.set", {}, [200, 100])
            ],
            connections=[
                WorkflowConnection("Node A", "Node B", "main", 0),
                WorkflowConnection("Node B", "Node A", "main", 0)  # Creates cycle
            ],
            status=WorkflowStatus.UNKNOWN
        )
        
        has_cycle = analyzer._has_circular_dependencies(circular_workflow)
        assert has_cycle is True
    
    def test_has_circular_dependencies_false(self, analyzer, sample_workflow):
        """Test circular dependency detection - negative case"""
        has_cycle = analyzer._has_circular_dependencies(sample_workflow)
        assert has_cycle is False
    
    def test_evaluate_workflow_documentation_good(self, analyzer):
        """Test documentation evaluation for well-documented workflow"""
        well_documented = WorkflowInfo(
            name="Well Documented Workflow",
            file_path="/test/documented.json",
            nodes=[
                WorkflowNode(
                    "node1", 
                    "Descriptive Node Name", 
                    "n8n-nodes-base.set", 
                    {"notes": "This node does something important"}, 
                    [100, 100]
                )
            ],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({
                "name": "Well Documented Workflow",
                "meta": {"description": "This workflow does important things"},
                "tags": ["important", "documented"]
            }))):
                issues = analyzer.evaluate_workflow_documentation(well_documented)
        
        # Should have minimal documentation issues
        critical_issues = [i for i in issues if i.severity == Priority.CRITICAL]
        assert len(critical_issues) == 0
    
    def test_evaluate_workflow_documentation_poor(self, analyzer):
        """Test documentation evaluation for poorly documented workflow"""
        poorly_documented = WorkflowInfo(
            name="Bad",  # Short name
            file_path="/test/bad.json",
            nodes=[
                WorkflowNode("node1", "n8n-nodes-base.set", "n8n-nodes-base.set", {}, [100, 100])  # Name same as type
            ],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({
                "name": "Bad"
                # Missing meta, tags, etc.
            }))):
                issues = analyzer.evaluate_workflow_documentation(poorly_documented)
        
        # Should have multiple documentation issues
        assert len(issues) >= 2
        name_issues = [i for i in issues if "name" in i.description.lower()]
        assert len(name_issues) >= 1
    
    def test_assess_nca_workflow_functionality(self, analyzer):
        """Test NCA workflow functionality assessment"""
        nca_workflow = WorkflowInfo(
            name="NCA Toolkit Extended",
            file_path="/test/nca.json",
            nodes=[
                WorkflowNode("var", "Variables", "n8n-nodes-base.set", {}, [100, 100]),
                WorkflowNode("api", "API Call", "n8n-nodes-base.httpRequest", {}, [200, 100]),
                WorkflowNode("check", "Error Check", "n8n-nodes-base.if", {}, [300, 100])
            ],
            connections=[
                WorkflowConnection("Variables", "API Call", "main", 0),
                WorkflowConnection("API Call", "Error Check", "main", 0)
            ],
            status=WorkflowStatus.UNKNOWN
        )
        
        score, issues = analyzer._assess_nca_workflow_functionality(nca_workflow)
        
        assert score == 1.0  # Should have perfect score with all components
        assert len(issues) == 0
    
    def test_assess_monetization_workflow_functionality(self, analyzer):
        """Test monetization workflow functionality assessment"""
        monetization_workflow = WorkflowInfo(
            name="Phoenix Monetization",
            file_path="/test/monetization.json",
            nodes=[
                WorkflowNode(
                    "affiliate", 
                    "Affiliate Tracker", 
                    "n8n-nodes-base.httpRequest", 
                    {"url": "https://api.digitalocean.com/affiliate"}, 
                    [100, 100]
                ),
                WorkflowNode(
                    "revenue", 
                    "Revenue API", 
                    "n8n-nodes-base.httpRequest", 
                    {"url": "http://localhost:8080/revenue/tracking"}, 
                    [200, 100]
                ),
                WorkflowNode(
                    "aggregate", 
                    "Data Aggregation", 
                    "n8n-nodes-base.set", 
                    {"assignments": {"assignments": [{"name": "revenue_total", "value": "100"}]}}, 
                    [300, 100]
                )
            ],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        score, issues = analyzer._assess_monetization_workflow_functionality(monetization_workflow)
        
        assert score == 1.0  # Should have perfect score with all components
        assert len(issues) == 0
    
    def test_assess_grant_workflow_functionality(self, analyzer):
        """Test grant workflow functionality assessment"""
        grant_workflow = WorkflowInfo(
            name="Grant Application Generator",
            file_path="/test/grant.json",
            nodes=[
                WorkflowNode("code", "Document Generator", "n8n-nodes-base.code", {}, [100, 100]),
                WorkflowNode("data", "Data Collection", "n8n-nodes-base.set", {}, [200, 100]),
                WorkflowNode("submit", "Submission Tracker", "n8n-nodes-base.httpRequest", {}, [300, 100])
            ],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        score, issues = analyzer._assess_grant_workflow_functionality(grant_workflow)
        
        assert score == 1.0  # Should have perfect score with all components
        assert len(issues) == 0
    
    def test_assess_generic_workflow_functionality(self, analyzer):
        """Test generic workflow functionality assessment"""
        generic_workflow = WorkflowInfo(
            name="Generic Workflow",
            file_path="/test/generic.json",
            nodes=[
                WorkflowNode("webhook", "Webhook", "n8n-nodes-base.webhook", {}, [100, 100]),
                WorkflowNode("process", "Process", "n8n-nodes-base.code", {}, [200, 100]),
                WorkflowNode("decide", "Decision", "n8n-nodes-base.if", {}, [300, 100])
            ],
            connections=[
                WorkflowConnection("Webhook", "Process", "main", 0),
                WorkflowConnection("Process", "Decision", "main", 0)
            ],
            status=WorkflowStatus.UNKNOWN
        )
        
        score, issues = analyzer._assess_generic_workflow_functionality(generic_workflow)
        
        assert score >= 0.7  # Should have good score with diverse nodes and connections
        assert len(issues) == 0
    
    def test_calculate_workflow_health_score(self, analyzer, sample_workflow):
        """Test workflow health score calculation"""
        # Test with no issues
        health_score = analyzer.calculate_workflow_health_score(sample_workflow, [])
        assert 0.0 <= health_score <= 1.0
        assert health_score > 0.5  # Should be decent with good structure
        
        # Test with critical issues
        critical_issues = [
            Issue(Priority.CRITICAL, "Critical issue", "test", recommendation="Fix it")
        ]
        health_score_with_issues = analyzer.calculate_workflow_health_score(sample_workflow, critical_issues)
        assert health_score_with_issues < health_score
    
    def test_calculate_workflow_health_score_empty(self, analyzer):
        """Test health score calculation for empty workflow"""
        empty_workflow = WorkflowInfo(
            name="Empty",
            file_path="/test/empty.json",
            nodes=[],
            connections=[],
            status=WorkflowStatus.UNKNOWN
        )
        
        health_score = analyzer.calculate_workflow_health_score(empty_workflow, [])
        assert health_score == 0.0
    
    @patch.object(N8nAnalyzer, 'check_n8n_health')
    @patch.object(N8nAnalyzer, 'analyze_workflow_files')
    def test_generate_evaluation_result(self, mock_analyze, mock_health, analyzer):
        """Test evaluation result generation"""
        # Mock workflow analysis
        mock_analyze.return_value = [
            WorkflowInfo("Test Workflow", "/test.json", [], [], WorkflowStatus.UNKNOWN)
        ]
        
        # Mock health check
        mock_health.return_value = (True, "1.0.0", [])
        
        result = analyzer.generate_evaluation_result()
        
        assert result is not None
        assert result.component.name == "n8n_workflows"
        assert result.component.category == "automation"
        assert 0.0 <= result.completion_percentage <= 1.0
        assert 0.0 <= result.quality_score <= 1.0
        assert isinstance(result.criteria_met, list)
        assert isinstance(result.criteria_missing, list)
    
    @patch.object(N8nAnalyzer, 'check_n8n_health')
    @patch.object(N8nAnalyzer, 'analyze_workflow_files')
    def test_generate_analysis_report(self, mock_analyze, mock_health, analyzer):
        """Test analysis report generation"""
        # Mock workflow analysis
        mock_workflows = [
            WorkflowInfo("Workflow 1", "/test1.json", [], [], WorkflowStatus.UNKNOWN),
            WorkflowInfo("Workflow 2", "/test2.json", [], [], WorkflowStatus.UNKNOWN)
        ]
        mock_analyze.return_value = mock_workflows
        
        # Mock health check
        mock_health.return_value = (True, "1.0.0", [])
        
        report = analyzer.generate_analysis_report()
        
        assert isinstance(report, N8nAnalysis)
        assert report.total_workflows == 2
        assert report.n8n_health is True
        assert report.n8n_version == "1.0.0"
        assert 0.0 <= report.health_score <= 1.0
        assert len(report.workflows) == 2