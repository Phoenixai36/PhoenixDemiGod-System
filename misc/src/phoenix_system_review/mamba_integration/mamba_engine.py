"""
Mamba Inference Engine for Phoenix Hydra System Review

Provides energy-efficient local inference using State Space Models (SSM) instead of
traditional transformers. Optimized for startup hardware constraints and grant compliance.
"""

import torch
import time
import psutil
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import json

try:
    from mamba_ssm import Mamba
    from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel
    MAMBA_SSM_AVAILABLE = True
except ImportError:
    MAMBA_SSM_AVAILABLE = False
    logging.warning("mamba-ssm not available, falling back to Hugging Face implementation")

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.error("transformers library required but not available")

from .energy_monitor import EnergyEfficiencyMonitor


@dataclass
class InferenceResult:
    """Result of Mamba model inference"""
    output_text: str
    confidence_score: float
    inference_time_ms: float
    energy_consumed_wh: float
    model_used: str
    tokens_generated: int
    tokens_per_second: float
    memory_peak_mb: float


@dataclass
class ModelConfig:
    """Configuration for Mamba model"""
    model_name: str
    model_path: Optional[str] = None
    max_length: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    use_gpu: bool = True
    quantization: Optional[str] = None  # "int8", "int4", None
    batch_size: int = 1


class MambaInferenceEngine:
    """
    Energy-efficient inference engine using Mamba/SSM models for Phoenix Hydra analysis.
    
    Designed for startup environments with hardware constraints and energy efficiency
    requirements for grant proposals (NEOTEC, ENISA).
    """
    
    def __init__(self, config: ModelConfig, energy_monitor: Optional[EnergyEfficiencyMonitor] = None):
        self.config = config
        self.energy_monitor = energy_monitor or EnergyEfficiencyMonitor()
        self.model = None
        self.tokenizer = None
        self.device = self._determine_device()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.inference_history: List[InferenceResult] = []
        self.total_inferences = 0
        self.total_energy_consumed = 0.0
        
        # Initialize model
        self._load_model()
    
    def _determine_device(self) -> torch.device:
        """Determine optimal device based on hardware availability"""
        if self.config.use_gpu and torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            self.logger.info(f"Using GPU: {torch.cuda.get_device_name(0)} ({gpu_memory:.1f}GB)")
        else:
            device = torch.device("cpu")
            cpu_count = psutil.cpu_count()
            ram_gb = psutil.virtual_memory().total / 1e9
            self.logger.info(f"Using CPU: {cpu_count} cores, {ram_gb:.1f}GB RAM")
        
        return device
    
    def _load_model(self):
        """Load Mamba model with fallback strategies"""
        try:
            if MAMBA_SSM_AVAILABLE and "mamba" in self.config.model_name.lower():
                self._load_mamba_ssm_model()
            elif TRANSFORMERS_AVAILABLE:
                self._load_huggingface_model()
            else:
                raise RuntimeError("No compatible Mamba implementation available")
                
        except Exception as e:
            self.logger.error(f"Failed to load model {self.config.model_name}: {e}")
            raise
    
    def _load_mamba_ssm_model(self):
        """Load model using official mamba-ssm library"""
        self.logger.info(f"Loading Mamba model via mamba-ssm: {self.config.model_name}")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load Mamba model
            self.model = MambaLMHeadModel.from_pretrained(
                self.config.model_name,
                device=self.device,
                dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            )
            
            self.logger.info("Mamba-SSM model loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load via mamba-ssm: {e}, falling back to Hugging Face")
            self._load_huggingface_model()
    
    def _load_huggingface_model(self):
        """Load model using Hugging Face transformers with Mamba support"""
        self.logger.info(f"Loading Mamba model via Hugging Face: {self.config.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Model loading options
        model_kwargs = {
            "torch_dtype": torch.float16 if self.device.type == "cuda" else torch.float32,
            "device_map": "auto" if self.device.type == "cuda" else None,
            "trust_remote_code": True
        }
        
        # Add quantization if specified
        if self.config.quantization:
            if self.config.quantization == "int8":
                model_kwargs["load_in_8bit"] = True
            elif self.config.quantization == "int4":
                model_kwargs["load_in_4bit"] = True
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            **model_kwargs
        )
        
        if self.device.type == "cpu":
            self.model = self.model.to(self.device)
        
        self.logger.info("Hugging Face Mamba model loaded successfully")
    
    def infer(self, 
              prompt: str, 
              max_new_tokens: Optional[int] = None,
              temperature: Optional[float] = None,
              top_p: Optional[float] = None) -> InferenceResult:
        """
        Perform inference with energy monitoring and performance tracking
        
        Args:
            prompt: Input text for analysis
            max_new_tokens: Maximum tokens to generate (overrides config)
            temperature: Sampling temperature (overrides config)
            top_p: Top-p sampling parameter (overrides config)
            
        Returns:
            InferenceResult with output and performance metrics
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        # Use provided parameters or fall back to config
        max_new_tokens = max_new_tokens or (self.config.max_length // 2)
        temperature = temperature or self.config.temperature
        top_p = top_p or self.config.top_p
        
        # Start monitoring
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.energy_monitor.start_measurement()
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=self.config.max_length
            ).to(self.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode output
            generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
            output_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Calculate metrics
            end_time = time.time()
            inference_time_ms = (end_time - start_time) * 1000
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_peak_mb = final_memory - initial_memory
            
            energy_consumed = self.energy_monitor.stop_measurement()
            tokens_generated = len(generated_tokens)
            tokens_per_second = tokens_generated / (inference_time_ms / 1000) if inference_time_ms > 0 else 0
            
            # Calculate confidence score (simplified heuristic)
            confidence_score = self._calculate_confidence(outputs, inputs.input_ids.shape[1])
            
            # Create result
            result = InferenceResult(
                output_text=output_text,
                confidence_score=confidence_score,
                inference_time_ms=inference_time_ms,
                energy_consumed_wh=energy_consumed,
                model_used=self.config.model_name,
                tokens_generated=tokens_generated,
                tokens_per_second=tokens_per_second,
                memory_peak_mb=memory_peak_mb
            )
            
            # Track performance
            self.inference_history.append(result)
            self.total_inferences += 1
            self.total_energy_consumed += energy_consumed
            
            self.logger.debug(f"Inference completed: {tokens_generated} tokens in {inference_time_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            self.energy_monitor.stop_measurement()  # Ensure monitoring stops
            self.logger.error(f"Inference failed: {e}")
            raise
    
    def _calculate_confidence(self, outputs: torch.Tensor, input_length: int) -> float:
        """
        Calculate confidence score based on token probabilities
        
        This is a simplified heuristic - in production, you might want more
        sophisticated confidence estimation methods.
        """
        try:
            # Get the generated portion
            generated_portion = outputs[0][input_length:]
            
            # Simple confidence based on sequence length and consistency
            # In a real implementation, you'd use logits or other probability measures
            if len(generated_portion) == 0:
                return 0.0
            
            # Heuristic: longer, more coherent responses get higher confidence
            # This is a placeholder - implement proper confidence scoring
            base_confidence = min(0.9, len(generated_portion) / 50)  # Max 0.9 for 50+ tokens
            
            return max(0.1, base_confidence)  # Minimum 0.1 confidence
            
        except Exception:
            return 0.5  # Default confidence if calculation fails
    
    def batch_infer(self, prompts: List[str], **kwargs) -> List[InferenceResult]:
        """Perform batch inference for multiple prompts"""
        results = []
        
        for prompt in prompts:
            try:
                result = self.infer(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Batch inference failed for prompt: {e}")
                # Create error result
                error_result = InferenceResult(
                    output_text="",
                    confidence_score=0.0,
                    inference_time_ms=0.0,
                    energy_consumed_wh=0.0,
                    model_used=self.config.model_name,
                    tokens_generated=0,
                    tokens_per_second=0.0,
                    memory_peak_mb=0.0
                )
                results.append(error_result)
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.inference_history:
            return {"error": "No inference history available"}
        
        # Calculate averages
        avg_inference_time = sum(r.inference_time_ms for r in self.inference_history) / len(self.inference_history)
        avg_energy = sum(r.energy_consumed_wh for r in self.inference_history) / len(self.inference_history)
        avg_tokens_per_sec = sum(r.tokens_per_second for r in self.inference_history) / len(self.inference_history)
        avg_confidence = sum(r.confidence_score for r in self.inference_history) / len(self.inference_history)
        
        # Energy efficiency metrics
        total_tokens = sum(r.tokens_generated for r in self.inference_history)
        energy_per_token = self.total_energy_consumed / total_tokens if total_tokens > 0 else 0
        
        return {
            "total_inferences": self.total_inferences,
            "total_energy_consumed_wh": self.total_energy_consumed,
            "total_tokens_generated": total_tokens,
            "average_inference_time_ms": avg_inference_time,
            "average_energy_per_inference_wh": avg_energy,
            "average_tokens_per_second": avg_tokens_per_sec,
            "average_confidence_score": avg_confidence,
            "energy_per_token_wh": energy_per_token,
            "model_name": self.config.model_name,
            "device": str(self.device),
            "quantization": self.config.quantization
        }
    
    def save_performance_log(self, filepath: Union[str, Path]):
        """Save performance statistics to file for grant reporting"""
        stats = self.get_performance_stats()
        
        # Add detailed history for analysis
        detailed_log = {
            "summary": stats,
            "detailed_history": [
                {
                    "inference_time_ms": r.inference_time_ms,
                    "energy_consumed_wh": r.energy_consumed_wh,
                    "tokens_generated": r.tokens_generated,
                    "tokens_per_second": r.tokens_per_second,
                    "confidence_score": r.confidence_score,
                    "memory_peak_mb": r.memory_peak_mb
                }
                for r in self.inference_history
            ],
            "hardware_info": {
                "device": str(self.device),
                "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                "cpu_count": psutil.cpu_count(),
                "total_ram_gb": psutil.virtual_memory().total / 1e9
            },
            "model_config": {
                "model_name": self.config.model_name,
                "max_length": self.config.max_length,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "quantization": self.config.quantization
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(detailed_log, f, indent=2)
        
        self.logger.info(f"Performance log saved to {filepath}")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.model, 'cpu'):
            self.model.cpu()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.logger.info("Mamba inference engine cleaned up")