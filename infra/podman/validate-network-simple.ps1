# Phoenix Hydra Network Validation Script (Simplified PowerShell)
# Validates network configuration and connectivity

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"
$NetworkName = "phoenix-hydra_phoenix-net"

Write-Host "🔍 Phoenix Hydra Network Validation" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if compose file exists
Write-Host "📋 Validating network configuration..." -ForegroundColor Blue
if (Test-Path $ComposeFile) {
    Write-Host "✅ Compose file found: $ComposeFile" -ForegroundColor Green
    
    $composeContent = Get-Content $ComposeFile -Raw
    
    # Check for phoenix-net network definition
    if ($composeContent -match "phoenix-net:") {
        Write-Host "✅ Network definition found in compose file" -ForegroundColor Green
    } else {
        Write-Host "❌ Network definition not found in compose file" -ForegroundColor Red
    }
    
    # Check subnet configuration
    if ($composeContent -match "172\.20\.0\.0/16") {
        Write-Host "✅ Subnet configuration is correct (172.20.0.0/16)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Subnet configuration may be incorrect" -ForegroundColor Yellow
    }
    
    # Check gateway configuration
    if ($composeContent -match "172\.20\.0\.1") {
        Write-Host "✅ Gateway configuration is correct (172.20.0.1)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Gateway configuration may be incorrect" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Compose file not found: $ComposeFile" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if network exists
Write-Host "🌐 Checking network existence..." -ForegroundColor Blue
try {
    $null = & podman network exists $NetworkName 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Network '$NetworkName' exists" -ForegroundColor Green
        
        # Get network details
        try {
            $networkInfo = & podman network inspect $NetworkName 2>$null | ConvertFrom-Json
            if ($networkInfo -and $networkInfo.subnets) {
                foreach ($subnet in $networkInfo.subnets) {
                    Write-Host "  └─ Subnet: $($subnet.subnet)" -ForegroundColor Gray
                    Write-Host "  └─ Gateway: $($subnet.gateway)" -ForegroundColor Gray
                }
            }
        } catch {
            Write-Host "  └─ Could not retrieve network details" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  Network '$NetworkName' does not exist (will be created when services start)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Network '$NetworkName' does not exist (will be created when services start)" -ForegroundColor Yellow
}

Write-Host ""

# Check service network assignments
Write-Host "🔗 Validating service network assignments..." -ForegroundColor Blue
$services = @("gap-detector", "recurrent-processor", "db", "windmill", "rubik-agent", "nginx", "analysis-engine")
$validCount = 0

foreach ($service in $services) {
    if ($composeContent -match "(?s)^\s*$service\s*:.*?networks:\s*-\s*phoenix-net") {
        Write-Host "✅ Service '$service' is assigned to phoenix-net" -ForegroundColor Green
        $validCount++
    } else {
        Write-Host "⚠️  Service '$service' may not be assigned to phoenix-net" -ForegroundColor Yellow
    }
}

Write-Host "📊 Network assignment validation: $validCount/$($services.Count) services configured" -ForegroundColor Blue

Write-Host ""

# Check port configurations
Write-Host "🚪 Validating port configurations..." -ForegroundColor Blue
$expectedPorts = @("8000:8000", "5000:5000", "3000:3000", "8080:8080")
$foundPorts = 0

foreach ($port in $expectedPorts) {
    if ($composeContent -match [regex]::Escape("`"$port`"")) {
        Write-Host "✅ Port mapping '$port' found" -ForegroundColor Green
        $foundPorts++
    } else {
        Write-Host "⚠️  Port mapping '$port' not found" -ForegroundColor Yellow
    }
}

Write-Host "📊 Port configuration validation: $foundPorts/$($expectedPorts.Count) expected ports configured" -ForegroundColor Blue

Write-Host ""

# Check security settings
Write-Host "🔒 Validating security settings..." -ForegroundColor Blue
if ($composeContent -match "no-new-privileges:true") {
    Write-Host "✅ Security option 'no-new-privileges:true' found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Security option 'no-new-privileges:true' not found" -ForegroundColor Yellow
}

if ($composeContent -match "user:") {
    Write-Host "✅ User settings found (rootless execution)" -ForegroundColor Green
} else {
    Write-Host "⚠️  User settings not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Network validation completed!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start services: podman-compose -f $ComposeFile up -d" -ForegroundColor Gray
Write-Host "  2. Test network: .\test-network.ps1" -ForegroundColor Gray
Write-Host "  3. Verify connectivity between services" -ForegroundColor Gray