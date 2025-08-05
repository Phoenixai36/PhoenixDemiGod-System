/** @type {import('jest').Config} */
const config = {
  verbose: true,
  testTimeout: 600000, // 10 minutes timeout for comprehensive migration tests
  maxWorkers: 1, // Run tests sequentially to avoid resource conflicts
  testMatch: ["**/__tests__/**/*.test.js", "**/?(*.)+(spec|test).js"],
  setupFilesAfterEnv: [],
  testEnvironment: "node",
  collectCoverage: false, // Disable coverage for integration tests
  forceExit: true, // Force exit after tests complete
  detectOpenHandles: true, // Detect handles that prevent Jest from exiting
};

module.exports = config;
