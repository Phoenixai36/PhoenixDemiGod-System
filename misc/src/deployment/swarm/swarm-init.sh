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

# Initialize Docker Swarm on the manager node
init_swarm_manager() {
  section "Initializing Docker Swarm Manager"
  
  # Check if already in swarm mode
  if docker info | grep -q "Swarm: active"; then
    echo "Node is already part of a swarm. Leaving current swarm..."
    docker swarm leave --force || error "Failed to leave current swarm"
    
    echo "Initializing new swarm..."
    # Get public-facing IP address
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    docker swarm init --advertise-addr $IP_ADDRESS || error "Failed to initialize new swarm"
    success "Swarm initialized"
    
    # Get tokens
    manager_token=$(docker swarm join-token manager -q)
    worker_token=$(docker swarm join-token worker -q)
  else
    echo "Initializing new swarm..."
    # Get public-facing IP address
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    docker swarm init --advertise-addr $IP_ADDRESS || error "Failed to initialize swarm"
    success "Swarm initialized"
    
    # Get tokens
    manager_token=$(docker swarm join-token manager -q)
    worker_token=$(docker swarm join-token worker -q)
  fi
  
  echo "Manager join token: $manager_token"
  echo "Worker join token: $worker_token"
  
  # Save tokens to files for later use
  echo $manager_token > .manager_token
  echo $worker_token > .worker_token
  chmod 600 .manager_token .worker_token
  
  # Create attachable overlay network
  echo "Creating phoenix-network..."
  docker network create --driver overlay --attachable phoenix-network || warning "Network may already exist"

  # Create traefik network
  echo "Creating traefik-public network..."
  docker network create --driver overlay --attachable traefik-public || warning "Network may already exist"
}

# Create Docker configs
setup_configs() {
  section "Setting up Docker Configs"
  
  # Check for existing configs
  if docker config ls | grep -q "traefik-conf"; then
    warning "Config 'traefik-conf' already exists. Using existing config."
  else
    # Create traefik config
    echo "Creating Traefik configuration..."
    if [ -f "$(dirname "$0")/../n8n_config/traefik-config.toml" ]; then
      docker config create traefik-conf "$(dirname "$0")/../n8n_config/traefik-config.toml"
      success "Created Traefik configuration"
    else
      warning "Traefik config file not found. Skipping."
    fi
  fi

  # Set up dynamic config
  if docker config ls | grep -q "traefik-dynamic-conf"; then
    warning "Config 'traefik-dynamic-conf' already exists. Using existing config."
  else
    # Create dynamic config
    echo "Creating Traefik dynamic configuration..."
    if [ -f "$(dirname "$0")/../n8n_config/dynamic-conf.toml" ]; then
      docker config create traefik-dynamic-conf "$(dirname "$0")/../n8n_config/dynamic-conf.toml"
      success "Created Traefik dynamic configuration"
    else
      warning "Traefik dynamic config file not found. Skipping."
    fi
  fi
}

# Set up Docker secrets
setup_secrets() {
  section "Setting up Docker Secrets"
  
  # Create DB password secret
  if docker secret ls | grep -q "postgres-password"; then
    warning "Secret 'postgres-password' already exists. Using existing secret."
  else
    echo "Creating PostgreSQL password secret..."
    echo "ph03n1xDem1g0d" | docker secret create postgres-password -
    success "Created PostgreSQL password secret"
  fi
  
  # Create n8n admin password secret
  if docker secret ls | grep -q "n8n-admin-password"; then
    warning "Secret 'n8n-admin-password' already exists. Using existing secret."
  else
    echo "Creating n8n admin password secret..."
    echo "ph03n1xDem1g0d" | docker secret create n8n-admin-password -
    success "Created n8n admin password secret"
  fi
}

# Main execution
section "Phoenix DemiGod - Docker Swarm Initialization"
echo "This script will initialize a Docker Swarm and prepare for Phoenix DemiGod deployment."

init_swarm_manager
setup_configs
setup_secrets

section "Next Steps"
echo "1. To add worker nodes, run this on each worker:"
echo -e "   ${BLUE}docker swarm join --token $(cat .worker_token) $(hostname -I | awk '{print $1}'):2377${NC}"
echo "2. To add manager nodes, run this on each manager:"
echo -e "   ${BLUE}docker swarm join --token $(cat .manager_token) $(hostname -I | awk '{print $1}'):2377${NC}"
echo "3. Deploy the stack with:"
echo -e "   ${BLUE}./deploy-stack.sh${NC}"
echo "4. Access Traefik dashboard at:"
echo -e "   ${BLUE}https://traefik.phoenix-demigod.local${NC}"
echo "5. Access n8n at:"
echo -e "   ${BLUE}https://n8n.phoenix-demigod.local${NC}"
