#!/usr/bin/env python3
"""
Phoenix Hydra Model Manager
Comprehensive local model management system for Phoenix Hydra ecosystem
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Model type enumeration"""
    REASONING = "reasoning"
    CODING = "coding"
    GENERAL = "general"
    CREATIVE = "creative"
    VISION = "vision"
    AUDIO = "audio"
    CONTEXT_LONG = "context_long"
    CPU_OPTIMIZED = "cpu_optimized"
    SSM = "ssm"
    BIOMIMETIC = "biomimetic"

class ModelStatus(Enum):
    """Model status enumeration"""
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

@dataclass
class ModelConfig:
    """Model configuration dataclass"""
    name: str
    type: ModelType
    primary: bool = False
    fallback: Optional[str] = None
    local_path: Optional[str] = None
    ollama_name: Optional[str] = None
    huggingface_name: Optional[str] = None
    parameters: Dict[str, Any] = None
    requirements: List[str] = None
    energy_efficient: bool = True
    rootless_compatible: bool = True
    memory_requirement_mb: int = 1024
    cpu_threads: int = 4
    gpu_required: bool = False
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.requirements is None:
            self.requirements = []

@dataclass
class ModelInstance:
    """Model instance with runtime information"""
    config: ModelConfig
    status: ModelStatus = ModelStatus.NOT_DOWNLOADED
    loaded_at: Optional[datetime] = None
    memory_usage_mb: int = 0
    cpu_usage_percent: float = 0.0
    error_message: Optional[str] = None
    model_object: Any = None

class PhoenixModelManager:
    """
    Phoenix Hydra Model Manager
    Manages local AI models with energy-efficient SSM architecture
    """
    
    def __init__(self, models_dir: str = "models", config_path: str = "config/models.yaml"):
        self.models_dir = Path(models_dir)
        self.config_path = Path(config_path)
        self.models: Dict[str, ModelInstance] = {}
        self.active_models: Dict[ModelType, str] = {}
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize model configurations
        self._initialize_model_configs()
        
        logger.info(f"Phoenix Model Manager initialized with {len(self.models)} models")
    
    def _initialize_model_configs(self):
        """Initialize model configurations based on Phoenix Hydra requirements"""
        
        # Phoenix Hydra 2025 Model Stack Configuration
        model_configs = [
            # Reasoning Models (Primary: Zyphra Zamba2-2.7B)
            ModelConfig(
                name="zamba2-2.7b",
                type=ModelType.REASONING,
                primary=True,
                ollama_name="zamba2:2.7b",
                huggingface_name="Zyphra/Zamba2-2.7B",
                parameters={"max_tokens": 8192, "temperature": 0.7},
                memory_requirement_mb=3072,
                energy_efficient=True
            ),
            ModelConfig(
                name="llama3-8b",
                type=ModelType.REASONING,
                fallback="zamba2-2.7b",
                ollama_name="llama3:8b",
                huggingface_name="meta-llama/Llama-3-8B",
                parameters={"max_tokens": 4096, "temperature": 0.7},
                memory_requirement_mb=8192
            ),
            ModelConfig(
                name="falcon-7b",
                type=ModelType.REASONING,
                ollama_name="falcon:7b",
                huggingface_name="tiiuae/falcon-7b",
                parameters={"max_tokens": 2048, "temperature": 0.7},
                memory_requirement_mb=7168
            ),
            
            # Coding Models (Primary: DeepSeek-Coder-v2, Codestral-Mamba-7B)
            ModelConfig(
                name="deepseek-coder-v2",
                type=ModelType.CODING,
                primary=True,
                ollama_name="deepseek-coder:6.7b",
                huggingface_name="deepseek-ai/deepseek-coder-6.7b-base",
                parameters={"max_tokens": 4096, "temperature": 0.1},
                memory_requirement_mb=7168,
                energy_efficient=True
            ),
            ModelConfig(
                name="codestral-mamba-7b",
                type=ModelType.CODING,
                primary=True,
                ollama_name="codestral:7b",
                huggingface_name="mistralai/Codestral-22B-v0.1",
                parameters={"max_tokens": 8192, "temperature": 0.1},
                memory_requirement_mb=7168,
                energy_efficient=True
            ),
            ModelConfig(
                name="qwen2.5-coder-7b",
                type=ModelType.CODING,
                fallback="deepseek-coder-v2",
                ollama_name="qwen2.5-coder:7b",
                huggingface_name="Qwen/Qwen2.5-Coder-7B",
                parameters={"max_tokens": 4096, "temperature": 0.1},
                memory_requirement_mb=7168
            ),
            
            # General LLM Models
            ModelConfig(
                name="llama3.2",
                type=ModelType.GENERAL,
                primary=True,
                ollama_name="llama3.2:3b",
                huggingface_name="meta-llama/Llama-3.2-3B",
                parameters={"max_tokens": 4096, "temperature": 0.8},
                memory_requirement_mb=3072
            ),
            ModelConfig(
                name="falcon-mamba-7b",
                type=ModelType.GENERAL,
                ollama_name="falcon:7b",
                huggingface_name="tiiuae/falcon-mamba-7b",
                parameters={"max_tokens": 4096, "temperature": 0.8},
                memory_requirement_mb=7168,
                energy_efficient=True
            ),
            
            # Creative/Multimodal Models
            ModelConfig(
                name="phi-3-14b",
                type=ModelType.CREATIVE,
                primary=True,
                ollama_name="phi3:14b",
                huggingface_name="microsoft/Phi-3-medium-14b",
                parameters={"max_tokens": 4096, "temperature": 0.9},
                memory_requirement_mb=14336
            ),
            
            # Vision Models
            ModelConfig(
                name="clip",
                type=ModelType.VISION,
                primary=True,
                huggingface_name="openai/clip-vit-base-patch32",
                parameters={"image_size": 224},
                memory_requirement_mb=1024,
                energy_efficient=True
            ),
            ModelConfig(
                name="yolov11",
                type=ModelType.VISION,
                huggingface_name="ultralytics/yolov8n",
                parameters={"confidence": 0.5, "iou": 0.45},
                memory_requirement_mb=512,
                energy_efficient=True
            ),
            
            # Audio/TTS Models
            ModelConfig(
                name="chatterbox",
                type=ModelType.AUDIO,
                primary=True,
                huggingface_name="microsoft/speecht5_tts",
                parameters={"sample_rate": 16000},
                memory_requirement_mb=512,
                energy_efficient=True
            ),
            ModelConfig(
                name="vits",
                type=ModelType.AUDIO,
                huggingface_name="facebook/mms-tts-eng",
                parameters={"sample_rate": 22050},
                memory_requirement_mb=256,
                energy_efficient=True
            ),
            
            # Context Long/RAG Models
            ModelConfig(
                name="minimax-m1",
                type=ModelType.CONTEXT_LONG,
                primary=True,
                ollama_name="minimax:m1",
                parameters={"max_tokens": 80000, "temperature": 0.7},
                memory_requirement_mb=16384
            ),
            
            # CPU/License Alternatives
            ModelConfig(
                name="rwkv-7b",
                type=ModelType.CPU_OPTIMIZED,
                primary=True,
                huggingface_name="BlinkDL/rwkv-4-world-7b",
                parameters={"max_tokens": 4096, "temperature": 0.7},
                memory_requirement_mb=7168,
                cpu_threads=8,
                energy_efficient=True
            ),
            
            # SSM Models (Phoenix Hydra Specialty)
            ModelConfig(
                name="mamba-codestral-7b",
                type=ModelType.SSM,
                primary=True,
                huggingface_name="state-spaces/mamba-codestral-7b",
                parameters={"d_model": 256, "d_state": 32, "conv_width": 4},
                memory_requirement_mb=7168,
                energy_efficient=True
            ),
            
            # Biomimetic Agent Models
            ModelConfig(
                name="rubik-agent-base",
                type=ModelType.BIOMIMETIC,
                primary=True,
                local_path="models/biomimetic/rubik-agent-base",
                parameters={"population_size": 50, "evolution_interval": 300},
                memory_requirement_mb=2048,
                energy_efficient=True
            )
        ]
        
        # Initialize model instances
        for config in model_configs:
            self.models[config.name] = ModelInstance(config=config)
        
        # Set primary models as active
        for model_name, instance in self.models.items():
            if instance.config.primary:
                self.active_models[instance.config.type] = model_name
        
        # Save configuration
        self._save_config()
    
    def _save_config(self):
        """Save model configuration to YAML file"""
        config_data = {
            "models": {
                name: {
                    "config": asdict(instance.config),
                    "status": instance.status.value
                }
                for name, instance in self.models.items()
            },
            "active_models": {
                model_type.value: model_name 
                for model_type, model_name in self.active_models.items()
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    def load_config(self):
        """Load model configuration from YAML file"""
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load models
            for name, data in config_data.get("models", {}).items():
                config_dict = data["config"]
                config_dict["type"] = ModelType(config_dict["type"])
                config = ModelConfig(**config_dict)
                
                instance = ModelInstance(
                    config=config,
                    status=ModelStatus(data["status"])
                )
                self.models[name] = instance
            
            # Load active models
            for model_type_str, model_name in config_data.get("active_models", {}).items():
                model_type = ModelType(model_type_str)
                self.active_models[model_type] = model_name
                
            logger.info(f"Loaded configuration for {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    async def download_model(self, model_name: str) -> bool:
        """Download a specific model"""
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found in configuration")
            return False
        
        instance = self.models[model_name]
        config = instance.config
        
        try:
            instance.status = ModelStatus.DOWNLOADING
            logger.info(f"Downloading model: {model_name}")
            
            # Download via Ollama if available
            if config.ollama_name:
                process = await asyncio.create_subprocess_exec(
                    "ollama", "pull", config.ollama_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    instance.status = ModelStatus.DOWNLOADED
                    logger.info(f"Successfully downloaded {model_name} via Ollama")
                    self._save_config()
                    return True
                else:
                    logger.error(f"Ollama download failed: {stderr.decode()}")
            
            # Download via Hugging Face if Ollama failed
            if config.huggingface_name:
                try:
                    from transformers import AutoModel, AutoTokenizer
                    
                    model_path = self.models_dir / model_name
                    model_path.mkdir(parents=True, exist_ok=True)
                    
                    # Download model and tokenizer
                    model = AutoModel.from_pretrained(
                        config.huggingface_name,
                        cache_dir=str(model_path),
                        torch_dtype=torch.float16 if config.energy_efficient else torch.float32
                    )
                    tokenizer = AutoTokenizer.from_pretrained(
                        config.huggingface_name,
                        cache_dir=str(model_path)
                    )
                    
                    # Save locally
                    model.save_pretrained(str(model_path))
                    tokenizer.save_pretrained(str(model_path))
                    
                    config.local_path = str(model_path)
                    instance.status = ModelStatus.DOWNLOADED
                    logger.info(f"Successfully downloaded {model_name} via Hugging Face")
                    self._save_config()
                    return True
                    
                except ImportError:
                    logger.error("transformers library not installed for Hugging Face downloads")
                except Exception as e:
                    logger.error(f"Hugging Face download failed: {e}")
            
            instance.status = ModelStatus.ERROR
            instance.error_message = "No valid download method available"
            return False
            
        except Exception as e:
            instance.status = ModelStatus.ERROR
            instance.error_message = str(e)
            logger.error(f"Error downloading {model_name}: {e}")
            return False
    
    async def load_model(self, model_name: str) -> bool:
        """Load a model into memory"""
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found")
            return False
        
        instance = self.models[model_name]
        
        if instance.status != ModelStatus.DOWNLOADED:
            logger.error(f"Model {model_name} not downloaded")
            return False
        
        try:
            instance.status = ModelStatus.LOADING
            logger.info(f"Loading model: {model_name}")
            
            config = instance.config
            
            # Load based on model type
            if config.type == ModelType.SSM:
                # Load SSM model (custom implementation)
                from .ssm_analysis_engine import SSMAnalysisConfig, SSMAnalysisEngine
                
                ssm_config = SSMAnalysisConfig(
                    d_model=config.parameters.get("d_model", 256),
                    d_state=config.parameters.get("d_state", 32),
                    conv_width=config.parameters.get("conv_width", 4)
                )
                instance.model_object = SSMAnalysisEngine(ssm_config)
                
            elif config.type == ModelType.VISION:
                # Load vision model
                if "clip" in model_name.lower():
                    from transformers import CLIPModel, CLIPProcessor
                    instance.model_object = {
                        "model": CLIPModel.from_pretrained(config.huggingface_name),
                        "processor": CLIPProcessor.from_pretrained(config.huggingface_name)
                    }
                elif "yolo" in model_name.lower():
                    try:
                        from ultralytics import YOLO
                        instance.model_object = YOLO(config.huggingface_name)
                    except ImportError:
                        logger.error("ultralytics not installed for YOLO models")
                        return False
            
            elif config.type == ModelType.AUDIO:
                # Load audio/TTS model
                from transformers import AutoModel, AutoProcessor
                instance.model_object = {
                    "model": AutoModel.from_pretrained(config.huggingface_name),
                    "processor": AutoProcessor.from_pretrained(config.huggingface_name)
                }
            
            elif config.type == ModelType.BIOMIMETIC:
                # Load biomimetic agent model (custom implementation)
                from ..agents.rubik_agent_service import RubikAgentEcosystem
                instance.model_object = RubikAgentEcosystem(config.parameters)
            
            else:
                # Load standard language model
                if config.local_path and Path(config.local_path).exists():
                    from transformers import AutoModel, AutoTokenizer
                    instance.model_object = {
                        "model": AutoModel.from_pretrained(config.local_path),
                        "tokenizer": AutoTokenizer.from_pretrained(config.local_path)
                    }
                elif config.ollama_name:
                    # For Ollama models, we'll use the API
                    instance.model_object = {"ollama_name": config.ollama_name}
            
            instance.status = ModelStatus.LOADED
            instance.loaded_at = datetime.now()
            logger.info(f"Successfully loaded model: {model_name}")
            self._save_config()
            return True
            
        except Exception as e:
            instance.status = ModelStatus.ERROR
            instance.error_message = str(e)
            logger.error(f"Error loading {model_name}: {e}")
            return False
    
    def get_active_model(self, model_type: ModelType) -> Optional[str]:
        """Get the currently active model for a given type"""
        return self.active_models.get(model_type)
    
    def set_active_model(self, model_type: ModelType, model_name: str) -> bool:
        """Set the active model for a given type"""
        if model_name not in self.models:
            logger.error(f"Model {model_name} not found")
            return False
        
        if self.models[model_name].config.type != model_type:
            logger.error(f"Model {model_name} is not of type {model_type}")
            return False
        
        self.active_models[model_type] = model_name
        self._save_config()
        logger.info(f"Set active {model_type.value} model to {model_name}")
        return True
    
    def get_model_status(self, model_name: str) -> Optional[ModelStatus]:
        """Get the status of a specific model"""
        if model_name not in self.models:
            return None
        return self.models[model_name].status
    
    def list_models(self, model_type: Optional[ModelType] = None) -> List[Dict[str, Any]]:
        """List all models or models of a specific type"""
        models = []
        for name, instance in self.models.items():
            if model_type is None or instance.config.type == model_type:
                models.append({
                    "name": name,
                    "type": instance.config.type.value,
                    "status": instance.status.value,
                    "primary": instance.config.primary,
                    "memory_mb": instance.config.memory_requirement_mb,
                    "energy_efficient": instance.config.energy_efficient,
                    "loaded_at": instance.loaded_at.isoformat() if instance.loaded_at else None
                })
        return models
    
    async def download_all_models(self, parallel: bool = True, max_concurrent: int = 3) -> Dict[str, bool]:
        """Download all configured models"""
        results = {}
        
        if parallel:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_with_semaphore(model_name: str):
                async with semaphore:
                    return await self.download_model(model_name)
            
            tasks = [
                download_with_semaphore(name) 
                for name in self.models.keys()
                if self.models[name].status == ModelStatus.NOT_DOWNLOADED
            ]
            
            if tasks:
                results_list = await asyncio.gather(*tasks, return_exceptions=True)
                for i, (name, result) in enumerate(zip(self.models.keys(), results_list)):
                    if isinstance(result, Exception):
                        results[name] = False
                        logger.error(f"Error downloading {name}: {result}")
                    else:
                        results[name] = result
        else:
            for name in self.models.keys():
                if self.models[name].status == ModelStatus.NOT_DOWNLOADED:
                    results[name] = await self.download_model(name)
        
        return results
    
    def get_system_requirements(self) -> Dict[str, Any]:
        """Get system requirements for all models"""
        total_memory = sum(
            instance.config.memory_requirement_mb 
            for instance in self.models.values()
            if instance.status in [ModelStatus.LOADED, ModelStatus.LOADING]
        )
        
        max_cpu_threads = max(
            instance.config.cpu_threads 
            for instance in self.models.values()
        )
        
        gpu_required = any(
            instance.config.gpu_required 
            for instance in self.models.values()
            if instance.status in [ModelStatus.LOADED, ModelStatus.LOADING]
        )
        
        return {
            "total_memory_mb": total_memory,
            "max_cpu_threads": max_cpu_threads,
            "gpu_required": gpu_required,
            "loaded_models": len([
                instance for instance in self.models.values()
                if instance.status == ModelStatus.LOADED
            ])
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all loaded models"""
        health_status = {
            "overall_healthy": True,
            "models": {},
            "system_resources": self.get_system_requirements(),
            "timestamp": datetime.now().isoformat()
        }
        
        for name, instance in self.models.items():
            if instance.status == ModelStatus.LOADED:
                try:
                    # Basic health check - verify model object exists
                    model_healthy = instance.model_object is not None
                    
                    health_status["models"][name] = {
                        "healthy": model_healthy,
                        "status": instance.status.value,
                        "memory_usage_mb": instance.memory_usage_mb,
                        "loaded_at": instance.loaded_at.isoformat() if instance.loaded_at else None,
                        "error": instance.error_message
                    }
                    
                    if not model_healthy:
                        health_status["overall_healthy"] = False
                        
                except Exception as e:
                    health_status["models"][name] = {
                        "healthy": False,
                        "error": str(e)
                    }
                    health_status["overall_healthy"] = False
        
        return health_status

# Global model manager instance
model_manager = PhoenixModelManager()

# Convenience functions
async def download_all_models(**kwargs):
    """Download all models"""
    return await model_manager.download_all_models(**kwargs)

async def load_model(model_name: str):
    """Load a specific model"""
    return await model_manager.load_model(model_name)

def get_active_model(model_type: ModelType):
    """Get active model for type"""
    return model_manager.get_active_model(model_type)

def list_models(model_type: Optional[ModelType] = None):
    """List all models"""
    return model_manager.list_models(model_type)

async def health_check():
    """Perform system health check"""
    return await model_manager.health_check()