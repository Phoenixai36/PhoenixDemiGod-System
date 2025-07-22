#!/bin/bash
# chaos-agent.sh
# Introduce fallos controlados para pruebas de resiliencia.

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
LOG_FILE="omas/logs/chaos-agent.log"
TARGET_SERVICE="${TARGET_SERVICE:-phoenix-demigod}"

# Simular fallo en servicio (mock para pruebas)
log "Simulando fallo en $TARGET_SERVICE..." "ChaosAgent" "$LOG_FILE"
echo "Mock: Fallo simulado en $TARGET_SERVICE"

log "Chaos Agent completado" "ChaosAgent" "$LOG_FILE"
exit 0