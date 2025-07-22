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

section "Creating Traefik Network for Docker Swarm"

# Check if running in swarm mode
if ! docker info | grep -q "Swarm: active"; then
    error "Docker swarm is not active. Initialize swarm with 'docker swarm init' before running this script."
fi

# Check if the network already exists
if docker network ls | grep -q "traefik-public"; then
    warning "Network 'traefik-public' already exists."
else
    # Create the overlay network
    echo "Creating 'traefik-public' overlay network..."
    docker network create --driver=overlay --attachable traefik-public
    
    if [ $? -eq 0 ]; then
        success "Successfully created 'traefik-public' network."
    else
        error "Failed to create network."
    fi
fi

# Display network information
echo -e "\nNetwork Information:"
docker network inspect traefik-public --format '{{json .}}' | python3 -m json.tool

success "Traefik network setup complete."
echo -e "You can now deploy services that need to be exposed through Traefik"
echo -e "Make sure services connect to this network and have proper Traefik labels"
