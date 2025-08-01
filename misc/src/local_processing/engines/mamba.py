from typing import Any, Dict

import torch

from ..model_manager import ModelMetadata
from .base import InferenceEngine

try:
    from mamba_ssm.models.mixer_seq_simple import MambaLMHeadModel
    MAMBA_SSM_AVAILABLE = True
except ImportError:
    MAMBA_SSM_AVAILABLE = False

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class MambaSSMEngine(InferenceEngine):
    """Inference engine for Mamba/SSM models."""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    def can_load(self, metadata: ModelMetadata) -> bool:
        return metadata.model_type in ["mamba", "ssm"]

    async def load_model(self, metadata: ModelMetadata) -> Any:
        """Loads a Mamba/SSM model."""
        if MAMBA_SSM_AVAILABLE and "mamba" in metadata.name.lower():
            return self._load_mamba_ssm_model(metadata)
        elif TRANSFORMERS_AVAILABLE:
            return self._load_huggingface_model(metadata)
        else:
            raise RuntimeError("No compatible Mamba implementation available")

    def _load_mamba_ssm_model(self, metadata: ModelMetadata) -> Any:
        """Loads a model using the mamba-ssm library."""
        self.tokenizer = AutoTokenizer.from_pretrained(metadata.file_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = MambaLMHeadModel.from_pretrained(
            metadata.file_path,
            device=self.device,
            dtype=(
                torch.float16 if self.device.type == "cuda" else torch.float32
            ),
        )
        return self.model

    def _load_huggingface_model(self, metadata: ModelMetadata) -> Any:
        """Loads a model using the Hugging Face transformers library."""
        self.tokenizer = AutoTokenizer.from_pretrained(metadata.file_path)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs = {
            "torch_dtype": (
                torch.float16 if self.device.type == "cuda" else torch.float32
            ),
            "device_map": "auto" if self.device.type == "cuda" else None,
            "trust_remote_code": True,
        }
        self.model = AutoModelForCausalLM.from_pretrained(
            metadata.file_path, **model_kwargs
        )
        if self.device.type == "cpu":
            self.model = self.model.to(self.device)
        return self.model

    async def predict(self, model: Any, data: Any, options: Dict) -> Any:
        """Performs inference on the loaded Mamba/SSM model."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        inputs = self.tokenizer(
            data,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs.input_ids,
                max_new_tokens=options.get("max_new_tokens", 100),
                temperature=options.get("temperature", 0.7),
                top_p=options.get("top_p", 0.9),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        generated_tokens = outputs[0][inputs.input_ids.shape[1]:]
        output_text = self.tokenizer.decode(
            generated_tokens, skip_special_tokens=True
        )
        return output_text