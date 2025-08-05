# Docker-to-Podman Migration Testing Guide

This document describes the comprehensive testing suite for validating the Docker-to-Podman migration in the Phoenix Hydra system.

## Overview

The migration testing suite consists of multiple test layers designed to validate:

1. **Service Startup**: All services start correctly with Podman
2. **Network Connectivity**: Inter-service communication works properly
3. **Data Persistence**: PostgreSQL data persists across restarts
4. **Performance**: Startup times and resource usage are acceptable
5. **Security**: Rootless execution and proper isolation
6. **Compatibility**: Feature parity with Docker setup

## Test Structure

```
__tests__/
├── deployment.integration.test.js      # Original deployment test
├── podman-migration.integration.test.js # Comprehensive migration tests
└── performance-comparison.test.js       # Docker vs Podman performance

scripts/
├── test-migration.sh                   # Bash test runner
└── test-migration.ps1                  # PowerShell test runner

docs/
└── migration-testing.md               # This documentation
```

## Running Tests

### Prerequisites

Before running tests, ensure you have:

- **Podman** installed and configured
- **podman-compose** installed (`pip install podman-compose`)
- **Node.js** and **npm** for Jest tests
- **curl** for health checks
- **Docker** (optional, for performance comparison)

### Quick Test Commands

```bash
# Run all migration tests
npm run test:migration

# Run performance comparison tests
npm run test:performance

# Run all new tests
npm run test:all

# Run original deployment test
npm run test:original

# Run comprehensive shell script tests
./scripts/test-migration.sh

# Run PowerShell tests (Windows)
./scripts/test-migration.ps1
```

### Detailed Test Execution

#### 1. Jest Integration Tests

```bash
# Install dependencies
npm install

# Run specific test suites
npm test -- --testPathPattern="podman-migration" --verbose
npm test -- --testPathPattern="performance-comparison" --verbose

# Run with custom timeout
npm test -- --testTimeout=300000
```

#### 2. Shell Script Tests

```bash
# Make script executable (Linux/macOS)
chmod +x scripts/test-migration.sh

# Run comprehensive tests
./scripts/test-migration.sh

# Run with options
./scripts/test-migration.sh --help
```

#### 3. PowerShell Tests

```powershell
# Run comprehensive tests
./scripts/test-migration.ps1

# Skip Jest tests
./scripts/test-migration.ps1 -SkipJest

# Verbose output
./scripts/test-migration.ps1 -Verbose
```

## Test Categories

### 1. Service Startup Tests

**Purpose**: Verify all services start correctly with Podman

**Tests**:
- ✅ All services start without errors
- ✅ Proper user namespace mapping (non-root execution)
- ✅ Security options applied (no-new-privileges)
- ✅ Dependency resolution works correctly

**Expected Results**:
- All 7 services should start successfully
- Containers should run as non-root users (1000:1000)
- Security options should be properly configured

### 2. Health Check Tests

**Purpose**: Verify all exposed services respond to health checks

**Services Tested**:
- **gap-detector** (port 8000): `/health` endpoint
- **analysis-engine** (port 5000): `/health` endpoint  
- **windmill** (port 3000): `/api/version` endpoint
- **nginx** (port 8080): `/health` endpoint

**Expected Results**:
- At least 75% of services should respond within 30 seconds
- Health endpoints should return HTTP 200 status
- Services should be accessible on expected ports

### 3. Network Connectivity Tests

**Purpose**: Verify proper network isolation and inter-service communication

**Tests**:
- ✅ Phoenix network (`phoenix-hydra_phoenix-net`) exists
- ✅ DNS resolution between containers works
- ✅ Database connectivity from application services
- ✅ Network isolation prevents external access to internal services

**Expected Results**:
- Custom bridge network should be created
- Services should resolve each other by name
- Database should be accessible only from within the network

### 4. Data Persistence Tests

**Purpose**: Verify PostgreSQL data persists correctly

**Tests**:
- ✅ Database volume is properly mounted
- ✅ Write permissions work correctly
- ✅ Data survives container restarts
- ✅ Volume permissions are secure (700 for database)

**Expected Results**:
- Database should accept connections
- Test data should persist across restarts
- Volume should have proper ownership and permissions

### 5. Security Tests

**Purpose**: Verify rootless execution and security boundaries

**Tests**:
- ✅ All containers run in rootless mode
- ✅ User namespace mapping is configured
- ✅ Security options are applied
- ✅ Network isolation prevents unauthorized access

**Expected Results**:
- No containers should run as root (UID 0)
- `no-new-privileges` should be enabled
- Containers should use user namespace mapping

### 6. Performance Tests

**Purpose**: Measure and compare performance metrics

**Metrics**:
- **Startup Time**: Time to start all services
- **Total Deployment Time**: Time until all services are healthy
- **Resource Usage**: CPU and memory consumption
- **Response Times**: Average response time for health checks

**Expected Results**:
- Total deployment should complete within 5 minutes
- No container should consistently use >80% CPU or memory
- Response times should be reasonable (<1000ms average)

### 7. Performance Comparison Tests

**Purpose**: Compare Docker vs Podman performance

**Comparisons**:
- Startup time differences
- Resource usage differences  
- Response time differences
- Service reliability comparison

**Expected Results**:
- Podman should not be more than 50% slower than Docker
- Resource usage should be comparable or better
- At least the same number of services should be healthy

## Test Configuration

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  verbose: true,
  testTimeout: 300000, // 5 minutes for integration tests
  testMatch: [
    "**/__tests__/**/*.test.js"
  ]
};
```

### Service Endpoints

| Service             | Port | Health Check Path | Notes                    |
| ------------------- | ---- | ----------------- | ------------------------ |
| gap-detector        | 8000 | `/health`         | Main application service |
| analysis-engine     | 5000 | `/health`         | AI analysis service      |
| windmill            | 3000 | `/api/version`    | Workflow engine          |
| nginx               | 8080 | `/health`         | Reverse proxy            |
| db                  | 5432 | N/A (internal)    | PostgreSQL database      |
| recurrent-processor | N/A  | N/A (internal)    | Background processor     |
| rubik-agent         | N/A  | N/A (internal)    | Agent service            |

### Network Configuration

- **Network Name**: `phoenix-hydra_phoenix-net`
- **Subnet**: `172.20.0.0/16`
- **Gateway**: `172.20.0.1`
- **Driver**: `bridge`
- **Isolation**: Enabled

### Volume Configuration

- **Database Volume**: `${HOME}/.local/share/phoenix-hydra/db_data`
- **Nginx Config**: `${HOME}/.local/share/phoenix-hydra/nginx_config`
- **Permissions**: 700 for database, 755 for configs

## Troubleshooting

### Common Issues

#### 1. Services Not Starting

**Symptoms**: Containers exit immediately or fail to start

**Solutions**:
- Check Podman installation: `podman --version`
- Verify rootless setup: `podman system info`
- Check user namespace mapping: `/etc/subuid` and `/etc/subgid`
- Review container logs: `podman logs <container_name>`

#### 2. Network Connectivity Issues

**Symptoms**: Services can't communicate with each other

**Solutions**:
- Verify network exists: `podman network ls`
- Check network configuration: `podman network inspect phoenix-hydra_phoenix-net`
- Test DNS resolution: `podman exec <container> nslookup <service>`
- Restart networking: `podman network rm phoenix-hydra_phoenix-net && podman-compose up -d`

#### 3. Permission Issues

**Symptoms**: Volume mounting fails or database can't write

**Solutions**:
- Check directory permissions: `ls -la ~/.local/share/phoenix-hydra/`
- Fix ownership: `chown -R $(id -u):$(id -g) ~/.local/share/phoenix-hydra/`
- Verify user namespace mapping: `podman unshare cat /proc/self/uid_map`

#### 4. Performance Issues

**Symptoms**: Slow startup or high resource usage

**Solutions**:
- Check system resources: `podman stats`
- Review container resource limits
- Optimize Containerfiles for better caching
- Consider using `podman system prune` to clean up

### Debug Commands

```bash
# Check Podman system information
podman system info

# List all containers
podman ps -a

# Check container logs
podman logs <container_name>

# Inspect container configuration
podman inspect <container_name>

# Check network configuration
podman network inspect phoenix-hydra_phoenix-net

# Check volume mounts
podman volume ls
podman volume inspect <volume_name>

# Test service connectivity
curl -f http://localhost:8000/health
curl -f http://localhost:3000/api/version
curl -f http://localhost:8080/health

# Check resource usage
podman stats --no-stream

# Test database connectivity
podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT version();"
```

## Test Results Interpretation

### Success Criteria

A successful migration should meet these criteria:

- ✅ **95%+ test pass rate**: At least 95% of tests should pass
- ✅ **All services healthy**: All exposed services should respond to health checks
- ✅ **Network isolation**: Services should communicate only through the defined network
- ✅ **Data persistence**: Database should maintain data across restarts
- ✅ **Security compliance**: All containers should run rootless with proper security options
- ✅ **Performance acceptable**: Startup time should be under 5 minutes, resource usage reasonable

### Warning Conditions

These conditions indicate potential issues but don't fail the migration:

- ⚠️ **75-94% test pass rate**: Some tests failing but core functionality works
- ⚠️ **Slow performance**: Startup time over 3 minutes but under 5 minutes
- ⚠️ **High resource usage**: Containers using 60-80% of system resources
- ⚠️ **Intermittent connectivity**: Occasional network timeouts

### Failure Conditions

These conditions indicate migration failure:

- ❌ **<75% test pass rate**: Too many critical tests failing
- ❌ **Services not starting**: Core services fail to start or stay running
- ❌ **Network isolation broken**: Services accessible from outside the network
- ❌ **Data loss**: Database data not persisting across restarts
- ❌ **Security violations**: Containers running as root or with excessive privileges
- ❌ **Performance unacceptable**: Startup time over 5 minutes or excessive resource usage

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Podman Migration Tests
on: [push, pull_request]

jobs:
  migration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
          pip install podman-compose
          
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm install
        
      - name: Run migration tests
        run: |
          npm run test:migration
          
      - name: Run performance tests
        run: |
          npm run test:performance
          
      - name: Run shell script tests
        run: |
          chmod +x scripts/test-migration.sh
          ./scripts/test-migration.sh
```

### Local Development Workflow

1. **Pre-commit**: Run quick tests before committing
   ```bash
   npm run test:migration
   ```

2. **Pre-push**: Run comprehensive tests before pushing
   ```bash
   ./scripts/test-migration.sh
   ```

3. **Release**: Run full performance comparison
   ```bash
   npm run test:all
   ```

## Maintenance

### Regular Test Updates

- **Monthly**: Review and update test timeouts based on performance trends
- **Quarterly**: Add new test cases for new features or discovered edge cases
- **Annually**: Review and optimize test suite performance

### Test Data Management

- Clean up test data after each run
- Use unique identifiers for test data to avoid conflicts
- Implement proper cleanup in test teardown phases

### Documentation Updates

- Keep this document updated with new test cases
- Document any new troubleshooting procedures
- Update expected results as the system evolves

## Conclusion

This comprehensive testing suite ensures that the Docker-to-Podman migration maintains all functionality while improving security through rootless execution. The tests provide confidence that the migration is successful and the system is ready for production use.

For questions or issues with the testing suite, refer to the troubleshooting section or consult the Phoenix Hydra development team.