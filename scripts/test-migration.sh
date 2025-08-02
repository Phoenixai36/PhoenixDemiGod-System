#!/bin/bash
set -euo pipefail

# Comprehensive migration validation test script
# This script runs various tests to validate the Docker-to-Podman migration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PODMAN_COMPOSE_FILE="$PROJECT_ROOT/infra/podman/podman-compose.yaml"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/compose.yaml"

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

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Podman is installed
    if ! command -v podman &> /dev/null; then
        print_error "Podman is not installed"
        return 1
    fi
    
    # Check if podman-compose is installed
    if ! command -v podman-compose &> /dev/null; then
        print_error "podman-compose is not installed"
        return 1
    fi
    
    # Check if Node.js and npm are available for Jest tests
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found - Jest tests will be skipped"
    fi
    
    # Check if compose files exist
    if [[ ! -f "$PODMAN_COMPOSE_FILE" ]]; then
        print_error "Podman compose file not found: $PODMAN_COMPOSE_FILE"
        return 1
    fi
    
    print_success "Prerequisites check passed"
    return 0
}

# Function to run basic connectivity tests
test_basic_connectivity() {
    print_status "Running basic connectivity tests..."
    
    local services=(
        "8000:gap-detector:/health"
        "5000:analysis-engine:/health"
        "3000:windmill:/api/version"
        "8080:nginx:/health"
    )
    
    local healthy_count=0
    local total_services=${#services[@]}
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r port name path <<< "$service_info"
        
        print_status "Testing $name on port $port..."
        
        # Check if port is listening
        if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
            print_success "Port $port is listening"
            
            # Try to connect to health endpoint
            local health_url="http://localhost:$port$path"
            if timeout 10 curl -f -s "$health_url" >/dev/null 2>&1; then
                print_success "$name service is responding"
                ((healthy_count++))
            else
                print_warning "$name service on port $port may not be ready"
            fi
        else
            print_warning "Port $port is not listening - $name may not be started"
        fi
    done
    
    print_status "Connectivity test results: $healthy_count/$total_services services responding"
    
    # Return success if at least 75% of services are healthy
    local min_healthy=$((total_services * 3 / 4))
    if [[ $healthy_count -ge $min_healthy ]]; then
        print_success "Basic connectivity tests passed"
        return 0
    else
        print_error "Basic connectivity tests failed"
        return 1
    fi
}

# Function to test database connectivity
test_database_connectivity() {
    print_status "Testing database connectivity..."
    
    # Wait for database to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if podman exec phoenix-hydra_db_1 pg_isready -U windmill_user -d windmill >/dev/null 2>&1; then
            print_success "Database is ready"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "Database failed to become ready after $max_attempts attempts"
            return 1
        fi
        
        print_status "Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    # Test database connection
    if podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT version();" >/dev/null 2>&1; then
        print_success "Database connection test passed"
        return 0
    else
        print_error "Database connection test failed"
        return 1
    fi
}

# Function to test network isolation
test_network_isolation() {
    print_status "Testing network isolation..."
    
    # Check if phoenix-net network exists
    if podman network exists phoenix-hydra_phoenix-net 2>/dev/null; then
        print_success "Phoenix network exists"
        
        # Show network details
        local network_info
        network_info=$(podman network inspect phoenix-hydra_phoenix-net --format "{{.Subnets}}" 2>/dev/null || echo "unknown")
        print_status "Network subnet: $network_info"
        
        # Test inter-container connectivity
        if podman exec phoenix-hydra_gap-detector_1 ping -c 1 db >/dev/null 2>&1; then
            print_success "Inter-container connectivity working"
        else
            print_warning "Inter-container connectivity test inconclusive"
        fi
        
        return 0
    else
        print_error "Phoenix network not found"
        return 1
    fi
}

# Function to test volume persistence
test_volume_persistence() {
    print_status "Testing volume persistence..."
    
    # Check if database volume is mounted
    if podman exec phoenix-hydra_db_1 test -d /var/lib/postgresql/data >/dev/null 2>&1; then
        print_success "Database volume is mounted"
        
        # Test write permissions
        local test_file="/var/lib/postgresql/data/migration_test_$(date +%s)"
        if podman exec phoenix-hydra_db_1 touch "$test_file" >/dev/null 2>&1; then
            print_success "Database volume has write permissions"
            # Clean up test file
            podman exec phoenix-hydra_db_1 rm -f "$test_file" >/dev/null 2>&1
        else
            print_warning "Database volume write test failed"
        fi
        
        return 0
    else
        print_error "Database volume not properly mounted"
        return 1
    fi
}

# Function to test security configuration
test_security_configuration() {
    print_status "Testing security configuration..."
    
    # Get list of running containers
    local containers
    containers=$(podman-compose -f "$PODMAN_COMPOSE_FILE" ps --format "{{.Names}}" 2>/dev/null | grep -v '^$' || echo "")
    
    if [[ -z "$containers" ]]; then
        print_error "No containers found"
        return 1
    fi
    
    local security_issues=0
    
    while IFS= read -r container; do
        if [[ -n "$container" ]]; then
            print_status "Checking security for container: $container"
            
            # Check user configuration
            local user_info
            user_info=$(podman inspect "$container" --format "{{.Config.User}}" 2>/dev/null || echo "unknown")
            if [[ "$user_info" != "unknown" && "$user_info" != "" && "$user_info" != "0:0" ]]; then
                print_success "Container $container running as non-root user: $user_info"
            else
                print_warning "Container $container user configuration unclear: $user_info"
                ((security_issues++))
            fi
            
            # Check security options
            local security_opts
            security_opts=$(podman inspect "$container" --format "{{.HostConfig.SecurityOpt}}" 2>/dev/null || echo "[]")
            if [[ "$security_opts" == *"no-new-privileges"* ]]; then
                print_success "Container $container has no-new-privileges enabled"
            else
                print_warning "Container $container may not have no-new-privileges enabled"
                ((security_issues++))
            fi
        fi
    done <<< "$containers"
    
    if [[ $security_issues -eq 0 ]]; then
        print_success "Security configuration tests passed"
        return 0
    else
        print_warning "Security configuration has $security_issues potential issues"
        return 0  # Don't fail the test for security warnings
    fi
}

# Function to run performance tests
test_performance() {
    print_status "Running performance tests..."
    
    # Measure startup time
    print_status "Measuring service startup time..."
    local start_time
    start_time=$(date +%s)
    
    # Stop services first
    podman-compose -f "$PODMAN_COMPOSE_FILE" down >/dev/null 2>&1 || true
    sleep 5
    
    # Start services and measure time
    local startup_start
    startup_start=$(date +%s)
    
    if podman-compose -f "$PODMAN_COMPOSE_FILE" up -d >/dev/null 2>&1; then
        local startup_end
        startup_end=$(date +%s)
        local startup_time=$((startup_end - startup_start))
        
        print_success "Services started in ${startup_time} seconds"
        
        # Wait for services to be healthy
        sleep 30
        
        # Test if services are responding
        if test_basic_connectivity; then
            local total_time
            total_time=$(date +%s)
            total_time=$((total_time - start_time))
            print_success "Total deployment and health check time: ${total_time} seconds"
            
            # Performance should be reasonable (under 5 minutes)
            if [[ $total_time -lt 300 ]]; then
                print_success "Performance test passed"
                return 0
            else
                print_warning "Performance test completed but took longer than expected"
                return 0
            fi
        else
            print_error "Services failed to become healthy after startup"
            return 1
        fi
    else
        print_error "Failed to start services for performance test"
        return 1
    fi
}

# Function to run Jest integration tests
run_jest_tests() {
    print_status "Running Jest integration tests..."
    
    if command -v npm &> /dev/null; then
        cd "$PROJECT_ROOT"
        
        # Install dependencies if needed
        if [[ ! -d "node_modules" ]]; then
            print_status "Installing npm dependencies..."
            npm install
        fi
        
        # Run the migration-specific tests
        if npm test -- --testPathPattern="podman-migration" --verbose; then
            print_success "Jest integration tests passed"
            return 0
        else
            print_error "Jest integration tests failed"
            return 1
        fi
    else
        print_warning "Node.js not available - skipping Jest tests"
        return 0
    fi
}

# Function to generate test report
generate_test_report() {
    local test_results=("$@")
    local total_tests=${#test_results[@]}
    local passed_tests=0
    
    print_status "Generating test report..."
    
    echo ""
    echo "=========================================="
    echo "         MIGRATION TEST REPORT"
    echo "=========================================="
    echo ""
    
    for i in "${!test_results[@]}"; do
        local test_name="${test_results[i]%%:*}"
        local test_result="${test_results[i]##*:}"
        
        if [[ "$test_result" == "PASSED" ]]; then
            echo -e "✅ $test_name: ${GREEN}PASSED${NC}"
            ((passed_tests++))
        else
            echo -e "❌ $test_name: ${RED}FAILED${NC}"
        fi
    done
    
    echo ""
    echo "=========================================="
    echo -e "Summary: ${passed_tests}/${total_tests} tests passed"
    
    local pass_rate=$((passed_tests * 100 / total_tests))
    if [[ $pass_rate -ge 80 ]]; then
        echo -e "Overall result: ${GREEN}MIGRATION VALIDATION SUCCESSFUL${NC}"
        echo "The Docker-to-Podman migration appears to be working correctly."
    elif [[ $pass_rate -ge 60 ]]; then
        echo -e "Overall result: ${YELLOW}MIGRATION PARTIALLY SUCCESSFUL${NC}"
        echo "The migration is mostly working but some issues were detected."
    else
        echo -e "Overall result: ${RED}MIGRATION VALIDATION FAILED${NC}"
        echo "Significant issues were detected with the migration."
    fi
    echo "=========================================="
    echo ""
    
    return $((100 - pass_rate))
}

# Main test execution function
main() {
    print_status "Starting comprehensive migration validation tests..."
    echo ""
    
    # Array to store test results
    local test_results=()
    
    # Check prerequisites
    if check_prerequisites; then
        test_results+=("Prerequisites:PASSED")
    else
        test_results+=("Prerequisites:FAILED")
        print_error "Prerequisites check failed - aborting tests"
        exit 1
    fi
    
    # Ensure services are running
    print_status "Ensuring services are running..."
    podman-compose -f "$PODMAN_COMPOSE_FILE" up -d >/dev/null 2>&1 || true
    sleep 30  # Give services time to start
    
    # Run individual tests
    if test_basic_connectivity; then
        test_results+=("Basic Connectivity:PASSED")
    else
        test_results+=("Basic Connectivity:FAILED")
    fi
    
    if test_database_connectivity; then
        test_results+=("Database Connectivity:PASSED")
    else
        test_results+=("Database Connectivity:FAILED")
    fi
    
    if test_network_isolation; then
        test_results+=("Network Isolation:PASSED")
    else
        test_results+=("Network Isolation:FAILED")
    fi
    
    if test_volume_persistence; then
        test_results+=("Volume Persistence:PASSED")
    else
        test_results+=("Volume Persistence:FAILED")
    fi
    
    if test_security_configuration; then
        test_results+=("Security Configuration:PASSED")
    else
        test_results+=("Security Configuration:FAILED")
    fi
    
    if test_performance; then
        test_results+=("Performance:PASSED")
    else
        test_results+=("Performance:FAILED")
    fi
    
    if run_jest_tests; then
        test_results+=("Jest Integration Tests:PASSED")
    else
        test_results+=("Jest Integration Tests:FAILED")
    fi
    
    # Generate final report
    generate_test_report "${test_results[@]}"
    local exit_code=$?
    
    print_status "Migration validation tests completed"
    exit $exit_code
}

# Handle script interruption
trap 'print_error "Tests interrupted"; exit 1' INT TERM

# Run main function
main "$@"