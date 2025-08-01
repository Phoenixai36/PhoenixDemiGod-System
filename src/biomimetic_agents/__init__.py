"""
RUBIK Biomimetic Agent System

This package implements the revolutionary self-evolving biomimetic agent system
with 20-base logarithmic matrix genetics, mood engines, and cross-generational learning.

Key Components:
- RUBIKGenome: 20-base logarithmic matrix genetic system
- BiomimeticAgent: Self-evolving agents with mood and archetype systems
- ThanatosController: Agent lifecycle management with death/rebirth cycles
- CrossGenerationalLearningSystem: Knowledge inheritance across generations

Integration with 2025 Advanced AI Models:
- MiniMax M1: Ultra-long context reasoning with Lightning Attention
- Kimi K2: Agentic capabilities with ultra-low costs
- FLUX Kontext: Contextual image generation and editing
- GLM-4.5: Unified reasoning and coding capabilities
- Qwen Coder 3: Advanced programming with massive context

Usage:
    from src.biomimetic_agents import (
        RUBIKGenome, BiomimeticAgent, ThanatosController,
        CrossGenerationalLearningSystem, create_rubik_ecosystem
    )

    # Create complete RUBIK ecosystem
    ecosystem = await create_rubik_ecosystem()

    # Submit task to ecosystem
    result = await ecosystem.process_task({
        'task_type': 'system_analysis',
        'input_data': 'Analyze Phoenix Hydra architecture'
    })
"""

from .agent_system import (
    AgentMemory,
    AgentPerformanceMetrics,
    AgentStatus,
    BiomimeticAgent,
)
from .cross_generational_learning import (
    CrossGenerationalLearningSystem,
    KnowledgeBase,
    KnowledgeFragment,
    LearningExperience,
)
from .rubik_genome import (
    Archetype,
    GeneExpression,
    GeneticBase,
    GenomePool,
    MoodState,
    RUBIKGenome,
)
from .thanatos_controller import LifecycleEvent, LifecycleRecord, ThanatosController

__all__ = [
    # Genetic System
    "RUBIKGenome",
    "GenomePool",
    "GeneExpression",
    "GeneticBase",
    "Archetype",
    "MoodState",
    # Agent System
    "BiomimeticAgent",
    "AgentStatus",
    "AgentMemory",
    "AgentPerformanceMetrics",
    # Lifecycle Management
    "ThanatosController",
    "LifecycleEvent",
    "LifecycleRecord",
    # Learning System
    "CrossGenerationalLearningSystem",
    "KnowledgeBase",
    "KnowledgeFragment",
    "LearningExperience",
    # Ecosystem Creation
    "create_rubik_ecosystem",
    "RUBIKEcosystem",
]

# Import ecosystem after other imports to avoid circular dependencies
from .ecosystem import RUBIKEcosystem, create_rubik_ecosystem

__version__ = "1.0.0"
