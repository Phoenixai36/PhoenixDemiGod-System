# Phoenix Hydra Root Folder Refactoring

The Phoenix Hydra Root Folder Refactoring system provides automated and manual tools to organize and clean up the project's root directory structure. This system helps maintain a clean, organized codebase by consolidating scattered files, removing legacy directories, and ensuring consistent organization.

## Overview

The refactoring system analyzes the current directory structure and creates a comprehensive plan to:

- **Consolidate Virtual Environments**: Merge multiple venv directories into a single `.venv`
- **Organize Build Outputs**: Move build artifacts into a structured `build/` directory
- **Clean Legacy Directories**: Remove unused or legacy directories safely
- **Consolidate Configuration**: Move scattered config files into `configs/` directory
- **Organize Logs**: Consolidate log files into `logs/` directory
- **Model Organization**: Ensure AI models are properly organized in `models/` directory

## Features

### 🔍 Intelligent Analysis
- Scans entire root directory structure
- Identifies optimization opportunities
- Calculates space savings and file counts
- Provides detailed refactoring plan before execution

### 🛡️ Safety First
- **Automatic Backups**: Creates complete backup before making changes
- **Dry Run Mode**: Preview changes without modifying anything
- **Rollback Support**: Easy restoration from backups
- **Confirmation Prompts**: User confirmation for destructive operations

### ⚙️ Highly Configurable
- JSON-based configuration system
- Customizable rules for each refactoring category
- Include/exclude patterns for fine-grained control
- Environment-specific settings

### 🔄 Multiple Execution Methods
- **VS Code Tasks**: Integrated with VS Code task system
- **PowerShell Script**: Windows-friendly execution
- **Python Direct**: Direct Python execution
- **Event-Driven**: Automatic triggering based on file system events

### 🪟 Windows Compatibility
- **Graceful Error Handling**: Automatically handles Windows file locking issues
- **Virtual Environment Safety**: Skips locked .pyd files and venv directories in use
- **Process-Safe Operations**: Continues refactoring even when some files are locked by running processes
- **Detailed Logging**: Provides clear warnings for skipped files with explanations

## Quick Start

### Using VS Code Tasks (Recommended)

1. **Open Command Palette**: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
2. **Run Task**: Type "Tasks: Run Task"
3. **Select Task**: Choose either:
   - `Refactor Root Folder (Dry Run)` - Preview changes only
   - `Refactor Root Folder` - Execute refactoring

### Using PowerShell Script

```powershell
# Preview changes (recommended first)
.\scripts\refactor-root-folder.ps1 -DryRun

# Execute refactoring with backup
.\scripts\refactor-root-folder.ps1

# Execute without confirmation prompts
.\scripts\refactor-root-folder.ps1 -Force

# Execute without backup (not recommended)
.\scripts\refactor-root-folder.ps1 -NoBackup
```

### Using Python Directly

```bash
# Set Python path
export PYTHONPATH="./src"  # Linux/macOS
$env:PYTHONPATH = "./src"  # Windows PowerShell

# Preview changes
python src/hooks/refactor_root_folder.py --dry-run

# Execute refactoring
python src/hooks/refactor_root_folder.py

# Execute without backup
python src/hooks/refactor_root_folder.py --no-backup
```

## Configuration

The refactoring behavior is controlled by `.kiro/hooks/refactor_config.json`. Key configuration sections:

### Virtual Environments
```json
{
  "virtual_environments": {
    "consolidate": true,
    "target_name": ".venv",
    "remove_duplicates": true,
    "preserve_requirements": true
  }
}
```

### Build Outputs
```json
{
  "build_outputs": {
    "consolidate": true,
    "target_directory": "build",
    "subdirectories": ["output", "dist", "artifacts", "temp"],
    "clean_pycache": true
  }
}
```

### Legacy Cleanup
```json
{
  "legacy_cleanup": {
    "enabled": true,
    "directories_to_remove": [
      "Nueva carpeta",
      "BooPhoenix369",
      "awesome-n8n-templates-main"
    ],
    "empty_directories": true
  }
}
```

### Safety Settings
```json
{
  "safety": {
    "create_backup": true,
    "dry_run": false,
    "require_confirmation": false,
    "max_file_size_mb": 1000,
    "preserve_git": true
  }
}
```

## Refactoring Categories

### 1. Virtual Environment Consolidation
- **Problem**: Multiple virtual environments (`.venv`, `venv`, `venv2`, `venv3`)
- **Solution**: Consolidate into single `.venv` directory
- **Benefits**: Reduces disk usage, simplifies development setup

### 2. Build Output Organization
- **Problem**: Scattered build artifacts (`build/`, `build_output/`, `dist/`, `__pycache__/`)
- **Solution**: Organize into structured `build/` directory with subdirectories
- **Benefits**: Cleaner root directory, easier cleanup

### 3. Legacy Directory Cleanup
- **Problem**: Unused directories from old experiments or downloads
- **Solution**: Safe removal with backup
- **Benefits**: Reduced clutter, improved navigation

### 4. Configuration Consolidation
- **Problem**: Config files scattered in root directory
- **Solution**: Move to `configs/` directory (excluding essential files)
- **Benefits**: Centralized configuration management

### 5. Log File Organization
- **Problem**: Log files in root directory
- **Solution**: Consolidate into `logs/` directory
- **Benefits**: Centralized logging, easier log management

## Safety Features

### Automatic Backups
- Complete backup created in `.refactor_backup/YYYYMMDD_HHMMSS/`
- Includes manifest file with operation details
- Preserves original file permissions and timestamps

### Dry Run Mode
- Shows exactly what would be changed
- No modifications made to file system
- Detailed analysis and size calculations
- Perfect for planning and verification

### Rollback Support
```bash
# Manual rollback from backup
cp -r .refactor_backup/20250108_143022/* .

# Or use the backup manifest for selective restoration
```

### Git Integration
- Respects `.gitignore` patterns
- Preserves Git repository integrity
- Recommends committing changes after refactoring

## Windows-Specific Improvements

### Enhanced Error Handling
The refactoring system includes specialized handling for Windows-specific challenges:

**File Locking Issues**
- **Virtual Environments**: Automatically detects and skips locked .pyd files and active virtual environment directories
- **Process-Locked Files**: Gracefully handles files locked by running processes (IDEs, Python interpreters, etc.)
- **Detailed Logging**: Provides clear warnings explaining why files were skipped

**Example Log Output**
```
WARNING - Skipping locked file/directory (common on Windows): .venv\Lib\site-packages\numpy\core\_multiarray_umath.pyd
WARNING - Reason: [Errno 13] Permission denied: '.venv\\Lib\\site-packages\\numpy\\core\\_multiarray_umath.pyd'
```

**Behavior Changes**
- **Before**: Refactoring would fail completely when encountering locked files
- **After**: System continues operation, skipping only the locked files with detailed logging
- **Result**: More reliable execution on Windows development environments

### Best Practices for Windows
1. **Close IDEs**: Close VS Code, PyCharm, or other IDEs that might lock files
2. **Deactivate Virtual Environments**: Exit any active Python virtual environments
3. **Review Warnings**: Check logs for skipped files - this is normal and expected
4. **Multiple Runs**: Run refactoring multiple times if needed after closing processes

## Integration with Phoenix Hydra

### Event System Integration
The refactoring hook integrates with the Phoenix Hydra event system:

```python
# Register with event bus
from src.hooks.register_refactor_hook import register_refactor_hooks

register_refactor_hooks(event_bus)

# Manual trigger
await event_bus.emit({
    "event_type": "refactor.root.manual",
    "source": "user_request"
})
```

### Automatic Triggering
- **File System Events**: Triggered when root directory becomes cluttered
- **Scheduled Execution**: Weekly or daily cleanup (configurable)
- **Threshold-Based**: Automatic analysis when file count exceeds limits

## Monitoring and Reporting

### Execution Reports
- Detailed JSON reports saved to `logs/refactor_execution_report.json`
- Includes success/failure counts, timing, and file details
- Backup location and restoration instructions

### Logging
- Comprehensive logging to console and files
- Color-coded output for easy reading
- Progress indicators for long operations

### Metrics
- Space saved (MB)
- Files processed
- Directories consolidated
- Execution time

## Best Practices

### Before Running
1. **Commit Current Changes**: Ensure Git working directory is clean
2. **Run Dry Run First**: Always preview changes before execution
3. **Review Configuration**: Customize settings for your needs
4. **Check Disk Space**: Ensure sufficient space for backups

### After Running
1. **Test Functionality**: Verify all services still work
2. **Update Scripts**: Fix any hardcoded paths that changed
3. **Commit Changes**: Add refactored structure to version control
4. **Update Documentation**: Reflect any structural changes
5. **Review Warnings**: Check logs for any skipped files (normal on Windows)

### Regular Maintenance
- Run monthly to prevent accumulation of clutter
- Review and update configuration as project evolves
- Monitor execution reports for optimization opportunities

## Troubleshooting

### Common Issues

**Permission Errors**
```bash
# Ensure proper permissions
chmod +x scripts/refactor-root-folder.ps1
```

**Python Path Issues**
```bash
# Set PYTHONPATH correctly
export PYTHONPATH="$(pwd)/src"
```

**Windows File Locking (Handled Gracefully)**
- **Virtual Environment Files**: System automatically skips locked .pyd files and active venv directories
- **Process-Locked Files**: Continues operation and logs warnings for files in use by other processes
- **Expected Behavior**: Warnings about skipped files are normal on Windows and don't indicate failure
- **Log Messages**: Look for "Skipping locked file/directory (common on Windows)" messages

**Configuration Errors**
- Validate JSON syntax in configuration file
- Check file paths in configuration
- Ensure target directories are writable

### Recovery from Failed Refactoring
1. **Check Backup**: Locate backup in `.refactor_backup/`
2. **Review Logs**: Check execution report for specific failures
3. **Selective Restore**: Restore only failed operations
4. **Re-run with Fixes**: Update configuration and retry

## Advanced Usage

### Custom Configuration
```bash
# Use custom configuration file
python src/hooks/refactor_root_folder.py --config my_config.json
```

### Programmatic Usage
```python
from src.hooks.refactor_root_folder import RootFolderRefactor

refactor = RootFolderRefactor()
plan = refactor.analyze_root_structure()
refactor.execute_plan(plan)
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Refactor Root Directory
  run: |
    python src/hooks/refactor_root_folder.py --dry-run
    # Review output and conditionally execute
```

## Contributing

To extend the refactoring system:

1. **Add New Categories**: Extend analysis methods in `RootFolderRefactor`
2. **Custom Actions**: Add new action types beyond move/delete/create
3. **Enhanced Safety**: Add more validation and safety checks
4. **UI Integration**: Create web interface for configuration and execution

The refactoring system is designed to be extensible and maintainable, following Phoenix Hydra's architectural patterns and coding standards.