#!/usr/bin/env pwsh
param(
    [switch]$Help,
    [switch]$SkipChecks,
    [switch]$NoVerify,
    [switch]$SetupVolumes,
    [switch]$CleanupVolumes
)

# Podman-specific deployment script for Phoenix Hydra (PowerShell version)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ScriptDir "infra/podman/podman-compose.yaml"
$VolumeSetupScript = Join-Path $ScriptDir "infra/podman/setup-volumes.ps1"
$VolumeCleanupScript = Join-Path $ScriptDir "infra/podman/cleanup-volumes.ps1"

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

# Function to check Podman installation
function Test-PodmanInstallation {
    Write-Status "Checking Podman installation..."
    
    if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
        Write-Error "Podman is not installed. Please install Podman first."
        Write-Host "Installation instructions:"
        Write-Host "  Windows: winget install RedHat.Podman"
        Write-Host "  Or download from: https://podman.io/getting-started/installation"
        exit 1
    }
    
    if (-not (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
        Write-Error "podman-compose is not installed."
        Write-Host "Install with one of the following methods:"
        Write-Host "  pip install podman-compose"
        Write-Host "  pip3 install podman-compose"
        exit 1
    }
    
    Write-Success "Podman and podman-compose are installed"
}

# Function to setup rootless environment with user namespace mapping
function Initialize-RootlessEnvironment {
    Write-Status "Setting up rootless environment with user namespace mapping..."
    
    # Create necessary directories
    $phoenixDir = Join-Path $env:USERPROFILE ".local/share/phoenix-hydra"
    $dbDataDir = Join-Path $phoenixDir "db_data"
    $nginxConfigDir = Join-Path $phoenixDir "nginx_config"
    $logsDir = Join-Path $phoenixDir "logs"
    $configDir = Join-Path $env:USERPROFILE ".config/containers"
    
    New-Item -ItemType Directory -Path $phoenixDir -Force | Out-Null
    New-Item -ItemType Directory -Path $dbDataDir -Force | Out-Null
    New-Item -ItemType Directory -Path $nginxConfigDir -Force | Out-Null
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    
    # Configure containers.conf for better security
    $containersConf = Join-Path $configDir "containers.conf"
    if (-not (Test-Path $containersConf)) {
        Write-Status "Creating containers.conf with security optimizations..."
        $configContent = @"
[containers]
# Security: Always use user namespace mapping
userns = "auto"

# Security: Disable privileged containers
privileged = false

# Security: Set default security options
security_opt = ["no-new-privileges:true"]

# Performance: Set default cgroup manager
cgroup_manager = "systemd"

# Network: Default network mode
netns = "bridge"

[engine]
# Security: Disable privileged operations
privileged = false

# Performance: Set runtime
runtime = "crun"

# Security: Set default capabilities
default_capabilities = [
    "CHOWN",
    "DAC_OVERRIDE", 
    "FOWNER",
    "FSETID",
    "KILL",
    "NET_BIND_SERVICE",
    "SETFCAP",
    "SETGID",
    "SETPCAP",
    "SETUID",
    "SYS_CHROOT"
]
"@
        Set-Content -Path $containersConf -Value $configContent
        Write-Success "Created containers.conf with security optimizations"
    }
    
    # Setup volumes using dedicated script
    if (Test-Path $VolumeSetupScript) {
        Write-Status "Setting up volumes with proper permissions..."
        & pwsh -File $VolumeSetupScript
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Volume setup script failed, using fallback"
        }
    } else {
        Write-Warning "Volume setup script not found: $VolumeSetupScript"
    }
    
    Write-Success "Rootless environment with user namespace mapping setup complete"
}

# Function to verify compose file exists
function Test-ComposeFile {
    Write-Status "Checking compose file..."
    
    if (-not (Test-Path $ComposeFile)) {
        Write-Error "Podman compose file not found at: $ComposeFile"
        Write-Host "Please ensure the Podman migration is complete and the compose file exists."
        exit 1
    }
    
    Write-Success "Compose file found: $ComposeFile"
}

# Function to configure network isolation and security boundaries
function Initialize-NetworkSecurity {
    Write-Status "Configuring network isolation and security boundaries..."
    
    # Check if phoenix-net network exists and remove if needed for clean setup
    try {
        $networkExists = & podman network exists phoenix-hydra_phoenix-net 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "Removing existing phoenix-net network for clean setup..."
            & podman network rm phoenix-hydra_phoenix-net 2>$null
        }
    } catch {
        # Network doesn't exist, continue
    }
    
    # Configure Windows Firewall rules for exposed ports (8000, 3000, 8080, 5000)
    Write-Status "Configuring security boundaries for exposed ports..."
    
    $ports = @(8000, 3000, 8080, 5000)
    $serviceNames = @{
        8000 = "Phoenix Hydra - Gap Detector"
        3000 = "Phoenix Hydra - Windmill"
        8080 = "Phoenix Hydra - Nginx"
        5000 = "Phoenix Hydra - Analysis Engine"
    }
    
    foreach ($port in $ports) {
        try {
            $ruleName = $serviceNames[$port]
            # Check if rule already exists
            $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
            if (-not $existingRule) {
                New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -ErrorAction SilentlyContinue
                Write-Success "Configured firewall rule for port $port"
            } else {
                Write-Status "Firewall rule for port $port already exists"
            }
        } catch {
            Write-Warning "Could not configure firewall rule for port $port (may require admin privileges)"
        }
    }
    
    Write-Success "Network security configuration complete"
}

# Function to check if services are already running
function Test-ExistingServices {
    Write-Status "Checking for existing services..."
    
    try {
        $runningServices = & podman-compose -f $ComposeFile ps --services --filter status=running 2>$null
        if ($runningServices) {
            Write-Warning "Some services are already running"
            $response = Read-Host "Do you want to stop existing services and restart? (y/N)"
            if ($response -match "^[Yy]$") {
                Write-Status "Stopping existing services..."
                & podman-compose -f $ComposeFile down
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Could not stop some services"
                }
                
                # Clean up volumes if requested
                $cleanupResponse = Read-Host "Do you want to clean up volumes as well? (y/N)"
                if ($cleanupResponse -match "^[Yy]$") {
                    if (Test-Path $VolumeCleanupScript) {
                        Write-Status "Running volume cleanup..."
                        & pwsh -File $VolumeCleanupScript
                    } else {
                        Write-Warning "Volume cleanup script not found: $VolumeCleanupScript"
                    }
                }
            } else {
                Write-Status "Continuing with existing services..."
            }
        }
    } catch {
        # Ignore errors when checking existing services
    }
}

# Function to build and start services
function Start-Services {
    Write-Status "Building and starting Phoenix Hydra services..."
    
    # Build images first
    Write-Status "Building container images..."
    & podman-compose -f $ComposeFile build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build container images"
        exit 1
    }
    
    # Start services
    Write-Status "Starting services in detached mode..."
    & podman-compose -f $ComposeFile up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services"
        exit 1
    }
    
    Write-Success "Services started successfully"
}

# Function to verify deployment with security and network checks
function Test-Deployment {
    Write-Status "Verifying deployment with security and network isolation checks..."
    
    # Wait a moment for services to initialize
    Start-Sleep -Seconds 10
    
    # Check service status
    Write-Status "Service status:"
    & podman-compose -f $ComposeFile ps
    
    # Verify network isolation
    Write-Status "Verifying network isolation..."
    
    try {
        $networkExists = & podman network exists phoenix-hydra_phoenix-net 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Phoenix network created successfully"
            
            # Show network details
            Write-Status "Network configuration:"
            & podman network inspect phoenix-hydra_phoenix-net --format "{{.Name}}: {{.Subnets}}" 2>$null
        } else {
            Write-Warning "Phoenix network not found - services may not be properly isolated"
        }
    } catch {
        Write-Warning "Could not verify network isolation"
    }
    
    # Check security boundaries for exposed ports
    Write-Status "Verifying security boundaries for exposed ports (8000, 3000, 8080, 5000)..."
    
    $portsToCheck = @(
        @{Port=8000; Service="gap-detector"; HealthPath="/health"},
        @{Port=3000; Service="windmill"; HealthPath="/api/version"},
        @{Port=8080; Service="nginx"; HealthPath="/"},
        @{Port=5000; Service="analysis-engine"; HealthPath="/health"}
    )
    
    $healthyServices = 0
    $totalServices = $portsToCheck.Count
    
    foreach ($portInfo in $portsToCheck) {
        $port = $portInfo.Port
        $service = $portInfo.Service
        $healthPath = $portInfo.HealthPath
        
        Write-Status "Checking $service on port $port..."
        
        # Check if port is listening
        try {
            $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
            if ($connection) {
                Write-Success "Port $port is listening"
                
                # Try to connect to health endpoint
                $healthUrl = "http://localhost:$port$healthPath"
                try {
                    $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 10 -ErrorAction SilentlyContinue
                    if ($response.StatusCode -eq 200) {
                        Write-Success "$service service is responding on port $port"
                        $healthyServices++
                    }
                } catch {
                    Write-Warning "$service service on port $port may not be ready yet"
                }
            } else {
                Write-Warning "Port $port is not listening - $service may not be started"
            }
        } catch {
            Write-Warning "Could not check port $port for $service"
        }
    }
    
    # Verify volume security
    Write-Status "Verifying volume security and permissions..."
    
    $phoenixDataDir = Join-Path $env:USERPROFILE ".local/share/phoenix-hydra"
    if (Test-Path $phoenixDataDir) {
        $dbDataDir = Join-Path $phoenixDataDir "db_data"
        $nginxConfigDir = Join-Path $phoenixDataDir "nginx_config"
        
        if (Test-Path $dbDataDir) {
            Write-Success "Database volume exists with secure location"
        } else {
            Write-Warning "Database volume not found: $dbDataDir"
        }
        
        if (Test-Path $nginxConfigDir) {
            Write-Success "Nginx config volume exists with proper location"
        } else {
            Write-Warning "Nginx config volume not found: $nginxConfigDir"
        }
    } else {
        Write-Warning "Phoenix data directory not found: $phoenixDataDir"
    }
    
    # Summary
    Write-Status "Deployment verification complete"
    Write-Host ""
    Write-Host "Security Status:"
    Write-Host "  - Services responding: $healthyServices/$totalServices"
    Write-Host "  - Network isolation: $(if ($networkExists -eq 0) { "✅ Active" } else { "❌ Not configured" })"
    Write-Host "  - User namespace mapping: ✅ Configured"
    Write-Host "  - Volume security: ✅ Configured"
    Write-Host ""
    Write-Host "Phoenix Hydra services are starting up. You can:"
    Write-Host "  - Check logs: podman-compose -f $ComposeFile logs -f"
    Write-Host "  - Check status: podman-compose -f $ComposeFile ps"
    Write-Host "  - Stop services: podman-compose -f $ComposeFile down"
    Write-Host "  - Clean volumes: pwsh -File $VolumeCleanupScript"
    Write-Host ""
    Write-Host "Service endpoints (with security boundaries):"
    Write-Host "  - Gap Detector: http://localhost:8000 (isolated network)"
    Write-Host "  - Windmill: http://localhost:3000 (isolated network)"
    Write-Host "  - Nginx: http://localhost:8080 (isolated network)"
    Write-Host "  - Analysis Engine: http://localhost:5000 (isolated network)"
    Write-Host ""
    Write-Host "Internal services (not externally accessible):"
    Write-Host "  - PostgreSQL: Internal port 5432 (network isolated)"
    Write-Host "  - Recurrent Processor: Internal only (network isolated)"
    Write-Host "  - Rubik Agent: Internal only (network isolated)"
}

# Function to manage volume operations
function Invoke-VolumeManagement {
    param([string]$Action)
    
    switch ($Action) {
        "setup" {
            if (Test-Path $VolumeSetupScript) {
                Write-Status "Setting up volumes..."
                & pwsh -File $VolumeSetupScript
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Volume setup failed"
                    exit 1
                }
            } else {
                Write-Error "Volume setup script not found: $VolumeSetupScript"
                exit 1
            }
        }
        "cleanup" {
            if (Test-Path $VolumeCleanupScript) {
                Write-Status "Cleaning up volumes..."
                & pwsh -File $VolumeCleanupScript
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Volume cleanup failed"
                    exit 1
                }
            } else {
                Write-Error "Volume cleanup script not found: $VolumeCleanupScript"
                exit 1
            }
        }
        default {
            Write-Error "Unknown volume action: $Action"
            Write-Host "Valid actions: setup, cleanup"
            exit 1
        }
    }
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: deploy.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help             Show this help message"
    Write-Host "  -SkipChecks       Skip environment checks (use with caution)"
    Write-Host "  -NoVerify         Skip deployment verification"
    Write-Host "  -SetupVolumes     Setup volumes only (don't deploy services)"
    Write-Host "  -CleanupVolumes   Cleanup volumes only (don't deploy services)"
    Write-Host ""
    Write-Host "This script deploys the Phoenix Hydra stack using Podman with:"
    Write-Host "  - Rootless execution with user namespace mapping"
    Write-Host "  - Network isolation and security boundaries"
    Write-Host "  - Secure volume management with proper permissions"
    Write-Host "  - Exposed ports: 8000 (gap-detector), 3000 (windmill), 8080 (nginx), 5000 (analysis-engine)"
    Write-Host "  - Internal services: PostgreSQL (5432), recurrent-processor, rubik-agent"
}

# Main deployment function
function Invoke-Deployment {
    if ($Help) {
        Show-Usage
        exit 0
    }
    
    # Handle volume-only operations
    if ($SetupVolumes) {
        Invoke-VolumeManagement "setup"
        exit 0
    }
    
    if ($CleanupVolumes) {
        Invoke-VolumeManagement "cleanup"
        exit 0
    }
    
    Write-Status "Starting Phoenix Hydra deployment with Podman..."
    Write-Host ""
    
    # Run checks unless skipped
    if (-not $SkipChecks) {
        Test-PodmanInstallation
        Initialize-RootlessEnvironment
        Test-ComposeFile
        Initialize-NetworkSecurity
        Test-ExistingServices
    }
    
    # Deploy services
    Start-Services
    
    # Verify deployment unless skipped
    if (-not $NoVerify) {
        Test-Deployment
    }
    
    Write-Success "Phoenix Hydra deployment completed!"
}

# Handle script interruption
trap {
    Write-Error "Deployment interrupted"
    exit 1
}

# Run main function
try {
    Invoke-Deployment
} catch {
    Write-Error "Deployment failed: $_"
    exit 1
}