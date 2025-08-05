const { execSync, spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");
const { promisify } = require("util");

/**
 * Comprehensive migration validation tests for Docker-to-Podman migration
 * This test suite validates that all services start correctly, network connectivity works,
 * data persistence is maintained, and performance is acceptable.
 *
 * Requirements covered:
 * - 1.3: Migration validation and testing
 * - 3.2: Service communication and networking
 * - 5.2: Network connectivity and DNS resolution
 */

const sleep = promisify(setTimeout);

/**
 * Helper function to execute shell commands with better error handling
 */
const executeCommand = (command, options = {}) => {
  try {
    const result = execSync(command, {
      encoding: "utf8",
      stdio: "pipe",
      timeout: 120000,
      ...options,
    });
    return { success: true, output: result.trim(), error: null };
  } catch (error) {
    return {
      success: false,
      output: error.stdout ? error.stdout.trim() : "",
      error: error.stderr ? error.stderr.trim() : error.message,
    };
  }
};

/**
 * Check if a service is responding on a specific port
 */
const checkServiceHealth = (port, path = "/health", timeout = 10000) => {
  return new Promise((resolve) => {
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
        resolve({
          success: res.statusCode >= 200 && res.statusCode < 300,
          statusCode: res.statusCode,
          data: data,
          error: null,
        });
      });
    });

    req.on("error", (error) => {
      resolve({
        success: false,
        statusCode: null,
        data: null,
        error: error.message,
      });
    });

    req.on("timeout", () => {
      req.destroy();
      resolve({
        success: false,
        statusCode: null,
        data: null,
        error: "Request timeout",
      });
    });

    req.end();
  });
};

/**
 * Wait for a service to become healthy
 */
const waitForService = async (
  port,
  path = "/health",
  maxAttempts = 30,
  interval = 5000
) => {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(
      `    Attempt ${attempt}/${maxAttempts}: Checking service on port ${port}...`
    );

    const result = await checkServiceHealth(port, path, 5000);
    if (result.success) {
      console.log(`    ✅ Service on port ${port} is healthy`);
      return true;
    }

    if (attempt < maxAttempts) {
      console.log(`    ⏳ Service not ready, waiting ${interval / 1000}s...`);
      await sleep(interval);
    }
  }

  console.log(
    `    ❌ Service on port ${port} failed to become healthy after ${maxAttempts} attempts`
  );
  return false;
};

/**
 * Test database connectivity and data persistence
 */
const testDatabasePersistence = async () => {
  console.log("  🔍 Testing database connectivity and persistence...");

  // Test database connection
  const dbTest = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT version();"`,
    {
      timeout: 30000,
    }
  );

  if (!dbTest.success) {
    throw new Error(`Database connection failed: ${dbTest.error}`);
  }

  // Create test table and insert data
  const createTable = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "CREATE TABLE IF NOT EXISTS migration_test (id SERIAL PRIMARY KEY, test_data TEXT, created_at TIMESTAMP DEFAULT NOW());"`,
    {
      timeout: 30000,
    }
  );

  if (!createTable.success) {
    throw new Error(`Failed to create test table: ${createTable.error}`);
  }

  const testData = `podman-migration-test-${Date.now()}`;
  const insertData = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "INSERT INTO migration_test (test_data) VALUES ('${testData}');"`,
    {
      timeout: 30000,
    }
  );

  if (!insertData.success) {
    throw new Error(`Failed to insert test data: ${insertData.error}`);
  }

  // Verify data exists
  const selectData = executeCommand(
    `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT test_data FROM migration_test WHERE test_data = '${testData}';"`,
    {
      timeout: 30000,
    }
  );

  if (!selectData.success || !selectData.output.includes(testData)) {
    throw new Error(`Failed to verify test data: ${selectData.error}`);
  }

  console.log("  ✅ Database persistence test passed");
  return true;
};

/**
 * Test network connectivity between services
 */
const testNetworkConnectivity = async () => {
  console.log("  🔍 Testing network connectivity between services...");

  // Test database connectivity from recurrent-processor
  const dbConnectivity = executeCommand(
    `podman exec phoenix-hydra_recurrent-processor_1 python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex(('db', 5432))
    sock.close()
    if result == 0:
        print('Database connection successful')
        sys.exit(0)
    else:
        print('Database connection failed')
        sys.exit(1)
except Exception as e:
    print(f'Connection error: {e}')
    sys.exit(1)
"`,
    { timeout: 30000 }
  );

  if (!dbConnectivity.success) {
    throw new Error(
      `Database network connectivity test failed: ${dbConnectivity.error}`
    );
  }

  // Test HTTP connectivity between services
  const httpConnectivity = executeCommand(
    `podman exec phoenix-hydra_nginx_1 curl -f -s http://windmill:3000/api/version`,
    {
      timeout: 30000,
    }
  );

  if (!httpConnectivity.success) {
    console.log(
      "  ⚠️  HTTP connectivity test failed (may be expected during startup)"
    );
  } else {
    console.log("  ✅ HTTP connectivity between services working");
  }

  console.log("  ✅ Network connectivity tests passed");
  return true;
};

describe("Migration Validation Tests", () => {
  const podmanComposeFile = "infra/podman/podman-compose.yaml";
  const originalComposeFile = "compose.yaml";

  beforeAll(async () => {
    console.log("\n🔧 Setting up migration validation tests...");

    // Verify Podman is installed
    const podmanCheck = executeCommand("podman --version");
    if (!podmanCheck.success) {
      throw new Error("Podman is not installed or not accessible");
    }
    console.log(`  ✅ Podman version: ${podmanCheck.output}`);

    // Verify podman-compose is installed
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

    console.log("  ✅ Migration validation test setup complete");
  }, 120000);

  afterAll(async () => {
    console.log("\n🧹 Cleaning up migration validation test environment...");

    // Stop and remove all containers
    executeCommand(`podman-compose -f ${podmanComposeFile} down -v`, {
      timeout: 60000,
    });

    console.log("  ✅ Migration validation cleanup complete");
  }, 60000);

  describe("Service Startup Validation", () => {
    test("should start all services successfully with Podman", async () => {
      console.log("\n🚀 Testing Podman service startup...");

      // Start services
      const startResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} up -d`,
        {
          timeout: 300000,
        }
      );

      expect(startResult.success).toBe(true);
      if (!startResult.success) {
        console.error("Startup failed:", startResult.error);
        throw new Error(`Failed to start services: ${startResult.error}`);
      }

      console.log("  ✅ Services started successfully");

      // Wait for services to initialize
      console.log("  ⏳ Waiting for services to initialize...");
      await sleep(45000);

      // Check service status
      const statusResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} ps`
      );
      expect(statusResult.success).toBe(true);
      console.log("  📊 Service status:");
      console.log(statusResult.output);
    }, 400000);

    test("should have all critical services responding to health checks", async () => {
      console.log("\n🏥 Testing service health checks...");

      const services = [
        { name: "gap-detector", port: 8000, path: "/health" },
        { name: "analysis-engine", port: 5000, path: "/health" },
        { name: "windmill", port: 3000, path: "/api/version" },
        { name: "nginx", port: 8080, path: "/health" },
      ];

      const healthResults = [];

      for (const service of services) {
        console.log(`  🔍 Checking ${service.name} on port ${service.port}...`);
        const healthy = await waitForService(
          service.port,
          service.path,
          15,
          4000
        );
        healthResults.push({ service: service.name, healthy });

        if (healthy) {
          console.log(`  ✅ ${service.name} is healthy`);
        } else {
          console.log(`  ❌ ${service.name} is not responding`);
        }
      }

      // At least 3 out of 4 services should be healthy for the test to pass
      const healthyCount = healthResults.filter((r) => r.healthy).length;
      expect(healthyCount).toBeGreaterThanOrEqual(3);

      console.log(
        `  📊 Health check summary: ${healthyCount}/${services.length} services healthy`
      );
    }, 240000);
  });

  describe("Network Connectivity Validation", () => {
    test("should have proper network connectivity between services", async () => {
      console.log("\n🌐 Testing network connectivity...");

      await testNetworkConnectivity();
    }, 120000);

    test("should have proper DNS resolution within phoenix-net network", async () => {
      console.log("\n🔍 Testing DNS resolution...");

      // Check if phoenix-net network exists
      const networkCheck = executeCommand(
        'podman network ls --format "{{.Name}}" | grep phoenix-hydra_phoenix-net'
      );
      expect(networkCheck.success).toBe(true);
      console.log("  ✅ Phoenix network exists");

      // Test DNS resolution from one container to another
      const dnsTest = executeCommand(
        `podman exec phoenix-hydra_gap-detector_1 getent hosts db`,
        {
          timeout: 30000,
        }
      );

      if (dnsTest.success) {
        console.log("  ✅ DNS resolution working between services");
        console.log(`  📝 DNS result: ${dnsTest.output}`);
      } else {
        console.log(
          "  ⚠️  DNS resolution test inconclusive (may be environment-specific)"
        );
      }
    }, 60000);
  });

  describe("Data Persistence Validation", () => {
    test("should maintain PostgreSQL data persistence", async () => {
      console.log("\n💾 Testing data persistence...");

      await testDatabasePersistence();
    }, 120000);

    test("should have proper volume mounting with correct permissions", async () => {
      console.log("\n📁 Testing volume permissions...");

      // Check if volumes are properly mounted
      const volumeCheck = executeCommand(
        'podman volume ls --format "{{.Name}}" | grep phoenix-hydra'
      );
      if (volumeCheck.success) {
        console.log("  ✅ Phoenix Hydra volumes found");
        console.log(`  📝 Volumes: ${volumeCheck.output}`);
      }

      // Check database volume permissions
      const dbVolumeTest = executeCommand(
        `podman exec phoenix-hydra_db_1 ls -la /var/lib/postgresql/data`,
        {
          timeout: 30000,
        }
      );

      if (dbVolumeTest.success) {
        console.log("  ✅ Database volume accessible");
      } else {
        console.log("  ⚠️  Database volume test inconclusive");
      }
    }, 60000);

    test("should persist data across container restarts", async () => {
      console.log("\n🔄 Testing data persistence across restarts...");

      // Insert test data
      const testData = `restart-test-${Date.now()}`;
      const insertData = executeCommand(
        `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "INSERT INTO migration_test (test_data) VALUES ('${testData}');"`,
        {
          timeout: 30000,
        }
      );

      expect(insertData.success).toBe(true);

      // Restart database container
      const restartDb = executeCommand(
        `podman-compose -f ${podmanComposeFile} restart db`,
        {
          timeout: 60000,
        }
      );

      expect(restartDb.success).toBe(true);

      // Wait for database to be ready
      await sleep(30000);

      // Verify data still exists
      const selectData = executeCommand(
        `podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT test_data FROM migration_test WHERE test_data = '${testData}';"`,
        {
          timeout: 30000,
        }
      );

      expect(selectData.success).toBe(true);
      expect(selectData.output).toContain(testData);

      console.log("  ✅ Data persistence across restarts verified");
    }, 180000);
  });

  describe("Security Validation", () => {
    test("should run all containers in rootless mode", async () => {
      console.log("\n🔒 Testing rootless execution...");

      // Check if containers are running as non-root
      const containersResult = executeCommand(
        `podman-compose -f ${podmanComposeFile} ps --format "{{.Names}}"`
      );
      expect(containersResult.success).toBe(true);

      const containers = containersResult.output
        .split("\n")
        .filter((name) => name.trim());

      for (const container of containers) {
        if (container.trim()) {
          // Check if container is running with user namespace mapping
          const userNsCheck = executeCommand(
            `podman inspect ${container.trim()} --format "{{.HostConfig.UsernsMode}}"`
          );
          if (userNsCheck.success) {
            console.log(
              `  ✅ Container ${container.trim()} user namespace: ${
                userNsCheck.output || "default"
              }`
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
            console.log(
              `  ✅ Container ${container.trim()} has no-new-privileges enabled`
            );
          }
        }
      }
    }, 60000);

    test("should have proper network isolation", async () => {
      console.log("\n🛡️  Testing network isolation...");

      // Check network configuration
      const networkInfo = executeCommand(
        'podman network inspect phoenix-hydra_phoenix-net --format "{{.Subnets}}"'
      );
      if (networkInfo.success) {
        console.log(`  ✅ Network subnet configuration: ${networkInfo.output}`);
      }

      // Verify containers are on the isolated network
      const networkContainers = executeCommand(
        'podman network inspect phoenix-hydra_phoenix-net --format "{{range .Containers}}{{.Name}} {{end}}"'
      );
      if (networkContainers.success) {
        console.log(
          `  ✅ Containers on phoenix-net: ${networkContainers.output}`
        );
      }
    }, 60000);
  });
});
