"""
Metrics storage package.

This package provides storage and retrieval functionality for metrics data.
"""

from .time_series_storage import (
    RetentionPolicy,
    TimeSeriesStorage,
    InMemoryTimeSeriesStorage
)
from .query_engine import QueryEngine
from .retention_manager import RetentionManager, RetentionRule
from .storage_factory import StorageFactory, StorageBackend
from .metrics_storage_system import MetricsStorageSystem, create_metrics_storage_system
from .query_interface import (
    QueryFilter,
    AggregationQuery,
    QueryResult,
    AggregationResult,
    TimeRange,
    AggregationType
)

__all__ = [
    # Time series storage
    'RetentionPolicy',
    'TimeSeriesStorage',
    'InMemoryTimeSeriesStorage',
    
    # Query engine
    'QueryEngine',
    
    # Retention management
    'RetentionManager',
    'RetentionRule',
    
    # Storage factory
    'StorageFactory',
    'StorageBackend',
    
    # Query interface
    'QueryFilter',
    'AggregationQuery',
    'QueryResult',
    'AggregationResult',
    'TimeRange',
    'AggregationType',
    
    # Integrated storage system
    'MetricsStorageSystem',
    'create_metrics_storage_system'
]