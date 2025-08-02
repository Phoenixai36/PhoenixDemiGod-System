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
echo "Iniciando el despliegue de la pila Phoenix DemiGod..."

$COMPOSE_CMD up --build -d

echo "El despliegue ha sido iniciado en segundo plano."
