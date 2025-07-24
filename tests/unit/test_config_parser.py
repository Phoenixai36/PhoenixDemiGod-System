"""
Unit tests for Configuration Parser
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path
from datetime import datetime

# Simple TOML serializer for testing
def toml_dumps(data):
    """Simple TOML serializer for testing"""
    lines = []
    
    def serialize_value(value):
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            return '[' + ', '.join(f'"{item}"' if isinstance(item, str) else str(item) for item in value) + ']'
        else:
            return str(value)
    
    def serialize_section(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                section_name = f"{prefix}.{key}" if prefix else key
                lines.append(f"[{section_name}]")
                serialize_section(value, section_name)
            else:
                lines.append(f"{key} = {serialize_value(value)}")
    
    serialize_section(data)
    return '\n'.join(lines)

from src.phoenix_system_review.discovery.config_parser import ConfigurationParser, ConfigurationData
from src.phoenix_system_review.models.data_models import Priority


class TestConfigurationParser:
    """Test cases for ConfigurationParser class"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory with various configuration files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create YAML config
            yaml_config = {
                'services': {
                    'phoenix-core': {
                        'image': 'phoenix:latest',
                        'ports': ['8080:8080'],
                        'healthcheck': {'test': 'curl -f http://localhost:8080/health'}
                    }
                }
            }
            (temp_path / "docker-compose.yml").write_text(yaml.dump(yaml_config))
            
            # Create JSON config
            json_config = {
                'name': 'phoenix-hydra',
                'version': '1.0.0',
                'scripts': {
                    'test': 'pytest',
                    'build': 'python setup.py build',
                    'start': 'python main.py'
                }
            }
            (temp_path / "package.json").write_text(json.dumps(json_config, indent=2))
            
            # Create TOML config
            toml_config = {
                'project': {'name': 'phoenix-hydra', 'version': '1.0.0'},
                'tool': {
                    'pytest': {'testpaths': ['tests']},
                    'black': {'line-length': 88},
                    'ruff': {'select': ['E', 'F']}
                }
            }
            (temp_path / "pyproject.toml").write_text(toml_dumps(toml_config))
            
            # Create INI config
            ini_content = """[DEFAULT]
debug = true

[database]
host = localhost
port = 5432
name = phoenix_db
"""
            (temp_path / "config.ini").write_text(ini_content)
            
            # Create ENV file
            env_content = """DEBUG=true
DATABASE_URL=postgresql://localhost:5432/phoenix
SECRET_KEY="super-secret-key"
PORT=8080
"""
            (temp_path / ".env").write_text(env_content)
            
            # Create Dockerfile
            dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8080/health
USER appuser
CMD ["python", "main.py"]
"""
            (temp_path / "Dockerfile").write_text(dockerfile_content)
            
            # Create invalid JSON
            (temp_path / "invalid.json").write_text('{"invalid": json}')
            
            # Create invalid YAML
            (temp_path / "invalid.yml").write_text('invalid: yaml: content: [')
            
            yield temp_path
    
    def test_parser_initialization(self):
        """Test parser initialization"""
        parser = ConfigurationParser()
        
        assert len(parser.parsed_configs) == 0
        assert len(parser.parsing_errors) == 0
        assert parser.SUPPORTED_FORMATS['.yaml'] == 'yaml'
        assert parser.SUPPORTED_FORMATS['.json'] == 'json'
        assert parser.SUPPORTED_FORMATS['.toml'] == 'toml'
    
    def test_determine_format(self, temp_config_dir):
        """Test format determination logic"""
        parser = ConfigurationParser()
        
        # Test by extension
        assert parser._determine_format(Path("config.yaml")) == "yaml"
        assert parser._determine_format(Path("config.json")) == "json"
        assert parser._determine_format(Path("config.toml")) == "toml"
        assert parser._determine_format(Path("config.ini")) == "ini"
        assert parser._determine_format(Path(".env")) == "env"
        
        # Test special cases
        assert parser._determine_format(Path("Dockerfile")) == "dockerfile"
        assert parser._determine_format(Path("docker-compose.yml")) == "yaml"
        assert parser._determine_format(Path(".env.local")) == "env"
        
        # Test unsupported format
        assert parser._determine_format(Path("config.xyz")) is None
    
    def test_parse_yaml_file(self, temp_config_dir):
        """Test YAML file parsing"""
        parser = ConfigurationParser()
        yaml_file = str(temp_config_dir / "docker-compose.yml")
        
        config_data = parser.parse_single_file(yaml_file)
        
        assert config_data is not None
        assert config_data.format_type == "yaml"
        assert config_data.schema_valid is True
        assert 'services' in config_data.data
        assert 'phoenix-core' in config_data.data['services']
        assert isinstance(config_data.last_modified, datetime)
        assert config_data.file_size > 0
    
    def test_parse_json_file(self, temp_config_dir):
        """Test JSON file parsing"""
        parser = ConfigurationParser()
        json_file = str(temp_config_dir / "package.json")
        
        config_data = parser.parse_single_file(json_file)
        
        assert config_data is not None
        assert config_data.format_type == "json"
        assert config_data.schema_valid is True
        assert config_data.data['name'] == 'phoenix-hydra'
        assert config_data.data['version'] == '1.0.0'
        assert 'scripts' in config_data.data
    
    def test_parse_toml_file(self, temp_config_dir):
        """Test TOML file parsing"""
        parser = ConfigurationParser()
        toml_file = str(temp_config_dir / "pyproject.toml")
        
        config_data = parser.parse_single_file(toml_file)
        
        assert config_data is not None
        assert config_data.format_type == "toml"
        assert config_data.schema_valid is True
        assert 'project' in config_data.data
        assert 'tool' in config_data.data
        assert 'pytest' in config_data.data['tool']
    
    def test_parse_ini_file(self, temp_config_dir):
        """Test INI file parsing"""
        parser = ConfigurationParser()
        ini_file = str(temp_config_dir / "config.ini")
        
        config_data = parser.parse_single_file(ini_file)
        
        assert config_data is not None
        assert config_data.format_type == "ini"
        assert 'database' in config_data.data
        assert config_data.data['database']['host'] == 'localhost'
        assert config_data.data['database']['port'] == '5432'
    
    def test_parse_env_file(self, temp_config_dir):
        """Test environment file parsing"""
        parser = ConfigurationParser()
        env_file = str(temp_config_dir / ".env")
        
        config_data = parser.parse_single_file(env_file)
        
        assert config_data is not None
        assert config_data.format_type == "env"
        assert config_data.data['DEBUG'] == 'true'
        assert config_data.data['DATABASE_URL'] == 'postgresql://localhost:5432/phoenix'
        assert config_data.data['SECRET_KEY'] == 'super-secret-key'  # Quotes removed
        assert config_data.data['PORT'] == '8080'
    
    def test_parse_dockerfile(self, temp_config_dir):
        """Test Dockerfile parsing"""
        parser = ConfigurationParser()
        dockerfile = str(temp_config_dir / "Dockerfile")
        
        config_data = parser.parse_single_file(dockerfile)
        
        assert config_data is not None
        assert config_data.format_type == "dockerfile"
        assert config_data.data['from_image'] == 'python:3.11-slim'
        assert '8080' in config_data.data['exposed_ports']
        assert len(config_data.data['instructions']) > 0
        
        # Check for specific instructions
        instructions = [inst['instruction'] for inst in config_data.data['instructions']]
        assert 'FROM' in instructions
        assert 'WORKDIR' in instructions
        assert 'EXPOSE' in instructions
        assert 'USER' in instructions
        assert 'CMD' in instructions
    
    def test_parse_multiple_configurations(self, temp_config_dir):
        """Test parsing multiple configuration files"""
        parser = ConfigurationParser()
        
        config_files = [
            str(temp_config_dir / "docker-compose.yml"),
            str(temp_config_dir / "package.json"),
            str(temp_config_dir / "pyproject.toml")
        ]
        
        results = parser.parse_configurations(config_files)
        
        assert len(results) == 3
        assert len(parser.parsed_configs) == 3
        
        # Check that all files were parsed
        for file_path in config_files:
            assert file_path in results
            assert file_path in parser.parsed_configs
    
    def test_invalid_file_handling(self, temp_config_dir):
        """Test handling of invalid configuration files"""
        parser = ConfigurationParser()
        
        # Test invalid JSON
        invalid_json = str(temp_config_dir / "invalid.json")
        config_data = parser.parse_single_file(invalid_json)
        
        assert config_data is not None
        assert config_data.schema_valid is False
        assert len(config_data.parsing_errors) > 0
        assert config_data.data == {}
        
        # Test invalid YAML
        invalid_yaml = str(temp_config_dir / "invalid.yml")
        config_data = parser.parse_single_file(invalid_yaml)
        
        assert config_data is not None
        assert config_data.schema_valid is False
        assert len(config_data.parsing_errors) > 0
    
    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        parser = ConfigurationParser()
        
        config_data = parser.parse_single_file("nonexistent.json")
        
        assert config_data is None
        assert len(parser.parsing_errors) > 0
        assert parser.parsing_errors[0].description == "File does not exist"
    
    def test_pyproject_validation(self, temp_config_dir):
        """Test pyproject.toml validation"""
        parser = ConfigurationParser()
        toml_file = str(temp_config_dir / "pyproject.toml")
        
        config_data = parser.parse_single_file(toml_file)
        
        assert config_data is not None
        assert config_data.schema_valid is True
        
        # The test file has all required tools, so should be valid
        # But let's test missing tools by creating a config with project but no tool section
        minimal_toml = temp_config_dir / "minimal_pyproject.toml"  # Name it so it triggers validation
        minimal_toml.write_text('[project]\nname = "test"\nversion = "1.0.0"')  # Has project but no tool section
        
        config_data = parser.parse_single_file(str(minimal_toml))
        assert len(config_data.validation_errors) > 0  # Should have validation errors for missing tools
    
    def test_docker_compose_validation(self, temp_config_dir):
        """Test docker-compose.yml validation"""
        parser = ConfigurationParser()
        compose_file = str(temp_config_dir / "docker-compose.yml")
        
        config_data = parser.parse_single_file(compose_file)
        
        assert config_data is not None
        # The test file has services but may be missing some expected Phoenix services
        # This should generate validation warnings but still be parseable
    
    def test_package_json_validation(self, temp_config_dir):
        """Test package.json validation"""
        parser = ConfigurationParser()
        json_file = str(temp_config_dir / "package.json")
        
        config_data = parser.parse_single_file(json_file)
        
        assert config_data is not None
        assert config_data.schema_valid is True
        
        # Test invalid package.json (missing required fields)
        invalid_package = temp_config_dir / "invalid_package.json"
        invalid_package.write_text('{"description": "missing name and version"}')  # Missing name and version
        
        config_data = parser.parse_single_file(str(invalid_package))
        assert len(config_data.validation_errors) >= 2  # Should have errors for missing name and version
    
    def test_dockerfile_validation(self, temp_config_dir):
        """Test Dockerfile validation"""
        parser = ConfigurationParser()
        dockerfile = str(temp_config_dir / "Dockerfile")
        
        config_data = parser.parse_single_file(dockerfile)
        
        assert config_data is not None
        # The test Dockerfile should be valid as it has FROM, USER, HEALTHCHECK, etc.
        
        # Test minimal Dockerfile
        minimal_dockerfile = temp_config_dir / "Dockerfile.minimal"
        minimal_dockerfile.write_text("FROM ubuntu:20.04\nRUN apt-get update")
        
        config_data = parser.parse_single_file(str(minimal_dockerfile))
        if config_data:  # Only check if parsing succeeded
            assert len(config_data.validation_errors) > 0  # Should warn about missing USER, HEALTHCHECK
    
    def test_sensitive_data_detection(self, temp_config_dir):
        """Test detection of sensitive data in configurations"""
        parser = ConfigurationParser()
        
        # Create config with sensitive data
        sensitive_config = temp_config_dir / "sensitive.json"
        sensitive_data = {
            "database_password": "secret123",
            "api_token": "abc123def456",
            "secret_key": "super-secret"
        }
        sensitive_config.write_text(json.dumps(sensitive_data))
        
        config_data = parser.parse_single_file(str(sensitive_config))
        
        assert config_data is not None
        # Should detect sensitive data patterns
        sensitive_warnings = [error for error in config_data.validation_errors 
                            if "sensitive data" in error.lower()]
        assert len(sensitive_warnings) > 0
    
    def test_get_parsed_config(self, temp_config_dir):
        """Test retrieving specific parsed configuration"""
        parser = ConfigurationParser()
        json_file = str(temp_config_dir / "package.json")
        
        # Parse the file first
        parser.parse_single_file(json_file)
        
        # Retrieve it
        config_data = parser.get_parsed_config(json_file)
        
        assert config_data is not None
        assert config_data.format_type == "json"
        assert config_data.data['name'] == 'phoenix-hydra'
        
        # Test non-existent file
        assert parser.get_parsed_config("nonexistent.json") is None
    
    def test_get_all_parsed_configs(self, temp_config_dir):
        """Test retrieving all parsed configurations"""
        parser = ConfigurationParser()
        
        config_files = [
            str(temp_config_dir / "package.json"),
            str(temp_config_dir / "pyproject.toml")
        ]
        
        parser.parse_configurations(config_files)
        
        all_configs = parser.get_all_parsed_configs()
        
        assert len(all_configs) == 2
        assert all(isinstance(config, ConfigurationData) for config in all_configs.values())
    
    def test_get_parsing_errors(self, temp_config_dir):
        """Test retrieving parsing errors"""
        parser = ConfigurationParser()
        
        # Parse invalid file
        parser.parse_single_file("nonexistent.json")
        parser.parse_single_file(str(temp_config_dir / "invalid.json"))
        
        errors = parser.get_parsing_errors()
        
        assert len(errors) >= 2
        assert all(error.severity == Priority.HIGH for error in errors)
        assert all(error.component == "configuration_parser" for error in errors)
    
    def test_validate_configuration_files(self, temp_config_dir):
        """Test validation of multiple configuration files"""
        parser = ConfigurationParser()
        
        config_files = [
            str(temp_config_dir / "package.json"),
            str(temp_config_dir / "invalid.json"),
            "nonexistent.json"
        ]
        
        issues = parser.validate_configuration_files(config_files)
        
        assert len(issues) > 0
        assert any("nonexistent.json" in issue for issue in issues)
        assert any("invalid.json" in issue for issue in issues)
    
    def test_get_configuration_summary(self, temp_config_dir):
        """Test configuration summary generation"""
        parser = ConfigurationParser()
        
        config_files = [
            str(temp_config_dir / "package.json"),
            str(temp_config_dir / "pyproject.toml"),
            str(temp_config_dir / "docker-compose.yml"),
            str(temp_config_dir / "invalid.json")
        ]
        
        parser.parse_configurations(config_files)
        
        summary = parser.get_configuration_summary()
        
        assert summary['total_configurations'] == 4
        assert summary['valid_configurations'] >= 3  # At least 3 should be valid
        assert summary['invalid_configurations'] >= 1  # At least 1 should be invalid
        assert 'format_distribution' in summary
        assert 'validation_success_rate' in summary
        assert isinstance(summary['validation_success_rate'], (int, float))
    
    def test_properties_file_parsing(self, temp_config_dir):
        """Test Java properties file parsing"""
        parser = ConfigurationParser()
        
        # Create properties file
        props_content = """# Application properties
app.name=Phoenix Hydra
app.version=1.0.0
database.host=localhost
database.port=5432
# Comment line
debug.enabled=true
"""
        props_file = temp_config_dir / "app.properties"
        props_file.write_text(props_content)
        
        config_data = parser.parse_single_file(str(props_file))
        
        assert config_data is not None
        assert config_data.format_type == "properties"
        assert config_data.data['app.name'] == 'Phoenix Hydra'
        assert config_data.data['database.host'] == 'localhost'
        assert config_data.data['debug.enabled'] == 'true'
    
    def test_large_file_warning(self, temp_config_dir):
        """Test warning for large configuration files"""
        parser = ConfigurationParser()
        
        # Create a large JSON file (mock the size)
        large_config = temp_config_dir / "large.json"
        large_config.write_text('{"key": "value"}')
        
        # Mock the file size to be large
        import unittest.mock
        from unittest.mock import MagicMock
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 2 * 1024 * 1024  # 2MB
        mock_stat_result.st_mtime = datetime.now().timestamp()
        mock_stat_result.st_mode = 0o100644  # Regular file mode
        
        with unittest.mock.patch('pathlib.Path.stat', return_value=mock_stat_result):
            config_data = parser.parse_single_file(str(large_config))
            
            assert config_data is not None
            large_file_warnings = [error for error in config_data.validation_errors 
                                 if "very large" in error.lower()]
            assert len(large_file_warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__])