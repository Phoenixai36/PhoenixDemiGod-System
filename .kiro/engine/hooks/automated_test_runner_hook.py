"""
Automated Test Runner Hook for the Agent Hooks Enhancement system.

This hook automatically runs tests when code files are modified.
"""

import time
import asyncio
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from ..core.models import AgentHook, HookContext, HookResult, HookPriority, HookTrigger
from ..events.models import EventType, FileEvent
from ..utils.logging import get_logger, ExecutionError


class AutomatedTestRunnerHook(AgentHook):
    """
    Hook that automatically runs tests when code files are modified.
    
    This hook monitors file system events for code changes and automatically
    runs relevant tests for the changed modules.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the automated test runner hook."""
        super().__init__(config)
        self.logger = get_logger(f"hooks.{self.__class__.__name__}")
        
        # Load configuration
        self.test_command = config.get("test_command", "pytest")
        self.test_directory = config.get("test_directory", "tests")
        self.code_directory = config.get("code_directory", "src")
        self.file_patterns = config.get("file_patterns", ["*.py"])
        self.exclude_patterns = config.get("exclude_patterns", ["__pycache__/*", "*.pyc"])
        self.run_all_tests_patterns = config.get("run_all_tests_patterns", ["setup.py", "pyproject.toml", "requirements.txt"])
        self.test_timeout_seconds = config.get("test_timeout_seconds", 60)
        self.debounce_seconds = config.get("debounce_seconds", 2.0)
        
        # Internal state
        self.last_test_run: Dict[str, float] = {}  # module_name -> timestamp
        self.test_results_cache: Dict[str, Tuple[bool, str]] = {}  # module_name -> (success, output)
    
    async def should_execute(self, context: HookContext) -> bool:
        """
        Determine if this hook should execute.
        
        This hook executes when:
        1. It is enabled
        2. The event is a file modification, creation, or rename event
        3. The file matches the configured patterns
        4. We're not in a debounce period for the module
        """
        if not self.enabled:
            return False
        
        # Check if this is a file event
        event_type = context.trigger_event.get("type")
        if event_type not in [EventType.FILE_SAVE.value, EventType.FILE_MODIFY.value, 
                             EventType.FILE_CREATE.value, EventType.FILE_RENAME.value]:
            return False
        
        # Get file path
        file_path = context.trigger_event.get("file_path")
        if not file_path:
            return False
        
        # Convert to Path object if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Check if the file matches the configured patterns
        if not self._matches_patterns(file_path.name, self.file_patterns):
            return False
        
        # Check if the file is excluded
        if self._matches_patterns(file_path.name, self.exclude_patterns):
            return False
        
        # Determine the module name
        module_name = self._get_module_name(file_path)
        if not module_name:
            return False
        
        # Check if we're in a debounce period
        last_run = self.last_test_run.get(module_name, 0)
        if time.time() - last_run < self.debounce_seconds:
            return False
        
        return True
    
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook to run tests for changed code.
        
        Args:
            context: Current execution context
            
        Returns:
            Result of the hook execution
        """
        start_time = time.time()
        
        try:
            # Get file path
            file_path = context.trigger_event.get("file_path")
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            self.logger.info(
                f"Running tests for changed file: {file_path}",
                extra={"file_path": str(file_path), "execution_id": context.execution_id}
            )
            
            # Determine if we should run all tests
            run_all_tests = self._matches_patterns(file_path.name, self.run_all_tests_patterns)
            
            # Determine the module name and test path
            module_name = self._get_module_name(file_path)
            test_path = self._get_test_path(file_path, module_name, run_all_tests)
            
            # Update last test run time
            self.last_test_run[module_name] = time.time()
            
            # Run the tests
            success, output = await self._run_tests(test_path)
            
            # Cache the test results
            self.test_results_cache[module_name] = (success, output)
            
            if success:
                message = f"Tests passed for {module_name}"
                self.logger.info(
                    message,
                    extra={"module_name": module_name, "execution_id": context.execution_id}
                )
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=True,
                    message=message,
                    actions_taken=[f"Ran tests for {module_name}"],
                    suggestions=[],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "test_path": str(test_path)
                    },
                    execution_time_ms=execution_time_ms
                )
            else:
                message = f"Tests failed for {module_name}"
                self.logger.warning(
                    message,
                    extra={"module_name": module_name, "execution_id": context.execution_id}
                )
                
                # Extract error information from test output
                error_summary = self._extract_error_summary(output)
                
                execution_time_ms = (time.time() - start_time) * 1000
                return HookResult(
                    success=False,
                    message=message,
                    actions_taken=[f"Ran tests for {module_name}"],
                    suggestions=[
                        "Fix failing tests",
                        "Check test dependencies",
                        "Review test output for details"
                    ],
                    metrics={
                        "execution_time_ms": execution_time_ms,
                        "test_path": str(test_path)
                    },
                    execution_time_ms=execution_time_ms,
                    error=ExecutionError(f"Tests failed: {error_summary}")
                )
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Error executing automated test runner hook: {e}",
                extra={"execution_id": context.execution_id}
            )
            
            return HookResult(
                success=False,
                message=f"Error executing automated test runner hook: {e}",
                actions_taken=[],
                suggestions=["Check hook configuration", "Verify test environment"],
                metrics={"execution_time_ms": execution_time_ms},
                execution_time_ms=execution_time_ms,
                error=ExecutionError(str(e))
            )
    
    def get_resource_requirements(self) -> Dict[str, Any]:
        """
        Get resource requirements for this hook.
        
        Returns:
            Dictionary of resource requirements
        """
        return {
            "cpu": 0.5,
            "memory_mb": 200,
            "disk_mb": 50,
            "network": False
        }
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """
        Check if a filename matches any of the patterns.
        
        Args:
            filename: Filename to check
            patterns: List of glob patterns
            
        Returns:
            True if the filename matches any pattern, False otherwise
        """
        import fnmatch
        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)
    
    def _get_module_name(self, file_path: Path) -> Optional[str]:
        """
        Get the module name for a file path.
        
        Args:
            file_path: File path
            
        Returns:
            Module name, or None if the file is not in a module
        """
        # Convert to absolute path
        file_path = file_path.resolve()
        
        # Check if the file is in the code directory
        code_dir = Path(self.code_directory).resolve()
        if code_dir in file_path.parents:
            # Get the relative path from the code directory
            rel_path = file_path.relative_to(code_dir)
            
            # Convert path to module name
            module_parts = list(rel_path.parts)
            
            # Remove file extension
            if module_parts and "." in module_parts[-1]:
                module_parts[-1] = module_parts[-1].split(".", 1)[0]
            
            # Join with dots to form module name
            return ".".join(module_parts)
        
        # Check if the file is in the test directory
        test_dir = Path(self.test_directory).resolve()
        if test_dir in file_path.parents:
            # Get the relative path from the test directory
            rel_path = file_path.relative_to(test_dir)
            
            # Convert path to module name
            module_parts = list(rel_path.parts)
            
            # Remove file extension and "test_" prefix
            if module_parts and "." in module_parts[-1]:
                module_name = module_parts[-1].split(".", 1)[0]
                if module_name.startswith("test_"):
                    module_name = module_name[5:]
                module_parts[-1] = module_name
            
            # Join with dots to form module name
            return ".".join(module_parts)
        
        # If the file is not in a module, use the filename without extension
        return file_path.stem
    
    def _get_test_path(self, file_path: Path, module_name: str, run_all_tests: bool) -> str:
        """
        Get the test path for a file.
        
        Args:
            file_path: File path
            module_name: Module name
            run_all_tests: Whether to run all tests
            
        Returns:
            Test path
        """
        if run_all_tests:
            return self.test_directory
        
        # Convert to absolute path
        file_path = file_path.resolve()
        
        # If the file is a test file, run it directly
        test_dir = Path(self.test_directory).resolve()
        if test_dir in file_path.parents:
            return str(file_path)
        
        # Otherwise, try to find the corresponding test file
        module_parts = module_name.split(".")
        
        # Check for test file with the same name
        test_file = test_dir / Path(*module_parts[:-1]) / f"test_{module_parts[-1]}.py"
        if test_file.exists():
            return str(test_file)
        
        # Check for test directory with the same name
        test_dir_path = test_dir / Path(*module_parts)
        if test_dir_path.exists() and test_dir_path.is_dir():
            return str(test_dir_path)
        
        # If no specific test is found, run all tests for the module
        module_dir = test_dir / Path(*module_parts[:-1])
        if module_dir.exists() and module_dir.is_dir():
            return str(module_dir)
        
        # If no tests are found, run all tests
        return self.test_directory
    
    async def _run_tests(self, test_path: str) -> Tuple[bool, str]:
        """
        Run tests for a specific path.
        
        Args:
            test_path: Path to test file or directory
            
        Returns:
            Tuple of (success, output)
        """
        try:
            # Build the test command
            cmd = f"{self.test_command} {test_path}"
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.test_timeout_seconds
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.kill()
                return False, f"Test execution timed out after {self.test_timeout_seconds} seconds"
            
            # Check if the tests passed
            success = process.returncode == 0
            
            # Combine stdout and stderr
            output = stdout.decode() + stderr.decode()
            
            return success, output
        
        except Exception as e:
            return False, f"Error running tests: {e}"
    
    def _extract_error_summary(self, output: str) -> str:
        """
        Extract a summary of test errors from the output.
        
        Args:
            output: Test output
            
        Returns:
            Error summary
        """
        # Look for error summary at the end of the output
        lines = output.splitlines()
        
        # Try to find the summary line (e.g., "FAILED tests/test_module.py::test_function")
        error_lines = []
        for line in reversed(lines):
            if "FAILED" in line and "::" in line:
                error_lines.append(line.strip())
            elif "ERROR" in line and "::" in line:
                error_lines.append(line.strip())
            
            # Stop after finding a few errors
            if len(error_lines) >= 5:
                break
        
        if error_lines:
            return "\n".join(reversed(error_lines))
        
        # If no specific error lines are found, return a generic message
        return "Tests failed, see output for details"