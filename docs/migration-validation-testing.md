# Migration Validation Testing Guide

This document provides comprehensive guidance for running and understanding the Docker-to-Podman migration validation tests for Phoenix Hydra.

## Overview

The migration validation test suite ensures that the Docker-to-Podman migration maintains all functionality while improving security and performance. The tests cover four main areas:

1. **Integration Tests** - Verify all services start correctly with Podman
2. **Network Connectivity Tests** - Validate inter-service communication
3. **Data Persistence Tests** - Ensure PostgreSQL volume persistence
4. **Performance Comparison Tests** - Compare Docker and Podman performance

## Requirements Coverage

The test suite validates the following requirements from the migration specification:

- **Requirement 1.3**: Migration validation and testing
- **Requirement 3.2**: Service communication and networking  
- **Requirement 5.2**: Network connectivity and DNS resolution

## Test Files

### Core Test Files

| File                                                   | Purpose                        | Coverage                       |
| ------------------------------------------------------ | ------------------------------ | ------------------------------ |
| `__tests__/comprehensive-migration-validation.test.js` | Complete end-to-end validation | All requirements               |
| `__tests__/migration-validation.test.js`               | Basic migration functionality  | Service startup, health checks |
| `__tests__/network-connectivity.test.js`               | Network communication testing  | Inter-service connectivity     |
| `__tests__/performance-comparison.test.js`             | Performance benchmarking       | Docker vs Podman metrics       |
| `__tests__/podman-migration.integration.test.js`       | Integration testing            | Service integration            |

### Test Runners

| File                                    | Platform       | Purpose                |
| --------------------------------------- | -------------- | ---------------------- |
| `scripts/test-migration-validation.js`  | Cross-platform | Node.js test runner    |
| `scripts/test-migration-validation.ps1` | Windows        | PowerShell test runner |

## Prerequisites

Before running the migration validation tests, ensure the following are installed:

### Required Software

1. **Podman** - Container runtime
   ```bash
   # Installation varies by platform
   # See: https://podman.io/getting-started/installation
   ```

2. **podman-compose** - Container orchestration
   ```bash
   pip install podman-compose
   ```

3. **Node.js** - JavaScript runtime
   ```bash
   # Version 16+ recommended
   node --version
   ```

4. **npm/Jest** - Testing framework
   ```bash
   npm install
   npx jest --version
   ```

### Required Files

- `infra/podman/podman-compose.yaml` - Podman compose configuration
- `compose.yaml` - Original Docker compose (for comparison)
- All Containerfiles in `infra/podman/*/`

## Running Tests

### Quick Start

```bash
# Run all migration validation tests
node scripts/test-migration-validation.js

# Or using PowerShell (Windows)
.\scripts\test-migration-validation.ps1
```

### Advanced Usage

```bash
# Run specific test pattern
node scripts/test-migration-validation.js --pattern="Integration Tests"

# Skip environment cleanup
node scripts/test-migration-validation.js --skip-cleanup

# Generate report only
node scripts/test-migration-validation.js --report-only

# Show help
node scripts/test-migration-validation.js --help
```

### Manual Test Execution

```bash
# Run individual test files
npx jest __tests__/comprehensive-migration-validation.test.js --verbose
npx jest __tests__/network-connectivity.test.js --verbose
npx jest __tests__/performance-comparison.test.js --verbose

# Run all tests with specific timeout
npx jest --testTimeout=600000 --runInBand --forceExit
```

## Test Categories

### 1. Integration Tests - Service Startup Validation

**Purpose**: Verify all services start correctly with Podman

**Tests Include**:
- Service startup with detailed monitoring
- Container status verification
- User namespace mapping validation
- Health check endpoint testing
- Service response time measurement

**Expected Results**:
- All services start within 5 minutes
- At least 75% of services pass health checks
- All containers run in rootless mode
- Average response time < 2 seconds

### 2. Network Connectivity Tests

**Purpose**: Validate inter-service communication and networking

**Tests Include**:
- Database connectivity from application services
- HTTP communication between web services
- DNS resolution between all services
- Network latency measurements
- Network isolation and security validation

**Expected Results**:
- Database connections successful from all app services
- At least 50% of HTTP connections work
- DNS resolution works for critical service pairs
- Network latency < 100ms average
- External access works for exposed ports

### 3. Data Persistence Tests

**Purpose**: Ensure PostgreSQL volume persistence and data integrity

**Tests Include**:
- Basic database connection testing
- Table creation and schema operations
- Data insertion with various data types
- Complex query and retrieval testing
- Data integrity and constraint validation
- Transaction support and rollback testing
- Persistence across container restarts
- Persistence across full stack restarts

**Expected Results**:
- All database operations succeed
- Data persists across container restarts
- Data persists across full stack restarts
- Transaction support works correctly
- Restart operations complete within reasonable time

### 4. Performance Comparison Tests

**Purpose**: Compare Docker and Podman performance metrics

**Tests Include**:
- Startup time measurement
- Service health check timing
- Resource usage analysis (CPU, Memory)
- Service response time benchmarking
- Docker vs Podman comparison (if Docker available)

**Expected Results**:
- Podman startup time < 5 minutes
- Resource usage within acceptable limits (CPU < 80%, Memory < 90%)
- Podman performance comparable to Docker (within 2x)
- Service response times reasonable (< 2 seconds average)

## Test Configuration

### Jest Configuration

The tests use a custom Jest configuration optimized for integration testing:

```javascript
{
  verbose: true,
  testTimeout: 600000, // 10 minutes
  maxWorkers: 1, // Sequential execution
  forceExit: true,
  detectOpenHandles: true
}
```

### Environment Variables

The tests can be configured using environment variables:

| Variable              | Purpose                      | Default                            |
| --------------------- | ---------------------------- | ---------------------------------- |
| `TEST_TIMEOUT`        | Test timeout in milliseconds | 600000                             |
| `PODMAN_COMPOSE_FILE` | Path to Podman compose file  | `infra/podman/podman-compose.yaml` |
| `DOCKER_COMPOSE_FILE` | Path to Docker compose file  | `compose.yaml`                     |
| `SKIP_DOCKER_TESTS`   | Skip Docker comparison tests | `false`                            |

## Troubleshooting

### Common Issues

#### 1. Podman Not Found
```
Error: Podman is not installed or not accessible
```
**Solution**: Install Podman following the official installation guide

#### 2. podman-compose Not Found
```
Error: podman-compose is not installed or not accessible
```
**Solution**: Install podman-compose using pip:
```bash
pip install podman-compose
```

#### 3. Services Not Starting
```
Error: Failed to start services
```
**Solutions**:
- Check if ports are already in use
- Verify compose file syntax
- Check container logs: `podman logs <container-name>`
- Clean up existing containers: `podman container prune -f`

#### 4. Network Connectivity Issues
```
Error: Network connectivity test failed
```
**Solutions**:
- Verify network exists: `podman network ls`
- Check DNS resolution: `podman exec <container> nslookup <service>`
- Verify firewall settings
- Check container network configuration

#### 5. Database Connection Issues
```
Error: Database connection failed
```
**Solutions**:
- Wait longer for database initialization
- Check database logs: `podman logs phoenix-hydra_db_1`
- Verify database credentials
- Check volume mounting

#### 6. Performance Test Failures
```
Error: Performance metrics outside acceptable range
```
**Solutions**:
- Check system resources
- Close other applications
- Increase timeout values
- Run tests on dedicated hardware

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export DEBUG=1
node scripts/test-migration-validation.js

# Or run Jest with verbose output
npx jest --verbose --runInBand __tests__/comprehensive-migration-validation.test.js
```

### Log Analysis

Test logs are output to the console. Key log patterns:

- `✅` - Successful operations
- `❌` - Failed operations  
- `⚠️` - Warnings or partial failures
- `🔍` - Test progress indicators
- `📊` - Performance metrics
- `🧹` - Cleanup operations

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Migration Validation Tests
on: [push, pull_request]

jobs:
  migration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install Podman
        run: |
          sudo apt-get update
          sudo apt-get install -y podman
          
      - name: Install podman-compose
        run: pip install podman-compose
        
      - name: Install dependencies
        run: npm install
        
      - name: Run migration validation tests
        run: node scripts/test-migration-validation.js
        
      - name: Upload test report
        uses: actions/upload-artifact@v3
        with:
          name: migration-validation-report
          path: migration-validation-report.md
```

### Local CI Setup

```bash
# Create a local CI script
cat > scripts/ci-migration-tests.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Running CI Migration Validation Tests"

# Clean environment
podman system prune -f

# Run tests
node scripts/test-migration-validation.js

# Check results
if [ -f "migration-validation-report.md" ]; then
    echo "✅ Tests completed successfully"
    cat migration-validation-report.md
else
    echo "❌ Tests failed - no report generated"
    exit 1
fi
EOF

chmod +x scripts/ci-migration-tests.sh
```

## Test Metrics and Reporting

### Automated Reporting

The test suite generates a comprehensive report (`migration-validation-report.md`) that includes:

- Test execution summary
- Performance metrics
- Requirements validation status
- Environment information
- Next steps and recommendations

### Key Performance Indicators (KPIs)

| Metric                    | Target      | Measurement                                  |
| ------------------------- | ----------- | -------------------------------------------- |
| Service Startup Time      | < 5 minutes | Time to all services healthy                 |
| Health Check Success Rate | > 75%       | Percentage of services passing health checks |
| Network Connectivity Rate | > 80%       | Percentage of successful network tests       |
| Data Persistence Success  | 100%        | All persistence tests must pass              |
| Resource Usage (CPU)      | < 80%       | Average CPU usage across containers          |
| Resource Usage (Memory)   | < 90%       | Average memory usage across containers       |

### Custom Metrics Collection

```javascript
// Example custom metrics collection
const metrics = {
  startupTime: Date.now() - startTime,
  healthyServices: healthResults.filter(r => r.healthy).length,
  networkLatency: avgLatency,
  resourceUsage: { cpu: avgCpu, memory: avgMem }
};

// Export metrics for external monitoring
fs.writeFileSync('test-metrics.json', JSON.stringify(metrics, null, 2));
```

## Best Practices

### Test Development

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always clean up resources after tests complete
3. **Timeouts**: Use appropriate timeouts for different types of operations
4. **Error Handling**: Provide clear error messages and debugging information
5. **Logging**: Include detailed logging for troubleshooting

### Test Execution

1. **Sequential Execution**: Run tests sequentially to avoid resource conflicts
2. **Environment Preparation**: Always start with a clean environment
3. **Resource Monitoring**: Monitor system resources during test execution
4. **Regular Execution**: Run tests regularly to catch regressions early
5. **Documentation**: Keep test documentation up to date

### Performance Testing

1. **Baseline Establishment**: Establish performance baselines for comparison
2. **Consistent Environment**: Use consistent hardware and environment for testing
3. **Multiple Runs**: Run performance tests multiple times for accuracy
4. **Resource Isolation**: Ensure no other processes interfere with tests
5. **Trend Analysis**: Track performance trends over time

## Future Enhancements

### Planned Improvements

1. **Chaos Testing**: Add chaos engineering tests for resilience validation
2. **Load Testing**: Include load testing for performance under stress
3. **Security Testing**: Add security vulnerability scanning
4. **Monitoring Integration**: Integrate with monitoring systems
5. **Automated Remediation**: Add automated issue remediation

### Extension Points

The test framework is designed to be extensible:

```javascript
// Add custom test categories
describe("Custom Migration Tests", () => {
  test("should validate custom requirement", async () => {
    // Custom test implementation
  });
});

// Add custom metrics collection
const customMetrics = await collectCustomMetrics();
performanceResults.custom = customMetrics;
```

## Support and Maintenance

### Getting Help

1. **Documentation**: Check this guide and inline code comments
2. **Logs**: Review test execution logs for error details
3. **Issues**: Create GitHub issues for bugs or feature requests
4. **Community**: Engage with the Phoenix Hydra community

### Maintenance Schedule

- **Weekly**: Run full test suite
- **Monthly**: Review and update test cases
- **Quarterly**: Performance baseline updates
- **Annually**: Major test framework updates

---

*This documentation is maintained as part of the Phoenix Hydra project. For updates and contributions, please refer to the project's contribution guidelines.*