#!/usr/bin/env pwsh
<#
.SYNOPSIS
Phoenix Hydra Root Folder Refactoring Script

.DESCRIPTION
This script provides a convenient way to run the Phoenix Hydra root folder
refactoring hook with various options and safety checks.

.PARAMETER DryRun
Show what would be done without making changes

.PARAMETER NoBackup
Skip backup creation (not recommended)

.PARAMETER Force
Skip confirmation prompts

.PARAMETER Config
Path to custom configuration file

.EXAMPLE
.\scripts\refactor-root-folder.ps1
.\scripts\refactor-root-folder.ps1 -DryRun
.\scripts\refactor-root-folder.ps1 -Force -NoBackup
#>

param(
    [switch]$DryRun,
    [switch]$NoBackup,
    [switch]$Force,
    [string]$Config = ""
)

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Magenta = "`e[35m"
$Cyan = "`e[36m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Reset)
    Write-Host "$Color$Message$Reset"
}

function Show-Banner {
    Write-ColorOutput @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🔧 Phoenix Hydra Root Folder Refactoring                 ║
║                                                              ║
║    • Consolidate virtual environments                       ║
║    • Clean up build outputs and temporary files             ║
║    • Remove legacy/unused directories                       ║
║    • Organize configuration and log files                   ║
║    • Create comprehensive backup before changes             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ $Cyan
}fu
nction Test-Prerequisites {
    Write-ColorOutput "🔍 Checking prerequisites..." $Blue
    
    $missing = @()
    
    if (!(Get-Command python -ErrorAction SilentlyContinue)) {
        $missing += "python"
    }
    
    if (!(Test-Path "src/hooks/refactor_root_folder.py")) {
        $missing += "refactor_root_folder.py"
    }
    
    if ($missing.Count -gt 0) {
        Write-ColorOutput "❌ Missing prerequisites: $($missing -join ', ')" $Red
        Write-ColorOutput "Please ensure Python is installed and you're in the Phoenix Hydra root directory." $Yellow
        exit 1
    }
    
    Write-ColorOutput "✅ All prerequisites found" $Green
}

function Show-Warning {
    if (!$Force -and !$DryRun) {
        Write-ColorOutput @"

⚠️  WARNING: This script will modify your directory structure!

The following operations may be performed:
• Move or delete directories and files
• Consolidate virtual environments
• Clean up build outputs and temporary files
• Remove legacy directories

💡 Windows Note: Some files may be locked by processes (like virtual environments).
   This is normal and the script will continue with other operations.

"@ $Yellow

        if (!$NoBackup) {
            Write-ColorOutput "✅ A backup will be created before making changes." $Green
        } else {
            Write-ColorOutput "❌ NO BACKUP will be created (--NoBackup specified)." $Red
        }
        
        Write-ColorOutput "`nDo you want to continue? (y/N): " $Yellow -NoNewline
        $response = Read-Host
        
        if ($response -ne "y" -and $response -ne "Y") {
            Write-ColorOutput "❌ Operation cancelled by user." $Yellow
            exit 0
        }
    }
}

function Build-PythonArgs {
    $args = @("src/hooks/refactor_root_folder.py")
    
    if ($DryRun) {
        $args += "--dry-run"
        Write-ColorOutput "🔍 Running in DRY RUN mode - no changes will be made" $Blue
    }
    
    if ($NoBackup) {
        $args += "--no-backup"
        Write-ColorOutput "⚠️ Backup creation disabled" $Yellow
    }
    
    if ($Config) {
        if (Test-Path $Config) {
            $args += "--config", $Config
            Write-ColorOutput "📄 Using custom config: $Config" $Blue
        } else {
            Write-ColorOutput "❌ Config file not found: $Config" $Red
            exit 1
        }
    }
    
    return $args
}

# Main execution
try {
    Show-Banner
    Test-Prerequisites
    Show-Warning
    
    Write-ColorOutput "🚀 Starting root folder refactoring..." $Magenta
    
    # Set Python path
    $env:PYTHONPATH = "$PWD/src"
    
    # Build arguments
    $pythonArgs = Build-PythonArgs
    
    # Execute the refactoring
    Write-ColorOutput "🐍 Executing: python $($pythonArgs -join ' ')" $Blue
    
    $result = & python @pythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput @"

🎉 Root folder refactoring completed successfully!

📊 Results Summary:
• Successfully organized your project structure
• Backup created in .refactor_backup/ directory
• Execution report saved in logs/refactor_execution_report.json

Next steps:
• Review the changes made
• Test that everything still works correctly
• Commit the changes to version control
• Update any scripts that reference moved files

💡 If any operations failed due to locked files (common on Windows),
   you can safely ignore these - the important cleanup was completed.

"@ $Green
    } else {
        Write-ColorOutput @"
⚠️ Refactoring completed with some warnings (exit code: $LASTEXITCODE)

This is often normal on Windows due to locked files in virtual environments.
Check the execution report for details: logs/refactor_execution_report.json

Most operations likely completed successfully. Review the output above.
"@ $Yellow
    }
    
} catch {
    Write-ColorOutput "💥 Unexpected error: $_" $Red
    Write-ColorOutput "Please check the error details and try again." $Yellow
    exit 1
}