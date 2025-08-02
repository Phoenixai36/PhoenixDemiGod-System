# Phoenix Hydra Network Validation Script (PowerShell)
# Validates network configuration and connectivity

param(
    [switch]$GenerateReport
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"
$NetworkName = "phoenix-hydra_phoenix-net"

# Function to print colored status messages
function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    
    switch ($Status) {
        "SUCCESS" { Write-Host "✅ $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "❌ $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
        "INFO" { Write-Host "ℹ️  $Message" -ForegroundColor Blue }
    }
}

# Function to validate network configuration
function Test-NetworkConfig {
    Write-Status "INFO" "Validating network configuration..."
    
    # Check if compose file exists
    if (-not (Test-Path $ComposeFile)) {
        Write-Status "ERROR" "Compose file not found: $ComposeFile"
        return $false
    }
    
    $composeContent = Get-Content $ComposeFile -Raw
    
    # Validate network definition in compose file
    if ($composeContent -match "phoenix-net:") {
        Write-Status "SUCCESS" "Network definition found in compose file"
    }
    else {
        Write-Status "ERROR" "Network definition not found in compose file"
        return $false
    }
    
    # Check subnet configuration
    if ($composeContent -match "172\.20\.0\.0/16") {
        Write-Status "SUCCESS" "Subnet configuration is correct (172.20.0.0/16)"
    }
    else {
        Write-Status "WARNING" "Subnet configuration may be incorrect"
    }
    
    # Check gateway configuration
    if ($composeContent -match "172\.20\.0\.1") {
        Write-Status "SUCCESS" "Gateway configuration is correct (172.20.0.1)"
    }
    else {
        Write-Status "WARNING" "Gateway configuration may be incorrect"
    }
    
    return $true
}

# Function to validate network exists
function Test-NetworkExists {
    Write-Status "INFO" "Checking if network exists..."
    
    try {
        $null = & podman network exists $NetworkName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "SUCCESS" "Network '$NetworkName' exists"
            
            # Get network details
            try {
                $networkInfo = & podman network inspect $NetworkName 2>$null | ConvertFrom-Json
                if ($networkInfo) {
                    Write-Status "INFO" "Network details:"
                    if ($networkInfo.subnets) {
                        foreach ($subnet in $networkInfo.subnets) {
                            Write-Host "    Subnet: $($subnet.subnet)" -ForegroundColor Gray
                            Write-Host "    Gateway: $($subnet.gateway)" -ForegroundColor Gray
                        }
                    }
                    Write-Host "    Driver: $($networkInfo.driver)" -ForegroundColor Gray
                }
            }
            catch {
                Write-Status "WARNING" "Could not retrieve network details"
            }
            
            return $true
        }
        else {
            Write-Status "WARNING" "Network '$NetworkName' does not exist (will be created when services start)"
            return $false
        }
    }
    catch {
        Write-Status "WARNING" "Network '$NetworkName' does not exist (will be created when services start)"
        return $false
    }
}

# Function to validate service network assignments
function Test-ServiceNetworks {
    Write-Status "INFO" "Validating service network assignments..."
    
    $services = @("gap-detector", "recurrent-processor", "db", "windmill", "rubik-agent", "nginx", "analysis-engine")
    $validCount = 0
    $composeContent = Get-Content $ComposeFile -Raw
    
    foreach ($service in $services) {
        # Look for service definition and phoenix-net assignment
        if ($composeContent -match "(?s)^\s*$service\s*:.*?networks:\s*-\s*phoenix-net") {
            Write-Status "SUCCESS" "Service '$service' is assigned to phoenix-net"
            $validCount++
        }
        else {
            Write-Status "WARNING" "Service '$service' may not be assigned to phoenix-net"
        }
    }
    
    Write-Status "INFO" "Network assignment validation: $validCount/$($services.Count) services configured"
    return $true
}

# Function to validate DNS prerequisites
function Test-DnsPrerequisites {
    Write-Status "INFO" "Validating DNS prerequisites..."
    
    # Check if aardvark-dns is available (Podman's DNS resolver)
    try {
        $null = Get-Command aardvark-dns -ErrorAction Stop
        Write-Status "SUCCESS" "aardvark-dns is available"
    }
    catch {
        Write-Status "WARNING" "aardvark-dns not found in PATH (may be installed elsewhere)"
    }
    
    # Check if netavark is available (Podman's network backend)
    try {
        $null = Get-Command netavark -ErrorAction Stop
        Write-Status "SUCCESS" "netavark is available"
    }
    catch {
        Write-Status "WARNING" "netavark not found in PATH (may be installed elsewhere)"
    }
    
    return $true
}

# Function to validate port configurations
function Test-PortConfig {
    Write-Status "INFO" "Validating port configurations..."
    
    $expectedPorts = @("8000:8000", "5000:5000", "3000:3000", "8080:8080")
    $foundPorts = 0
    $composeContent = Get-Content $ComposeFile -Raw
    
    foreach ($port in $expectedPorts) {
        if ($composeContent -match [regex]::Escape("`"$port`"")) {
            Write-Status "SUCCESS" "Port mapping '$port' found"
            $foundPorts++
        }
        else {
            Write-Status "WARNING" "Port mapping '$port' not found"
        }
    }
    
    Write-Status "INFO" "Port configuration validation: $foundPorts/$($expectedPorts.Count) expected ports configured"
    return $true
}

# Function to check for network conflicts
function Test-NetworkConflicts {
    Write-Status "INFO" "Checking for network conflicts..."
    
    try {
        # Get all networks and check for subnet conflicts
        $networks = & podman network ls --format "{{.Name}}" 2>$null
        $conflictFound = $false
        
        foreach ($network in $networks) {
            if ($network -ne $NetworkName) {
                try {
                    $networkInfo = & podman network inspect $network 2>$null | ConvertFrom-Json
                    if ($networkInfo.subnets) {
                        foreach ($subnet in $networkInfo.subnets) {
                            if ($subnet.subnet -eq "172.20.0.0/16") {
                                Write-Status "WARNING" "Potential subnet conflict detected with network: $network"
                                $conflictFound = $true
                            }
                        }
                    }
                }
                catch {
                    # Ignore errors inspecting individual networks
                }
            }
        }
        
        if (-not $conflictFound) {
            Write-Status "SUCCESS" "No network conflicts detected"
        }
    }
    catch {
        Write-Status "WARNING" "Could not check for network conflicts"
    }
    
    return $true
}

# Function to validate security settings
function Test-SecuritySettings {
    Write-Status "INFO" "Validating network security settings..."
    
    $composeContent = Get-Content $ComposeFile -Raw
    
    # Check for security_opt settings
    if ($composeContent -match "no-new-privileges:true") {
        Write-Status "SUCCESS" "Security option 'no-new-privileges:true' found"
    }
    else {
        Write-Status "WARNING" "Security option 'no-new-privileges:true' not found"
    }
    
    # Check for user settings (rootless execution)
    if ($composeContent -match "user:") {
        Write-Status "SUCCESS" "User settings found (rootless execution)"
    }
    else {
        Write-Status "WARNING" "User settings not found"
    }
    
    return $true
}

# Function to generate network validation report
function New-ValidationReport {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $reportFile = Join-Path $ScriptDir "network-validation-report.txt"
    
    Write-Status "INFO" "Generating network validation report..."
    
    # Build report content as array
    $reportLines = @()
    $reportLines += "Phoenix Hydra Network Validation Report"
    $reportLines += "Generated: $timestamp"
    $reportLines += ""
    $reportLines += "Network Configuration:"
    $reportLines += "- Compose File: $ComposeFile"
    $reportLines += "- Network Name: $NetworkName"
    $reportLines += "- Subnet: 172.20.0.0/16"
    $reportLines += "- Gateway: 172.20.0.1"
    $reportLines += ""
    $reportLines += "Validation Results:"
    
    # Capture validation results
    $originalPreference = $InformationPreference
    $InformationPreference = "Continue"
    
    $reportLines += ""
    $reportLines += "--- Network Configuration ---"
    $reportLines += (Test-NetworkConfig *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- Network Existence ---"
    $reportLines += (Test-NetworkExists *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- Service Networks ---"
    $reportLines += (Test-ServiceNetworks *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- DNS Prerequisites ---"
    $reportLines += (Test-DnsPrerequisites *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- Port Configuration ---"
    $reportLines += (Test-PortConfig *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- Network Conflicts ---"
    $reportLines += (Test-NetworkConflicts *>&1 | Out-String).Split("`n")
    
    $reportLines += ""
    $reportLines += "--- Security Settings ---"
    $reportLines += (Test-SecuritySettings *>&1 | Out-String).Split("`n")
    
    $InformationPreference = $originalPreference
    
    $reportLines += ""
    $reportLines += "Recommendations:"
    $reportLines += "- Ensure all services are properly configured to use phoenix-net"
    $reportLines += "- Verify DNS resolution between services after starting containers"
    $reportLines += "- Monitor network performance and adjust MTU if needed"
    $reportLines += "- Regularly test network connectivity using test-network.ps1"
    $reportLines += ""
    $reportLines += "For detailed network testing, run: .\test-network.ps1"

    # Join lines and remove ANSI color codes
    $reportContent = ($reportLines -join "`n") -replace '\x1b\[[0-9;]*m', ''
    
    Set-Content -Path $reportFile -Value $reportContent -Encoding UTF8
    Write-Status "SUCCESS" "Network validation report saved to: $reportFile"
}

# Main execution
function Main {
    Write-Host "🔍 Phoenix Hydra Network Validation" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    
    $exitCode = 0
    
    if (-not (Test-NetworkConfig)) { $exitCode = 1 }
    Write-Host ""
    
    Test-NetworkExists | Out-Null  # Don't fail if network doesn't exist yet
    Write-Host ""
    
    if (-not (Test-ServiceNetworks)) { $exitCode = 1 }
    Write-Host ""
    
    Test-DnsPrerequisites | Out-Null  # Don't fail on DNS prerequisites
    Write-Host ""
    
    if (-not (Test-PortConfig)) { $exitCode = 1 }
    Write-Host ""
    
    Test-NetworkConflicts | Out-Null  # Don't fail on conflicts
    Write-Host ""
    
    Test-SecuritySettings | Out-Null  # Don't fail on security settings
    Write-Host ""
    
    if ($GenerateReport) {
        New-ValidationReport
        Write-Host ""
    }
    
    if ($exitCode -eq 0) {
        Write-Status "SUCCESS" "Network validation completed successfully!"
        Write-Host ""
        Write-Status "INFO" "Next steps:"
        Write-Host "  1. Start services: podman-compose -f $ComposeFile up -d" -ForegroundColor Gray
        Write-Host "  2. Test network: .\test-network.ps1" -ForegroundColor Gray
        Write-Host "  3. Verify connectivity between services" -ForegroundColor Gray
    }
    else {
        Write-Status "ERROR" "Network validation completed with warnings/errors"
        Write-Host ""
        Write-Status "INFO" "Please review the issues above and fix them before proceeding"
    }
    
    return $exitCode
}

# Run main function
Main