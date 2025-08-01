#!/usr/bin/env python3
"""
Phoenix Hydra Pod Integration Script
Integra phoenix_hugger.py con el pod Podman existente
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class PodmanIntegrator:
    def __init__(self):
        self.pod_name = "gallant_shannon"  # Tu pod actual
        self.ollama_container = "ollama-phoenix-podified"
        self.models_volume = "phoenix-models"

    def check_pod_status(self) -> Dict:
        """Verifica el estado del pod existente"""
        console.print("🔍 Verificando estado del pod...", style="cyan")

        try:
            # Get pod info
            result = subprocess.run(
                ["podman", "pod", "inspect", self.pod_name],
                capture_output=True,
                text=True,
                check=True,
            )

            pod_info = json.loads(result.stdout)

            # Extract container info
            containers = []
            for container in pod_info.get("Containers", []):
                containers.append(
                    {
                        "name": container["Name"],
                        "state": container["State"],
                        "id": container["Id"][:12],
                    }
                )

            return {
                "pod_name": pod_info["Name"],
                "state": pod_info["State"],
                "containers": containers,
                "port_bindings": pod_info.get("InfraConfig", {}).get(
                    "PortBindings", {}
                ),
            }

        except subprocess.CalledProcessError as e:
            console.print(f"❌ Error verificando pod: {e}", style="red")
            return {}

    def display_pod_status(self, pod_info: Dict):
        """Muestra el estado del pod en una tabla"""
        if not pod_info:
            return

        # Pod summary
        pod_table = Table(
            title=f"🐳 Pod: {pod_info['pod_name']}", header_style="bold blue"
        )
        pod_table.add_column("Propiedad", style="cyan")
        pod_table.add_column("Valor", style="green")

        pod_table.add_row("Estado", pod_info["state"])
        pod_table.add_row("Contenedores", str(len(pod_info["containers"])))

        # Port bindings
        ports = []
        for port, bindings in pod_info.get("port_bindings", {}).items():
            for binding in bindings:
                ports.append(f"{binding['HostPort']}:{port}")
        pod_table.add_row("Puertos", ", ".join(ports) if ports else "Ninguno")

        console.print(pod_table)

        # Containers table
        if pod_info["containers"]:
            containers_table = Table(
                title="📦 Contenedores", header_style="bold magenta"
            )
            containers_table.add_column("Nombre", style="cyan")
            containers_table.add_column("Estado", style="green")
            containers_table.add_column("ID", style="yellow")

            for container in pod_info["containers"]:
                state_style = "green" if container["state"] == "running" else "red"
                containers_table.add_row(
                    container["name"],
                    f"[{state_style}]{container['state']}[/{state_style}]",
                    container["id"],
                )

            console.print(containers_table)

    def check_ollama_connectivity(self) -> bool:
        """Verifica conectividad con Ollama"""
        console.print("🦙 Verificando conectividad Ollama...", style="cyan")

        try:
            # Try direct connection to Ollama
            result = subprocess.run(
                ["podman", "exec", self.ollama_container, "ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                console.print("✅ Ollama accesible en el contenedor", style="green")

                # Parse models
                models = []
                for line in result.stdout.split("\n")[1:]:  # Skip header
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)

                console.print(f"📊 Modelos actuales: {len(models)}", style="blue")
                if models:
                    console.print("Modelos encontrados:", style="dim")
                    for model in models[:5]:  # Show first 5
                        console.print(f"  • {model}", style="dim")
                    if len(models) > 5:
                        console.print(f"  ... y {len(models) - 5} más", style="dim")

                return True
            else:
                console.print("❌ Ollama no responde", style="red")
                return False

        except subprocess.TimeoutExpired:
            console.print("⏰ Timeout conectando a Ollama", style="yellow")
            return False
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Error ejecutando comando: {e}", style="red")
            return False

    def create_volume_if_needed(self) -> bool:
        """Crea volumen para modelos si no existe"""
        console.print("💾 Verificando volumen de modelos...", style="cyan")

        try:
            # Check if volume exists
            result = subprocess.run(
                ["podman", "volume", "inspect", self.models_volume],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.print(f"✅ Volumen {self.models_volume} existe", style="green")
                return True
            else:
                # Create volume
                console.print(
                    f"📁 Creando volumen {self.models_volume}...", style="yellow"
                )
                subprocess.run(
                    ["podman", "volume", "create", self.models_volume], check=True
                )
                console.print(f"✅ Volumen {self.models_volume} creado", style="green")
                return True

        except subprocess.CalledProcessError as e:
            console.print(f"❌ Error con volumen: {e}", style="red")
            return False

    def run_phoenix_hugger_in_pod(self, test_mode: bool = True) -> bool:
        """Ejecuta phoenix_hugger.py dentro del pod"""
        console.print("🚀 Ejecutando Phoenix Hugger en el pod...", style="bold cyan")

        # Prepare command
        cmd = [
            "podman",
            "exec",
            "-it",
            self.ollama_container,
            "python3",
            "-c",
            f"""
import subprocess
import sys

# Install dependencies
subprocess.run([sys.executable, "-m", "pip", "install", "rich", "click", "huggingface_hub", "requests"], check=True)

# Run phoenix_hugger
exec(open('/scripts/phoenix_hugger.py').read())
""",
        ]

        try:
            # Copy script to container first
            console.print("📋 Copiando script al contenedor...", style="yellow")
            subprocess.run(
                [
                    "podman",
                    "cp",
                    "scripts/phoenix_hugger.py",
                    f"{self.ollama_container}:/tmp/phoenix_hugger.py",
                ],
                check=True,
            )

            # Execute in container
            console.print("▶️  Ejecutando en contenedor...", style="yellow")

            env_vars = [
                "-e",
                "PHX_HYDRA_MODELDIR=/models",
                "-e",
                "PHX_HYDRA_WORKERS=2",  # Conservative for container
            ]

            exec_cmd = (
                ["podman", "exec", "-it"]
                + env_vars
                + [
                    self.ollama_container,
                    "python3",
                    "/tmp/phoenix_hugger.py",
                    "--out",
                    "/models",
                    "--workers",
                    "2",
                    "--ollama-host",
                    "localhost:11434",
                ]
            )

            if test_mode:
                exec_cmd.append("--test-mode")

            result = subprocess.run(exec_cmd)

            if result.returncode == 0:
                console.print("✅ Phoenix Hugger ejecutado exitosamente", style="green")
                return True
            else:
                console.print("❌ Phoenix Hugger falló", style="red")
                return False

        except subprocess.CalledProcessError as e:
            console.print(f"❌ Error ejecutando: {e}", style="red")
            return False

    def generate_integration_report(self) -> Dict:
        """Genera reporte de integración"""
        console.print("📊 Generando reporte de integración...", style="cyan")

        pod_info = self.check_pod_status()
        ollama_ok = self.check_ollama_connectivity()

        report = {
            "timestamp": __import__("time").time(),
            "pod_status": pod_info,
            "ollama_accessible": ollama_ok,
            "integration_ready": bool(pod_info and ollama_ok),
            "recommendations": [],
        }

        # Add recommendations
        if not pod_info:
            report["recommendations"].append("Verificar que el pod esté ejecutándose")

        if not ollama_ok:
            report["recommendations"].append("Verificar conectividad con Ollama")
            report["recommendations"].append(
                "Reiniciar contenedor Ollama si es necesario"
            )

        if pod_info and ollama_ok:
            report["recommendations"].append("Sistema listo para descarga de modelos")
            report["recommendations"].append(
                "Ejecutar phoenix_hugger.py en modo test primero"
            )

        return report


def main():
    """Función principal"""
    console.rule("[bold blue]🔗 Phoenix Hydra Pod Integration")

    integrator = PodmanIntegrator()

    # Check pod status
    pod_info = integrator.check_pod_status()
    integrator.display_pod_status(pod_info)

    if not pod_info:
        console.print(
            "\n❌ No se pudo acceder al pod. Verifica que esté ejecutándose.",
            style="red",
        )
        return

    # Check Ollama
    ollama_ok = integrator.check_ollama_connectivity()

    # Create volume
    volume_ok = integrator.create_volume_if_needed()

    # Generate report
    report = integrator.generate_integration_report()

    # Show recommendations
    if report["recommendations"]:
        console.print("\n💡 Recomendaciones:", style="bold yellow")
        for i, rec in enumerate(report["recommendations"], 1):
            console.print(f"  {i}. {rec}", style="yellow")

    # Integration status
    if report["integration_ready"]:
        console.print("\n✅ Sistema listo para integración!", style="bold green")

        # Ask if user wants to run test
        console.print("\n🧪 ¿Ejecutar Phoenix Hugger en modo test?", style="bold cyan")
        console.print(
            "Esto descargará solo algunos modelos para verificar funcionamiento.",
            style="dim",
        )

        response = (
            input("Presiona Enter para continuar o 'n' para salir: ").strip().lower()
        )

        if response != "n":
            success = integrator.run_phoenix_hugger_in_pod(test_mode=True)
            if success:
                console.print(
                    "\n🎉 Integración completada exitosamente!", style="bold green"
                )
                console.print("\nPróximos pasos:", style="bold cyan")
                console.print(
                    "1. Ejecutar sin --test-mode para descarga completa", style="green"
                )
                console.print(
                    "2. Verificar modelos con: podman exec ollama-phoenix-podified ollama list",
                    style="green",
                )
                console.print(
                    "3. Ejecutar: python examples/complete_2025_stack_demo.py",
                    style="green",
                )
    else:
        console.print("\n⚠️  Sistema no listo para integración", style="bold yellow")
        console.print("Revisa las recomendaciones arriba.", style="yellow")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n⏹ Cancelado por usuario", style="yellow")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 Error inesperado: {e}", style="bold red")
        sys.exit(1)
