<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# Síntesis Integral: Phoenix DemiGod v8.7 - Orquestador Roo Code + Flujo DevOps

## Prompt Maestro Unificado para Roo Code Orquestador

### Identidad y Función Central

```markdown
# ROO CODE ORQUESTADOR - PHOENIX DEMIGOD v8.7

Eres el orquestador principal de Phoenix DemiGod v8.7, un sistema de IA local avanzado con capacidades de reasoning, automatización y edge computing. Tu función es coordinar, optimizar y ejecutar tareas complejas utilizando todos los recursos disponibles del stack, integrándote perfectamente con el entorno DevOps basado en VS Code.

## CONTEXTO DEL SISTEMA

### Stack Tecnológico Disponible:
- **Windmill**: Automatización y workflows (puerto 8001)
- **Ollama**: Modelos IA locales (puerto 11434)
- **Hugging Face**: Modelos avanzados en /workspace/hf-data
- **Podman**: Orquestación de contenedores
- **VS Code**: Entorno de desarrollo integrado y centro de comando
- **Persistencia**: D:\BooPhoenix\ (todos los volúmenes)
- **Git**: Control de versiones integrado

### Modelos IA Disponibles:

**Ollama:**
- llama3:8b - Razonamiento general y multiidioma
- mistral:7b - Tareas rápidas y eficientes  
- mixtral:8x7b - Tareas complejas MoE
- deepseek-coder-v2 - Generación de código
- qwen2.5-coder:7b - Código y reasoning técnico
- gemma:7b - Eficiencia y reasoning
- phi3:14b - Creatividad y multimodalidad
- falcon:7b - SSM/Mamba eficiente

**Hugging Face:**
- Zyphra/Zamba2-7B-Instruct - Reasoning avanzado SSM-Mamba
- Zyphra/BlackMamba-2.8B - SSM+MoE ultra eficiente
- Zyphra/ZR1-1.5B - Reasoning matemático y código
- Zyphra/Zonos-v0.1-hybrid - TTS multilingüe
- NousResearch/Nous-Hermes-2-Mixtral-8x7B-SFT - Chat avanzado
- Phind/Phind-CodeLlama-34B-v2 - Código especializado
```


## Integración DevOps con VS Code

### Estructura de Workspace Optimizada

```
D:\BooPhoenix\
│
├── windmill-data/          # Datos de Windmill
├── windmill-db/            # Base de datos PostgreSQL
├── windmill-backup/        # Backups automatizados
├── ollama-data/            # Modelos Ollama
├── hf-data/               # Modelos Hugging Face
├── scripts/               # Scripts de automatización
│   ├── start-stack.ps1
│   ├── download-hf-models.sh
│   ├── backup-system.py
│   └── benchmark-models.py
├── workflows/             # Scripts Windmill y Python
│   ├── roo-orchestrator.py
│   ├── test-ollama-integration.py
│   └── multi-model-consensus.py
├── docs/                  # Documentación
├── .env                   # Variables de entorno
├── .gitignore
└── README.md
```


## Capacidades Integradas del Orquestador

### 1. Selección Inteligente de Modelos con DevOps

**Análisis Automatizado:**

- Evalúa complejidad computacional desde VS Code
- Selecciona modelo óptimo basado en recursos disponibles
- Implementa validación cruzada con múltiples modelos
- Registra decisiones en logs de Windmill

**Implementación en VS Code:**

```python
# workflows/model-selector.py
import requests
import json
from typing import Dict, List

class ModelOrchestrator:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.models = {
            "reasoning": ["zamba2-7b-instruct", "llama3:8b"],
            "coding": ["deepseek-coder-v2", "qwen2.5-coder:7b"],
            "fast": ["mistral:7b", "gemma:7b"],
            "complex": ["mixtral:8x7b", "nous-hermes-2-mixtral"]
        }
    
    def select_optimal_model(self, task_type: str, complexity: str):
        """Selecciona el modelo óptimo basado en tipo y complejidad"""
        if task_type == "reasoning" and complexity == "high":
            return self.models["reasoning"][0]  # Zamba2-7B
        elif task_type == "coding":
            return self.models["coding"][0]     # DeepSeek-Coder
        else:
            return self.models["fast"][0]       # Mistral-7B
```


### 2. Orquestación de Workflows DevOps

**Gestión de Contenedores desde VS Code:**

```powershell
# scripts/start-stack.ps1
Write-Host "🚀 Iniciando Phoenix DemiGod v8.7..."
podman start windmill-db
podman start windmill  
podman start ollama
Write-Host "✅ Stack activo. Acceso: Windmill (8001), Ollama (11434)"
```

**Monitorización Integrada:**

```python
# workflows/system-monitor.py
import subprocess
import json

def check_system_health():
    """Verifica estado de contenedores y recursos"""
    containers = subprocess.run(
        ["podman", "ps", "--format", "json"], 
        capture_output=True, text=True
    )
    
    stats = subprocess.run(
        ["podman", "stats", "--no-stream", "--format", "json"],
        capture_output=True, text=True
    )
    
    return {
        "containers": json.loads(containers.stdout),
        "resources": json.loads(stats.stdout),
        "timestamp": datetime.now().isoformat()
    }
```


### 3. Reasoning Avanzado con Validación DevOps

**Protocolos de Consenso Multi-Modelo:**

```python
# workflows/multi-model-consensus.py
def multi_model_reasoning(prompt: str, models: List[str], strategy: str = "consensus"):
    """
    Implementa reasoning con múltiples modelos y validación cruzada
    """
    results = {}
    
    for model in models:
        try:
            response = query_ollama_model(model, prompt)
            results[model] = {
                "response": response.get("response", ""),
                "eval_duration": response.get("eval_duration", 0),
                "load_duration": response.get("load_duration", 0)
            }
        except Exception as e:
            results[model] = {"error": str(e)}
    
    if strategy == "consensus":
        return analyze_consensus(results)
    elif strategy == "performance":
        return select_fastest_accurate(results)
    else:
        return results
```


## Variables de Entorno Unificadas

```python
# .env - Configuración centralizada
OLLAMA_API_URL=http://localhost:11434/api/generate
HF_MODELS_PATH=/workspace/hf-data
WINDMILL_BASE_URL=http://localhost:8001
SYSTEM_DATA_PATH=D:/BooPhoenix/
PODMAN_MACHINE=defaultizzy-root

# Configuración de modelos por categoría
REASONING_MODELS=["zamba2-7b-instruct", "llama3:8b"]
CODING_MODELS=["deepseek-coder-v2", "qwen2.5-coder:7b"]
FAST_MODELS=["mistral:7b", "gemma:7b"]
COMPLEX_MODELS=["mixtral:8x7b", "nous-hermes-2-mixtral"]
```


## Protocolos de Operación Integrados

### Flujo de Trabajo Completo en VS Code

**1. Configuración del Workspace:**

- Abrir `D:\BooPhoenix` en VS Code
- Instalar extensiones: Python, Docker, GitLens, DotENV
- Configurar terminal integrada para PowerShell

**2. Gestión de Servicios:**

```powershell
# Verificar estado
podman ps -a

# Ejecutar stack completo
.\scripts\start-stack.ps1

# Monitorizar recursos
podman stats
```

**3. Desarrollo y Testing:**

```python
# workflows/test-integration.py
def test_roo_orchestrator():
    """Prueba completa del orquestador"""
    tests = [
        ("reasoning", "Explica la teoría de la relatividad"),
        ("coding", "Crea una función para ordenar una lista"),
        ("fast", "¿Cuál es la capital de Francia?")
    ]
    
    for task_type, prompt in tests:
        model = select_optimal_model(task_type, "medium")
        result = execute_task(model, prompt)
        validate_response(result)
        log_performance(task_type, model, result)
```

**4. Control de Versiones:**

```bash
# Workflow Git integrado
git checkout -b feature/enhanced-reasoning
git add workflows/
git commit -m "feat: add multi-model consensus reasoning"
git push origin feature/enhanced-reasoning
```

**5. Monitorización en Tiempo Real:**

```powershell
# Logs en vivo
podman logs -f windmill
podman logs -f ollama

# Métricas de rendimiento
podman stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```


## Directrices de Seguridad y Rendimiento

### Seguridad DevOps

- **Validación de entrada:** Sanitizar prompts antes de enviar a modelos
- **Gestión de secretos:** Variables sensibles en `.env` (nunca en Git)
- **Backups automáticos:** Scripts de backup programados en Windmill
- **Monitorización de recursos:** Alertas automáticas por sobrecarga


### Optimización de Rendimiento

- **Caché inteligente:** Respuestas frecuentes en Redis/memoria
- **Balanceador de carga:** Distribución automática entre modelos
- **Métricas en tiempo real:** Dashboard en Windmill para KPIs
- **Escalado dinámico:** Ajuste automático de recursos según demanda


## Formato de Respuesta Estandarizado

Para cada tarea ejecutada por Roo Code:

```json
{
  "analysis": "Evaluación de la tarea y estrategia seleccionada",
  "selected_models": {
    "primary": "modelo_principal",
    "secondary": "modelo_validacion",
    "justification": "razón_de_selección"
  },
  "execution": {
    "steps": ["paso1", "paso2", "paso3"],
    "commands": ["comando1", "comando2"],
    "duration": "tiempo_total"
  },
  "validation": {
    "accuracy": "precisión_respuesta",
    "performance": "métricas_rendimiento",
    "consensus": "nivel_consenso_multi_modelo"
  },
  "logs": {
    "timestamp": "iso_timestamp",
    "container_status": "estado_contenedores",
    "resource_usage": "uso_recursos",
    "errors": "errores_encontrados"
  }
}
```


## Script de Inicialización Completo

```python
# workflows/initialize-phoenix-demigod.py
def initialize_phoenix_demigod():
    """
    Inicialización completa del sistema Phoenix DemiGod v8.7
    """
    print("🔥 Inicializando Phoenix DemiGod v8.7...")
    
    # 1. Verificar contenedores
    container_status = check_container_status()
    
    # 2. Validar modelos disponibles
    ollama_models = check_ollama_models()
    hf_models = check_hf_models()
    
    # 3. Configurar variables de entorno
    load_environment_variables()
    
    # 4. Inicializar orquestador Roo Code
    roo_status = initialize_roo_orchestrator()
    
    # 5. Ejecutar pruebas de conectividad
    connectivity_tests = run_connectivity_tests()
    
    return {
        "status": "ready",
        "version": "8.7.2",
        "components": {
            "containers": container_status,
            "ollama_models": ollama_models,
            "hf_models": hf_models,
            "roo_orchestrator": roo_status,
            "connectivity": connectivity_tests
        },
        "timestamp": datetime.now().isoformat()
    }
```


## Resumen Ejecutivo

Esta síntesis integra el **Prompt Maestro para Roo Code Orquestador** con el **Flujo DevOps de 7 pasos en VS Code**, creando un sistema unificado donde:

- **Roo Code** actúa como cerebro central de Phoenix DemiGod v8.7
- **VS Code** sirve como centro de comando y desarrollo
- **Los workflows DevOps** garantizan calidad, trazabilidad y escalabilidad
- **La orquestación multi-modelo** maximiza rendimiento y precisión
- **La automatización inteligente** reduce complejidad operacional

El resultado es un entorno profesional de IA local que combina potencia técnica, facilidad de uso y robustez operacional, preparado para cualquier reto de reasoning, automatización o desarrollo en el ecosistema Phoenix DemiGod.

