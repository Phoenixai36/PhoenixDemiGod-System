#!/usr/bin/env python3
"""
Phoenix Hydra 2025 • Hugging Face & Ollama Model Fetcher
========================================================
Descarga de forma paralela toda la pila de modelos HF u open-weights
definida en `MODEL_STACK` y, opcionalmente, los modelos locales de Ollama
indicados en `OLLAMA_MODELS`.

• 100% compatible con contenedores Podman / Docker.
• Reanuda descargas interrumpidas (snapshot-download).
• Reporte JSON + tabla resumen en consola Rich.
• Pull automático de modelos Ollama vía CLI (`ollama pull`).
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

###############################################################################
# 1- Configuración                                                             #
###############################################################################
console = Console()

# Phoenix Hydra 2025 Model Stack - Actualizado con modelos flagship
MODEL_STACK: Dict[str, list[str]] = {
    # SSM/Mamba Models - Core energy-efficient architecture
    "ssm_mamba": [
        "state-spaces/mamba-130m-hf",
        "state-spaces/mamba-370m-hf",
        "state-spaces/mamba-790m-hf",
        "state-spaces/mamba-1.4b-hf",
        "state-spaces/mamba-2.8b-hf",
        # Zyphra Zamba models - Hybrid Mamba+Transformer
        "Zyphra/Zamba2-2.7B",
        "Zyphra/Zamba2-1.2B",
        "Zyphra/Zamba-7B-v1",
    ],
    # 2025 Flagship Models - Latest and greatest
    "flagship_2025": [
        "deepseek-ai/DeepSeek-R1",
        "deepseek-ai/DeepSeek-R1-0528",
        "moonshotai/Kimi-K2-Instruct",
        "microsoft/phi-2",
        "microsoft/phi-1_5",
        "google/gemma-2b",
        "google/gemma-7b",
        "meta-llama/Llama-2-7b-hf",
        "meta-llama/Llama-2-13b-hf",
    ],
    # Specialized Coding Models
    "coding_specialists": [
        "bigcode/starcoder",
        "bigcode/starcoderbase",
        "microsoft/CodeBERT-base",
        "microsoft/codebert-base-mlm",
        "microsoft/graphcodebert-base",
        "salesforce/codet5-base",
        "salesforce/codet5-large",
    ],
    # Energy Efficient Models - Optimized for local processing
    "energy_efficient": [
        "google/electra-small-discriminator",
        "google/electra-base-discriminator",
        "sentence-transformers/all-MiniLM-L6-v2",
        "sentence-transformers/all-MiniLM-L12-v2",
        "distilbert-base-uncased",
        "distilbert-base-cased",
        "distilgpt2",
    ],
    # Biomimetic Agent Models - For RUBIK system
    "biomimetic_agents": [
        "microsoft/DialoGPT-medium",
        "microsoft/DialoGPT-large",
        "facebook/blenderbot-400M-distill",
        "facebook/blenderbot_small-90M",
        "microsoft/PersonaGPT",
        "EleutherAI/gpt-neo-125M",
    ],
    # FLUX Models - For multimedia processing
    "flux_multimedia": [
        "black-forest-labs/FLUX.1-dev",
        "black-forest-labs/FLUX.1-schnell",
        "black-forest-labs/FLUX.1-Kontext-dev",
    ],
}

# Modelos Ollama 2025 - Optimizados para Phoenix Hydra
OLLAMA_MODELS = [
    # Core 2025 models
    "qwen2.5-coder:7b",
    "qwen2.5-coder:14b",
    "qwen2.5-coder:32b",
    "deepseek-coder-v2:16b",
    "phi3:mini",
    "phi3:medium",
    "gemma2:2b",
    "gemma2:9b",
    "llama3.2:1b",
    "llama3.2:3b",
    # Energy efficient models
    "tinyllama:1.1b",
    "stablelm2:1.6b",
    "openchat:7b",
    # Specialized models
    "codestral:22b",
    "neural-chat:7b",
    "orca-mini:3b",
    "vicuna:7b",
]

PARALLEL_WORKERS = int(os.environ.get("PHX_HYDRA_WORKERS", 4))
DEFAULT_OUT_DIR = Path(os.environ.get("PHX_HYDRA_MODELDIR", "/models")).expanduser()


###############################################################################
# 2- Descargador Hugging Face                                                  #
###############################################################################
class HFDownloader:
    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[Dict] = []

    def _dl_single(self, repo_id: str, tag: str) -> Dict:
        console.print(f"⬇️  Descargando {tag}: {repo_id}", style="yellow")

        try:
            local_dir = (
                self.out_dir
                / "huggingface"
                / tag.replace(" ", "_")
                / repo_id.replace("/", "_")
            )

            # Create directory structure
            local_dir.mkdir(parents=True, exist_ok=True)

            snapshot_download(
                repo_id=repo_id,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
                resume_download=True,
                ignore_patterns=["*.bin"]
                if "large" in repo_id.lower()
                else None,  # Skip large bins for some models
            )

            console.print(f"✅ Completado: {repo_id}", style="green")
            status, err = "Success", ""

        except HfHubHTTPError as e:
            console.print(f"❌ HTTP Error {repo_id}: {e}", style="red")
            status, err = "HTTP-Error", str(e)
        except Exception as e:
            console.print(f"❌ Error {repo_id}: {e}", style="red")
            status, err = "Error", str(e)

        result = {
            "repo": repo_id,
            "group": tag,
            "status": status,
            "error": err,
            "path": str(local_dir) if "local_dir" in locals() else "",
            "timestamp": time.time(),
        }
        self.results.append(result)
        return result

    def download(self, parallel: bool, workers: int) -> list[Dict]:
        jobs = [(repo, grp) for grp, lst in MODEL_STACK.items() for repo in lst]
        console.print(
            f"🎯 Total modelos HF a descargar: {len(jobs)}", style="bold cyan"
        )

        if parallel:
            console.print(f"🔄 Descarga paralela con {workers} workers", style="blue")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as prog:
                task = prog.add_task("Descargando modelos HF…", total=len(jobs))
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futs = {pool.submit(self._dl_single, r, g): (r, g) for r, g in jobs}
                    for fut in as_completed(futs):
                        prog.advance(task)
        else:
            console.print("📥 Descarga secuencial", style="blue")
            for i, (r, g) in enumerate(jobs, 1):
                console.print(f"Progreso: {i}/{len(jobs)}", style="dim")
                self._dl_single(r, g)

        return self.results

    def report(self) -> Path:
        ok, ko = (
            len([r for r in self.results if r["status"] == "Success"]),
            len([r for r in self.results if r["status"] != "Success"]),
        )
        rpt = {
            "phoenix_hydra_version": "2025",
            "timestamp": time.time(),
            "total": len(self.results),
            "successful": ok,
            "failed": ko,
            "success_rate": 0
            if not self.results
            else round(ok / len(self.results) * 100, 2),
            "models_by_category": self._categorize_results(),
            "items": self.results,
        }

        out = self.out_dir / f"hf_report_{int(time.time())}.json"
        out.write_text(json.dumps(rpt, indent=2))
        self._table(rpt)
        console.print(f"\n📄 Reporte HF guardado en {out}", style="green")
        return out

    def _categorize_results(self) -> Dict:
        categories = {}
        for result in self.results:
            category = result["group"]
            if category not in categories:
                categories[category] = {"total": 0, "successful": 0, "failed": 0}
            categories[category]["total"] += 1
            if result["status"] == "Success":
                categories[category]["successful"] += 1
            else:
                categories[category]["failed"] += 1
        return categories

    @staticmethod
    def _table(rpt: Dict):
        t = Table(title="📊 Resumen Hugging Face", header_style="bold magenta")
        t.add_column("Métrica", style="cyan")
        t.add_column("Valor", style="green")

        t.add_row("Total Modelos", str(rpt["total"]))
        t.add_row("Descargados", str(rpt["successful"]))
        t.add_row("Fallidos", str(rpt["failed"]))
        t.add_row("Tasa de Éxito", f'{rpt["success_rate"]}%')

        console.print(t)

        # Show category breakdown
        if rpt.get("models_by_category"):
            console.print("\n📋 Por Categoría:", style="bold blue")
            cat_table = Table(header_style="bold blue")
            cat_table.add_column("Categoría", style="cyan")
            cat_table.add_column("Total", style="white")
            cat_table.add_column("Exitosos", style="green")
            cat_table.add_column("Fallidos", style="red")

            for cat, stats in rpt["models_by_category"].items():
                cat_table.add_row(
                    cat.replace("_", " ").title(),
                    str(stats["total"]),
                    str(stats["successful"]),
                    str(stats["failed"]),
                )
            console.print(cat_table)

        if rpt["failed"]:
            console.print("\n❌ Modelos fallidos:", style="bold red")
            for item in rpt["items"]:
                if item["status"] != "Success":
                    console.print(
                        f" • {item['repo']} → {item['error'][:100]}...", style="red"
                    )


###############################################################################
# 3- Pull de modelos Ollama                                                   #
###############################################################################
def pull_ollama_models(models: list[str], ollama_host: str = "localhost:11434"):
    """Intenta ejecutar `ollama pull` para cada modelo."""
    if not shutil.which("ollama"):
        console.print(
            "⚠️  Ollama CLI no encontrado, intentando conexión directa...",
            style="yellow",
        )
        return _pull_ollama_api(models, ollama_host)

    console.rule("[bold blue]🦙 Pull Ollama Models")
    console.print(f"🎯 Total modelos Ollama: {len(models)}", style="bold cyan")

    results = []
    for i, model in enumerate(models, 1):
        console.print(f"⬇️  [{i}/{len(models)}] ollama pull {model}", style="cyan")
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                check=True,
                text=True,
                capture_output=True,
                timeout=300,  # 5 minute timeout per model
            )
            console.print(f"✅ Completado: {model}", style="green")
            results.append(
                {"model": model, "status": "Success", "output": result.stdout}
            )

        except subprocess.TimeoutExpired:
            console.print(f"⏰ Timeout: {model}", style="yellow")
            results.append(
                {"model": model, "status": "Timeout", "error": "Download timeout"}
            )

        except subprocess.CalledProcessError as e:
            console.print(f"❌ Falló {model}: {e}", style="red")
            results.append({"model": model, "status": "Failed", "error": str(e)})

    # Generate Ollama report
    _generate_ollama_report(results)
    return results


def _pull_ollama_api(models: list[str], host: str):
    """Fallback to API calls if CLI not available"""
    import requests

    console.print(f"🌐 Intentando conexión API a {host}", style="blue")
    results = []

    for model in models:
        try:
            response = requests.post(
                f"http://{host}/api/pull", json={"name": model}, timeout=300
            )
            if response.status_code == 200:
                console.print(f"✅ API Pull exitoso: {model}", style="green")
                results.append({"model": model, "status": "Success", "method": "API"})
            else:
                console.print(
                    f"❌ API Pull falló {model}: {response.status_code}", style="red"
                )
                results.append(
                    {
                        "model": model,
                        "status": "Failed",
                        "error": f"HTTP {response.status_code}",
                    }
                )

        except requests.RequestException as e:
            console.print(f"❌ Error conexión {model}: {e}", style="red")
            results.append({"model": model, "status": "Failed", "error": str(e)})

    _generate_ollama_report(results)
    return results


def _generate_ollama_report(results: list[Dict]):
    """Generate Ollama download report"""
    successful = len([r for r in results if r["status"] == "Success"])
    failed = len([r for r in results if r["status"] != "Success"])

    table = Table(title="🦙 Resumen Ollama", header_style="bold blue")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Total Modelos", str(len(results)))
    table.add_row("Descargados", str(successful))
    table.add_row("Fallidos", str(failed))
    table.add_row(
        "Tasa de Éxito", f"{(successful/len(results)*100):.1f}%" if results else "0%"
    )

    console.print(table)

    if failed > 0:
        console.print("\n❌ Modelos Ollama fallidos:", style="bold red")
        for result in results:
            if result["status"] != "Success":
                console.print(
                    f" • {result['model']} → {result.get('error', 'Unknown error')}",
                    style="red",
                )


###############################################################################
# 4- CLI                                                                      #
###############################################################################
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
def cli(
    out: str,
    workers: int,
    serial: bool,
    hf_token: Optional[str],
    skip_ollama: bool,
    skip_hf: bool,
    ollama_host: str,
    test_mode: bool,
):
    """Phoenix Hydra 2025 Model Fetcher CLI."""

    out_dir = Path(out).expanduser()
    console.rule("[bold blue]🚀 Phoenix Hydra Model Fetcher 2025")

    # Show configuration
    config_table = Table(title="⚙️  Configuración", header_style="bold magenta")
    config_table.add_column("Parámetro", style="cyan")
    config_table.add_column("Valor", style="green")

    config_table.add_row("Directorio salida", str(out_dir))
    config_table.add_row("Workers paralelos", str(workers))
    config_table.add_row("Modo", "Secuencial" if serial else "Paralelo")
    config_table.add_row("Ollama host", ollama_host)
    config_table.add_row("Modo test", "Sí" if test_mode else "No")

    console.print(config_table)

    # Test mode - limit models
    if test_mode:
        console.print("🧪 Modo test activado - limitando modelos", style="yellow")
        global MODEL_STACK, OLLAMA_MODELS
        MODEL_STACK = {k: v[:2] for k, v in MODEL_STACK.items()}
        OLLAMA_MODELS = OLLAMA_MODELS[:5]

    # HF authentication
    if hf_token and not skip_hf:
        try:
            login(token=hf_token)
            console.print("✅ Login Hugging Face OK", style="green")
        except Exception as e:
            console.print(f"⚠️  Login HF fallido: {e}", style="yellow")

    start_time = time.time()

    # HF download
    if not skip_hf:
        console.print("\n🤗 Iniciando descarga Hugging Face...", style="bold blue")
        hf = HFDownloader(out_dir)
        hf.download(parallel=not serial, workers=workers)
        hf_report = hf.report()
    else:
        console.print("⏭️  Saltando descarga Hugging Face", style="yellow")

    # Ollama pull
    if not skip_ollama:
        console.print("\n🦙 Iniciando descarga Ollama...", style="bold blue")
        ollama_results = pull_ollama_models(OLLAMA_MODELS, ollama_host)
    else:
        console.print("⏭️  Saltando descarga Ollama", style="yellow")

    total_time = time.time() - start_time

    # Final summary
    console.rule("[bold green]🎉 Resumen Final")

    summary_table = Table(title="📊 Resumen Total", header_style="bold green")
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")

    summary_table.add_row("Tiempo total", f"{total_time:.1f} segundos")
    summary_table.add_row("Directorio modelos", str(out_dir))

    if not skip_hf:
        hf_success = len([r for r in hf.results if r["status"] == "Success"])
        summary_table.add_row("Modelos HF exitosos", str(hf_success))

    if not skip_ollama:
        ollama_success = len([r for r in ollama_results if r["status"] == "Success"])
        summary_table.add_row("Modelos Ollama exitosos", str(ollama_success))

    console.print(summary_table)

    # Integration instructions
    console.print("\n🔧 Integración con Phoenix Hydra:", style="bold cyan")
    console.print("1. Modelos listos para montar en Podman 🐳", style="green")
    console.print(
        "2. Ejecutar: python examples/complete_2025_stack_demo.py", style="green"
    )
    console.print(
        "3. Verificar: python src/ssm_analysis/advanced_gap_detection.py", style="green"
    )

    console.rule("[bold green]✅ Completado")


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n⏹ Cancelado por usuario", style="yellow")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 Error inesperado: {e}", style="bold red")
        sys.exit(1)
