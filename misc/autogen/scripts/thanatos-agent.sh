#!/bin/bash
# thanatos-agent.sh
# Gestiona el renacimiento de otros agentes.

# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipelines return the exit status of the last command to fail.
set -o pipefail

# Cargar utilidades comunes
source "$(dirname "$0")/utils.sh"

# Cargar variables de entorno
load_env

# Configuración
LOG_FILE="omas/logs/thanatos-agent.log" # Use a relative path for the log file
# Use PROJECT_ROOT from utils.sh instead of a locally defined ROOT_DIR
COMPOSE_FILE="$PROJECT_ROOT/src/deployment/docker/compose.yaml"
ENV_FILE="$PROJECT_ROOT/.env"
AGENT_NAME="${1:-}" # Use parameter expansion for safety with set -u

# Validar argumento
if [ -z "$AGENT_NAME" ]; then
  # Use a relative path for the log file, as expected by the log function.
  log "ERROR: Se requiere el nombre del agente como argumento. Uso: $0 <nombre-agente>" "SYSTEM" "$LOG_FILE"
  exit 1
fi

# Validar que podman existe y está operativo
if ! command -v podman >/dev/null 2>&1; then
    log "ERROR: El comando 'podman' no se encuentra. Por favor, instale Podman." "SYSTEM" "$LOG_FILE"
    exit 1
fi
if ! podman info >/dev/null 2>&1; then
    log "ERROR: No se pudo conectar con el servicio Podman. Asegúrese de que la máquina Podman esté iniciada." "SYSTEM" "$LOG_FILE"
    exit 1
fi

# Validar que los archivos necesarios existen
if [ ! -f "$COMPOSE_FILE" ]; then
    log "ERROR: No se encuentra el archivo compose: $COMPOSE_FILE" "$AGENT_NAME" "$LOG_FILE"
    exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
    log "ERROR: No se encuentra el archivo .env: $ENV_FILE" "$AGENT_NAME" "$LOG_FILE"
    exit 1
fi

# Validar que el agente existe como servicio en el archivo compose
if ! grep -q "^\s*${AGENT_NAME}:" "$COMPOSE_FILE"; then
    log "ERROR: El agente '$AGENT_NAME' no es un servicio válido en $COMPOSE_FILE" "$AGENT_NAME" "$LOG_FILE"
    exit 1
fi

# Lógica de renacimiento
log "Iniciando renacimiento para el servicio: $AGENT_NAME" "$AGENT_NAME" "$LOG_FILE"

# Generar nuevo Genma (usando timestamp como mock)
NEW_GENMA=$(date +%s)
log "Nuevo Genma generado: $NEW_GENMA" "$AGENT_NAME" "$LOG_FILE"

# Actualizar el .env con el nuevo Genma.
# Esto asume una convención en .env como "DEMIGOD_AGENT_GENMA", "CHAOS_AGENT_GENMA", etc.
temp_agent_name=${AGENT_NAME//-/_} # Replace hyphens with underscores
ENV_VAR_NAME=${temp_agent_name^^}_GENMA # Convert to uppercase and append _GENMA
log "Actualizando la variable de entorno $ENV_VAR_NAME en el archivo .env" "$AGENT_NAME" "$LOG_FILE"

# Forma más segura de actualizar el archivo .env usando un archivo temporal.
temp_env_file=$(mktemp)
if grep -q "^${ENV_VAR_NAME}=" "$ENV_FILE"; then
  # La variable existe, reemplazarla en el archivo temporal
  sed "s|^${ENV_VAR_NAME}=.*|${ENV_VAR_NAME}=${NEW_GENMA}|" "$ENV_FILE" > "$temp_env_file"
else
  # La variable no existe, copiar el original y añadirla al final del archivo temporal
  cp "$ENV_FILE" "$temp_env_file"
  echo "${ENV_VAR_NAME}=${NEW_GENMA}" >> "$temp_env_file"
fi
# Reemplazar atómicamente el archivo .env original con el temporal
mv "$temp_env_file" "$ENV_FILE"

# Forzar la recreación del contenedor para aplicar el nuevo entorno.
log "Recreando el servicio $AGENT_NAME para aplicar el nuevo Genma..." "$AGENT_NAME" "$LOG_FILE"
if podman compose -f "$COMPOSE_FILE" up -d --force-recreate "$AGENT_NAME" --remove-orphans; then
    log "Servicio $AGENT_NAME recreado con éxito." "$AGENT_NAME" "$LOG_FILE"
else
    log "ERROR: Falló la recreación del servicio $AGENT_NAME." "$AGENT_NAME" "$LOG_FILE"
    exit 1
fi

log "Thanatos Agent completado para: $AGENT_NAME" "$AGENT_NAME" "$LOG_FILE"