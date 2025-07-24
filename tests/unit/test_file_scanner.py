"""
Unit tests for File System Scanner
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.phoenix_system_review.discovery.file_scanner import FileSystemScanner, FileInfo
from src.phoenix_system_review.models.data_models import ComponentCategory, ComponentStatus


class TestFileSystemScanner:
    """Test cases for FileSystemScanner class"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create directory structure
            (temp_path / "src").mkdir()
            (temp_path / "src" / "core").mkdir()
            (temp_path / "tests").mkdir()
            (temp_path / "docs").mkdir()
            (temp_path / "scripts").mkdir()
            (temp_path / "infra").mkdir()
            (temp_path / "__pycache__").mkdir()  # Should be excluded
            
            # Create test files
            (temp_path / "pyproject.toml").write_text("[tool.pytest]")
            (temp_path / "README.md").write_text("# Test Project")
            (temp_path / "src" / "__init__.py").write_text("")
            (temp_path / "src" / "core" / "main.py").write_text("def main(): pass")
            (temp_path / "tests" / "test_main.py").write_text("def test_main(): pass")
            (temp_path / "docs" / "guide.md").write_text("# Guide")
            (temp_path / "scripts" / "deploy.sh").write_text("#!/bin/bash")
            (temp_path / "infra" / "main.tf").write_text("resource 'aws_instance' 'test' {}")
            (temp_path / ".env").write_text("DEBUG=true")
            (temp_path / "__pycache__" / "test.pyc").write_text("compiled")  # Should be excluded
            
            yield temp_path
    
    def test_scanner_initialization(self, temp_project):
        """Test scanner initialization"""
        scanner = FileSystemScanner(str(temp_project))
        
        assert scanner.root_path == temp_project.resolve()
        assert scanner.include_hidden is False
        assert len(scanner.scanned_files) == 0
        assert len(scanner.components) == 0
    
    def test_scan_project_structure(self, temp_project):
        """Test complete project structure scanning"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Check inventory properties
        assert inventory.total_files > 0
        assert inventory.total_directories > 0
        assert len(inventory.components) > 0
        assert len(inventory.configuration_files) > 0
        assert len(inventory.source_files) > 0
        assert len(inventory.documentation_files) > 0
        assert isinstance(inventory.scan_timestamp, datetime)
        
        # Verify specific files were found
        file_names = [Path(f.path).name for f in scanner.scanned_files]
        assert "pyproject.toml" in file_names
        assert "main.py" in file_names
        assert "test_main.py" in file_names
        assert "README.md" in file_names
        
        # Verify excluded files were not found
        assert "test.pyc" not in file_names
    
    def test_file_type_detection(self, temp_project):
        """Test file type detection logic"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Test Python file
        py_file = temp_project / "test.py"
        py_file.write_text("print('hello')")
        file_info = scanner._analyze_file(py_file)
        assert file_info.file_type == "python"
        assert file_info.extension == ".py"
        
        # Test configuration file
        config_file = temp_project / "config.yaml"
        config_file.write_text("key: value")
        file_info = scanner._analyze_file(config_file)
        assert file_info.file_type == "yaml-config"
        assert file_info.is_configuration is True
        
        # Test test file
        test_file = temp_project / "test_example.py"
        test_file.write_text("def test_func(): pass")
        file_info = scanner._analyze_file(test_file)
        assert file_info.file_type == "python-test"
    
    def test_category_determination(self, temp_project):
        """Test component category determination"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Test infrastructure category
        infra_file = temp_project / "infra" / "main.tf"
        category = scanner._determine_category(infra_file, "terraform")
        assert category == ComponentCategory.INFRASTRUCTURE
        
        # Test testing category
        test_file = temp_project / "tests" / "test_example.py"
        category = scanner._determine_category(test_file, "python-test")
        assert category == ComponentCategory.TESTING
        
        # Test documentation category
        doc_file = temp_project / "docs" / "guide.md"
        category = scanner._determine_category(doc_file, "markdown")
        assert category == ComponentCategory.DOCUMENTATION
        
        # Test automation category
        script_file = temp_project / "scripts" / "deploy.sh"
        category = scanner._determine_category(script_file, "script")
        assert category == ComponentCategory.AUTOMATION
    
    def test_configuration_file_detection(self, temp_project):
        """Test configuration file detection"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Test known configuration files
        assert scanner._is_configuration_file(Path("pyproject.toml")) is True
        assert scanner._is_configuration_file(Path("package.json")) is True
        assert scanner._is_configuration_file(Path("docker-compose.yml")) is True
        assert scanner._is_configuration_file(Path(".env")) is True
        assert scanner._is_configuration_file(Path("config.yaml")) is True
        
        # Test non-configuration files
        assert scanner._is_configuration_file(Path("main.py")) is False
        assert scanner._is_configuration_file(Path("README.md")) is False
    
    def test_directory_exclusion(self, temp_project):
        """Test that excluded directories are skipped"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Check that __pycache__ files were excluded
        file_paths = [f.path for f in scanner.scanned_files]
        assert not any("__pycache__" in path for path in file_paths)
        assert not any("test.pyc" in path for path in file_paths)
    
    def test_file_hash_calculation(self, temp_project):
        """Test file content hash calculation"""
        scanner = FileSystemScanner(str(temp_project))
        
        test_file = temp_project / "test_hash.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        file_hash = scanner._calculate_file_hash(test_file)
        
        # Verify hash is calculated
        assert file_hash is not None
        assert len(file_hash) == 64  # SHA-256 hex length
        assert file_hash != ""
    
    def test_component_creation(self, temp_project):
        """Test component creation from discovered files"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # Check that components were created
        assert len(scanner.components) > 0
        
        # Find infrastructure component
        infra_components = [c for c in scanner.components if c.category == ComponentCategory.INFRASTRUCTURE]
        assert len(infra_components) > 0
        
        # Check component properties
        component = infra_components[0]
        assert component.name is not None
        assert component.category == ComponentCategory.INFRASTRUCTURE
        assert component.path is not None
        assert isinstance(component.configuration, dict)
        assert component.status in [ComponentStatus.OPERATIONAL, ComponentStatus.DEGRADED, ComponentStatus.UNKNOWN]
    
    def test_component_status_determination(self, temp_project):
        """Test component status determination logic"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Create file info with configuration
        config_file = FileInfo(
            path="config.yaml",
            name="config.yaml",
            extension=".yaml",
            size=100,
            modified_time=datetime.now(),
            file_type="yaml-config",
            category=ComponentCategory.INFRASTRUCTURE,
            is_configuration=True
        )
        
        # Test with configuration file
        status = scanner._determine_component_status([config_file])
        assert status in [ComponentStatus.OPERATIONAL, ComponentStatus.DEGRADED]
        
        # Test with no files
        status = scanner._determine_component_status([])
        assert status == ComponentStatus.FAILED
    
    def test_get_files_by_category(self, temp_project):
        """Test filtering files by category"""
        scanner = FileSystemScanner(str(temp_project))
        scanner.scan_project_structure()
        
        # Get documentation files
        doc_files = scanner.get_files_by_category(ComponentCategory.DOCUMENTATION)
        assert len(doc_files) > 0
        assert all(f.category == ComponentCategory.DOCUMENTATION for f in doc_files)
        
        # Get infrastructure files
        infra_files = scanner.get_files_by_category(ComponentCategory.INFRASTRUCTURE)
        assert len(infra_files) > 0
        assert all(f.category == ComponentCategory.INFRASTRUCTURE for f in infra_files)
    
    def test_get_configuration_files(self, temp_project):
        """Test getting all configuration files"""
        scanner = FileSystemScanner(str(temp_project))
        scanner.scan_project_structure()
        
        config_files = scanner.get_configuration_files()
        assert len(config_files) > 0
        assert all(f.is_configuration for f in config_files)
        
        # Check that pyproject.toml is included
        config_names = [Path(f.path).name for f in config_files]
        assert "pyproject.toml" in config_names
    
    def test_find_files_by_pattern(self, temp_project):
        """Test finding files by pattern matching"""
        scanner = FileSystemScanner(str(temp_project))
        scanner.scan_project_structure()
        
        # Find all Python files
        py_files = scanner.find_files_by_pattern("*.py")
        assert len(py_files) > 0
        assert all(f.extension == ".py" for f in py_files)
        
        # Find test files
        test_files = scanner.find_files_by_pattern("test_*.py")
        test_names = [f.name for f in test_files]
        assert any("test_" in name for name in test_names)
    
    def test_hidden_files_handling(self, temp_project):
        """Test handling of hidden files"""
        # Create hidden file
        hidden_file = temp_project / ".hidden"
        hidden_file.write_text("hidden content")
        
        # Test with include_hidden=False (default)
        scanner = FileSystemScanner(str(temp_project), include_hidden=False)
        scanner.scan_project_structure()
        
        file_names = [Path(f.path).name for f in scanner.scanned_files]
        assert ".hidden" not in file_names
        assert ".env" in file_names  # .env should be included as exception
        
        # Test with include_hidden=True
        scanner = FileSystemScanner(str(temp_project), include_hidden=True)
        scanner.scan_project_structure()
        
        file_names = [Path(f.path).name for f in scanner.scanned_files]
        assert ".hidden" in file_names
    
    @patch('builtins.print')
    def test_error_handling(self, mock_print, temp_project):
        """Test error handling during scanning"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Test with permission error
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            files, dirs = scanner._scan_directory(temp_project)
            mock_print.assert_called()
            assert files == 0
            assert dirs == 0
        
        # Test with general exception
        with patch('pathlib.Path.iterdir', side_effect=Exception("General error")):
            files, dirs = scanner._scan_directory(temp_project)
            mock_print.assert_called()
            assert files == 0
            assert dirs == 0
    
    def test_large_file_hash_skipping(self, temp_project):
        """Test that large files skip hash calculation"""
        scanner = FileSystemScanner(str(temp_project))
        
        # Create a large file (mock size)
        large_file = temp_project / "large_file.txt"
        large_file.write_text("content")
        
        # Mock file size to be > 1MB
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 2 * 1024 * 1024  # 2MB
            mock_stat.return_value.st_mtime = datetime.now().timestamp()
            
            file_info = scanner._analyze_file(large_file)
            assert file_info.content_hash is None
    
    def test_relative_path_handling(self, temp_project):
        """Test that file paths are relative to root"""
        scanner = FileSystemScanner(str(temp_project))
        inventory = scanner.scan_project_structure()
        
        # All file paths should be relative
        for file_info in scanner.scanned_files:
            assert not file_info.path.startswith('/')
            assert not file_info.path.startswith(str(temp_project))
    
    def test_empty_directory_handling(self):
        """Test handling of empty directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            scanner = FileSystemScanner(temp_dir)
            inventory = scanner.scan_project_structure()
            
            assert inventory.total_files == 0
            assert inventory.total_directories == 0
            assert len(inventory.components) == 0
            assert len(scanner.scanned_files) == 0


if __name__ == "__main__":
    pytest.main([__file__])