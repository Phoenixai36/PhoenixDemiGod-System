const { execSync } = require('child_process');

/**
 * Helper function to execute a shell script from the project root.
 * @param {string} scriptName - The name of the script to execute (e.g., 'deploy.sh').
 * @returns {{code: number, error?: Error}} - An object indicating the exit code and an optional error.
 */
const executeScript = (scriptName) => {
  try {
    // The scripts are in the project root, so we can call them directly with a relative path.
    // The CWD for execSync is the project root where `npm test` is run.
    // Using 'bash ./${scriptName}' is more portable for Windows environments with Git Bash.
    execSync(`bash ./${scriptName}`, { stdio: 'inherit' });
    return { code: 0 };
  } catch (error) {
    console.error(`Error executing script: ${scriptName}`);
    return { code: error.status || 1, error };
  }
};

describe('Phoenix DemiGod Deployment Lifecycle', () => {
  // This is a long-running integration test that validates the entire container lifecycle.
  // The timeout has been increased in jest.config.js to accommodate this.

  it('should successfully deploy, verify, and tear down the application stack', () => {
    // Step 1: Deploy the application
    console.log('\n🚀 [TEST] Executing deploy.sh...');
    const deployResult = executeScript('deploy.sh');
    expect(deployResult.code).toBe(0, `Deployment script 'deploy.sh' failed with exit code ${deployResult.code}.`);
    console.log('✅ [TEST] deploy.sh executed successfully.');

    // Step 2: Verify the deployment
    console.log('\n🔍 [TEST] Executing verify.sh...');
    const verifyResult = executeScript('verify.sh');
    expect(verifyResult.code).toBe(0, `Verification script 'verify.sh' failed with exit code ${verifyResult.code}.`);
    console.log('✅ [TEST] verify.sh executed successfully.');

    // Step 3: Tear down the application
    // This runs even if the other steps fail, ensuring cleanup.
    // We use a finally block logic here, but in Jest, we'll just run it sequentially.
    // For a more robust setup, afterAll() could be used.
    console.log('\n🧹 [TEST] Executing teardown.sh...');
    const teardownResult = executeScript('teardown.sh');
    expect(teardownResult.code).toBe(0, `Teardown script 'teardown.sh' failed with exit code ${teardownResult.code}.`);
    console.log('✅ [TEST] teardown.sh executed successfully.');
  });
});