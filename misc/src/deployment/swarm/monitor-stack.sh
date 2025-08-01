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

# Function to display error messages
error() {
  echo -e "${RED}$1${NC}"
}

# Function to display warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}"
}

# Check if stack is deployed
check_stack() {
  section "Checking Stack Status"
  
  if ! docker stack ls | grep -q "phoenix-demigod"; then
    error "Phoenix DemiGod stack not found. Deploy it first with ./deploy-stack.sh"
    exit 1
  else
    success "Phoenix DemiGod stack is deployed"
  fi
}

# Monitor stack services
monitor_services() {
  section "Monitoring Stack Services"
  
  echo "Stack services:"
  docker stack services phoenix-demigod
  
  echo -e "\nStack tasks:"
  docker stack ps phoenix-demigod --format "table {{.Name}}\t{{.Node}}\t{{.CurrentState}}\t{{.Error}}"
}

# Monitor resource usage
monitor_resources() {
  section "Monitoring Resource Usage"
  
  echo "Node resources:"
  docker node ls
  
  echo -e "\nSystem resources:"
  echo "CPU usage:"
  top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}' | awk '{print $0 "%"}'
  
  echo "Memory usage:"
  free -m | awk 'NR==2{printf "%.2f%%\n", $3*100/$2}'
  
  echo "Disk usage:"
  df -h | grep -E '^/dev/[a-z]' | awk '{print $5, "on", $6}'
}

# Check logs for specific services
check_logs() {
  section "Checking Service Logs"
  
  services=("phoenix-core" "n8n" "sphere-orchestrator" "quantum-scraper-internal" "traefik")
  
  for service in "${services[@]}"; do
    echo -e "${BOLD}Recent logs for ${service}:${NC}"
    docker service logs --tail 5 "phoenix-demigod_${service}" 2>&1
    echo -e "\n"
  done
}

# Advanced monitoring for n8n
monitor_n8n() {
  section "Advanced n8n Monitoring"
  
  echo "n8n queue status:"
  n8n_container=$(docker ps --filter "name=phoenix-demigod_n8n" -q | head -1)
  
  if [ -z "$n8n_container" ]; then
    error "No running n8n container found"
  else
    echo "n8n container ID: $n8n_container"
    
    # Check n8n status via Redis
    redis_container=$(docker ps --filter "name=phoenix-demigod_redis" -q | head -1)
    if [ -n "$redis_container" ]; then
      echo -e "\nRedis queue keys:"
      docker exec -it "$redis_container" redis-cli keys "bull:*" 2>/dev/null || echo "Could not connect to Redis"
    else
      warning "Redis container not found"
    fi
  fi
  
  echo -e "\nn8n worker status:"
  docker service ps phoenix-demigod_n8n-worker --no-trunc
}

# Interactive menu
show_menu() {
  section "Phoenix DemiGod Stack Monitor"
  echo "Please select an option:"
  echo "1) View stack services and tasks"
  echo "2) View resource usage"
  echo "3) View service logs"
  echo "4) Advanced n8n monitoring"
  echo "5) Continuous monitoring (updates every 5s)"
  echo "q) Quit"
  
  read -p "Enter your choice: " choice
  
  case $choice in
    1) monitor_services ;;
    2) monitor_resources ;;
    3) check_logs ;;
    4) monitor_n8n ;;
    5) 
      clear
      echo "Continuous monitoring (press Ctrl+C to stop)..."
      while true; do
        clear
        date
        monitor_services
        echo
        monitor_resources
        sleep 5
      done
      ;;
    q) exit 0 ;;
    *) echo "Invalid option. Please try again." ;;
  esac
  
  echo
  read -p "Press Enter to continue..."
  clear
  show_menu
}

# Main execution
clear
check_stack
show_menu
