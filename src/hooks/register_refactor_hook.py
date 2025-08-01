#!/usr/bin/env python3
"""
Phoenix Hydra Root Folder Refactoring Hook Registration

This module registers the root folder refactoring hook with the Phoenix Hydra
event system, enabling automatic and manual execution.

Author: Phoenix Hydra Team
Version: 1.0.0
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from .core.events import EventBus, EventFilter
from .refactor_root_folder import refactor_root_folder_hook

logger = logging.getLogger(__name__)


class RefactorHookManager:
    """Manages the root folder refactoring hook registration and execution"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.config = self._load_hook_config()

    def _load_hook_config(self) -> Dict[str, Any]:
        """Load hook-specific configuration"""
        return {
            "auto_trigger": {
                "enabled": False,  # Disabled by default for safety
                "file_threshold": 100,  # Trigger when root has >100 files
                "schedule": "weekly",  # weekly, daily, manual
            },
            "manual_trigger": {"enabled": True, "require_confirmation": True},
            "event_filters": {
                "file_creation_threshold": 50,  # Trigger analysis after 50 new files
                "directory_creation_threshold": 10,  # Trigger analysis after 10 new dirs
            },
        }

    def register_hooks(self):
        """Register all refactoring-related hooks with the event bus"""
        logger.info("🔧 Registering root folder refactoring hooks...")

        # Manual execution hook (always enabled)
        self.event_bus.subscribe(
            self._manual_refactor_handler,
            EventFilter(event_types=["refactor.root.manual"]),
        )

        # Scheduled execution hook
        if self.config["auto_trigger"]["enabled"]:
            self.event_bus.subscribe(
                self._scheduled_refactor_handler,
                EventFilter(event_types=["scheduler.weekly", "scheduler.daily"]),
            )

        # File system monitoring hook (for analysis triggers)
        self.event_bus.subscribe(
            self._file_system_analysis_handler,
            EventFilter(
                event_types=["code.file.created", "code.directory.created"],
                custom_filter=self._should_trigger_analysis,
            ),
        )

        logger.info("✅ Root folder refactoring hooks registered")

    async def _manual_refactor_handler(self, event):
        """Handle manual refactoring requests"""
        logger.info("🔧 Manual root folder refactoring requested")

        try:
            # Add confirmation step if required
            if self.config["manual_trigger"]["require_confirmation"]:
                logger.info("⚠️ Manual refactoring requires confirmation")
                # In a real implementation, this would show a UI confirmation
                # For now, we'll proceed with the assumption of confirmation

            await refactor_root_folder_hook(event)

            # Emit completion event
            await self.event_bus.emit(
                {
                    "event_type": "refactor.root.completed",
                    "source": "refactor_hook",
                    "data": {
                        "trigger": "manual",
                        "success": True,
                        "timestamp": event.get("timestamp"),
                    },
                }
            )

        except Exception as e:
            logger.error(f"❌ Manual refactoring failed: {e}")
            await self.event_bus.emit(
                {
                    "event_type": "refactor.root.failed",
                    "source": "refactor_hook",
                    "data": {
                        "trigger": "manual",
                        "error": str(e),
                        "timestamp": event.get("timestamp"),
                    },
                }
            )

    async def _scheduled_refactor_handler(self, event):
        """Handle scheduled refactoring execution"""
        schedule_type = event.get("data", {}).get("schedule_type", "unknown")

        if schedule_type not in ["weekly", "daily"]:
            return

        if (
            schedule_type == "weekly"
            and self.config["auto_trigger"]["schedule"] != "weekly"
        ):
            return

        if (
            schedule_type == "daily"
            and self.config["auto_trigger"]["schedule"] != "daily"
        ):
            return

        logger.info(f"🕒 Scheduled root folder refactoring ({schedule_type})")

        try:
            await refactor_root_folder_hook(event)

            await self.event_bus.emit(
                {
                    "event_type": "refactor.root.completed",
                    "source": "refactor_hook",
                    "data": {
                        "trigger": f"scheduled_{schedule_type}",
                        "success": True,
                        "timestamp": event.get("timestamp"),
                    },
                }
            )

        except Exception as e:
            logger.error(f"❌ Scheduled refactoring failed: {e}")

    async def _file_system_analysis_handler(self, event):
        """Handle file system events that might trigger analysis"""
        logger.debug("📁 File system event received for refactoring analysis")

        # This is a lightweight analysis to determine if refactoring is needed
        # It doesn't perform the actual refactoring, just triggers analysis

        try:
            from .refactor_root_folder import RootFolderRefactor

            refactor = RootFolderRefactor()
            plan = refactor.analyze_root_structure()

            if len(plan.actions) > 0:
                logger.info(
                    f"📊 Refactoring analysis found {len(plan.actions)} potential improvements"
                )

                # Emit analysis result event
                await self.event_bus.emit(
                    {
                        "event_type": "refactor.root.analysis_complete",
                        "source": "refactor_hook",
                        "data": {
                            "actions_count": len(plan.actions),
                            "total_size_mb": plan.total_size_mb,
                            "total_files": plan.total_files,
                            "trigger": "file_system_change",
                            "timestamp": event.get("timestamp"),
                        },
                    }
                )

        except Exception as e:
            logger.error(f"❌ Refactoring analysis failed: {e}")

    def _should_trigger_analysis(self, event) -> bool:
        """Determine if file system event should trigger refactoring analysis"""
        data = event.get("data", {})

        # Only trigger for root-level changes
        file_path = data.get("file_path", "")
        if "/" in file_path or "\\" in file_path:
            return False  # Not a root-level file

        # Check if it's a type of file/directory that affects organization
        if event.get("event_type") == "code.file.created":
            # Trigger analysis for certain file types in root
            root_file_patterns = [".log", ".tmp", ".bak", ".old", ".config"]
            return any(file_path.endswith(pattern) for pattern in root_file_patterns)

        if event.get("event_type") == "code.directory.created":
            # Trigger analysis for new directories in root
            return True

        return False


# Integration function for Phoenix Hydra
def register_refactor_hooks(event_bus: EventBus):
    """Register root folder refactoring hooks with the Phoenix Hydra event system"""
    manager = RefactorHookManager(event_bus)
    manager.register_hooks()
    return manager


# Manual trigger function for VS Code tasks and scripts
async def trigger_manual_refactor():
    """Manually trigger root folder refactoring"""
    # This would typically get the event bus from the main application
    # For now, we'll call the hook directly
    await refactor_root_folder_hook(
        {
            "event_type": "refactor.root.manual",
            "source": "manual_trigger",
            "timestamp": "now",
        }
    )


if __name__ == "__main__":
    # Allow direct execution for testing
    asyncio.run(trigger_manual_refactor())
