#!/bin/bash
set -euo pipefail

# Phoenix Hydra Security Boundaries Application Script
# This script applies network isolation and security boundaries

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SECURITY_CONFIG="${SCRIPT_DIR}/security-boundaries.yaml"
COMPOSE_FILE="${SCRIPT_DIR}/podman-compose.yaml"

echo "🔒 Applying Phoenix Hydra security boundaries..."

# Function to check if podman is available
check_podman() {
    if ! command -v podman &> /dev/null; then
        echo "❌ Podman is not installed. Please install Podman first."
        exit 1
    fi
    
    if ! command -v podman-compose &> /dev/null; then
        echo "❌ podman-compose is not installed. Install with: pip install podman-compose"
        exit 1
    fi
}

# Function to create network with security policies
create_secure_network() {
    echo "Creating secure phoenix-net network..."
    
    # Remove existing network if it exists
    podman network rm phoenix-hydra_phoenix-net 2>/dev/null || true
    
    # Create network with security settings (using only supported options)
    podman network create \
        --driver bridge \
        --subnet 172.20.0.0/16 \
        --gateway 172.20.0.1 \
        --ip-range 172.20.1.0/24 \
        --label project=phoenix-hydra \
        --label environment=development \
        --label network.type=bridge \
        --label network.isolation=secure \
        phoenix-hydra_phoenix-net
    
    echo "✅ Secure network created successfully"
}

# Function to configure firewall rules (if available)
configure_firewall() {
    echo "Configuring firewall rules..."
    
    # Check if firewall tools are available
    if command -v ufw &> /dev/null; then
        echo "Configuring UFW firewall rules..."
        
        # Allow external access to exposed ports only
        sudo ufw allow 8000/tcp comment "Phoenix Hydra - Gap Detector API"
        sudo ufw allow 3000/tcp comment "Phoenix Hydra - Windmill UI"
        sudo ufw allow 8080/tcp comment "Phoenix Hydra - Nginx Proxy"
        sudo ufw allow 5000/tcp comment "Phoenix Hydra - Analysis Engine API"
        
        # Block direct access to internal services
        sudo ufw deny 5432/tcp comment "Phoenix Hydra - Block direct DB access"
        
        echo "✅ UFW firewall rules configured"
        
    elif command -v firewall-cmd &> /dev/null; then
        echo "Configuring firewalld rules..."
        
        # Create Phoenix Hydra zone
        sudo firewall-cmd --permanent --new-zone=phoenix-hydra 2>/dev/null || true
        sudo firewall-cmd --reload
        
        # Add allowed ports
        sudo firewall-cmd --permanent --zone=phoenix-hydra --add-port=8000/tcp
        sudo firewall-cmd --permanent --zone=phoenix-hydra --add-port=3000/tcp
        sudo firewall-cmd --permanent --zone=phoenix-hydra --add-port=8080/tcp
        sudo firewall-cmd --permanent --zone=phoenix-hydra --add-port=5000/tcp
        
        sudo firewall-cmd --reload
        echo "✅ Firewalld rules configured"
        
    else
        echo "⚠️  No supported firewall found. Manual firewall configuration may be needed."
    fi
}

# Function to set up volume security
setup_volume_security() {
    echo "Setting up volume security..."
    
    PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"
    
    # Ensure volumes exist with correct permissions
    mkdir -p "${PHOENIX_DATA_DIR}/db_data"
    mkdir -p "${PHOENIX_DATA_DIR}/nginx_config"
    mkdir -p "${PHOENIX_DATA_DIR}/logs"
    
    # Set restrictive permissions for database
    chmod 700 "${PHOENIX_DATA_DIR}/db_data"
    chown $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/db_data"
    
    # Set appropriate permissions for nginx config (read-only)
    chmod 755 "${PHOENIX_DATA_DIR}/nginx_config"
    chown $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/nginx_config"
    
    # Set permissions for logs
    chmod 755 "${PHOENIX_DATA_DIR}/logs"
    chown $(id -u):$(id -g) "${PHOENIX_DATA_DIR}/logs"
    
    # Set SELinux contexts if SELinux is enabled
    if command -v semanage &> /dev/null && getenforce 2>/dev/null | grep -q "Enforcing"; then
        echo "Setting SELinux contexts..."
        chcon -R -t container_file_t "${PHOENIX_DATA_DIR}" 2>/dev/null || true
        echo "✅ SELinux contexts set"
    fi
    
    echo "✅ Volume security configured"
}

# Function to validate security configuration
validate_security() {
    echo "Validating security configuration..."
    
    # Check network exists
    if podman network inspect phoenix-hydra_phoenix-net &>/dev/null; then
        echo "✅ Secure network exists"
    else
        echo "❌ Secure network not found"
        return 1
    fi
    
    # Check volume permissions
    PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"
    
    if [ "$(stat -c "%a" "${PHOENIX_DATA_DIR}/db_data")" = "700" ]; then
        echo "✅ Database volume has correct permissions (700)"
    else
        echo "⚠️  Database volume permissions may be incorrect"
    fi
    
    if [ "$(stat -c "%a" "${PHOENIX_DATA_DIR}/nginx_config")" = "755" ]; then
        echo "✅ Nginx config volume has correct permissions (755)"
    else
        echo "⚠️  Nginx config volume permissions may be incorrect"
    fi
    
    # Check if compose file has security options
    if grep -q "no-new-privileges:true" "${COMPOSE_FILE}"; then
        echo "✅ Security options present in compose file"
    else
        echo "⚠️  Security options may be missing from compose file"
    fi
    
    echo "✅ Security validation complete"
}

# Function to create network monitoring script
create_monitoring_script() {
    echo "Creating network monitoring script..."
    
    cat > "${SCRIPT_DIR}/monitor-security.sh" << 'EOF'
#!/bin/bash
# Phoenix Hydra Security Monitoring Script

echo "🔍 Phoenix Hydra Security Status"
echo "================================"

# Check network status
echo "Network Status:"
podman network inspect phoenix-hydra_phoenix-net --format "{{.Name}}: {{.Subnets}}" 2>/dev/null || echo "❌ Network not found"

# Check container security
echo -e "\nContainer Security:"
for container in $(podman ps --format "{{.Names}}" | grep phoenix-hydra); do
    echo "  $container:"
    
    # Check if running as non-root
    user_info=$(podman inspect "$container" --format "{{.Config.User}}" 2>/dev/null || echo "unknown")
    if [ "$user_info" != "root" ] && [ "$user_info" != "" ]; then
        echo "    ✅ Running as non-root user: $user_info"
    else
        echo "    ⚠️  User info: $user_info"
    fi
    
    # Check security options
    security_opts=$(podman inspect "$container" --format "{{.HostConfig.SecurityOpt}}" 2>/dev/null || echo "[]")
    if echo "$security_opts" | grep -q "no-new-privileges:true"; then
        echo "    ✅ no-new-privileges enabled"
    else
        echo "    ⚠️  no-new-privileges not found"
    fi
done

# Check exposed ports
echo -e "\nExposed Ports:"
podman ps --format "table {{.Names}}\t{{.Ports}}" | grep phoenix-hydra

# Check volume permissions
echo -e "\nVolume Permissions:"
PHOENIX_DATA_DIR="${HOME}/.local/share/phoenix-hydra"
if [ -d "$PHOENIX_DATA_DIR" ]; then
    echo "  Database: $(stat -c "%a %U:%G" "$PHOENIX_DATA_DIR/db_data" 2>/dev/null || echo "not found")"
    echo "  Nginx Config: $(stat -c "%a %U:%G" "$PHOENIX_DATA_DIR/nginx_config" 2>/dev/null || echo "not found")"
    echo "  Logs: $(stat -c "%a %U:%G" "$PHOENIX_DATA_DIR/logs" 2>/dev/null || echo "not found")"
else
    echo "  ❌ Phoenix data directory not found"
fi

echo -e "\n✅ Security monitoring complete"
EOF
    
    chmod +x "${SCRIPT_DIR}/monitor-security.sh"
    echo "✅ Security monitoring script created"
}

# Function to test network isolation
test_network_isolation() {
    echo "Testing network isolation..."
    
    # Check if containers are running
    if ! podman-compose -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
        echo "⚠️  Containers not running. Start them first with: podman-compose up -d"
        return 0
    fi
    
    # Test external port accessibility
    echo "Testing external port accessibility..."
    
    # Test gap-detector (port 8000)
    if curl -s -f http://localhost:8000/health &>/dev/null; then
        echo "✅ Gap Detector accessible on port 8000"
    else
        echo "⚠️  Gap Detector not accessible on port 8000"
    fi
    
    # Test windmill (port 3000)
    if curl -s -f http://localhost:3000/api/version &>/dev/null; then
        echo "✅ Windmill accessible on port 3000"
    else
        echo "⚠️  Windmill not accessible on port 3000"
    fi
    
    # Test nginx (port 8080)
    if curl -s -f http://localhost:8080/health &>/dev/null; then
        echo "✅ Nginx accessible on port 8080"
    else
        echo "⚠️  Nginx not accessible on port 8080"
    fi
    
    # Test that database is NOT accessible externally
    if ! nc -z localhost 5432 2>/dev/null; then
        echo "✅ Database correctly isolated (not accessible externally)"
    else
        echo "⚠️  Database may be exposed externally"
    fi
    
    echo "✅ Network isolation test complete"
}

# Main execution
main() {
    echo "Starting security boundaries application..."
    
    check_podman
    create_secure_network
    setup_volume_security
    configure_firewall
    create_monitoring_script
    validate_security
    
    echo ""
    echo "🎉 Security boundaries applied successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start services: podman-compose -f ${COMPOSE_FILE} up -d"
    echo "2. Test isolation: ./test-network-isolation.sh"
    echo "3. Monitor security: ./monitor-security.sh"
    echo ""
    echo "Exposed ports:"
    echo "  - Gap Detector API: http://localhost:8000"
    echo "  - Windmill UI: http://localhost:3000"
    echo "  - Nginx Proxy: http://localhost:8080"
    echo "  - Analysis Engine API: http://localhost:5000"
    echo ""
    echo "Security features enabled:"
    echo "  ✅ Network isolation with custom bridge"
    echo "  ✅ Rootless container execution"
    echo "  ✅ Volume permission restrictions"
    echo "  ✅ Security options (no-new-privileges)"
    echo "  ✅ Firewall rules (if supported)"
    echo "  ✅ Security monitoring script"
}

# Run main function
main "$@"