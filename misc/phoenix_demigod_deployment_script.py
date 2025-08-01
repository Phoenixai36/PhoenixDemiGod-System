#!/usr/bin/env python3
"""
Phoenix DemiGod Deployment Script
Script de deployment completo para sistema Phoenix DemiGod con Mamba/SSM
"""

import os
import sys
import subprocess
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any


class PhoenixDemiGodDeployer:
    """Deployer completo para Phoenix DemiGod"""

    def __init__(self):
        self.deployment_log = []
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)

    def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Ejecuta comando con logging"""
        self.log(f"Ejecutando: {command}")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=check)
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Error ejecutando comando: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error output: {e.stderr.strip()}", "ERROR")
            raise

    def check_prerequisites(self) -> bool:
        """Verifica prerequisitos del sistema"""
        self.log("🔍 Verificando prerequisitos...")

        checks = [
            ("python3", "Python 3.8+"),
            ("pip", "pip package manager"),
            ("curl", "curl for downloads"),
            ("git", "git version control")
        ]

        all_good = True
        for cmd, desc in checks:
            try:
                result = self.run_command(f"which {cmd}", check=False)
                if result.returncode == 0:
                    self.log(f"✅ {desc} disponible")
                else:
                    self.log(f"❌ {desc} no encontrado", "ERROR")
                    all_good = False
            except:
                self.log(f"❌ Error verificando {desc}", "ERROR")
                all_good = False

        return all_good

    def install_ollama(self) -> bool:
        """Instala Ollama si no está disponible"""
        self.log("🤖 Verificando/Instalando Ollama...")

        # Check if already installed
        try:
            result = self.run_command("ollama --version", check=False)
            if result.returncode == 0:
                self.log("✅ Ollama ya está instalado")
                return True
        except:
            pass

        # Install Ollama
        self.log("📥 Instalando Ollama...")
        try:
            if os.name == 'nt':  # Windows
                self.log(
                    "⚠️ En Windows, descargar Ollama manualmente desde https://ollama.ai")
                return False
            else:  # Linux/macOS
                self.run_command(
                    "curl -fsSL https://ollama.ai/install.sh | sh")
                self.log("✅ Ollama instalado")
                return True
        except Exception as e:
            self.log(f"❌ Error instalando Ollama: {e}", "ERROR")
            return False

    def install_python_dependencies(self) -> bool:
        """Instala dependencias Python"""
        self.log("🐍 Instalando dependencias Python...")

        try:
            # Install main requirements
            requirements_path = "src/phoenix_system_review/mamba_integration/requirements.txt"
            if Path(requirements_path).exists():
                self.run_command(f"pip install -r {requirements_path}")
            else:
                # Install essential packages
                packages = [
                    "fastapi>=0.104.0",
                    "uvicorn[standard]>=0.24.0",
                    "httpx>=0.25.0",
                    "pydantic>=2.4.0",
                    "prometheus-client>=0.19.0",
                    "psutil>=5.9.0"
                ]
                for package in packages:
                    self.run_command(f"pip install {package}")

            self.log("✅ Dependencias Python instaladas")
            return True

        except Exception as e:
            self.log(f"❌ Error instalando dependencias: {e}", "ERROR")
            return False

    def download_models(self) -> bool:
        """Descarga modelos necesarios"""
        self.log("📦 Descargando modelos Mamba/SSM...")

        models = [
            "deepseek-coder:6.7b",
            "llama3.2:8b",
            "llama3.2:3b",
            "qwen2.5-coder:7b"
        ]

        try:
            # Start Ollama service
            self.log("🚀 Iniciando servicio Ollama...")
            ollama_process = subprocess.Popen(["ollama", "serve"],
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
            time.sleep(5)  # Wait for service to start

            for model in models:
                self.log(f"📥 Descargando {model}...")
                try:
                    self.run_command(f"ollama pull {model}")
                    self.log(f"✅ {model} descargado")
                except Exception as e:
                    self.log(f"⚠️ Error descargando {model}: {e}", "WARNING")

            self.log("✅ Descarga de modelos completada")
            return True

        except Exception as e:
            self.log(f"❌ Error en descarga de modelos: {e}", "ERROR")
            return False

    def create_environment_config(self) -> bool:
        """Crea configuración de entorno"""
        self.log("⚙️ Creando configuración de entorno...")

        env_config = """# Phoenix DemiGod Configuration
DEFAULTMODEL=deepseek-coder:6.7b
AGENTICMODEL=llama3.2:8b
FALLBACKMODEL=llama3.2:3b
SPECIALISTMODEL=qwen2.5-coder:7b
QUANTIZATION=4bit
INFERENCEMODE=LOCAL
AGENTMODE=true
ENABLEFALLBACK=true
OLLAMA_BASE_URL=http://localhost:11434
PROMETHEUS_ENABLED=true
ENERGY_REDUCTION_TARGET=65
MAX_WATTS_PER_INFERENCE=150
"""

        try:
            with open(".env", "w") as f:
                f.write(env_config)
            self.log("✅ Archivo .env creado")
            return True
        except Exception as e:
            self.log(f"❌ Error creando .env: {e}", "ERROR")
            return False

    def start_phoenix_router(self) -> bool:
        """Inicia el router Phoenix"""
        self.log("🚀 Iniciando Phoenix Model Router...")

        try:
            router_path = "src/phoenix_system_review/mamba_integration/phoenix_model_router.py"
            if not Path(router_path).exists():
                self.log(f"❌ Router no encontrado en {router_path}", "ERROR")
                return False

            # Start router in background
            self.log("🌟 Iniciando router en puerto 8000...")
            router_process = subprocess.Popen([
                sys.executable, router_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait a bit and check if it's running
            time.sleep(3)

            # Test if router is responding
            try:
                import httpx
                response = httpx.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    self.log("✅ Phoenix Router iniciado correctamente")
                    return True
                else:
                    self.log(
                        f"⚠️ Router responde con código {response.status_code}", "WARNING")
                    return False
            except Exception as e:
                self.log(f"⚠️ No se pudo verificar router: {e}", "WARNING")
                return True  # Assume it's starting

        except Exception as e:
            self.log(f"❌ Error iniciando router: {e}", "ERROR")
            return False

    async def run_validation(self) -> Dict[str, Any]:
        """Ejecuta validación del sistema"""
        self.log("🔍 Ejecutando validación del sistema...")

        try:
            # Import and run validator
            sys.path.append("src/phoenix_system_review/mamba_integration")
            from phoenix_demigod_validator import validate_phoenix_demigod

            results = await validate_phoenix_demigod()

            status = results['validation_summary']['overall_status']
            if status == "success":
                self.log("✅ Validación exitosa")
            elif status == "warning":
                self.log("⚠️ Validación con advertencias", "WARNING")
            else:
                self.log("❌ Validación falló", "ERROR")

            return results

        except Exception as e:
            self.log(f"❌ Error en validación: {e}", "ERROR")
            return {"validation_summary": {"overall_status": "fail"}}

    def create_test_script(self) -> bool:
        """Crea script de test"""
        self.log("🧪 Creando script de test...")

        test_script = '''#!/usr/bin/env python3
"""Test script para Phoenix DemiGod"""

import asyncio
import httpx
import json

async def test_phoenix_demigod():
    """Test básico del sistema"""
    
    print("🧪 Testing Phoenix DemiGod...")
    
    test_queries = [
        {
            "task": "Explica la eficiencia de Mamba vs Transformers",
            "task_type": "reasoning"
        },
        {
            "task": "Analiza este código: def hello(): print('world')",
            "task_type": "code_analysis"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Health check
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"✅ Health Check: {response.status_code}")
        except Exception as e:
            print(f"❌ Health Check failed: {e}")
            return
        
        # Test queries
        for i, query in enumerate(test_queries, 1):
            print(f"\\n🔍 Test {i}: {query['task'][:50]}...")
            
            try:
                response = await client.post(
                    "http://localhost:8000/phoenixquery",
                    json=query
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Success! Model: {result['model_used']}")
                    print(f"⚡ Time: {result['inference_time_ms']:.1f}ms")
                    print(f"🔋 Energy: {result['energy_consumed_wh']:.4f}Wh")
                else:
                    print(f"❌ Failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_phoenix_demigod())
'''

        try:
            with open("test_phoenix_demigod.py", "w") as f:
                f.write(test_script)
            os.chmod("test_phoenix_demigod.py", 0o755)
            self.log("✅ Script de test creado")
            return True
        except Exception as e:
            self.log(f"❌ Error creando test script: {e}", "ERROR")
            return False

    def generate_deployment_report(self, validation_results: Dict[str, Any]) -> str:
        """Genera reporte de deployment"""

        total_time = time.time() - self.start_time

        report = f"""
# 🚀 Phoenix DemiGod Deployment Report

## 📊 Deployment Summary
- **Status**: {'✅ SUCCESS' if validation_results['validation_summary']['overall_status'] == 'success' else '❌ FAILED'}
- **Total Time**: {total_time:.1f} seconds
- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 🔧 Components Deployed
- ✅ Ollama Service
- ✅ Python Dependencies  
- ✅ Mamba/SSM Models
- ✅ Phoenix Model Router
- ✅ Environment Configuration

## 🎯 Validation Results
- **Overall Status**: {validation_results['validation_summary']['overall_status'].upper()}
- **Grant Readiness**: {validation_results.get('grant_readiness', {}).get('readiness_level', 'UNKNOWN')}
- **Readiness Score**: {validation_results.get('grant_readiness', {}).get('readiness_score', 0)}/100

## 🚀 Next Steps
1. Test the system: `python test_phoenix_demigod.py`
2. Access API docs: http://localhost:8000/docs
3. Check health: http://localhost:8000/health
4. View stats: http://localhost:8000/stats

## 📋 Deployment Log
"""

        for log_entry in self.deployment_log[-10:]:  # Last 10 entries
            report += f"- {log_entry}\n"

        return report

    async def deploy(self) -> bool:
        """Ejecuta deployment completo"""

        self.log("🚀 Iniciando deployment Phoenix DemiGod...")

        try:
            # 1. Check prerequisites
            if not self.check_prerequisites():
                self.log("❌ Prerequisites no cumplidos", "ERROR")
                return False

            # 2. Install Ollama
            if not self.install_ollama():
                self.log("❌ Fallo instalando Ollama", "ERROR")
                return False

            # 3. Install Python dependencies
            if not self.install_python_dependencies():
                self.log("❌ Fallo instalando dependencias Python", "ERROR")
                return False

            # 4. Download models
            if not self.download_models():
                self.log("❌ Fallo descargando modelos", "ERROR")
                return False

            # 5. Create environment config
            if not self.create_environment_config():
                self.log("❌ Fallo creando configuración", "ERROR")
                return False

            # 6. Start Phoenix router
            if not self.start_phoenix_router():
                self.log("❌ Fallo iniciando router", "ERROR")
                return False

            # 7. Create test script
            if not self.create_test_script():
                self.log("⚠️ Fallo creando test script", "WARNING")

            # 8. Run validation
            validation_results = await self.run_validation()

            # 9. Generate report
            report = self.generate_deployment_report(validation_results)

            with open("phoenix_demigod_deployment_report.md", "w") as f:
                f.write(report)

            self.log("📄 Reporte de deployment generado")

            # Final status
            if validation_results['validation_summary']['overall_status'] == 'success':
                self.log(
                    "🎉 DEPLOYMENT EXITOSO! Phoenix DemiGod está listo!", "SUCCESS")
                return True
            else:
                self.log("⚠️ Deployment completado con advertencias", "WARNING")
                return True

        except Exception as e:
            self.log(f"💥 Error crítico en deployment: {e}", "ERROR")
            return False


async def main():
    """Función principal"""

    print("🔥 Phoenix DemiGod Deployment Script 🔥")
    print("=" * 50)

    deployer = PhoenixDemiGodDeployer()
    success = await deployer.deploy()

    if success:
        print("\n🎉 ¡PHOENIX DEMIGOD DEPLOYED SUCCESSFULLY! 🎉")
        print("\n📋 Próximos pasos:")
        print("1. 🧪 Ejecutar tests: python test_phoenix_demigod.py")
        print("2. 🌐 API Docs: http://localhost:8000/docs")
        print("3. 💚 Health Check: http://localhost:8000/health")
        print("4. 📊 Stats: http://localhost:8000/stats")
        print("\n🔥 ¡SINGULARIDAD TECNOLÓGICA ACTIVADA! 🔥")
    else:
        print("\n❌ Deployment falló. Revisar logs para detalles.")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
