#!/bin/bash
set -euo pipefail

# Phoenix Hydra Docker Configuration Backup Script
# This script creates a backup of the current Docker configuration before migration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.docker-backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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
    echo "  --force            Overwrite existing backup"
    echo "  --include-data     Include Docker volume data in backup"
    echo "  --verify-only      Only verify what would be backed up"
    echo ""
    echo "This script backs up the current Docker configuration including:"
    echo "  - compose.yaml file"
    echo "  - All Dockerfiles in compose/ directory"
    echo "  - Deployment scripts (deploy.sh, teardown.sh, verify.sh)"
    echo "  - Configuration files (nginx.conf, etc.)"
    echo "  - Optionally: Docker volume data"
}

# Function to check backup prerequisites
check_prerequisites() {
    print_status "Checking backup prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/compose.yaml" ]]; then
        print_error "compose.yaml not found in project root: $PROJECT_ROOT"
        print_error "Please run this script from the Phoenix Hydra project directory"
        return 1
    fi
    
    # Check if Docker is running (for data backup)
    if ! docker info &> /dev/null 2>&1; then
        print_warning "Docker daemon is not running. Data backup will be skipped."
    fi
    
    print_success "Prerequisites checked"
    return 0
}

# Function to create backup directory structure
create_backup_structure() {
    print_status "Creating backup directory structure..."
    
    # Create main backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Create subdirectories
    mkdir -p "$BACKUP_DIR/compose/analysis-engine"
    mkdir -p "$BACKUP_DIR/compose/gap-detector"
    mkdir -p "$BACKUP_DIR/compose/nginx"
    mkdir -p "$BACKUP_DIR/compose/rubik-agent"
    mkdir -p "$BACKUP_DIR/scripts"
    mkdir -p "$BACKUP_DIR/data"
    
    print_success "Backup directory structure created: $BACKUP_DIR"
}

# Function to backup configuration files
backup_configuration() {
    print_status "Backing up Docker configuration files..."
    
    # Backup main compose file
    if [[ -f "$PROJECT_ROOT/compose.yaml" ]]; then
        cp "$PROJECT_ROOT/compose.yaml" "$BACKUP_DIR/"
        print_success "Backed up compose.yaml"
    else
        print_error "compose.yaml not found"
        return 1
    fi
    
    # Backup deployment scripts
    local scripts=("deploy.sh" "teardown.sh" "verify.sh")
    for script in "${scripts[@]}"; do
        if [[ -f "$PROJECT_ROOT/$script" ]]; then
            cp "$PROJECT_ROOT/$script" "$BACKUP_DIR/"
            print_success "Backed up $script"
        else
            print_warning "$script not found, skipping"
        fi
    done
    
    # Backup Dockerfiles
    local dockerfiles=(
        "compose/Dockerfile"
        "compose/analysis-engine/Dockerfile"
        "compose/gap-detector/Dockerfile"
        "compose/nginx/Dockerfile"
        "compose/rubik-agent/Dockerfile"
    )
    
    for dockerfile in "${dockerfiles[@]}"; do
        if [[ -f "$PROJECT_ROOT/$dockerfile" ]]; then
            cp "$PROJECT_ROOT/$dockerfile" "$BACKUP_DIR/$dockerfile"
            print_success "Backed up $dockerfile"
        else
            print_warning "$dockerfile not found, skipping"
        fi
    done
    
    # Backup nginx configuration
    if [[ -f "$PROJECT_ROOT/compose/nginx/nginx.conf" ]]; then
        cp "$PROJECT_ROOT/compose/nginx/nginx.conf" "$BACKUP_DIR/compose/nginx/"
        print_success "Backed up nginx.conf"
    else
        print_warning "nginx.conf not found, skipping"
    fi
    
    # Backup any additional configuration files
    local config_files=(
        "requirements.txt"
        "requirements-analysis-engine.txt"
        "requirements-gap-detector.txt"
        "requirements-recurrent.txt"
        "requirements-rubik-agent.txt"
    )
    
    for config_file in "${config_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$config_file" ]]; then
            cp "$PROJECT_ROOT/$config_file" "$BACKUP_DIR/"
            print_success "Backed up $config_file"
        fi
    done
}

# Function to backup Docker volume data
backup_docker_data() {
    local include_data="$1"
    
    if [[ "$include_data" != "true" ]]; then
        print_status "Skipping Docker volume data backup (not requested)"
        return 0
    fi
    
    print_status "Backing up Docker volume data..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null 2>&1; then
        print_warning "Docker daemon not running, skipping data backup"
        return 0
    fi
    
    # Check if compose services are running
    cd "$PROJECT_ROOT"
    local compose_cmd=""
    if command -v docker-compose &> /dev/null; then
        compose_cmd="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        compose_cmd="docker compose"
    else
        print_warning "No docker-compose command available, skipping data backup"
        return 0
    fi
    
    # Get list of volumes
    local volumes=$($compose_cmd config --volumes 2>/dev/null || true)
    
    if [[ -n "$volumes" ]]; then
        print_status "Found volumes to backup: $volumes"
        
        for volume in $volumes; do
            print_status "Backing up volume: $volume"
            
            # Create volume backup using a temporary container
            local volume_backup_dir="$BACKUP_DIR/data/$volume"
            mkdir -p "$volume_backup_dir"
            
            # Use a temporary container to copy volume data
            if docker run --rm -v "${volume}:/source" -v "$volume_backup_dir:/backup" alpine:latest sh -c "cp -r /source/* /backup/ 2>/dev/null || true"; then
                print_success "Volume $volume backed up successfully"
            else
                print_warning "Failed to backup volume $volume"
            fi
        done
    else
        print_status "No volumes found to backup"
    fi
}

# Function to create backup manifest
create_backup_manifest() {
    print_status "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/backup-manifest.txt"
    
    cat > "$manifest_file" << EOF
Phoenix Hydra Docker Configuration Backup
=========================================

Backup Date: $(date)
Backup Location: $BACKUP_DIR
Project Root: $PROJECT_ROOT

Files Backed Up:
EOF
    
    # List all backed up files
    find "$BACKUP_DIR" -type f -not -name "backup-manifest.txt" | sort | while read -r file; do
        local relative_path="${file#$BACKUP_DIR/}"
        echo "  - $relative_path" >> "$manifest_file"
    done
    
    # Add system information
    cat >> "$manifest_file" << EOF

System Information:
  - OS: $(uname -s) $(uname -r)
  - Docker Version: $(docker --version 2>/dev/null || echo "Not available")
  - Docker Compose Version: $(docker-compose --version 2>/dev/null || docker compose version 2>/dev/null || echo "Not available")
  - User: $(whoami)
  - Hostname: $(hostname)

Backup Integrity:
  - File Count: $(find "$BACKUP_DIR" -type f -not -name "backup-manifest.txt" | wc -l)
  - Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)

Restoration Instructions:
  1. Run: ./scripts/rollback-to-docker.sh
  2. Or manually restore files from this backup directory
  3. Ensure Docker is installed and running
  4. Run: docker-compose up -d

EOF
    
    print_success "Backup manifest created: $manifest_file"
}

# Function to verify backup integrity
verify_backup() {
    print_status "Verifying backup integrity..."
    
    local errors=0
    
    # Check essential files
    local essential_files=(
        "compose.yaml"
        "compose/Dockerfile"
        "compose/analysis-engine/Dockerfile"
        "compose/gap-detector/Dockerfile"
        "compose/nginx/Dockerfile"
        "compose/rubik-agent/Dockerfile"
    )
    
    for file in "${essential_files[@]}"; do
        if [[ ! -f "$BACKUP_DIR/$file" ]]; then
            print_error "Essential file missing from backup: $file"
            ((errors++))
        fi
    done
    
    # Check if backup directory has reasonable size
    local backup_size=$(du -s "$BACKUP_DIR" | cut -f1)
    if [[ $backup_size -lt 10 ]]; then
        print_warning "Backup directory seems unusually small: ${backup_size}KB"
    fi
    
    if [[ $errors -eq 0 ]]; then
        print_success "Backup integrity verified"
        return 0
    else
        print_error "Backup verification failed with $errors errors"
        return 1
    fi
}

# Function to show backup summary
show_backup_summary() {
    print_status "Backup Summary"
    echo ""
    echo "Backup Location: $BACKUP_DIR"
    echo "Backup Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
    echo "Files Backed Up: $(find "$BACKUP_DIR" -type f | wc -l)"
    echo ""
    echo "Configuration Files:"
    find "$BACKUP_DIR" -name "*.yaml" -o -name "Dockerfile" -o -name "*.conf" -o -name "*.sh" | sort | while read -r file; do
        local relative_path="${file#$BACKUP_DIR/}"
        echo "  ✅ $relative_path"
    done
    echo ""
    echo "Data Backup:"
    if [[ -d "$BACKUP_DIR/data" ]] && [[ -n "$(ls -A "$BACKUP_DIR/data" 2>/dev/null)" ]]; then
        echo "  ✅ Docker volume data included"
        ls -la "$BACKUP_DIR/data/"
    else
        echo "  ⏭️ Docker volume data not included"
    fi
    echo ""
    echo "To restore this backup, run:"
    echo "  ./scripts/rollback-to-docker.sh"
    echo ""
    echo "Backup manifest available at:"
    echo "  $BACKUP_DIR/backup-manifest.txt"
}

# Main backup function
main() {
    local force=false
    local include_data=false
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
            --include-data)
                include_data=true
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
    
    print_status "Starting Phoenix Hydra Docker configuration backup..."
    echo ""
    
    # Check prerequisites
    if ! check_prerequisites; then
        print_error "Prerequisites not met. Aborting backup."
        exit 1
    fi
    
    if [[ "$verify_only" == true ]]; then
        print_status "Files that would be backed up:"
        echo ""
        echo "Configuration Files:"
        [[ -f "$PROJECT_ROOT/compose.yaml" ]] && echo "  ✅ compose.yaml"
        [[ -f "$PROJECT_ROOT/deploy.sh" ]] && echo "  ✅ deploy.sh"
        [[ -f "$PROJECT_ROOT/teardown.sh" ]] && echo "  ✅ teardown.sh"
        [[ -f "$PROJECT_ROOT/verify.sh" ]] && echo "  ✅ verify.sh"
        echo ""
        echo "Dockerfiles:"
        [[ -f "$PROJECT_ROOT/compose/Dockerfile" ]] && echo "  ✅ compose/Dockerfile"
        [[ -f "$PROJECT_ROOT/compose/analysis-engine/Dockerfile" ]] && echo "  ✅ compose/analysis-engine/Dockerfile"
        [[ -f "$PROJECT_ROOT/compose/gap-detector/Dockerfile" ]] && echo "  ✅ compose/gap-detector/Dockerfile"
        [[ -f "$PROJECT_ROOT/compose/nginx/Dockerfile" ]] && echo "  ✅ compose/nginx/Dockerfile"
        [[ -f "$PROJECT_ROOT/compose/rubik-agent/Dockerfile" ]] && echo "  ✅ compose/rubik-agent/Dockerfile"
        echo ""
        echo "Additional Files:"
        [[ -f "$PROJECT_ROOT/compose/nginx/nginx.conf" ]] && echo "  ✅ compose/nginx/nginx.conf"
        echo ""
        echo "Backup would be created at: $BACKUP_DIR"
        exit 0
    fi
    
    # Check if backup already exists
    if [[ -d "$BACKUP_DIR" ]] && [[ "$force" != true ]]; then
        print_warning "Backup directory already exists: $BACKUP_DIR"
        echo "Do you want to overwrite the existing backup? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_status "Backup cancelled by user"
            exit 0
        fi
        print_status "Removing existing backup..."
        rm -rf "$BACKUP_DIR"
    fi
    
    # Execute backup steps
    create_backup_structure
    backup_configuration
    backup_docker_data "$include_data"
    create_backup_manifest
    
    # Verify backup
    if verify_backup; then
        show_backup_summary
        print_success "Phoenix Hydra Docker configuration backup completed successfully!"
    else
        print_error "Backup completed with errors. Please review the backup manually."
        exit 1
    fi
}

# Handle script interruption
trap 'print_error "Backup interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"