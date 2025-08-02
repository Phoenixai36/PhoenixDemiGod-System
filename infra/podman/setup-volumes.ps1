#!/usr/bin/env pwsh

# Phoenix Hydra Podman Volume Setup Script (PowerShell)
# This script creates and configures volumes with proper rootless permissions

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PhoenixDataDir = Join-Path $env:USERPROFILE ".local/share/phoenix-hydra"
$NginxConfigSource = Join-Path $ScriptDir "nginx"

Write-Host "Setting up Phoenix Hydra Podman volumes..." -ForegroundColor Blue

# Create base directory structure
Write-Host "Creating base directories..." -ForegroundColor Blue
New-Item -ItemType Directory -Path $PhoenixDataDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PhoenixDataDir "db_data") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PhoenixDataDir "nginx_config") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $PhoenixDataDir "logs") -Force | Out-Null

# Set proper permissions for db_data volume
Write-Host "Setting up db_data volume permissions..." -ForegroundColor Blue
$dbDataDir = Join-Path $PhoenixDataDir "db_data"

# In Windows, we set the directory to be accessible by the current user
# Podman will handle user namespace mapping automatically
try {
    $acl = Get-Acl $dbDataDir
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $env:USERNAME, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
    )
    $acl.SetAccessRule($accessRule)
    Set-Acl -Path $dbDataDir -AclObject $acl
    Write-Host "Set secure permissions for db_data directory" -ForegroundColor Green
} catch {
    Write-Warning "Could not set specific permissions for db_data directory: $_"
}

Write-Host "Setting up nginx_config volume..." -ForegroundColor Blue
$nginxConfigDir = Join-Path $PhoenixDataDir "nginx_config"

# Copy nginx configuration files to the volume directory
$nginxConfSource = Join-Path $NginxConfigSource "nginx.conf"
if (Test-Path $nginxConfSource) {
    $nginxConfDest = Join-Path $nginxConfigDir "default.conf"
    Copy-Item -Path $nginxConfSource -Destination $nginxConfDest -Force
    Write-Host "Copied nginx.conf to volume directory" -ForegroundColor Green
} else {
    Write-Warning "nginx.conf not found at $nginxConfSource"
}

# Set proper permissions for nginx config volume
try {
    $acl = Get-Acl $nginxConfigDir
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $env:USERNAME, "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow"
    )
    $acl.SetAccessRule($accessRule)
    Set-Acl -Path $nginxConfigDir -AclObject $acl
    Write-Host "Set proper permissions for nginx_config directory" -ForegroundColor Green
} catch {
    Write-Warning "Could not set specific permissions for nginx_config directory: $_"
}

# Create logs directory with proper permissions
Write-Host "Setting up logs directory..." -ForegroundColor Blue
$logsDir = Join-Path $PhoenixDataDir "logs"

try {
    $acl = Get-Acl $logsDir
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        $env:USERNAME, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
    )
    $acl.SetAccessRule($accessRule)
    Set-Acl -Path $logsDir -AclObject $acl
    Write-Host "Set proper permissions for logs directory" -ForegroundColor Green
} catch {
    Write-Warning "Could not set specific permissions for logs directory: $_"
}

# Verify directory structure
Write-Host "Volume setup complete. Directory structure:" -ForegroundColor Blue
Get-ChildItem -Path $PhoenixDataDir | Format-Table Name, LastWriteTime, Length

Write-Host ""
Write-Host "✅ Phoenix Hydra volumes configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Volume locations:"
Write-Host "  - Database data: $(Join-Path $PhoenixDataDir 'db_data')"
Write-Host "  - Nginx config: $(Join-Path $PhoenixDataDir 'nginx_config')"
Write-Host "  - Logs: $(Join-Path $PhoenixDataDir 'logs')"
Write-Host ""
Write-Host "Note: In rootless Podman, user namespace mapping will handle"
Write-Host "      container user permissions automatically."