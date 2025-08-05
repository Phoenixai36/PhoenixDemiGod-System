#!/bin/bash
set -euo pipefail

# Phoenix Hydra Migration Recovery Script
# This script provides recovery procedures for failed migration scenarios

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.docker-backup"
PODMAN_COMPOSE_FILE="${PROJECT_ROOT}/infra/podman/podman-compose.yaml"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/compose.yaml"
RECOVERY_LOG="${PROJECT_ROOT}/migration-recovery.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$RECOVERY_LOG"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $1" >> "$RECOVERY_LOG"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$RECOVERY_LOG"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$RECOVERY_LOG"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [RECOVERY_SCENARIO] [OPTIONS]"
    echo ""
    echo "Recovery Scenarios:"
    echo "  failed-build       Recover from failed container builds"
    echo "  failed-startup     Recover from failed service startup"
    echo "  network-issues     Recover from network connectivity problems"
    echo "  volume-issues      Recover from volume mounting problems"
    echo "  permission-issues  Recover from permission-related failures"
    echo "  complete-rollback  Perform complete rollback to Docker"
    echo "  diagnose           Diagnose current system state"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  --force            Force recovery without confirmation"
    echo "  --preserve-data    Preserve data during recovery"
    echo "  --verbose          Show detailed recovery steps"
    echo ""
    echo "This script provides automated recovery for common migration failure scenarios."
}

# Function to initialize recovery logging
init_recovery_log() {
    echo "Phoenix Hydra Migration Recovery Log" > "$RECOVERY_LOG"
    echo "====================================" >> "$RECOVERY_LOG"
    echo "Recovery started: $(date)" >> "$RECOVERY_LOG"
    echo "System: $(uname -s) $(uname -r)" >> "$RECOVERY_LOG"
    echo "User: $(whoami)" >> "$RECOVERY_LOG"
    echo "" >> "$RECOVERY_LOG"
}

# Function to diagnose current system state
diagnose_system() {
    print_status "Diagnosing current system state..."
    
    echo ""
    print_status "=== SYSTEM DIAGNOSIS ==="
    
    # Check Docker status
    print_status "Docker Status:"
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
            local docker_containers=$(docker ps -q | wc -l)
            echo "  - Running containers: $docker_containers"
        else
            print_warning "Docker daemon is not running"
        fi
    else
        print_warning "Docker is not installed"
    fi
    
    # Check Podman status
    print_status "Podman Status:"
    if command -v podman &> /dev/null; then
        if podman info &> /dev/null; then
            print_success "Podman is accessible"
            local podman_containers=$(podman ps -q | wc -l)
            echo "  - Running containers: $podman_containers"
            
            # Check rootless mode
            local rootless=$(podman info --format json 2>/dev/null | grep -o '"rootless":[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "unknown")
            echo "  - Rootless mode: $rootless"
        else
            print_warning "Podman is not accessible"
        fi
    else
        print_warning "Podman is not installed"
    fi
    
    # Check compose files
    print_status "Configuration Files:"
    if [[ -f "$DOCKER_COMPOSE_FILE" ]]; then
        print_success "Docker compose.yaml exists"
    else
        print_warning "Docker compose.yaml missing"
    fi
    
    if [[ -f "$PODMAN_COMPOSE_FILE" ]]; then
        print_success "Podman compose file exists"
    else
        print_warning "Podman compose file missing"
    fi
    
    # Check backup status
    print_status "Backup Status:"
    if [[ -d "$BACKUP_DIR" ]]; then
        print_success "Backup directory exists"
        local backup_files=$(find "$BACKUP_DIR" -type f | wc -l)
        echo "  - Backup files: $backup_files"
    else
        print_error "No backup directory found"
    fi
    
    # Check network status
    print_status "Network Status:"
    local required_ports=("8000" "3000" "8080" "5000")
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            echo "  - Port $port: IN USE"
        else
            echo "  - Port $port: Available"
        fi
    done
    
    # Check data directories
    print_status "Data Directories:"
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    if [[ -d "$phoenix_data_dir" ]]; then
        print_success "Phoenix data directory exists"
        echo "  - Location: $phoenix_data_dir"
        echo "  - Size: $(du -sh "$phoenix_data_dir" 2>/dev/null | cut -f1 || echo "unknown")"
    else
        print_warning "Phoenix data directory missing"
    fi
    
    # Check recent errors in logs
    print_status "Recent Errors:"
    if command -v journalctl &> /dev/null; then
        local recent_errors=$(journalctl --user -u "container-*" --since "1 hour ago" --no-pager -q 2>/dev/null | grep -i error | wc -l || echo "0")
        echo "  - Recent container errors: $recent_errors"
    fi
    
    echo ""
    print_status "Diagnosis complete. Check recovery log: $RECOVERY_LOG"
}

# Function to recover from failed builds
recover_failed_build() {
    print_status "Recovering from failed container builds..."
    
    # Clean up failed build artifacts
    print_status "Cleaning up failed build artifacts..."
    
    if command -v podman &> /dev/null; then
        # Remove dangling images
        local dangling_images=$(podman images -f "dangling=true" -q 2>/dev/null || true)
        if [[ -n "$dangling_images" ]]; then
            print_status "Removing dangling images..."
            echo "$dangling_images" | xargs -r podman rmi || print_warning "Some images could not be removed"
        fi
        
        # Clean build cache
        print_status "Cleaning build cache..."
        podman system prune -f || print_warning "Could not clean system cache"
    fi
    
    # Check Containerfile syntax
    print_status "Validating Containerfiles..."
    local containerfiles=(
        "infra/podman/gap-detector/Containerfile"
        "infra/podman/recurrent-processor/Containerfile"
        "infra/podman/rubik-agent/Containerfile"
        "infra/podman/nginx/Containerfile"
        "infra/podman/analysis-engine/Containerfile"
    )
    
    for containerfile in "${containerfiles[@]}"; do
        local full_path="$PROJECT_ROOT/$containerfile"
        if [[ -f "$full_path" ]]; then
            # Basic syntax check
            if grep -q "^FROM " "$full_path"; then
                print_success "Containerfile syntax OK: $containerfile"
            else
                print_error "Containerfile syntax error: $containerfile"
                print_error "Missing FROM instruction"
            fi
        else
            print_warning "Containerfile not found: $containerfile"
        fi
    done
    
    # Attempt rebuild with verbose output
    print_status "Attempting rebuild with verbose output..."
    cd "$PROJECT_ROOT"
    
    if [[ -f "$PODMAN_COMPOSE_FILE" ]] && command -v podman-compose &> /dev/null; then
        print_status "Building images individually for better error diagnosis..."
        
        # Build each service individually
        local services=("gap-detector" "recurrent-processor" "rubik-agent" "nginx" "analysis-engine")
        for service in "${services[@]}"; do
            print_status "Building $service..."
            if podman-compose -f "$PODMAN_COMPOSE_FILE" build "$service" 2>&1 | tee -a "$RECOVERY_LOG"; then
                print_success "Successfully built $service"
            else
                print_error "Failed to build $service - check logs for details"
            fi
        done
    else
        print_error "Podman compose file not found or podman-compose not available"
        return 1
    fi
}

# Function to recover from failed startup
recover_failed_startup() {
    print_status "Recovering from failed service startup..."
    
    # Stop all services first
    print_status "Stopping all services..."
    
    if command -v podman-compose &> /dev/null && [[ -f "$PODMAN_COMPOSE_FILE" ]]; then
        podman-compose -f "$PODMAN_COMPOSE_FILE" down || print_warning "Some services may not have stopped cleanly"
    fi
    
    # Check for port conflicts
    print_status "Checking for port conflicts..."
    local required_ports=("8000" "3000" "8080" "5000")
    local conflicts=0
    
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port is in use"
            
            # Try to identify the process
            local pid=$(lsof -ti:$port 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 || echo "unknown")
            if [[ "$pid" != "unknown" && "$pid" != "" ]]; then
                local process_name=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
                print_warning "Process using port $port: $process_name (PID: $pid)"
                
                # Offer to kill the process
                echo "Kill process $pid to free port $port? (y/N)"
                read -r response
                if [[ "$response" =~ ^[Yy]$ ]]; then
                    if kill "$pid" 2>/dev/null; then
                        print_success "Process $pid killed"
                        sleep 2
                    else
                        print_warning "Could not kill process $pid"
                    fi
                fi
            fi
            ((conflicts++))
        fi
    done
    
    # Check service dependencies
    print_status "Checking service dependencies..."
    
    # Verify database is accessible
    if command -v podman &> /dev/null; then
        print_status "Starting database service first..."
        if podman-compose -f "$PODMAN_COMPOSE_FILE" up -d db 2>&1 | tee -a "$RECOVERY_LOG"; then
            print_success "Database service started"
            sleep 10
            
            # Test database connectivity
            if podman exec phoenix-hydra_db_1 pg_isready -U windmill_user 2>/dev/null; then
                print_success "Database is accessible"
            else
                print_warning "Database may not be ready yet"
            fi
        else
            print_error "Failed to start database service"
        fi
    fi
    
    # Start services in dependency order
    print_status "Starting services in dependency order..."
    local service_order=("db" "recurrent-processor" "gap-detector" "windmill" "rubik-agent" "nginx")
    
    for service in "${service_order[@]}"; do
        print_status "Starting $service..."
        if podman-compose -f "$PODMAN_COMPOSE_FILE" up -d "$service" 2>&1 | tee -a "$RECOVERY_LOG"; then
            print_success "Started $service"
            sleep 5
        else
            print_error "Failed to start $service"
            
            # Show service logs for diagnosis
            print_status "Showing logs for $service:"
            podman-compose -f "$PODMAN_COMPOSE_FILE" logs "$service" | tail -20
        fi
    done
}

# Function to recover from network issues
recover_network_issues() {
    print_status "Recovering from network connectivity problems..."
    
    # Remove existing networks
    print_status "Cleaning up existing networks..."
    
    local phoenix_networks=$(podman network ls --format "{{.Name}}" | grep "phoenix" || true)
    if [[ -n "$phoenix_networks" ]]; then
        print_status "Removing existing Phoenix networks..."
        echo "$phoenix_networks" | xargs -r podman network rm || print_warning "Some networks could not be removed"
    fi
    
    # Recreate network with explicit configuration
    print_status "Recreating Phoenix network..."
    
    if podman network create \
        --driver bridge \
        --subnet 172.20.0.0/16 \
        --gateway 172.20.0.1 \
        phoenix-hydra_phoenix-net 2>&1 | tee -a "$RECOVERY_LOG"; then
        print_success "Phoenix network recreated"
    else
        print_error "Failed to recreate Phoenix network"
    fi
    
    # Test network connectivity
    print_status "Testing network connectivity..."
    
    # Start a test container to verify network
    if podman run --rm --network phoenix-hydra_phoenix-net alpine:latest ping -c 1 172.20.0.1 &>/dev/null; then
        print_success "Network connectivity verified"
    else
        print_warning "Network connectivity test failed"
    fi
    
    # Check DNS resolution
    print_status "Testing DNS resolution..."
    if podman run --rm --network phoenix-hydra_phoenix-net alpine:latest nslookup google.com &>/dev/null; then
        print_success "DNS resolution working"
    else
        print_warning "DNS resolution may have issues"
    fi
    
    # Restart services with network
    print_status "Restarting services with new network..."
    if [[ -f "$PODMAN_COMPOSE_FILE" ]]; then
        podman-compose -f "$PODMAN_COMPOSE_FILE" down || true
        sleep 5
        podman-compose -f "$PODMAN_COMPOSE_FILE" up -d || print_error "Failed to restart services"
    fi
}

# Function to recover from volume issues
recover_volume_issues() {
    print_status "Recovering from volume mounting problems..."
    
    # Check and fix directory permissions
    print_status "Checking and fixing directory permissions..."
    
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    
    # Create directory structure if missing
    if [[ ! -d "$phoenix_data_dir" ]]; then
        print_status "Creating Phoenix data directory structure..."
        mkdir -p "$phoenix_data_dir"/{db_data,logs,config,nginx_config}
    fi
    
    # Fix permissions
    print_status "Setting correct permissions..."
    chmod 755 "$phoenix_data_dir"
    chmod 700 "$phoenix_data_dir/db_data"
    chmod 755 "$phoenix_data_dir/logs"
    chmod 755 "$phoenix_data_dir/config"
    chmod 755 "$phoenix_data_dir/nginx_config"
    
    # Check SELinux contexts if applicable
    if command -v getenforce &> /dev/null && [[ "$(getenforce)" == "Enforcing" ]]; then
        print_status "Setting SELinux contexts for volumes..."
        chcon -Rt container_file_t "$phoenix_data_dir" 2>/dev/null || print_warning "Could not set SELinux contexts"
    fi
    
    # Test volume mounting
    print_status "Testing volume mounting..."
    
    local test_container="test-volume-$$"
    if podman run --name "$test_container" -v "$phoenix_data_dir/db_data:/test" alpine:latest touch /test/test-file 2>/dev/null; then
        print_success "Volume mounting test successful"
        podman rm "$test_container" &>/dev/null || true
        rm -f "$phoenix_data_dir/db_data/test-file" 2>/dev/null || true
    else
        print_error "Volume mounting test failed"
        podman rm "$test_container" &>/dev/null || true
    fi
    
    # Recreate volumes in compose
    print_status "Recreating volumes in compose..."
    if [[ -f "$PODMAN_COMPOSE_FILE" ]]; then
        podman-compose -f "$PODMAN_COMPOSE_FILE" down -v || true
        sleep 5
        podman-compose -f "$PODMAN_COMPOSE_FILE" up -d || print_error "Failed to restart with volumes"
    fi
}

# Function to recover from permission issues
recover_permission_issues() {
    print_status "Recovering from permission-related failures..."
    
    # Check if running as root (should not be)
    if [[ $EUID -eq 0 ]]; then
        print_error "Running as root - this is not supported for rootless migration"
        print_error "Please run as a regular user"
        return 1
    fi
    
    # Fix user namespace mapping
    print_status "Checking user namespace mapping..."
    
    local current_user=$(whoami)
    if ! grep -q "^${current_user}:" /etc/subuid 2>/dev/null; then
        print_warning "User namespace mapping not configured in /etc/subuid"
        print_warning "Run: sudo usermod --add-subuids 100000-165535 $current_user"
    fi
    
    if ! grep -q "^${current_user}:" /etc/subgid 2>/dev/null; then
        print_warning "User namespace mapping not configured in /etc/subgid"
        print_warning "Run: sudo usermod --add-subgids 100000-165535 $current_user"
    fi
    
    # Reset Podman configuration
    print_status "Resetting Podman configuration..."
    
    local containers_config_dir="${HOME}/.config/containers"
    if [[ -d "$containers_config_dir" ]]; then
        print_status "Backing up existing containers config..."
        mv "$containers_config_dir" "${containers_config_dir}.backup.$(date +%s)" 2>/dev/null || true
    fi
    
    mkdir -p "$containers_config_dir"
    
    # Create new containers.conf with proper settings
    cat > "$containers_config_dir/containers.conf" << EOF
[containers]
userns = "auto"
user = "$(id -u):$(id -g)"
privileged = false
security_opt = ["no-new-privileges:true"]
cgroup_manager = "systemd"
netns = "bridge"

[engine]
privileged = false
runtime = "crun"
default_capabilities = [
    "CHOWN",
    "DAC_OVERRIDE", 
    "FOWNER",
    "FSETID",
    "KILL",
    "NET_BIND_SERVICE",
    "SETFCAP",
    "SETGID",
    "SETPCAP",
    "SETUID",
    "SYS_CHROOT"
]
EOF
    
    print_success "Containers configuration reset"
    
    # Restart Podman system
    print_status "Restarting Podman system..."
    podman system reset --force || print_warning "Could not reset Podman system"
    
    # Test Podman access
    if podman info &>/dev/null; then
        print_success "Podman access restored"
    else
        print_error "Podman access still not working"
    fi
}

# Function to perform complete rollback
complete_rollback() {
    print_status "Performing complete rollback to Docker..."
    
    # Use the dedicated rollback script if available
    local rollback_script="$SCRIPT_DIR/rollback-to-docker.sh"
    if [[ -x "$rollback_script" ]]; then
        print_status "Using dedicated rollback script..."
        "$rollback_script" --force --keep-data
    else
        print_warning "Dedicated rollback script not found, performing manual rollback..."
        
        # Manual rollback steps
        print_status "Stopping Podman services..."
        if [[ -f "$PODMAN_COMPOSE_FILE" ]] && command -v podman-compose &> /dev/null; then
            podman-compose -f "$PODMAN_COMPOSE_FILE" down -v || true
        fi
        
        # Restore Docker configuration
        if [[ -d "$BACKUP_DIR" ]]; then
            print_status "Restoring Docker configuration..."
            cp "$BACKUP_DIR/compose.yaml" "$PROJECT_ROOT/" || print_error "Failed to restore compose.yaml"
            cp "$BACKUP_DIR/deploy.sh" "$PROJECT_ROOT/" || print_error "Failed to restore deploy.sh"
            cp "$BACKUP_DIR/teardown.sh" "$PROJECT_ROOT/" || print_error "Failed to restore teardown.sh"
            cp "$BACKUP_DIR/verify.sh" "$PROJECT_ROOT/" || print_error "Failed to restore verify.sh"
            
            # Restore compose directory
            if [[ -d "$BACKUP_DIR/compose" ]]; then
                rm -rf "$PROJECT_ROOT/compose" 2>/dev/null || true
                cp -r "$BACKUP_DIR/compose" "$PROJECT_ROOT/" || print_error "Failed to restore compose directory"
            fi
            
            print_success "Docker configuration restored"
        else
            print_error "No backup found for rollback"
            return 1
        fi
        
        # Start Docker services
        print_status "Starting Docker services..."
        cd "$PROJECT_ROOT"
        if command -v docker-compose &> /dev/null; then
            docker-compose up -d || print_error "Failed to start Docker services"
        elif docker compose version &> /dev/null 2>&1; then
            docker compose up -d || print_error "Failed to start Docker services"
        else
            print_error "No docker-compose command available"
            return 1
        fi
    fi
    
    print_success "Complete rollback finished"
}

# Main recovery function
main() {
    local scenario=""
    local force=false
    local preserve_data=false
    local verbose=false
    
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
            --preserve-data)
                preserve_data=true
                shift
                ;;
            --verbose)
                verbose=true
                shift
                ;;
            failed-build|failed-startup|network-issues|volume-issues|permission-issues|complete-rollback|diagnose)
                scenario="$1"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Initialize recovery logging
    init_recovery_log
    
    print_status "Starting Phoenix Hydra migration recovery..."
    print_status "Recovery scenario: ${scenario:-"not specified"}"
    echo ""
    
    # If no scenario specified, run diagnosis
    if [[ -z "$scenario" ]]; then
        print_status "No recovery scenario specified, running diagnosis..."
        diagnose_system
        echo ""
        echo "Based on the diagnosis, choose an appropriate recovery scenario:"
        echo "  - failed-build: If container builds are failing"
        echo "  - failed-startup: If services won't start"
        echo "  - network-issues: If services can't communicate"
        echo "  - volume-issues: If data persistence is broken"
        echo "  - permission-issues: If getting permission errors"
        echo "  - complete-rollback: If you want to revert to Docker"
        exit 0
    fi
    
    # Confirm recovery unless forced
    if [[ "$force" != true && "$scenario" != "diagnose" ]]; then
        echo ""
        print_warning "This will attempt to recover from: $scenario"
        if [[ "$preserve_data" == true ]]; then
            print_status "Data will be preserved during recovery."
        else
            print_warning "Data may be lost during recovery."
        fi
        echo ""
        echo "Do you want to continue? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_status "Recovery cancelled by user"
            exit 0
        fi
    fi
    
    # Execute recovery based on scenario
    case "$scenario" in
        "failed-build")
            recover_failed_build
            ;;
        "failed-startup")
            recover_failed_startup
            ;;
        "network-issues")
            recover_network_issues
            ;;
        "volume-issues")
            recover_volume_issues
            ;;
        "permission-issues")
            recover_permission_issues
            ;;
        "complete-rollback")
            complete_rollback
            ;;
        "diagnose")
            diagnose_system
            ;;
        *)
            print_error "Unknown recovery scenario: $scenario"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Recovery procedure completed!"
    print_status "Recovery log available at: $RECOVERY_LOG"
    
    # Suggest next steps
    echo ""
    echo "Next steps:"
    echo "  - Verify services are working: ./verify.sh"
    echo "  - Check service logs: podman-compose logs -f"
    echo "  - If issues persist, try: $0 diagnose"
    echo "  - For complete rollback: $0 complete-rollback"
}

# Handle script interruption
trap 'print_error "Recovery interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"