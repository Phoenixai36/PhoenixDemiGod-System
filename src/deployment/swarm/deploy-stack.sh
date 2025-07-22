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

# Check if Docker Swarm is active
check_swarm() {
  section "Checking Docker Swarm Status"
  
  if ! docker info | grep -q "Swarm: active"; then
    error "Docker Swarm is not active. Run ./swarm-init.sh first."
  else
    success "Docker Swarm is active"
  fi
}

# Check if necessary networks exist
check_networks() {
  section "Checking Required Networks"
  
  if ! docker network ls | grep -q "phoenix-network"; then
    warning "Network 'phoenix-network' does not exist. Creating..."
    docker network create --driver overlay --attachable phoenix-network || error "Failed to create phoenix-network"
  else
    success "Network 'phoenix-network' exists"
  fi
  
  if ! docker network ls | grep -q "traefik-public"; then
    warning "Network 'traefik-public' does not exist. Creating..."
    docker network create --driver overlay --attachable traefik-public || error "Failed to create traefik-public"
  else
    success "Network 'traefik-public' exists"
  fi
}

# Deploy the stack
deploy_stack() {
  section "Deploying Phoenix DemiGod Stack"
  
  # Check if docker-stack.yml exists
  if [ ! -f "$(dirname "$0")/../../../docker/docker-compose.yml" ]; then
    error "Stack configuration file not found at $(dirname "$0")/../../../docker/docker-compose.yml"
  fi
  
  # Source environment variables if .env exists
  if [ -f "$(dirname "$0")/../../../.env" ]; then
    echo "Loading environment variables..."
    set -a
    source "$(dirname "$0")/../../../.env"
    set +a
  else
    warning "No .env file found. Using default environment variables."
  fi
  
  # Deploy the stack
  echo "Deploying Phoenix DemiGod stack..."
  docker stack deploy -c "$(dirname "$0")/../../../docker/docker-compose.yml" phoenix-demigod
  
  if [ $? -eq 0 ]; then
    success "Stack deployed successfully"
  else
    error "Failed to deploy stack"
  fi
}

# Check deployment status
check_deployment() {
  section "Checking Deployment Status"
  
  echo "Waiting for services to start..."
  sleep 5
  
  echo "Stack services:"
  docker stack services phoenix-demigod
  
  echo -e "\nStack tasks:"
  docker stack ps phoenix-demigod --no-trunc
}

# Setup DNS entries (local development only)
setup_local_dns() {
  section "Setting Up Local DNS Entries"
  
  if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "staging" ]; then
    echo "Adding DNS entries to /etc/hosts..."
    
    # Get the node's IP address
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
    
    # Check if entries already exist
    if ! grep -q "phoenix-demigod.local" /etc/hosts; then
      echo "Adding entries to /etc/hosts (requires sudo)..."
      
      sudo bash -c "cat >> /etc/hosts << EOF
$IP_ADDRESS phoenix-demigod.local
$IP_ADDRESS n8n.phoenix-demigod.local
$IP_ADDRESS traefik.phoenix-demigod.local
EOF"
      
      if [ $? -eq 0 ]; then
        success "DNS entries added successfully"
      else
        warning "Failed to add DNS entries. Please add them manually."
      fi
    else
      success "DNS entries already exist in /etc/hosts"
    fi
  else
    echo "Production environment detected. Skipping local DNS setup."
    echo "Ensure your DNS is properly configured for production domains."
  fi
}

# Main execution
section "Phoenix DemiGod - Stack Deployment"
echo "This script will deploy the Phoenix DemiGod stack to Docker Swarm."

check_swarm
check_networks
deploy_stack
check_deployment
setup_local_dns

section "Next Steps"
echo "1. Monitor the stack with:"
echo -e "   ${BLUE}docker stack ps phoenix-demigod${NC}"
echo "2. View service logs with:"
echo -e "   ${BLUE}docker service logs phoenix-demigod_phoenix-core${NC}"
echo "3. Access Phoenix DemiGod at:"
echo -e "   ${BLUE}https://phoenix-demigod.local${NC}"
echo "4. Access n8n at:"
echo -e "   ${BLUE}https://n8n.phoenix-demigod.local${NC}"
echo "5. Access Traefik dashboard at:"
echo -e "   ${BLUE}https://traefik.phoenix-demigod.local${NC}"
