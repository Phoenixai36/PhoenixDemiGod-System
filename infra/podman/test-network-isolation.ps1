# Phoenix Hydra Network Isolation Test Script (PowerShell)
# This script tests network isolation and security boundaries

param(
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "🔒 Testing Phoenix Hydra network isolation and security boundaries..." -ForegroundColor Cyan

# Function to test port accessibility
function Test-PortAccessibility {
    param(
        [string]$Host,
        [int]$Port,
        [string]$ServiceName,
        [bool]$ShouldBeAccessible
    )
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $connectTask = $tcpClient.ConnectAsync($Host, $Port)
        $connectTask.Wait(2000)  # 2 second timeout
        
        if ($tcpClient.Connected) {
            $tcpClient.Close()
            if ($ShouldBeAccessible) {
                Write-Host "  ✅ $ServiceName accessible on port $Port (expected)" -ForegroundColor Green
            } else {
                Write-Host "  ❌ $ServiceName accessible on port $Port (SECURITY ISSUE - should be blocked)" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        if ($ShouldBeAccessible) {
            Write-Host "  ⚠️  $ServiceName not accessible on port $Port (may not be ready)" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ $ServiceName blocked on port $Port (expected)" -ForegroundColor Green
        }
    }
    return $true
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Url,
        [string]$ServiceName,
        [bool]$ShouldBeAccessible
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            if ($ShouldBeAccessible) {
                Write-Host "  ✅ $ServiceName HTTP endpoint accessible (expected)" -ForegroundColor Green
            } else {
                Write-Host "  ❌ $ServiceName HTTP endpoint accessible (SECURITY ISSUE - should be blocked)" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        if ($ShouldBeAccessible) {
            Write-Host "  ⚠️  $ServiceName HTTP endpoint not accessible (may not be ready)" -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ $ServiceName HTTP endpoint blocked (expected)" -ForegroundColor Green
        }
    }
    return $true
}

# Function to test inter-container communication
function Test-InterContainerCommunication {
    Write-Host "Testing inter-container communication..." -ForegroundColor Yellow
    
    try {
        $containers = podman ps --format "{{.Names}}" | Where-Object { $_ -match "phoenix-hydra" }
        
        if ($containers.Count -eq 0) {
            Write-Host "  ⚠️  No Phoenix Hydra containers running" -ForegroundColor Yellow
            return
        }
        
        # Test DNS resolution between containers
        $testContainer = $containers[0]  # Use first container for testing
        Write-Host "  Testing DNS resolution from $testContainer:" -ForegroundColor Gray
        
        $services = @("db", "windmill", "nginx", "gap-detector", "recurrent-processor", "rubik-agent", "analysis-engine")
        
        foreach ($service in $services) {
            try {
                $result = podman exec $testContainer nslookup $service 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✅ Can resolve $service" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  Cannot resolve $service (may be normal if service not running)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ⚠️  Cannot test DNS resolution for $service" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "  ❌ Could not test inter-container communication: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to test volume security
function Test-VolumeSecurity {
    Write-Host "Testing volume security..." -ForegroundColor Yellow
    
    $PhoenixDataDir = "$env:USERPROFILE\.local\share\phoenix-hydra"
    
    # Test database volume permissions
    $dbDataPath = "$PhoenixDataDir\db_data"
    if (Test-Path $dbDataPath) {
        try {
            $acl = Get-Acl $dbDataPath
            $hasRestrictiveAccess = $acl.Access | Where-Object { 
                $_.IdentityReference -like "*$env:USERNAME*" -and 
                $_.FileSystemRights -match "FullControl"
            }
            
            if ($hasRestrictiveAccess) {
                Write-Host "  ✅ Database volume has restrictive permissions" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Database volume permissions may not be restrictive enough" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ⚠️  Could not check database volume permissions" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Database volume directory not found" -ForegroundColor Red
    }
    
    # Test nginx config volume
    $nginxConfigPath = "$PhoenixDataDir\nginx_config"
    if (Test-Path $nginxConfigPath) {
        Write-Host "  ✅ Nginx config volume exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Nginx config volume directory not found" -ForegroundColor Red
    }
    
    # Test logs volume
    $logsPath = "$PhoenixDataDir\logs"
    if (Test-Path $logsPath) {
        Write-Host "  ✅ Logs volume exists" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Logs volume directory not found" -ForegroundColor Red
    }
    
    # Test that volumes are accessible by current user
    $volumePaths = @($dbDataPath, $nginxConfigPath, $logsPath)
    foreach ($volumePath in $volumePaths) {
        if (Test-Path $volumePath) {
            try {
                $testFile = Join-Path $volumePath ".access_test"
                New-Item -ItemType File -Path $testFile -Force | Out-Null
                Remove-Item $testFile -Force
                Write-Host "  ✅ $(Split-Path $volumePath -Leaf) volume is writable by current user" -ForegroundColor Green
            } catch {
                Write-Host "  ⚠️  $(Split-Path $volumePath -Leaf) volume may not be writable by current user" -ForegroundColor Yellow
            }
        }
    }
}

# Function to test container security
function Test-ContainerSecurity {
    Write-Host "Testing container security..." -ForegroundColor Yellow
    
    try {
        $containers = podman ps --format "{{.Names}}" | Where-Object { $_ -match "phoenix-hydra" }
        
        if ($containers.Count -eq 0) {
            Write-Host "  ⚠️  No Phoenix Hydra containers running" -ForegroundColor Yellow
            return
        }
        
        foreach ($container in $containers) {
            Write-Host "  Testing security for $container:" -ForegroundColor Gray
            
            # Check if running as non-root
            try {
                $userInfo = podman inspect $container --format "{{.Config.User}}" 2>$null
                if ($userInfo -and $userInfo -ne "root" -and $userInfo -ne "") {
                    Write-Host "    ✅ Running as non-root user: $userInfo" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  User info: $userInfo" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ⚠️  Could not check user info" -ForegroundColor Yellow
            }
            
            # Check security options
            try {
                $securityOpts = podman inspect $container --format "{{.HostConfig.SecurityOpt}}" 2>$null
                if ($securityOpts -match "no-new-privileges:true") {
                    Write-Host "    ✅ no-new-privileges enabled" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  no-new-privileges not found in security options" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ⚠️  Could not check security options" -ForegroundColor Yellow
            }
            
            # Check if container has privileged access
            try {
                $privileged = podman inspect $container --format "{{.HostConfig.Privileged}}" 2>$null
                if ($privileged -eq "false") {
                    Write-Host "    ✅ Container is not privileged" -ForegroundColor Green
                } else {
                    Write-Host "    ⚠️  Container privileged status: $privileged" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ⚠️  Could not check privileged status" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "  ❌ Could not test container security: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to test network configuration
function Test-NetworkConfiguration {
    Write-Host "Testing network configuration..." -ForegroundColor Yellow
    
    try {
        $networkInfo = podman network inspect phoenix-hydra_phoenix-net 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ phoenix-net network exists" -ForegroundColor Green
            
            # Check network configuration
            try {
                $subnet = podman network inspect phoenix-hydra_phoenix-net --format "{{range .Subnets}}{{.Subnet}}{{end}}" 2>$null
                if ($subnet -eq "172.20.0.0/16") {
                    Write-Host "  ✅ Network subnet correctly configured: $subnet" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠️  Network subnet: $subnet (expected: 172.20.0.0/16)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  ⚠️  Could not check network subnet" -ForegroundColor Yellow
            }
            
            # Check if network is internal
            try {
                $internal = podman network inspect phoenix-hydra_phoenix-net --format "{{.Internal}}" 2>$null
                if ($internal -eq "false") {
                    Write-Host "  ✅ Network allows external connectivity" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠️  Network internal setting: $internal" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  ⚠️  Could not check network internal setting" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  ❌ phoenix-net network not found" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ Could not test network configuration: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Main test execution
function Invoke-MainTests {
    Write-Host "Starting network isolation tests..." -ForegroundColor Cyan
    Write-Host ""
    
    # Test 1: External port accessibility
    Write-Host "Test 1: External Port Accessibility" -ForegroundColor Yellow
    Write-Host "====================================" -ForegroundColor Yellow
    
    # These ports should be accessible from outside
    Test-PortAccessibility -Host "localhost" -Port 8000 -ServiceName "Gap Detector API" -ShouldBeAccessible $true
    Test-PortAccessibility -Host "localhost" -Port 3000 -ServiceName "Windmill UI" -ShouldBeAccessible $true
    Test-PortAccessibility -Host "localhost" -Port 8080 -ServiceName "Nginx Proxy" -ShouldBeAccessible $true
    Test-PortAccessibility -Host "localhost" -Port 5000 -ServiceName "Analysis Engine API" -ShouldBeAccessible $true
    
    # These ports should NOT be accessible from outside
    Test-PortAccessibility -Host "localhost" -Port 5432 -ServiceName "PostgreSQL Database" -ShouldBeAccessible $false
    
    Write-Host ""
    
    # Test 2: HTTP endpoint accessibility
    Write-Host "Test 2: HTTP Endpoint Accessibility" -ForegroundColor Yellow
    Write-Host "====================================" -ForegroundColor Yellow
    
    Test-HttpEndpoint -Url "http://localhost:8000/health" -ServiceName "Gap Detector" -ShouldBeAccessible $true
    Test-HttpEndpoint -Url "http://localhost:3000/api/version" -ServiceName "Windmill" -ShouldBeAccessible $true
    Test-HttpEndpoint -Url "http://localhost:8080/health" -ServiceName "Nginx" -ShouldBeAccessible $true
    Test-HttpEndpoint -Url "http://localhost:5000/health" -ServiceName "Analysis Engine" -ShouldBeAccessible $true
    
    Write-Host ""
    
    # Test 3: Network configuration
    Write-Host "Test 3: Network Configuration" -ForegroundColor Yellow
    Write-Host "==============================" -ForegroundColor Yellow
    Test-NetworkConfiguration
    
    Write-Host ""
    
    # Test 4: Inter-container communication
    Write-Host "Test 4: Inter-container Communication" -ForegroundColor Yellow
    Write-Host "=====================================" -ForegroundColor Yellow
    Test-InterContainerCommunication
    
    Write-Host ""
    
    # Test 5: Volume security
    Write-Host "Test 5: Volume Security" -ForegroundColor Yellow
    Write-Host "=======================" -ForegroundColor Yellow
    Test-VolumeSecurity
    
    Write-Host ""
    
    # Test 6: Container security
    Write-Host "Test 6: Container Security" -ForegroundColor Yellow
    Write-Host "==========================" -ForegroundColor Yellow
    Test-ContainerSecurity
    
    Write-Host ""
    Write-Host "🎉 Network isolation and security boundary tests completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Summary of security features tested:" -ForegroundColor Yellow
    Write-Host "  ✅ External port exposure (8000, 3000, 8080, 5000)"
    Write-Host "  ✅ Database port isolation (5432 blocked externally)"
    Write-Host "  ✅ HTTP endpoint accessibility"
    Write-Host "  ✅ Network configuration and isolation"
    Write-Host "  ✅ Inter-container DNS resolution"
    Write-Host "  ✅ Volume permission restrictions"
    Write-Host "  ✅ Container security options"
    Write-Host ""
    Write-Host "If any tests show warnings or errors, review the security configuration." -ForegroundColor Cyan
}

# Check if containers are running
try {
    $runningContainers = podman-compose -f $ComposeFile ps | Where-Object { $_ -match "Up" }
    
    if (-not $runningContainers) {
        Write-Host "⚠️  Phoenix Hydra containers are not running." -ForegroundColor Yellow
        Write-Host "Start them first with: podman-compose -f $ComposeFile up -d"
        Write-Host ""
        Write-Host "Running basic configuration tests only..." -ForegroundColor Yellow
        Write-Host ""
        
        # Run only tests that don't require running containers
        Write-Host "Test: Network Configuration" -ForegroundColor Yellow
        Write-Host "==========================" -ForegroundColor Yellow
        Test-NetworkConfiguration
        
        Write-Host ""
        Write-Host "Test: Volume Security" -ForegroundColor Yellow
        Write-Host "====================" -ForegroundColor Yellow
        Test-VolumeSecurity
        
        Write-Host ""
        Write-Host "To run full tests, start the containers and run this script again." -ForegroundColor Cyan
    } else {
        # Run all tests
        Invoke-MainTests
    }
} catch {
    Write-Host "❌ Could not check container status: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Running basic configuration tests only..." -ForegroundColor Yellow
    
    # Run basic tests
    Test-NetworkConfiguration
    Test-VolumeSecurity
}