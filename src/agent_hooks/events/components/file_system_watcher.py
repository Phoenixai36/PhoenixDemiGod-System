"""
File system watcher for the Agent Hooks Automation system.

This module implements a file system watcher that monitors for file changes
and generates events when files are created, modified, deleted, or renamed.
"""

import asyncio
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable, Awaitable
import fnmatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.agent_hooks.events.models import FileEvent, EventType
from src.agent_hooks.core.event_bus import EventBus
from src.agent_hooks.utils.logging import get_logger, ExecutionError


class FileSystemWatcherConfig:
    """Configuration for the file system watcher."""
    
    def __init__(
        self,
        paths: List[str],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        debounce_seconds: float = 0.5,
        compute_hash: bool = True,
        max_file_size_mb: int = 10
    ):
        """
        Initialize file system watcher configuration.
        
        Args:
            paths: List of paths to watch
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
            recursive: Whether to watch directories recursively
            debounce_seconds: Debounce period for file events
            compute_hash: Whether to compute file hashes
            max_file_size_mb: Maximum file size to compute hash for
        """
        self.paths = [Path(p).resolve() for p in paths]
        self.include_patterns = include_patterns or ["*"]
        self.exclude_patterns = exclude_patterns or []
        self.recursive = recursive
        self.debounce_seconds = debounce_seconds
        self.compute_hash = compute_hash
        self.max_file_size_mb = max_file_size_mb


class FileSystemWatcherEventHandler(FileSystemEventHandler):
    """Event handler for file system events."""
    
    def __init__(
        self,
        config: FileSystemWatcherConfig,
        event_callback: Callable[[FileEvent], Awaitable[None]]
    ):
        """
        Initialize the event handler.
        
        Args:
            config: File system watcher configuration
            event_callback: Callback function for file events
        """
        super().__init__()
        self.logger = get_logger("events.file_system_watcher")
        self.config = config
        self.event_callback = event_callback
        self.last_events: Dict[str, float] = {}  # path -> timestamp
        self.loop = asyncio.get_event_loop()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation event.
        
        Args:
            event: File system event
        """
        if not self._should_process_event(event):
            return
        
        path = Path(event.src_path).resolve()
        
        # Debounce events
        now = time.time()
        key = f"create:{path}"
        if key in self.last_events and now - self.last_events[key] < self.config.debounce_seconds:
            return
        
        self.last_events[key] = now
        
        # Create file event
        file_event = self._create_file_event(path, "create")
        
        # Schedule event callback
        self.loop.create_task(self._call_event_callback(file_event))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification event.
        
        Args:
            event: File system event
        """
        if not self._should_process_event(event):
            return
        
        path = Path(event.src_path).resolve()
        
        # Debounce events
        now = time.time()
        key = f"modify:{path}"
        if key in self.last_events and now - self.last_events[key] < self.config.debounce_seconds:
            return
        
        self.last_events[key] = now
        
        # Create file event
        file_event = self._create_file_event(path, "modify")
        
        # Schedule event callback
        self.loop.create_task(self._call_event_callback(file_event))
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """
        Handle file deletion event.
        
        Args:
            event: File system event
        """
        if not self._should_process_event(event):
            return
        
        path = Path(event.src_path).resolve()
        
        # Debounce events
        now = time.time()
        key = f"delete:{path}"
        if key in self.last_events and now - self.last_events[key] < self.config.debounce_seconds:
            return
        
        self.last_events[key] = now
        
        # Create file event
        file_event = self._create_file_event(path, "delete")
        
        # Schedule event callback
        self.loop.create_task(self._call_event_callback(file_event))
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """
        Handle file move/rename event.
        
        Args:
            event: File system event
        """
        if not self._should_process_event(event):
            return
        
        src_path = Path(event.src_path).resolve()
        dest_path = Path(event.dest_path).resolve()
        
        # Debounce events
        now = time.time()
        key = f"move:{src_path}:{dest_path}"
        if key in self.last_events and now - self.last_events[key] < self.config.debounce_seconds:
            return
        
        self.last_events[key] = now
        
        # Create file event
        file_event = FileEvent.create_rename_event(
            old_path=src_path,
            new_path=dest_path
        )
        
        # Schedule event callback
        self.loop.create_task(self._call_event_callback(file_event))
    
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """
        Check if an event should be processed.
        
        Args:
            event: File system event
            
        Returns:
            True if the event should be processed, False otherwise
        """
        # Ignore directory events
        if event.is_directory:
            return False
        
        path = Path(event.src_path).resolve()
        
        # Check include patterns
        included = any(fnmatch.fnmatch(path.name, pattern) for pattern in self.config.include_patterns)
        if not included:
            return False
        
        # Check exclude patterns
        excluded = any(fnmatch.fnmatch(path.name, pattern) for pattern in self.config.exclude_patterns)
        if excluded:
            return False
        
        return True
    
    def _create_file_event(self, path: Path, operation: str) -> FileEvent:
        """
        Create a file event.
        
        Args:
            path: File path
            operation: File operation (create, modify, delete)
            
        Returns:
            File event
        """
        content_hash = None
        size_bytes = None
        
        if operation != "delete" and path.exists() and path.is_file():
            try:
                size_bytes = path.stat().st_size
                
                # Compute hash if enabled and file is not too large
                if self.config.compute_hash and size_bytes <= self.config.max_file_size_mb * 1024 * 1024:
                    with open(path, "rb") as f:
                        content_hash = hashlib.md5(f.read()).hexdigest()
            except Exception as e:
                self.logger.warning(
                    f"Error getting file info: {e}",
                    {"path": str(path), "operation": operation}
                )
        
        if operation == "create":
            return FileEvent.create_create_event(
                file_path=path,
                content_hash=content_hash,
                data={"size_bytes": size_bytes}
            )
        elif operation == "modify":
            return FileEvent.create_modify_event(
                file_path=path,
                content_hash=content_hash,
                data={"size_bytes": size_bytes}
            )
        elif operation == "delete":
            return FileEvent.create_delete_event(
                file_path=path
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _call_event_callback(self, event: FileEvent) -> None:
        """
        Call the event callback function.
        
        Args:
            event: File event
        """
        try:
            await self.event_callback(event)
        except Exception as e:
            self.logger.error(
                f"Error in event callback: {e}",
                {"event_id": event.id, "event_type": event.type.value},
                e
            )


class FileSystemWatcher:
    """
    File system watcher that monitors for file changes.
    
    This class uses the watchdog library to monitor file system events
    and generates events when files are created, modified, deleted, or renamed.
    """
    
    def __init__(self, event_bus: EventBus, config: FileSystemWatcherConfig):
        """
        Initialize the file system watcher.
        
        Args:
            event_bus: Event bus to publish events to
            config: File system watcher configuration
        """
        self.logger = get_logger("events.file_system_watcher")
        self.event_bus = event_bus
        self.config = config
        self.observer = Observer()
        self.event_handler = FileSystemWatcherEventHandler(config, self._on_file_event)
        self.running = False
    
    async def start(self) -> None:
        """
        Start the file system watcher.
        
        This method starts watching the configured paths for file system events.
        """
        if self.running:
            return
        
        # Schedule observers for each path
        for path in self.config.paths:
            if not path.exists():
                self.logger.warning(
                    f"Path does not exist: {path}",
                    {"path": str(path)}
                )
                continue
            
            self.observer.schedule(
                self.event_handler,
                str(path),
                recursive=self.config.recursive
            )
        
        # Start the observer
        self.observer.start()
        self.running = True
        
        self.logger.info(
            "File system watcher started",
            {"paths": [str(p) for p in self.config.paths]}
        )
    
    async def stop(self) -> None:
        """
        Stop the file system watcher.
        
        This method stops watching for file system events.
        """
        if not self.running:
            return
        
        # Stop the observer
        self.observer.stop()
        self.observer.join()
        self.running = False
        
        self.logger.info("File system watcher stopped")
    
    async def _on_file_event(self, event: FileEvent) -> None:
        """
        Handle a file event.
        
        Args:
            event: File event
        """
        try:
            # Publish the event to the event bus
            await self.event_bus.publish(event)
            
            self.logger.debug(
                f"Published file event: {event.type.value}",
                {"event_id": event.id, "file_path": str(event.file_path)}
            )
        except Exception as e:
            self.logger.error(
                f"Error publishing file event: {e}",
                {"event_id": event.id, "event_type": event.type.value},
                e
            )