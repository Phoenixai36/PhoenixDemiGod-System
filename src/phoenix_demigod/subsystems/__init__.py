"""
Specialized subsystems for the Phoenix DemiGod system.

This module contains the various subsystems that can be generated
and specialized by the differentiation engine.
"""

from .synchronization import SynchronizationSubsystem
from .intelligence import IntelligenceSubsystem
from .optimization import OptimizationSubsystem
from .security import SecuritySubsystem

__all__ = [
    "SynchronizationSubsystem",
    "IntelligenceSubsystem", 
    "OptimizationSubsystem",
    "SecuritySubsystem"
]