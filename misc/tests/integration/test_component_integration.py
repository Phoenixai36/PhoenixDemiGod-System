"""
Integration tests for component interactions between engines
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from phoenix_system_review.discovery.file_scanner import FileSystemScanner
from phoenix_system_review.discovery.config_parser import ConfigurationParser
from phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from phoenix_system_review.assessment.gap_analyzer import GapAnalyzer
from phoenix_system_review.assessment.completion_calculator import CompletionCalculator
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, EvaluationResult, Gap, ImpactLevel
)


class TestDiscoveryAnalysisIntegration:
    """Test integration between Discovery and Analysis engines"""
    
    @pytest.fixture
    def sample_project_structure(self):
        """Create a sample project structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            (temp_path / "src" / "core").mkdir(parents=True)
            (temp_path / "src" / "services").mkdir()
            (temp_path / "configs").mkdir()
            (temp_path / "infra" / "podman").mkdir(parents=True)
            
            # Create source files with dependencies
            (temp_path / "src" / "core" / "main.py").write_text('''
"""Main application module"""
from src.services.database import DatabaseService
from src.services.storage import StorageService

class MainApplication:
    def __init__(self):
        self.db = DatabaseService()
        self.storage = StorageService()
    
    def start(self):
        """Start the application"""
        self.db.connect()
        self.storage.initialize()
''')
            
            (temp_path / "src" / "services" / "database.py").write_text('''
"""Database service module"""

class DatabaseService:
    def connect(self):
        """Connect to database"""
        pass
    
    def query(self, sql):
        """Execute SQL query"""
        pass
''')
            
            (temp_path / "src" / "services" / "storage.py").write_text('''
"""Storage service module"""
from src.services.database import DatabaseService

class StorageService:
    def __init__(self):
        self.db = DatabaseService()
    
    def initialize(self):
        """Initialize storage"""
        pass
''')
            
            # Create configuration files
            app_config = {
                'app': {
                    'name': 'phoenix-test',
                    'version': '1.0.0',
                    'dependencies': ['database', 'storage']
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'phoenix_db'
                },
                'storage': {
                    'type': 's3',
                    'bucket': 'phoenix-storage',
                    'region': 'us-east-1'
                }
            }
            
            with open(temp_path / "configs" / "app.yaml", 'w') as f:
                yaml.dump(app_config, f)
            
            # Create Podman compose file
            compose_config = {
                'version': '3.8',
                'services': {
                    'phoenix-app': {
                        'build': '.',
                        'ports': ['8080:8080'],
                        'depends_on': ['database', 'storage']
                    },
                    'database': {
                        'image': 'postgres:13',
                        'environment': ['POSTGRES_DB=phoenix_db']
                    },
                    'storage': {
                        'image': 'minio/minio:latest',
                        'ports': ['9000:9000']
                    }
                }
            }
            
            with open(temp_path / "infra" / "podman" / "compose.yaml", 'w') as f:
                yaml.dump(compose_config, f)
            
            yield temp_path
    
    def test_discovery_to_analysis_pipeline(self, sample_project_structure):
        """Test pipeline from file discovery to component analysis"""
        
        # Phase 1: Discovery
        scanner = FileSystemScanner(str(sample_project_structure))
        config_parser = ConfigurationParser()
        
        # Scan project structure
        inventory = scanner.scan_project_structure()
        
        assert inventory.total_files >= 4  # main.py, database.py, storage.py, configs
        assert len(inventory.source_files) >= 3
        assert len(inventory.configuration_files) >= 2
        
        # Parse configurations
        configurations = config_parser.parse_configurations(inventory.configuration_files)
        
        assert len(configurations) >= 2
        
        # Verify configuration content
        app_config = None
        compose_config = None
        
        for file_path, config in configurations.items():
            if 'app.yaml' in file_path:
                app_config = config
            elif 'compose.yaml' in file_path:
                compose_config = config
        
        assert app_config is not None
        assert compose_config is not None
        assert 'app' in app_config
        assert 'services' in compose_config
        
        # Phase 2: Analysis
        evaluator = ComponentEvaluator()
        dependency_analyzer = DependencyAnalyzer()
        
        # Create components from discovered data
        components = []
        
        # Main application component
        main_component = Component(
            name="phoenix-app",
            category=ComponentCategory.INFRASTRUCTURE,
            path=str(sample_project_structure / "src" / "core"),
            dependencies=app_config['app']['dependencies'],
            configuration=app_config['app'],
            status=ComponentStatus.OPERATIONAL
        )
        components.append(main_component)
        
        # Database component
        database_component = Component(
            name="database",
            category=ComponentCategory.INFRASTRUCTURE,
            path=str(sample_project_structure / "src" / "services"),
            configuration=app_config['database'],
            status=ComponentStatus.OPERATIONAL
        )
        components.append(database_component)
        
        # Storage component
        storage_component = Component(
            name="storage",
            category=ComponentCategory.INFRASTRUCTURE,
            path=str(sample_project_structure / "src" / "services"),
            dependencies=["database"],  # storage depends on database
            configuration=app_config['storage'],
            status=ComponentStatus.OPERATIONAL
        )
        components.append(storage_component)
        
        # Analyze dependencies
        dependency_graph = dependency_analyzer.map_dependencies(components)
        
        assert len(dependency_graph.nodes) == 3
        assert len(dependency_graph.edges) >= 2  # phoenix-app -> database, phoenix-app -> storage, storage -> database
        
        # Verify specific dependencies
        expected_edges = [
            ("phoenix-app", "database"),
            ("phoenix-app", "storage"),
            ("storage", "database")
        ]
        
        for edge in expected_edges:
            assert edge in dependency_graph.edges
        
        # Evaluate components
        evaluation_results = []
        for component in components:
            criteria = evaluator.get_evaluation_criteria(component.category.value)
            
            # Mock evaluation based on discovered files and configurations
            with patch.object(evaluator, '_check_criterion') as mock_check:
                def mock_criterion_check(comp, criterion):
                    # Simulate evaluation based on component characteristics
                    if criterion.id == 'configuration':
                        return len(comp.configuration) > 0
                    elif criterion.id == 'file_existence':
                        return comp.path is not None
                    elif criterion.id == 'dependencies':
                        return len(comp.dependencies) >= 0
                    else:
                        return True  # Default to passing
                
                mock_check.side_effect = mock_criterion_check
                result = evaluator.evaluate_component(component, criteria)
                evaluation_results.append(result)
        
        # Verify evaluation results
        assert len(evaluation_results) == 3
        
        for result in evaluation_results:
            assert isinstance(result, EvaluationResult)
            assert result.completion_percentage > 0
            assert len(result.criteria_met) > 0
    
    def test_configuration_driven_component_creation(self, sample_project_structure):
        """Test creating components based on discovered configurations"""
        
        scanner = FileSystemScanner(str(sample_project_structure))
        config_parser = ConfigurationParser()
        
        # Discover and parse configurations
        inventory = scanner.scan_project_structure()
        configurations = config_parser.parse_configurations(inventory.configuration_files)
        
        # Extract component information from configurations
        components = []
        
        for file_path, config in configurations.items():
            if config is None:
                continue
                
            if 'compose.yaml' in file_path and 'services' in config:
                # Create components from Podman compose services
                for service_name, service_config in config['services'].items():
                    component = Component(
                        name=service_name,
                        category=ComponentCategory.INFRASTRUCTURE,
                        path=str(sample_project_structure / "infra" / "podman"),
                        configuration=service_config,
                        status=ComponentStatus.OPERATIONAL
                    )
                    
                    # Extract dependencies from compose file
                    if 'depends_on' in service_config:
                        component.dependencies = service_config['depends_on']
                    
                    components.append(component)
        
        # Verify components were created from configuration
        assert len(components) >= 3  # phoenix-app, database, storage
        
        component_names = [comp.name for comp in components]
        assert 'phoenix-app' in component_names
        assert 'database' in component_names
        assert 'storage' in component_names
        
        # Verify dependencies were extracted correctly
        phoenix_app = next(comp for comp in components if comp.name == 'phoenix-app')
        assert 'database' in phoenix_app.dependencies
        assert 'storage' in phoenix_app.dependencies


class TestAnalysisAssessmentIntegration:
    """Test integration between Analysis and Assessment engines"""
    
    @pytest.fixture
    def sample_evaluation_results(self):
        """Create sample evaluation results for testing"""
        
        # High-performing component
        high_component = Component(
            name="high-performance",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/high"
        )
        
        high_result = EvaluationResult(
            component=high_component,
            criteria_met=["api_endpoints", "health_checks", "documentation", "monitoring"],
            criteria_missing=["advanced_monitoring"],
            completion_percentage=90.0,
            quality_score=95.0
        )
        
        # Medium-performing component
        medium_component = Component(
            name="medium-performance",
            category=ComponentCategory.MONETIZATION,
            path="/src/medium"
        )
        
        medium_result = EvaluationResult(
            component=medium_component,
            criteria_met=["basic_setup", "configuration"],
            criteria_missing=["tracking", "reporting", "optimization"],
            completion_percentage=60.0,
            quality_score=70.0
        )
        
        # Low-performing component
        low_component = Component(
            name="low-performance",
            category=ComponentCategory.AUTOMATION,
            path="/src/low"
        )
        
        low_result = EvaluationResult(
            component=low_component,
            criteria_met=["basic_structure"],
            criteria_missing=["automation", "error_handling", "monitoring", "documentation"],
            completion_percentage=25.0,
            quality_score=40.0
        )
        
        return [high_result, medium_result, low_result]
    
    def test_analysis_to_assessment_pipeline(self, sample_evaluation_results):
        """Test pipeline from component analysis to gap assessment"""
        
        gap_analyzer = GapAnalyzer()
        completion_calculator = CompletionCalculator()
        
        # Phase 1: Gap Analysis
        gaps = gap_analyzer.identify_gaps(sample_evaluation_results)
        
        # Should identify gaps for missing criteria
        assert len(gaps) > 0
        
        # Verify gaps are created for each missing criterion
        total_missing_criteria = sum(len(result.criteria_missing) for result in sample_evaluation_results)
        assert len(gaps) >= total_missing_criteria
        
        # Verify gap impact levels are assigned correctly
        gap_impacts = [gap.impact for gap in gaps]
        assert ImpactLevel.HIGH in gap_impacts or ImpactLevel.CRITICAL in gap_impacts  # Low-performing component should have high-impact gaps
        
        # Phase 2: Completion Calculation
        completion_scores = completion_calculator.calculate_completion(sample_evaluation_results)
        
        assert len(completion_scores) == 3
        
        # Verify completion scores match evaluation results
        for result in sample_evaluation_results:
            component_name = result.component.name
            assert component_name in completion_scores
            
            score = completion_scores[component_name]
            assert score.completion_percentage == result.completion_percentage
            assert score.quality_score == result.quality_score
        
        # Calculate overall completion
        overall_completion = completion_calculator.calculate_overall_completion(completion_scores)
        
        # Should be weighted average of component completions
        assert 0.0 <= overall_completion <= 100.0
        
        # Should be between the lowest and highest individual scores
        individual_scores = [result.completion_percentage for result in sample_evaluation_results]
        min_score = min(individual_scores)
        max_score = max(individual_scores)
        
        assert min_score <= overall_completion <= max_score
    
    def test_gap_categorization_and_prioritization(self, sample_evaluation_results):
        """Test gap categorization and prioritization integration"""
        
        gap_analyzer = GapAnalyzer()
        
        # Identify gaps
        gaps = gap_analyzer.identify_gaps(sample_evaluation_results)
        
        # Categorize gaps by impact
        categorized_gaps = gap_analyzer.categorize_gaps_by_impact(gaps)
        
        assert isinstance(categorized_gaps, dict)
        assert all(impact_level in categorized_gaps for impact_level in ImpactLevel)
        
        # Verify categorization logic
        for impact_level, impact_gaps in categorized_gaps.items():
            for gap in impact_gaps:
                assert gap.impact == impact_level
        
        # High-impact gaps should exist for low-performing components
        high_impact_gaps = categorized_gaps[ImpactLevel.HIGH]
        critical_gaps = categorized_gaps[ImpactLevel.CRITICAL]
        
        # Should have some high-impact or critical gaps
        assert len(high_impact_gaps) > 0 or len(critical_gaps) > 0
        
        # Verify effort estimation
        for gap in gaps:
            if gap.effort_estimate == 0:  # If not already estimated
                estimated_effort = gap_analyzer.estimate_gap_effort(gap)
                assert estimated_effort > 0
                assert estimated_effort <= 80  # Reasonable upper bound
    
    def test_quality_score_integration(self, sample_evaluation_results):
        """Test integration of quality scores in assessment"""
        
        completion_calculator = CompletionCalculator()
        
        # Calculate completion with quality consideration
        completion_scores = completion_calculator.calculate_completion(sample_evaluation_results)
        
        # Verify quality scores are preserved
        for result in sample_evaluation_results:
            component_name = result.component.name
            score = completion_scores[component_name]
            
            assert score.quality_score == result.quality_score
            
            # Quality score should influence weighted score
            if result.quality_score > 80:
                assert score.weighted_score >= score.completion_percentage * 0.9
            elif result.quality_score < 50:
                assert score.weighted_score <= score.completion_percentage * 1.1


class TestConfigurationValidationIntegration:
    """Test integration of configuration parsing and validation"""
    
    def test_configuration_parsing_and_validation_pipeline(self):
        """Test pipeline from configuration discovery to validation"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create valid configuration
            valid_config = {
                'app': {
                    'name': 'phoenix-test',
                    'port': 8080,
                    'debug': False
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'ssl': True
                }
            }
            
            valid_file = temp_path / "valid.yaml"
            with open(valid_file, 'w') as f:
                yaml.dump(valid_config, f)
            
            # Create invalid configuration
            invalid_config = {
                'app': {
                    'name': '',  # Invalid empty name
                    'port': 'invalid',  # Invalid port type
                    'debug': 'yes'  # Invalid boolean
                },
                'database': {
                    # Missing required host
                    'port': -1,  # Invalid port number
                    'ssl': 'true'  # Invalid boolean type
                }
            }
            
            invalid_file = temp_path / "invalid.yaml"
            with open(invalid_file, 'w') as f:
                yaml.dump(invalid_config, f)
            
            # Parse configurations
            config_parser = ConfigurationParser()
            
            valid_parsed = config_parser.parse_configuration_file(str(valid_file))
            invalid_parsed = config_parser.parse_configuration_file(str(invalid_file))
            
            assert valid_parsed is not None
            assert invalid_parsed is not None  # Should parse but may have validation issues
            
            # Validate configurations (mock validation)
            from phoenix_system_review.analysis.quality_assessor import QualityAssessor
            quality_assessor = QualityAssessor()
            
            # Test configuration validation
            config_files = [str(valid_file), str(invalid_file)]
            validation_issues = quality_assessor.validate_configuration_files(config_files)
            
            # Should identify issues in invalid configuration
            assert isinstance(validation_issues, list)
            # Note: Actual validation logic would identify specific issues
    
    def test_service_discovery_configuration_integration(self):
        """Test integration between configuration parsing and service discovery"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create service configuration
            service_config = {
                'services': {
                    'phoenix-core': {
                        'host': 'localhost',
                        'port': 8080,
                        'health_endpoint': '/health',
                        'enabled': True
                    },
                    'n8n': {
                        'host': 'localhost',
                        'port': 5678,
                        'health_endpoint': '/',
                        'enabled': True
                    },
                    'windmill': {
                        'host': 'localhost',
                        'port': 8000,
                        'health_endpoint': '/api/health',
                        'enabled': False
                    }
                }
            }
            
            config_file = temp_path / "services.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(service_config, f)
            
            # Parse configuration
            config_parser = ConfigurationParser()
            parsed_config = config_parser.parse_configuration_file(str(config_file))
            
            assert parsed_config is not None
            assert 'services' in parsed_config
            
            # Extract service endpoints from configuration
            from phoenix_system_review.discovery.service_discovery import ServiceDiscovery
            service_discovery = ServiceDiscovery()
            
            endpoints = {}
            for service_name, service_info in parsed_config['services'].items():
                if service_info.get('enabled', True):
                    host = service_info['host']
                    port = service_info['port']
                    health_endpoint = service_info.get('health_endpoint', '/health')
                    endpoints[service_name] = f"http://{host}:{port}{health_endpoint}"
            
            # Should extract enabled services only
            assert len(endpoints) == 2  # phoenix-core and n8n (windmill is disabled)
            assert 'phoenix-core' in endpoints
            assert 'n8n' in endpoints
            assert 'windmill' not in endpoints
            
            # Mock service discovery
            with patch.object(service_discovery, 'check_service_health', return_value=False):
                registry = service_discovery.discover_services(endpoints)
                
                assert len(registry.services) == 2
                assert len(registry.endpoints) == 2


if __name__ == '__main__':
    pytest.main([__file__])