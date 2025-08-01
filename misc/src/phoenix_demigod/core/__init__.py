"""
Core components of the Phoenix DemiGod system.

This module contains the fundamental components that form the nucleus
of the self-evolving system.
"""

from .nucleus import NucleusManager
from .state_tree import StateTree, StateNode, StateTreeManager
from .interfaces import Subsystem, CommunicationChannel

__all__ = [
    "NucleusManager",
    "StateTree", 
    "StateNode",
    "StateTreeManager",
    "Subsystem",
    "CommunicationChannel"
]