# Phoenix DemiGod v8.7 - Guía de Despliegue Local Offline

Este documento proporciona una guía completa para desplegar el entorno de desarrollo 100% offline de Phoenix DemiGod v8.7 en tu máquina local. El stack utiliza Podman para la orquestación de contenedores y Ollama para servir modelos de IA locales.

## Requisitos Previos

Asegúrate de tener instalados **Podman** y **Podman Compose** en tu sistema.

## Archivos de Configuración

El entorno se define mediante los siguientes tres archivos en el directorio raíz:

### 1. Infraestructura de Servicios (`podman-compose.yml`)
Este archivo define los servicios de `windsuf` (el IDE de automatización) y `ollama` (el servidor de modelos).

```yaml
version: "3.9"

services:
  windsuf:
    image: ghcr.io/windsurf/ide:latest
    container_name: windsuf
    ports:
      - "3001:3001"          # UI
    volumes:
      - ./workspace:/workspace
      - ./windsuf-config:/root/.config/windsurf
    environment:
      - WINDMILL_API=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./models:/root/.ollama
    deploy:
      resources:
        limits:
          memory: 8G
    restart: unless-stopped
```

### 2. Script de Descarga de Modelos (`pull_models.sh`)
Este script automatiza la descarga de los modelos de IA necesarios.

```bash
#!/usr/bin/env bash
set -e
podman start ollama 2>/dev/null || true

MODELS=(
  "codestral-mamba-7b-instruct-q4"
  "deepseek-r1-7b-instruct-q4"
  "phi-3mini-4k-instruct-q4"
  "rwkv-7b-world-q4"
  "llama3:8b-instruct-q4"
)

for M in "${MODELS[@]}"; do
  echo "Descargando $M..."
  podman exec ollama ollama pull "$M"
done

echo "✅  Modelos listos."
```

### 3. Configuración del Router de Modelos (`config.json`)
Este archivo configura el enrutamiento inteligente de peticiones a los modelos locales.

```json
{
  "router": {
    "default":     ["ollama", "codestral-mamba-7b-instruct-q4"],
    "think":       ["ollama", "deepseek-r1-7b-instruct-q4"],
    "background":  ["ollama", "phi-3mini-4k-instruct-q4"],
    "longContext": ["ollama", "rwkv-7b-world-q4"]
  },
  "providers": {
    "ollama": {
      "api_base": "http://ollama:11434/v1/chat/completions",
      "api_key":  "ollama-local"
    }
  },
  "fallback_strategy": {
    "enabled": true,
    "provider": "ollama",
    "model":    "llama3-8b-instruct-q4"
  }
}
```

## Puesta en Marcha

Sigue estos pasos en orden desde la terminal en el directorio raíz del proyecto.

### Paso 1: Levantar la Infraestructura
Inicia los contenedores de Windsurf y Ollama.

```bash
podman-compose up -d
```

### Paso 2: Descargar los Modelos de IA
Primero, otorga permisos de ejecución al script y luego ejecútalo.

```bash
chmod +x pull_models.sh
./pull_models.sh
```
Este proceso puede tardar varios minutos dependiendo de tu conexión a internet.

### Paso 3: Ejecutar las Pruebas de Auditoría
Para verificar la correcta configuración y estado del entorno, ejecuta el script de auditoría.

Primero, dale permisos de ejecución:
```bash
chmod +x test_environment.sh
```

Luego, ejecútalo:
```bash
./test_environment.sh
```

Este script realizará las siguientes comprobaciones:
1.  **Salud de los Servicios**: Confirma que `Windsurf` y `Ollama` estén operativos.
2.  **Disponibilidad de Modelos**: Verifica que los 5 modelos de IA necesarios estén descargados y listos.
3.  **Simulación de Enrutamiento**: Realiza una prueba básica para asegurar que el enrutamiento de peticiones funciona.

Una salida exitosa mostrará "✅ Todas las pruebas pasaron", confirmando que el sistema está listo para su uso y para cualquier demostración o benchmarking.

---

¡Listo! Tu entorno Phoenix DemiGod v8.7 está ahora completamente configurado y operativo en modo offline.
# PhoenixSeed
