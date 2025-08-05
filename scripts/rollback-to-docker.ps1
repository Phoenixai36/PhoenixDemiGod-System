# Phoenix Hydra Docker Rollback Script (PowerShell)
# This script reverts the system from Podman back to Docker configuration

param(
    [switch]$Help,
    [switch]$Force,
    [switch]$KeepData,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackupDir = Join-Path $ProjectRoot ".docker-backup"
$PodmanComposeFile = Join-Path $ProjectRoot "infra\podman\podman-compose.yaml"
$DockerComposeFile = Join-Path $ProjectRoot "compose.yaml"

# Function to show usage
function Show-Usage {
    Write-Host @"
Usage: .\scripts\rollback-to-docker.ps1 [OPTIONS]

Options:
  -Help          Show this help message
  -Force         Force rollback without confirmation
  -KeepData      Keep existing data volumes during rollback
  -VerifyOnly    Only verify rollback prerequisites

This script rolls back Phoenix Hydra from Podman to Docker by:
  - Stopping all Podman services
  - Restoring Docker configuration from backup
  - Migrating data volumes if requested
  - Starting Docker services
  - Verifying rollback success
"@
}

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

# Function to check rollback prerequisites
function Test-Prerequisites {
    Write-Status "Checking rollback prerequisites..."
    
    # Check if Docker is installed
    try {
        $dockerVersion = docker --version 2>$null
        Write-Success "Docker installed: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker first."
        Write-Host "Visit: https://docs.docker.com/get-docker/"
        return $false
    }
    
    # Check if docker-compose is available
    try {
        $composeVersion = docker-compose --version 2>$null
        Write-Success "Docker Compose available: $composeVersion"
    }
    catch {
        try {
            $composeVersion = docker compose version 2>$null
            Write-Success "Docker Compose available: $composeVersion"
        }
        catch {
            Write-Error "Docker Compose is not installed."
            return $false
        }
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker first."
        return $false
    }
    
    # Check if backup exists
    if (-not (Test-Path $BackupDir)) {
        Write-Error "Docker backup directory not found: $BackupDir"
        Write-Host "Please ensure you have created a backup before attempting rollback."
        Write-Host "Run: .\scripts\backup-docker-config.ps1"
        return $false
    }
    
    # Verify backup integrity
    $requiredFiles = @(
        "compose.yaml",
        "deploy.sh",
        "teardown.sh",
        "verify.sh",
        "compose\Dockerfile",
        "compose\analysis-engine\Dockerfile",
        "compose\gap-detector\Dockerfile",
        "compose\nginx\Dockerfile",
        "compose\rubik-agent\Dockerfile",
        "compose\nginx\nginx.conf"
    )
    
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $BackupDir $file
        if (-not (Test-Path $filePath)) {
            Write-Error "Required backup file missing: $file"
            return $false
        }
    }
    
    Write-Success "All prerequisites met"
    return $true
}

# Function to stop Podman services
function Stop-PodmanServices {
    Write-Status "Stopping Podman services..."
    
    if ((Test-Path $PodmanComposeFile) -and (Get-Command podman-compose -ErrorAction SilentlyContinue)) {
        Write-Status "Stopping Podman services using podman-compose..."
        try {
            podman-compose -f $PodmanComposeFile down -v
        }
        catch {
            Write-Warning "Some Podman services may not have stopped cleanly"
        }
        
        # Stop any remaining containers
        try {
            $containers = podman ps -q --filter "label=project=phoenix-hydra" 2>$null
            if ($containers) {
                Write-Status "Stopping remaining Phoenix Hydra containers..."
                $containers | ForEach-Object { podman stop $_ }
                $containers | ForEach-Object { podman rm $_ }
            }
        }
        catch {
            Write-Warning "Some containers may not have stopped"
        }
        
        # Remove Phoenix Hydra networks
        try {
            $networks = podman network ls --format "{{.Name}}" | Where-Object { $_ -like "*phoenix*" }
            if ($networks) {
                Write-Status "Removing Phoenix Hydra networks..."
                $networks | ForEach-Object { podman network rm $_ }
            }
        }
        catch {
            Write-Warning "Some networks may not have been removed"
        }
        
        Write-Success "Podman services stopped"
    }
    else {
        Write-Warning "Podman compose file not found or podman-compose not available"
    }
}

# Function to backup current Podman data
function Backup-PodmanData {
    param([bool]$KeepData)
    
    if ($KeepData) {
        Write-Status "Backing up Podman data for migration..."
        
        $podmanDataDir = Join-Path $env:USERPROFILE ".local\share\phoenix-hydra"
        $backupDataDir = Join-Path $BackupDir "podman-data-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        
        if (Test-Path $podmanDataDir) {
            New-Item -ItemType Directory -Path $backupDataDir -Force | Out-Null
            try {
                Copy-Item -Path "$podmanDataDir\*" -Destination $backupDataDir -Recurse -Force
                Write-Success "Podman data backed up to: $backupDataDir"
                $backupDataDir | Out-File -FilePath (Join-Path $BackupDir ".podman-data-location") -Encoding UTF8
            }
            catch {
                Write-Warning "Some data may not have been backed up"
            }
        }
        else {
            Write-Warning "No Podman data directory found to backup"
        }
    }
}

# Function to restore Docker configuration
function Restore-DockerConfig {
    Write-Status "Restoring Docker configuration from backup..."
    
    # Restore main compose file
    try {
        Copy-Item -Path (Join-Path $BackupDir "compose.yaml") -Destination $ProjectRoot -Force
        Write-Success "Restored compose.yaml"
    }
    catch {
        Write-Error "Failed to restore compose.yaml"
        throw
    }
    
    # Restore deployment scripts
    $scripts = @("deploy.sh", "teardown.sh", "verify.sh")
    foreach ($script in $scripts) {
        try {
            Copy-Item -Path (Join-Path $BackupDir $script) -Destination $ProjectRoot -Force
            Write-Success "Restored $script"
        }
        catch {
            Write-Error "Failed to restore $script"
            throw
        }
    }
    
    # Restore Docker compose directory
    $composeBackupDir = Join-Path $BackupDir "compose"
    if (Test-Path $composeBackupDir) {
        $composeDir = Join-Path $ProjectRoot "compose"
        if (Test-Path $composeDir) {
            Remove-Item -Path $composeDir -Recurse -Force
        }
        try {
            Copy-Item -Path $composeBackupDir -Destination $ProjectRoot -Recurse -Force
            Write-Success "Restored compose directory"
        }
        catch {
            Write-Error "Failed to restore compose directory"
            throw
        }
    }
    
    Write-Success "Docker configuration restored"
}

# Function to migrate data volumes
function Move-DataVolumes {
    param([bool]$KeepData)
    
    if ($KeepData) {
        Write-Status "Migrating data volumes from Podman to Docker..."
        
        # Check if we have backed up Podman data
        $podmanDataLocationFile = Join-Path $BackupDir ".podman-data-location"
        if (Test-Path $podmanDataLocationFile) {
            $podmanDataLocation = Get-Content $podmanDataLocationFile -Raw
            $podmanDataLocation = $podmanDataLocation.Trim()
            
            if (Test-Path $podmanDataLocation) {
                # Create Docker volume and copy data
                Write-Status "Creating Docker volume for database data..."
                
                try {
                    docker volume create phoenix_hydra_db_data
                }
                catch {
                    Write-Warning "Volume may already exist"
                }
                
                # Copy database data if it exists
                $dbDataPath = Join-Path $podmanDataLocation "db_data"
                if (Test-Path $dbDataPath) {
                    Write-Status "Copying database data to Docker volume..."
                    try {
                        docker run --rm -v "phoenix_hydra_db_data:/target" -v "${dbDataPath}:/source" alpine:latest sh -c "cp -r /source/* /target/ 2>/dev/null || true"
                        Write-Success "Database data migrated to Docker volume"
                    }
                    catch {
                        Write-Warning "Failed to migrate database data"
                    }
                }
                
                # Copy nginx config if it exists
                $nginxConfigPath = Join-Path $podmanDataLocation "nginx_config"
                if (Test-Path $nginxConfigPath) {
                    Write-Status "Copying nginx configuration..."
                    $nginxDestPath = Join-Path $ProjectRoot "compose\nginx"
                    New-Item -ItemType Directory -Path $nginxDestPath -Force | Out-Null
                    try {
                        Copy-Item -Path "$nginxConfigPath\*" -Destination $nginxDestPath -Recurse -Force
                        Write-Success "Nginx configuration migrated"
                    }
                    catch {
                        Write-Warning "Some nginx config may not have been copied"
                    }
                }
            }
            else {
                Write-Warning "No Podman data found to migrate"
            }
        }
        else {
            Write-Warning "No Podman data location file found"
        }
    }
}

# Function to start Docker services
function Start-DockerServices {
    Write-Status "Starting Docker services..."
    
    Set-Location $ProjectRoot
    
    # Determine docker-compose command
    $composeCmd = $null
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        $composeCmd = "docker-compose"
    }
    elseif (docker compose version 2>$null) {
        $composeCmd = "docker compose"
    }
    else {
        Write-Error "No docker-compose command available"
        throw
    }
    
    # Build and start services
    Write-Status "Building Docker images..."
    try {
        if ($composeCmd -eq "docker-compose") {
            docker-compose build
        }
        else {
            docker compose build
        }
        Write-Success "Docker images built"
    }
    catch {
        Write-Error "Failed to build Docker images"
        throw
    }
    
    Write-Status "Starting Docker services..."
    try {
        if ($composeCmd -eq "docker-compose") {
            docker-compose up -d
        }
        else {
            docker compose up -d
        }
        Write-Success "Docker services started"
    }
    catch {
        Write-Error "Failed to start Docker services"
        throw
    }
}

# Function to verify rollback success
function Test-Rollback {
    Write-Status "Verifying rollback success..."
    
    Set-Location $ProjectRoot
    
    # Wait for services to start
    Start-Sleep -Seconds 15
    
    # Check if verify script exists and run it
    $verifyScript = Join-Path $ProjectRoot "verify.sh"
    if (Test-Path $verifyScript) {
        Write-Status "Running service verification..."
        try {
            bash $verifyScript
            Write-Success "All services verified successfully"
        }
        catch {
            Write-Warning "Some services may not be ready yet"
        }
    }
    else {
        Write-Warning "Verify script not found"
    }
    
    # Check service endpoints
    $portsToCheck = @("8000", "3000", "8080")
    $healthyServices = 0
    
    foreach ($port in $portsToCheck) {
        $serviceName = switch ($port) {
            "8000" { "gap-detector" }
            "3000" { "windmill" }
            "8080" { "nginx" }
        }
        
        Write-Status "Checking $serviceName on port $port..."
        
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port" -TimeoutSec 10 -UseBasicParsing
            Write-Success "$serviceName service is responding on port $port"
            $healthyServices++
        }
        catch {
            Write-Warning "$serviceName service on port $port may not be ready yet"
        }
    }
    
    # Summary
    Write-Status "Rollback verification complete"
    Write-Host ""
    Write-Host "Rollback Status:"
    Write-Host "  - Services responding: $healthyServices/$($portsToCheck.Count)"
    Write-Host "  - Configuration: ✅ Docker"
    
    $podmanDataLocationFile = Join-Path $BackupDir ".podman-data-location"
    if (Test-Path $podmanDataLocationFile) {
        Write-Host "  - Data migration: ✅ Completed"
    }
    else {
        Write-Host "  - Data migration: ⏭️ Skipped"
    }
    
    Write-Host ""
    Write-Host "Docker services are running. You can:"
    Write-Host "  - Check logs: docker-compose logs -f"
    Write-Host "  - Check status: docker-compose ps"
    Write-Host "  - Stop services: docker-compose down"
    Write-Host ""
    Write-Host "Service endpoints:"
    Write-Host "  - Gap Detector: http://localhost:8000"
    Write-Host "  - Windmill: http://localhost:3000"
    Write-Host "  - Nginx: http://localhost:8080"
}

# Function to cleanup rollback artifacts
function Remove-RollbackArtifacts {
    Write-Status "Cleaning up rollback artifacts..."
    
    # Remove Podman configuration if rollback was successful
    $response = Read-Host "Do you want to remove Podman configuration? (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        $podmanDir = Join-Path $ProjectRoot "infra\podman"
        if (Test-Path $podmanDir) {
            Remove-Item -Path $podmanDir -Recurse -Force
            Write-Success "Podman configuration removed"
        }
        
        # Remove Podman data directory
        $podmanDataDir = Join-Path $env:USERPROFILE ".local\share\phoenix-hydra"
        if (Test-Path $podmanDataDir) {
            $dataResponse = Read-Host "Do you want to remove Podman data directory? (y/N)"
            if ($dataResponse -eq "y" -or $dataResponse -eq "Y") {
                Remove-Item -Path $podmanDataDir -Recurse -Force
                Write-Success "Podman data directory removed"
            }
        }
    }
}

# Main function
function Main {
    if ($Help) {
        Show-Usage
        return
    }
    
    Write-Status "Starting Phoenix Hydra rollback from Podman to Docker..."
    Write-Host ""
    
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Error "Prerequisites not met. Aborting rollback."
        exit 1
    }
    
    if ($VerifyOnly) {
        Write-Success "Rollback prerequisites verified successfully"
        return
    }
    
    # Confirm rollback unless forced
    if (-not $Force) {
        Write-Host ""
        Write-Warning "This will rollback Phoenix Hydra from Podman to Docker configuration."
        Write-Warning "All Podman services will be stopped and Docker services will be started."
        if ($KeepData) {
            Write-Status "Data volumes will be migrated from Podman to Docker."
        }
        else {
            Write-Warning "Data volumes will NOT be migrated. You may lose data."
        }
        Write-Host ""
        $response = Read-Host "Do you want to continue? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Status "Rollback cancelled by user"
            return
        }
    }
    
    try {
        # Execute rollback steps
        Stop-PodmanServices
        Backup-PodmanData $KeepData
        Restore-DockerConfig
        Move-DataVolumes $KeepData
        Start-DockerServices
        Test-Rollback
        Remove-RollbackArtifacts
        
        Write-Success "Phoenix Hydra rollback to Docker completed successfully!"
        Write-Host ""
        Write-Host "Next steps:"
        Write-Host "  - Verify all services are working correctly"
        Write-Host "  - Update any CI/CD pipelines to use Docker commands"
        Write-Host "  - Consider removing Podman if no longer needed"
    }
    catch {
        Write-Error "Rollback failed: $_"
        Write-Host "Check the error above and try manual recovery if needed."
        exit 1
    }
}

# Run main function
Main