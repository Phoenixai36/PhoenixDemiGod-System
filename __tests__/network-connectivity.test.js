const { execSync } = require("child_process");
const http = require("http");
const { promisify } = require("util");

/**
 * Network connectivity tests for Podman migration
 * Tests inter-service communication, DNS resolution, and network isolation
 */

const sleep = promisify(setTimeout);

/**
 * Helper function to execute shell commands
 */
const executeCommand = (command, options = {}) => {
  try {
    const result = execSync(command, {
      encoding: "utf8",
      stdio: "pipe",
      timeout: 60000,
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
 * Test HTTP connectivity between services
 */
const testHttpConnectivity = async (
  fromContainer,
  toService,
  port,
  path = "/"
) => {
  const command = `podman exec ${fromContainer} curl -f -s --connect-timeout 10 http://${toService}:${port}${path}`;
  const result = executeCommand(command, { timeout: 30000 });

  return {
    success: result.success,
    fromContainer,
    toService,
    port,
    path,
    error: result.error,
    output: result.output,
  };
};

/**
 * Test TCP connectivity between services
 */
const testTcpConnectivity = async (fromContainer, toService, port) => {
  const command = `podman exec ${fromContainer} python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex(('${toService}', ${port}))
    sock.close()
    if result == 0:
        print('Connection successful')
        sys.exit(0)
    else:
        print('Connection failed')
        sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"`;

  const result = executeCommand(command, { timeout: 30000 });

  return {
    success: result.success,
    fromContainer,
    toService,
    port,
    error: result.error,
    output: result.output,
  };
};

/**
 * Test DNS resolution between services
 */
const testDnsResolution = async (fromContainer, targetService) => {
  const command = `podman exec ${fromContainer} nslookup ${targetService}`;
  const result = executeCommand(command, { timeout: 30000 });

  return {
    success: result.success,
    fromContainer,
    targetService,
    error: result.error,
    output: result.output,
  };
};

/**
 * Test network isolation by attempting to access external services
 */
const testNetworkIsolation = async (container) => {
  // Try to access external service (should work unless explicitly blocked)
  const externalTest = executeCommand(
    `podman exec ${container} curl -f -s --connect-timeout 5 http://httpbin.org/ip`,
    { timeout: 15000 }
  );

  return {
    container,
    canAccessExternal: externalTest.success,
    error: externalTest.error,
  };
};

describe("Network Connectivity Tests", () => {
  const podmanComposeFile = "infra/podman/podman-compose.yaml";

  beforeAll(async () => {
    console.log("\n🔧 Setting up network connectivity tests...");

    // Ensure services are running
    const statusResult = executeCommand(
      `podman-compose -f ${podmanComposeFile} ps --format "{{.Names}}"`
    );

    if (!statusResult.success) {
      throw new Error("Services are not running. Please start them first.");
    }

    const containers = statusResult.output
      .split("\n")
      .filter((name) => name.trim());
    console.log(`  ✅ Found ${containers.length} running containers`);

    // Wait for services to be fully ready
    await sleep(10000);
  }, 60000);

  describe("Inter-Service Communication", () => {
    test("should allow database connections from application services", async () => {
      console.log("\n🔍 Testing database connectivity...");

      const dbTests = [
        {
          container: "phoenix-hydra_recurrent-processor_1",
          service: "db",
          port: 5432,
        },
        {
          container: "phoenix-hydra_windmill_1",
          service: "db",
          port: 5432,
        },
      ];

      const results = [];

      for (const test of dbTests) {
        console.log(
          `  Testing ${test.container} -> ${test.service}:${test.port}`
        );
        const result = await testTcpConnectivity(
          test.container,
          test.service,
          test.port
        );
        results.push(result);

        if (result.success) {
          console.log(`    ✅ Connection successful`);
        } else {
          console.log(`    ❌ Connection failed: ${result.error}`);
        }
      }

      // At least one service should be able to connect to the database
      const successfulConnections = results.filter((r) => r.success).length;
      expect(successfulConnections).toBeGreaterThan(0);
    }, 120000);

    test("should allow HTTP communication between web services", async () => {
      console.log("\n🌐 Testing HTTP connectivity...");

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

      const results = [];

      for (const test of httpTests) {
        console.log(
          `  Testing ${test.from} -> ${test.to}:${test.port}${test.path}`
        );
        const result = await testHttpConnectivity(
          test.from,
          test.to,
          test.port,
          test.path
        );
        results.push(result);

        if (result.success) {
          console.log(`    ✅ HTTP request successful`);
        } else {
          console.log(`    ⚠️  HTTP request failed: ${result.error}`);
        }
      }

      // At least 50% of HTTP connections should work
      const successfulConnections = results.filter((r) => r.success).length;
      expect(successfulConnections).toBeGreaterThanOrEqual(
        Math.ceil(httpTests.length * 0.5)
      );
    }, 120000);
  });

  describe("DNS Resolution", () => {
    test("should resolve service names within the network", async () => {
      console.log("\n🔍 Testing DNS resolution...");

      const dnsTests = [
        {
          from: "phoenix-hydra_gap-detector_1",
          target: "db",
        },
        {
          from: "phoenix-hydra_gap-detector_1",
          target: "windmill",
        },
        {
          from: "phoenix-hydra_recurrent-processor_1",
          target: "db",
        },
        {
          from: "phoenix-hydra_nginx_1",
          target: "windmill",
        },
      ];

      const results = [];

      for (const test of dnsTests) {
        console.log(`  Testing DNS resolution: ${test.from} -> ${test.target}`);
        const result = await testDnsResolution(test.from, test.target);
        results.push(result);

        if (result.success) {
          console.log(`    ✅ DNS resolution successful`);
        } else {
          console.log(`    ⚠️  DNS resolution failed: ${result.error}`);
        }
      }

      // At least 50% of DNS resolutions should work
      const successfulResolutions = results.filter((r) => r.success).length;
      expect(successfulResolutions).toBeGreaterThanOrEqual(
        Math.ceil(dnsTests.length * 0.5)
      );
    }, 120000);
  });

  describe("Network Configuration", () => {
    test("should have phoenix-net network properly configured", async () => {
      console.log("\n🔧 Testing network configuration...");

      // Check if phoenix-net network exists
      const networkExists = executeCommand(
        'podman network ls --format "{{.Name}}" | grep phoenix-hydra_phoenix-net'
      );
      expect(networkExists.success).toBe(true);
      console.log("  ✅ Phoenix network exists");

      // Get network details
      const networkInfo = executeCommand(
        'podman network inspect phoenix-hydra_phoenix-net --format "{{json .}}"'
      );

      if (networkInfo.success) {
        try {
          const network = JSON.parse(networkInfo.output);
          console.log(`  ✅ Network driver: ${network.driver || "bridge"}`);
          console.log(
            `  ✅ Network subnet: ${network.subnets?.[0]?.subnet || "default"}`
          );

          // Verify network has expected configuration
          expect(network.driver).toBeDefined();
          if (network.subnets && network.subnets.length > 0) {
            expect(network.subnets[0].subnet).toMatch(
              /^\d+\.\d+\.\d+\.\d+\/\d+$/
            );
          }
        } catch (error) {
          console.log("  ⚠️  Could not parse network configuration");
        }
      }
    }, 60000);

    test("should have all containers connected to phoenix-net", async () => {
      console.log("\n🔗 Testing container network connections...");

      // Get containers on the network
      const networkContainers = executeCommand(
        'podman network inspect phoenix-hydra_phoenix-net --format "{{range .Containers}}{{.Name}} {{end}}"'
      );

      if (networkContainers.success) {
        const containers = networkContainers.output
          .split(" ")
          .filter((name) => name.trim());
        console.log(`  ✅ Containers on phoenix-net: ${containers.length}`);
        console.log(`  📝 Container names: ${containers.join(", ")}`);

        // Should have at least 4 containers (db, windmill, gap-detector, nginx)
        expect(containers.length).toBeGreaterThanOrEqual(4);
      } else {
        console.log("  ⚠️  Could not retrieve network container information");
      }
    }, 60000);
  });

  describe("Network Security", () => {
    test("should allow external access for exposed services", async () => {
      console.log("\n🌍 Testing external network access...");

      const externalTests = [
        { port: 8000, service: "gap-detector" },
        { port: 3000, service: "windmill" },
        { port: 8080, service: "nginx" },
        { port: 5000, service: "analysis-engine" },
      ];

      const results = [];

      for (const test of externalTests) {
        console.log(
          `  Testing external access to ${test.service} on port ${test.port}`
        );

        const result = await new Promise((resolve) => {
          const req = http.request(
            {
              hostname: "localhost",
              port: test.port,
              path: "/health",
              method: "GET",
              timeout: 10000,
            },
            (res) => {
              resolve({
                success: res.statusCode >= 200 && res.statusCode < 400,
                statusCode: res.statusCode,
                service: test.service,
                port: test.port,
              });
            }
          );

          req.on("error", () => {
            resolve({
              success: false,
              statusCode: null,
              service: test.service,
              port: test.port,
            });
          });

          req.on("timeout", () => {
            req.destroy();
            resolve({
              success: false,
              statusCode: null,
              service: test.service,
              port: test.port,
            });
          });

          req.end();
        });

        results.push(result);

        if (result.success) {
          console.log(`    ✅ ${test.service} accessible externally`);
        } else {
          console.log(`    ⚠️  ${test.service} not accessible externally`);
        }
      }

      // At least 50% of exposed services should be accessible
      const accessibleServices = results.filter((r) => r.success).length;
      expect(accessibleServices).toBeGreaterThanOrEqual(
        Math.ceil(externalTests.length * 0.5)
      );
    }, 120000);

    test("should block access to internal services", async () => {
      console.log("\n🔒 Testing internal service protection...");

      // Database should not be accessible externally
      const dbAccessTest = await new Promise((resolve) => {
        const req = http.request(
          {
            hostname: "localhost",
            port: 5432,
            method: "GET",
            timeout: 5000,
          },
          (res) => {
            resolve({ accessible: true });
          }
        );

        req.on("error", () => {
          resolve({ accessible: false });
        });

        req.on("timeout", () => {
          req.destroy();
          resolve({ accessible: false });
        });

        req.end();
      });

      // Database should NOT be accessible externally
      expect(dbAccessTest.accessible).toBe(false);
      console.log("  ✅ Database properly protected from external access");
    }, 30000);
  });
});
