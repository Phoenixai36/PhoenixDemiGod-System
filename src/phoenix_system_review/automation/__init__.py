"""
Automation and Scheduling Module for Phoenix Hydra System Review

This module provides automated review scheduling, VS Code task integration,
and Kiro agent hooks for continuous monitoring and alerting.
"""

from .scheduler import ReviewScheduler
from .vscode_integration import VSCodeTaskIntegration
from .kiro_hooks import KiroAgentHooks
from .monitoring import ContinuousMonitoring

__all__ = [
    "ReviewScheduler",
    "VSCodeTaskIntegration",
    "KiroAgentHooks",
    "ContinuousMonitoring"
]
