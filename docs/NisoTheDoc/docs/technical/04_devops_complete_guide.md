# Guía Completa de DevOps para Phoenix DemiGod v8.7

Esta guía exhaustiva proporciona todas las instrucciones necesarias para implementar, configurar, desplegar, monitorizar y mantener el sistema Phoenix DemiGod v8.7 siguiendo las mejores prácticas de DevOps.

## Índice

1. [Seguridad y Gestión de Secretos](#1-seguridad-y-gestión-de-secretos)
2. [Configuración de Entornos](#2-configuración-de-entornos)
3. [CI/CD y Automatización](#3-cicd-y-automatización)
4. [Despliegue y Orquestación](#4-despliegue-y-orquestación)
5. [Monitorización y Observabilidad](#5-monitorización-y-observabilidad)
6. [Gestión de Dependencias](#6-gestión-de-dependencias)
7. [Testing y Validación](#7-testing-y-validacion)
8. [Documentación](#8-documentacion)
9. [Mantenimiento y Operaciones](#9-mantenimiento-y-operaciones)
10. [Estrategias de Rollback](#10-estrategias-de-rollback)

## 1. Seguridad y Gestión de Secretos

### 1.1 Gestión de Tokens y Credenciales

⚠️ **CRÍTICO: Nunca almacenar tokens o credenciales en el repositorio**

#### Configuración de Docker/Podman Secrets

```bash
# Crear secretos para Docker/Podman
docker secret create db_password /path/to/password/file
docker secret create manager_token /path/to/manager/token
docker secret create worker_token /path/to/worker/token

# Verificar secretos creados
docker secret ls
```

#### Implementación con HashiCorp Vault (Recomendado)

1. Instalar HashiCorp Vault:

```bash
# Instalación de Vault
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install vault
```

1. Configurar Vault para Phoenix DemiGod:

```bash
# Iniciar Vault en modo desarrollo (solo para pruebas)
vault server -dev

# En otra terminal, configurar variables de entorno
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root-token-dev-only'

# Crear política para Phoenix DemiGod
vault policy write phoenix-policy - <<EOF
path "secret/data/phoenix/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# Almacenar secretos
vault kv put secret/phoenix/database db_user=phoenix db_password=secure_password
vault kv put secret/phoenix/swarm manager_token=your_manager_token worker_token=your_worker_token
```

1. Integrar Vault con Docker Compose:

```yaml
version: '3.8'

services:
  demigod-agent:
    image: demigod-agent:latest
    environment:
      - VAULT_ADDR=http://vault:8200
      - VAULT_TOKEN_FILE=/run/secrets/vault_token
    secrets:
      - vault_token
    # ...

secrets:
  vault_token:
    file: ./vault_token.txt
```

### 1.2 Configuración de .gitignore

Asegúrate de que el archivo `.gitignore` incluya todas las entradas necesarias para evitar la exposición de secretos:

```gitignore
# Tokens y secretos
.manager_token
.worker_token
*_token
*.pem
*.key
id_*
*.env
.env*
*secret*
*password*

# Directorios sensibles
ollama-data/
```

### 1.3 Auditoría de Seguridad Automatizada

Implementar escaneo de secretos en el pipeline de CI/CD:

```yaml
# Añadir a ci.yml
jobs:
  security_scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Scan for secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 2. Configuración de Entornos

### 2.1 Estructura de Archivos de Entorno

Crear plantillas de archivos de entorno para cada ambiente:

```bash
# Crear plantillas de entorno
cp BooPhoenix369/.env.example BooPhoenix369/.env.development.template
cp BooPhoenix369/.env.example BooPhoenix369/.env.staging.template
cp BooPhoenix369/.env.example BooPhoenix369/.env.production.template
```

Estructura recomendada para archivos `.env`:

```env
# Configuración de red
OSC_PORT=9000
PHOENIX_API_PORT=8000
OLLAMA_PORT=11434
N8N_PORT=5678
REDIS_PORT=6379

# Endpoints
AUTO_GEN_ENDPOINT=http://localhost:8000
TARGET_SERVICE=phoenix-demigod

# Rutas de volúmenes
DATA_VOLUME_PATH=./data
MODELS_VOLUME_PATH=./models

# Entorno
PHOENIX_ENV=development  # Cambiar según el entorno
```

### 2.2 Gestión de Configuración con ConfigMaps en Kubernetes

```yaml
# Crear ConfigMap para cada entorno
apiVersion: v1
kind: ConfigMap
metadata:
  name: phoenix-config-development
data:
  PHOENIX_ENV: "development"
  AUTO_GEN_ENDPOINT: "http://autogen-service:8081/autogen/generate"
  # Otras variables no sensibles
```

### 2.3 Separación de Configuración y Secretos

Estructura recomendada:

```plaintext
BooPhoenix369/
├── config/
│   ├── development/
│   │   ├── config.yaml  # Configuración no sensible
│   ├── staging/
│   │   ├── config.yaml
│   ├── production/
│   │   ├── config.yaml
├── secrets/  # Directorio NO versionado
│   ├── development/
│   │   ├── secrets.yaml  # Secretos locales (no en Git)
│   ├── staging/
│   ├── production/
```

## 3. CI/CD y Automatización

### 3.1 Pipeline de CI/CD Completo

Actualizar el archivo `ci.yml` para incluir todas las etapas necesarias:

```yaml
name: Phoenix DemiGod CI/CD

on:
  push:
    branches: [ "main", "develop" ]
  pull_request:
    branches: [ "main", "develop" ]

env:
  CARGO_TERM_COLOR: always
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff black pytest
          if [ -f BooPhoenix369/requirements.txt ]; then pip install -r BooPhoenix369/requirements.txt; fi
      - name: Lint with ruff
        run: |
          ruff check BooPhoenix369/
      - name: Format with black
        run: |
          black --check BooPhoenix369/

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          if [ -f BooPhoenix369/requirements.txt ]; then pip install -r BooPhoenix369/requirements.txt; fi
      - name: Test with pytest
        run: |
          pytest --cov=BooPhoenix369 tests/

  security_scan:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - name: Scan for secrets
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Run SAST scan
        uses: github/codeql-action/analyze@v2

  build:
    runs-on: ubuntu-latest
    needs: [test, security_scan]
    if: github.event_name == 'push'
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Log in to the Container registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
      - name: Build and push demigod-agent
        uses: docker/build-push-action@v4
        with:
          context: .
          file: BooPhoenix369/docker/Dockerfile.demigod
          push: true
          tags: ${{ steps.meta.outputs.tags }}-demigod
          labels: ${{ steps.meta.outputs.labels }}
      - name: Build and push chaos-agent
        uses: docker/build-push-action@v4
        with:
          context: .
          file: BooPhoenix369/docker/Dockerfile.chaos
          push: true
          tags: ${{ steps.meta.outputs.tags }}-chaos
          labels: ${{ steps.meta.outputs.labels }}
      - name: Build and push thanatos-agent
        uses: docker/build-push-action@v4
        with:
          context: .
          file: BooPhoenix369/docker/Dockerfile.thanatos
          push: true
          tags: ${{ steps.meta.outputs.tags }}-thanatos
          labels: ${{ steps.meta.outputs.labels }}

  deploy_staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v3
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}
      - name: Deploy to staging
        run: |
          # Actualizar imágenes en los manifiestos
          sed -i "s|your-registry/demigod-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-demigod:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          sed -i "s|your-registry/chaos-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-chaos:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          sed -i "s|your-registry/thanatos-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-thanatos:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          
          # Aplicar ConfigMap con variables de entorno
          kubectl create configmap phoenix-agent-config --from-env-file=BooPhoenix369/.env.staging -n phoenix --dry-run=client -o yaml | kubectl apply -f -
          
          # Aplicar manifiestos
          kubectl apply -f BooPhoenix369/kubernetes-deploy.yaml -n phoenix
          
          # Verificar despliegue
          kubectl rollout status deployment/demigod-agent-deployment -n phoenix
          kubectl rollout status deployment/chaos-agent-deployment -n phoenix
          kubectl rollout status deployment/thanatos-agent-deployment -n phoenix

  deploy_production:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v3
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}
      - name: Deploy to production
        run: |
          # Actualizar imágenes en los manifiestos
          sed -i "s|your-registry/demigod-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-demigod:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          sed -i "s|your-registry/chaos-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-chaos:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          sed -i "s|your-registry/thanatos-agent:v1.0|${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-thanatos:${{ github.sha }}|g" BooPhoenix369/kubernetes-deploy.yaml
          
          # Aplicar ConfigMap con variables de entorno
          kubectl create configmap phoenix-agent-config --from-env-file=BooPhoenix369/.env.production -n phoenix-prod --dry-run=client -o yaml | kubectl apply -f -
          
          # Aplicar manifiestos
          kubectl apply -f BooPhoenix369/kubernetes-deploy.yaml -n phoenix-prod
          
          # Verificar despliegue
          kubectl rollout status deployment/demigod-agent-deployment -n phoenix-prod
          kubectl rollout status deployment/chaos-agent-deployment -n phoenix-prod
          kubectl rollout status deployment/thanatos-agent-deployment -n phoenix-prod
```

### 3.2 Pre-commit Hooks

Asegúrate de que `.pre-commit-config.yaml` esté correctamente configurado:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-json
    -   id: detect-private-key
    -   id: check-merge-conflict

-   repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.262
    hooks:
    -   id: ruff
        args: [--fix, --exit-non-zero-on-fix]

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/gitleaks/gitleaks
    rev: v8.16.3
    hooks:
    -   id: gitleaks
```

Instalación de pre-commit:

```bash
pip install pre-commit
pre-commit install
```

## 4. Despliegue y Orquestación

### 4.1 Docker Swarm

#### Inicialización del Swarm

```bash
# Inicializar Docker Swarm
docker swarm init --advertise-addr <IP_MANAGER>

# Guardar tokens de forma segura (NO en el repositorio)
docker swarm join-token manager -q > /path/to/secure/manager_token
docker swarm join-token worker -q > /path/to/secure/worker_token

# Crear red overlay para servicios
docker network create --driver overlay --attachable phoenix-net
```

#### Despliegue con Secretos

Actualizar el script `deploy-stack.sh` para usar secretos:

```bash
#!/bin/bash

# Phoenix DemiGod - Docker Swarm Stack Deployment Script
# This script deploys the Phoenix DemiGod stack to a Docker Swarm cluster

# Function to handle errors
handle_error() {
  echo "Error: $1"
  exit 1
}

# Check if Docker Swarm is active
if ! docker info | grep -q "Swarm: active"; then
  handle_error "Docker Swarm is not active. Please initialize it first with swarm-init.sh"
fi

echo "Deploying Phoenix DemiGod stack to Docker Swarm..."

# Set environment variables from .env file if it exists
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  # Use set -a to automatically export variables, and then source the .env file
  set -a
  . ./.env
  set +a
fi

# Determine environment
ENVIRONMENT=${1:-production}
echo "Deploying to $ENVIRONMENT environment"

# Set file paths based on environment
case $ENVIRONMENT in
  "production")
    COMPOSE_FILE="docker/docker-compose.prod.yml"
    ENV_FILE=".env.production"
    ;;
  "staging")
    COMPOSE_FILE="docker/docker-compose.staging.yml"
    ENV_FILE=".env.staging"
    ;;
  "development")
    COMPOSE_FILE="docker/docker-compose.dev.yml"
    ENV_FILE=".env.development"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Using production environment"
    COMPOSE_FILE="docker/docker-compose.prod.yml"
    ENV_FILE=".env.production"
    ;;
esac

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
  handle_error "Compose file $COMPOSE_FILE not found!"
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
  handle_error "Environment file $ENV_FILE not found!"
fi

# Create secrets from environment file
echo "Creating secrets from environment file..."
grep -E '^[A-Z_]+=.+$' "$ENV_FILE" | while IFS='=' read -r key value; do
  # Skip comments
  [[ $key == \#* ]] && continue
  
  # Create secret if it doesn't exist
  if ! docker secret inspect "${key,,}" &>/dev/null; then
    echo "$value" | docker secret create "${key,,}" -
    echo "Created secret: ${key,,}"
  else
    echo "Secret ${key,,} already exists"
  fi
done

# Deploy the stack with secrets
echo "Deploying Phoenix DemiGod stack using $COMPOSE_FILE..."
docker stack deploy -c $COMPOSE_FILE --with-registry-auth phoenix || handle_error "Failed to deploy stack"

# Wait for services to be deployed and verify their status
echo "Waiting for services to be deployed..."
sleep 10

echo "Verifying service status..."
SERVICES=$(docker stack services phoenix --format "{{.Name}}")
for SERVICE in $SERVICES; do
  REPLICAS=$(docker service ls --filter "name=$SERVICE" --format "{{.Replicas}}")
  RUNNING_REPLICAS=$(echo $REPLICAS | cut -d'/' -f1)
  TOTAL_REPLICAS=$(echo $REPLICAS | cut -d'/' -f2)
  
  if [ "$RUNNING_REPLICAS" -lt "$TOTAL_REPLICAS" ]; then
    echo "Warning: Service $SERVICE has only $RUNNING_REPLICAS/$TOTAL_REPLICAS replicas running."
  else
    echo "Service $SERVICE is running correctly ($REPLICAS replicas)."
  fi
done

echo ""
echo "Phoenix DemiGod stack deployment completed!"
echo "You can monitor the stack using the monitor-stack.sh script"
```

### 4.2 Kubernetes

#### Actualización de Manifiestos

Actualizar `kubernetes-deploy.yaml` para usar secretos:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: phoenix-agent-secrets
type: Opaque
data:
  # Estos valores deben ser generados con: echo -n "valor" | base64
  DB_PASSWORD: cGFzc3dvcmQ=  # Ejemplo: "password" en base64
  API_KEY: YXBpLWtleS1leGFtcGxl  # Ejemplo: "api-key-example" en base64
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: phoenix-agent-config
data:
  # Variables no sensibles
  OSC_PORT: "9000"
  AUTO_GEN_ENDPOINT: "http://autogen-service:8081/autogen/generate"
  DEMIGOD_AGENT_GENMA: "demigod-agent-service"
  CHAOS_AGENT_GENMA: "chaos-agent-service"
  THANATOS_AGENT_GENMA: "thanatos-agent-service"
---
# Resto del archivo kubernetes-deploy.yaml...
```

#### Script de Despliegue para Kubernetes

Crear un nuevo script `deploy-k8s.sh`:

```bash
#!/bin/bash

# Phoenix DemiGod - Kubernetes Deployment Script

# Function to handle errors
handle_error() {
  echo "Error: $1"
  exit 1
}

# Determine environment
ENVIRONMENT=${1:-production}
echo "Deploying to $ENVIRONMENT environment"

# Set namespace based on environment
case $ENVIRONMENT in
  "production")
    NAMESPACE="phoenix-prod"
    ENV_FILE=".env.production"
    ;;
  "staging")
    NAMESPACE="phoenix-staging"
    ENV_FILE=".env.staging"
    ;;
  "development")
    NAMESPACE="phoenix-dev"
    ENV_FILE=".env.development"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Using production environment"
    NAMESPACE="phoenix-prod"
    ENV_FILE=".env.production"
    ;;
esac

# Check if namespace exists, create if not
if ! kubectl get namespace $NAMESPACE &>/dev/null; then
  echo "Creating namespace $NAMESPACE..."
  kubectl create namespace $NAMESPACE
fi

# Create ConfigMap from environment file
echo "Creating ConfigMap from environment file..."
kubectl create configmap phoenix-agent-config --from-env-file=$ENV_FILE -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets from secure environment file
if [ -f "${ENV_FILE}.secrets" ]; then
  echo "Creating secrets from secure environment file..."
  kubectl create secret generic phoenix-agent-secrets --from-env-file=${ENV_FILE}.secrets -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
else
  echo "Warning: No secrets file found at ${ENV_FILE}.secrets"
fi

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f kubernetes-deploy.yaml -n $NAMESPACE || handle_error "Failed to apply manifests"

# Verify deployment
echo "Verifying deployment..."
kubectl rollout status deployment/demigod-agent-deployment -n $NAMESPACE
kubectl rollout status deployment/chaos-agent-deployment -n $NAMESPACE
kubectl rollout status deployment/thanatos-agent-deployment -n $NAMESPACE

echo ""
echo "Phoenix DemiGod deployment to Kubernetes completed!"
echo "You can monitor the deployment with: kubectl get pods -n $NAMESPACE"
```

### 4.3 Terraform para Infraestructura como Código

Actualizar `main.tf` para usar variables y módulos:

```hcl
# Variables
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"
}

variable "phoenix_api_port" {
  description = "Port for Phoenix API"
  type        = number
  default     = 8000
}

variable "osc_port" {
  description = "Port for OSC"
  type        = number
  default     = 9000
}

# Módulos
module "phoenix_network" {
  source = "./modules/network"
  
  network_name = "phoenix-net-${var.environment}"
}

module "demigod_agent" {
  source = "./modules/agent"
  
  agent_name     = "demigod-agent"
  agent_image    = "demigod-agent:latest"
  environment    = var.environment
  network_id     = module.phoenix_network.network_id
  exposed_port   = var.osc_port
  internal_port  = 9000
  healthcheck    = {
    test     = ["CMD", "curl", "--fail", "http://localhost:9000/health"]
    interval = "30s"
    timeout  = "10s"
    retries  = 5
  }
}

module "chaos_agent" {
  source = "./modules/agent"
  
  agent_name     = "chaos-agent"
  agent_image    = "chaos-agent:latest"
  environment    = var.environment
  network_id     = module.phoenix_network.network_id
  healthcheck    = {
    test     = ["CMD", "pgrep", "-f", "chaos-agent.py"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
}

module "thanatos_agent" {
  source = "./modules/agent"
  
  agent_name     = "thanatos-agent"
  agent_image    = "thanatos-agent:latest"
  environment    = var.environment
  network_id     = module.phoenix_network.network_id
  healthcheck    = {
    test     = ["CMD", "pgrep", "-f", "thanatos-agent.py"]
    interval = "30s"
    timeout  = "10s"
    retries  = 3
  }
}

# Outputs
output "demigod_agent_endpoint" {
  value = "http://localhost:${var.osc_port}"
}
```

## 5. Monitorización y Observabilidad

### 5.1 Prometheus y Grafana

Crear archivo `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'phoenix-agents'
    static_configs:
      - targets: ['demigod-agent:9000', 'chaos-agent:9100', 'thanatos-agent:9100']
```

Crear archivo `monitoring/docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - phoenix-net

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - phoenix-net
    depends_on:
      - prometheus

volumes:
  grafana-data:

networks:
  phoenix-net:
    external: true
```

### 5.2 Logging Centralizado con ELK Stack

Crear archivo `logging/docker-compose.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - phoenix-net

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    networks:
      - phoenix-net
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    networks:
      - phoenix-net
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:

networks:
  phoenix-net:
    external: true
```

### 5.3 Healthchecks y Readiness Probes

Implementar endpoints de health en todos los servicios:

```python
# Ejemplo para FastAPI
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "version": "1.0.0"}
    )

@app.get("/readiness")
async def readiness_check():
    # Verificar conexiones a dependencias
    db_status = check_database_connection()
    redis_status = check_redis_connection()
    
    if db_status and redis_status:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "dependencies": {"database": "connected", "redis": "connected"}}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "dependencies": {"database": "disconnected" if not db_status else "connected", "redis": "disconnected" if not redis_status else "connected"}}
        )
```

## 6. Gestión de Dependencias

### 6.1 Python

Actualizar `requirements.txt` con versiones específicas y separar dependencias de desarrollo:

```text
# requirements.txt - Dependencias de producción
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
autogen==0.4.0
openai==1.47.0
keras==3.5.0
numpy==1.26.4
typer==0.12.5
```

```text
# requirements-dev.txt - Dependencias de desarrollo
-r requirements.txt
pytest==8.3.3
pytest-cov==4.0
