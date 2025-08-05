#!/bin/bash
set -euo pipefail

# Phoenix Hydra Migration Prerequisites Validation Script
# This script validates that all prerequisites are met before migrating from Docker to Podman

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Global counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# Function to record check result
record_check() {
    local status="$1"
    case "$status" in
        "pass")
            ((CHECKS_PASSED++))
            ;;
        "fail")
            ((CHECKS_FAILED++))
            ;;
        "warning")
            ((CHECKS_WARNING++))
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help         Show this help message"
    echo "  --fix-issues       Attempt to fix detected issues automatically"
    echo "  --detailed         Show detailed information for each check"
    echo "  --export-report    Export validation report to file"
    echo ""
    echo "This script validates prerequisites for migrating Phoenix Hydra from Docker to Podman:"
    echo "  - System requirements and compatibility"
    echo "  - Docker configuration and services"
    echo "  - Podman installation and setup"
    echo "  - File system permissions and structure"
    echo "  - Network and security requirements"
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    # Check operating system
    local os_name=$(uname -s)
    local os_version=$(uname -r)
    
    case "$os_name" in
        "Linux")
            print_success "Operating System: Linux $os_version ✅"
            record_check "pass"
            
            # Check for systemd (recommended for rootless)
            if systemctl --version &> /dev/null; then
                print_success "Systemd available ✅"
                record_check "pass"
            else
                print_warning "Systemd not available - some features may be limited"
                record_check "warning"
            fi
            ;;
        "Darwin")
            print_success "Operating System: macOS $os_version ✅"
            print_warning "macOS support for rootless Podman may have limitations"
            record_check "warning"
            ;;
        *)
            print_error "Unsupported operating system: $os_name"
            print_error "Podman rootless mode works best on Linux"
            record_check "fail"
            ;;
    esac
    
    # Check available memory
    local memory_kb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
    local memory_gb=$((memory_kb / 1024 / 1024))
    
    if [[ $memory_gb -ge 4 ]]; then
        print_success "Available Memory: ${memory_gb}GB ✅"
        record_check "pass"
    elif [[ $memory_gb -ge 2 ]]; then
        print_warning "Available Memory: ${memory_gb}GB (minimum met, 4GB+ recommended)"
        record_check "warning"
    else
        print_error "Available Memory: ${memory_gb}GB (insufficient, minimum 2GB required)"
        record_check "fail"
    fi
    
    # Check available disk space
    local disk_space=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    local disk_space_gb=$((disk_space / 1024 / 1024))
    
    if [[ $disk_space_gb -ge 10 ]]; then
        print_success "Available Disk Space: ${disk_space_gb}GB ✅"
        record_check "pass"
    elif [[ $disk_space_gb -ge 5 ]]; then
        print_warning "Available Disk Space: ${disk_space_gb}GB (minimum met, 10GB+ recommended)"
        record_check "warning"
    else
        print_error "Available Disk Space: ${disk_space_gb}GB (insufficient, minimum 5GB required)"
        record_check "fail"
    fi
}

# Function to check Docker configuration
check_docker_configuration() {
    print_status "Checking current Docker configuration..."
    
    # Check if Docker is installed
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version 2>/dev/null || echo "unknown")
        print_success "Docker installed: $docker_version ✅"
        record_check "pass"
    else
        print_error "Docker not installed"
        record_check "fail"
        return
    fi
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_success "Docker daemon running ✅"
        record_check "pass"
    else
        print_error "Docker daemon not running"
        record_check "fail"
        return
    fi
    
    # Check docker-compose
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
        local compose_version=$(docker-compose --version 2>/dev/null || docker compose version 2>/dev/null || echo "unknown")
        print_success "Docker Compose available: $compose_version ✅"
        record_check "pass"
    else
        print_error "Docker Compose not available"
        record_check "fail"
    fi
    
    # Check if Phoenix Hydra services are running
    cd "$PROJECT_ROOT"
    if [[ -f "compose.yaml" ]]; then
        print_success "Phoenix Hydra compose.yaml found ✅"
        record_check "pass"
        
        # Check service status
        local compose_cmd=""
        if command -v docker-compose &> /dev/null; then
            compose_cmd="docker-compose"
        elif docker compose version &> /dev/null 2>&1; then
            compose_cmd="docker compose"
        fi
        
        if [[ -n "$compose_cmd" ]]; then
            local running_services=$($compose_cmd ps --services --filter status=running 2>/dev/null | wc -l || echo "0")
            if [[ $running_services -gt 0 ]]; then
                print_success "Phoenix Hydra services running: $running_services ✅"
                record_check "pass"
            else
                print_warning "No Phoenix Hydra services currently running"
                record_check "warning"
            fi
        fi
    else
        print_error "Phoenix Hydra compose.yaml not found"
        record_check "fail"
    fi
}

# Function to check Podman installation
check_podman_installation() {
    print_status "Checking Podman installation and configuration..."
    
    # Check if Podman is installed
    if command -v podman &> /dev/null; then
        local podman_version=$(podman --version 2>/dev/null || echo "unknown")
        print_success "Podman installed: $podman_version ✅"
        record_check "pass"
    else
        print_error "Podman not installed"
        print_error "Install with: sudo apt-get install podman (Ubuntu/Debian)"
        print_error "Or visit: https://podman.io/getting-started/installation"
        record_check "fail"
        return
    fi
    
    # Check podman-compose
    if command -v podman-compose &> /dev/null; then
        local podman_compose_version=$(podman-compose --version 2>/dev/null || echo "unknown")
        print_success "Podman Compose installed: $podman_compose_version ✅"
        record_check "pass"
    else
        print_error "Podman Compose not installed"
        print_error "Install with: pip install podman-compose"
        record_check "fail"
    fi
    
    # Check Podman configuration
    if podman info &> /dev/null; then
        print_success "Podman daemon accessible ✅"
        record_check "pass"
        
        # Check if running rootless
        local podman_info=$(podman info --format json 2>/dev/null || echo "{}")
        local rootless=$(echo "$podman_info" | grep -o '"rootless":[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "unknown")
        
        if [[ "$rootless" == "true" ]]; then
            print_success "Podman running in rootless mode ✅"
            record_check "pass"
        else
            print_warning "Podman not running in rootless mode"
            record_check "warning"
        fi
    else
        print_error "Cannot access Podman daemon"
        record_check "fail"
    fi
    
    # Check user namespace configuration
    local current_user=$(whoami)
    if grep -q "^${current_user}:" /etc/subuid 2>/dev/null && grep -q "^${current_user}:" /etc/subgid 2>/dev/null; then
        print_success "User namespace mapping configured ✅"
        record_check "pass"
    else
        print_warning "User namespace mapping not configured"
        print_warning "Consider running: sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $current_user"
        record_check "warning"
    fi
}

# Function to check file system permissions
check_filesystem_permissions() {
    print_status "Checking file system permissions and structure..."
    
    # Check project directory permissions
    if [[ -r "$PROJECT_ROOT" && -w "$PROJECT_ROOT" ]]; then
        print_success "Project directory accessible ✅"
        record_check "pass"
    else
        print_error "Project directory not accessible: $PROJECT_ROOT"
        record_check "fail"
    fi
    
    # Check if user can create directories in home
    local test_dir="${HOME}/.test-phoenix-migration-$$"
    if mkdir "$test_dir" 2>/dev/null && rmdir "$test_dir" 2>/dev/null; then
        print_success "Home directory writable ✅"
        record_check "pass"
    else
        print_error "Cannot create directories in home directory"
        record_check "fail"
    fi
    
    # Check existing Phoenix Hydra data
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    if [[ -d "$phoenix_data_dir" ]]; then
        print_warning "Existing Phoenix Hydra data directory found: $phoenix_data_dir"
        print_warning "Migration may overwrite existing data"
        record_check "warning"
    else
        print_success "No conflicting data directories found ✅"
        record_check "pass"
    fi
    
    # Check containers configuration directory
    local containers_config_dir="${HOME}/.config/containers"
    if [[ -d "$containers_config_dir" ]]; then
        if [[ -w "$containers_config_dir" ]]; then
            print_success "Containers config directory accessible ✅"
            record_check "pass"
        else
            print_error "Containers config directory not writable: $containers_config_dir"
            record_check "fail"
        fi
    else
        print_success "Containers config directory will be created ✅"
        record_check "pass"
    fi
}

# Function to check network requirements
check_network_requirements() {
    print_status "Checking network requirements..."
    
    # Check if required ports are available
    local required_ports=("8000" "3000" "8080" "5000")
    local port_conflicts=0
    
    for port in "${required_ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            print_warning "Port $port is currently in use"
            ((port_conflicts++))
            record_check "warning"
        else
            print_success "Port $port available ✅"
            record_check "pass"
        fi
    done
    
    if [[ $port_conflicts -eq 0 ]]; then
        print_success "All required ports available ✅"
    else
        print_warning "$port_conflicts ports have conflicts - may need to stop services"
    fi
    
    # Check network namespace support
    if [[ -d /proc/sys/net/netns ]]; then
        print_success "Network namespaces supported ✅"
        record_check "pass"
    else
        print_warning "Network namespaces may not be fully supported"
        record_check "warning"
    fi
    
    # Check bridge networking
    if ip link show type bridge &> /dev/null; then
        print_success "Bridge networking supported ✅"
        record_check "pass"
    else
        print_warning "Bridge networking may not be available"
        record_check "warning"
    fi
}

# Function to check security requirements
check_security_requirements() {
    print_status "Checking security requirements..."
    
    # Check if running as root (should not be)
    if [[ $EUID -eq 0 ]]; then
        print_error "Running as root - rootless migration not possible"
        print_error "Please run as a regular user"
        record_check "fail"
    else
        print_success "Running as non-root user ✅"
        record_check "pass"
    fi
    
    # Check SELinux status (if applicable)
    if command -v getenforce &> /dev/null; then
        local selinux_status=$(getenforce 2>/dev/null || echo "unknown")
        case "$selinux_status" in
            "Enforcing")
                print_warning "SELinux is enforcing - may require additional configuration"
                record_check "warning"
                ;;
            "Permissive")
                print_success "SELinux is permissive ✅"
                record_check "pass"
                ;;
            "Disabled")
                print_success "SELinux is disabled ✅"
                record_check "pass"
                ;;
            *)
                print_status "SELinux status unknown"
                record_check "pass"
                ;;
        esac
    fi
    
    # Check AppArmor status (if applicable)
    if command -v aa-status &> /dev/null; then
        if aa-status --enabled 2>/dev/null; then
            print_warning "AppArmor is enabled - may require additional configuration"
            record_check "warning"
        else
            print_success "AppArmor not restricting containers ✅"
            record_check "pass"
        fi
    fi
    
    # Check cgroup version
    if [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
        print_success "Cgroups v2 available ✅"
        record_check "pass"
    elif [[ -d /sys/fs/cgroup/memory ]]; then
        print_warning "Cgroups v1 detected - v2 recommended for better rootless support"
        record_check "warning"
    else
        print_error "Cgroups not properly configured"
        record_check "fail"
    fi
}

# Function to check backup requirements
check_backup_requirements() {
    print_status "Checking backup requirements..."
    
    # Check if backup script exists
    if [[ -x "$SCRIPT_DIR/backup-docker-config.sh" ]]; then
        print_success "Backup script available ✅"
        record_check "pass"
    else
        print_error "Backup script not found or not executable: $SCRIPT_DIR/backup-docker-config.sh"
        record_check "fail"
    fi
    
    # Check available space for backup
    local backup_dir="${PROJECT_ROOT}/.docker-backup"
    local parent_dir=$(dirname "$backup_dir")
    local available_space=$(df "$parent_dir" | tail -1 | awk '{print $4}')
    local available_space_mb=$((available_space / 1024))
    
    if [[ $available_space_mb -ge 100 ]]; then
        print_success "Sufficient space for backup: ${available_space_mb}MB ✅"
        record_check "pass"
    else
        print_error "Insufficient space for backup: ${available_space_mb}MB (minimum 100MB required)"
        record_check "fail"
    fi
    
    # Check if existing backup exists
    if [[ -d "$backup_dir" ]]; then
        print_warning "Existing backup found: $backup_dir"
        print_warning "Backup may be overwritten during migration"
        record_check "warning"
    else
        print_success "No conflicting backup directory ✅"
        record_check "pass"
    fi
}

# Function to generate validation report
generate_report() {
    local export_file="$1"
    
    local report_content="Phoenix Hydra Migration Prerequisites Validation Report
================================================================

Validation Date: $(date)
System: $(uname -s) $(uname -r)
User: $(whoami)
Project Root: $PROJECT_ROOT

Summary:
--------
✅ Checks Passed: $CHECKS_PASSED
⚠️  Warnings: $CHECKS_WARNING
❌ Checks Failed: $CHECKS_FAILED

Total Checks: $((CHECKS_PASSED + CHECKS_WARNING + CHECKS_FAILED))

Migration Readiness:
"

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        if [[ $CHECKS_WARNING -eq 0 ]]; then
            report_content+="🟢 READY - All prerequisites met, migration can proceed safely"
        else
            report_content+="🟡 READY WITH WARNINGS - Migration can proceed but review warnings"
        fi
    else
        report_content+="🔴 NOT READY - Critical issues must be resolved before migration"
    fi

    report_content+="

Recommendations:
---------------"

    if [[ $CHECKS_FAILED -gt 0 ]]; then
        report_content+="
1. Resolve all failed checks before attempting migration
2. Install missing dependencies (Podman, podman-compose)
3. Configure user namespace mapping if needed
4. Ensure sufficient system resources"
    fi

    if [[ $CHECKS_WARNING -gt 0 ]]; then
        report_content+="
1. Review all warnings and consider addressing them
2. Test migration in a development environment first
3. Ensure backup is created before migration
4. Monitor system resources during migration"
    fi

    report_content+="

Next Steps:
----------
1. Create backup: ./scripts/backup-docker-config.sh
2. Run migration: ./deploy.sh (will use Podman if available)
3. Verify migration: ./verify.sh
4. If issues occur: ./scripts/rollback-to-docker.sh

Generated by: $0
"

    if [[ -n "$export_file" ]]; then
        echo "$report_content" > "$export_file"
        print_success "Validation report exported to: $export_file"
    else
        echo "$report_content"
    fi
}

# Function to attempt automatic fixes
attempt_fixes() {
    print_status "Attempting to fix detected issues automatically..."
    
    local fixes_applied=0
    
    # Try to install podman-compose if missing
    if ! command -v podman-compose &> /dev/null && command -v pip &> /dev/null; then
        print_status "Attempting to install podman-compose..."
        if pip install --user podman-compose; then
            print_success "podman-compose installed successfully"
            ((fixes_applied++))
        else
            print_warning "Failed to install podman-compose automatically"
        fi
    fi
    
    # Create containers config directory if missing
    local containers_config_dir="${HOME}/.config/containers"
    if [[ ! -d "$containers_config_dir" ]]; then
        print_status "Creating containers config directory..."
        if mkdir -p "$containers_config_dir"; then
            print_success "Containers config directory created"
            ((fixes_applied++))
        else
            print_warning "Failed to create containers config directory"
        fi
    fi
    
    # Create Phoenix Hydra data directory structure
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    if [[ ! -d "$phoenix_data_dir" ]]; then
        print_status "Creating Phoenix Hydra data directory structure..."
        if mkdir -p "$phoenix_data_dir"/{db_data,logs,config}; then
            chmod 755 "$phoenix_data_dir"
            chmod 700 "$phoenix_data_dir/db_data"
            chmod 755 "$phoenix_data_dir/logs"
            chmod 755 "$phoenix_data_dir/config"
            print_success "Phoenix Hydra data directory structure created"
            ((fixes_applied++))
        else
            print_warning "Failed to create Phoenix Hydra data directory structure"
        fi
    fi
    
    if [[ $fixes_applied -gt 0 ]]; then
        print_success "$fixes_applied issues fixed automatically"
        print_status "Re-running validation to check improvements..."
        echo ""
        # Re-run specific checks that might have been fixed
        check_podman_installation
        check_filesystem_permissions
    else
        print_warning "No issues could be fixed automatically"
    fi
}

# Main validation function
main() {
    local fix_issues=false
    local detailed=false
    local export_report=""
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --fix-issues)
                fix_issues=true
                shift
                ;;
            --detailed)
                detailed=true
                shift
                ;;
            --export-report)
                export_report="${PROJECT_ROOT}/migration-prerequisites-report.txt"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Phoenix Hydra migration prerequisites validation..."
    echo ""
    
    # Run all validation checks
    check_system_requirements
    echo ""
    check_docker_configuration
    echo ""
    check_podman_installation
    echo ""
    check_filesystem_permissions
    echo ""
    check_network_requirements
    echo ""
    check_security_requirements
    echo ""
    check_backup_requirements
    echo ""
    
    # Attempt fixes if requested
    if [[ "$fix_issues" == true ]]; then
        attempt_fixes
        echo ""
    fi
    
    # Generate and display summary
    print_status "Validation Summary:"
    echo "  ✅ Checks Passed: $CHECKS_PASSED"
    echo "  ⚠️  Warnings: $CHECKS_WARNING"
    echo "  ❌ Checks Failed: $CHECKS_FAILED"
    echo ""
    
    # Determine overall status
    if [[ $CHECKS_FAILED -eq 0 ]]; then
        if [[ $CHECKS_WARNING -eq 0 ]]; then
            print_success "🟢 MIGRATION READY - All prerequisites met!"
            echo ""
            echo "Next steps:"
            echo "  1. Create backup: ./scripts/backup-docker-config.sh"
            echo "  2. Run migration: ./deploy.sh"
            echo "  3. Verify services: ./verify.sh"
        else
            print_warning "🟡 MIGRATION READY WITH WARNINGS - Review warnings before proceeding"
            echo ""
            echo "Next steps:"
            echo "  1. Review warnings above"
            echo "  2. Create backup: ./scripts/backup-docker-config.sh"
            echo "  3. Run migration: ./deploy.sh"
            echo "  4. Monitor closely during migration"
        fi
    else
        print_error "🔴 MIGRATION NOT READY - Critical issues must be resolved"
        echo ""
        echo "Required actions:"
        echo "  1. Resolve all failed checks above"
        echo "  2. Re-run this validation script"
        echo "  3. Only proceed when all checks pass"
        exit 1
    fi
    
    # Generate report if requested
    if [[ -n "$export_report" ]]; then
        echo ""
        generate_report "$export_report"
    fi
}

# Handle script interruption
trap 'print_error "Validation interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"