"""
Unit tests for Discovery Engine components
"""

import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from phoenix_system_review.discovery.file_scanner import FileSystemScanner
from phoenix_system_review.discovery.config_parser import ConfigurationParser
from phoenix_system_review.discovery.service_discovery import ServiceDiscovery
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, ProjectInventory, ServiceRegistry
)


class TestFileSystemScanner:
    """Test cases for FileSystemScanner"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            (temp_path / "src").mkdir()
            (temp_path / "src" / "core").mkdir()
            (temp_path / "configs").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "tests").mkdir()
            
            # Create files
            (temp_path / "src" / "main.py").write_text("# Main application")
            (temp_path / "src" / "core" / "router.py").write_text("# Router module")
            (temp_path / "configs" / "app.yaml").write_text("app:\n  name: test")
            (temp_path / "configs" / "database.json").write_text('{"host": "localhost"}')
            (temp_path / "docs" / "README.md").write_text("# Documentation")
            (temp_path / "tests" / "test_main.py").write_text("# Tests")
            (temp_path / ".gitignore").write_text("*.pyc\n__pycache__/")
            
            yield temp_path
    
    @pytest.fixture
    def scanner(self, temp_project):
        """Create FileSystemScanner instance"""
        return FileSystemScanner(str(temp_project))
    
    def test_scan_project_structure(self, scanner, temp_project):
        """Test scanning project structure"""
        inventory = scanner.scan_project_structure()
        
        assert isinstance(inventory, ProjectInventory)
        assert inventory.total_files > 0
        assert inventory.total_directories > 0
        assert len(inventory.source_files) >= 2  # main.py, router.py
        assert len(inventory.configuration_files) >= 2  # app.yaml, database.json
        assert len(inventory.documentation_files) >= 1  # README.md
    
    def test_identify_file_types(self, scanner, temp_project):
        """Test file type identification"""
        inventory = scanner.scan_project_structure()
        
        # Check that Python files are identified as source files
        python_files = [f for f in inventory.source_files if f.endswith('.py')]
        assert len(python_files) >= 2
        
        # Check that config files are identified correctly
        config_files = [f for f in inventory.configuration_files if f.endswith(('.yaml', '.json'))]
        assert len(config_files) >= 2
        
        # Check that documentation files are identified
        doc_files = [f for f in inventory.documentation_files if f.endswith('.md')]
        assert len(doc_files) >= 1
    
    def test_exclude_patterns(self, scanner, temp_project):
        """Test that excluded patterns are ignored"""
        # Create files that should be excluded
        (temp_project / "src" / "__pycache__").mkdir()
        (temp_project / "src" / "__pycache__" / "main.cpython-39.pyc").write_text("bytecode")
        (temp_project / "temp.pyc").write_text("bytecode")
        
        inventory = scanner.scan_project_structure()
        
        # Check that excluded files are not in the inventory
        all_files = inventory.source_files + inventory.configuration_files + inventory.documentation_files
        excluded_files = [f for f in all_files if '.pyc' in f or '__pycache__' in f]
        assert len(excluded_files) == 0
    
    def test_empty_directory(self):
        """Test scanning empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FileSystemScanner(temp_dir)
            inventory = scanner.scan_project_structure()
            
            assert isinstance(inventory, ProjectInventory)
            assert inventory.total_files == 0
            assert inventory.total_directories == 1  # The root directory itself
            assert len(inventory.source_files) == 0
            assert len(inventory.configuration_files) == 0
    
    def test_nonexistent_directory(self):
        """Test scanning nonexistent directory"""
        with pytest.raises((FileNotFoundError, OSError)):
            scanner = FileSystemScanner("/nonexistent/path")
            scanner.scan_project_structure()


class TestConfigurationParser:
    """Test cases for ConfigurationParser"""
    
    @pytest.fixture
    def parser(self):
        """Create ConfigurationParser instance"""
        return ConfigurationParser()
    
    @pytest.fixture
    def config_files(self):
        """Create temporary configuration files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # YAML config
            yaml_config = {
                'app': {
                    'name': 'phoenix-hydra',
                    'version': '1.0.0',
                    'debug': True
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432
                }
            }
            yaml_file = temp_path / "config.yaml"
            with open(yaml_file, 'w') as f:
                yaml.dump(yaml_config, f)
            
            # JSON config
            json_config = {
                'services': {
                    'n8n': {'port': 5678, 'enabled': True},
                    'windmill': {'port': 8000, 'enabled': True}
                }
            }
            json_file = temp_path / "services.json"
            with open(json_file, 'w') as f:
                json.dump(json_config, f)
            
            # TOML config
            toml_content = """
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "INFO"
file = "app.log"
"""
            toml_file = temp_path / "config.toml"
            toml_file.write_text(toml_content)
            
            yield [str(yaml_file), str(json_file), str(toml_file)]
    
    def test_parse_yaml_configuration(self, parser, config_files):
        """Test parsing YAML configuration"""
        yaml_file = [f for f in config_files if f.endswith('.yaml')][0]
        config = parser.parse_configuration_file(yaml_file)
        
        assert config is not None
        assert 'app' in config
        assert config['app']['name'] == 'phoenix-hydra'
        assert config['database']['port'] == 5432
    
    def test_parse_json_configuration(self, parser, config_files):
        """Test parsing JSON configuration"""
        json_file = [f for f in config_files if f.endswith('.json')][0]
        config = parser.parse_configuration_file(json_file)
        
        assert config is not None
        assert 'services' in config
        assert config['services']['n8n']['port'] == 5678
        assert config['services']['windmill']['enabled'] is True
    
    def test_parse_toml_configuration(self, parser, config_files):
        """Test parsing TOML configuration"""
        toml_file = [f for f in config_files if f.endswith('.toml')][0]
        config = parser.parse_configuration_file(toml_file)
        
        assert config is not None
        assert 'server' in config
        assert config['server']['host'] == "0.0.0.0"
        assert config['logging']['level'] == "INFO"
    
    def test_parse_multiple_configurations(self, parser, config_files):
        """Test parsing multiple configuration files"""
        configs = parser.parse_configurations(config_files)
        
        assert len(configs) == 3
        assert all(config is not None for config in configs.values())
        
        # Check that all files were parsed
        yaml_file = [f for f in config_files if f.endswith('.yaml')][0]
        json_file = [f for f in config_files if f.endswith('.json')][0]
        toml_file = [f for f in config_files if f.endswith('.toml')][0]
        
        assert yaml_file in configs
        assert json_file in configs
        assert toml_file in configs
    
    def test_invalid_yaml_file(self, parser):
        """Test parsing invalid YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_file = f.name
        
        try:
            config = parser.parse_configuration_file(invalid_file)
            assert config is None  # Should return None for invalid files
        finally:
            os.unlink(invalid_file)
    
    def test_invalid_json_file(self, parser):
        """Test parsing invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')
            invalid_file = f.name
        
        try:
            config = parser.parse_configuration_file(invalid_file)
            assert config is None  # Should return None for invalid files
        finally:
            os.unlink(invalid_file)
    
    def test_nonexistent_file(self, parser):
        """Test parsing nonexistent file"""
        config = parser.parse_configuration_file("/nonexistent/config.yaml")
        assert config is None
    
    def test_unsupported_file_format(self, parser):
        """Test parsing unsupported file format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text content")
            unsupported_file = f.name
        
        try:
            config = parser.parse_configuration_file(unsupported_file)
            assert config is None  # Should return None for unsupported formats
        finally:
            os.unlink(unsupported_file)


class TestServiceDiscovery:
    """Test cases for ServiceDiscovery"""
    
    @pytest.fixture
    def service_discovery(self):
        """Create ServiceDiscovery instance"""
        return ServiceDiscovery()
    
    @patch('requests.get')
    def test_check_service_health_success(self, mock_get, service_discovery):
        """Test successful service health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'healthy'}
        mock_get.return_value = mock_response
        
        is_healthy = service_discovery.check_service_health('http://localhost:8080/health')
        
        assert is_healthy is True
        mock_get.assert_called_once_with('http://localhost:8080/health', timeout=5)
    
    @patch('requests.get')
    def test_check_service_health_failure(self, mock_get, service_discovery):
        """Test failed service health check"""
        mock_get.side_effect = Exception("Connection refused")
        
        is_healthy = service_discovery.check_service_health('http://localhost:8080/health')
        
        assert is_healthy is False
    
    @patch('requests.get')
    def test_check_service_health_bad_status(self, mock_get, service_discovery):
        """Test service health check with bad status code"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        is_healthy = service_discovery.check_service_health('http://localhost:8080/health')
        
        assert is_healthy is False
    
    @patch.object(ServiceDiscovery, 'check_service_health')
    def test_discover_services(self, mock_health_check, service_discovery):
        """Test discovering multiple services"""
        # Mock health check results
        mock_health_check.side_effect = [True, False, True]  # n8n healthy, windmill down, phoenix healthy
        
        service_endpoints = {
            'n8n': 'http://localhost:5678',
            'windmill': 'http://localhost:8000',
            'phoenix-core': 'http://localhost:8080/health'
        }
        
        registry = service_discovery.discover_services(service_endpoints)
        
        assert isinstance(registry, ServiceRegistry)
        assert len(registry.services) == 3
        assert registry.health_checks['n8n'] is True
        assert registry.health_checks['windmill'] is False
        assert registry.health_checks['phoenix-core'] is True
        assert registry.endpoints['n8n'] == 'http://localhost:5678'
    
    def test_discover_services_empty(self, service_discovery):
        """Test discovering services with empty endpoints"""
        registry = service_discovery.discover_services({})
        
        assert isinstance(registry, ServiceRegistry)
        assert len(registry.services) == 0
        assert len(registry.health_checks) == 0
        assert len(registry.endpoints) == 0
    
    @patch('requests.get')
    def test_get_service_metrics(self, mock_get, service_discovery):
        """Test getting service metrics"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'cpu_usage': 45.2,
            'memory_usage': 512,
            'uptime': 3600,
            'requests_per_second': 10.5
        }
        mock_get.return_value = mock_response
        
        metrics = service_discovery.get_service_metrics('http://localhost:8080/metrics')
        
        assert metrics is not None
        assert metrics['cpu_usage'] == 45.2
        assert metrics['memory_usage'] == 512
        assert metrics['uptime'] == 3600
        assert metrics['requests_per_second'] == 10.5
    
    @patch('requests.get')
    def test_get_service_metrics_failure(self, mock_get, service_discovery):
        """Test getting service metrics with failure"""
        mock_get.side_effect = Exception("Connection refused")
        
        metrics = service_discovery.get_service_metrics('http://localhost:8080/metrics')
        
        assert metrics is None
    
    def test_validate_service_configuration(self, service_discovery):
        """Test validating service configuration"""
        valid_config = {
            'name': 'phoenix-core',
            'port': 8080,
            'health_endpoint': '/health',
            'enabled': True
        }
        
        issues = service_discovery.validate_service_configuration(valid_config)
        assert len(issues) == 0
        
        invalid_config = {
            'name': '',  # Empty name
            'port': 'invalid',  # Invalid port
            'enabled': 'yes'  # Invalid boolean
        }
        
        issues = service_discovery.validate_service_configuration(invalid_config)
        assert len(issues) > 0
        assert any('name' in issue for issue in issues)
        assert any('port' in issue for issue in issues)


if __name__ == '__main__':
    pytest.main([__file__])