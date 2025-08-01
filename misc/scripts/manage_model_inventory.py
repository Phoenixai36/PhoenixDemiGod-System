#!/usr/bin/env python3
"""
Phoenix Hydra Model Inventory Manager
Manages and tracks all downloaded models from Ollama and Hugging Face
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class ModelInventoryManager:
    def __init__(
        self,
        ollama_models_path: str = "/ollama-models",
        hf_cache_path: str = "/hf-cache",
        output_path: str = "/models",
    ):
        self.ollama_models_path = Path(ollama_models_path)
        self.hf_cache_path = Path(hf_cache_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.inventory = {
            "timestamp": time.time(),
            "ollama_models": [],
            "huggingface_models": [],
            "total_size": 0,
            "model_count": 0,
        }

    def scan_ollama_models(self) -> List[Dict]:
        """Scan Ollama models directory"""
        console.print("🔍 Scanning Ollama models...", style="yellow")

        ollama_models = []

        try:
            # Try to connect to Ollama API
            response = requests.get(
                "http://ollama-downloader:11434/api/tags", timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                for model in data.get("models", []):
                    ollama_models.append(
                        {
                            "name": model["name"],
                            "size": model.get("size", 0),
                            "modified": model.get("modified_at", ""),
                            "digest": model.get("digest", ""),
                            "source": "ollama_api",
                        }
                    )
            else:
                console.print(
                    "⚠️  Ollama API not accessible, scanning filesystem", style="yellow"
                )
                raise requests.RequestException()

        except requests.RequestException:
            # Fallback to filesystem scan
            if self.ollama_models_path.exists():
                for model_dir in self.ollama_models_path.rglob("*"):
                    if model_dir.is_file() and model_dir.suffix in [
                        ".bin",
                        ".gguf",
                        ".safetensors",
                    ]:
                        stat = model_dir.stat()
                        ollama_models.append(
                            {
                                "name": model_dir.stem,
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                                "path": str(model_dir),
                                "source": "filesystem",
                            }
                        )

        console.print(f"✅ Found {len(ollama_models)} Ollama models", style="green")
        return ollama_models

    def scan_huggingface_models(self) -> List[Dict]:
        """Scan Hugging Face models directory"""
        console.print("🔍 Scanning Hugging Face models...", style="yellow")

        hf_models = []

        # Scan HF cache directory
        if self.hf_cache_path.exists():
            hub_path = self.hf_cache_path / "hub"
            if hub_path.exists():
                for model_dir in hub_path.iterdir():
                    if model_dir.is_dir() and model_dir.name.startswith("models--"):
                        model_name = model_dir.name.replace("models--", "").replace(
                            "--", "/"
                        )

                        # Calculate total size
                        total_size = 0
                        file_count = 0
                        for file_path in model_dir.rglob("*"):
                            if file_path.is_file():
                                total_size += file_path.stat().st_size
                                file_count += 1

                        hf_models.append(
                            {
                                "name": model_name,
                                "size": total_size,
                                "file_count": file_count,
                                "path": str(model_dir),
                                "modified": model_dir.stat().st_mtime,
                                "source": "huggingface_hub",
                            }
                        )

        # Also scan direct downloads
        hf_direct_path = self.output_path / "huggingface"
        if hf_direct_path.exists():
            for category_dir in hf_direct_path.iterdir():
                if category_dir.is_dir():
                    for model_dir in category_dir.iterdir():
                        if model_dir.is_dir():
                            total_size = 0
                            file_count = 0
                            for file_path in model_dir.rglob("*"):
                                if file_path.is_file():
                                    total_size += file_path.stat().st_size
                                    file_count += 1

                            hf_models.append(
                                {
                                    "name": model_dir.name.replace("_", "/"),
                                    "category": category_dir.name,
                                    "size": total_size,
                                    "file_count": file_count,
                                    "path": str(model_dir),
                                    "modified": model_dir.stat().st_mtime,
                                    "source": "direct_download",
                                }
                            )

        console.print(f"✅ Found {len(hf_models)} Hugging Face models", style="green")
        return hf_models

    def generate_inventory(self) -> Dict:
        """Generate complete model inventory"""
        console.print("📋 Generating model inventory...", style="cyan")

        # Scan both sources
        ollama_models = self.scan_ollama_models()
        hf_models = self.scan_huggingface_models()

        # Calculate totals
        total_size = sum(m.get("size", 0) for m in ollama_models + hf_models)
        model_count = len(ollama_models) + len(hf_models)

        self.inventory.update(
            {
                "timestamp": time.time(),
                "ollama_models": ollama_models,
                "huggingface_models": hf_models,
                "total_size": total_size,
                "model_count": model_count,
                "ollama_count": len(ollama_models),
                "hf_count": len(hf_models),
            }
        )

        return self.inventory

    def save_inventory(self, format: str = "json") -> Path:
        """Save inventory to file"""
        timestamp = int(time.time())

        if format == "json":
            file_path = self.output_path / f"model_inventory_{timestamp}.json"
            with open(file_path, "w") as f:
                json.dump(self.inventory, f, indent=2)
        elif format == "yaml":
            file_path = self.output_path / f"model_inventory_{timestamp}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(self.inventory, f, default_flow_style=False)

        console.print(f"💾 Inventory saved to: {file_path}", style="green")
        return file_path

    def display_summary(self):
        """Display inventory summary"""
        console.print("\n📊 Phoenix Hydra Model Inventory", style="cyan bold")

        # Summary table
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Models", str(self.inventory["model_count"]))
        summary_table.add_row("Ollama Models", str(self.inventory["ollama_count"]))
        summary_table.add_row("Hugging Face Models", str(self.inventory["hf_count"]))
        summary_table.add_row(
            "Total Size", self.format_size(self.inventory["total_size"])
        )

        console.print(summary_table)

        # Ollama models table
        if self.inventory["ollama_models"]:
            console.print("\n🦙 Ollama Models", style="blue bold")
            ollama_table = Table(show_header=True, header_style="bold blue")
            ollama_table.add_column("Model Name", style="cyan")
            ollama_table.add_column("Size", style="green")
            ollama_table.add_column("Source", style="yellow")

            for model in self.inventory["ollama_models"][:10]:  # Show first 10
                ollama_table.add_row(
                    model["name"],
                    self.format_size(model.get("size", 0)),
                    model.get("source", "unknown"),
                )

            console.print(ollama_table)

            if len(self.inventory["ollama_models"]) > 10:
                console.print(
                    f"... and {len(self.inventory['ollama_models']) - 10} more",
                    style="dim",
                )

        # Hugging Face models table
        if self.inventory["huggingface_models"]:
            console.print("\n🤗 Hugging Face Models", style="blue bold")
            hf_table = Table(show_header=True, header_style="bold blue")
            hf_table.add_column("Model Name", style="cyan")
            hf_table.add_column("Size", style="green")
            hf_table.add_column("Files", style="yellow")
            hf_table.add_column("Source", style="magenta")

            for model in self.inventory["huggingface_models"][:10]:  # Show first 10
                hf_table.add_row(
                    model["name"],
                    self.format_size(model.get("size", 0)),
                    str(model.get("file_count", 0)),
                    model.get("source", "unknown"),
                )

            console.print(hf_table)

            if len(self.inventory["huggingface_models"]) > 10:
                console.print(
                    f"... and {len(self.inventory['huggingface_models']) - 10} more",
                    style="dim",
                )

    def format_size(self, size_bytes: int) -> str:
        """Format size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def generate_phoenix_config(self) -> Dict:
        """Generate Phoenix Hydra configuration for available models"""
        config = {
            "phoenix_hydra": {
                "model_stack": {
                    "ollama_models": [
                        m["name"] for m in self.inventory["ollama_models"]
                    ],
                    "huggingface_models": [
                        m["name"] for m in self.inventory["huggingface_models"]
                    ],
                    "local_processing": {
                        "enabled": True,
                        "fallback_strategy": "local_only",
                        "energy_efficient": True,
                    },
                    "ssm_models": [
                        m["name"]
                        for m in self.inventory["huggingface_models"]
                        if "mamba" in m["name"].lower() or "ssm" in m["name"].lower()
                    ],
                    "biomimetic_agents": {
                        "rubik_genome": True,
                        "available_models": [
                            m["name"]
                            for m in self.inventory["ollama_models"]
                            + self.inventory["huggingface_models"]
                            if any(
                                keyword in m["name"].lower()
                                for keyword in ["chat", "dialog", "persona", "neural"]
                            )
                        ],
                    },
                }
            }
        }

        # Save Phoenix config
        config_path = self.output_path / "phoenix_model_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        console.print(f"⚙️  Phoenix Hydra config saved to: {config_path}", style="green")
        return config


def main():
    """Main function"""
    console.print("🚀 Phoenix Hydra Model Inventory Manager", style="cyan bold")
    console.print("=" * 50, style="cyan")

    # Initialize manager
    manager = ModelInventoryManager()

    try:
        # Generate inventory
        inventory = manager.generate_inventory()

        # Display summary
        manager.display_summary()

        # Save inventory
        manager.save_inventory("json")
        manager.save_inventory("yaml")

        # Generate Phoenix config
        manager.generate_phoenix_config()

        console.print("\n🎉 Model inventory complete!", style="green bold")
        console.print("Ready for Phoenix Hydra local processing!", style="cyan")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


if __name__ == "__main__":
    main()
