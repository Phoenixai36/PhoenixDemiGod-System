#!/usr/bin/env python3
"""
Phoenix Hydra 2025 Hugging Face Model Downloader
Downloads the complete 2025 model ecosystem from Hugging Face
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

import click
from huggingface_hub import hf_hub_download, login, snapshot_download
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

# 2025 Advanced Model Ecosystem for Hugging Face
HF_MODEL_STACK = {
    "SSM/Mamba Models": [
        "state-spaces/mamba-130m-hf",
        "state-spaces/mamba-370m-hf",
        "state-spaces/mamba-790m-hf",
        "state-spaces/mamba-1.4b-hf",
        "state-spaces/mamba-2.8b-hf",
        "microsoft/DialoGPT-medium",  # For SSM comparison
    ],
    "2025 Flagship Models": [
        "microsoft/DialoGPT-large",
        "microsoft/phi-2",
        "microsoft/phi-1_5",
        "google/gemma-2b",
        "google/gemma-7b",
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-13b-hf",
    ],
    "Specialized Coding Models": [
        "microsoft/CodeBERT-base",
        "microsoft/codebert-base-mlm",
        "microsoft/graphcodebert-base",
        "salesforce/codet5-base",
        "salesforce/codet5-large",
        "bigcode/starcoder",
        "bigcode/starcoderbase",
    ],
    "Local Processing Optimized": [
        "microsoft/DialoGPT-small",
        "distilbert-base-uncased",
        "distilbert-base-cased",
        "distilgpt2",
        "gpt2",
        "google/flan-t5-small",
        "google/flan-t5-base",
    ],
    "Biomimetic Agent Models": [
        "microsoft/DialoGPT-medium",
        "facebook/blenderbot-400M-distill",
        "facebook/blenderbot_small-90M",
        "microsoft/PersonaGPT",
        "PygmalionAI/pygmalion-350m",
        "EleutherAI/gpt-neo-125M",
    ],
    "Energy Efficient Models": [
        "distilbert-base-uncased",
        "google/electra-small-discriminator",
        "google/electra-base-discriminator",
        "microsoft/MiniLM-L12-H384-uncased",
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-MiniLM-L12-v2",
    ],
}


class ModelDownloader:
    def __init__(self, output_dir: str = "/models", max_workers: int = 3):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.results = []

    def download_model(self, model_name: str, category: str) -> Dict:
        """Download a single model from Hugging Face"""
        try:
            console.print(f"⬇️  Downloading {category}: {model_name}", style="yellow")

            # Create category directory
            category_dir = (
                self.output_dir
                / "huggingface"
                / category.lower().replace(" ", "_").replace("/", "_")
            )
            category_dir.mkdir(parents=True, exist_ok=True)

            # Download model
            local_dir = category_dir / model_name.replace("/", "_")

            snapshot_download(
                repo_id=model_name,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
                resume_download=True,
            )

            console.print(f"✅ Successfully downloaded: {model_name}", style="green")
            return {
                "model": model_name,
                "category": category,
                "status": "Success",
                "local_path": str(local_dir),
                "timestamp": time.time(),
            }

        except HfHubHTTPError as e:
            console.print(f"❌ HTTP Error downloading {model_name}: {e}", style="red")
            return {
                "model": model_name,
                "category": category,
                "status": "Failed",
                "error": f"HTTP Error: {e}",
                "timestamp": time.time(),
            }
        except Exception as e:
            console.print(f"❌ Error downloading {model_name}: {e}", style="red")
            return {
                "model": model_name,
                "category": category,
                "status": "Failed",
                "error": str(e),
                "timestamp": time.time(),
            }

    def download_all_models(self, parallel: bool = True) -> List[Dict]:
        """Download all models in the stack"""
        all_models = []
        for category, models in HF_MODEL_STACK.items():
            for model in models:
                all_models.append((model, category))

        console.print(
            f"🎯 Starting download of {len(all_models)} Hugging Face models...",
            style="cyan",
        )

        if parallel:
            console.print(
                f"🔄 Using parallel downloads (max {self.max_workers} concurrent)",
                style="blue",
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Downloading models...", total=len(all_models))

                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_model = {
                        executor.submit(self.download_model, model, category): (
                            model,
                            category,
                        )
                        for model, category in all_models
                    }

                    for future in as_completed(future_to_model):
                        result = future.result()
                        self.results.append(result)
                        progress.advance(task)
        else:
            # Sequential downloads
            for i, (model, category) in enumerate(all_models, 1):
                console.print(f"Progress: {i}/{len(all_models)}", style="blue")
                result = self.download_model(model, category)
                self.results.append(result)

        return self.results

    def generate_report(self) -> Dict:
        """Generate download summary report"""
        successful = len([r for r in self.results if r["status"] == "Success"])
        failed = len([r for r in self.results if r["status"] == "Failed"])
        total = len(self.results)

        report = {
            "timestamp": time.time(),
            "total_models": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "results": self.results,
        }

        # Save report
        report_path = self.output_dir / f"hf_download_report_{int(time.time())}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"\n📄 Detailed report saved to: {report_path}", style="green")
        return report

    def display_summary(self, report: Dict):
        """Display download summary"""
        console.print("\n📊 Hugging Face Download Summary", style="cyan bold")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Models", str(report["total_models"]))
        table.add_row("Successful", str(report["successful"]))
        table.add_row("Failed", str(report["failed"]))
        table.add_row("Success Rate", f"{report['success_rate']:.2f}%")

        console.print(table)

        # Show failed downloads
        failed_models = [r for r in self.results if r["status"] == "Failed"]
        if failed_models:
            console.print("\n❌ Failed Downloads:", style="red bold")
            for result in failed_models:
                console.print(
                    f"  - {result['model']} ({result['category']})", style="red"
                )
                if "error" in result:
                    console.print(f"    Error: {result['error']}", style="dark_red")


@click.command()
@click.option("--output-dir", default="/models", help="Output directory for models")
@click.option("--max-workers", default=3, help="Maximum concurrent downloads")
@click.option(
    "--sequential", is_flag=True, help="Use sequential downloads instead of parallel"
)
@click.option("--hf-token", help="Hugging Face token for private models")
def main(output_dir: str, max_workers: int, sequential: bool, hf_token: Optional[str]):
    """Phoenix Hydra 2025 Hugging Face Model Downloader"""

    console.print("🚀 Phoenix Hydra 2025 HF Model Stack Downloader", style="cyan bold")
    console.print("=" * 50, style="cyan")

    # Login to Hugging Face if token provided
    if hf_token:
        try:
            login(token=hf_token)
            console.print("✅ Logged in to Hugging Face", style="green")
        except Exception as e:
            console.print(f"⚠️  Failed to login to Hugging Face: {e}", style="yellow")

    # Initialize downloader
    downloader = ModelDownloader(output_dir=output_dir, max_workers=max_workers)

    # Download models
    try:
        results = downloader.download_all_models(parallel=not sequential)
        report = downloader.generate_report()
        downloader.display_summary(report)

        console.print("\n🔧 Integration with Phoenix Hydra:", style="cyan bold")
        console.print(
            "Models are now available in the shared volume for local processing!",
            style="green",
        )

    except KeyboardInterrupt:
        console.print("\n⚠️  Download interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}", style="red")


if __name__ == "__main__":
    main()
