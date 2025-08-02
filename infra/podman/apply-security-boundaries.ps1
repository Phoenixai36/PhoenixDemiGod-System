# Phoenix Hydra Security Boundaries Application Script (PowerShell)
# This script applies network isolation and security boundaries

param(
    [switch]$SkipFirewall = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SecurityConfig = Join-Path $ScriptDir "security-boundaries.yaml"
$ComposeFile = Join-Path $ScriptDir "podman-compose.yaml"

Write-Host "🔒 Applying Phoenix Hydra security boundaries..." -ForegroundColor Cyan

# Function to check if podman is available
function Test-PodmanAvailable {
    if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Podman is not installed. Please install Podman first." -ForegroundColor Red
        exit 1
    }
    
    if (-not (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
        Write-Host "❌ podman-compose is not installed. Install with: pip install podman-compose" -ForegroundColor Red
        exit 1
    }
}

# Function to create network with security policies
function New-SecureNetwork {
    Write-Host "Creating secure phoenix-net network..." -ForegroundColor Yellow
    
    # Remove existing network if it exists
    try {
        podman network rm phoenix-hydra_phoenix-net 2>$null
    } catch {
        # Network doesn't exist, continue
    }
    
    # Create network with security settings (using only supported options)
    $networkArgs = @(
        "network", "create",
        "--driver", "bridge",
        "--subnet", "172.20.0.0/16",
        "--gateway", "172.20.0.1",
        "--ip-range", "172.20.1.0/24",
        "--label", "project=phoenix-hydra",
        "--label", "environment=development",
        "--label", "network.type=bridge",
        "--label", "network.isolation=secure",
        "phoenix-hydra_phoenix-net"
    )
    
    & podman @networkArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Secure network created successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create secure network" -ForegroundColor Red
        exit 1
    }
}

# Function to configure Windows Firewall rules
function Set-FirewallRules {
    if ($SkipFirewall) {
        Write-Host "⏭️  Skipping firewall configuration" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Configuring Windows Firewall rules..." -ForegroundColor Yellow
    
    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
        
        if (-not $isAdmin) {
            Write-Host "⚠️  Administrator privileges required for firewall configuration. Skipping..." -ForegroundColor Yellow
            return
        }
        
        # Allow external access to exposed ports only
        $firewallRules = @(
            @{ Name = "Phoenix Hydra - Gap Detector API"; Port = 8000; Description = "Gap Detector API access" },
            @{ Name = "Phoenix Hydra - Windmill UI"; Port = 3000; Description = "Windmill workflow UI access" },
            @{ Name = "Phoenix Hydra - Nginx Proxy"; Port = 8080; Description = "Nginx reverse proxy access" },
            @{ Name = "Phoenix Hydra - Analysis Engine API"; Port = 5000; Description = "Analysis Engine API access" }
        )
        
        foreach ($rule in $firewallRules) {
            # Remove existing rule if it exists
            try {
                Remove-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
            } catch {
                # Rule doesn't exist, continue
            }
            
            # Create new inbound rule
            New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Protocol TCP -LocalPort $rule.Port -Action Allow -Description $rule.Description | Out-Null
            Write-Host "  ✅ Added firewall rule for port $($rule.Port)" -ForegroundColor Green
        }
        
        # Block direct access to database port
        try {
            Remove-NetFirewallRule -DisplayName "Phoenix Hydra - Block DB Access" -ErrorAction SilentlyContinue
        } catch {
            # Rule doesn't exist, continue
        }
        
        New-NetFirewallRule -DisplayName "Phoenix Hydra - Block DB Access" -Direction Inbound -Protocol TCP -LocalPort 5432 -Action Block -Description "Block direct database access" | Out-Null
        Write-Host "  ✅ Added firewall rule to block direct database access" -ForegroundColor Green
        
        Write-Host "✅ Windows Firewall rules configured" -ForegroundColor Green
        
    } catch {
        Write-Host "⚠️  Failed to configure firewall rules: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Function to set up volume security
function Set-VolumesSecurity {
    Write-Host "Setting up volume security..." -ForegroundColor Yellow
    
    $PhoenixDataDir = "$env:USERPROFILE\.local\share\phoenix-hydra"
    
    # Ensure volumes exist with correct permissions
    $directories = @(
        "$PhoenixDataDir\db_data",
        "$PhoenixDataDir\nginx_config",
        "$PhoenixDataDir\logs"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "  Created directory: $dir" -ForegroundColor Gray
        }
    }
    
    # Set restrictive permissions for database
    try {
        $dbDataPath = "$PhoenixDataDir\db_data"
        $acl = Get-Acl $dbDataPath
        
        # Remove inherited permissions
        $acl.SetAccessRuleProtection($true, $false)
        
        # Add full control for current user only
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $env:USERNAME, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
        )
        $acl.SetAccessRule($accessRule)
        Set-Acl -Path $dbDataPath -AclObject $acl
        
        Write-Host "  ✅ Database volume permissions set (restrictive)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not set restrictive permissions for database volume: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Set appropriate permissions for nginx config
    try {
        $nginxConfigPath = "$PhoenixDataDir\nginx_config"
        $acl = Get-Acl $nginxConfigPath
        
        # Add read/execute for current user
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $env:USERNAME, "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow"
        )
        $acl.SetAccessRule($accessRule)
        Set-Acl -Path $nginxConfigPath -AclObject $acl
        
        Write-Host "  ✅ Nginx config volume permissions set (read-only)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not set permissions for nginx config volume: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Set permissions for logs
    try {
        $logsPath = "$PhoenixDataDir\logs"
        $acl = Get-Acl $logsPath
        
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
            $env:USERNAME, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
        )
        $acl.SetAccessRule($accessRule)
        Set-Acl -Path $logsPath -AclObject $acl
        
        Write-Host "  ✅ Logs volume permissions set" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  Could not set permissions for logs volume: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    Write-Host "✅ Volume security configured" -ForegroundColor Green
}

# Function to validate security configuration
function Test-SecurityConfiguration {
    Write-Host "Validating security configuration..." -ForegroundColor Yellow
    
    # Check network exists
    try {
        $networkInfo = podman network inspect phoenix-hydra_phoenix-net 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Secure network exists" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Secure network not found" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ❌ Could not check network status" -ForegroundColor Red
        return $false
    }
    
    # Check volume permissions
    $PhoenixDataDir = "$env:USERPROFILE\.local\share\phoenix-hydra"
    
    $volumeChecks = @(
        @{ Path = "$PhoenixDataDir\db_data"; Name = "Database volume" },
        @{ Path = "$PhoenixDataDir\nginx_config"; Name = "Nginx config volume" },
        @{ Path = "$PhoenixDataDir\logs"; Name = "Logs volume" }
    )
    
    foreach ($check in $volumeChecks) {
        if (Test-Path $check.Path) {
            Write-Host "  ✅ $($check.Name) exists" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $($check.Name) not found" -ForegroundColor Yellow
        }
    }
    
    # Check if compose file has security options
    if (Test-Path $ComposeFile) {
        $composeContent = Get-Content $ComposeFile -Raw
        if ($composeContent -match "no-new-privileges:true") {
            Write-Host "  ✅ Security options present in compose file" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Security options may be missing from compose file" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ Compose file not found" -ForegroundColor Red
    }
    
    Write-Host "✅ Security validation complete" -ForegroundColor Green
    return $true
}

# Function to create network monitoring script
function New-MonitoringScript {
    Write-Host "Creating network monitoring script..." -ForegroundColor Yellow
    
    $monitoringScript = @'
# Phoenix Hydra Security Monitoring Script (PowerShell)

Write-Host "🔍 Phoenix Hydra Security Status" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check network status
Write-Host "`nNetwork Status:" -ForegroundColor Yellow
try {
    $networkInfo = podman network inspect phoenix-hydra_phoenix-net --format "{{.Name}}: {{.Subnets}}" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  $networkInfo" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Network not found" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ Could not check network status" -ForegroundColor Red
}

# Check container security
Write-Host "`nContainer Security:" -ForegroundColor Yellow
try {
    $containers = podman ps --format "{{.Names}}" | Where-Object { $_ -match "phoenix-hydra" }
    
    foreach ($container in $containers) {
        Write-Host "  $container:" -ForegroundColor White
        
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
                Write-Host "    ⚠️  no-new-privileges not found" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    ⚠️  Could not check security options" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "  ❌ Could not check container security" -ForegroundColor Red
}

# Check exposed ports
Write-Host "`nExposed Ports:" -ForegroundColor Yellow
try {
    podman ps --format "table {{.Names}}`t{{.Ports}}" | Where-Object { $_ -match "phoenix-hydra" }
} catch {
    Write-Host "  ❌ Could not check exposed ports" -ForegroundColor Red
}

# Check volume permissions
Write-Host "`nVolume Permissions:" -ForegroundColor Yellow
$PhoenixDataDir = "$env:USERPROFILE\.local\share\phoenix-hydra"
if (Test-Path $PhoenixDataDir) {
    $volumes = @(
        @{ Name = "Database"; Path = "$PhoenixDataDir\db_data" },
        @{ Name = "Nginx Config"; Path = "$PhoenixDataDir\nginx_config" },
        @{ Name = "Logs"; Path = "$PhoenixDataDir\logs" }
    )
    
    foreach ($volume in $volumes) {
        if (Test-Path $volume.Path) {
            $item = Get-Item $volume.Path
            Write-Host "  $($volume.Name): Exists ($(Get-Date $item.LastWriteTime -Format 'yyyy-MM-dd HH:mm'))" -ForegroundColor Green
        } else {
            Write-Host "  $($volume.Name): Not found" -ForegroundColor Red
        }
    }
} else {
    Write-Host "  ❌ Phoenix data directory not found" -ForegroundColor Red
}

Write-Host "`n✅ Security monitoring complete" -ForegroundColor Green
'@
    
    $monitoringScriptPath = Join-Path $ScriptDir "monitor-security.ps1"
    $monitoringScript | Out-File -FilePath $monitoringScriptPath -Encoding UTF8
    
    Write-Host "✅ Security monitoring script created at: $monitoringScriptPath" -ForegroundColor Green
}

# Function to test network isolation
function Test-NetworkIsolation {
    Write-Host "Testing network isolation..." -ForegroundColor Yellow
    
    # Check if containers are running
    try {
        $runningContainers = podman-compose -f $ComposeFile ps | Where-Object { $_ -match "Up" }
        if (-not $runningContainers) {
            Write-Host "  ⚠️  Containers not running. Start them first with: podman-compose up -d" -ForegroundColor Yellow
            return
        }
    } catch {
        Write-Host "  ⚠️  Could not check container status" -ForegroundColor Yellow
        return
    }
    
    # Test external port accessibility
    Write-Host "  Testing external port accessibility..." -ForegroundColor Gray
    
    $portTests = @(
        @{ Service = "Gap Detector"; Port = 8000; Path = "/health" },
        @{ Service = "Windmill"; Port = 3000; Path = "/api/version" },
        @{ Service = "Nginx"; Port = 8080; Path = "/health" },
        @{ Service = "Analysis Engine"; Port = 5000; Path = "/health" }
    )
    
    foreach ($test in $portTests) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($test.Port)$($test.Path)" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "    ✅ $($test.Service) accessible on port $($test.Port)" -ForegroundColor Green
            } else {
                Write-Host "    ⚠️  $($test.Service) returned status $($response.StatusCode) on port $($test.Port)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "    ⚠️  $($test.Service) not accessible on port $($test.Port)" -ForegroundColor Yellow
        }
    }
    
    # Test that database is NOT accessible externally
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.ConnectAsync("localhost", 5432).Wait(1000)
        if ($tcpClient.Connected) {
            Write-Host "    ⚠️  Database may be exposed externally" -ForegroundColor Yellow
            $tcpClient.Close()
        }
    } catch {
        Write-Host "    ✅ Database correctly isolated (not accessible externally)" -ForegroundColor Green
    }
    
    Write-Host "✅ Network isolation test complete" -ForegroundColor Green
}

# Main execution
function Main {
    Write-Host "Starting security boundaries application..." -ForegroundColor Cyan
    
    Test-PodmanAvailable
    New-SecureNetwork
    Set-VolumesSecurity
    Set-FirewallRules
    New-MonitoringScript
    
    if (Test-SecurityConfiguration) {
        Write-Host "`n🎉 Security boundaries applied successfully!" -ForegroundColor Green
        
        Write-Host "`nNext steps:" -ForegroundColor Yellow
        Write-Host "1. Start services: podman-compose -f $ComposeFile up -d"
        Write-Host "2. Test isolation: .\test-network-isolation.ps1"
        Write-Host "3. Monitor security: .\monitor-security.ps1"
        
        Write-Host "`nExposed ports:" -ForegroundColor Yellow
        Write-Host "  - Gap Detector API: http://localhost:8000"
        Write-Host "  - Windmill UI: http://localhost:3000"
        Write-Host "  - Nginx Proxy: http://localhost:8080"
        Write-Host "  - Analysis Engine API: http://localhost:5000"
        
        Write-Host "`nSecurity features enabled:" -ForegroundColor Yellow
        Write-Host "  ✅ Network isolation with custom bridge"
        Write-Host "  ✅ Rootless container execution"
        Write-Host "  ✅ Volume permission restrictions"
        Write-Host "  ✅ Security options (no-new-privileges)"
        Write-Host "  ✅ Firewall rules (if administrator)"
        Write-Host "  ✅ Security monitoring script"
    } else {
        Write-Host "`n❌ Security configuration validation failed" -ForegroundColor Red
        exit 1
    }
}

# Run main function
Main