# Phoenix Hydra Podman Network Testing Script (PowerShell)
# Tests DNS resolution and connectivity between services

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"
$NetworkName = "phoenix-hydra_phoenix-net"

Write-Host "🔍 Phoenix Hydra Network Testing Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Function to check if podman-compose is available
function Test-PodmanCompose {
    try {
        $null = Get-Command podman-compose -ErrorAction Stop
        return $true
    }
    catch {
        Write-Host "❌ Error: podman-compose is not installed" -ForegroundColor Red
        Write-Host "Install with: pip install podman-compose" -ForegroundColor Yellow
        exit 1
    }
}

# Function to check if services are running
function Test-ServicesRunning {
    Write-Host "📋 Checking if services are running..." -ForegroundColor Blue
    
    $services = @("gap-detector", "recurrent-processor", "db", "windmill", "rubik-agent", "nginx", "analysis-engine")
    $runningServices = @()
    
    foreach ($service in $services) {
        try {
            $result = & podman-compose -f $ComposeFile ps --services --filter "status=running" 2>$null
            if ($result -contains $service) {
                $runningServices += $service
                Write-Host "  ✅ $service is running" -ForegroundColor Green
            }
            else {
                Write-Host "  ⚠️  $service is not running" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "  ⚠️  $service is not running" -ForegroundColor Yellow
        }
    }
    
    if ($runningServices.Count -eq 0) {
        Write-Host "❌ No services are running. Start services first with:" -ForegroundColor Red
        Write-Host "   podman-compose -f $ComposeFile up -d" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Found $($runningServices.Count) running services" -ForegroundColor Green
}

# Function to test DNS resolution between services
function Test-DnsResolution {
    Write-Host ""
    Write-Host "🌐 Testing DNS resolution between services..." -ForegroundColor Blue
    Write-Host "=============================================" -ForegroundColor Blue
    
    $testServices = @("db", "windmill", "gap-detector", "recurrent-processor", "rubik-agent", "nginx")
    $testContainer = "gap-detector"
    
    # Check if test container is running
    try {
        $result = & podman-compose -f $ComposeFile ps --services --filter "status=running" 2>$null
        if ($result -notcontains $testContainer) {
            Write-Host "⚠️  Test container '$testContainer' is not running. Skipping DNS tests." -ForegroundColor Yellow
            return
        }
    }
    catch {
        Write-Host "⚠️  Test container '$testContainer' is not running. Skipping DNS tests." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Using '$testContainer' as test container..." -ForegroundColor Gray
    
    foreach ($service in $testServices) {
        if ($service -eq $testContainer) {
            continue  # Skip self-test
        }
        
        Write-Host -NoNewline "  Testing DNS resolution for '$service'... "
        
        try {
            # Test DNS resolution using getent hosts
            $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "getent hosts $service > /dev/null 2>&1"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Resolved" -ForegroundColor Green
                
                # Get the IP address
                try {
                    $ip = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "getent hosts $service | awk '{print `$1}'" 2>$null
                    if ($ip -and $ip.Trim()) {
                        Write-Host "    └─ IP: $($ip.Trim())" -ForegroundColor Gray
                    }
                }
                catch {
                    # IP retrieval failed, but DNS resolution worked
                }
            }
            else {
                Write-Host "❌ Failed" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
}

# Function to test network connectivity
function Test-NetworkConnectivity {
    Write-Host ""
    Write-Host "🔗 Testing network connectivity..." -ForegroundColor Blue
    Write-Host "=================================" -ForegroundColor Blue
    
    $testContainer = "gap-detector"
    
    # Check if test container is running
    try {
        $result = & podman-compose -f $ComposeFile ps --services --filter "status=running" 2>$null
        if ($result -notcontains $testContainer) {
            Write-Host "⚠️  Test container '$testContainer' is not running. Skipping connectivity tests." -ForegroundColor Yellow
            return
        }
    }
    catch {
        Write-Host "⚠️  Test container '$testContainer' is not running. Skipping connectivity tests." -ForegroundColor Yellow
        return
    }
    
    # Test connectivity to database
    Write-Host -NoNewline "  Testing connection to database (db:5432)... "
    try {
        $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "timeout 5 bash -c '</dev/tcp/db/5432' > /dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Connected" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed" -ForegroundColor Red
    }
    
    # Test connectivity to Windmill
    Write-Host -NoNewline "  Testing connection to Windmill (windmill:3000)... "
    try {
        $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "timeout 5 bash -c '</dev/tcp/windmill/3000' > /dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Connected" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed" -ForegroundColor Red
    }
    
    # Test connectivity to nginx
    Write-Host -NoNewline "  Testing connection to nginx (nginx:8080)... "
    try {
        $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "timeout 5 bash -c '</dev/tcp/nginx/8080' > /dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Connected" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed" -ForegroundColor Red
    }
}

# Function to display network information
function Show-NetworkInfo {
    Write-Host ""
    Write-Host "📊 Network Information" -ForegroundColor Blue
    Write-Host "=====================" -ForegroundColor Blue
    
    try {
        # Check if network exists
        $networkExists = & podman network exists $NetworkName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Network: $NetworkName" -ForegroundColor Gray
            
            # Get network details
            $networkInfo = & podman network inspect $NetworkName 2>$null | ConvertFrom-Json
            if ($networkInfo) {
                if ($networkInfo.subnets) {
                    foreach ($subnet in $networkInfo.subnets) {
                        Write-Host "  Subnet: $($subnet.subnet)" -ForegroundColor Gray
                        Write-Host "  Gateway: $($subnet.gateway)" -ForegroundColor Gray
                    }
                }
                Write-Host "  Driver: $($networkInfo.driver)" -ForegroundColor Gray
                
                Write-Host ""
                Write-Host "Connected containers:" -ForegroundColor Gray
                if ($networkInfo.containers) {
                    foreach ($container in $networkInfo.containers.PSObject.Properties) {
                        $containerInfo = $container.Value
                        Write-Host "  - $($containerInfo.name) ($($containerInfo.ipv4_address))" -ForegroundColor Gray
                    }
                }
            }
        }
        else {
            Write-Host "⚠️  Network '$NetworkName' not found" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Could not retrieve network information" -ForegroundColor Yellow
    }
}

# Function to test external connectivity
function Test-ExternalConnectivity {
    Write-Host ""
    Write-Host "🌍 Testing external connectivity..." -ForegroundColor Blue
    Write-Host "==================================" -ForegroundColor Blue
    
    $testContainer = "gap-detector"
    
    # Check if test container is running
    try {
        $result = & podman-compose -f $ComposeFile ps --services --filter "status=running" 2>$null
        if ($result -notcontains $testContainer) {
            Write-Host "⚠️  Test container '$testContainer' is not running. Skipping external connectivity tests." -ForegroundColor Yellow
            return
        }
    }
    catch {
        Write-Host "⚠️  Test container '$testContainer' is not running. Skipping external connectivity tests." -ForegroundColor Yellow
        return
    }
    
    # Test external DNS resolution
    Write-Host -NoNewline "  Testing external DNS resolution (google.com)... "
    try {
        $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "nslookup google.com > /dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Working" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed" -ForegroundColor Red
    }
    
    # Test external connectivity
    Write-Host -NoNewline "  Testing external connectivity (8.8.8.8:53)... "
    try {
        $null = & podman-compose -f $ComposeFile exec -T $testContainer sh -c "timeout 5 bash -c '</dev/tcp/8.8.8.8/53' > /dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Working" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Failed" -ForegroundColor Red
    }
}

# Main execution
function Main {
    Test-PodmanCompose
    Test-ServicesRunning
    Show-NetworkInfo
    Test-DnsResolution
    Test-NetworkConnectivity
    Test-ExternalConnectivity
    
    Write-Host ""
    Write-Host "🎉 Network testing completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Tips:" -ForegroundColor Yellow
    Write-Host "  - If DNS resolution fails, ensure services are running and healthy" -ForegroundColor Gray
    Write-Host "  - If connectivity fails, check firewall settings and network configuration" -ForegroundColor Gray
    Write-Host "  - Use 'podman network ls' to list all networks" -ForegroundColor Gray
    Write-Host "  - Use 'podman network inspect $NetworkName' for detailed network info" -ForegroundColor Gray
}

# Run main function
Main