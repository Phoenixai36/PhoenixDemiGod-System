"""
Tests for the Automated Test Runner Hook.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

# Add the .kiro directory to the Python path
kiro_path = Path(__file__).parent.parent / ".kiro"
sys.path.insert(0, str(kiro_path))

from engine.hooks.automated_test_runner_hook import AutomatedTestRunnerHook
from engine.core.models import HookContext
from engine.events.models import EventType


class TestAutomatedTestRunnerHook:
    """Test the AutomatedTestRunnerHook class."""
    
    @pytest.fixture
    def hook_config(self):
        """Create a basic hook configuration."""
        return {
            "id": "test_hook",
            "name": "Test Hook",
            "enabled": True,
            "test_command": "pytest",
            "test_directory": "tests",
            "code_directory": "src",
            "file_patterns": ["*.py"],
            "exclude_patterns": ["__pycache__/*", "*.pyc"],
            "debounce_seconds": 0.1
        }
    
    @pytest.fixture
    def hook(self, hook_config):
        """Create a hook instance."""
        return AutomatedTestRunnerHook(hook_config)
    
    @pytest.fixture
    def file_context(self):
        """Create a context for file events."""
        return HookContext(
            trigger_event={
                "type": EventType.FILE_SAVE.value,
                "file_path": "src/test_module.py"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    def test_hook_initialization(self, hook, hook_config):
        """Test hook initialization."""
        assert hook.id == "test_hook"
        assert hook.name == "Test Hook"
        assert hook.enabled is True
        assert hook.test_command == "pytest"
        assert hook.test_directory == "tests"
        assert hook.code_directory == "src"
    
    @pytest.mark.asyncio
    async def test_should_execute_enabled_hook(self, hook, file_context):
        """Test that enabled hook should execute for valid file events."""
        result = await hook.should_execute(file_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_execute_disabled_hook(self, hook_config, file_context):
        """Test that disabled hook should not execute."""
        hook_config["enabled"] = False
        hook = AutomatedTestRunnerHook(hook_config)
        
        result = await hook.should_execute(file_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_wrong_event_type(self, hook):
        """Test that hook should not execute for wrong event types."""
        context = HookContext(
            trigger_event={
                "type": "wrong_event_type",
                "file_path": "src/test_module.py"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_excluded_file(self, hook):
        """Test that hook should not execute for excluded files."""
        context = HookContext(
            trigger_event={
                "type": EventType.FILE_SAVE.value,
                "file_path": "__pycache__/test.pyc"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    def test_matches_patterns(self, hook):
        """Test pattern matching functionality."""
        # Should match Python files
        assert hook._matches_patterns("test.py", ["*.py"]) is True
        assert hook._matches_patterns("module.py", ["*.py"]) is True
        
        # Should not match other files
        assert hook._matches_patterns("test.txt", ["*.py"]) is False
        assert hook._matches_patterns("test.js", ["*.py"]) is False
        
        # Should match multiple patterns
        assert hook._matches_patterns("test.py", ["*.py", "*.js"]) is True
        assert hook._matches_patterns("test.js", ["*.py", "*.js"]) is True
    
    def test_get_module_name(self, hook):
        """Test module name extraction."""
        # Test code directory file
        module_name = hook._get_module_name(Path("src/package/module.py"))
        assert module_name == "package.module"
        
        # Test test directory file
        module_name = hook._get_module_name(Path("tests/test_module.py"))
        assert module_name == "module"
        
        # Test root file
        module_name = hook._get_module_name(Path("standalone.py"))
        assert module_name == "standalone"
    
    def test_get_test_path(self, hook):
        """Test test path determination."""
        # Test for code file
        test_path = hook._get_test_path(Path("src/module.py"), "module", False)
        assert "tests" in test_path
        
        # Test for run all tests
        test_path = hook._get_test_path(Path("setup.py"), "setup", True)
        assert test_path == "tests"
    
    @pytest.mark.asyncio
    async def test_run_tests_success(self, hook):
        """Test successful test execution."""
        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock successful process
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"All tests passed", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            success, output = await hook._run_tests("tests/test_module.py")
            
            assert success is True
            assert "All tests passed" in output
    
    @pytest.mark.asyncio
    async def test_run_tests_failure(self, hook):
        """Test failed test execution."""
        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            # Mock failed process
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Tests failed")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            success, output = await hook._run_tests("tests/test_module.py")
            
            assert success is False
            assert "Tests failed" in output
    
    @pytest.mark.asyncio
    async def test_execute_success(self, hook, file_context):
        """Test successful hook execution."""
        with patch.object(hook, '_run_tests', return_value=(True, "All tests passed")):
            result = await hook.execute(file_context)
            
            assert result.success is True
            assert "Tests passed" in result.message
            assert len(result.actions_taken) > 0
            assert result.execution_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_execute_failure(self, hook, file_context):
        """Test failed hook execution."""
        with patch.object(hook, '_run_tests', return_value=(False, "Tests failed")):
            result = await hook.execute(file_context)
            
            assert result.success is False
            assert "Tests failed" in result.message
            assert len(result.suggestions) > 0
            assert result.execution_time_ms is not None
    
    def test_extract_error_summary(self, hook):
        """Test error summary extraction."""
        output = """
        ============================= FAILURES =============================
        FAILED tests/test_module.py::test_function - AssertionError: Test failed
        FAILED tests/test_other.py::test_other - ValueError: Invalid value
        ============================= short test summary info =============================
        """
        
        summary = hook._extract_error_summary(output)
        assert "FAILED tests/test_module.py::test_function" in summary
        assert "FAILED tests/test_other.py::test_other" in summary
    
    def test_get_resource_requirements(self, hook):
        """Test resource requirements."""
        requirements = hook.get_resource_requirements()
        
        assert "cpu" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network" in requirements
        assert requirements["cpu"] > 0
        assert requirements["memory_mb"] > 0