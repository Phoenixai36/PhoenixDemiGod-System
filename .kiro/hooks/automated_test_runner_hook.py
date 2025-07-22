"""
Automated Test Runner Hook for the Agent Hooks Enhancement system.

This hook automatically runs tests when code files are modified.
"""

from typing import Any, Dict

from ..engine.hooks.automated_test_runner_hook import AutomatedTestRunnerHook as BaseAutomatedTestRunnerHook


class AutomatedTestRunnerHook(BaseAutomatedTestRunnerHook):
    """
    Hook that automatically runs tests when code files are modified.
    
    This is a wrapper around the main implementation in the engine.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the automated test runner hook."""
        super().__init__(config)

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
