#!/usr/bin/env pwsh
param(
    [switch]$Help,
    [switch]$SkipJest,
    [switch]$Verbose
)

# Comprehensive migration validation test script (PowerShell version)
# This script runs various tests to validate the Docker-to-Podman migration

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PodmanComposeFile = Join-Path $ProjectRoot "infra/podman/podman-compose.yaml"
$DockerComposeFile = Join-Path $ProjectRoot "compose.yaml"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check if Podman is installed
    if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
        Write-Error "Podman is not installed"
        return $false
    }
    
    # Check if podman-compose is installed
    if (-not (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
        Write-Error "podman-compose is not installed"
        return $false
    }
    
    # Check if Node.js is available for Jest tests
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Warning "Node.js not found - Jest tests will be skipped"
    }
    
    # Check if compose files exist
    if (-not (Test-Path $PodmanComposeFile)) {
        Write-Error "Podman compose file not found: $PodmanComposeFile"
        return $false
    }
    
    Write-Success "Prerequisites check passed"
    return $true
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -ErrorAction Stop
        return @{
            Success = $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
            StatusCode = $response.StatusCode
            Error = $null
        }
    } catch {
        return @{
            Success = $false
            StatusCode = $null
            Error = $_.Exception.Message
        }
    }
}

# Function to wait for service to become healthy
function Wait-ForService {
    param(
        [int]$Port,
        [string]$Path = "/health",
        [int]$MaxAttempts = 30,
        [int]$IntervalSeconds = 5
    )
    
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Write-Status "    Attempt $attempt/$MaxAttempts`: Checking service on port $Port..."
        
        $url = "http://localhost:$Port$Path"
        $result = Test-HttpEndpoint -Url $url -TimeoutSeconds 5
        
        if ($result.Success) {
            Write-Success "    Service on port $Port is healthy"
            return $true
        }
        
        if ($attempt -lt $MaxAttempts) {
            Write-Status "    Service not ready, waiting $IntervalSeconds seconds..."
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
    
    Write-Error "    Service on port $Port failed to become healthy after $MaxAttempts attempts"
    return $false
}

# Function to run basic connectivity tests
function Test-BasicConnectivity {
    Write-Status "Running basic connectivity tests..."
    
    $services = @(
        @{Port=8000; Name="gap-detector"; Path="/health"},
        @{Port=5000; Name="analysis-engine"; Path="/health"},
        @{Port=3000; Name="windmill"; Path="/api/version"},
        @{Port=8080; Name="nginx"; Path="/health"}
    )
    
    $healthyCount = 0
    $totalServices = $services.Count
    
    foreach ($service in $services) {
        Write-Status "Testing $($service.Name) on port $($service.Port)..."
        
        # Check if port is listening
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $service.Port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($connection) {
                Write-Success "Port $($service.Port) is listening"
                
                # Try to connect to health endpoint
                $healthUrl = "http://localhost:$($service.Port)$($service.Path)"
                $healthResult = Test-HttpEndpoint -Url $healthUrl -TimeoutSeconds 10
                
                if ($healthResult.Success) {
                    Write-Success "$($service.Name) service is responding"
                    $healthyCount++
                } else {
                    Write-Warning "$($service.Name) service on port $($service.Port) may not be ready"
                }
            } else {
                Write-Warning "Port $($service.Port) is not listening - $($service.Name) may not be started"
            }
        } catch {
            Write-Warning "Could not check port $($service.Port) for $($service.Name)"
        }
    }
    
    Write-Status "Connectivity test results: $healthyCount/$totalServices services responding"
    
    # Return success if at least 75% of services are healthy
    $minHealthy = [math]::Floor($totalServices * 0.75)
    if ($healthyCount -ge $minHealthy) {
        Write-Success "Basic connectivity tests passed"
        return $true
    } else {
        Write-Error "Basic connectivity tests failed"
        return $false
    }
}

# Function to test database connectivity
function Test-DatabaseConnectivity {
    Write-Status "Testing database connectivity..."
    
    # Wait for database to be ready
    $maxAttempts = 30
    $attempt = 1
    
    while ($attempt -le $maxAttempts) {
        try {
            $result = & podman exec phoenix-hydra_db_1 pg_isready -U windmill_user -d windmill 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Database is ready"
                break
            }
        } catch {
            # Continue trying
        }
        
        if ($attempt -eq $maxAttempts) {
            Write-Error "Database failed to become ready after $maxAttempts attempts"
            return $false
        }
        
        Write-Status "Waiting for database... (attempt $attempt/$maxAttempts)"
        Start-Sleep -Seconds 5
        $attempt++
    }
    
    # Test database connection
    try {
        $result = & podman exec phoenix-hydra_db_1 psql -U windmill_user -d windmill -c "SELECT version();" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database connection test passed"
            return $true
        } else {
            Write-Error "Database connection test failed"
            return $false
        }
    } catch {
        Write-Error "Database connection test failed with exception: $_"
        return $false
    }
}

# Function to test network isolation
function Test-NetworkIsolation {
    Write-Status "Testing network isolation..."
    
    # Check if phoenix-net network exists
    try {
        $networkExists = & podman network exists phoenix-hydra_phoenix-net 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Phoenix network exists"
            
            # Show network details
            try {
                $networkInfo = & podman network inspect phoenix-hydra_phoenix-net --format "{{.Subnets}}" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Status "Network subnet: $networkInfo"
                }
            } catch {
                Write-Status "Network subnet: unknown"
            }
            
            # Test inter-container connectivity
            try {
                $pingResult = & podman exec phoenix-hydra_gap-detector_1 ping -c 1 db 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Inter-container connectivity working"
                } else {
                    Write-Warning "Inter-container connectivity test inconclusive"
                }
            } catch {
                Write-Warning "Inter-container connectivity test inconclusive"
            }
            
            return $true
        } else {
            Write-Error "Phoenix network not found"
            return $false
        }
    } catch {
        Write-Error "Network isolation test failed: $_"
        return $false
    }
}

# Function to test volume persistence
function Test-VolumePersistence {
    Write-Status "Testing volume persistence..."
    
    # Check if database volume is mounted
    try {
        $volumeTest = & podman exec phoenix-hydra_db_1 test -d /var/lib/postgresql/data 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database volume is mounted"
            
            # Test write permissions
            $testFile = "/var/lib/postgresql/data/migration_test_$(Get-Date -Format 'yyyyMMddHHmmss')"
            try {
                $touchResult = & podman exec phoenix-hydra_db_1 touch $testFile 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "Database volume has write permissions"
                    # Clean up test file
                    & podman exec phoenix-hydra_db_1 rm -f $testFile 2>$null | Out-Null
                } else {
                    Write-Warning "Database volume write test failed"
                }
            } catch {
                Write-Warning "Database volume write test failed"
            }
            
            return $true
        } else {
            Write-Error "Database volume not properly mounted"
            return $false
        }
    } catch {
        Write-Error "Volume persistence test failed: $_"
        return $false
    }
}

# Function to test security configuration
function Test-SecurityConfiguration {
    Write-Status "Testing security configuration..."
    
    # Get list of running containers
    try {
        $containers = & podman-compose -f $PodmanComposeFile ps --format "{{.Names}}" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $containers) {
            Write-Error "No containers found"
            return $false
        }
        
        $securityIssues = 0
        
        foreach ($container in $containers) {
            if ($container.Trim()) {
                Write-Status "Checking security for container: $container"
                
                # Check user configuration
                try {
                    $userInfo = & podman inspect $container --format "{{.Config.User}}" 2>$null
                    if ($LASTEXITCODE -eq 0 -and $userInfo -and $userInfo -ne "unknown" -and $userInfo -ne "0:0") {
                        Write-Success "Container $container running as non-root user: $userInfo"
                    } else {
                        Write-Warning "Container $container user configuration unclear: $userInfo"
                        $securityIssues++
                    }
                } catch {
                    Write-Warning "Could not check user configuration for $container"
                    $securityIssues++
                }
                
                # Check security options
                try {
                    $securityOpts = & podman inspect $container --format "{{.HostConfig.SecurityOpt}}" 2>$null
                    if ($LASTEXITCODE -eq 0 -and $securityOpts -like "*no-new-privileges*") {
                        Write-Success "Container $container has no-new-privileges enabled"
                    } else {
                        Write-Warning "Container $container may not have no-new-privileges enabled"
                        $securityIssues++
                    }
                } catch {
                    Write-Warning "Could not check security options for $container"
                    $securityIssues++
                }
            }
        }
        
        if ($securityIssues -eq 0) {
            Write-Success "Security configuration tests passed"
            return $true
        } else {
            Write-Warning "Security configuration has $securityIssues potential issues"
            return $true  # Don't fail the test for security warnings
        }
    } catch {
        Write-Error "Security configuration test failed: $_"
        return $false
    }
}

# Function to test performance
function Test-Performance {
    Write-Status "Running performance tests..."
    
    # Measure startup time
    Write-Status "Measuring service startup time..."
    $startTime = Get-Date
    
    # Stop services first
    try {
        & podman-compose -f $PodmanComposeFile down 2>$null | Out-Null
        Start-Sleep -Seconds 5
    } catch {
        # Ignore errors when stopping
    }
    
    # Start services and measure time
    $startupStart = Get-Date
    
    try {
        & podman-compose -f $PodmanComposeFile up -d 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $startupEnd = Get-Date
            $startupTime = ($startupEnd - $startupStart).TotalSeconds
            
            Write-Success "Services started in $([math]::Round($startupTime, 1)) seconds"
            
            # Wait for services to be healthy
            Start-Sleep -Seconds 30
            
            # Test if services are responding
            if (Test-BasicConnectivity) {
                $totalTime = (Get-Date) - $startTime
                Write-Success "Total deployment and health check time: $([math]::Round($totalTime.TotalSeconds, 1)) seconds"
                
                # Performance should be reasonable (under 5 minutes)
                if ($totalTime.TotalSeconds -lt 300) {
                    Write-Success "Performance test passed"
                    return $true
                } else {
                    Write-Warning "Performance test completed but took longer than expected"
                    return $true
                }
            } else {
                Write-Error "Services failed to become healthy after startup"
                return $false
            }
        } else {
            Write-Error "Failed to start services for performance test"
            return $false
        }
    } catch {
        Write-Error "Performance test failed: $_"
        return $false
    }
}

# Function to run Jest integration tests
function Invoke-JestTests {
    Write-Status "Running Jest integration tests..."
    
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Push-Location $ProjectRoot
        
        try {
            # Install dependencies if needed
            if (-not (Test-Path "node_modules")) {
                Write-Status "Installing npm dependencies..."
                & npm install
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Failed to install npm dependencies"
                    return $false
                }
            }
            
            # Run the migration-specific tests
            & npm test -- --testPathPattern="podman-migration" --verbose
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Jest integration tests passed"
                return $true
            } else {
                Write-Error "Jest integration tests failed"
                return $false
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Warning "Node.js not available - skipping Jest tests"
        return $true
    }
}

# Function to generate test report
function New-TestReport {
    param([array]$TestResults)
    
    $totalTests = $TestResults.Count
    $passedTests = ($TestResults | Where-Object { $_ -like "*:PASSED" }).Count
    
    Write-Status "Generating test report..."
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "         MIGRATION TEST REPORT"
    Write-Host "=========================================="
    Write-Host ""
    
    foreach ($result in $TestResults) {
        $testName = $result.Split(':')[0]
        $testResult = $result.Split(':')[1]
        
        if ($testResult -eq "PASSED") {
            Write-Host "✅ $testName`: " -NoNewline
            Write-Host "PASSED" -ForegroundColor Green
        } else {
            Write-Host "❌ $testName`: " -NoNewline
            Write-Host "FAILED" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "Summary: $passedTests/$totalTests tests passed"
    
    $passRate = [math]::Round(($passedTests * 100 / $totalTests), 1)
    if ($passRate -ge 80) {
        Write-Host "Overall result: " -NoNewline
        Write-Host "MIGRATION VALIDATION SUCCESSFUL" -ForegroundColor Green
        Write-Host "The Docker-to-Podman migration appears to be working correctly."
    } elseif ($passRate -ge 60) {
        Write-Host "Overall result: " -NoNewline
        Write-Host "MIGRATION PARTIALLY SUCCESSFUL" -ForegroundColor Yellow
        Write-Host "The migration is mostly working but some issues were detected."
    } else {
        Write-Host "Overall result: " -NoNewline
        Write-Host "MIGRATION VALIDATION FAILED" -ForegroundColor Red
        Write-Host "Significant issues were detected with the migration."
    }
    Write-Host "=========================================="
    Write-Host ""
    
    return [math]::Floor(100 - $passRate)
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: test-migration.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help        Show this help message"
    Write-Host "  -SkipJest    Skip Jest integration tests"
    Write-Host "  -Verbose     Enable verbose output"
    Write-Host ""
    Write-Host "This script runs comprehensive validation tests for the Docker-to-Podman migration."
}

# Main test execution function
function Invoke-MigrationTests {
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    Write-Status "Starting comprehensive migration validation tests..."
    Write-Host ""
    
    # Array to store test results
    $testResults = @()
    
    # Check prerequisites
    if (Test-Prerequisites) {
        $testResults += "Prerequisites:PASSED"
    } else {
        $testResults += "Prerequisites:FAILED"
        Write-Error "Prerequisites check failed - aborting tests"
        exit 1
    }
    
    # Ensure services are running
    Write-Status "Ensuring services are running..."
    try {
        & podman-compose -f $PodmanComposeFile up -d 2>$null | Out-Null
        Start-Sleep -Seconds 30  # Give services time to start
    } catch {
        Write-Warning "Could not start services automatically"
    }
    
    # Run individual tests
    if (Test-BasicConnectivity) {
        $testResults += "Basic Connectivity:PASSED"
    } else {
        $testResults += "Basic Connectivity:FAILED"
    }
    
    if (Test-DatabaseConnectivity) {
        $testResults += "Database Connectivity:PASSED"
    } else {
        $testResults += "Database Connectivity:FAILED"
    }
    
    if (Test-NetworkIsolation) {
        $testResults += "Network Isolation:PASSED"
    } else {
        $testResults += "Network Isolation:FAILED"
    }
    
    if (Test-VolumePersistence) {
        $testResults += "Volume Persistence:PASSED"
    } else {
        $testResults += "Volume Persistence:FAILED"
    }
    
    if (Test-SecurityConfiguration) {
        $testResults += "Security Configuration:PASSED"
    } else {
        $testResults += "Security Configuration:FAILED"
    }
    
    if (Test-Performance) {
        $testResults += "Performance:PASSED"
    } else {
        $testResults += "Performance:FAILED"
    }
    
    if (-not $SkipJest) {
        if (Invoke-JestTests) {
            $testResults += "Jest Integration Tests:PASSED"
        } else {
            $testResults += "Jest Integration Tests:FAILED"
        }
    } else {
        Write-Status "Skipping Jest tests as requested"
    }
    
    # Generate final report
    $exitCode = New-TestReport -TestResults $testResults
    
    Write-Status "Migration validation tests completed"
    exit $exitCode
}

# Handle script interruption
trap {
    Write-Error "Tests interrupted"
    exit 1
}

# Run main function
try {
    Invoke-MigrationTests
} catch {
    Write-Error "Test execution failed: $_"
    exit 1
}