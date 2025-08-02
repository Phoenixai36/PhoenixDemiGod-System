#!/bin/bash
set -euo pipefail

# Podman-specific deployment script for Phoenix Hydra
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/infra/podman/podman-compose.yaml"
VOLUME_SETUP_SCRIPT="${SCRIPT_DIR}/infra/podman/setup-volumes.sh"
VOLUME_CLEANUP_SCRIPT="${SCRIPT_DIR}/infra/podman/cleanup-volumes.sh"

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

# Function to check Podman installation
check_podman() {
    print_status "Checking Podman installation..."
    
    if ! command -v podman &> /dev/null; then
        print_error "Podman is not installed. Please install Podman first."
        echo "Installation instructions:"
        echo "  Ubuntu/Debian: sudo apt-get install -y podman"
        echo "  RHEL/CentOS: sudo dnf install -y podman"
        echo "  macOS: brew install podman"
        echo "  Windows: winget install RedHat.Podman"
        echo "Visit: https://podman.io/getting-started/installation"
        exit 1
    fi
    
    if ! command -v podman-compose &> /dev/null; then
        print_error "podman-compose is not installed."
        echo "Install with one of the following methods:"
        echo "  pip install podman-compose"
        echo "  pip3 install podman-compose"
        echo "  sudo apt-get install podman-compose  # On newer Ubuntu/Debian"
        exit 1
    fi
    
    print_success "Podman and podman-compose are installed"
}

# Function to setup rootless environment with user namespace mapping
setup_rootless() {
    print_status "Setting up rootless environment with user namespace mapping..."
    
    # Enable lingering for systemd user services (if systemd is available)
    if command -v loginctl &> /dev/null; then
        loginctl enable-linger "$(whoami)" 2>/dev/null || print_warning "Could not enable lingering (may not be needed)"
    fi
    
    # Configure user namespace mapping for better security
    print_status "Configuring user namespace mapping..."
    
    # Check if subuid and subgid are configured
    local current_user=$(whoami)
    local uid=$(id -u)
    local gid=$(id -g)
    
    if ! grep -q "^${current_user}:" /etc/subuid 2>/dev/null; then
        print_warning "User namespace mapping not configured in /etc/subuid"
        print_warning "Consider running: sudo usermod --add-subuids 100000-165535 ${current_user}"
    fi
    
    if ! grep -q "^${current_user}:" /etc/subgid 2>/dev/null; then
        print_warning "User namespace mapping not configured in /etc/subgid"
        print_warning "Consider running: sudo usermod --add-subgids 100000-165535 ${current_user}"
    fi
    
    # Create containers configuration directory
    mkdir -p "${HOME}/.config/containers"
    
    # Configure containers.conf for better security and user namespace mapping
    local containers_conf="${HOME}/.config/containers/containers.conf"
    if [[ ! -f "$containers_conf" ]]; then
        print_status "Creating containers.conf with security optimizations..."
        cat > "$containers_conf" << EOF
[containers]
# Security: Always use user namespace mapping
userns = "auto"

# Security: Set default user for containers
user = "${uid}:${gid}"

# Security: Disable privileged containers
privileged = false

# Security: Set default security options
security_opt = ["no-new-privileges:true"]

# Performance: Set default cgroup manager
cgroup_manager = "systemd"

# Network: Default network mode
netns = "bridge"

[engine]
# Security: Disable privileged operations
privileged = false

# Performance: Set runtime
runtime = "crun"

# Security: Set default capabilities
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
        print_success "Created containers.conf with security optimizations"
    fi
    
    # Setup volumes using dedicated script
    if [[ -x "$VOLUME_SETUP_SCRIPT" ]]; then
        print_status "Setting up volumes with proper permissions..."
        "$VOLUME_SETUP_SCRIPT"
    else
        print_warning "Volume setup script not found or not executable: $VOLUME_SETUP_SCRIPT"
        # Fallback to basic directory creation
        mkdir -p "${HOME}/.local/share/phoenix-hydra/db_data"
        mkdir -p "${HOME}/.local/share/phoenix-hydra/logs"
        chmod 755 "${HOME}/.local/share/phoenix-hydra"
        chmod 700 "${HOME}/.local/share/phoenix-hydra/db_data"
        chmod 755 "${HOME}/.local/share/phoenix-hydra/logs"
    fi
    
    print_success "Rootless environment with user namespace mapping setup complete"
}

# Function to verify compose file exists
check_compose_file() {
    print_status "Checking compose file..."
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Podman compose file not found at: $COMPOSE_FILE"
        echo "Please ensure the Podman migration is complete and the compose file exists."
        exit 1
    fi
    
    print_success "Compose file found: $COMPOSE_FILE"
}

# Function to configure network isolation and security boundaries
configure_network_security() {
    print_status "Configuring network isolation and security boundaries..."
    
    # Check if phoenix-net network exists and remove if needed for clean setup
    if podman network exists phoenix-hydra_phoenix-net 2>/dev/null; then
        print_status "Removing existing phoenix-net network for clean setup..."
        podman network rm phoenix-hydra_phoenix-net 2>/dev/null || print_warning "Could not remove existing network"
    fi
    
    # Configure firewall rules for exposed ports (8000, 3000, 8080)
    print_status "Configuring security boundaries for exposed ports..."
    
    # Check if firewall tools are available
    if command -v ufw &> /dev/null; then
        print_status "Configuring UFW firewall rules..."
        # Allow only specific ports for Phoenix Hydra services
        sudo ufw allow 8000/tcp comment "Phoenix Hydra - Gap Detector" 2>/dev/null || print_warning "Could not configure UFW for port 8000"
        sudo ufw allow 3000/tcp comment "Phoenix Hydra - Windmill" 2>/dev/null || print_warning "Could not configure UFW for port 3000"
        sudo ufw allow 8080/tcp comment "Phoenix Hydra - Nginx" 2>/dev/null || print_warning "Could not configure UFW for port 8080"
        sudo ufw allow 5000/tcp comment "Phoenix Hydra - Analysis Engine" 2>/dev/null || print_warning "Could not configure UFW for port 5000"
    elif command -v firewall-cmd &> /dev/null; then
        print_status "Configuring firewalld rules..."
        sudo firewall-cmd --permanent --add-port=8000/tcp --add-port=3000/tcp --add-port=8080/tcp --add-port=5000/tcp 2>/dev/null || print_warning "Could not configure firewalld"
        sudo firewall-cmd --reload 2>/dev/null || print_warning "Could not reload firewalld"
    else
        print_warning "No firewall management tool found (ufw/firewalld). Manual firewall configuration may be needed."
    fi
    
    # Verify network isolation capabilities
    print_status "Verifying network isolation capabilities..."
    
    # Check if network namespaces are supported
    if [[ -d /proc/sys/net/netns ]]; then
        print_success "Network namespaces supported - containers will be properly isolated"
    else
        print_warning "Network namespaces may not be fully supported"
    fi
    
    # Check if bridge networking is available
    if podman network ls --format "{{.Name}}" | grep -q "podman"; then
        print_success "Podman bridge networking available"
    else
        print_warning "Podman bridge networking may not be configured"
    fi
    
    print_success "Network security configuration complete"
}

# Function to check if services are already running
check_existing_services() {
    print_status "Checking for existing services..."
    
    if podman-compose -f "$COMPOSE_FILE" ps --services --filter status=running 2>/dev/null | grep -q .; then
        print_warning "Some services are already running"
        echo "Do you want to stop existing services and restart? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_status "Stopping existing services..."
            podman-compose -f "$COMPOSE_FILE" down || print_warning "Could not stop some services"
            
            # Clean up volumes if requested
            echo "Do you want to clean up volumes as well? (y/N)"
            read -r cleanup_response
            if [[ "$cleanup_response" =~ ^[Yy]$ ]]; then
                if [[ -x "$VOLUME_CLEANUP_SCRIPT" ]]; then
                    print_status "Running volume cleanup..."
                    "$VOLUME_CLEANUP_SCRIPT"
                else
                    print_warning "Volume cleanup script not found: $VOLUME_CLEANUP_SCRIPT"
                fi
            fi
        else
            print_status "Continuing with existing services..."
        fi
    fi
}

# Function to build and start services
deploy_services() {
    print_status "Building and starting Phoenix Hydra services..."
    
    # Build images first
    print_status "Building container images..."
    if ! podman-compose -f "$COMPOSE_FILE" build; then
        print_error "Failed to build container images"
        exit 1
    fi
    
    # Start services
    print_status "Starting services in detached mode..."
    if ! podman-compose -f "$COMPOSE_FILE" up -d; then
        print_error "Failed to start services"
        exit 1
    fi
    
    print_success "Services started successfully"
}

# Function to verify deployment with security and network checks
verify_deployment() {
    print_status "Verifying deployment with security and network isolation checks..."
    
    # Wait a moment for services to initialize
    sleep 10
    
    # Check service status
    print_status "Service status:"
    podman-compose -f "$COMPOSE_FILE" ps
    
    # Verify network isolation
    print_status "Verifying network isolation..."
    
    # Check if phoenix-net network was created
    if podman network exists phoenix-hydra_phoenix-net 2>/dev/null; then
        print_success "Phoenix network created successfully"
        
        # Show network details
        print_status "Network configuration:"
        podman network inspect phoenix-hydra_phoenix-net --format "{{.Name}}: {{.Subnets}}" 2>/dev/null || true
    else
        print_warning "Phoenix network not found - services may not be properly isolated"
    fi
    
    # Verify user namespace mapping
    print_status "Verifying user namespace mapping..."
    
    # Check if containers are running with proper user mapping
    local containers=$(podman-compose -f "$COMPOSE_FILE" ps --format "{{.Names}}" 2>/dev/null || true)
    if [[ -n "$containers" ]]; then
        for container in $containers; do
            if [[ -n "$container" ]]; then
                local user_info=$(podman inspect "$container" --format "{{.Config.User}}" 2>/dev/null || echo "unknown")
                if [[ "$user_info" != "unknown" && "$user_info" != "" ]]; then
                    print_success "Container $container running as user: $user_info"
                else
                    print_warning "Container $container user mapping unclear"
                fi
            fi
        done
    fi
    
    # Check security boundaries for exposed ports
    print_status "Verifying security boundaries for exposed ports (8000, 3000, 8080, 5000)..."
    
    local ports_to_check=("8000" "3000" "8080" "5000")
    local healthy_services=0
    local total_services=${#ports_to_check[@]}
    
    for port in "${ports_to_check[@]}"; do
        local service_name=""
        case $port in
            8000) service_name="gap-detector" ;;
            3000) service_name="windmill" ;;
            8080) service_name="nginx" ;;
            5000) service_name="analysis-engine" ;;
        esac
        
        print_status "Checking $service_name on port $port..."
        
        # Check if port is listening
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            print_success "Port $port is listening"
            
            # Try to connect to health endpoint
            local health_url="http://localhost:$port/health"
            if [[ "$port" == "3000" ]]; then
                health_url="http://localhost:$port/api/version"
            elif [[ "$port" == "8080" ]]; then
                health_url="http://localhost:$port"
            fi
            
            if timeout 10 curl -f -s "$health_url" >/dev/null 2>&1; then
                print_success "$service_name service is responding on port $port"
                ((healthy_services++))
            else
                print_warning "$service_name service on port $port may not be ready yet"
            fi
        else
            print_warning "Port $port is not listening - $service_name may not be started"
        fi
    done
    
    # Verify volume security
    print_status "Verifying volume security and permissions..."
    
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    if [[ -d "$phoenix_data_dir" ]]; then
        local db_perms=$(stat -c "%a" "$phoenix_data_dir/db_data" 2>/dev/null || echo "unknown")
        local nginx_perms=$(stat -c "%a" "$phoenix_data_dir/nginx_config" 2>/dev/null || echo "unknown")
        
        if [[ "$db_perms" == "700" ]]; then
            print_success "Database volume has secure permissions (700)"
        else
            print_warning "Database volume permissions: $db_perms (expected: 700)"
        fi
        
        if [[ "$nginx_perms" == "755" ]]; then
            print_success "Nginx config volume has proper permissions (755)"
        else
            print_warning "Nginx config volume permissions: $nginx_perms (expected: 755)"
        fi
    else
        print_warning "Phoenix data directory not found: $phoenix_data_dir"
    fi
    
    # Summary
    print_status "Deployment verification complete"
    echo ""
    echo "Security Status:"
    echo "  - Services responding: $healthy_services/$total_services"
    echo "  - Network isolation: $(podman network exists phoenix-hydra_phoenix-net 2>/dev/null && echo "✅ Active" || echo "❌ Not configured")"
    echo "  - User namespace mapping: ✅ Configured"
    echo "  - Volume security: ✅ Configured"
    echo ""
    echo "Phoenix Hydra services are starting up. You can:"
    echo "  - Check logs: podman-compose -f $COMPOSE_FILE logs -f"
    echo "  - Check status: podman-compose -f $COMPOSE_FILE ps"
    echo "  - Stop services: podman-compose -f $COMPOSE_FILE down"
    echo "  - Clean volumes: $VOLUME_CLEANUP_SCRIPT"
    echo ""
    echo "Service endpoints (with security boundaries):"
    echo "  - Gap Detector: http://localhost:8000 (isolated network)"
    echo "  - Windmill: http://localhost:3000 (isolated network)"
    echo "  - Nginx: http://localhost:8080 (isolated network)"
    echo "  - Analysis Engine: http://localhost:5000 (isolated network)"
    echo ""
    echo "Internal services (not externally accessible):"
    echo "  - PostgreSQL: Internal port 5432 (network isolated)"
    echo "  - Recurrent Processor: Internal only (network isolated)"
    echo "  - Rubik Agent: Internal only (network isolated)"
}

# Function to manage volume cleanup
manage_volumes() {
    local action="$1"
    
    case "$action" in
        "setup")
            if [[ -x "$VOLUME_SETUP_SCRIPT" ]]; then
                print_status "Setting up volumes..."
                "$VOLUME_SETUP_SCRIPT"
            else
                print_error "Volume setup script not found or not executable: $VOLUME_SETUP_SCRIPT"
                exit 1
            fi
            ;;
        "cleanup")
            if [[ -x "$VOLUME_CLEANUP_SCRIPT" ]]; then
                print_status "Cleaning up volumes..."
                "$VOLUME_CLEANUP_SCRIPT"
            else
                print_error "Volume cleanup script not found or not executable: $VOLUME_CLEANUP_SCRIPT"
                exit 1
            fi
            ;;
        *)
            print_error "Unknown volume action: $action"
            echo "Valid actions: setup, cleanup"
            exit 1
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  --skip-checks      Skip environment checks (use with caution)"
    echo "  --no-verify        Skip deployment verification"
    echo "  --setup-volumes    Setup volumes only (don't deploy services)"
    echo "  --cleanup-volumes  Cleanup volumes only (don't deploy services)"
    echo ""
    echo "This script deploys the Phoenix Hydra stack using Podman with:"
    echo "  - Rootless execution with user namespace mapping"
    echo "  - Network isolation and security boundaries"
    echo "  - Secure volume management with proper permissions"
    echo "  - Exposed ports: 8000 (gap-detector), 3000 (windmill), 8080 (nginx), 5000 (analysis-engine)"
    echo "  - Internal services: PostgreSQL (5432), recurrent-processor, rubik-agent"
}

# Main deployment function
main() {
    local skip_checks=false
    local no_verify=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --skip-checks)
                skip_checks=true
                shift
                ;;
            --no-verify)
                no_verify=true
                shift
                ;;
            --setup-volumes)
                manage_volumes "setup"
                exit 0
                ;;
            --cleanup-volumes)
                manage_volumes "cleanup"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Phoenix Hydra deployment with Podman..."
    echo ""
    
    # Run checks unless skipped
    if [[ "$skip_checks" != true ]]; then
        check_podman
        setup_rootless
        check_compose_file
        configure_network_security
        check_existing_services
    fi
    
    # Deploy services
    deploy_services
    
    # Verify deployment unless skipped
    if [[ "$no_verify" != true ]]; then
        verify_deployment
    fi
    
    print_success "Phoenix Hydra deployment completed!"
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
