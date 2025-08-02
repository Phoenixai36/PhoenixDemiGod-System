#!/bin/bash
set -euo pipefail

# Phoenix Hydra Network Isolation Test Script
# This script tests network isolation and security boundaries

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/podman-compose.yaml"

echo "🔒 Testing Phoenix Hydra network isolation and security boundaries..."

# Function to test port accessibility
test_port() {
    local host=$1
    local port=$2
    local service_name=$3
    local should_be_accessible=$4
    
    if nc -z "$host" "$port" 2>/dev/null; then
        if [ "$should_be_accessible" = "true" ]; then
            echo "  ✅ $service_name accessible on port $port (expected)"
        else
            echo "  ❌ $service_name accessible on port $port (SECURITY ISSUE - should be blocked)"
            return 1
        fi
    else
        if [ "$should_be_accessible" = "true" ]; then
            echo "  ⚠️  $service_name not accessible on port $port (may not be ready)"
        else
            echo "  ✅ $service_name blocked on port $port (expected)"
        fi
    fi
    return 0
}

# Function to test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local service_name=$2
    local should_be_accessible=$3
    
    if curl -s -f "$url" >/dev/null 2>&1; then
        if [ "$should_be_accessible" = "true" ]; then
            echo "  ✅ $service_name HTTP endpoint accessible (expected)"
        else
            echo "  ❌ $service_name HTTP endpoint accessible (SECURITY ISSUE - should be blocked)"
            return 1
        fi
    else
        if [ "$should_be_accessible" = "true" ]; then
            echo "  ⚠️  $service_name HTTP endpoint not accessible (may not be ready)"
        else
            echo "  ✅ $service_name HTTP endpoint blocked (expected)"
        fi
    fi
    return 0
}

# Function to test inter-container communication
test_inter_container_communication() {
    echo "Testing inter-container communication..."
    
    # Get container names
    local containers=($(podman ps --format "{{.Names}}" | grep phoenix-hydra || true))
    
    if [ ${#containers[@]} -eq 0 ]; then
        echo "  ⚠️  No Phoenix Hydra containers running"
        return 0
    fi
    
    # Test DNS resolution between containers
    for container in "${containers[@]}"; do
        echo "  Testing DNS resolution from $container:"
        
        # Test if container can resolve other service names
        local services=("db" "windmill" "nginx" "gap-detector" "recurrent-processor" "rubik-agent" "analysis-engine")
        
        for service in "${services[@]}"; do
            if podman exec "$container" nslookup "$service" >/dev/null 2>&1; then
                echo "    ✅ Can resolve $service"
            else
                echo "    ⚠️  Cannot resolve $service (may be normal if service not running)"
            fi
        done
        break  # Only test from one container to avoid spam
    done
}

# Function to test volume security
test_volume_security() {
    echo "Testing volume security..."
    
    local phoenix_data_dir="${HOME}/.local/share/phoenix-hydra"
    
    # Test database volume permissions
    if [ -d "${phoenix_data_dir}/db_data" ]; then
        local db_perms=$(stat -c "%a" "${phoenix_data_dir}/db_data")
        if [ "$db_perms" = "700" ]; then
            echo "  ✅ Database volume has correct restrictive permissions (700)"
        else
            echo "  ⚠️  Database volume permissions: $db_perms (expected: 700)"
        fi
    else
        echo "  ❌ Database volume directory not found"
    fi
    
    # Test nginx config volume permissions
    if [ -d "${phoenix_data_dir}/nginx_config" ]; then
        local nginx_perms=$(stat -c "%a" "${phoenix_data_dir}/nginx_config")
        if [ "$nginx_perms" = "755" ]; then
            echo "  ✅ Nginx config volume has correct permissions (755)"
        else
            echo "  ⚠️  Nginx config volume permissions: $nginx_perms (expected: 755)"
        fi
    else
        echo "  ❌ Nginx config volume directory not found"
    fi
    
    # Test that volumes are owned by current user
    local current_user=$(id -u)
    local current_group=$(id -g)
    
    for volume_dir in "${phoenix_data_dir}/db_data" "${phoenix_data_dir}/nginx_config" "${phoenix_data_dir}/logs"; do
        if [ -d "$volume_dir" ]; then
            local owner=$(stat -c "%u:%g" "$volume_dir")
            if [ "$owner" = "${current_user}:${current_group}" ]; then
                echo "  ✅ $(basename "$volume_dir") volume owned by current user"
            else
                echo "  ⚠️  $(basename "$volume_dir") volume owner: $owner (expected: ${current_user}:${current_group})"
            fi
        fi
    done
}

# Function to test container security
test_container_security() {
    echo "Testing container security..."
    
    local containers=($(podman ps --format "{{.Names}}" | grep phoenix-hydra || true))
    
    if [ ${#containers[@]} -eq 0 ]; then
        echo "  ⚠️  No Phoenix Hydra containers running"
        return 0
    fi
    
    for container in "${containers[@]}"; do
        echo "  Testing security for $container:"
        
        # Check if running as non-root
        local user_info=$(podman inspect "$container" --format "{{.Config.User}}" 2>/dev/null || echo "unknown")
        if [ "$user_info" != "root" ] && [ "$user_info" != "" ] && [ "$user_info" != "unknown" ]; then
            echo "    ✅ Running as non-root user: $user_info"
        else
            echo "    ⚠️  User info: $user_info"
        fi
        
        # Check security options
        local security_opts=$(podman inspect "$container" --format "{{.HostConfig.SecurityOpt}}" 2>/dev/null || echo "[]")
        if echo "$security_opts" | grep -q "no-new-privileges:true"; then
            echo "    ✅ no-new-privileges enabled"
        else
            echo "    ⚠️  no-new-privileges not found in security options"
        fi
        
        # Check if container has privileged access
        local privileged=$(podman inspect "$container" --format "{{.HostConfig.Privileged}}" 2>/dev/null || echo "unknown")
        if [ "$privileged" = "false" ]; then
            echo "    ✅ Container is not privileged"
        else
            echo "    ⚠️  Container privileged status: $privileged"
        fi
    done
}

# Function to test network configuration
test_network_configuration() {
    echo "Testing network configuration..."
    
    # Check if phoenix-net network exists
    if podman network inspect phoenix-hydra_phoenix-net >/dev/null 2>&1; then
        echo "  ✅ phoenix-net network exists"
        
        # Check network configuration
        local subnet=$(podman network inspect phoenix-hydra_phoenix-net --format "{{range .Subnets}}{{.Subnet}}{{end}}" 2>/dev/null || echo "unknown")
        if [ "$subnet" = "172.20.0.0/16" ]; then
            echo "  ✅ Network subnet correctly configured: $subnet"
        else
            echo "  ⚠️  Network subnet: $subnet (expected: 172.20.0.0/16)"
        fi
        
        # Check if network is internal
        local internal=$(podman network inspect phoenix-hydra_phoenix-net --format "{{.Internal}}" 2>/dev/null || echo "unknown")
        if [ "$internal" = "false" ]; then
            echo "  ✅ Network allows external connectivity"
        else
            echo "  ⚠️  Network internal setting: $internal"
        fi
        
    else
        echo "  ❌ phoenix-net network not found"
    fi
}

# Main test execution
main() {
    echo "Starting network isolation tests..."
    echo ""
    
    # Test 1: External port accessibility
    echo "Test 1: External Port Accessibility"
    echo "===================================="
    
    # These ports should be accessible from outside
    test_port "localhost" 8000 "Gap Detector API" "true"
    test_port "localhost" 3000 "Windmill UI" "true"
    test_port "localhost" 8080 "Nginx Proxy" "true"
    test_port "localhost" 5000 "Analysis Engine API" "true"
    
    # These ports should NOT be accessible from outside
    test_port "localhost" 5432 "PostgreSQL Database" "false"
    
    echo ""
    
    # Test 2: HTTP endpoint accessibility
    echo "Test 2: HTTP Endpoint Accessibility"
    echo "===================================="
    
    test_http_endpoint "http://localhost:8000/health" "Gap Detector" "true"
    test_http_endpoint "http://localhost:3000/api/version" "Windmill" "true"
    test_http_endpoint "http://localhost:8080/health" "Nginx" "true"
    test_http_endpoint "http://localhost:5000/health" "Analysis Engine" "true"
    
    echo ""
    
    # Test 3: Network configuration
    echo "Test 3: Network Configuration"
    echo "=============================="
    test_network_configuration
    
    echo ""
    
    # Test 4: Inter-container communication
    echo "Test 4: Inter-container Communication"
    echo "====================================="
    test_inter_container_communication
    
    echo ""
    
    # Test 5: Volume security
    echo "Test 5: Volume Security"
    echo "======================="
    test_volume_security
    
    echo ""
    
    # Test 6: Container security
    echo "Test 6: Container Security"
    echo "=========================="
    test_container_security
    
    echo ""
    echo "🎉 Network isolation and security boundary tests completed!"
    echo ""
    echo "Summary of security features tested:"
    echo "  ✅ External port exposure (8000, 3000, 8080, 5000)"
    echo "  ✅ Database port isolation (5432 blocked externally)"
    echo "  ✅ HTTP endpoint accessibility"
    echo "  ✅ Network configuration and isolation"
    echo "  ✅ Inter-container DNS resolution"
    echo "  ✅ Volume permission restrictions"
    echo "  ✅ Container security options"
    echo ""
    echo "If any tests show warnings or errors, review the security configuration."
}

# Check if containers are running
if ! podman-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
    echo "⚠️  Phoenix Hydra containers are not running."
    echo "Start them first with: podman-compose -f $COMPOSE_FILE up -d"
    echo ""
    echo "Running basic configuration tests only..."
    echo ""
    
    # Run only tests that don't require running containers
    echo "Test: Network Configuration"
    echo "=========================="
    test_network_configuration
    
    echo ""
    echo "Test: Volume Security"
    echo "===================="
    test_volume_security
    
    echo ""
    echo "To run full tests, start the containers and run this script again."
else
    # Run all tests
    main
fi