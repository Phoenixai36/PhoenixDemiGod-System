const { execSync } = require("child_process");
const fs = require("fs");
const { promisify } = require("util");

/**
 * Performance comparison tests between Docker and Podman setups
 * This test suite compares startup times, resource usage, and response times
 */

const sleep = promisify(setTimeout);

/**
 * Helper function to execute commands with timing
 */
const executeWithTiming = (command, options = {}) => {
  const startTime = Date.now();
  try {
    const result = execSync(command, {
      encoding: "utf8",
      stdio: "pipe",
      timeout: 180000,
      ...options,
    });
    const endTime = Date.now();
    return {
      success: true,
      output: result.trim(),
      error: null,
      duration: endTime - startTime,
    };
  } catch (error) {
    const endTime = Date.now();
    return {
      success: false,
      output: error.stdout ? error.stdout.trim() : "",
      error: error.stderr ? error.stderr.trim() : error.message,
      duration: endTime - startTime,
    };
  }
};

/**
 * Measure service startup time
 */
const measureStartupTime = async (composeCommand, composeFile) => {
  console.log(`  🚀 Testing startup time for ${composeCommand}...`);

  // Stop any existing services
  try {
    execSync(`${composeCommand} -f ${composeFile} down -v`, {
      stdio: "pipe",
      timeout: 60000,
    });
  } catch (error) {
    // Ignore errors when stopping non-existent services
  }

  await sleep(5000); // Wait for cleanup

  // Measure startup time
  const startTime = Date.now();
  const result = executeWithTiming(`${composeCommand} -f ${composeFile} up -d`);

  if (!result.success) {
    throw new Error(
      `Failed to start services with ${composeCommand}: ${result.error}`
    );
  }

  // Wait for services to be ready
  await sleep(30000);

  // Check if services are responding
  const services = [
    { port: 8000, name: "gap-detector" },
    { port: 5000, name: "analysis-engine" },
    { port: 3000, name: "windmill" },
    { port: 8080, name: "nginx" },
  ];

  let healthyServices = 0;
  const serviceCheckStart = Date.now();

  for (const service of services) {
    try {
      const healthCheck = executeWithTiming(
        `curl -f -s http://localhost:${service.port}/health || curl -f -s http://localhost:${service.port}/api/version || curl -f -s http://localhost:${service.port}`,
        {
          timeout: 10000,
        }
      );

      if (healthCheck.success) {
        healthyServices++;
        console.log(
          `    ✅ ${service.name} responding in ${healthCheck.duration}ms`
        );
      } else {
        console.log(`    ⚠️  ${service.name} not responding`);
      }
    } catch (error) {
      console.log(`    ❌ ${service.name} health check failed`);
    }
  }

  const totalTime = Date.now() - startTime;
  const serviceCheckTime = Date.now() - serviceCheckStart;

  return {
    startupTime: result.duration,
    totalTime: totalTime,
    serviceCheckTime: serviceCheckTime,
    healthyServices: healthyServices,
    totalServices: services.length,
  };
};

/**
 * Measure resource usage
 */
const measureResourceUsage = (composeCommand, composeFile) => {
  console.log(`  📊 Measuring resource usage for ${composeCommand}...`);

  try {
    let statsCommand;
    if (composeCommand.includes("podman")) {
      statsCommand =
        'podman stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"';
    } else {
      statsCommand =
        'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"';
    }

    const result = executeWithTiming(statsCommand);

    if (result.success) {
      const lines = result.output.split("\n").slice(1); // Skip header
      const containerStats = [];

      for (const line of lines) {
        if (line.trim()) {
          const parts = line.split("\t");
          if (parts.length >= 4) {
            containerStats.push({
              container: parts[0].trim(),
              cpuPercent: parseFloat(parts[1].replace("%", "")),
              memUsage: parts[2].trim(),
              memPercent: parseFloat(parts[3].replace("%", "")),
            });
          }
        }
      }

      // Calculate averages
      const avgCpu =
        containerStats.reduce((sum, stat) => sum + stat.cpuPercent, 0) /
        containerStats.length;
      const avgMem =
        containerStats.reduce((sum, stat) => sum + stat.memPercent, 0) /
        containerStats.length;

      return {
        success: true,
        containerStats: containerStats,
        averageCpu: avgCpu,
        averageMemory: avgMem,
        containerCount: containerStats.length,
      };
    } else {
      return {
        success: false,
        error: result.error,
        containerStats: [],
        averageCpu: 0,
        averageMemory: 0,
        containerCount: 0,
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
      containerStats: [],
      averageCpu: 0,
      averageMemory: 0,
      containerCount: 0,
    };
  }
};

/**
 * Measure response times for services
 */
const measureResponseTimes = async () => {
  console.log("  ⚡ Measuring service response times...");

  const endpoints = [
    { url: "http://localhost:8000/health", name: "gap-detector" },
    { url: "http://localhost:5000/health", name: "analysis-engine" },
    { url: "http://localhost:3000/api/version", name: "windmill" },
    { url: "http://localhost:8080/health", name: "nginx" },
  ];

  const responseTimes = [];

  for (const endpoint of endpoints) {
    const times = [];

    // Make 5 requests to get average response time
    for (let i = 0; i < 5; i++) {
      try {
        const result = executeWithTiming(
          `curl -f -s -w "%{time_total}" -o /dev/null ${endpoint.url}`,
          {
            timeout: 10000,
          }
        );

        if (result.success) {
          times.push(result.duration);
        }
      } catch (error) {
        // Skip failed requests
      }

      await sleep(1000); // Wait between requests
    }

    if (times.length > 0) {
      const avgTime = times.reduce((sum, time) => sum + time, 0) / times.length;
      responseTimes.push({
        service: endpoint.name,
        averageResponseTime: avgTime,
        successfulRequests: times.length,
        totalRequests: 5,
      });

      console.log(`    📈 ${endpoint.name}: ${avgTime.toFixed(2)}ms average`);
    } else {
      responseTimes.push({
        service: endpoint.name,
        averageResponseTime: null,
        successfulRequests: 0,
        totalRequests: 5,
      });

      console.log(`    ❌ ${endpoint.name}: No successful responses`);
    }
  }

  return responseTimes;
};

/**
 * Generate performance comparison report
 */
const generatePerformanceReport = (dockerResults, podmanResults) => {
  console.log("\n📊 PERFORMANCE COMPARISON REPORT");
  console.log("=====================================");

  // Startup Time Comparison
  console.log("\n🚀 Startup Time Comparison:");
  console.log(`Docker startup time: ${dockerResults.startup.startupTime}ms`);
  console.log(`Podman startup time: ${podmanResults.startup.startupTime}ms`);

  const startupDiff =
    podmanResults.startup.startupTime - dockerResults.startup.startupTime;
  const startupPercent = (
    (startupDiff / dockerResults.startup.startupTime) *
    100
  ).toFixed(1);

  if (startupDiff < 0) {
    console.log(
      `✅ Podman is ${Math.abs(startupDiff)}ms (${Math.abs(
        startupPercent
      )}%) faster`
    );
  } else {
    console.log(`⚠️  Podman is ${startupDiff}ms (${startupPercent}%) slower`);
  }

  // Total Time Comparison
  console.log("\n⏱️  Total Deployment Time Comparison:");
  console.log(`Docker total time: ${dockerResults.startup.totalTime}ms`);
  console.log(`Podman total time: ${podmanResults.startup.totalTime}ms`);

  const totalDiff =
    podmanResults.startup.totalTime - dockerResults.startup.totalTime;
  const totalPercent = (
    (totalDiff / dockerResults.startup.totalTime) *
    100
  ).toFixed(1);

  if (totalDiff < 0) {
    console.log(
      `✅ Podman total deployment is ${Math.abs(totalDiff)}ms (${Math.abs(
        totalPercent
      )}%) faster`
    );
  } else {
    console.log(
      `⚠️  Podman total deployment is ${totalDiff}ms (${totalPercent}%) slower`
    );
  }

  // Service Health Comparison
  console.log("\n🏥 Service Health Comparison:");
  console.log(
    `Docker healthy services: ${dockerResults.startup.healthyServices}/${dockerResults.startup.totalServices}`
  );
  console.log(
    `Podman healthy services: ${podmanResults.startup.healthyServices}/${podmanResults.startup.totalServices}`
  );

  // Resource Usage Comparison
  console.log("\n💾 Resource Usage Comparison:");
  if (dockerResults.resources.success && podmanResults.resources.success) {
    console.log(
      `Docker average CPU: ${dockerResults.resources.averageCpu.toFixed(2)}%`
    );
    console.log(
      `Podman average CPU: ${podmanResults.resources.averageCpu.toFixed(2)}%`
    );

    console.log(
      `Docker average Memory: ${dockerResults.resources.averageMemory.toFixed(
        2
      )}%`
    );
    console.log(
      `Podman average Memory: ${podmanResults.resources.averageMemory.toFixed(
        2
      )}%`
    );

    const cpuDiff =
      podmanResults.resources.averageCpu - dockerResults.resources.averageCpu;
    const memDiff =
      podmanResults.resources.averageMemory -
      dockerResults.resources.averageMemory;

    if (cpuDiff < 0) {
      console.log(`✅ Podman uses ${Math.abs(cpuDiff).toFixed(2)}% less CPU`);
    } else {
      console.log(`⚠️  Podman uses ${cpuDiff.toFixed(2)}% more CPU`);
    }

    if (memDiff < 0) {
      console.log(
        `✅ Podman uses ${Math.abs(memDiff).toFixed(2)}% less memory`
      );
    } else {
      console.log(`⚠️  Podman uses ${memDiff.toFixed(2)}% more memory`);
    }
  } else {
    console.log("⚠️  Resource usage comparison unavailable");
  }

  // Response Time Comparison
  console.log("\n⚡ Response Time Comparison:");
  if (dockerResults.responseTimes && podmanResults.responseTimes) {
    for (let i = 0; i < dockerResults.responseTimes.length; i++) {
      const dockerService = dockerResults.responseTimes[i];
      const podmanService = podmanResults.responseTimes.find(
        (s) => s.service === dockerService.service
      );

      if (
        dockerService.averageResponseTime &&
        podmanService &&
        podmanService.averageResponseTime
      ) {
        const timeDiff =
          podmanService.averageResponseTime - dockerService.averageResponseTime;
        const timePercent = (
          (timeDiff / dockerService.averageResponseTime) *
          100
        ).toFixed(1);

        console.log(`${dockerService.service}:`);
        console.log(
          `  Docker: ${dockerService.averageResponseTime.toFixed(2)}ms`
        );
        console.log(
          `  Podman: ${podmanService.averageResponseTime.toFixed(2)}ms`
        );

        if (timeDiff < 0) {
          console.log(
            `  ✅ Podman is ${Math.abs(timeDiff).toFixed(2)}ms (${Math.abs(
              timePercent
            )}%) faster`
          );
        } else {
          console.log(
            `  ⚠️  Podman is ${timeDiff.toFixed(2)}ms (${timePercent}%) slower`
          );
        }
      }
    }
  }

  console.log("\n=====================================");

  // Overall assessment
  let podmanAdvantages = 0;
  let dockerAdvantages = 0;

  if (startupDiff < 0) podmanAdvantages++;
  else dockerAdvantages++;
  if (totalDiff < 0) podmanAdvantages++;
  else dockerAdvantages++;

  if (dockerResults.resources.success && podmanResults.resources.success) {
    if (podmanResults.resources.averageCpu < dockerResults.resources.averageCpu)
      podmanAdvantages++;
    else dockerAdvantages++;

    if (
      podmanResults.resources.averageMemory <
      dockerResults.resources.averageMemory
    )
      podmanAdvantages++;
    else dockerAdvantages++;
  }

  console.log("\n🏆 Overall Performance Assessment:");
  if (podmanAdvantages > dockerAdvantages) {
    console.log("✅ Podman shows better overall performance");
  } else if (dockerAdvantages > podmanAdvantages) {
    console.log("⚠️  Docker shows better overall performance");
  } else {
    console.log("🤝 Performance is comparable between Docker and Podman");
  }

  return {
    podmanAdvantages,
    dockerAdvantages,
    startupDiff,
    totalDiff,
  };
};

/**
 * Test volume persistence across container restarts
 */
const testVolumePersistence = async (composeCommand, composeFile) => {
  console.log(`  💾 Testing volume persistence for ${composeCommand}...`);

  // Insert test data
  const testData = `persistence-test-${Date.now()}`;
  const insertResult = executeWithTiming(
    `${composeCommand} -f ${composeFile} exec -T db psql -U windmill_user -d windmill -c "CREATE TABLE IF NOT EXISTS persistence_test (id SERIAL PRIMARY KEY, test_data TEXT); INSERT INTO persistence_test (test_data) VALUES ('${testData}');"`,
    { timeout: 30000 }
  );

  if (!insertResult.success) {
    return {
      success: false,
      error: `Failed to insert test data: ${insertResult.error}`,
      insertTime: insertResult.duration,
      restartTime: 0,
      verifyTime: 0,
    };
  }

  // Restart database container
  const restartResult = executeWithTiming(
    `${composeCommand} -f ${composeFile} restart db`,
    { timeout: 60000 }
  );

  if (!restartResult.success) {
    return {
      success: false,
      error: `Failed to restart database: ${restartResult.error}`,
      insertTime: insertResult.duration,
      restartTime: restartResult.duration,
      verifyTime: 0,
    };
  }

  // Wait for database to be ready
  await sleep(20000);

  // Verify data still exists
  const verifyResult = executeWithTiming(
    `${composeCommand} -f ${composeFile} exec -T db psql -U windmill_user -d windmill -c "SELECT test_data FROM persistence_test WHERE test_data = '${testData}';"`,
    { timeout: 30000 }
  );

  const dataExists =
    verifyResult.success && verifyResult.output.includes(testData);

  return {
    success: dataExists,
    error: dataExists
      ? null
      : `Data not found after restart: ${verifyResult.error}`,
    insertTime: insertResult.duration,
    restartTime: restartResult.duration,
    verifyTime: verifyResult.duration,
    totalTime:
      insertResult.duration + restartResult.duration + verifyResult.duration,
  };
};

describe("Performance Comparison Tests", () => {
  const dockerComposeFile = "compose.yaml";
  const podmanComposeFile = "infra/podman/podman-compose.yaml";

  let dockerResults = {};
  let podmanResults = {};

  beforeAll(async () => {
    console.log("\n🔧 Setting up performance comparison tests...");

    // Check if both compose files exist
    if (!fs.existsSync(dockerComposeFile)) {
      throw new Error(`Docker compose file not found: ${dockerComposeFile}`);
    }

    if (!fs.existsSync(podmanComposeFile)) {
      throw new Error(`Podman compose file not found: ${podmanComposeFile}`);
    }

    // Check if Docker is available
    try {
      execSync("docker --version", { stdio: "pipe" });
      execSync("docker-compose --version", { stdio: "pipe" });
      console.log("  ✅ Docker and docker-compose available");
    } catch (error) {
      console.log("  ⚠️  Docker not available - skipping Docker tests");
    }

    // Check if Podman is available
    try {
      execSync("podman --version", { stdio: "pipe" });
      execSync("podman-compose --version", { stdio: "pipe" });
      console.log("  ✅ Podman and podman-compose available");
    } catch (error) {
      throw new Error("Podman not available - cannot run comparison tests");
    }

    console.log("  ✅ Performance comparison setup complete");
  }, 60000);

  afterAll(async () => {
    console.log("\n🧹 Cleaning up performance test environment...");

    // Stop Docker services
    try {
      execSync(`docker-compose -f ${dockerComposeFile} down -v`, {
        stdio: "pipe",
        timeout: 60000,
      });
    } catch (error) {
      // Ignore cleanup errors
    }

    // Stop Podman services
    try {
      execSync(`podman-compose -f ${podmanComposeFile} down -v`, {
        stdio: "pipe",
        timeout: 60000,
      });
    } catch (error) {
      // Ignore cleanup errors
    }

    console.log("  ✅ Cleanup complete");
  }, 120000);

  describe("Docker Performance Tests", () => {
    test("should measure Docker startup performance", async () => {
      console.log("\n🐳 Testing Docker performance...");

      try {
        // Check if Docker is available
        execSync("docker --version", { stdio: "pipe" });
        execSync("docker-compose --version", { stdio: "pipe" });

        const startupResults = await measureStartupTime(
          "docker-compose",
          dockerComposeFile
        );
        dockerResults.startup = startupResults;

        console.log(`  📊 Docker Results:`);
        console.log(`    Startup time: ${startupResults.startupTime}ms`);
        console.log(`    Total time: ${startupResults.totalTime}ms`);
        console.log(
          `    Healthy services: ${startupResults.healthyServices}/${startupResults.totalServices}`
        );

        expect(startupResults.startupTime).toBeGreaterThan(0);
        expect(startupResults.healthyServices).toBeGreaterThanOrEqual(2); // At least 50% should be healthy
      } catch (error) {
        console.log(
          "  ⚠️  Docker not available - skipping Docker performance tests"
        );
        dockerResults.startup = {
          startupTime: 0,
          totalTime: 0,
          healthyServices: 0,
          totalServices: 4,
        };
      }
    }, 300000);

    test("should measure Docker resource usage", async () => {
      console.log("\n📊 Measuring Docker resource usage...");

      try {
        execSync("docker --version", { stdio: "pipe" });

        // Wait a bit for services to stabilize
        await sleep(10000);

        const resourceResults = measureResourceUsage(
          "docker-compose",
          dockerComposeFile
        );
        dockerResults.resources = resourceResults;

        if (resourceResults.success) {
          console.log(`  📈 Docker Resource Usage:`);
          console.log(
            `    Average CPU: ${resourceResults.averageCpu.toFixed(2)}%`
          );
          console.log(
            `    Average Memory: ${resourceResults.averageMemory.toFixed(2)}%`
          );
          console.log(`    Container count: ${resourceResults.containerCount}`);
        } else {
          console.log("  ⚠️  Could not measure Docker resource usage");
        }
      } catch (error) {
        console.log(
          "  ⚠️  Docker not available - skipping resource measurement"
        );
        dockerResults.resources = {
          success: false,
          error: "Docker not available",
        };
      }
    }, 60000);

    test("should test Docker volume persistence", async () => {
      console.log("\n💾 Testing Docker volume persistence...");

      try {
        execSync("docker --version", { stdio: "pipe" });

        const persistenceResults = await testVolumePersistence(
          "docker-compose",
          dockerComposeFile
        );
        dockerResults.persistence = persistenceResults;

        if (persistenceResults.success) {
          console.log(`  ✅ Docker volume persistence test passed`);
          console.log(`    Insert time: ${persistenceResults.insertTime}ms`);
          console.log(`    Restart time: ${persistenceResults.restartTime}ms`);
          console.log(`    Verify time: ${persistenceResults.verifyTime}ms`);
          console.log(`    Total time: ${persistenceResults.totalTime}ms`);
        } else {
          console.log(
            `  ❌ Docker volume persistence test failed: ${persistenceResults.error}`
          );
        }
      } catch (error) {
        console.log("  ⚠️  Docker not available - skipping persistence test");
        dockerResults.persistence = {
          success: false,
          error: "Docker not available",
        };
      }
    }, 180000);

    test("should measure Docker response times", async () => {
      console.log("\n⚡ Measuring Docker response times...");

      try {
        execSync("docker --version", { stdio: "pipe" });

        const responseResults = await measureResponseTimes();
        dockerResults.responseTimes = responseResults;

        console.log(
          `  📈 Docker Response Times measured for ${responseResults.length} services`
        );
      } catch (error) {
        console.log(
          "  ⚠️  Docker not available - skipping response time measurement"
        );
        dockerResults.responseTimes = [];
      }
    }, 120000);
  });

  describe("Podman Performance Tests", () => {
    test("should measure Podman startup performance", async () => {
      console.log("\n🦭 Testing Podman performance...");

      const startupResults = await measureStartupTime(
        "podman-compose",
        podmanComposeFile
      );
      podmanResults.startup = startupResults;

      console.log(`  📊 Podman Results:`);
      console.log(`    Startup time: ${startupResults.startupTime}ms`);
      console.log(`    Total time: ${startupResults.totalTime}ms`);
      console.log(
        `    Healthy services: ${startupResults.healthyServices}/${startupResults.totalServices}`
      );

      expect(startupResults.startupTime).toBeGreaterThan(0);
      expect(startupResults.healthyServices).toBeGreaterThanOrEqual(2); // At least 50% should be healthy
    }, 300000);

    test("should measure Podman resource usage", async () => {
      console.log("\n📊 Measuring Podman resource usage...");

      // Wait a bit for services to stabilize
      await sleep(10000);

      const resourceResults = measureResourceUsage(
        "podman-compose",
        podmanComposeFile
      );
      podmanResults.resources = resourceResults;

      if (resourceResults.success) {
        console.log(`  📈 Podman Resource Usage:`);
        console.log(
          `    Average CPU: ${resourceResults.averageCpu.toFixed(2)}%`
        );
        console.log(
          `    Average Memory: ${resourceResults.averageMemory.toFixed(2)}%`
        );
        console.log(`    Container count: ${resourceResults.containerCount}`);

        // Podman should have reasonable resource usage
        expect(resourceResults.averageCpu).toBeLessThan(50); // Less than 50% CPU on average
        expect(resourceResults.averageMemory).toBeLessThan(80); // Less than 80% memory on average
      } else {
        console.log("  ⚠️  Could not measure Podman resource usage");
      }
    }, 60000);

    test("should measure Podman response times", async () => {
      console.log("\n⚡ Measuring Podman response times...");

      const responseResults = await measureResponseTimes();
      podmanResults.responseTimes = responseResults;

      console.log(
        `  📈 Podman Response Times measured for ${responseResults.length} services`
      );

      // At least 75% of services should respond
      const respondingServices = responseResults.filter(
        (r) => r.averageResponseTime !== null
      ).length;
      expect(respondingServices).toBeGreaterThanOrEqual(
        Math.ceil(responseResults.length * 0.75)
      );
    }, 120000);

    test("should test Podman volume persistence", async () => {
      console.log("\n💾 Testing Podman volume persistence...");

      const persistenceResults = await testVolumePersistence(
        "podman-compose",
        podmanComposeFile
      );
      podmanResults.persistence = persistenceResults;

      if (persistenceResults.success) {
        console.log(`  ✅ Podman volume persistence test passed`);
        console.log(`    Insert time: ${persistenceResults.insertTime}ms`);
        console.log(`    Restart time: ${persistenceResults.restartTime}ms`);
        console.log(`    Verify time: ${persistenceResults.verifyTime}ms`);
        console.log(`    Total time: ${persistenceResults.totalTime}ms`);

        // Podman should have reasonable persistence performance
        expect(persistenceResults.totalTime).toBeLessThan(120000); // Less than 2 minutes total
      } else {
        console.log(
          `  ❌ Podman volume persistence test failed: ${persistenceResults.error}`
        );
        throw new Error(
          `Volume persistence test failed: ${persistenceResults.error}`
        );
      }
    }, 180000);
  });

  describe("Performance Comparison Analysis", () => {
    test("should generate comprehensive performance comparison", () => {
      console.log("\n📊 Generating performance comparison analysis...");

      const comparison = generatePerformanceReport(
        dockerResults,
        podmanResults
      );

      // The migration should not significantly degrade performance
      // Allow up to 50% slower startup time as acceptable for the security benefits
      if (dockerResults.startup.startupTime > 0) {
        const startupDegradation =
          comparison.startupDiff / dockerResults.startup.startupTime;
        expect(startupDegradation).toBeLessThan(0.5); // No more than 50% slower
      }

      // Total deployment time should be reasonable
      expect(podmanResults.startup.totalTime).toBeLessThan(300000); // Less than 5 minutes

      // At least as many services should be healthy
      expect(podmanResults.startup.healthyServices).toBeGreaterThanOrEqual(
        Math.max(2, dockerResults.startup.healthyServices - 1)
      );

      console.log("  ✅ Performance comparison analysis complete");
    }, 30000);
  });
});
