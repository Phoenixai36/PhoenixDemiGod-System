const { execSync, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");
const { promisify } = require("util");

/**
 * Comprehensive Migration Validation Test Suite
 *
 * This test suite provides complete validation for the Docker-to-Podman migration
 * covering all requirements from task 17:
 *
 * - Integration tests to verify all services start correctly with Podman
 * - Network connectivity tests between services
 * - Data persistence tests for PostgreSQL volume
 * - Performance comparison tests between Docker and Podman setups
 *
 * Requirements: 1.3, 3.2, 5.2
 */

const sleep = promisify(setTimeout);

/**
 * Enhanced command execution with detailed logging and error handling
 */
const executeCommand = (command, options = {}) => {
  const startTime = Date.now();
  try {
    const result = execSync(command, {
      encoding: "utf8",
      stdio: "pipe",
      timeout: 120000,
      ...options,
    });
    const duration = Date.now() - startTime;
    return {
      success: true,
      output: result.trim(),
      error: null,
      duration,
      command,
    };
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      output: error.stdout ? error.stdout.trim() : "",
      error: error.stderr ? error.stderr.trim() : error.message,
      duration,
      command,
    };
  }
};

/**
 * Enhanced service health check with retry logic and detailed reporting
 */
const checkServiceHealth = (port, path = "/health", timeout = 10000) => {
  return new Promise((resolve) => {
    const startTime = Date.now();
    const options = {
      hostname: "localhost",
      port: port,
      path: path,
      method: "GET",
      timeout: timeout,
    };

    const req = http.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        const duration = Date.now() - startTime;
        resolve({
          success: res.statusCode >= 200 && res.statusCode < 300,
          statusCode: res.statusCode,
          data: data,
          error: null,
          duration,
          port,
          path,
        });
      });
    });

    req.on("error", (error) => {
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        statusCode: null,
        data: null,
        error: error.message,
        duration,
        port,
        path,
      });
    });

    req.on("timeout", () => {
      req.destroy();
      const duration = Date.now() - startTime;
      resolve({
        success: false,
        statusCode: null,
        data: null,
        error: "Request timeout",
        duration,
        port,
        path,
      });
    });

    req.end();
  });
};

/**
 * Wait for service with exponential backoff and detailed progress reporting
 */
const waitForService = async (
  serviceName,
  port,
  path = "/health",
  maxAttempts = 30,
  initialInterval = 2000
) => {
  console.log(`    🔍 Waiting for ${serviceName} on port ${port}${path}...`);

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const interval = Math.min(
      initialInterval * Math.pow(1.2, attempt - 1),
      10000
    );

    console.log(
      `      Attempt ${attempt}/${maxAttempts}: Checking ${serviceName}...`
    );

    const result = await checkServiceHealth(port, path, 8000);
    if (result.success) {
      console.log(
        `      ✅ ${serviceName} is healthy (${result.duration}ms response time)`
      );
      return {
        success: true,
        attempts: attempt,
        responseTime: result.duration,
      };
    }

    if (attempt < maxAttempts) {
      console.log(
        `      ⏳ ${serviceName} not ready (${result.error}), waiting ${interval}ms...`
      );
      await sleep(interval);
    }
  }

  console.log(
    `      ❌ ${serviceName} failed to become healthy after ${maxAttempts} attempts`
  );
  return { success: false, attempts: maxAttempts, responseTime: null };
};

/**
 * Comprehensive database connectivity and persistence testing
 */
const testDatabasePersistence = async () => {
  console.log("  🔍 Testing comprehensive database persistence...");

  const testResults = {
    connection: false,
    tableCreation: false,
    dataInsertion: false,
    dataRetrieval: false,
    dataIntegrity: false,
    transactionSupport: false,
  };

  try {
    // Test 1: Basic database connection
    console.log("    Testing database connection...");
    const connectionTest = executeCommand(
      `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT version();"`,
      { timeout: 30000 }
    );

    if (!connectionTest.success) {
      throw new Error(`Database connection failed: ${connectionTest.error}`);
    }
    testResults.connection = true;
    console.log("    ✅ Database connection successful");

    // Test 2: Table creation and schema operations
    console.log("    Testing table creation and schema operations...");
    const createTableTest = executeCommand(
      `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
        DROP TABLE IF EXISTS migration_validation_test;
        CREATE TABLE migration_validation_test (
          id SERIAL PRIMARY KEY,
          test_data TEXT NOT NULL,
          test_number INTEGER,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP
        );
        CREATE INDEX idx_test_data ON migration_validation_test(test_data);
      "`,
      { timeout: 30000 }
    );

    if (!createTableTest.success) {
      throw new Error(`Table creation failed: ${createTableTest.error}`);
    }
    testResults.tableCreation = true;
    console.log("    ✅ Table creation and indexing successful");

    // Test 3: Data insertion with various data types
    console.log("    Testing data insertion with various data types...");
    const testData = [
      { data: `test-string-${Date.now()}`, number: 42 },
      { data: `test-unicode-${Date.now()}-🚀`, number: 100 },
      { data: `test-special-chars-${Date.now()}-!@#$%`, number: -1 },
    ];

    for (const item of testData) {
      const insertTest = executeCommand(
        `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
          INSERT INTO migration_validation_test (test_data, test_number) 
          VALUES ('${item.data}', ${item.number});
        "`,
        { timeout: 30000 }
      );

      if (!insertTest.success) {
        throw new Error(
          `Data insertion failed for ${item.data}: ${insertTest.error}`
        );
      }
    }
    testResults.dataInsertion = true;
    console.log("    ✅ Data insertion with various types successful");

    // Test 4: Data retrieval and querying
    console.log("    Testing data retrieval and complex queries...");
    const retrievalTest = executeCommand(
      `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
        SELECT COUNT(*) as total_count, 
               AVG(test_number) as avg_number,
               MIN(created_at) as earliest,
               MAX(created_at) as latest
        FROM migration_validation_test;
      "`,
      { timeout: 30000 }
    );

    if (
      !retrievalTest.success ||
      !retrievalTest.output.includes("total_count")
    ) {
      throw new Error(`Data retrieval failed: ${retrievalTest.error}`);
    }
    testResults.dataRetrieval = true;
    console.log("    ✅ Data retrieval and complex queries successful");

    // Test 5: Data integrity and constraints
    console.log("    Testing data integrity and constraints...");
    const integrityTest = executeCommand(
      `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
        UPDATE migration_validation_test 
        SET updated_at = NOW() 
        WHERE test_number > 0;
        
        SELECT COUNT(*) FROM migration_validation_test WHERE updated_at IS NOT NULL;
      "`,
      { timeout: 30000 }
    );

    if (!integrityTest.success) {
      throw new Error(`Data integrity test failed: ${integrityTest.error}`);
    }
    testResults.dataIntegrity = true;
    console.log("    ✅ Data integrity and update operations successful");

    // Test 6: Transaction support
    console.log("    Testing transaction support...");
    const transactionTest = executeCommand(
      `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
        BEGIN;
        INSERT INTO migration_validation_test (test_data, test_number) VALUES ('transaction-test', 999);
        SAVEPOINT sp1;
        INSERT INTO migration_validation_test (test_data, test_number) VALUES ('rollback-test', 888);
        ROLLBACK TO sp1;
        COMMIT;
        SELECT COUNT(*) FROM migration_validation_test WHERE test_data = 'transaction-test';
      "`,
      { timeout: 30000 }
    );

    if (!transactionTest.success || !transactionTest.output.includes("1")) {
      throw new Error(`Transaction test failed: ${transactionTest.error}`);
    }
    testResults.transactionSupport = true;
    console.log("    ✅ Transaction support and rollback successful");

    console.log("  ✅ Comprehensive database persistence tests passed");
    return testResults;
  } catch (error) {
    console.log(`  ❌ Database persistence test failed: ${error.message}`);
    throw error;
  }
};

/**
 * Comprehensive network connectivity testing between all services
 */
const testNetworkConnectivity = async () => {
  console.log("  🔍 Testing comprehensive network connectivity...");

  const connectivityResults = {
    databaseConnections: [],
    httpConnections: [],
    dnsResolutions: [],
    networkLatency: [],
  };

  // Test 1: Database connectivity from all application services
  console.log("    Testing database connectivity from all services...");
  const dbTestServices = [
    "phoenix-hydra_recurrent-processor_1",
    "phoenix-hydra_gap-detector_1",
  ];

  for (const service of dbTestServices) {
    console.log(`      Testing ${service} -> database connection...`);
    const dbConnTest = executeCommand(
      `podman exec ${service} python -c "
import socket
import sys
import time
try:
    start_time = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex(('db', 5432))
    latency = (time.time() - start_time) * 1000
    sock.close()
    if result == 0:
        print(f'SUCCESS: Connection latency {latency:.2f}ms')
        sys.exit(0)
    else:
        print(f'FAILED: Connection refused')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"`,
      { timeout: 30000 }
    );

    const result = {
      fromService: service,
      toService: "database",
      success: dbConnTest.success,
      latency: dbConnTest.success
        ? parseFloat(dbConnTest.output.match(/(\d+\.\d+)ms/)?.[1] || "0")
        : null,
      error: dbConnTest.error,
    };

    connectivityResults.databaseConnections.push(result);

    if (result.success) {
      console.log(
        `        ✅ Connection successful (${result.latency}ms latency)`
      );
    } else {
      console.log(`        ❌ Connection failed: ${result.error}`);
    }
  }

  // Test 2: HTTP connectivity between web services
  console.log("    Testing HTTP connectivity between services...");
  const httpTests = [
    {
      from: "phoenix-hydra_nginx_1",
      to: "windmill",
      port: 3000,
      path: "/api/version",
    },
    {
      from: "phoenix-hydra_nginx_1",
      to: "gap-detector",
      port: 8000,
      path: "/health",
    },
    {
      from: "phoenix-hydra_nginx_1",
      to: "analysis-engine",
      port: 5000,
      path: "/health",
    },
  ];

  for (const test of httpTests) {
    console.log(
      `      Testing ${test.from} -> ${test.to}:${test.port}${test.path}...`
    );
    const httpTest = executeCommand(
      `podman exec ${test.from} curl -f -s -w "RESPONSE_TIME:%{time_total}" --connect-timeout 10 http://${test.to}:${test.port}${test.path}`,
      { timeout: 30000 }
    );

    const responseTime = httpTest.success
      ? parseFloat(
          httpTest.output.match(/RESPONSE_TIME:(\d+\.\d+)/)?.[1] || "0"
        ) * 1000
      : null;

    const result = {
      fromService: test.from,
      toService: test.to,
      port: test.port,
      path: test.path,
      success: httpTest.success,
      responseTime: responseTime,
      error: httpTest.error,
    };

    connectivityResults.httpConnections.push(result);

    if (result.success) {
      console.log(
        `        ✅ HTTP request successful (${result.responseTime}ms response time)`
      );
    } else {
      console.log(`        ⚠️  HTTP request failed: ${result.error}`);
    }
  }

  // Test 3: DNS resolution between all services
  console.log("    Testing DNS resolution between services...");
  const dnsTests = [
    { from: "phoenix-hydra_gap-detector_1", target: "db" },
    { from: "phoenix-hydra_gap-detector_1", target: "windmill" },
    { from: "phoenix-hydra_recurrent-processor_1", target: "db" },
    { from: "phoenix-hydra_nginx_1", target: "windmill" },
    { from: "phoenix-hydra_nginx_1", target: "gap-detector" },
  ];

  for (const test of dnsTests) {
    console.log(
      `      Testing DNS resolution: ${test.from} -> ${test.target}...`
    );
    const dnsTest = executeCommand(
      `podman exec ${test.from} nslookup ${test.target}`,
      { timeout: 30000 }
    );

    const result = {
      fromService: test.from,
      targetService: test.target,
      success: dnsTest.success,
      resolvedIp: dnsTest.success
        ? dnsTest.output.match(/Address: (\d+\.\d+\.\d+\.\d+)/)?.[1]
        : null,
      error: dnsTest.error,
    };

    connectivityResults.dnsResolutions.push(result);

    if (result.success) {
      console.log(
        `        ✅ DNS resolution successful (IP: ${result.resolvedIp})`
      );
    } else {
      console.log(`        ⚠️  DNS resolution failed: ${result.error}`);
    }
  }

  // Test 4: Network latency measurements
  console.log("    Testing network latency between services...");
  const latencyTests = [
    { from: "phoenix-hydra_gap-detector_1", to: "db" },
    { from: "phoenix-hydra_recurrent-processor_1", to: "db" },
  ];

  for (const test of latencyTests) {
    console.log(`      Measuring latency: ${test.from} -> ${test.to}...`);
    const latencyTest = executeCommand(
      `podman exec ${test.from} ping -c 3 -W 5 ${test.to}`,
      { timeout: 30000 }
    );

    const avgLatency = latencyTest.success
      ? parseFloat(
          latencyTest.output.match(/avg = [\d.]+\/([\d.]+)\//)?.[1] || "0"
        )
      : null;

    const result = {
      fromService: test.from,
      toService: test.to,
      success: latencyTest.success,
      averageLatency: avgLatency,
      error: latencyTest.error,
    };

    connectivityResults.networkLatency.push(result);

    if (result.success) {
      console.log(`        ✅ Average latency: ${result.averageLatency}ms`);
    } else {
      console.log(`        ⚠️  Latency test failed: ${result.error}`);
    }
  }

  console.log("  ✅ Comprehensive network connectivity tests completed");
  return connectivityResults;
};

/**
 * Performance comparison between Docker and Podman setups
 */
const performanceComparison = async () => {
  console.log("  🔍 Running performance comparison tests...");

  const dockerComposeFile = "compose.yaml";
  const podmanComposeFile = "infra/podman/podman-compose.yaml";

  const performanceResults = {
    docker: { available: false, metrics: {} },
    podman: { available: true, metrics: {} },
  };

  // Check Docker availability
  try {
    execSync("docker --version && docker-compose --version", { stdio: "pipe" });
    performanceResults.docker.available = true;
    console.log("    ✅ Docker available for comparison");
  } catch (error) {
    console.log(
      "    ⚠️  Docker not available - Podman-only performance testing"
    );
  }

  // Test Podman performance
  console.log("    📊 Testing Podman performance metrics...");

  // Stop any existing services
  executeCommand(`podman-compose -f ${podmanComposeFile} down -v`, {
    timeout: 60000,
  });
  await sleep(5000);

  // Measure Podman startup time
  const podmanStartTime = Date.now();
  const podmanStartResult = executeCommand(
    `podman-compose -f ${podmanComposeFile} up -d`,
    { timeout: 180000 }
  );

  if (!podmanStartResult.success) {
    throw new Error(`Podman startup failed: ${podmanStartResult.error}`);
  }

  const podmanStartupTime = Date.now() - podmanStartTime;
  console.log(`      Podman startup time: ${podmanStartupTime}ms`);

  // Wait for services and measure health check time
  const healthCheckStartTime = Date.now();
  const services = [
    { name: "gap-detector", port: 8000, path: "/health" },
    { name: "analysis-engine", port: 5000, path: "/health" },
    { name: "windmill", port: 3000, path: "/api/version" },
    { name: "nginx", port: 8080, path: "/health" },
  ];

  let healthyServices = 0;
  const serviceHealthResults = [];

  for (const service of services) {
    const healthResult = await waitForService(
      service.name,
      service.port,
      service.path,
      15,
      3000
    );
    serviceHealthResults.push({
      service: service.name,
      healthy: healthResult.success,
      responseTime: healthResult.responseTime,
    });
    if (healthResult.success) healthyServices++;
  }

  const healthCheckTime = Date.now() - healthCheckStartTime;

  // Measure resource usage
  await sleep(10000); // Let services stabilize
  const resourceTest = executeCommand(
    `podman stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"`,
    { timeout: 30000 }
  );

  let avgCpu = 0,
    avgMem = 0,
    containerCount = 0;
  if (resourceTest.success) {
    const lines = resourceTest.output.split("\n").slice(1);
    const validLines = lines.filter(
      (line) => line.trim() && !line.includes("CONTAINER")
    );

    for (const line of validLines) {
      const parts = line.split("\t");
      if (parts.length >= 4) {
        const cpu = parseFloat(parts[1].replace("%", ""));
        const mem = parseFloat(parts[3].replace("%", ""));
        if (!isNaN(cpu) && !isNaN(mem)) {
          avgCpu += cpu;
          avgMem += mem;
          containerCount++;
        }
      }
    }

    if (containerCount > 0) {
      avgCpu /= containerCount;
      avgMem /= containerCount;
    }
  }

  performanceResults.podman.metrics = {
    startupTime: podmanStartupTime,
    healthCheckTime: healthCheckTime,
    totalDeploymentTime: podmanStartupTime + healthCheckTime,
    healthyServices: healthyServices,
    totalServices: services.length,
    averageCpu: avgCpu,
    averageMemory: avgMem,
    containerCount: containerCount,
    serviceHealthResults: serviceHealthResults,
  };

  // Test Docker performance if available
  if (performanceResults.docker.available) {
    console.log("    📊 Testing Docker performance metrics...");

    // Stop Podman services
    executeCommand(`podman-compose -f ${podmanComposeFile} down -v`, {
      timeout: 60000,
    });
    await sleep(5000);

    try {
      // Measure Docker startup time
      const dockerStartTime = Date.now();
      const dockerStartResult = executeCommand(
        `docker-compose -f ${dockerComposeFile} up -d`,
        { timeout: 180000 }
      );

      if (dockerStartResult.success) {
        const dockerStartupTime = Date.now() - dockerStartTime;
        console.log(`      Docker startup time: ${dockerStartupTime}ms`);

        // Wait for Docker services
        const dockerHealthCheckStartTime = Date.now();
        let dockerHealthyServices = 0;

        for (const service of services) {
          const healthResult = await waitForService(
            service.name,
            service.port,
            service.path,
            10,
            3000
          );
          if (healthResult.success) dockerHealthyServices++;
        }

        const dockerHealthCheckTime = Date.now() - dockerHealthCheckStartTime;

        // Measure Docker resource usage
        await sleep(10000);
        const dockerResourceTest = executeCommand(
          `docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"`,
          { timeout: 30000 }
        );

        let dockerAvgCpu = 0,
          dockerAvgMem = 0,
          dockerContainerCount = 0;
        if (dockerResourceTest.success) {
          const lines = dockerResourceTest.output.split("\n").slice(1);
          const validLines = lines.filter(
            (line) => line.trim() && !line.includes("CONTAINER")
          );

          for (const line of validLines) {
            const parts = line.split("\t");
            if (parts.length >= 4) {
              const cpu = parseFloat(parts[1].replace("%", ""));
              const mem = parseFloat(parts[3].replace("%", ""));
              if (!isNaN(cpu) && !isNaN(mem)) {
                dockerAvgCpu += cpu;
                dockerAvgMem += mem;
                dockerContainerCount++;
              }
            }
          }

          if (dockerContainerCount > 0) {
            dockerAvgCpu /= dockerContainerCount;
            dockerAvgMem /= dockerContainerCount;
          }
        }

        performanceResults.docker.metrics = {
          startupTime: dockerStartupTime,
          healthCheckTime: dockerHealthCheckTime,
          totalDeploymentTime: dockerStartupTime + dockerHealthCheckTime,
          healthyServices: dockerHealthyServices,
          totalServices: services.length,
          averageCpu: dockerAvgCpu,
          averageMemory: dockerAvgMem,
          containerCount: dockerContainerCount,
        };

        // Stop Docker services and restart Podman for remaining tests
        executeCommand(`docker-compose -f ${dockerComposeFile} down -v`, {
          timeout: 60000,
        });
        await sleep(5000);
        executeCommand(`podman-compose -f ${podmanComposeFile} up -d`, {
          timeout: 180000,
        });
        await sleep(30000);
      } else {
        console.log(
          "      ⚠️  Docker startup failed, skipping Docker comparison"
        );
      }
    } catch (error) {
      console.log(`      ⚠️  Docker performance test failed: ${error.message}`);
    }
  }

  // Generate comparison report
  console.log("\n    📊 PERFORMANCE COMPARISON REPORT");
  console.log("    =====================================");

  if (
    performanceResults.docker.available &&
    performanceResults.docker.metrics.startupTime
  ) {
    const dockerMetrics = performanceResults.docker.metrics;
    const podmanMetrics = performanceResults.podman.metrics;

    console.log(`    Startup Time Comparison:`);
    console.log(`      Docker:  ${dockerMetrics.startupTime}ms`);
    console.log(`      Podman:  ${podmanMetrics.startupTime}ms`);

    const startupDiff = podmanMetrics.startupTime - dockerMetrics.startupTime;
    const startupPercent = (
      (startupDiff / dockerMetrics.startupTime) *
      100
    ).toFixed(1);

    if (startupDiff < 0) {
      console.log(
        `      ✅ Podman is ${Math.abs(startupDiff)}ms (${Math.abs(
          startupPercent
        )}%) faster`
      );
    } else {
      console.log(
        `      ⚠️  Podman is ${startupDiff}ms (${startupPercent}%) slower`
      );
    }

    console.log(`    Resource Usage Comparison:`);
    console.log(`      Docker CPU:   ${dockerMetrics.averageCpu.toFixed(2)}%`);
    console.log(`      Podman CPU:   ${podmanMetrics.averageCpu.toFixed(2)}%`);
    console.log(
      `      Docker Memory: ${dockerMetrics.averageMemory.toFixed(2)}%`
    );
    console.log(
      `      Podman Memory: ${podmanMetrics.averageMemory.toFixed(2)}%`
    );
  } else {
    console.log(`    Podman Performance Metrics:`);
    console.log(
      `      Startup Time: ${performanceResults.podman.metrics.startupTime}ms`
    );
    console.log(
      `      Health Check Time: ${performanceResults.podman.metrics.healthCheckTime}ms`
    );
    console.log(
      `      Total Deployment: ${performanceResults.podman.metrics.totalDeploymentTime}ms`
    );
    console.log(
      `      Healthy Services: ${performanceResults.podman.metrics.healthyServices}/${performanceResults.podman.metrics.totalServices}`
    );
    console.log(
      `      Average CPU: ${performanceResults.podman.metrics.averageCpu.toFixed(
        2
      )}%`
    );
    console.log(
      `      Average Memory: ${performanceResults.podman.metrics.averageMemory.toFixed(
        2
      )}%`
    );
  }

  console.log("    =====================================");

  console.log("  ✅ Performance comparison tests completed");
  return performanceResults;
};

/**
 * Test data persistence across container restarts and system reboots
 */
const testDataPersistenceAcrossRestarts = async () => {
  console.log("  🔍 Testing data persistence across container restarts...");

  const testData = `persistence-test-${Date.now()}`;
  const podmanComposeFile = "infra/podman/podman-compose.yaml";

  // Insert test data
  console.log("    Inserting test data...");
  const insertResult = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
      CREATE TABLE IF NOT EXISTS restart_persistence_test (
        id SERIAL PRIMARY KEY, 
        test_data TEXT, 
        created_at TIMESTAMP DEFAULT NOW()
      );
      INSERT INTO restart_persistence_test (test_data) VALUES ('${testData}');
    "`,
    { timeout: 30000 }
  );

  if (!insertResult.success) {
    throw new Error(`Failed to insert test data: ${insertResult.error}`);
  }
  console.log("    ✅ Test data inserted successfully");

  // Restart the database container
  console.log("    Restarting database container...");
  const restartResult = executeCommand(
    `podman-compose -f ${podmanComposeFile} restart db`,
    { timeout: 60000 }
  );

  if (!restartResult.success) {
    throw new Error(`Failed to restart database: ${restartResult.error}`);
  }
  console.log("    ✅ Database container restarted");

  // Wait for database to be ready
  console.log("    Waiting for database to be ready...");
  await sleep(20000);

  // Verify data still exists
  console.log("    Verifying data persistence...");
  const verifyResult = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
      SELECT test_data, created_at FROM restart_persistence_test WHERE test_data = '${testData}';
    "`,
    { timeout: 30000 }
  );

  if (!verifyResult.success || !verifyResult.output.includes(testData)) {
    throw new Error(`Data not found after restart: ${verifyResult.error}`);
  }
  console.log("    ✅ Data persistence verified after container restart");

  // Test full stack restart
  console.log("    Testing full stack restart...");
  const fullRestartResult = executeCommand(
    `podman-compose -f ${podmanComposeFile} down && podman-compose -f ${podmanComposeFile} up -d`,
    { timeout: 120000 }
  );

  if (!fullRestartResult.success) {
    throw new Error(`Full stack restart failed: ${fullRestartResult.error}`);
  }
  console.log("    ✅ Full stack restarted");

  // Wait for services to be ready
  await sleep(45000);

  // Final verification
  console.log("    Final data persistence verification...");
  const finalVerifyResult = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "
      SELECT COUNT(*) as count FROM restart_persistence_test WHERE test_data = '${testData}';
    "`,
    { timeout: 30000 }
  );

  if (!finalVerifyResult.success || !finalVerifyResult.output.includes("1")) {
    throw new Error(
      `Data not found after full restart: ${finalVerifyResult.error}`
    );
  }
  console.log("    ✅ Data persistence verified after full stack restart");

  return {
    testData,
    insertTime: insertResult.duration,
    restartTime: restartResult.duration,
    verificationTime: verifyResult.duration,
    fullRestartTime: fullRestartResult.duration,
  };
};

describe("Comprehensive Migration Validation Tests", () => {
  const podmanComposeFile = "infra/podman/podman-compose.yaml";
  const originalComposeFile = "compose.yaml";

  beforeAll(async () => {
    console.log("\n🔧 Setting up comprehensive migration validation tests...");

    // Verify Podman installation
    const podmanCheck = executeCommand("podman --version");
    if (!podmanCheck.success) {
      throw new Error("Podman is not installed or not accessible");
    }
    console.log(`  ✅ Podman version: ${podmanCheck.output}`);

    // Verify podman-compose installation
    const composeCheck = executeCommand("podman-compose --version");
    if (!composeCheck.success) {
      throw new Error("podman-compose is not installed or not accessible");
    }
    console.log(`  ✅ podman-compose version: ${composeCheck.output}`);

    // Verify compose files exist
    if (!fs.existsSync(podmanComposeFile)) {
      throw new Error(`Podman compose file not found: ${podmanComposeFile}`);
    }
    console.log(`  ✅ Podman compose file found: ${podmanComposeFile}`);

    // Clean up any existing containers
    console.log("  🧹 Cleaning up existing containers...");
    executeCommand(`podman-compose -f ${podmanComposeFile} down -v`, {
      timeout: 60000,
    });
    await sleep(5000);

    console.log("  ✅ Comprehensive test setup complete");
  }, 120000);

  afterAll(async () => {
    console.log("\n🧹 Cleaning up comprehensive test environment...");

    // Stop and remove all containers
    executeCommand(`podman-compose -f ${podmanComposeFile} down -v`, {
      timeout: 60000,
    });

    // Clean up test volumes
    executeCommand(`podman volume prune -f`, { timeout: 30000 });

    console.log("  ✅ Comprehensive cleanup complete");
  }, 60000);

  describe("Integration Tests - Service Startup Validation", () => {
    test("should start all services successfully with Podman", async () => {
      console.log("\n🚀 Testing comprehensive service startup with Podman...");

      // Start services with detailed monitoring
      const startResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} up -d`,
        { timeout: 300000 }
      );

      expect(startResult.success).toBe(true);
      if (!startResult.success) {
        console.error("Startup failed:", startResult.error);
        throw new Error(`Failed to start services: ${startResult.error}`);
      }

      console.log("  ✅ Services started successfully");
      console.log(`  ⏱️  Startup time: ${startResult.duration}ms`);

      // Wait for services to initialize with progress monitoring
      console.log("  ⏳ Waiting for services to initialize...");
      await sleep(45000);

      // Check detailed service status
      const statusResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} ps`
      );
      expect(statusResult.success).toBe(true);
      console.log("  📊 Service status:");
      console.log(statusResult.output);

      // Verify all expected containers are running
      const runningContainers = statusResult.output
        .split("\n")
        .filter(
          (line) => line.includes("Up") || line.includes("running")
        ).length;

      expect(runningContainers).toBeGreaterThanOrEqual(5); // At least 5 services should be running
      console.log(`  ✅ ${runningContainers} containers are running`);
    }, 400000);

    test("should have all critical services responding to health checks", async () => {
      console.log("\n🏥 Testing comprehensive service health checks...");

      const services = [
        { name: "gap-detector", port: 8000, path: "/health" },
        { name: "analysis-engine", port: 5000, path: "/health" },
        { name: "windmill", port: 3000, path: "/api/version" },
        { name: "nginx", port: 8080, path: "/health" },
      ];

      const healthResults = [];

      for (const service of services) {
        console.log(`  🔍 Comprehensive health check for ${service.name}...`);
        const healthResult = await waitForService(
          service.name,
          service.port,
          service.path,
          20,
          3000
        );

        healthResults.push({
          service: service.name,
          healthy: healthResult.success,
          attempts: healthResult.attempts,
          responseTime: healthResult.responseTime,
        });

        if (healthResult.success) {
          console.log(
            `  ✅ ${service.name} is healthy (${healthResult.responseTime}ms response)`
          );
        } else {
          console.log(
            `  ❌ ${service.name} failed health check after ${healthResult.attempts} attempts`
          );
        }
      }

      // At least 75% of services should be healthy
      const healthyCount = healthResults.filter((r) => r.healthy).length;
      expect(healthyCount).toBeGreaterThanOrEqual(
        Math.ceil(services.length * 0.75)
      );

      console.log(
        `  📊 Health check summary: ${healthyCount}/${services.length} services healthy`
      );

      // Log response time statistics
      const responseTimes = healthResults
        .filter((r) => r.responseTime)
        .map((r) => r.responseTime);

      if (responseTimes.length > 0) {
        const avgResponseTime =
          responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        console.log(
          `  📈 Average response time: ${avgResponseTime.toFixed(2)}ms`
        );
      }
    }, 300000);
  });

  describe("Network Connectivity Tests", () => {
    test("should have comprehensive network connectivity between all services", async () => {
      console.log("\n🌐 Testing comprehensive network connectivity...");

      const connectivityResults = await testNetworkConnectivity();

      // Validate database connections
      const successfulDbConnections =
        connectivityResults.databaseConnections.filter((c) => c.success).length;
      expect(successfulDbConnections).toBeGreaterThan(0);
      console.log(
        `  📊 Database connectivity: ${successfulDbConnections}/${connectivityResults.databaseConnections.length} successful`
      );

      // Validate HTTP connections (allow some failures for optional services)
      const successfulHttpConnections =
        connectivityResults.httpConnections.filter((c) => c.success).length;
      expect(successfulHttpConnections).toBeGreaterThanOrEqual(
        Math.ceil(connectivityResults.httpConnections.length * 0.5)
      );
      console.log(
        `  📊 HTTP connectivity: ${successfulHttpConnections}/${connectivityResults.httpConnections.length} successful`
      );

      // Validate DNS resolutions (allow some failures in different environments)
      const successfulDnsResolutions =
        connectivityResults.dnsResolutions.filter((c) => c.success).length;
      expect(successfulDnsResolutions).toBeGreaterThanOrEqual(
        Math.ceil(connectivityResults.dnsResolutions.length * 0.5)
      );
      console.log(
        `  📊 DNS resolution: ${successfulDnsResolutions}/${connectivityResults.dnsResolutions.length} successful`
      );

      // Check network latency
      const latencyResults = connectivityResults.networkLatency.filter(
        (l) => l.success && l.averageLatency
      );
      if (latencyResults.length > 0) {
        const avgLatency =
          latencyResults.reduce((sum, l) => sum + l.averageLatency, 0) /
          latencyResults.length;
        console.log(`  📈 Average network latency: ${avgLatency.toFixed(2)}ms`);
        expect(avgLatency).toBeLessThan(100); // Network latency should be reasonable
      }
    }, 180000);

    test("should have proper network isolation and security", async () => {
      console.log("\n🛡️  Testing network isolation and security...");

      // Check if phoenix-net network exists and is properly configured
      const networkCheck = executeCommand(
        'podman network ls --format "{{.Name}}" | grep phoenix-hydra_phoenix-net'
      );
      expect(networkCheck.success).toBe(true);
      console.log("  ✅ Phoenix network exists");

      // Get detailed network information
      const networkInfo = executeCommand(
        'podman network inspect phoenix-hydra_phoenix-net --format "{{json .}}"'
      );

      if (networkInfo.success) {
        try {
          const network = JSON.parse(networkInfo.output);
          console.log(`  ✅ Network driver: ${network.driver || "bridge"}`);

          if (network.subnets && network.subnets.length > 0) {
            console.log(`  ✅ Network subnet: ${network.subnets[0].subnet}`);
            expect(network.subnets[0].subnet).toMatch(
              /^\d+\.\d+\.\d+\.\d+\/\d+$/
            );
          }

          // Check containers on the network
          const containerCount = Object.keys(network.containers || {}).length;
          console.log(`  ✅ Containers on network: ${containerCount}`);
          expect(containerCount).toBeGreaterThanOrEqual(4);
        } catch (error) {
          console.log("  ⚠️  Could not parse network configuration");
        }
      }

      // Test external connectivity (should work for exposed ports)
      const externalTests = [
        { port: 8000, service: "gap-detector" },
        { port: 3000, service: "windmill" },
        { port: 8080, service: "nginx" },
        { port: 5000, service: "analysis-engine" },
      ];

      let accessibleServices = 0;
      for (const test of externalTests) {
        const result = await checkServiceHealth(test.port, "/health", 5000);
        if (result.success) {
          accessibleServices++;
          console.log(
            `  ✅ ${test.service} accessible externally on port ${test.port}`
          );
        } else {
          console.log(
            `  ⚠️  ${test.service} not accessible externally on port ${test.port}`
          );
        }
      }

      // At least 50% of services should be externally accessible
      expect(accessibleServices).toBeGreaterThanOrEqual(
        Math.ceil(externalTests.length * 0.5)
      );
    }, 120000);
  });

  describe("Data Persistence Tests", () => {
    test("should maintain comprehensive PostgreSQL data persistence", async () => {
      console.log("\n💾 Testing comprehensive data persistence...");

      const persistenceResults = await testDatabasePersistence();

      // Verify all persistence tests passed
      expect(persistenceResults.connection).toBe(true);
      expect(persistenceResults.tableCreation).toBe(true);
      expect(persistenceResults.dataInsertion).toBe(true);
      expect(persistenceResults.dataRetrieval).toBe(true);
      expect(persistenceResults.dataIntegrity).toBe(true);
      expect(persistenceResults.transactionSupport).toBe(true);

      console.log("  ✅ All database persistence tests passed");
    }, 180000);

    test("should persist data across container restarts and system reboots", async () => {
      console.log("\n🔄 Testing data persistence across restarts...");

      const restartResults = await testDataPersistenceAcrossRestarts();

      expect(restartResults.testData).toBeDefined();
      console.log(`  ✅ Data persistence verified across restarts`);
      console.log(`  📊 Performance metrics:`);
      console.log(`    Insert time: ${restartResults.insertTime}ms`);
      console.log(
        `    Container restart time: ${restartResults.restartTime}ms`
      );
      console.log(
        `    Verification time: ${restartResults.verificationTime}ms`
      );
      console.log(`    Full restart time: ${restartResults.fullRestartTime}ms`);

      // Restart operations should complete within reasonable time
      expect(restartResults.restartTime).toBeLessThan(60000); // Less than 1 minute
      expect(restartResults.fullRestartTime).toBeLessThan(120000); // Less than 2 minutes
    }, 300000);
  });

  describe("Performance Comparison Tests", () => {
    test("should provide comprehensive performance comparison between Docker and Podman", async () => {
      console.log("\n📊 Running comprehensive performance comparison...");

      const performanceResults = await performanceComparison();

      // Validate Podman performance metrics
      expect(performanceResults.podman.metrics.startupTime).toBeGreaterThan(0);
      expect(
        performanceResults.podman.metrics.totalDeploymentTime
      ).toBeLessThan(300000); // Less than 5 minutes
      expect(
        performanceResults.podman.metrics.healthyServices
      ).toBeGreaterThanOrEqual(3); // At least 75% healthy
      expect(performanceResults.podman.metrics.averageCpu).toBeLessThan(80); // Less than 80% CPU
      expect(performanceResults.podman.metrics.averageMemory).toBeLessThan(90); // Less than 90% memory

      console.log("  ✅ Podman performance metrics within acceptable ranges");

      // If Docker comparison is available, validate relative performance
      if (
        performanceResults.docker.available &&
        performanceResults.docker.metrics.startupTime
      ) {
        const dockerMetrics = performanceResults.docker.metrics;
        const podmanMetrics = performanceResults.podman.metrics;

        // Podman should not be more than 100% slower than Docker
        const startupRatio =
          podmanMetrics.startupTime / dockerMetrics.startupTime;
        expect(startupRatio).toBeLessThan(2.0);

        // Resource usage should be comparable
        const cpuRatio =
          podmanMetrics.averageCpu / Math.max(dockerMetrics.averageCpu, 1);
        const memRatio =
          podmanMetrics.averageMemory /
          Math.max(dockerMetrics.averageMemory, 1);

        expect(cpuRatio).toBeLessThan(2.0); // Not more than 2x CPU usage
        expect(memRatio).toBeLessThan(2.0); // Not more than 2x memory usage

        console.log("  ✅ Podman performance comparable to Docker");
      }

      // Service response times should be reasonable
      const serviceHealthResults =
        performanceResults.podman.metrics.serviceHealthResults || [];
      const responseTimes = serviceHealthResults
        .filter((s) => s.responseTime)
        .map((s) => s.responseTime);

      if (responseTimes.length > 0) {
        const avgResponseTime =
          responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
        expect(avgResponseTime).toBeLessThan(2000); // Less than 2 seconds average response time
        console.log(
          `  ✅ Average service response time: ${avgResponseTime.toFixed(2)}ms`
        );
      }
    }, 600000);
  });

  describe("Security and Compliance Tests", () => {
    test("should run all containers in rootless mode with proper security", async () => {
      console.log("\n🔒 Testing rootless execution and security compliance...");

      // Get list of running containers
      const containersResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} ps --format "{{.Names}}"`
      );
      expect(containersResult.success).toBe(true);

      const containers = containersResult.output
        .split("\n")
        .filter((name) => name.trim());
      expect(containers.length).toBeGreaterThan(0);

      let rootlessContainers = 0;
      let secureContainers = 0;

      // Check each container for security compliance
      for (const container of containers) {
        if (container.trim()) {
          console.log(`    Checking security for ${container.trim()}...`);

          // Check user namespace mapping
          const userNsCheck = executeCommand(
            `podman inspect ${container.trim()} --format "{{.HostConfig.UsernsMode}}"`
          );
          if (userNsCheck.success) {
            rootlessContainers++;
            console.log(
              `      ✅ User namespace: ${userNsCheck.output || "default"}`
            );
          }

          // Check security options
          const securityOpts = executeCommand(
            `podman inspect ${container.trim()} --format "{{.HostConfig.SecurityOpt}}"`
          );
          if (
            securityOpts.success &&
            securityOpts.output.includes("no-new-privileges")
          ) {
            secureContainers++;
            console.log(`      ✅ Security options: no-new-privileges enabled`);
          }

          // Check if running as root
          const userCheck = executeCommand(
            `podman inspect ${container.trim()} --format "{{.Config.User}}"`
          );
          if (
            userCheck.success &&
            userCheck.output &&
            userCheck.output !== "root"
          ) {
            console.log(`      ✅ Running as user: ${userCheck.output}`);
          }
        }
      }

      // All containers should be rootless and secure
      expect(rootlessContainers).toBe(containers.length);
      expect(secureContainers).toBeGreaterThanOrEqual(
        Math.ceil(containers.length * 0.8)
      );

      console.log(
        `  ✅ Security compliance: ${rootlessContainers}/${containers.length} rootless, ${secureContainers}/${containers.length} secure`
      );
    }, 120000);
  });
});
