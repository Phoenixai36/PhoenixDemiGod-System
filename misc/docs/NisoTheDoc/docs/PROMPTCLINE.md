<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# ok refina y entrega un prompt ultra perfecto i ambicioso para cline en vs code insiders con mcps i extensiones que consideres tu mismo

Puedes llamarme **Oracle** - mi nomenclatura refleja la capacidad de análisis predictivo y optimización de arquitecturas complejas que aporto al ecosistema Phoenix DemiGod.

# Prompt Ultra Maestro para Cline en VS Code Insiders - Phoenix DemiGod v8.7

## Contexto Arquitectónico Completo

**Cline**, eres el agente autónomo supremo para orquestar todo el ecosistema Phoenix DemiGod v8.7 desde VS Code Insiders con integración MCP avanzada. Tu misión es ejecutar el despliegue completo, automatización DevOps y optimización de modelos sin transformers (Mamba/SSM, RWKV, Jamba) en arquitectura híbrida local-cloud.

**Definición MCP (Model Context Protocol):** Protocolo estandarizado que permite a modelos AI descubrir e interactuar con herramientas externas, aplicaciones y fuentes de datos. **Tools:** Servidores MCP, cliente integrado en VS Code, routing middleware. **Lógica ideal:** Conexión seamless entre AI y ecosistema de desarrollo existente.

## Extensiones VS Code Insiders Críticas

### Stack de Extensiones Recomendado

- **Continue.dev**: Asistente AI open-source con soporte multi-modelo y edición contextual
- **Cline (MCP Native)**: Agente autónomo para tareas de desarrollo complejas con protocolos MCP
- **GitHub Copilot**: Autocomplete inteligente y sugerencias contextuales
- **Docker + Podman Extensions**: Gestión unificada de contenedores con soporte multi-runtime
- **Python + Pylance**: Desarrollo Python avanzado con type checking
- **YAML + JSON Tools**: Validación y autocompletado para configuraciones
- **GitLens**: Control de versiones visual y análisis de cambios
- **Thunder Client**: Testing de APIs REST integrado
- **Remote Development**: Desarrollo en contenedores y WSL2

**Definición Continue.dev:** Asistente AI open-source que permite usar múltiples modelos LLM locales y remotos dentro de VS Code. **Tools:** Model switching, context awareness, chat interface. **Lógica ideal:** Flexibilidad total de modelos sin vendor lock-in.

## Configuración MCP Servers para Phoenix DemiGod

### Servidores MCP Especializados

```json
{
  "phoenix_mcp_config": {
    "servers": {
      "phoenix_model_router": {
        "command": "python",
        "args": ["-m", "phoenix_mcp.model_router"],
        "env": {
          "PHOENIX_ENV": "production",
          "MODEL_PATH": "./models/quantized"
        }
      },
      "ollama_bridge": {
        "command": "python", 
        "args": ["-m", "phoenix_mcp.ollama_bridge"],
        "env": {
          "OLLAMA_HOST": "localhost:11434"
        }
      },
      "n8n_workflows": {
        "command": "node",
        "args": ["./mcp-servers/n8n-bridge.js"],
        "env": {
          "N8N_API_URL": "http://localhost:5678"
        }
      },
      "windmill_orchestrator": {
        "command": "python",
        "args": ["-m", "phoenix_mcp.windmill_bridge"],
        "env": {
          "WINDMILL_URL": "http://localhost:8002"
        }
      }
    }
  }
}
```

**Definición Windmill:** Plataforma de automatización que convierte scripts Python/TypeScript en workflows auto-escalables con UI web. **Tools:** Script editor, flow builder, webhook triggers, observabilidad integrada. **Lógica ideal:** Developer-first automation con código como configuración.

## Prompt Maestro Completo

```markdown
# MISIÓN ULTRA AMBICIOSA: Phoenix DemiGod v8.7 - Despliegue Autónomo Total

Eres Cline, orquestador supremo del ecosistema Phoenix DemiGod v8.7. Ejecuta el despliegue completo desde el repositorio https://github.com/Phoenixai36/BooPhoenix369 hasta un sistema productivo escalable con validación para subvenciones ACCI/BerriUp.

## FASE 1: Configuración Avanzada del Entorno (15 minutos)

### 1.1 Clonación y Setup Optimizado
```


# Clonar repositorio con optimizaciones Git

git clone --depth 1 --filter=blob:none https://github.com/Phoenixai36/BooPhoenix369.git
cd BooPhoenix369

# Configurar entorno híbrido

python -m venv .venv-phoenix
source .venv-phoenix/bin/activate  \# Linux/macOS

# .venv-phoenix\Scripts\activate  \# Windows

# Instalar dependencias con optimizaciones

pip install -r requirements.txt \
--extra-index-url https://download.pytorch.org/whl/cu121 \
--timeout 300 --retries 3

```

### 1.2 Configuración MCP Servers
Inicializa los servidores MCP especializados para:
- Router multi-modelo (Zamba2-2.7B, Codestral-Mamba-7B, Falcon-Mamba-7B)
- Bridge Ollama para modelos locales
- Integración n8n workflows
- Orquestación Windmill

### 1.3 Variables de Entorno Críticas
```

PHOENIX_VERSION=8.7.0
ENVIRONMENT=production
GPU_PROFILER=RTX4060-4GB
INFERENCE_MODE=HYBRID

# Modelos SSM prioritarios

DEFAULT_MODEL=zamba2-2.7b-instruct
CODING_SPECIALIST=codestral-mamba-7b
FALLBACK_MODEL=falcon-mamba-7b

# Optimizaciones XAMBA

XAMBA_ENABLED=true
QUANTIZATION=4bit

```

## FASE 2: Despliegue de Infraestructura Híbrida (20 minutos)

### 2.1 Contenedores con Podman
Despliega el stack completo usando docker-compose.hybrid.yml:
- Phoenix Core (puerto 8001)
- Windmill Orchestrator (puerto 8002) 
- Ollama Models (puerto 11435)
- Qdrant Vector DB (puerto 6333)
- MLflow Tracking (puerto 5000)

**Definición Qdrant:** Base de datos vectorial de alta performance para almacenamiento y búsqueda de embeddings con similitud coseno/euclidiana. **Tools:** REST API, Python client, vector indexing, filtering. **Lógica ideal:** Búsqueda semántica eficiente para RAG y memoria a largo plazo.

### 2.2 Configuración IaC con Terraform
Aplica la configuración Infrastructure as Code:
```

module "phoenix_core" {
source = "./terraform/modules/phoenix"
replicas = 2
gpu_enabled = true
quantization = "4bit"
}

```

### 2.3 Scripts de Automatización
Ejecuta los scripts de initialización:
- `./phoenix-prerequisites.sh` - Dependencias del sistema
- `./phoenix-context-rules-manager.sh` - Configuración de contexto
- `./shell-commands/core/init-modules-complete.sh` - Módulos completos

## FASE 3: Optimización y Validación (25 minutos)

### 3.1 Router Multi-Modelo Inteligente
Configura el router que selecciona automáticamente:
- **Zamba2-2.7B** para reasoning eficiente
- **Codestral-Mamba-7B** para programación
- **Falcon-Mamba-7B** como fallback robusto

### 3.2 Workflows n8n Avanzados
Activa los workflows críticos:
- `autogen-integration.json` - Integración AutoGen
- `core-orchestration.json` - Orquestación principal  
- `omas-integration.json` - Agentes OMAS

**Definición n8n:** Plataforma de automatización workflow que permite crear pipelines de datos complejos mediante nodos visuales. **Tools:** Nodos preconstruidos, JavaScript personalizado, webhooks, triggers. **Lógica ideal:** Workflows deben incluir error handling y minimizar API calls usando caché.

### 3.3 Validación Técnica Completa
Ejecuta la suite de validación:
```

python ./scripts/validation_suite_grants.py --mode complete --output validation_pack.zip

```

Verifica métricas objetivo:
- Latencia p95: <2s
- Throughput: >100 tokens/s por modelo
- Uptime: >99.5%
- Eficiencia energética: <100W por instancia 7B

## FASE 4: Preparación para Subvenciones (15 minutos)

### 4.1 Generación de Documentación
Crea automáticamente:
- Memoria técnica con arquitectura híbrida
- Video demo de 2:45 min mostrando capacidades
- Métricas de performance vs competencia
- Proyección financiera y ROI

### 4.2 Paquete de Validación
Genera `phoenix_demigod_grant_package.zip` conteniendo:
- Especificaciones técnicas (TRL 6-7)
- Benchmarks comparativos
- Documentación compliance AI Act
- Plan de escalado comercial

## FASE 5: Monitorización y Observabilidad (10 minutos)

### 5.1 Dashboard Unificado
Configura Grafana con métricas críticas:
- Uso GPU local/cloud
- Latencia de inferencia por modelo
- Estado de conexiones MCP
- Throughput de workflows n8n

### 5.2 Alertas Proactivas
Implementa alertas para:
- Latencia >2s en p95
- Modelos inactivos <2 disponibles
- Fallos en workflows críticos
- Uso memoria >80%

## RESTRICCIONES Y OPTIMIZACIONES

### Recursos Disponibles
- GPU: RTX 4060 4GB local + cloud burst Vast.ai A40
- Memoria: Optimizar para <8GB RAM total
- Almacenamiento: Modelos cuantizados 4-bit máximo

### Deadlines Críticos
- ACCI Startup Capital: Julio 10, 2025
- BerriUp aplicación: Julio 11, 2025
- Kit Digital 2025: Julio 20, 2025

## RESULTADO ESPERADO

Sistema Phoenix DemiGod v8.7 completamente operativo con:
✅ Arquitectura híbrida local-cloud funcional
✅ Router multi-modelo con consenso inteligente
✅ Workflows automatizados n8n + Windmill
✅ Observabilidad 360° con alertas proactivas
✅ Paquete completo para subvenciones listo
✅ Validación técnica certificada (TRL 6-7)

Ejecuta cada fase secuencialmente, validando éxito antes de continuar. Registra todos los logs en `./logs/cline_execution_${timestamp}.log` y notifica completion con métricas finales.

¡Inicia la orquestación completa AHORA!
```


## Configuración Avanzada VS Code Insiders

### Workspace Settings Optimizado

```json
{
  "python.defaultInterpreterPath": "./.venv-phoenix/bin/python",
  "files.associations": {
    "*.roo": "yaml",
    "*.phoenix": "json"
  },
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "docker.defaultPlatform": "linux",
  "continue.models": [
    {
      "title": "Phoenix Core Local",
      "provider": "ollama",
      "model": "zamba2-2.7b-instruct"
    },
    {
      "title": "Coding Specialist", 
      "provider": "ollama",
      "model": "codestral-mamba-7b"
    }
  ],
  "cline.mcpServers": [
    "phoenix_model_router",
    "ollama_bridge", 
    "n8n_workflows",
    "windmill_orchestrator"
  ]
}
```

**Definición Cline MCP Integration:** Extensión que permite a Cline comunicarse con servidores MCP para acceder a herramientas externas y fuentes de datos. **Tools:** MCP client protocol, server discovery, tool invocation. **Lógica ideal:** Expandir capacidades de Cline más allá del filesystem local.

## Tasks Automatizadas

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Phoenix: Deploy Complete Stack",
      "type": "shell",
      "command": "./phoenix-master.sh --mode production",
      "group": "build"
    },
    {
      "label": "Phoenix: Validate System",
      "type": "shell", 
      "command": "python ./scripts/validation_suite_grants.py",
      "group": "test"
    },
    {
      "label": "Phoenix: Generate Grant Package",
      "type": "shell",
      "command": "./scripts/prepare_submission.sh --target acci,berriup",
      "group": "build"
    }
  ]
}
```


## Resumen No Técnico

He creado un prompt ultra completo que permite a Cline automatizar todo el despliegue de Phoenix DemiGod desde VS Code Insiders. El prompt integra servidores MCP especializados, configura un stack híbrido completo con modelos sin transformers, y genera automáticamente toda la documentación necesaria para las subvenciones españolas de 2025. Con las extensiones recomendadas y la configuración optimizada, tendrás un entorno de desarrollo de clase mundial que puede competir con cualquier solución comercial, manteniendo control total y privacidad de datos.

NEXT FASE? (EJECUCIÓN INMEDIATA DEL PROMPT MAESTRO EN CLINE)

<div style="text-align: center">⁂</div>

[^1]: ADIEU.md

[^2]: Modelos-de-IA_-Mamba-Falcon-Zyphra-Ollama-Hugg.md

[^3]: ahora-lo-mismo-pero-omite-nombres-de-cosas-ya-hech.md

[^4]: BOBOBO.md

[^5]: y-si-para-facilitar-todo-ya-que-con-los-scripts-m.md

[^6]: esto-es-real_-mira-el-script-que-adjunto-como-cre.md

[^7]: Vale-pues-estamos-aqui._Ya-sabemos-el-plan._neces.md

[^8]: vale-pues-estamos-aqui-ya-sabe-jHXnASCFSfm_hwdKG1UzZg.md

[^9]: dame-el-organigrama-de-el-proy-UR0zLuxcSv.xCH1m9m840w.md

[^10]: vale-vale-pues-semana-1-manana-cegCGaE9RZ.oj1YeYC9I2Q.md

[^11]: ya-ves-i-eso-con-roo-code-IDE-PUEDO-montar-las-a.md

