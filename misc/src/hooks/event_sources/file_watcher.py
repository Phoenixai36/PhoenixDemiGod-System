"""
File System Watcher for Agent Hooks Automation

This module implements efficient file change detection with debouncing,
file type filtering, and pattern matching for the Phoenix DemiGod system.
Supports monitoring Terraform files, Windmill scripts, and configuration changes.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import fnmatch
import hashlib

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    raise ImportError("watchdog is required. Install with: pip install watchdog")

from ..core.events import Event, EventBus
from ..core.config import FileWatcherConfig


class FileChangeType(Enum):
    """Types of file changes that can be detected."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChangeEvent:
    """Represents a file change event with metadata."""
    path: Path
    change_type: FileChangeType
    timestamp: float
    file_hash: Optional[str] = None
    old_path: Optional[Path] = None  # For move events
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileWatcherEventHandler(FileSystemEventHandler):
    """Custom event handler for file system changes."""
    
    def __init__(self, watcher: 'FileSystemWatcher'):
        super().__init__()
        self.watcher = watcher
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory:
            self.watcher._queue_change(
                Path(event.src_path), 
                FileChangeType.CREATED
            )
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory:
            self.watcher._queue_change(
                Path(event.src_path), 
                FileChangeType.MODIFIED
            )
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory:
            self.watcher._queue_change(
                Path(event.src_path), 
                FileChangeType.DELETED
            )
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events."""
        if not event.is_directory:
            self.watcher._queue_change(
                Path(event.dest_path), 
                FileChangeType.MOVED,
                old_path=Path(event.src_path)
            )


class FileSystemWatcher:
    """
    Advanced file system watcher with debouncing, filtering, and pattern matching.
    
    Features:
    - Debounced change detection to avoid duplicate events
    - File type filtering (e.g., .py, .tf, .yaml)
    - Pattern matching for specific directories
    - Hash-based change detection for content verification
    - Support for Terraform, Windmill, and configuration files
    """
    
    def __init__(self, config: FileWatcherConfig, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # Internal state
        self.observer = Observer()
        self.event_handler = FileWatcherEventHandler(self)
        self.pending_changes: Dict[Path, FileChangeEvent] = {}
        self.file_hashes: Dict[Path, str] = {}
        self.debounce_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile file patterns for efficient matching."""
        self.include_patterns = [
            pattern.strip() for pattern in self.config.include_patterns
        ]
        self.exclude_patterns = [
            pattern.strip() for pattern in self.config.exclude_patterns
        ]
        
        # Default patterns for Phoenix DemiGod system
        if not self.include_patterns:
            self.include_patterns = [
                "*.py",           # Python files
                "*.tf",           # Terraform files
                "*.yaml",         # YAML configurations
                "*.yml",          # YAML configurations
                "*.json",         # JSON configurations
                "*.toml",         # TOML configurations
                "*.js",           # Windmill JavaScript
                "*.ts",           # Windmill TypeScript
                "*.sql",          # SQL scripts
                "*.sh",           # Shell scripts
                "*.ps1",          # PowerShell scripts
                "Dockerfile*",    # Docker files
                "*.env*",         # Environment files
            ]
        
        if not self.exclude_patterns:
            self.exclude_patterns = [
                "*.pyc",
                "__pycache__/*",
                ".git/*",
                ".vscode/*",
                "node_modules/*",
                "*.log",
                "*.tmp",
                ".terraform/*",
                "terraform.tfstate*",
            ]
    
    def _should_watch_file(self, file_path: Path) -> bool:
        """Determine if a file should be watched based on patterns."""
        file_str = str(file_path)
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_str, pattern):
                return False
        
        # Check include patterns
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(file_str, pattern):
                return True
        
        return False
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA-256 hash of file content."""
        try:
            if not file_path.exists():
                return None
            
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return None
    
    def _queue_change(self, file_path: Path, change_type: FileChangeType, 
                     old_path: Optional[Path] = None):
        """Queue a file change for debounced processing."""
        if not self._should_watch_file(file_path):
            return
        
        # Calculate file hash for content verification
        file_hash = None
        if change_type in [FileChangeType.CREATED, FileChangeType.MODIFIED]:
            file_hash = self._calculate_file_hash(file_path)
            
            # Skip if content hasn't actually changed
            if change_type == FileChangeType.MODIFIED:
                old_hash = self.file_hashes.get(file_path)
                if old_hash == file_hash:
                    return  # No actual content change
        
        # Create change event
        change_event = FileChangeEvent(
            path=file_path,
            change_type=change_type,
            timestamp=time.time(),
            file_hash=file_hash,
            old_path=old_path,
            metadata=self._extract_file_metadata(file_path)
        )
        
        # Queue for debounced processing
        self.pending_changes[file_path] = change_event
        
        # Update hash cache
        if file_hash:
            self.file_hashes[file_path] = file_hash
        elif change_type == FileChangeType.DELETED:
            self.file_hashes.pop(file_path, None)
        
        # Start or restart debounce timer
        if self.debounce_task:
            self.debounce_task.cancel()
        
        self.debounce_task = asyncio.create_task(
            self._debounce_changes()
        )
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from file path and content."""
        metadata = {
            "file_extension": file_path.suffix,
            "file_name": file_path.name,
            "directory": str(file_path.parent),
        }
        
        # Categorize file types for Phoenix DemiGod system
        if file_path.suffix == '.tf':
            metadata["category"] = "terraform"
            metadata["infrastructure"] = True
        elif file_path.suffix in ['.js', '.ts'] and 'windmill' in str(file_path):
            metadata["category"] = "windmill"
            metadata["workflow"] = True
        elif file_path.suffix == '.py':
            metadata["category"] = "python"
            metadata["code"] = True
        elif file_path.suffix in ['.yaml', '.yml', '.json', '.toml']:
            metadata["category"] = "configuration"
            metadata["config"] = True
        elif 'Dockerfile' in file_path.name:
            metadata["category"] = "container"
            metadata["infrastructure"] = True
        
        return metadata
    
    async def _debounce_changes(self):
        """Process queued changes after debounce delay."""
        await asyncio.sleep(self.config.debounce_delay)
        
        if not self.pending_changes:
            return
        
        # Process all pending changes
        changes_to_process = list(self.pending_changes.values())
        self.pending_changes.clear()
        
        for change in changes_to_process:
            await self._process_file_change(change)
    
    async def _process_file_change(self, change: FileChangeEvent):
        """Process a single file change and emit events."""
        try:
            # Create normalized event for the event bus
            event_data = {
                "file_path": str(change.path),
                "change_type": change.change_type.value,
                "timestamp": change.timestamp,
                "file_hash": change.file_hash,
                "metadata": change.metadata
            }
            
            if change.old_path:
                event_data["old_path"] = str(change.old_path)
            
            # Determine event type based on file category
            event_type = self._determine_event_type(change)
            
            # Create and emit event
            event = Event(
                event_type=event_type,
                source="file_watcher",
                timestamp=change.timestamp,
                data=event_data,
                metadata={
                    "component": "file_system_watcher",
                    "category": change.metadata.get("category", "unknown")
                }
            )
            
            await self.event_bus.emit(event)
            
            self.logger.info(
                f"File change detected: {change.path} ({change.change_type.value})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process file change {change.path}: {e}")
    
    def _determine_event_type(self, change: FileChangeEvent) -> str:
        """Determine the appropriate event type based on file metadata."""
        category = change.metadata.get("category", "unknown")
        change_type = change.change_type.value
        
        # Map to specific event types for different file categories
        event_type_map = {
            "terraform": f"infrastructure.file.{change_type}",
            "windmill": f"workflow.file.{change_type}",
            "python": f"code.file.{change_type}",
            "configuration": f"config.file.{change_type}",
            "container": f"container.file.{change_type}",
        }
        
        return event_type_map.get(category, f"file.{change_type}")
    
    async def start(self):
        """Start the file system watcher."""
        if self.is_running:
            return
        
        try:
            # Add watch paths
            for watch_path in self.config.watch_paths:
                path = Path(watch_path)
                if path.exists():
                    self.observer.schedule(
                        self.event_handler,
                        str(path),
                        recursive=self.config.recursive
                    )
                    self.logger.info(f"Watching path: {path}")
                else:
                    self.logger.warning(f"Watch path does not exist: {path}")
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            self.logger.info("File system watcher started")
            
        except Exception as e:
            self.logger.error(f"Failed to start file system watcher: {e}")
            raise
    
    async def stop(self):
        """Stop the file system watcher."""
        if not self.is_running:
            return
        
        try:
            # Cancel debounce task
            if self.debounce_task:
                self.debounce_task.cancel()
            
            # Stop observer
            self.observer.stop()
            self.observer.join()
            
            self.is_running = False
            self.logger.info("File system watcher stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop file system watcher: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current status of the file watcher."""
        return {
            "is_running": self.is_running,
            "watched_paths": [str(path) for path in self.config.watch_paths],
            "pending_changes": len(self.pending_changes),
            "cached_hashes": len(self.file_hashes),
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
        }