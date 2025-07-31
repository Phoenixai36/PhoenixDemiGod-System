"""
n8n Workflow Analysis for Phoenix Hydra System Review

Provides specialized analysis capabilities for n8n workflow configurations,
health assessment, and functionality evaluation.
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..models.data_models import Component, ComponentStatus, Issue, Priority, EvaluationResult


class WorkflowStatus(Enum):
    """Workflow status indicators"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"


class NodeType(Enum):
    """n8n node types"""
    HTTP_REQUEST = "n8n-nodes-base.httpRequest"
    SET = "n8n-nodes-base.set"
    WEBHOOK = "n8n-nodes-base.webhook"
    CRON = "n8n-nodes-base.cron"
    CODE = "n8n-nodes-base.code"
    IF = "n8n-nodes-base.if"
    SWITCH = "n8n-nodes-base.switch"
    MERGE = "n8n-nodes-base.merge"


@dataclass
class WorkflowNode:
    """Information about a workflow node"""
    id: str
    name: str
    type: str
    parameters: Dict[str, Any]
    position: List[int]
    type_version: Optional[str] = None


@dataclass
class WorkflowConnection:
    """Information about workflow connections"""
    source_node: str
    target_node: str
    connection_type: str = "main"
    index: int = 0


@dataclass
class WorkflowInfo:
    """Information about an n8n workflow"""
    name: str
    file_path: str
    nodes: List[WorkflowNode]
    connections: List[WorkflowConnection]
    status: WorkflowStatus
    last_execution: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0


@dataclass
class N8nAnalysis:
    """Analysis results for n8n workflows"""
    workflows: List[WorkflowInfo]
    n8n_health: bool
    n8n_version: Optional[str]
    total_workflows: int
    active_workflows: int
    issues: List[Issue]
    health_score: float


class N8nAnalyzer:
    """
    Analyzer for n8n workflow infrastructure in Phoenix Hydra.
    
    Provides comprehensive analysis of:
    - n8n workflow configurations
    - Workflow health and functionality
    - Node validation and best practices
    - Integration with Phoenix Hydra services
    """
    
    def __init__(self, project_root: str, n8n_url: str = "http://localhost:5678"):
        """
        Initialize n8n analyzer.
        
        Args:
            project_root: Root directory of the Phoenix Hydra project
            n8n_url: URL of the n8n instance
        """
        self.project_root = Path(project_root)
        self.n8n_url = n8n_url
        self.workflows_dir = self.project_root / "configs" / "n8n-workflows"
        
        # Expected Phoenix Hydra workflows
        self.expected_workflows = {
            "nca-toolkit-extended": {
                "required_nodes": ["Phoenix Variables", "NCA API Call"],
                "required_connections": 1,
                "description": "Extended NCA Toolkit integration workflow"
            },
            "phoenix-monetization": {
                "required_nodes": ["DigitalOcean Affiliate Tracker", "Revenue Tracking API"],
                "required_connections": 1,
                "description": "Phoenix Hydra monetization tracking workflow"
            },
            "grant-application": {
                "required_nodes": ["NEOTEC Generator", "Application Tracker"],
                "required_connections": 1,
                "description": "Automated grant application workflow"
            }
        }
        
        # Phoenix Hydra specific node validation rules
        self.validation_rules = {
            "api_endpoints": [
                "sea-turtle-app-nlak2.ondigitalocean.app",
                "localhost:8080",
                "localhost:8081"
            ],
            "required_headers": ["x-api-key", "authorization"],
            "monetization_sources": [
                "digitalocean_affiliate",
                "customgpt_affiliate", 
                "aws_marketplace",
                "huggingface_marketplace"
            ]
        }
    
    def analyze_workflow_files(self) -> List[WorkflowInfo]:
        """
        Analyze n8n workflow files in the configurations directory.
        
        Returns:
            List of WorkflowInfo objects for each workflow file
        """
        workflows = []
        
        if not self.workflows_dir.exists():
            return workflows
        
        # Find all JSON workflow files
        workflow_files = list(self.workflows_dir.glob("*.json"))
        
        for workflow_file in workflow_files:
            try:
                workflow_info = self._parse_workflow_file(workflow_file)
                workflows.append(workflow_info)
            except Exception as e:
                # Create workflow info with error
                workflow_info = WorkflowInfo(
                    name=workflow_file.stem,
                    file_path=str(workflow_file),
                    nodes=[],
                    connections=[],
                    status=WorkflowStatus.ERROR,
                    error_count=1
                )
                workflows.append(workflow_info)
        
        return workflows
    
    def _parse_workflow_file(self, workflow_file: Path) -> WorkflowInfo:
        """
        Parse a single n8n workflow file.
        
        Args:
            workflow_file: Path to the workflow JSON file
            
        Returns:
            WorkflowInfo object with parsed workflow data
        """
        with open(workflow_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Parse nodes
        nodes = []
        if 'nodes' in workflow_data:
            for node_data in workflow_data['nodes']:
                node = WorkflowNode(
                    id=node_data.get('id', ''),
                    name=node_data.get('name', ''),
                    type=node_data.get('type', ''),
                    parameters=node_data.get('parameters', {}),
                    position=node_data.get('position', [0, 0]),
                    type_version=node_data.get('typeVersion')
                )
                nodes.append(node)
        
        # Parse connections
        connections = []
        if 'connections' in workflow_data:
            for source_node, targets in workflow_data['connections'].items():
                if 'main' in targets:
                    for i, target_list in enumerate(targets['main']):
                        for target in target_list:
                            connection = WorkflowConnection(
                                source_node=source_node,
                                target_node=target['node'],
                                connection_type=target.get('type', 'main'),
                                index=target.get('index', 0)
                            )
                            connections.append(connection)
        
        return WorkflowInfo(
            name=workflow_data.get('name', workflow_file.stem),
            file_path=str(workflow_file),
            nodes=nodes,
            connections=connections,
            status=WorkflowStatus.UNKNOWN  # Will be determined by runtime check
        )
    
    def check_n8n_health(self) -> Tuple[bool, Optional[str], List[Issue]]:
        """
        Check the health status of the n8n instance.
        
        Returns:
            Tuple of (is_healthy, version, list_of_issues)
        """
        issues = []
        
        try:
            # Check n8n health endpoint
            response = requests.get(f"{self.n8n_url}/healthz", timeout=10)
            
            if response.status_code == 200:
                # Try to get version information
                try:
                    version_response = requests.get(f"{self.n8n_url}/rest/login", timeout=5)
                    version = None
                    if version_response.status_code in [200, 401]:  # 401 is expected without auth
                        # n8n is responding
                        version = "unknown"
                except:
                    version = "unknown"
                
                return True, version, issues
            else:
                issues.append(Issue(
                    severity=Priority.HIGH,
                    description=f"n8n health check failed with status {response.status_code}",
                    component="n8n_instance",
                    recommendation="Check n8n service status and configuration"
                ))
                return False, None, issues
                
        except requests.exceptions.ConnectionError:
            issues.append(Issue(
                severity=Priority.CRITICAL,
                description="Cannot connect to n8n instance",
                component="n8n_instance",
                recommendation="Start n8n service or check connection URL"
            ))
            return False, None, issues
        except requests.exceptions.Timeout:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="n8n health check timed out",
                component="n8n_instance",
                recommendation="Check n8n service performance and resources"
            ))
            return False, None, issues
        except Exception as e:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"n8n health check failed: {str(e)}",
                component="n8n_instance",
                recommendation="Verify n8n service configuration"
            ))
            return False, None, issues
    
    def validate_workflow(self, workflow: WorkflowInfo) -> List[Issue]:
        """
        Validate a workflow against Phoenix Hydra requirements.
        
        Args:
            workflow: WorkflowInfo object to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check if workflow has nodes
        if not workflow.nodes:
            issues.append(Issue(
                severity=Priority.HIGH,
                description=f"Workflow '{workflow.name}' has no nodes",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add workflow nodes to implement functionality"
            ))
            return issues
        
        # Check for Phoenix Hydra specific patterns
        self._validate_phoenix_integration(workflow, issues)
        self._validate_api_configurations(workflow, issues)
        self._validate_monetization_tracking(workflow, issues)
        self._validate_workflow_structure(workflow, issues)
        
        # Evaluate documentation
        documentation_issues = self.evaluate_workflow_documentation(workflow)
        issues.extend(documentation_issues)
        
        # Assess functionality
        functionality_score, functionality_issues = self.assess_workflow_functionality(workflow)
        issues.extend(functionality_issues)
        
        return issues
    
    def _validate_phoenix_integration(self, workflow: WorkflowInfo, issues: List[Issue]):
        """Validate Phoenix Hydra specific integration patterns"""
        
        # Check for Phoenix API endpoints
        has_phoenix_endpoint = False
        for node in workflow.nodes:
            if node.type == NodeType.HTTP_REQUEST.value:
                url = node.parameters.get('url', '')
                if any(endpoint in url for endpoint in self.validation_rules['api_endpoints']):
                    has_phoenix_endpoint = True
                    break
        
        if not has_phoenix_endpoint and 'phoenix' in workflow.name.lower():
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Phoenix workflow '{workflow.name}' doesn't use Phoenix API endpoints",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add HTTP Request nodes pointing to Phoenix Hydra services"
            ))
    
    def _validate_api_configurations(self, workflow: WorkflowInfo, issues: List[Issue]):
        """Validate API configuration in HTTP request nodes"""
        
        for node in workflow.nodes:
            if node.type == NodeType.HTTP_REQUEST.value:
                # Check for API key headers
                headers = node.parameters.get('headerParameters', {}).get('parameters', [])
                has_auth_header = any(
                    header.get('name', '').lower() in ['x-api-key', 'authorization']
                    for header in headers
                )
                
                if not has_auth_header:
                    issues.append(Issue(
                        severity=Priority.MEDIUM,
                        description=f"HTTP node '{node.name}' lacks authentication headers",
                        component="n8n_workflow",
                        file_path=workflow.file_path,
                        recommendation="Add x-api-key or authorization header"
                    ))
                
                # Check for proper error handling
                if not node.parameters.get('options', {}).get('response', {}).get('response', {}).get('neverError'):
                    issues.append(Issue(
                        severity=Priority.LOW,
                        description=f"HTTP node '{node.name}' may not handle errors properly",
                        component="n8n_workflow",
                        file_path=workflow.file_path,
                        recommendation="Configure error handling options"
                    ))
    
    def _validate_monetization_tracking(self, workflow: WorkflowInfo, issues: List[Issue]):
        """Validate monetization tracking configurations"""
        
        if 'monetization' in workflow.name.lower():
            # Check for required monetization sources
            found_sources = []
            for node in workflow.nodes:
                if node.type == NodeType.HTTP_REQUEST.value:
                    body = node.parameters.get('jsonBody', '')
                    for source in self.validation_rules['monetization_sources']:
                        if source in body:
                            found_sources.append(source)
            
            if len(found_sources) < 2:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Monetization workflow '{workflow.name}' tracks few revenue sources",
                    component="n8n_workflow",
                    file_path=workflow.file_path,
                    recommendation="Add tracking for more monetization sources"
                ))
    
    def _validate_workflow_structure(self, workflow: WorkflowInfo, issues: List[Issue]):
        """Validate overall workflow structure"""
        
        # Check for disconnected nodes
        connected_nodes = set()
        for connection in workflow.connections:
            connected_nodes.add(connection.source_node)
            connected_nodes.add(connection.target_node)
        
        disconnected_nodes = []
        for node in workflow.nodes:
            if node.name not in connected_nodes and len(workflow.nodes) > 1:
                disconnected_nodes.append(node.name)
        
        if disconnected_nodes:
            issues.append(Issue(
                severity=Priority.LOW,
                description=f"Workflow '{workflow.name}' has disconnected nodes: {', '.join(disconnected_nodes)}",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Connect all nodes or remove unused ones"
            ))
        
        # Check for circular dependencies
        if self._has_circular_dependencies(workflow):
            issues.append(Issue(
                severity=Priority.HIGH,
                description=f"Workflow '{workflow.name}' has circular dependencies",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Remove circular connections between nodes"
            ))
    
    def evaluate_workflow_documentation(self, workflow: WorkflowInfo) -> List[Issue]:
        """
        Evaluate workflow documentation completeness and quality.
        
        Args:
            workflow: WorkflowInfo object to evaluate
            
        Returns:
            List of documentation-related issues
        """
        issues = []
        
        # Check for workflow description
        if not workflow.name or len(workflow.name.strip()) < 5:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Workflow has insufficient name/description",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Provide descriptive workflow name"
            ))
        
        # Check for node documentation
        undocumented_nodes = []
        for node in workflow.nodes:
            # Check if node has meaningful name
            if not node.name or node.name.strip() == node.type or len(node.name.strip()) < 3:
                undocumented_nodes.append(node.name or node.id)
            
            # Check for node notes/documentation in parameters
            if 'notes' not in node.parameters and 'description' not in node.parameters:
                # For critical nodes, documentation is more important
                if node.type in [NodeType.HTTP_REQUEST.value, NodeType.CODE.value, NodeType.WEBHOOK.value]:
                    undocumented_nodes.append(node.name or node.id)
        
        if undocumented_nodes:
            issues.append(Issue(
                severity=Priority.LOW,
                description=f"Workflow '{workflow.name}' has undocumented nodes: {', '.join(undocumented_nodes[:5])}",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add meaningful names and notes to workflow nodes"
            ))
        
        # Check for workflow metadata
        workflow_file_path = Path(workflow.file_path)
        if workflow_file_path.exists():
            try:
                with open(workflow_file_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                
                # Check for workflow-level documentation
                if 'meta' not in workflow_data or not workflow_data.get('meta', {}).get('description'):
                    issues.append(Issue(
                        severity=Priority.LOW,
                        description=f"Workflow '{workflow.name}' lacks metadata description",
                        component="n8n_workflow",
                        file_path=workflow.file_path,
                        recommendation="Add workflow description in metadata"
                    ))
                
                # Check for tags
                if 'tags' not in workflow_data or not workflow_data.get('tags'):
                    issues.append(Issue(
                        severity=Priority.LOW,
                        description=f"Workflow '{workflow.name}' has no tags for categorization",
                        component="n8n_workflow",
                        file_path=workflow.file_path,
                        recommendation="Add relevant tags for workflow categorization"
                    ))
                    
            except Exception as e:
                issues.append(Issue(
                    severity=Priority.MEDIUM,
                    description=f"Cannot read workflow file for documentation check: {str(e)}",
                    component="n8n_workflow",
                    file_path=workflow.file_path,
                    recommendation="Ensure workflow file is valid JSON"
                ))
        
        return issues
    
    def assess_workflow_functionality(self, workflow: WorkflowInfo) -> Tuple[float, List[Issue]]:
        """
        Assess the functionality completeness of a workflow.
        
        Args:
            workflow: WorkflowInfo object to assess
            
        Returns:
            Tuple of (functionality_score, list_of_issues)
        """
        issues = []
        functionality_score = 0.0
        
        if not workflow.nodes:
            issues.append(Issue(
                severity=Priority.CRITICAL,
                description=f"Workflow '{workflow.name}' has no functional nodes",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add workflow nodes to implement functionality"
            ))
            return 0.0, issues
        
        # Assess based on workflow type and expected functionality
        if 'nca' in workflow.name.lower() or 'toolkit' in workflow.name.lower():
            functionality_score, nca_issues = self._assess_nca_workflow_functionality(workflow)
            issues.extend(nca_issues)
        elif 'monetization' in workflow.name.lower() or 'revenue' in workflow.name.lower():
            functionality_score, monetization_issues = self._assess_monetization_workflow_functionality(workflow)
            issues.extend(monetization_issues)
        elif 'grant' in workflow.name.lower() or 'application' in workflow.name.lower():
            functionality_score, grant_issues = self._assess_grant_workflow_functionality(workflow)
            issues.extend(grant_issues)
        else:
            # Generic workflow assessment
            functionality_score, generic_issues = self._assess_generic_workflow_functionality(workflow)
            issues.extend(generic_issues)
        
        return functionality_score, issues
    
    def _assess_nca_workflow_functionality(self, workflow: WorkflowInfo) -> Tuple[float, List[Issue]]:
        """Assess NCA Toolkit workflow functionality"""
        issues = []
        score = 0.0
        
        # Check for required components
        has_api_call = any(node.type == NodeType.HTTP_REQUEST.value for node in workflow.nodes)
        has_variables = any(node.type == NodeType.SET.value for node in workflow.nodes)
        has_error_handling = any(node.type == NodeType.IF.value for node in workflow.nodes)
        
        if has_api_call:
            score += 0.4
        else:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="NCA workflow missing HTTP request nodes",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add HTTP Request nodes to call NCA Toolkit APIs"
            ))
        
        if has_variables:
            score += 0.3
        else:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description="NCA workflow missing variable configuration",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add Set nodes for API configuration variables"
            ))
        
        if has_error_handling:
            score += 0.3
        else:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description="NCA workflow lacks error handling",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add IF nodes for error handling and retry logic"
            ))
        
        return score, issues
    
    def _assess_monetization_workflow_functionality(self, workflow: WorkflowInfo) -> Tuple[float, List[Issue]]:
        """Assess monetization workflow functionality"""
        issues = []
        score = 0.0
        
        # Check for revenue tracking components
        has_affiliate_tracking = False
        has_revenue_api = False
        has_data_aggregation = False
        
        for node in workflow.nodes:
            if node.type == NodeType.HTTP_REQUEST.value:
                url = node.parameters.get('url', '').lower()
                if 'affiliate' in url or 'referral' in url:
                    has_affiliate_tracking = True
                elif 'revenue' in url or 'tracking' in url:
                    has_revenue_api = True
            elif node.type == NodeType.SET.value:
                # Check for data aggregation logic
                assignments = node.parameters.get('assignments', {}).get('assignments', [])
                if any('revenue' in str(assignment).lower() for assignment in assignments):
                    has_data_aggregation = True
        
        if has_affiliate_tracking:
            score += 0.4
        else:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="Monetization workflow missing affiliate tracking",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add affiliate program tracking nodes"
            ))
        
        if has_revenue_api:
            score += 0.4
        else:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="Monetization workflow missing revenue API calls",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add revenue tracking API integration"
            ))
        
        if has_data_aggregation:
            score += 0.2
        else:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description="Monetization workflow lacks data aggregation",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add data aggregation and calculation nodes"
            ))
        
        return score, issues
    
    def _assess_grant_workflow_functionality(self, workflow: WorkflowInfo) -> Tuple[float, List[Issue]]:
        """Assess grant application workflow functionality"""
        issues = []
        score = 0.0
        
        # Check for grant-specific components
        has_document_generation = any(node.type == NodeType.CODE.value for node in workflow.nodes)
        has_data_collection = any(node.type == NodeType.SET.value for node in workflow.nodes)
        has_submission_tracking = any(node.type == NodeType.HTTP_REQUEST.value for node in workflow.nodes)
        
        if has_document_generation:
            score += 0.4
        else:
            issues.append(Issue(
                severity=Priority.HIGH,
                description="Grant workflow missing document generation",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add Code nodes for grant document generation"
            ))
        
        if has_data_collection:
            score += 0.3
        else:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description="Grant workflow missing data collection",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add Set nodes for grant data collection"
            ))
        
        if has_submission_tracking:
            score += 0.3
        else:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description="Grant workflow missing submission tracking",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add HTTP Request nodes for submission tracking"
            ))
        
        return score, issues
    
    def _assess_generic_workflow_functionality(self, workflow: WorkflowInfo) -> Tuple[float, List[Issue]]:
        """Assess generic workflow functionality"""
        issues = []
        score = 0.0
        
        # Basic functionality checks
        node_types = [node.type for node in workflow.nodes]
        unique_types = set(node_types)
        
        # Score based on node diversity and connections
        if len(unique_types) >= 3:
            score += 0.4
        elif len(unique_types) >= 2:
            score += 0.2
        
        if len(workflow.connections) >= len(workflow.nodes) - 1:
            score += 0.3
        elif len(workflow.connections) > 0:
            score += 0.1
        
        # Check for basic workflow patterns
        has_input = any(node.type in [NodeType.WEBHOOK.value, NodeType.CRON.value] for node in workflow.nodes)
        has_processing = any(node.type in [NodeType.CODE.value, NodeType.SET.value, NodeType.HTTP_REQUEST.value] for node in workflow.nodes)
        has_logic = any(node.type in [NodeType.IF.value, NodeType.SWITCH.value] for node in workflow.nodes)
        
        if has_input:
            score += 0.1
        if has_processing:
            score += 0.1
        if has_logic:
            score += 0.1
        
        if score < 0.3:
            issues.append(Issue(
                severity=Priority.MEDIUM,
                description=f"Workflow '{workflow.name}' has limited functionality",
                component="n8n_workflow",
                file_path=workflow.file_path,
                recommendation="Add more diverse node types and connections"
            ))
        
        return min(score, 1.0), issues
    
    def _has_circular_dependencies(self, workflow: WorkflowInfo) -> bool:
        """Check if workflow has circular dependencies"""
        
        # Build adjacency list
        graph = {}
        for node in workflow.nodes:
            graph[node.name] = []
        
        for connection in workflow.connections:
            if connection.source_node in graph:
                graph[connection.source_node].append(connection.target_node)
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def calculate_workflow_health_score(self, workflow: WorkflowInfo, issues: List[Issue]) -> float:
        """
        Calculate health score for a workflow.
        
        Args:
            workflow: WorkflowInfo object
            issues: List of issues found
            
        Returns:
            Health score between 0.0 and 1.0
        """
        if not workflow.nodes:
            return 0.0
        
        # Get functionality score
        functionality_score, _ = self.assess_workflow_functionality(workflow)
        
        # Base score combines structure and functionality
        structure_score = 0.4 if len(workflow.nodes) > 0 and len(workflow.connections) > 0 else 0.2
        base_score = (structure_score + functionality_score * 0.6)
        
        # Deduct points for issues
        issue_penalty = 0.0
        for issue in issues:
            if issue.severity == Priority.CRITICAL:
                issue_penalty += 0.4
            elif issue.severity == Priority.HIGH:
                issue_penalty += 0.3
            elif issue.severity == Priority.MEDIUM:
                issue_penalty += 0.2
            elif issue.severity == Priority.LOW:
                issue_penalty += 0.1
        
        return max(0.0, base_score - issue_penalty)
    
    def generate_evaluation_result(self) -> EvaluationResult:
        """
        Generate comprehensive evaluation result for n8n infrastructure.
        
        Returns:
            EvaluationResult with complete analysis
        """
        # Create component
        component = Component(
            name="n8n_workflows",
            category="automation",
            path=str(self.workflows_dir),
            status=ComponentStatus.UNKNOWN
        )
        
        all_issues = []
        criteria_met = []
        criteria_missing = []
        
        # Analyze workflow files
        workflows = self.analyze_workflow_files()
        if workflows:
            criteria_met.append("workflow_files_present")
            
            # Validate each workflow
            total_health_score = 0.0
            for workflow in workflows:
                workflow_issues = self.validate_workflow(workflow)
                all_issues.extend(workflow_issues)
                
                health_score = self.calculate_workflow_health_score(workflow, workflow_issues)
                total_health_score += health_score
                
                if health_score >= 0.7:
                    criteria_met.append(f"workflow_healthy_{workflow.name}")
                else:
                    criteria_missing.append(f"workflow_healthy_{workflow.name}")
            
            # Check for expected workflows
            workflow_names = [w.name.lower() for w in workflows]
            for expected_name in self.expected_workflows.keys():
                if any(expected_name in name for name in workflow_names):
                    criteria_met.append(f"expected_workflow_{expected_name}")
                else:
                    criteria_missing.append(f"expected_workflow_{expected_name}")
                    all_issues.append(Issue(
                        severity=Priority.MEDIUM,
                        description=f"Expected workflow '{expected_name}' not found",
                        component="n8n_workflows",
                        recommendation=f"Create {self.expected_workflows[expected_name]['description']}"
                    ))
        else:
            criteria_missing.append("workflow_files_present")
            all_issues.append(Issue(
                severity=Priority.HIGH,
                description="No n8n workflow files found",
                component="n8n_workflows",
                recommendation="Create n8n workflow configuration files"
            ))
        
        # Check n8n health
        n8n_healthy, n8n_version, n8n_issues = self.check_n8n_health()
        all_issues.extend(n8n_issues)
        if n8n_healthy:
            criteria_met.append("n8n_instance_healthy")
        else:
            criteria_missing.append("n8n_instance_healthy")
        
        # Calculate completion percentage
        total_criteria = len(criteria_met) + len(criteria_missing)
        completion_percentage = len(criteria_met) / total_criteria if total_criteria > 0 else 0.0
        
        # Calculate quality score based on issues
        critical_high_issues = len([i for i in all_issues if i.severity in [Priority.CRITICAL, Priority.HIGH]])
        quality_score = max(0.0, 1.0 - (critical_high_issues * 0.2))
        
        return EvaluationResult(
            component=component,
            criteria_met=criteria_met,
            criteria_missing=criteria_missing,
            completion_percentage=completion_percentage,
            quality_score=quality_score,
            issues=all_issues
        )
    
    def generate_analysis_report(self) -> N8nAnalysis:
        """
        Generate comprehensive n8n analysis report.
        
        Returns:
            N8nAnalysis object with complete analysis
        """
        workflows = self.analyze_workflow_files()
        n8n_healthy, n8n_version, n8n_issues = self.check_n8n_health()
        
        all_issues = list(n8n_issues)
        total_health_score = 0.0
        active_workflows = 0
        
        for workflow in workflows:
            workflow_issues = self.validate_workflow(workflow)
            all_issues.extend(workflow_issues)
            
            health_score = self.calculate_workflow_health_score(workflow, workflow_issues)
            total_health_score += health_score
            
            if health_score >= 0.7:
                active_workflows += 1
        
        overall_health_score = total_health_score / len(workflows) if workflows else 0.0
        
        return N8nAnalysis(
            workflows=workflows,
            n8n_health=n8n_healthy,
            n8n_version=n8n_version,
            total_workflows=len(workflows),
            active_workflows=active_workflows,
            issues=all_issues,
            health_score=overall_health_score
        )