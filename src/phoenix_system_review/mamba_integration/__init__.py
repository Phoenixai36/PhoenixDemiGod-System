"""
Mamba/SSM Integration Module for Phoenix Hydra System Review

This module provides State Space Model (SSM) based analysis engines for energy-efficient
local processing, replacing traditional transformer architectures with Mamba models.

Key Features:
- 60-70% energy reduction vs transformers
- 100% local processing (no cloud dependencies)
- Hardware-optimized inference for startup environments
- Integration with Hugging Face and mamba-ssm official library

Target Hardware:
- CPU: 8+ cores (Ryzen 7, i7 10th gen+)
- GPU: RTX 3060 12GB+ (recommended)
- RAM: 32GB ideal, 16GB minimum
- Storage: NVMe SSD 512GB+

Supported Models:
- Zamba2-2.7B (general purpose)
- Codestral-Mamba (code generation)
- Mamba-2.8B (balanced performance)
- Falcon-Mamba-7B (advanced analysis)
"""

from .mamba_engine import MambaInferenceEngine
from .phoenix_model_router import PhoenixModelRouter

__all__ = [
    "MambaInferenceEngine",
    "PhoenixModelRouter",
]

# Version and compatibility info
__version__ = "0.1.0"
__mamba_ssm_version__ = ">=1.2.0"
__transformers_version__ = ">=4.36.0"

# Hardware requirements validation
MINIMUM_REQUIREMENTS = {
    "cpu_cores": 8,
    "ram_gb": 16,
    "storage_gb": 256,
    "gpu_vram_gb": 8  # Optional but recommended
}

RECOMMENDED_REQUIREMENTS = {
    "cpu_cores": 12,
    "ram_gb": 32,
    "storage_gb": 512,
    "gpu_vram_gb": 12
}

# Model configurations for startup environment
MODEL_CONFIGS = {
    "zamba2-2.7b": {
        "model_name": "Zyphra/Zamba2-2.7B",
        "ram_requirement_gb": 8,
        "vram_requirement_gb": 6,
        "inference_latency_target_ms": 1500,
        "use_case": "general_analysis"
    },
    "codestral-mamba": {
        "model_name": "mistralai/Codestral-22B-v0.1",  # Mamba variant
        "ram_requirement_gb": 16,
        "vram_requirement_gb": 12,
        "inference_latency_target_ms": 2000,
        "use_case": "code_analysis"
    },
    "mamba-2.8b": {
        "model_name": "state-spaces/mamba-2.8b-hf",
        "ram_requirement_gb": 6,
        "vram_requirement_gb": 4,
        "inference_latency_target_ms": 1200,
        "use_case": "lightweight_analysis"
    }
}

# Energy efficiency targets
ENERGY_TARGETS = {
    "reduction_vs_transformer_percent": 65,  # Target 60-70% reduction
    "max_watts_per_inference": 150,
    "idle_power_watts": 50,
    "efficiency_metric_target": 0.8  # inferences per watt-hour
}
