#!/usr/bin/env python3
"""
Phoenix Hydra Root Folder Refactoring Hook

This hook analyzes and refactors the root directory structure to:
- Consolidate virtual environments
- Clean up build outputs and temporary files
- Remove legacy/unused directories
- Organize configuration files
- Ensure proper directory structure

Author: Phoenix Hydra Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class RefactorAction:
    """Represents a single refactoring action"""

    action_type: str  # 'move', 'delete', 'consolidate', 'create'
    source_path: str
    target_path: Optional[str] = None
    reason: str = ""
    size_mb: float = 0.0
    file_count: int = 0
    backup_created: bool = False


@dataclass
class RefactorPlan:
    """Complete refactoring plan"""

    actions: List[RefactorAction]
    total_size_mb: float
    total_files: int
    backup_location: str
    created_at: str


class RootFolderRefactor:
    """Main class for root folder refactoring operations"""

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.backup_dir = (
            self.root_path
            / ".refactor_backup"
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load refactoring configuration"""
        config_path = self.root_path / ".kiro" / "hooks" / "refactor_config.json"

        default_config = {
            "virtual_environments": {
                "consolidate": True,
                "target_name": ".venv",
                "remove_duplicates": True,
            },
            "build_outputs": {
                "consolidate": True,
                "target_directory": "build",
                "subdirectories": ["output", "dist", "artifacts"],
            },
            "legacy_cleanup": {
                "enabled": True,
                "directories_to_remove": [
                    "Nueva carpeta",
                    "BooPhoenix369",
                    "awesome-n8n-templates-main",
                ],
                "empty_directories": True,
            },
            "configuration_consolidation": {
                "enabled": True,
                "target_directory": "configs",
                "file_patterns": ["*.config.js", "*.conf", "*.ini"],
            },
            "log_consolidation": {
                "enabled": True,
                "target_directory": "logs",
                "max_age_days": 30,
            },
            "safety": {
                "create_backup": True,
                "dry_run": False,
                "require_confirmation": True,
            },
        }

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}, using defaults")

        return default_config

    def _get_directory_size(self, path: Path) -> Tuple[float, int]:
        """Get directory size in MB and file count"""
        total_size = 0
        file_count = 0

        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not access {path}: {e}")

        return total_size / (1024 * 1024), file_count  # Convert to MB

    def analyze_root_structure(self) -> RefactorPlan:
        """Analyze current root structure and create refactoring plan"""
        logger.info("🔍 Analyzing root directory structure...")
        actions = []

        # Analyze virtual environments
        if self.config["virtual_environments"]["consolidate"]:
            actions.extend(self._analyze_virtual_environments())

        # Analyze build outputs
        if self.config["build_outputs"]["consolidate"]:
            actions.extend(self._analyze_build_outputs())

        # Analyze legacy directories
        if self.config["legacy_cleanup"]["enabled"]:
            actions.extend(self._analyze_legacy_directories())

        # Analyze configuration files
        if self.config["configuration_consolidation"]["enabled"]:
            actions.extend(self._analyze_configuration_files())

        # Analyze log files
        if self.config["log_consolidation"]["enabled"]:
            actions.extend(self._analyze_log_files())

        # Calculate totals
        total_size = sum(action.size_mb for action in actions)
        total_files = sum(action.file_count for action in actions)

        plan = RefactorPlan(
            actions=actions,
            total_size_mb=total_size,
            total_files=total_files,
            backup_location=str(self.backup_dir),
            created_at=datetime.now().isoformat(),
        )

        logger.info(
            f"📊 Analysis complete: {len(actions)} actions, {total_size:.1f}MB, {total_files} files"
        )
        return plan

    def _analyze_virtual_environments(self) -> List[RefactorAction]:
        """Analyze virtual environment directories"""
        actions = []
        venv_dirs = []

        # Find all virtual environment directories
        for item in self.root_path.iterdir():
            if item.is_dir() and item.name in [
                ".venv",
                "venv",
                "venv2",
                "venv3",
                ".venv2",
            ]:
                venv_dirs.append(item)

        if len(venv_dirs) <= 1:
            return actions

        target_name = self.config["virtual_environments"]["target_name"]
        target_path = self.root_path / target_name

        # Keep the most recent or largest venv as primary
        primary_venv = max(venv_dirs, key=lambda x: x.stat().st_mtime)

        for venv_dir in venv_dirs:
            size_mb, file_count = self._get_directory_size(venv_dir)

            if venv_dir == primary_venv and venv_dir.name != target_name:
                # Rename primary to target name
                actions.append(
                    RefactorAction(
                        action_type="move",
                        source_path=str(venv_dir),
                        target_path=str(target_path),
                        reason=f"Rename primary virtual environment to {target_name}",
                        size_mb=size_mb,
                        file_count=file_count,
                    )
                )
            elif venv_dir != primary_venv:
                # Remove duplicate virtual environments
                actions.append(
                    RefactorAction(
                        action_type="delete",
                        source_path=str(venv_dir),
                        reason="Remove duplicate virtual environment",
                        size_mb=size_mb,
                        file_count=file_count,
                    )
                )

        return actions

    def _analyze_build_outputs(self) -> List[RefactorAction]:
        """Analyze build output directories"""
        actions = []
        build_dirs = ["build", "build_output", "dist", "__pycache__"]

        target_dir = self.root_path / self.config["build_outputs"]["target_directory"]

        for dir_name in build_dirs:
            dir_path = self.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                size_mb, file_count = self._get_directory_size(dir_path)

                if dir_name == "build":
                    continue  # Already in target location

                if dir_name == "__pycache__":
                    # Delete __pycache__ directories
                    actions.append(
                        RefactorAction(
                            action_type="delete",
                            source_path=str(dir_path),
                            reason="Remove Python cache directory",
                            size_mb=size_mb,
                            file_count=file_count,
                        )
                    )
                else:
                    # Move to build subdirectory
                    target_subdir = target_dir / dir_name
                    actions.append(
                        RefactorAction(
                            action_type="move",
                            source_path=str(dir_path),
                            target_path=str(target_subdir),
                            reason=f"Consolidate build output into {target_dir.name}",
                            size_mb=size_mb,
                            file_count=file_count,
                        )
                    )

        return actions

    def _analyze_legacy_directories(self) -> List[RefactorAction]:
        """Analyze legacy and unused directories"""
        actions = []

        legacy_dirs = self.config["legacy_cleanup"]["directories_to_remove"]

        for dir_name in legacy_dirs:
            dir_path = self.root_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                size_mb, file_count = self._get_directory_size(dir_path)

                actions.append(
                    RefactorAction(
                        action_type="delete",
                        source_path=str(dir_path),
                        reason=f"Remove legacy/unused directory: {dir_name}",
                        size_mb=size_mb,
                        file_count=file_count,
                    )
                )

        # Find empty directories
        if self.config["legacy_cleanup"]["empty_directories"]:
            for item in self.root_path.iterdir():
                if item.is_dir() and self._is_empty_directory(item):
                    actions.append(
                        RefactorAction(
                            action_type="delete",
                            source_path=str(item),
                            reason="Remove empty directory",
                            size_mb=0.0,
                            file_count=0,
                        )
                    )

        return actions

    def _analyze_configuration_files(self) -> List[RefactorAction]:
        """Analyze scattered configuration files"""
        actions = []

        config_files = []
        patterns = self.config["configuration_consolidation"]["file_patterns"]

        # Find configuration files in root
        for pattern in patterns:
            config_files.extend(self.root_path.glob(pattern))

        target_dir = (
            self.root_path
            / self.config["configuration_consolidation"]["target_directory"]
        )

        for config_file in config_files:
            if config_file.parent == self.root_path:  # Only move files from root
                size_mb = config_file.stat().st_size / (1024 * 1024)
                target_path = target_dir / config_file.name

                actions.append(
                    RefactorAction(
                        action_type="move",
                        source_path=str(config_file),
                        target_path=str(target_path),
                        reason="Consolidate configuration files",
                        size_mb=size_mb,
                        file_count=1,
                    )
                )

        return actions

    def _analyze_log_files(self) -> List[RefactorAction]:
        """Analyze log files and directories"""
        actions = []

        # Find log files in root
        log_files = list(self.root_path.glob("*.log"))
        target_dir = (
            self.root_path / self.config["log_consolidation"]["target_directory"]
        )

        for log_file in log_files:
            size_mb = log_file.stat().st_size / (1024 * 1024)
            target_path = target_dir / log_file.name

            actions.append(
                RefactorAction(
                    action_type="move",
                    source_path=str(log_file),
                    target_path=str(target_path),
                    reason="Consolidate log files",
                    size_mb=size_mb,
                    file_count=1,
                )
            )

        return actions

    def _is_empty_directory(self, path: Path) -> bool:
        """Check if directory is empty or contains only hidden files"""
        try:
            items = list(path.iterdir())
            return len(items) == 0 or all(item.name.startswith(".") for item in items)
        except (PermissionError, OSError):
            return False

    def create_backup(self, plan: RefactorPlan) -> bool:
        """Create backup of files that will be modified"""
        if not self.config["safety"]["create_backup"]:
            return True

        logger.info(f"📦 Creating backup at {self.backup_dir}")

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Create backup manifest
            manifest = {
                "created_at": datetime.now().isoformat(),
                "actions": [asdict(action) for action in plan.actions],
                "root_path": str(self.root_path),
            }

            with open(self.backup_dir / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=2)

            # Backup files that will be moved or deleted
            for action in plan.actions:
                source_path = Path(action.source_path)
                if source_path.exists():
                    relative_path = source_path.relative_to(self.root_path)
                    backup_path = self.backup_dir / relative_path

                    backup_path.parent.mkdir(parents=True, exist_ok=True)

                    if source_path.is_dir():
                        shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source_path, backup_path)

                    action.backup_created = True

            logger.info("✅ Backup created successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False

    def execute_plan(self, plan: RefactorPlan) -> bool:
        """Execute the refactoring plan"""
        if self.config["safety"]["dry_run"]:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
            self._print_plan_summary(plan)
            return True

        logger.info("🚀 Executing refactoring plan...")

        success_count = 0
        error_count = 0

        for i, action in enumerate(plan.actions, 1):
            logger.info(
                f"[{i}/{len(plan.actions)}] {action.action_type.upper()}: {action.source_path}"
            )

            try:
                if action.action_type == "move":
                    self._execute_move(action)
                elif action.action_type == "delete":
                    self._execute_delete(action)
                elif action.action_type == "create":
                    self._execute_create(action)

                success_count += 1
                logger.info(f"✅ Completed: {action.reason}")

            except Exception as e:
                error_count += 1
                logger.error(f"❌ Failed: {action.reason} - {e}")

        logger.info(
            f"📊 Execution complete: {success_count} successful, {error_count} failed"
        )

        # Save execution report
        self._save_execution_report(plan, success_count, error_count)

        return error_count == 0

    def _execute_move(self, action: RefactorAction):
        """Execute a move action"""
        source = Path(action.source_path)
        target = Path(action.target_path)

        if not source.exists():
            raise FileNotFoundError(f"Source path does not exist: {source}")

        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)

        # Move the file/directory
        shutil.move(str(source), str(target))

    def _execute_delete(self, action: RefactorAction):
        """Execute a delete action"""
        path = Path(action.source_path)

        if not path.exists():
            logger.warning(f"Path already deleted: {path}")
            return

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def _execute_create(self, action: RefactorAction):
        """Execute a create action"""
        path = Path(action.target_path)
        path.mkdir(parents=True, exist_ok=True)

    def _print_plan_summary(self, plan: RefactorPlan):
        """Print a summary of the refactoring plan"""
        print("\n" + "=" * 60)
        print("🔧 REFACTORING PLAN SUMMARY")
        print("=" * 60)
        print(f"📁 Root Directory: {self.root_path}")
        print(f"📊 Total Actions: {len(plan.actions)}")
        print(f"💾 Total Size: {plan.total_size_mb:.1f} MB")
        print(f"📄 Total Files: {plan.total_files}")
        print(f"🗓️ Created: {plan.created_at}")

        if self.config["safety"]["create_backup"]:
            print(f"📦 Backup Location: {plan.backup_location}")

        print("\n📋 ACTIONS:")
        print("-" * 60)

        action_counts = {}
        for action in plan.actions:
            action_counts[action.action_type] = (
                action_counts.get(action.action_type, 0) + 1
            )

            icon = {"move": "📁", "delete": "🗑️", "create": "📂"}.get(
                action.action_type, "⚡"
            )
            print(f"{icon} {action.action_type.upper()}: {action.source_path}")
            if action.target_path:
                print(f"   → {action.target_path}")
            print(f"   💡 {action.reason}")
            print(f"   📊 {action.size_mb:.1f}MB, {action.file_count} files")
            print()

        print("📈 ACTION SUMMARY:")
        for action_type, count in action_counts.items():
            print(f"   {action_type.upper()}: {count}")

        print("=" * 60)

    def _save_execution_report(
        self, plan: RefactorPlan, success_count: int, error_count: int
    ):
        """Save execution report"""
        report = {
            "execution_time": datetime.now().isoformat(),
            "plan": asdict(plan),
            "results": {
                "successful_actions": success_count,
                "failed_actions": error_count,
                "total_actions": len(plan.actions),
            },
        }

        report_path = self.root_path / "logs" / "refactor_execution_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Execution report saved: {report_path}")


# Hook integration functions
async def refactor_root_folder_hook(event=None):
    """Main hook function for root folder refactoring"""
    try:
        logger.info("🔧 Starting root folder refactoring...")

        refactor = RootFolderRefactor()

        # Analyze current structure
        plan = refactor.analyze_root_structure()

        if not plan.actions:
            logger.info(
                "✅ No refactoring needed - directory structure is already optimal"
            )
            return

        # Print plan summary
        refactor._print_plan_summary(plan)

        # Create backup if enabled
        if refactor.config["safety"]["create_backup"]:
            if not refactor.create_backup(plan):
                logger.error("❌ Backup creation failed - aborting refactoring")
                return

        # Execute plan
        success = refactor.execute_plan(plan)

        if success:
            logger.info("🎉 Root folder refactoring completed successfully!")
        else:
            logger.error("⚠️ Refactoring completed with some errors - check logs")

    except Exception as e:
        logger.error(f"💥 Refactoring failed: {e}")
        raise


# Manual execution support
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Phoenix Hydra Root Folder Refactoring"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--config", help="Path to custom configuration file")

    args = parser.parse_args()

    # Run the refactoring
    asyncio.run(refactor_root_folder_hook())
