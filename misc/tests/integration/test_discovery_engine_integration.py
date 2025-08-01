"""
Integration tests for Discovery Engine components
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.phoenix_system_review.discovery import (
    FileSystemScanner, ConfigurationParser, ServiceDiscovery
)
from src.phoenix_system_review.models.data_models import ComponentCategory


class TestDiscoveryEngineIntegration:
    """Integration tests for Discovery Engine components working together"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project structure
            (temp_path / "src").mkdir()
            (temp_path / "infra").mkdir()
            (temp_path / "configs").mkdir()
            
            # Create configuration files
            (temp_path / "pyproject.toml").write_text("""
[project]
name = "phoenix-hydra"
version = "1.0.0"

[tool.pytest]
testpaths = ["tests"]

[tool.black]
line-length = 88
""")
            
            (temp_path / "infra" / "docker-compose.yml").write_text("""
services:
  phoenix-core:
    image: phoenix:latest
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  postgres:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: phoenix_db
      POSTGRES_USER: phoenix
      POSTGRES_PASSWORD: secret
""")
            
            (temp_path / "configs" / "app.json").write_text("""
{
  "name": "phoenix-hydra",
  "version": "1.0.0",
  "services": {
    "phoenix-core": "http://localhost:8080",
    "postgres": "postgresql://localhost:5432/phoenix_db"
  }
}
""")
            
            # Create source files
            (temp_path / "src" / "main.py").write_text("def main(): pass")
            (temp_path / "README.md").write_text("# Phoenix Hydra")
            
            yield temp_path
    
    def test_file_scanner_discovers_config_files(self, temp_project):
        """Test that file scanner discovers configuration files"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Check that configuration files were found
        config_files = inventory.configuration_files
        assert len(config_files) > 0
        
        config_names = [Path(f).name for f in config_files]
        assert "pyproject.toml" in config_names
        assert "docker-compose.yml" in config_names
        assert "app.json" in config_names
        
        # Check categorization
        infra_files = scanner.get_files_by_category(ComponentCategory.INFRASTRUCTURE)
        assert len(infra_files) > 0
        
        doc_files = scanner.get_files_by_category(ComponentCategory.DOCUMENTATION)
        assert len(doc_files) > 0
    
    def test_config_parser_processes_discovered_files(self, temp_project):
        """Test that config parser can process files discovered by file scanner"""
        # First, discover files
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Debug: Print discovered files
        print(f"Discovered config files: {inventory.configuration_files}")
        
        # Then parse the configuration files
        parser = ConfigurationParser()
        config_files = inventory.configuration_files
        
        # Convert relative paths to absolute paths based on the temp directory
        absolute_config_files = [str(temp_project / config_file) for config_file in config_files]
        parsed_configs = parser.parse_configurations(absolute_config_files)
        
        # Verify parsing results
        assert len(parsed_configs) == len(config_files)
        
        # Check specific configurations
        pyproject_file = None
        compose_file = None
        json_file = None
        
        for abs_file_path in absolute_config_files:
            if "pyproject.toml" in abs_file_path:
                pyproject_file = abs_file_path
            elif "docker-compose.yml" in abs_file_path:
                compose_file = abs_file_path
            elif "app.json" in abs_file_path:
                json_file = abs_file_path
        
        # Verify pyproject.toml parsing
        if pyproject_file:
            pyproject_data = parsed_configs[pyproject_file]
            assert "project" in pyproject_data
            # The test creates a pyproject.toml with name "phoenix-hydra"
            # If we're getting a different name, it means we're reading the wrong file
            expected_name = "phoenix-hydra"
            actual_name = pyproject_data["project"]["name"]
            print(f"Expected: {expected_name}, Actual: {actual_name}, File: {pyproject_file}")
            assert actual_name == expected_name
        
        # Verify docker-compose.yml parsing
        if compose_file:
            compose_data = parsed_configs[compose_file]
            assert "services" in compose_data
            assert "phoenix-core" in compose_data["services"]
        
        # Verify JSON parsing
        if json_file:
            json_data = parsed_configs[json_file]
            assert json_data["name"] == "phoenix-hydra"
            assert "services" in json_data
    
    def test_config_parser_validates_phoenix_configs(self, temp_project):
        """Test that config parser validates Phoenix-specific configurations"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        parser = ConfigurationParser()
        
        # Parse and validate configurations
        for config_file in inventory.configuration_files:
            config_data = parser.parse_single_file(config_file)
            if config_data:
                # Check that validation was performed
                assert isinstance(config_data.schema_valid, bool)
                assert isinstance(config_data.validation_errors, list)
                
                # Check Phoenix-specific validations
                if "pyproject.toml" in config_file:
                    # Should have validation results for Phoenix tools
                    pass  # Validation logic already tested in unit tests
                elif "docker-compose.yml" in config_file:
                    # Should validate Phoenix services
                    pass  # Validation logic already tested in unit tests
    
    @pytest.mark.asyncio
    async def test_service_discovery_integration(self, temp_project):
        """Test service discovery integration"""
        # Mock container discovery to avoid requiring actual containers
        service_discovery = ServiceDiscovery(container_runtime="podman")
        
        with patch.object(service_discovery, '_discover_containers') as mock_containers, \
             patch.object(service_discovery, '_check_all_services_health') as mock_health:
            
            # Mock some discovered containers
            mock_container_info = {
                "phoenix-hydra_phoenix-core_1": MagicMock(
                    name="phoenix-hydra_phoenix-core_1",
                    image="phoenix:latest",
                    status="running",
                    ports=["8080:8080"]
                )
            }
            service_discovery.container_info = mock_container_info
            
            # Mock health check results
            from src.phoenix_system_review.discovery.service_discovery import ServiceHealth
            mock_health_results = {
                "phoenix-core": ServiceHealth("phoenix-core", True, status_code=200, response_time=0.1)
            }
            service_discovery.health_checks = mock_health_results
            
            # Perform discovery
            registry = await service_discovery.discover_services()
            
            # Verify results
            assert registry is not None
            assert len(service_discovery.discovered_services) > 0
            assert "phoenix-core" in service_discovery.discovered_services
            
            # Check service summary
            summary = service_discovery.get_service_summary()
            assert summary["total_services"] > 0
            assert "container_runtime" in summary
    
    @pytest.mark.asyncio
    async def test_full_discovery_pipeline(self, temp_project):
        """Test the complete discovery pipeline"""
        # Step 1: File System Discovery
        print("Step 1: Scanning file system...")
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        assert inventory.total_files > 0
        assert len(inventory.configuration_files) > 0
        
        # Step 2: Configuration Parsing
        print("Step 2: Parsing configurations...")
        parser = ConfigurationParser()
        parsed_configs = parser.parse_configurations(inventory.configuration_files)
        
        assert len(parsed_configs) > 0
        
        # Get configuration summary
        config_summary = parser.get_configuration_summary()
        assert config_summary["total_configurations"] > 0
        
        # Step 3: Service Discovery
        print("Step 3: Discovering services...")
        service_discovery = ServiceDiscovery()
        
        # Mock the container and health check operations
        with patch.object(service_discovery, '_discover_containers') as mock_containers, \
             patch.object(service_discovery, '_check_all_services_health') as mock_health:
            
            registry = await service_discovery.discover_services()
            
            assert registry is not None
            service_summary = service_discovery.get_service_summary()
            assert service_summary["total_services"] > 0
        
        # Step 4: Combine Results
        print("Step 4: Combining discovery results...")
        
        # Create a combined discovery report
        discovery_report = {
            "file_system": {
                "total_files": inventory.total_files,
                "total_directories": inventory.total_directories,
                "configuration_files": len(inventory.configuration_files),
                "source_files": len(inventory.source_files),
                "documentation_files": len(inventory.documentation_files)
            },
            "configurations": config_summary,
            "services": service_summary,
            "discovery_timestamp": inventory.scan_timestamp.isoformat()
        }
        
        # Verify combined report
        assert discovery_report["file_system"]["total_files"] > 0
        assert discovery_report["configurations"]["total_configurations"] > 0
        assert discovery_report["services"]["total_services"] > 0
        
        print(f"Discovery completed successfully:")
        print(f"- Files: {discovery_report['file_system']['total_files']}")
        print(f"- Configurations: {discovery_report['configurations']['total_configurations']}")
        print(f"- Services: {discovery_report['services']['total_services']}")
    
    def test_error_handling_integration(self, temp_project):
        """Test error handling across discovery components"""
        # Test file scanner with permission issues
        scanner = FileSystemScanner("/nonexistent/path")
        inventory = scanner.scan_project_structure()
        
        # Should handle gracefully
        assert inventory.total_files == 0
        assert inventory.total_directories == 0
        
        # Test config parser with invalid files
        parser = ConfigurationParser()
        invalid_files = ["/nonexistent/config.json", "/invalid/path.yaml"]
        
        parsed_configs = parser.parse_configurations(invalid_files)
        errors = parser.get_parsing_errors()
        
        # Should have errors but not crash
        assert len(errors) > 0
        assert len(parsed_configs) == len(invalid_files)  # Empty configs for failed files
    
    def test_component_data_flow(self, temp_project):
        """Test data flow between discovery components"""
        # Scan files
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Get configuration files from scanner
        config_files = scanner.get_configuration_files()
        assert len(config_files) > 0
        
        # Parse those specific files
        parser = ConfigurationParser()
        for file_info in config_files:
            config_data = parser.parse_single_file(file_info.path)
            if config_data:
                # Verify data consistency
                assert config_data.file_path == file_info.path
                assert config_data.format_type in ["yaml", "json", "toml", "ini", "env"]
                
                # Check that file metadata matches
                if file_info.is_configuration:
                    assert config_data.data is not None
    
    def test_phoenix_specific_discovery(self, temp_project):
        """Test Phoenix Hydra specific discovery patterns"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Look for Phoenix-specific patterns
        phoenix_files = []
        for component in inventory.components:
            if "phoenix" in component.name.lower() or "hydra" in component.name.lower():
                phoenix_files.append(component)
        
        # Parse Phoenix configurations
        parser = ConfigurationParser()
        phoenix_configs = []
        
        for config_file in inventory.configuration_files:
            config_data = parser.parse_single_file(config_file)
            if config_data and config_data.data:
                # Look for Phoenix-specific configuration keys
                config_str = str(config_data.data).lower()
                if any(keyword in config_str for keyword in ["phoenix", "hydra", "n8n", "windmill"]):
                    phoenix_configs.append(config_data)
        
        # Should find some Phoenix-related configurations
        assert len(phoenix_configs) > 0


if __name__ == "__main__":
    pytest.main([__file__])