#!/bin/bash
# demigod-agent.sh
# Orquesta el agente DemiGod, conecta vía OSC y registra logs en JSON.

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
LOG_FILE="omas/logs/demigod-agent.log"
OSC_ADDRESS="udp://localhost:${OSC_PORT:-9000}"
REST_ENDPOINT="${AUTO_GEN_ENDPOINT:-http://localhost:8081/autogen/generate}"

# Iniciar conexión OSC (mockeada para pruebas)
log "Iniciando conexión OSC a $OSC_ADDRESS" "DemigodAgent" "$LOG_FILE"
echo "Mock: Conexión OSC establecida"

# Ejecutar petición REST
log "Ejecutando petición a $REST_ENDPOINT" "DemigodAgent" "$LOG_FILE"
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$REST_ENDPOINT" -d '{"prompt":"Orquestar agente DemiGod"}')
if [ "$http_code" -ne 200 ]; then
  log "ERROR: Fallo en la petición REST a $REST_ENDPOINT (Código: $http_code)" "DemigodAgent" "$LOG_FILE"
  exit 1
fi

log "Agente DemiGod orquestado correctamente" "DemigodAgent" "$LOG_FILE"
exit 0