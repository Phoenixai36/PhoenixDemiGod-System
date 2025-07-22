"""
Factory for creating time series storage instances.

This module provides a factory for creating different types of
time series storage backends with appropriate configurations.
"""

import logging
from typing import Dict, Any, Optional

from .time_series_storage import (
    TimeSeriesStorage,
    MemoryTimeSeriesStorage,
    SQLiteTimeSeriesStorage,
    FileTimeSeriesStorage,
    StorageBackend
)
from .retention_policy import RetentionManager, create_retention_manager
from .query_engine import QueryEngine


class StorageFactory:
    """Factory for creating time series storage instances."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_storage(self, backend: StorageBackend, config: Dict[str, Any] = None) -> TimeSeriesStorage:
        """Create a time series storage instance."""
        config = config or {}
        
        if backend == StorageBackend.MEMORY:
            return MemoryTimeSeriesStorage(config)
        elif backend == StorageBackend.SQLITE:
            return SQLiteTimeSeriesStorage(config)
        elif backend == StorageBackend.FILE:
            return FileTimeSeriesStorage(config)
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")
    
    def create_storage_from_config(self, config: Dict[str, Any]) -> TimeSeriesStorage:
        """Create storage from configuration dictionary."""
        backend_name = config.get("backend", "memory")
        
        try:
            backend = StorageBackend(backend_name)
        except ValueError:
            self.logger.error(f"Unknown storage backend: {backend_name}")
            backend = StorageBackend.MEMORY
        
        storage_config = config.get("config", {})
        return self.create_storage(backend, storage_config)
    
    def create_complete_system(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a complete storage system with storage, retention, and query engine."""
        config = config or {}
        
        # Create storage
        storage_config = config.get("storage", {"backend": "memory"})
        storage = self.create_storage_from_config(storage_config)
        
        # Create retention manager
        retention_config = config.get("retention", {"with_defaults": True})
        retention_manager = create_retention_manager(
            storage, 
            with_defaults=retention_config.get("with_defaults", True)
        )
        
        # Configure retention manager
        if "cleanup_interval_hours" in retention_config:
            from datetime import timedelta
            retention_manager.cleanup_interval = timedelta(
                hours=retention_config["cleanup_interval_hours"]
            )
        
        # Create query engine
        query_engine = QueryEngine(storage)
        
        return {
            "storage": storage,
            "retention_manager": retention_manager,
            "query_engine": query_engine
        }
    
    def get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default configurations for different storage backends."""
        return {
            "memory": {
                "backend": "memory",
                "config": {
                    "max_points_per_metric": 10000
                }
            },
            "sqlite": {
                "backend": "sqlite",
                "config": {
                    "db_path": "metrics.db"
                }
            },
            "file": {
                "backend": "file",
                "config": {
                    "storage_dir": "metrics_data"
                }
            },
            "production": {
                "backend": "sqlite",
                "config": {
                    "db_path": "/var/lib/metrics/metrics.db"
                },
                "retention": {
                    "with_defaults": True,
                    "cleanup_interval_hours": 1
                }
            },
            "development": {
                "backend": "memory",
                "config": {
                    "max_points_per_metric": 5000
                },
                "retention": {
                    "with_defaults": False,
                    "cleanup_interval_hours": 24
                }
            },
            "testing": {
                "backend": "memory",
                "config": {
                    "max_points_per_metric": 1000
                },
                "retention": {
                    "with_defaults": False
                }
            }
        }
    
    def create_for_environment(self, environment: str = "development") -> Dict[str, Any]:
        """Create storage system for a specific environment."""
        configs = self.get_default_configs()
        
        if environment not in configs:
            self.logger.warning(f"Unknown environment: {environment}, using development")
            environment = "development"
        
        config = configs[environment]
        return self.create_complete_system(config)


# Global factory instance
storage_factory = StorageFactory()


def create_storage_system(backend: str = "memory", 
                         config: Dict[str, Any] = None,
                         with_retention: bool = True,
                         with_query_engine: bool = True) -> Dict[str, Any]:
    """Convenience function to create a complete storage system."""
    try:
        backend_enum = StorageBackend(backend)
    except ValueError:
        logging.getLogger(__name__).error(f"Unknown backend: {backend}, using memory")
        backend_enum = StorageBackend.MEMORY
    
    storage = storage_factory.create_storage(backend_enum, config)
    
    result = {"storage": storage}
    
    if with_retention:
        retention_manager = create_retention_manager(storage, with_defaults=True)
        result["retention_manager"] = retention_manager
    
    if with_query_engine:
        query_engine = QueryEngine(storage)
        result["query_engine"] = query_engine
    
    return result