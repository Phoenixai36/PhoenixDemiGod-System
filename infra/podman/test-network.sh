#!/bin/bash

# Phoenix Hydra Podman Network Testing Script
# Tests DNS resolution and connectivity between services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/podman-compose.yaml"
NETWORK_NAME="phoenix-hydra_phoenix-net"

echo "🔍 Phoenix Hydra Network Testing Script"
echo "========================================"

# Function to check if podman-compose is available
check_podman_compose() {
    if ! command -v podman-compose &> /dev/null; then
        echo "❌ Error: podman-compose is not installed"
        echo "Install with: pip install podman-compose"
        exit 1
    fi
}

# Function to check if services are running
check_services_running() {
    echo "📋 Checking if services are running..."
    
    local services=("gap-detector" "recurrent-processor" "db" "windmill" "rubik-agent" "nginx" "analysis-engine")
    local running_services=()
    
    for service in "${services[@]}"; do
        if podman-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${service}$"; then
            running_services+=("$service")
            echo "  ✅ $service is running"
        else
            echo "  ⚠️  $service is not running"
        fi
    done
    
    if [ ${#running_services[@]} -eq 0 ]; then
        echo "❌ No services are running. Start services first with:"
        echo "   podman-compose -f $COMPOSE_FILE up -d"
        exit 1
    fi
    
    echo "✅ Found ${#running_services[@]} running services"
    return 0
}

# Function to test DNS resolution between services
test_dns_resolution() {
    echo ""
    echo "🌐 Testing DNS resolution between services..."
    echo "============================================="
    
    local test_services=("db" "windmill" "gap-detector" "recurrent-processor" "rubik-agent" "nginx")
    local test_container="gap-detector"
    
    # Check if test container is running
    if ! podman-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${test_container}$"; then
        echo "⚠️  Test container '$test_container' is not running. Skipping DNS tests."
        return 0
    fi
    
    echo "Using '$test_container' as test container..."
    
    for service in "${test_services[@]}"; do
        if [ "$service" = "$test_container" ]; then
            continue  # Skip self-test
        fi
        
        echo -n "  Testing DNS resolution for '$service'... "
        
        # Test DNS resolution using nslookup or getent
        if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "getent hosts $service > /dev/null 2>&1"; then
            echo "✅ Resolved"
            
            # Get the IP address
            local ip=$(podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "getent hosts $service | awk '{print \$1}'" 2>/dev/null | tr -d '\r')
            if [ -n "$ip" ]; then
                echo "    └─ IP: $ip"
            fi
        else
            echo "❌ Failed"
        fi
    done
}

# Function to test network connectivity
test_network_connectivity() {
    echo ""
    echo "🔗 Testing network connectivity..."
    echo "================================="
    
    local test_container="gap-detector"
    
    # Check if test container is running
    if ! podman-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${test_container}$"; then
        echo "⚠️  Test container '$test_container' is not running. Skipping connectivity tests."
        return 0
    fi
    
    # Test connectivity to database
    echo -n "  Testing connection to database (db:5432)... "
    if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "timeout 5 bash -c '</dev/tcp/db/5432' > /dev/null 2>&1"; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
    fi
    
    # Test connectivity to Windmill
    echo -n "  Testing connection to Windmill (windmill:3000)... "
    if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "timeout 5 bash -c '</dev/tcp/windmill/3000' > /dev/null 2>&1"; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
    fi
    
    # Test connectivity to nginx
    echo -n "  Testing connection to nginx (nginx:8080)... "
    if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "timeout 5 bash -c '</dev/tcp/nginx/8080' > /dev/null 2>&1"; then
        echo "✅ Connected"
    else
        echo "❌ Failed"
    fi
}

# Function to display network information
show_network_info() {
    echo ""
    echo "📊 Network Information"
    echo "====================="
    
    # Show network details
    if podman network exists "$NETWORK_NAME" 2>/dev/null; then
        echo "Network: $NETWORK_NAME"
        podman network inspect "$NETWORK_NAME" --format "  Subnet: {{range .Subnets}}{{.Subnet}}{{end}}"
        podman network inspect "$NETWORK_NAME" --format "  Gateway: {{range .Subnets}}{{.Gateway}}{{end}}"
        podman network inspect "$NETWORK_NAME" --format "  Driver: {{.Driver}}"
        
        echo ""
        echo "Connected containers:"
        podman network inspect "$NETWORK_NAME" --format "{{range .Containers}}  - {{.Name}} ({{.IPv4Address}}){{end}}"
    else
        echo "⚠️  Network '$NETWORK_NAME' not found"
    fi
}

# Function to test external connectivity
test_external_connectivity() {
    echo ""
    echo "🌍 Testing external connectivity..."
    echo "=================================="
    
    local test_container="gap-detector"
    
    # Check if test container is running
    if ! podman-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "^${test_container}$"; then
        echo "⚠️  Test container '$test_container' is not running. Skipping external connectivity tests."
        return 0
    fi
    
    # Test external DNS resolution
    echo -n "  Testing external DNS resolution (google.com)... "
    if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "nslookup google.com > /dev/null 2>&1"; then
        echo "✅ Working"
    else
        echo "❌ Failed"
    fi
    
    # Test external connectivity
    echo -n "  Testing external connectivity (8.8.8.8:53)... "
    if podman-compose -f "$COMPOSE_FILE" exec -T "$test_container" sh -c "timeout 5 bash -c '</dev/tcp/8.8.8.8/53' > /dev/null 2>&1"; then
        echo "✅ Working"
    else
        echo "❌ Failed"
    fi
}

# Main execution
main() {
    check_podman_compose
    check_services_running
    show_network_info
    test_dns_resolution
    test_network_connectivity
    test_external_connectivity
    
    echo ""
    echo "🎉 Network testing completed!"
    echo ""
    echo "💡 Tips:"
    echo "  - If DNS resolution fails, ensure services are running and healthy"
    echo "  - If connectivity fails, check firewall settings and network configuration"
    echo "  - Use 'podman network ls' to list all networks"
    echo "  - Use 'podman network inspect $NETWORK_NAME' for detailed network info"
}

# Run main function
main "$@"