"""
SSM Analysis Engine - Non-Transformer Analysis System

This package implements the revolutionary SSM/Mamba-based analysis engines
that replace traditional transformer logic with energy-efficient state-space
processing, integrated with 2025 advanced AI model architectures.

Key Components:
- StateSpaceLayer: Core SSM implementation with selective mechanism
- NonTransformerAnalysisEngine: Main analysis engine
- AdvancedSSMAnalysisEngine: 2025 model integration
- AdvancedGapDetectionSystem: Comprehensive validation system

2025 Model Integration:
- MiniMax M1: Lightning Attention with 75% FLOP reduction
- Kimi K2: Agentic processing with autonomous learning
- Qwen Coder 3: Specialized coding analysis with RL
- GLM-4.5: Unified reasoning capabilities
- FLUX Kontext: Multimodal processing

Usage:
    from src.ssm_analysis import (
        NonTransformerAnalysisEngine,
        AdvancedSSMAnalysisEngine,
        AdvancedGapDetectionSystem,
        SSMAnalysisConfig
    )

    # Create advanced SSM engine
    config = SSMAnalysisConfig(
        d_model=512,
        energy_optimization=True,
        local_processing=True
    )

    engine = AdvancedSSMAnalysisEngine(config)

    # Analyze with model selection
    result = await engine.analyze_with_model_selection(
        data={'metrics': {...}},
        task_type='reasoning'
    )
"""

from .advanced_ssm_components import (
    AdvancedSSMAnalysisEngine,
    AgenticProcessingLayer,
    HybridSSMTransformerLayer,
    LightningAttentionConfig,
    LightningAttentionLayer,
    ModelArchitecture,
    ModelRouter,
    SpecializedCodingLayer,
)
from .gap_detection_system import (
    AdvancedGapDetectionSystem,
    BiomimeticReadinessEvaluator,
    CloudDependencyDetector,
    EnergyEfficiencyAnalyzer,
    GapDetectionResult,
    GapType,
    TransformerResidualDetector,
)
from .state_space_engine import (
    EnergyEfficiencyMonitor,
    NonTransformerAnalysisEngine,
    RecurrentMemoryState,
    SSMAnalysisConfig,
    StateSpaceLayer,
)

__all__ = [
    # Core SSM Engine
    "StateSpaceLayer",
    "NonTransformerAnalysisEngine",
    "SSMAnalysisConfig",
    "EnergyEfficiencyMonitor",
    "RecurrentMemoryState",
    # Advanced 2025 Components
    "AdvancedSSMAnalysisEngine",
    "LightningAttentionLayer",
    "AgenticProcessingLayer",
    "SpecializedCodingLayer",
    "HybridSSMTransformerLayer",
    "ModelArchitecture",
    "ModelRouter",
    "LightningAttentionConfig",
    # Gap Detection System
    "AdvancedGapDetectionSystem",
    "GapDetectionResult",
    "GapType",
    "TransformerResidualDetector",
    "CloudDependencyDetector",
    "EnergyEfficiencyAnalyzer",
    "BiomimeticReadinessEvaluator",
]

__version__ = "2025.1.0"
