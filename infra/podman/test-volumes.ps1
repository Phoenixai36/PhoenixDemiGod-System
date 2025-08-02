# Phoenix Hydra Podman Volume Test Script (PowerShell)
# This script validates that volumes are properly configured

$ErrorActionPreference = "Stop"

$PhoenixDataDir = "$env:USERPROFILE\.local\share\phoenix-hydra"

Write-Host "🧪 Testing Phoenix Hydra Podman volumes..." -ForegroundColor Cyan

# Test 1: Check if volume directories exist
Write-Host "`nTest 1: Checking volume directory structure..."
$RequiredDirs = @(
    $PhoenixDataDir,
    "$PhoenixDataDir\db_data",
    "$PhoenixDataDir\nginx_config",
    "$PhoenixDataDir\logs"
)

$allDirsExist = $true
foreach ($dir in $RequiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✅ Directory exists: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Directory missing: $dir" -ForegroundColor Red
        $allDirsExist = $false
    }
}

if (-not $allDirsExist) {
    Write-Host "Some required directories are missing. Run setup-volumes.ps1 first." -ForegroundColor Red
    exit 1
}

# Test 2: Check directory accessibility
Write-Host "`nTest 2: Checking directory accessibility..."

foreach ($dir in $RequiredDirs) {
    try {
        $acl = Get-Acl $dir
        $hasAccess = $acl.Access | Where-Object { 
            $_.IdentityReference -like "*$env:USERNAME*" -and 
            ($_.FileSystemRights -match "FullControl|Write|Modify")
        }
        
        if ($hasAccess) {
            Write-Host "  ✅ Directory accessible: $(Split-Path $dir -Leaf)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Directory may have limited access: $(Split-Path $dir -Leaf)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠️  Could not check permissions for: $(Split-Path $dir -Leaf)" -ForegroundColor Yellow
    }
}

# Test 3: Check nginx configuration file
Write-Host "`nTest 3: Checking nginx configuration..."
$NginxConfigFile = "$PhoenixDataDir\nginx_config\default.conf"

if (Test-Path $NginxConfigFile) {
    Write-Host "  ✅ Nginx config file exists: $NginxConfigFile" -ForegroundColor Green
    
    try {
        $configContent = Get-Content $NginxConfigFile -Raw
        
        if ($configContent -match "listen 8080") {
            Write-Host "  ✅ Nginx config contains listen directive" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Nginx config missing listen directive" -ForegroundColor Yellow
        }
        
        if ($configContent -match "location /health") {
            Write-Host "  ✅ Nginx config contains health check endpoint" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Nginx config missing health check endpoint" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ Could not read nginx config file" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ❌ Nginx config file missing: $NginxConfigFile" -ForegroundColor Red
    exit 1
}

# Test 4: Test write permissions
Write-Host "`nTest 4: Testing write permissions..."

# Test db_data write permission
$TestFile = "$PhoenixDataDir\db_data\.test_write"
try {
    New-Item -ItemType File -Path $TestFile -Force | Out-Null
    Write-Host "  ✅ db_data directory is writable" -ForegroundColor Green
    Remove-Item $TestFile -Force
} catch {
    Write-Host "  ❌ db_data directory is not writable" -ForegroundColor Red
    exit 1
}

# Test logs write permission
$TestFile = "$PhoenixDataDir\logs\.test_write"
try {
    New-Item -ItemType File -Path $TestFile -Force | Out-Null
    Write-Host "  ✅ logs directory is writable" -ForegroundColor Green
    Remove-Item $TestFile -Force
} catch {
    Write-Host "  ❌ logs directory is not writable" -ForegroundColor Red
    exit 1
}

# Test 5: Check disk space
Write-Host "`nTest 5: Checking available disk space..."
try {
    $drive = (Get-Item $PhoenixDataDir).PSDrive
    $freeSpace = [math]::Round($drive.Free / 1GB, 2)
    
    if ($freeSpace -gt 1) {
        Write-Host "  ✅ Sufficient disk space available: ${freeSpace}GB" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Low disk space: ${freeSpace}GB" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Could not check disk space" -ForegroundColor Yellow
}

Write-Host "`n🎉 All volume tests passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Volume summary:" -ForegroundColor Yellow
Write-Host "  - Database data: $PhoenixDataDir\db_data"
Write-Host "  - Nginx config: $PhoenixDataDir\nginx_config"
Write-Host "  - Logs: $PhoenixDataDir\logs"
Write-Host ""
Write-Host "Ready for Podman deployment!" -ForegroundColor Cyan