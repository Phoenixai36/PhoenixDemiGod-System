# Test script for gap-detector Containerfile
param(
    [switch]$SkipCleanup
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "../../..")

Write-Host "Testing gap-detector Containerfile..." -ForegroundColor Green
Write-Host "Project root: $ProjectRoot"

# Change to project root for build context
Set-Location $ProjectRoot

try {
    # Build the container image
    Write-Host "Building gap-detector container image..." -ForegroundColor Yellow
    podman build -f infra/podman/gap-detector/Containerfile -t phoenix-hydra/gap-detector:test .

    # Test that the image was built successfully
    Write-Host "Verifying image was built..." -ForegroundColor Yellow
    $images = podman images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -match "phoenix-hydra/gap-detector:test" }
    if (-not $images) {
        throw "Image phoenix-hydra/gap-detector:test was not found"
    }
    Write-Host "Image found: $images" -ForegroundColor Green

    # Test running the container (dry run)
    Write-Host "Testing container execution (dry run)..." -ForegroundColor Yellow
    podman run --rm --name gap-detector-test `
        -e PROJECT_PATH=/app `
        -e REPORT_OUTPUT_PATH=/app/data/test_report.json `
        -e CI_REPORT_OUTPUT_PATH=/app/data/test_ci_report.json `
        --user 1000:1000 `
        phoenix-hydra/gap-detector:test python -c "print('Container runs successfully')"

    Write-Host "Gap-detector Containerfile test completed successfully!" -ForegroundColor Green

} catch {
    Write-Error "Test failed: $_"
    exit 1
} finally {
    if (-not $SkipCleanup) {
        # Clean up test image
        Write-Host "Cleaning up test image..." -ForegroundColor Yellow
        try {
            podman rmi phoenix-hydra/gap-detector:test
            Write-Host "Test cleanup completed." -ForegroundColor Green
        } catch {
            Write-Warning "Failed to clean up test image: $_"
        }
    }
}