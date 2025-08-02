#!/bin/bash

# Phoenix Hydra Network Validation Script
# Validates network configuration and connectivity

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/podman-compose.yaml"
NETWORK_NAME="phoenix-hydra_phoenix-net"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to validate network configuration
validate_network_config() {
    print_status "INFO" "Validating network configuration..."
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_status "ERROR" "Compose file not found: $COMPOSE_FILE"
        return 1
    fi
    
    # Validate network definition in compose file
    if grep -q "phoenix-net:" "$COMPOSE_FILE"; then
        print_status "SUCCESS" "Network definition found in compose file"
    else
        print_status "ERROR" "Network definition not found in compose file"
        return 1
    fi
    
    # Check subnet configuration
    if grep -q "172.20.0.0/16" "$COMPOSE_FILE"; then
        print_status "SUCCESS" "Subnet configuration is correct (172.20.0.0/16)"
    else
        print_status "WARNING" "Subnet configuration may be incorrect"
    fi
    
    # Check gateway configuration
    if grep -q "172.20.0.1" "$COMPOSE_FILE"; then
        print_status "SUCCESS" "Gateway configuration is correct (172.20.0.1)"
    else
        print_status "WARNING" "Gateway configuration may be incorrect"
    fi
    
    return 0
}

# Function to validate network exists
validate_network_exists() {
    print_status "INFO" "Checking if network exists..."
    
    if podman network exists "$NETWORK_NAME" 2>/dev/null; then
        print_status "SUCCESS" "Network '$NETWORK_NAME' exists"
        
        # Get network details
        local subnet=$(podman network inspect "$NETWORK_NAME" --format "{{range .Subnets}}{{.Subnet}}{{end}}" 2>/dev/null)
        local gateway=$(podman network inspect "$NETWORK_NAME" --format "{{range .Subnets}}{{.Gateway}}{{end}}" 2>/dev/null)
        local driver=$(podman network inspect "$NETWORK_NAME" --format "{{.Driver}}" 2>/dev/null)
        
        print_status "INFO" "Network details:"
        echo "    Subnet: $subnet"
        echo "    Gateway: $gateway"
        echo "    Driver: $driver"
        
        return 0
    else
        print_status "WARNING" "Network '$NETWORK_NAME' does not exist (will be created when services start)"
        return 1
    fi
}

# Function to validate service network assignments
validate_service_networks() {
    print_status "INFO" "Validating service network assignments..."
    
    local services=("gap-detector" "recurrent-processor" "db" "windmill" "rubik-agent" "nginx" "analysis-engine")
    local valid_count=0
    
    for service in "${services[@]}"; do
        if grep -A 10 "^  $service:" "$COMPOSE_FILE" | grep -q "phoenix-net"; then
            print_status "SUCCESS" "Service '$service' is assigned to phoenix-net"
            ((valid_count++))
        else
            print_status "WARNING" "Service '$service' may not be assigned to phoenix-net"
        fi
    done
    
    print_status "INFO" "Network assignment validation: $valid_count/${#services[@]} services configured"
    return 0
}

# Function to validate DNS prerequisites
validate_dns_prerequisites() {
    print_status "INFO" "Validating DNS prerequisites..."
    
    # Check if aardvark-dns is available (Podman's DNS resolver)
    if command -v aardvark-dns &> /dev/null; then
        print_status "SUCCESS" "aardvark-dns is available"
    else
        print_status "WARNING" "aardvark-dns not found in PATH (may be installed elsewhere)"
    fi
    
    # Check if netavark is available (Podman's network backend)
    if command -v netavark &> /dev/null; then
        print_status "SUCCESS" "netavark is available"
    else
        print_status "WARNING" "netavark not found in PATH (may be installed elsewhere)"
    fi
    
    return 0
}

# Function to validate port configurations
validate_port_config() {
    print_status "INFO" "Validating port configurations..."
    
    local expected_ports=("8000:8000" "5000:5000" "3000:3000" "8080:8080")
    local found_ports=0
    
    for port in "${expected_ports[@]}"; do
        if grep -q "\"$port\"" "$COMPOSE_FILE"; then
            print_status "SUCCESS" "Port mapping '$port' found"
            ((found_ports++))
        else
            print_status "WARNING" "Port mapping '$port' not found"
        fi
    done
    
    print_status "INFO" "Port configuration validation: $found_ports/${#expected_ports[@]} expected ports configured"
    return 0
}

# Function to check for network conflicts
check_network_conflicts() {
    print_status "INFO" "Checking for network conflicts..."
    
    # Check if subnet conflicts with existing networks
    local conflicting_networks=$(podman network ls --format "{{.Name}}" | xargs -I {} sh -c 'podman network inspect {} --format "{{.Name}}: {{range .Subnets}}{{.Subnet}}{{end}}" 2>/dev/null | grep "172.20.0.0/16" || true')
    
    if [ -n "$conflicting_networks" ] && [ "$conflicting_networks" != "$NETWORK_NAME: 172.20.0.0/16" ]; then
        print_status "WARNING" "Potential subnet conflict detected:"
        echo "$conflicting_networks"
    else
        print_status "SUCCESS" "No network conflicts detected"
    fi
    
    return 0
}

# Function to validate security settings
validate_security_settings() {
    print_status "INFO" "Validating network security settings..."
    
    # Check for security_opt settings
    if grep -q "no-new-privileges:true" "$COMPOSE_FILE"; then
        print_status "SUCCESS" "Security option 'no-new-privileges:true' found"
    else
        print_status "WARNING" "Security option 'no-new-privileges:true' not found"
    fi
    
    # Check for user settings (rootless execution)
    if grep -q "user:" "$COMPOSE_FILE"; then
        print_status "SUCCESS" "User settings found (rootless execution)"
    else
        print_status "WARNING" "User settings not found"
    fi
    
    return 0
}

# Function to generate network validation report
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="${SCRIPT_DIR}/network-validation-report.txt"
    
    print_status "INFO" "Generating network validation report..."
    
    cat > "$report_file" << EOF
Phoenix Hydra Network Validation Report
Generated: $timestamp

Network Configuration:
- Compose File: $COMPOSE_FILE
- Network Name: $NETWORK_NAME
- Subnet: 172.20.0.0/16
- Gateway: 172.20.0.1

Validation Results:
$(validate_network_config 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(validate_network_exists 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(validate_service_networks 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(validate_dns_prerequisites 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(validate_port_config 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(check_network_conflicts 2>&1 | sed 's/\x1b\[[0-9;]*m//g')
$(validate_security_settings 2>&1 | sed 's/\x1b\[[0-9;]*m//g')

Recommendations:
- Ensure all services are properly configured to use phoenix-net
- Verify DNS resolution between services after starting containers
- Monitor network performance and adjust MTU if needed
- Regularly test network connectivity using test-network.sh

For detailed network testing, run: ./test-network.sh
EOF

    print_status "SUCCESS" "Network validation report saved to: $report_file"
}

# Main execution
main() {
    echo "🔍 Phoenix Hydra Network Validation"
    echo "===================================="
    echo ""
    
    local exit_code=0
    
    validate_network_config || exit_code=1
    echo ""
    
    validate_network_exists || true  # Don't fail if network doesn't exist yet
    echo ""
    
    validate_service_networks || exit_code=1
    echo ""
    
    validate_dns_prerequisites || true  # Don't fail on DNS prerequisites
    echo ""
    
    validate_port_config || exit_code=1
    echo ""
    
    check_network_conflicts || true  # Don't fail on conflicts
    echo ""
    
    validate_security_settings || true  # Don't fail on security settings
    echo ""
    
    generate_report
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        print_status "SUCCESS" "Network validation completed successfully!"
        echo ""
        print_status "INFO" "Next steps:"
        echo "  1. Start services: podman-compose -f $COMPOSE_FILE up -d"
        echo "  2. Test network: ./test-network.sh"
        echo "  3. Verify connectivity between services"
    else
        print_status "ERROR" "Network validation completed with warnings/errors"
        echo ""
        print_status "INFO" "Please review the issues above and fix them before proceeding"
    fi
    
    return $exit_code
}

# Run main function
main "$@"