"""
Utility functions for Phoenix Hydra security management.
Provides common functionality used across security components.
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the Phoenix Hydra project root directory."""
    current_path = Path(__file__).resolve()
    
    # Look for project markers
    for parent in current_path.parents:
        if (parent / "package.json").exists() or (parent / "pyproject.toml").exists():
            return parent
    
    # Fallback to current working directory
    return Path.cwd()


def get_security_config_path() -> Path:
    """Get the path to the security configuration file."""
    return get_project_root() / "scripts" / "security" / "config" / "security-config.json"


def get_vulnerability_db_path() -> Path:
    """Get the path to the local vulnerability database."""
    return get_project_root() / ".phoenix-hydra" / "security" / "vulnerability-db.sqlite"


def get_audit_log_path() -> Path:
    """Get the path to the audit log directory."""
    return get_project_root() / ".phoenix-hydra" / "security" / "audit-logs"


def ensure_directory_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return ""
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def generate_unique_id() -> str:
    """Generate a unique ID for security records."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = hashlib.md5(str(datetime.now().microsecond).encode()).hexdigest()[:8]
    return f"{timestamp}_{random_suffix}"


async def run_command(command: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Run a command asynchronously and return exit code, stdout, and stderr.
    
    Args:
        command: Command and arguments as a list
        cwd: Working directory for the command
        timeout: Timeout in seconds
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return process.returncode, stdout.decode(), stderr.decode()
    
    except asyncio.TimeoutError:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(command)}")
        return -1, "", f"Command timed out after {timeout} seconds"
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return -1, "", str(e)


async def run_npm_audit() -> Dict[str, Any]:
    """Run npm audit and return parsed JSON results."""
    project_root = get_project_root()
    
    # Check if package.json exists
    package_json_path = project_root / "package.json"
    if not package_json_path.exists():
        logger.warning("No package.json found, skipping npm audit")
        return {"vulnerabilities": {}, "metadata": {"totalDependencies": 0}}
    
    exit_code, stdout, stderr = await run_command(
        ["npm", "audit", "--json"],
        cwd=project_root
    )
    
    if exit_code == 0 or exit_code == 1:  # npm audit returns 1 when vulnerabilities found
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse npm audit output: {e}")
            return {"error": "Failed to parse npm audit output"}
    else:
        logger.error(f"npm audit failed: {stderr}")
        return {"error": f"npm audit failed: {stderr}"}


def parse_package_json() -> Dict[str, Any]:
    """Parse the project's package.json file."""
    project_root = get_project_root()
    package_json_path = project_root / "package.json"
    
    if not package_json_path.exists():
        return {}
    
    try:
        with open(package_json_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to parse package.json: {e}")
        return {}


def get_installed_packages() -> Dict[str, str]:
    """Get list of installed packages and their versions."""
    package_json = parse_package_json()
    
    dependencies = {}
    dependencies.update(package_json.get("dependencies", {}))
    dependencies.update(package_json.get("devDependencies", {}))
    
    return dependencies


def is_phoenix_core_package(package_name: str) -> bool:
    """Check if a package is considered a Phoenix Hydra core component."""
    core_packages = {
        "react-syntax-highlighter",
        "prismjs", 
        "highlight.js",
        "lowlight",
        "@types/react",
        "react",
        "react-dom",
        "typescript",
        "vite",
        "@vitejs/plugin-react"
    }
    
    return package_name in core_packages


def format_vulnerability_summary(vulnerabilities: List[Dict[str, Any]]) -> str:
    """Format a human-readable summary of vulnerabilities."""
    if not vulnerabilities:
        return "No vulnerabilities found."
    
    severity_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "unknown").lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    summary_parts = []
    for severity, count in severity_counts.items():
        if count > 0:
            summary_parts.append(f"{count} {severity}")
    
    return f"Found {len(vulnerabilities)} vulnerabilities: {', '.join(summary_parts)}"


def create_backup_filename(package_name: str, version: str) -> str:
    """Create a backup filename for package updates."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_package_name = package_name.replace("/", "_").replace("@", "")
    return f"backup_{safe_package_name}_{version}_{timestamp}.json"


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return {}


def save_json_file(data: Dict[str, Any], file_path: Path) -> bool:
    """Save data to a JSON file."""
    try:
        ensure_directory_exists(file_path.parent)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def get_current_user() -> str:
    """Get the current user name for audit logging."""
    return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def format_datetime(dt: datetime) -> str:
    """Format datetime for consistent display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string."""
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            logger.error(f"Failed to parse datetime: {dt_str}")
            return None