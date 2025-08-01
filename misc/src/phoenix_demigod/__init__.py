"""
Phoenix DemiGod - Self-Evolving Digital Organism

A biomimetic system that functions like a digital cell, capable of:
- Self-analysis and adaptation
- Autonomous subsystem generation
- Regeneration after failures
- Distributed operation with sovereignty
"""

__version__ = "1.0.0"
__author__ = "Phoenix DemiGod Team"

from .core.nucleus import NucleusManager
from .core.state_tree import StateTree, StateNode
from .engines.traversal import TraversalEngine
from .engines.differentiation import DifferentiationEngine
from .engines.regeneration import RegenerationEngine
from .communication.layer import CommunicationLayer

__all__ = [
    "NucleusManager",
    "StateTree",
    "StateNode", 
    "TraversalEngine",
    "DifferentiationEngine",
    "RegenerationEngine",
    "CommunicationLayer"
]