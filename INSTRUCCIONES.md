# Configuración del Entorno de IA Local con Podman

Esta guía te mostrará cómo desplegar y configurar tu entorno de modelos de IA local utilizando Podman Compose.

## Prerrequisitos

-   Tener `podman` y `podman-compose` instalados en tu sistema.
-   Haber guardado los archivos `podman-compose.yml` y `pull_models.sh` en el mismo directorio.

## Pasos

### 1. Levantar los Servicios

Abre una terminal en el directorio donde guardaste los archivos y ejecuta el siguiente comando para iniciar los contenedores de Ollama y Windsurf en segundo plano:

```bash
podman-compose up -d
```

### 2. Descargar los Modelos de IA

Una vez que los servicios estén en ejecución, necesitas descargar los modelos de IA. Primero, dale permisos de ejecución al script:

```bash
chmod +x pull_models.sh
```

Luego, ejecuta el script para iniciar la descarga:

```bash
./pull_models.sh
```

El script descargará los siguientes modelos:
-   `codestral-mamba-7b-instruct-q4`
-   `deepseek-r1-7b-instruct-q4`
-   `phi-3mini-4k-instruct-q4`
-   `rwkv-7b-world-q4`
-   `llama3:8b-instruct-q4`

Este proceso puede tardar varios minutos dependiendo de tu conexión a internet.

### 3. Verificar los Modelos

Para asegurarte de que los modelos se han descargado correctamente, puedes listar los modelos disponibles en Ollama con el siguiente comando:

```bash
podman exec ollama ollama list
```

Deberías ver en la salida la lista de los modelos que acabas de descargar.

## Finalización

¡Listo! Tu entorno de IA local está configurado y los modelos están listos para ser utilizados por Windsurf.