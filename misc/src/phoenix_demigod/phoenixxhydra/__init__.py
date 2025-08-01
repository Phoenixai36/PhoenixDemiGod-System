"""
PHOENIXxHYDRA System - Hybrid Cellular Architecture with Multi-Head Patterns

Extends the Phoenix DemiGod system with:
- Cellular digital architecture (100+ cells per HYDRA head)
- 7 specialized HYDRA heads with unique capabilities
- Evolutionary Gene Py system with animal-inspired traits
- P2P Rubik mesh networking
- Tesla-inspired orchestration with sacred numerology
- Digital natural selection and chaos engineering
"""

__version__ = "1.0.0"

from .core.digital_cell import DigitalCell, CellLifecycleManager
from .core.hydra_head import HydraHead, HydraHeadRegistry
from .core.phoenix_core import PhoenixCore, PhoenixCoreOrchestrator
from .core.gene_py import GenePy, GenePool, RubikPersonalityMatrix
from .core.events import SystemEvent, EventBus, EventType
from .core.p2p_mesh import P2PNetworkManager, MeshNetworkResilience
from .agents.nick_orchestrator import NickOrchestrator
from .agents.kai_agent import KaiAgent
from .agents.thanatos_agent import ThanatosAgent
from .agents.niso_agent import NisoAgent
from .agents.mape_agent import MapEAgent

__all__ = [
    "DigitalCell",
    "CellLifecycleManager", 
    "HydraHead",
    "HydraHeadRegistry",
    "PhoenixCore",
    "PhoenixCoreOrchestrator",
    "GenePy",
    "GenePool",
    "RubikPersonalityMatrix",
    "SystemEvent",
    "EventBus",
    "EventType",
    "P2PNetworkManager",
    "MeshNetworkResilience",
    "NickOrchestrator",
    "KaiAgent",
    "ThanatosAgent",
    "NisoAgent",
    "MapEAgent"
]