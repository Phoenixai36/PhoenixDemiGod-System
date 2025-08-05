#!/bin/bash
set -euo pipefail

# Phoenix Hydra Docker Rollback Script
# This script reverts the system from Podman back to Docker configuration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.docker-backup"
PODMAN_COMPOSE_FILE="${PROJECT_ROOT}/infra/podman/podman-compose.yaml"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/compose.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  --force            Force rollback without confirmation"
    echo "  --keep-data        Keep existing data volumes during rollback"
    echo "  --verify-only      Only verify rollback prerequisites"
    echo ""
    echo "This script rolls back Phoenix Hydra from Podman to Docker by:"
    echo "  - Stopping all Podman services"
    echo "  - Restoring Docker configuration from backup"
    echo "  - Migrating data volumes if requested"
    echo "  - Starting Docker services"
    echo "  - Verifying rollback success"
}

# Function to check rollback prerequisites
check_prerequisites() {
    print_status "Checking rollback prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Installation instructions:"
        echo "  Ubuntu/Debian: sudo apt-get install -y docker.io docker-compose"
        echo "  RHEL/CentOS: sudo dnf install -y docker docker-compose"
        echo "  macOS: brew install docker docker-compose"
        echo "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "docker-compose is not installed."
        echo "Install with:"
        echo "  sudo apt-get install docker-compose"
        echo "  pip install docker-compose"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        echo "Start with:"
        echo "  sudo systemctl start docker"
        echo "  sudo service docker start"
        return 1
    fi
    
    # Check if backup exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_error "Docker backup directory not found: $BACKUP_DIR"
        echo "Please ensure you have created a backup before attempting rollback."
        echo "Run: ./scripts/backup-docker-config.sh"
        return 1
    fi
    
    # Verify backup integrity
    local required_files=(
        "compose.yaml"
        "deploy.sh"
        "teardown.sh" 
        "verify.sh"
        "compose/Dockerfile"
        "compose/analysis-engine/Dockerfile"
        "compose/gap-detector/Dockerfile"
        "compose/nginx/Dockerfile"
        "compose/rubik-agent/Dockerfile"
        "compose/nginx/nginx.conf"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$BACKUP_DIR/$file" ]]; then
            print_error "Required backup file missing: $file"
            return 1
        fi
    done
    
    print_success "All prerequisites met"
    return 0
}

# Function to stop Podman services
stop_podman_services() {
    print_status "Stopping Podman services..."
    
    if [[ -f "$PODMAN_COMPOSE_FILE" ]] && command -v podman-compose &> /dev/null; then
        print_status "Stopping Podman services using podman-compose..."
        podman-compose -f "$PODMAN_COMPOSE_FILE" down -v || print_warning "Some Podman services may not have stopped cleanly"
        
        # Stop any remaining containers
        local containers=$(podman ps -q --filter "label=project=phoenix-hydra" 2>/dev/null || true)
        if [[ -n "$containers" ]]; then
            print_status "Stopping remaining Phoenix Hydra containers..."
            echo "$containers" | xargs -r podman stop || print_warning "Some containers may not have stopped"
            echo "$containers" | xargs -r podman rm || print_warning "Some containers may not have been removed"
        fi
        
        # Remove Phoenix Hydra networks
        local networks=$(podman network ls --format "{{.Name}}" | grep "phoenix" || true)
        if [[ -n "$networks" ]]; then
            print_status "Removing Phoenix Hydra networks..."
            echo "$networks" | xargs -r podman network rm || print_warning "Some networks may not have been removed"
        fi
        
        print_success "Podman services stopped"
    else
        print_warning "Podman compose file not found or podman-compose not available"
    fi
}

# Function to backup current Podman data
backup_podman_data() {
    local keep_data="$1"
    
    if [[ "$keep_data" == "true" ]]; then
        print_status "Backing up Podman data for migration..."
        
        local podman_data_dir="${HOME}/.local/share/phoenix-hydra"
        local backup_data_dir="${BACKUP_DIR}/podman-data-$(date +%Y%m%d_%H%M%S)"
        
        if [[ -d "$podman_data_dir" ]]; then
            mkdir -p "$backup_data_dir"
            cp -r "$podman_data_dir"/* "$backup_data_dir/" 2>/dev/null || print_warning "Some data may not have been backed up"
            print_success "Podman data backed up to: $backup_data_dir"
            echo "$backup_data_dir" > "${BACKUP_DIR}/.podman-data-location"
        else
            print_warning "No Podman data directory found to backup"
        fi
    fi
}

# Function to restore Docker configuration
restore_docker_config() {
    print_status "Restoring Docker configuration from backup..."
    
    # Restore main compose file
    cp "$BACKUP_DIR/compose.yaml" "$PROJECT_ROOT/" || {
        print_error "Failed to restore compose.yaml"
        return 1
    }
    
    # Restore deployment scripts
    cp "$BACKUP_DIR/deploy.sh" "$PROJECT_ROOT/" || {
        print_error "Failed to restore deploy.sh"
        return 1
    }
    
    cp "$BACKUP_DIR/teardown.sh" "$PROJECT_ROOT/" || {
        print_error "Failed to restore teardown.sh"
        return 1
    }
    
    cp "$BACKUP_DIR/verify.sh" "$PROJECT_ROOT/" || {
        print_error "Failed to restore verify.sh"
        return 1
    }
    
    # Make scripts executable
    chmod +x "$PROJECT_ROOT/deploy.sh" "$PROJECT_ROOT/teardown.sh" "$PROJECT_ROOT/verify.sh"
    
    # Restore Docker compose directory
    if [[ -d "$BACKUP_DIR/compose" ]]; then
        rm -rf "$PROJECT_ROOT/compose" 2>/dev/null || true
        cp -r "$BACKUP_DIR/compose" "$PROJECT_ROOT/" || {
            print_error "Failed to restore compose directory"
            return 1
        }
    fi
    
    print_success "Docker configuration restored"
}

# Function to migrate data volumes
migrate_data_volumes() {
    local keep_data="$1"
    
    if [[ "$keep_data" == "true" ]]; then
        print_status "Migrating data volumes from Podman to Docker..."
        
        # Check if we have backed up Podman data
        local podman_data_location=""
        if [[ -f "${BACKUP_DIR}/.podman-data-location" ]]; then
            podman_data_location=$(cat "${BACKUP_DIR}/.podman-data-location")
        fi
        
        if [[ -n "$podman_data_location" && -d "$podman_data_location" ]]; then
            # Create Docker volume and copy data
            print_status "Creating Docker volume for database data..."
            
            # Start a temporary container to copy data
            docker volume create phoenix_hydra_db_data || print_warning "Volume may already exist"
            
            # Copy database data if it exists
            if [[ -d "$podman_data_location/db_data" ]]; then
                print_status "Copying database data to Docker volume..."
                docker run --rm -v phoenix_hydra_db_data:/target -v "$podman_data_location/db_data":/source alpine:latest sh -c "cp -r /source/* /target/ 2>/dev/null || true"
                print_success "Database data migrated to Docker volume"
            fi
            
            # Copy nginx config if it exists
            if [[ -d "$podman_data_location/nginx_config" ]]; then
                print_status "Copying nginx configuration..."
                mkdir -p "$PROJECT_ROOT/compose/nginx"
                cp -r "$podman_data_location/nginx_config"/* "$PROJECT_ROOT/compose/nginx/" 2>/dev/null || print_warning "Some nginx config may not have been copied"
                print_success "Nginx configuration migrated"
            fi
        else
            print_warning "No Podman data found to migrate"
        fi
    fi
}

# Function to start Docker services
start_docker_services() {
    print_status "Starting Docker services..."
    
    cd "$PROJECT_ROOT"
    
    # Determine docker-compose command
    local compose_cmd=""
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    elif docker compose version &> /dev/null; then
        compose_cmd="docker compose"
    else
        print_error "No docker-compose command available"
        return 1
    fi
    
    # Build and start services
    print_status "Building Docker images..."
    $compose_cmd build || {
        print_error "Failed to build Docker images"
        return 1
    }
    
    print_status "Starting Docker services..."
    $compose_cmd up -d || {
        print_error "Failed to start Docker services"
        return 1
    }
    
    print_success "Docker services started"
}

# Function to verify rollback success
verify_rollback() {
    print_status "Verifying rollback success..."
    
    cd "$PROJECT_ROOT"
    
    # Wait for services to start
    sleep 15
    
    # Check if verify script exists and run it
    if [[ -x "./verify.sh" ]]; then
        print_status "Running service verification..."
        if ./verify.sh; then
            print_success "All services verified successfully"
        else
            print_warning "Some services may not be ready yet"
        fi
    else
        print_warning "Verify script not found or not executable"
    fi
    
    # Check service endpoints
    local ports_to_check=("8000" "3000" "8080")
    local healthy_services=0
    
    for port in "${ports_to_check[@]}"; do
        local service_name=""
        case $port in
            8000) service_name="gap-detector" ;;
            3000) service_name="windmill" ;;
            8080) service_name="nginx" ;;
        esac
        
        print_status "Checking $service_name on port $port..."
        
        if timeout 10 curl -f -s "http://localhost:$port" >/dev/null 2>&1; then
            print_success "$service_name service is responding on port $port"
            ((healthy_services++))
        else
            print_warning "$service_name service on port $port may not be ready yet"
        fi
    done
    
    # Summary
    print_status "Rollback verification complete"
    echo ""
    echo "Rollback Status:"
    echo "  - Services responding: $healthy_services/${#ports_to_check[@]}"
    echo "  - Configuration: ✅ Docker"
    echo "  - Data migration: $([ -f "${BACKUP_DIR}/.podman-data-location" ] && echo "✅ Completed" || echo "⏭️ Skipped")"
    echo ""
    echo "Docker services are running. You can:"
    echo "  - Check logs: docker-compose logs -f"
    echo "  - Check status: docker-compose ps"
    echo "  - Stop services: docker-compose down"
    echo ""
    echo "Service endpoints:"
    echo "  - Gap Detector: http://localhost:8000"
    echo "  - Windmill: http://localhost:3000"
    echo "  - Nginx: http://localhost:8080"
}

# Function to cleanup rollback artifacts
cleanup_rollback() {
    print_status "Cleaning up rollback artifacts..."
    
    # Remove Podman configuration if rollback was successful
    echo "Do you want to remove Podman configuration? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [[ -d "$PROJECT_ROOT/infra/podman" ]]; then
            rm -rf "$PROJECT_ROOT/infra/podman"
            print_success "Podman configuration removed"
        fi
        
        # Remove Podman data directory
        local podman_data_dir="${HOME}/.local/share/phoenix-hydra"
        if [[ -d "$podman_data_dir" ]]; then
            echo "Do you want to remove Podman data directory? (y/N)"
            read -r data_response
            if [[ "$data_response" =~ ^[Yy]$ ]]; then
                rm -rf "$podman_data_dir"
                print_success "Podman data directory removed"
            fi
        fi
    fi
}

# Main rollback function
main() {
    local force=false
    local keep_data=false
    local verify_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --force)
                force=true
                shift
                ;;
            --keep-data)
                keep_data=true
                shift
                ;;
            --verify-only)
                verify_only=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Phoenix Hydra rollback from Podman to Docker..."
    echo ""
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites not met. Aborting rollback."
        exit 1
    fi
    
    if [[ "$verify_only" == true ]]; then
        print_success "Rollback prerequisites verified successfully"
        exit 0
    fi
    
    # Confirm rollback unless forced
    if [[ "$force" != true ]]; then
        echo ""
        print_warning "This will rollback Phoenix Hydra from Podman to Docker configuration."
        print_warning "All Podman services will be stopped and Docker services will be started."
        if [[ "$keep_data" == true ]]; then
            print_status "Data volumes will be migrated from Podman to Docker."
        else
            print_warning "Data volumes will NOT be migrated. You may lose data."
        fi
        echo ""
        echo "Do you want to continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_status "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Execute rollback steps
    stop_podman_services
    backup_podman_data "$keep_data"
    restore_docker_config
    migrate_data_volumes "$keep_data"
    start_docker_services
    verify_rollback
    cleanup_rollback
    
    print_success "Phoenix Hydra rollback to Docker completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  - Verify all services are working correctly"
    echo "  - Update any CI/CD pipelines to use Docker commands"
    echo "  - Consider removing Podman if no longer needed"
}

# Handle script interruption
trap 'print_error "Rollback interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"