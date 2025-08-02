#!/bin/bash
set -e

# Detect compose command
if command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "Error: Ni 'podman-compose' ni 'docker-compose' se encontraron en el PATH."
    exit 1
fi

echo "Usando: $COMPOSE_CMD"
echo "Iniciando la verificación de servicios..."

# Lista de servicios en orden de dependencia
SERVICES=("db" "analysis-engine" "recurrent-processor" "windmill" "rubik-agent" "gap-detector" "nginx")

for service in "${SERVICES[@]}"; do
    echo "Verificando el servicio: $service..."
    # Comprueba si el servicio está en ejecución.
    # La salida de 'ps -q' es el ID del contenedor si está corriendo.
    # El grep busca un estado 'running' o 'Up', compatible con ambos compose.
    if [ -z "$($COMPOSE_CMD ps -q $service)" ] || [ -z "$($COMPOSE_CMD ps $service | grep -E 'running|Up')" ]; then
        echo "Error: El servicio $service no está en ejecución."
        exit 1
    fi
    echo "Servicio $service verificado correctamente."
done

echo "Todos los servicios se han verificado exitosamente."
exit 0