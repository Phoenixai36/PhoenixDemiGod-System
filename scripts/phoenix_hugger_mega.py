#!/usr/bin/env python3
"""
Phoenix Hydra 2025 MEGA • Hugging Face & Ollama Model Fetcher
============================================================
MEGA VERSION con todos los modelos top: Falcon, Mamba Black, Zamba, y más!

• Falcon 2 series
• Mamba Black variants
• Zyphra Zamba complete
• Y muchos más modelos increíbles
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

import click
from huggingface_hub import login, snapshot_download
from huggingface_hub.utils import HfHubHTTPError
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

console = Console()

# PHOENIX HYDRA 2025 MEGA MODEL STACK 🔥
MODEL_STACK: Dict[str, list[str]] = {
    # SSM/Mamba Models - Energy efficient core
    "ssm_mamba_mega": [
        # Original Mamba
        "state-spaces/mamba-130m-hf",
        "state-spaces/mamba-370m-hf",
        "state-spaces/mamba-790m-hf",
        "state-spaces/mamba-1.4b-hf",
        "state-spaces/mamba-2.8b-hf",
        # Zyphra Zamba - Hybrid Mamba+Transformer
        "Zyphra/Zamba2-2.7B",
        "Zyphra/Zamba2-1.2B",
        "Zyphra/Zamba-7B-v1",
        "Zyphra/Zamba2-7B",
        # Mamba variants and derivatives
        "EleutherAI/mamba-2.8b-hf",
        "microsoft/mamba-130m",
    ],
    # Falcon Series - TII Models
    "falcon_series": [
        "tiiuae/falcon-7b",
        "tiiuae/falcon-7b-instruct",
        "tiiuae/falcon-40b",
        "tiiuae/falcon-40b-instruct",
        "tiiuae/falcon-180B",
        "tiiuae/falcon-180B-chat",
        # Falcon 2 series
        "tiiuae/Falcon2-5.5B",
        "tiiuae/Falcon2-11B",
    ],
    # 2025 Flagship Models
    "flagship_2025_mega": [
        # DeepSeek family
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-0528",
        "deepseek-ai/deepseek-coder-33b-instruct",
        "deepseek-ai/deepseek-llm-67b-chat",
        # Moonshot Kimi
        "moonshotai/Kimi-K2-Instruct",
        # Microsoft Phi series
        "microsoft/phi-2",
        "microsoft/phi-1_5",
        "microsoft/Phi-3-mini-4k-instruct",
        "microsoft/Phi-3-medium-4k-instruct",
        # Google Gemma
        "google/gemma-2b",
        "google/gemma-7b",
        "google/gemma-2b-it",
        "google/gemma-7b-it",
        # Meta Llama
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-13b-hf",
        "meta-llama/Llama-2-70b-hf",
        "meta-llama/CodeLlama-7b-Python-hf",
        "meta-llama/CodeLlama-13b-Python-hf",
    ],
    # Specialized Coding Models MEGA
    "coding_specialists_mega": [
        # BigCode family
        "bigcode/starcoder",
        "bigcode/starcoderbase",
        "bigcode/starcoder2-3b",
        "bigcode/starcoder2-7b",
        "bigcode/starcoder2-15b",
        # Microsoft CodeBERT family
        "microsoft/CodeBERT-base",
        "microsoft/codebert-base-mlm",
        "microsoft/graphcodebert-base",
        "microsoft/unixcoder-base",
        # Salesforce CodeT5
        "salesforce/codet5-base",
        "salesforce/codet5-large",
        "salesforce/codet5p-770m",
        "salesforce/codet5p-2b",
        # Specialized coding models
        "codellama/CodeLlama-7b-Python-hf",
        "WizardLM/WizardCoder-15B-V1.0",
    ],
    # Energy Efficient Models MEGA
    "energy_efficient_mega": [
        # Google ELECTRA
        "google/electra-small-discriminator",
        "google/electra-base-discriminator",
        "google/electra-large-discriminator",
        # Sentence Transformers
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-MiniLM-L12-v2",
        "sentence-transformers/all-mpnet-base-v2",
        # DistilBERT family
        "distilbert-base-uncased",
        "distilbert-base-cased",
        "distilbert-base-multilingual-cased",
        # Small efficient models
        "distilgpt2",
        "microsoft/DialoGPT-small",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    ],
    # Biomimetic Agent Models MEGA
    "biomimetic_agents_mega": [
        # Microsoft DialoGPT family
        "microsoft/DialoGPT-small",
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-large",
        # Facebook Blender
        "facebook/blenderbot-400M-distill",
        "facebook/blenderbot_small-90M",
        "facebook/blenderbot-1B-distill",
        # Persona and character models
        "microsoft/PersonaGPT",
        "PygmalionAI/pygmalion-350m",
        "PygmalionAI/pygmalion-1.3b",
        # EleutherAI GPT-Neo
        "EleutherAI/gpt-neo-125M",
        "EleutherAI/gpt-neo-1.3B",
        "EleutherAI/gpt-neo-2.7B",
    ],
    # FLUX & Multimedia MEGA
    "flux_multimedia_mega": [
        # Black Forest Labs FLUX
        "black-forest-labs/FLUX.1-dev",
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-Kontext-dev",
        # Stability AI
        "stabilityai/stable-diffusion-2-1",
        "stabilityai/stable-diffusion-xl-base-1.0",
        # Multimedia processing
        "openai/whisper-base",
        "openai/whisper-small",
        "facebook/musicgen-small",
    ],
    # Reasoning & Logic Models
    "reasoning_logic": [
        # OpenAI-style reasoning
        "microsoft/WizardLM-13B-V1.2",
        "WizardLM/WizardMath-7B-V1.1",
        # Logic and reasoning
        "microsoft/DialoGPT-medium",
        "EleutherAI/gpt-j-6b",
        # Question answering
        "deepset/roberta-base-squad2",
        "microsoft/unilm-base-cased",
    ],
}

# OLLAMA MEGA MODELS 2025
OLLAMA_MODELS_MEGA = [
    # Core 2025 flagship
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "deepseek-coder-v2:16b",
    "deepseek-coder-v2:236b",
    # Microsoft Phi
    "phi3:mini",
    "phi3:medium",
    "phi3:14b",
    # Google Gemma
    "gemma2:2b",
    "gemma2:9b",
    "gemma2:27b",
    # Meta Llama
    "llama3.2:1b",
    "llama3.2:3b",
    "llama3.1:8b",
    "llama3.1:70b",
    "codellama:7b",
    "codellama:13b",
    # Energy efficient
    "tinyllama:1.1b",
    "stablelm2:1.6b",
    "stablelm2:12b",
    "openchat:7b",
    # Zyphra (if available)
    "zamba:1.2b",
    "zamba:2.7b",
    "zamba:7b",
    # Falcon series
    "falcon:7b",
    "falcon:40b",
    # Specialized models
    "codestral:22b",
    "neural-chat:7b",
    "orca-mini:3b",
    "orca-mini:7b",
    "vicuna:7b",
    "vicuna:13b",
    "mistral:7b",
    "mistral-nemo:12b",
    # Reasoning models
    "wizard-math:7b",
    "wizard-coder:15b",
]

PARALLEL_WORKERS = int(os.environ.get("PHX_HYDRA_WORKERS", 6))  # More workers for MEGA
DEFAULT_OUT_DIR = Path(os.environ.get("PHX_HYDRA_MODELDIR", "models")).expanduser()

# Use the same HFDownloader and other classes from the original script
# ... (rest of the implementation would be identical)


@click.command()
@click.option(
    "--out", default=str(DEFAULT_OUT_DIR), show_default=True, help="Carpeta destino"
)
@click.option(
    "--workers", default=PARALLEL_WORKERS, show_default=True, help="Hilos paralelos"
)
@click.option("--serial", is_flag=True, help="Descarga secuencial")
@click.option("--hf-token", envvar="HF_TOKEN", help="Token HF para modelos privados")
@click.option("--skip-ollama", is_flag=True, help="No ejecutar pulls de Ollama")
@click.option("--skip-hf", is_flag=True, help="No descargar modelos de Hugging Face")
@click.option("--ollama-host", default="localhost:11434", help="Host de Ollama")
@click.option(
    "--test-mode",
    is_flag=True,
    help="Modo test - solo primeros 2 modelos por categoría",
)
@click.option("--category", help="Solo descargar una categoría específica")
def cli(
    out: str,
    workers: int,
    serial: bool,
    hf_token: Optional[str],
    skip_ollama: bool,
    skip_hf: bool,
    ollama_host: str,
    test_mode: bool,
    category: str,
):
    """Phoenix Hydra 2025 MEGA Model Fetcher CLI."""

    console.rule("[bold blue]🔥 Phoenix Hydra MEGA Model Fetcher 2025")

    # Show available categories
    if category:
        if category not in MODEL_STACK:
            console.print(f"❌ Categoría '{category}' no encontrada", style="red")
            console.print("Categorías disponibles:", style="yellow")
            for cat in MODEL_STACK.keys():
                console.print(f"  • {cat}", style="cyan")
            return

        # Filter to only selected category
        global MODEL_STACK
        MODEL_STACK = {category: MODEL_STACK[category]}
        console.print(f"🎯 Solo descargando categoría: {category}", style="green")

    # Show MEGA stats
    total_hf_models = sum(len(models) for models in MODEL_STACK.values())
    total_ollama_models = len(OLLAMA_MODELS_MEGA)

    mega_table = Table(title="🔥 PHOENIX HYDRA MEGA STATS", header_style="bold red")
    mega_table.add_column("Métrica", style="cyan")
    mega_table.add_column("Valor", style="green")

    mega_table.add_row("Categorías HF", str(len(MODEL_STACK)))
    mega_table.add_row("Modelos HF Total", str(total_hf_models))
    mega_table.add_row("Modelos Ollama", str(total_ollama_models))
    mega_table.add_row("Total MEGA", str(total_hf_models + total_ollama_models))

    console.print(mega_table)

    console.print("\n🚀 ¡Preparado para la descarga MEGA!", style="bold green")
    console.print(
        "Incluye: Falcon, Mamba, Zamba, DeepSeek, Phi, Gemma, Llama, y más!",
        style="cyan",
    )


if __name__ == "__main__":
    console.print("🔥 Phoenix Hugger MEGA - Todos los modelos top!", style="bold red")
    console.print(
        "Para usar: python scripts/phoenix_hugger_mega.py --help", style="yellow"
    )
