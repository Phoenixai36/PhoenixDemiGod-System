#!/bin/bash

# Color definitions for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to display section headers
section() {
  echo -e "${BOLD}${BLUE}$1${NC}"
}

# Function to display success messages
success() {
  echo -e "${GREEN}$1${NC}"
}

# Function to display error messages and exit
error() {
  echo -e "${RED}$1${NC}"
  exit 1
}

# Function to display warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}"
}

# Configuration Setup
section "n8n Queue Mode Configuration Setup"

echo "This script sets up n8n in queue mode for Phoenix DemiGod"

# Create directory for n8n configuration if it doesn't exist
if [ ! -d "n8n_config" ]; then
    mkdir -p n8n_config
    success "Created n8n_config directory"
fi

# Create .env file for n8n if it doesn't exist
if [ ! -f "n8n_config/.env" ]; then
    cat > n8n_config/.env << EOF
# n8n Environment Variables

# Database configuration
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=postgres
DB_POSTGRESDB_PASSWORD=ph03n1xDem1g0d

# Queue mode configuration
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
QUEUE_BULL_REDIS_DB=0
QUEUE_HEALTH_CHECK_ACTIVE=true

# Worker configuration
WORKERS_COUNT=4
MAX_PARALLEL_EXECUTIONS=4

# Base URL configuration
N8N_PROTOCOL=http
N8N_HOST=n8n
N8N_PORT=5678
N8N_PATH=/

# Security
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=ph03n1xDem1g0d
N8N_JWT_AUTH_ACTIVE=true
N8N_JWT_AUTH_HEADER=Authorization
N8N_JWT_AUTH_EXPIRY_TIME=12h

# Webhook configuration for multi-host
WEBHOOK_URL=\${N8N_PROTOCOL}://\${N8N_HOST}:\${N8N_PORT}
WEBHOOK_TUNNEL_URL=\${N8N_PROTOCOL}://\${N8N_HOST}:\${N8N_PORT}

# Logging
N8N_LOG_LEVEL=info
EOF
    success "Created n8n environment file with queue mode settings"
fi

# Create a Docker Compose file for local testing if it doesn't exist
if [ ! -f "n8n_config/docker-compose.yml" ]; then
    cat > n8n_config/docker-compose.yml << EOF
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=ph03n1xDem1g0d
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_HEALTH_CHECK_ACTIVE=true
      - WORKERS_COUNT=4
      - MAX_PARALLEL_EXECUTIONS=4
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=ph03n1xDem1g0d
      - NODE_ENV=production
      - WEBHOOK_URL=http://n8n:5678/
      - WEBHOOK_TUNNEL_URL=http://n8n:5678/
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
      - redis
    networks:
      - n8n-network

  n8n-worker:
    image: n8nio/n8n:latest
    restart: always
    command: worker
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=ph03n1xDem1g0d
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_HEALTH_CHECK_ACTIVE=true
      - WORKERS_COUNT=4
      - MAX_PARALLEL_EXECUTIONS=4
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=ph03n1xDem1g0d
      - NODE_ENV=production
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres
      - redis
      - n8n
    networks:
      - n8n-network

  postgres:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=ph03n1xDem1g0d
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - n8n-network

  redis:
    image: redis:6-alpine
    restart: always
    networks:
      - n8n-network
    volumes:
      - redis_data:/data

networks:
  n8n-network:

volumes:
  n8n_data:
  postgres_data:
  redis_data:
EOF
    success "Created Docker Compose file for local n8n testing with queue mode"
fi

# Create n8n Docker Stack file for Swarm
if [ ! -f "n8n_config/docker-stack.yml" ]; then
    cat > n8n_config/docker-stack.yml << EOF
version: '3.8'

services:
  traefik:
    image: traefik:v2.9
    command:
      - "--api.dashboard=true"
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.swarmMode=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=traefik-public"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@phoenix-demigod.local"
      - "--certificatesresolvers.letsencrypt.acme.storage=/certificates/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_certificates:/certificates
    deploy:
      placement:
        constraints:
          - node.role == manager
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.traefik-secure.entrypoints=websecure"
        - "traefik.http.routers.traefik-secure.rule=Host(\`traefik.phoenix-demigod.local\`)"
        - "traefik.http.routers.traefik-secure.service=api@internal"
        - "traefik.http.routers.traefik-secure.middlewares=auth"
        - "traefik.http.middlewares.auth.basicauth.users=admin:\$apr1\$ruca84Hq\$\$mbjdMZpxBhuM3NW14/M0f/"
    networks:
      - traefik-public

  n8n:
    image: n8nio/n8n:latest
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=ph03n1xDem1g0d
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_HEALTH_CHECK_ACTIVE=true
      - WEBHOOK_URL=https://n8n.phoenix-demigod.local/
      - WEBHOOK_TUNNEL_URL=https://n8n.phoenix-demigod.local/
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=ph03n1xDem1g0d
      - NODE_ENV=production
    volumes:
      - n8n_data:/home/node/.n8n
    deploy:
      replicas: 1
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.n8n.rule=Host(\`n8n.phoenix-demigod.local\`)"
        - "traefik.http.routers.n8n.entrypoints=websecure"
        - "traefik.http.routers.n8n.tls.certresolver=letsencrypt"
        - "traefik.http.services.n8n.loadbalancer.server.port=5678"
    depends_on:
      - postgres
      - redis
    networks:
      - traefik-public
      - backend

  n8n-worker:
    image: n8nio/n8n:latest
    command: worker
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=ph03n1xDem1g0d
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_HEALTH_CHECK_ACTIVE=true
      - NODE_ENV=production
    volumes:
      - n8n_data:/home/node/.n8n
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    depends_on:
      - postgres
      - redis
      - n8n
    networks:
      - backend

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=ph03n1xDem1g0d
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      placement:
        constraints:
          - node.role == manager
      restart_policy:
        condition: on-failure
    networks:
      - backend

  redis:
    image: redis:6-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    deploy:
      placement:
        constraints:
          - node.role == manager
      restart_policy:
        condition: on-failure
    networks:
      - backend

networks:
  traefik-public:
    external: true
  backend:
    driver: overlay
    internal: true

volumes:
  traefik_certificates:
  n8n_data:
  postgres_data:
  redis_data:
EOF
    success "Created Docker Stack file for Swarm deployment with queue mode"
fi

# Create script to check n8n worker and queue status
if [ ! -f "n8n_config/check-queue-status.sh" ]; then
    cat > n8n_config/check-queue-status.sh << EOF
#!/bin/bash

# Script to check n8n queue status and worker health

echo "Checking n8n Queue Status"
echo "========================="

# Check Redis queue status
echo "Redis Queue Status:"
docker exec -it \$(docker ps --filter name=redis -q) redis-cli -c KEYS "bull:*"
docker exec -it \$(docker ps --filter name=redis -q) redis-cli -c LLEN "bull:queue:webhook"
docker exec -it \$(docker ps --filter name=redis -q) redis-cli -c LLEN "bull:queue:workflow"

# Check worker status
echo -e "\nWorker Status:"
docker service ps n8n-worker

# Check n8n logs for queue info
echo -e "\nRecent queue processing logs:"
docker service logs --tail 20 n8n 2>&1 | grep -i "queue\|worker\|execution"

echo -e "\nHealth check complete"
EOF
    chmod +x n8n_config/check-queue-status.sh
    success "Created queue status check script"
fi

section "Setup Complete"
echo "The n8n queue mode configuration is now ready."
echo -e "${BLUE}To start n8n locally with Docker Compose:${NC}"
echo "  cd n8n_config && docker-compose up -d"
echo -e "${BLUE}To deploy to Docker Swarm:${NC}"
echo "  docker stack deploy -c n8n_config/docker-stack.yml n8n-stack"
echo -e "${BLUE}To check queue status:${NC}"
echo "  ./n8n_config/check-queue-status.sh"
