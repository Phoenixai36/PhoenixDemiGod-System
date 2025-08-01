"""
Time series data storage for metrics.

This module provides a storage system for time series metrics data with
configurable retention policies and query capabilities.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
import heapq
import json
import os
import sys

from ..models import MetricValue, MetricType


class RetentionPolicy:
    """Defines how long metrics data should be stored."""
    
    def __init__(
        self,
        name: str,
        retention_period: timedelta,
        downsampling_interval: Optional[timedelta] = None,
        max_points_per_series: Optional[int] = None
    ):
        """
        Initialize a retention policy.
        
        Args:
            name: Policy name
            retention_period: How long to keep data
            downsampling_interval: Optional interval for downsampling data
            max_points_per_series: Optional maximum number of points per series
        """
        self.name = name
        self.retention_period = retention_period
        self.downsampling_interval = downsampling_interval
        self.max_points_per_series = max_points_per_series
    
    def should_retain(self, timestamp: datetime, current_time: datetime) -> bool:
        """Check if a data point should be retained based on its timestamp."""
        return current_time - timestamp <= self.retention_period
    
    def should_downsample(self, points: List[Tuple[datetime, Any]]) -> bool:
        """Check if a series should be downsampled based on the policy."""
        if self.max_points_per_series and len(points) > self.max_points_per_series:
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary for serialization."""
        return {
            "name": self.name,
            "retention_period_seconds": self.retention_period.total_seconds(),
            "downsampling_interval_seconds": (
                self.downsampling_interval.total_seconds() 
                if self.downsampling_interval else None
            ),
            "max_points_per_series": self.max_points_per_series
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RetentionPolicy":
        """Create policy from dictionary."""
        return cls(
            name=data["name"],
            retention_period=timedelta(seconds=data["retention_period_seconds"]),
            downsampling_interval=(
                timedelta(seconds=data["downsampling_interval_seconds"])
                if data.get("downsampling_interval_seconds") else None
            ),
            max_points_per_series=data.get("max_points_per_series")
        )

c
lass TimeSeriesStorage(ABC):
    """Abstract base class for time series data storage."""
    
    @abstractmethod
    async def store_metrics(self, metrics: List[MetricValue]) -> bool:
        """
        Store multiple metrics.
        
        Args:
            metrics: List of metrics to store
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MetricValue]:
        """
        Query metrics by name, time range, and optional labels.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Start of time range
            end_time: End of time range
            labels: Optional label filters
            aggregation: Optional aggregation function (avg, sum, min, max)
            limit: Optional limit on number of results
            
        Returns:
            List of matching MetricValue objects
        """
        pass
    
    @abstractmethod
    async def get_metric_names(self) -> List[str]:
        """
        Get all available metric names.
        
        Returns:
            List of metric names
        """
        pass
    
    @abstractmethod
    async def get_label_keys(self, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available label keys.
        
        Args:
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label keys
        """
        pass
    
    @abstractmethod
    async def get_label_values(self, label_key: str, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available values for a label key.
        
        Args:
            label_key: The label key to get values for
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label values
        """
        pass
    
    @abstractmethod
    async def apply_retention_policy(self) -> int:
        """
        Apply retention policy to stored metrics.
        
        Returns:
            Number of metrics removed
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the storage.
        
        Returns:
            Dictionary with storage statistics
        """
        pass

cla
ss InMemoryTimeSeriesStorage(TimeSeriesStorage):
    """In-memory implementation of time series storage."""
    
    def __init__(self, retention_policy: RetentionPolicy):
        """
        Initialize in-memory storage.
        
        Args:
            retention_policy: The retention policy to apply
        """
        self.retention_policy = retention_policy
        self.logger = logging.getLogger("metrics.storage.memory")
        
        # Main storage structure:
        # {metric_name: {label_hash: [(timestamp, value), ...]}}
        self._data: Dict[str, Dict[str, List[Tuple[datetime, Union[float, int, str]]]]] = {}
        
        # Label key-value mappings for efficient querying
        # {metric_name: {label_key: {label_value: set(label_hashes)}}}
        self._label_index: Dict[str, Dict[str, Dict[str, Set[str]]]] = {}
        
        # Track last cleanup time
        self._last_cleanup = datetime.now()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    def _hash_labels(self, labels: Dict[str, str]) -> str:
        """Create a hash from label dictionary for storage."""
        # Sort to ensure consistent hashing
        sorted_items = sorted(labels.items())
        return json.dumps(sorted_items)
    
    def _match_labels(self, stored_labels_hash: str, query_labels: Dict[str, str]) -> bool:
        """Check if stored labels match query labels."""
        if not query_labels:
            return True
            
        # Deserialize the stored labels hash
        stored_items = json.loads(stored_labels_hash)
        stored_labels = dict(stored_items)
        
        # Check if all query labels are in stored labels with matching values
        return all(
            key in stored_labels and stored_labels[key] == value
            for key, value in query_labels.items()
        )
    
    def _update_label_index(self, metric_name: str, labels: Dict[str, str], label_hash: str) -> None:
        """Update the label index for efficient querying."""
        if metric_name not in self._label_index:
            self._label_index[metric_name] = {}
            
        for key, value in labels.items():
            if key not in self._label_index[metric_name]:
                self._label_index[metric_name][key] = {}
                
            if value not in self._label_index[metric_name][key]:
                self._label_index[metric_name][key][value] = set()
                
            self._label_index[metric_name][key][value].add(label_hash)    
 
   async def store_metrics(self, metrics: List[MetricValue]) -> bool:
        """Store multiple metrics in memory."""
        if not metrics:
            return True
            
        async with self._lock:
            for metric in metrics:
                # Initialize storage for this metric if needed
                if metric.name not in self._data:
                    self._data[metric.name] = {}
                
                # Hash the labels for storage
                label_hash = self._hash_labels(metric.labels)
                
                # Initialize series for this label combination if needed
                if label_hash not in self._data[metric.name]:
                    self._data[metric.name][label_hash] = []
                
                # Store the data point
                self._data[metric.name][label_hash].append((metric.timestamp, metric.value))
                
                # Update label index
                self._update_label_index(metric.name, metric.labels, label_hash)
            
            # Check if we should apply retention policy
            current_time = datetime.now()
            if (current_time - self._last_cleanup).total_seconds() > 3600:  # Every hour
                await self.apply_retention_policy()
                self._last_cleanup = current_time
                
            return True
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MetricValue]:
        """Query metrics from memory storage."""
        if metric_name not in self._data:
            return []
            
        results = []
        
        async with self._lock:
            # Find matching label combinations
            matching_hashes = set()
            
            if labels and metric_name in self._label_index:
                # Use label index for efficient filtering
                candidate_hashes = None
                
                for key, value in labels.items():
                    if key in self._label_index[metric_name] and value in self._label_index[metric_name][key]:
                        hashes = self._label_index[metric_name][key][value]
                        if candidate_hashes is None:
                            candidate_hashes = hashes.copy()
                        else:
                            candidate_hashes &= hashes
                    else:
                        # No matches for this label
                        candidate_hashes = set()
                        break
                
                if candidate_hashes:
                    matching_hashes = candidate_hashes
            else:
                # No label filtering, use all series
                matching_hashes = set(self._data[metric_name].keys())   
         
            # Process each matching series
            for label_hash in matching_hashes:
                # Get the data points
                points = self._data[metric_name][label_hash]
                
                # Filter by time range
                filtered_points = [
                    (ts, val) for ts, val in points
                    if start_time <= ts <= end_time
                ]
                
                if not filtered_points:
                    continue
                
                # Apply aggregation if requested
                if aggregation and filtered_points:
                    values = [val for _, val in filtered_points]
                    timestamp = max(ts for ts, _ in filtered_points)
                    
                    if aggregation == "avg" and values:
                        try:
                            # Only numeric values can be averaged
                            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                            if numeric_values:
                                value = sum(numeric_values) / len(numeric_values)
                                # Deserialize the label hash to get original labels
                                labels_dict = dict(json.loads(label_hash))
                                results.append(MetricValue(
                                    name=metric_name,
                                    value=value,
                                    timestamp=timestamp,
                                    labels=labels_dict
                                ))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Cannot average non-numeric values for {metric_name}")
                    
                    elif aggregation == "sum" and values:
                        try:
                            # Only numeric values can be summed
                            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                            if numeric_values:
                                value = sum(numeric_values)
                                # Deserialize the label hash to get original labels
                                labels_dict = dict(json.loads(label_hash))
                                results.append(MetricValue(
                                    name=metric_name,
                                    value=value,
                                    timestamp=timestamp,
                                    labels=labels_dict
                                ))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Cannot sum non-numeric values for {metric_name}")
                    
                    elif aggregation == "min" and values:
                        try:
                            # Only numeric values can be compared
                            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                            if numeric_values:
                                value = min(numeric_values)
                                # Deserialize the label hash to get original labels
                                labels_dict = dict(json.loads(label_hash))
                                results.append(MetricValue(
                                    name=metric_name,
                                    value=value,
                                    timestamp=timestamp,
                                    labels=labels_dict
                                ))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Cannot find min of non-numeric values for {metric_name}")
                    
                    elif aggregation == "max" and values:
                        try:
                            # Only numeric values can be compared
                            numeric_values = [float(v) for v in values if isinstance(v, (int, float))]
                            if numeric_values:
                                value = max(numeric_values)
                                # Deserialize the label hash to get original labels
                                labels_dict = dict(json.loads(label_hash))
                                results.append(MetricValue(
                                    name=metric_name,
                                    value=value,
                                    timestamp=timestamp,
                                    labels=labels_dict
                                ))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Cannot find max of non-numeric values for {metric_name}")
                    
                    elif aggregation == "last" and values:
                        # Get the most recent value
                        last_point = max(filtered_points, key=lambda x: x[0])
                        # Deserialize the label hash to get original labels
                        labels_dict = dict(json.loads(label_hash))
                        results.append(MetricValue(
                            name=metric_name,
                            value=last_point[1],
                            timestamp=last_point[0],
                            labels=labels_dict
                        ))
                else:
                    # No aggregation, return all points
                    labels_dict = dict(json.loads(label_hash))
                    for ts, val in filtered_points:
                        results.append(MetricValue(
                            name=metric_name,
                            value=val,
                            timestamp=ts,
                            labels=labels_dict
                        ))     
       
            # Apply limit if specified
            if limit and len(results) > limit:
                # Sort by timestamp (newest first) and take the limit
                results.sort(key=lambda x: x.timestamp, reverse=True)
                results = results[:limit]
                
            return results
    
    async def get_metric_names(self) -> List[str]:
        """Get all available metric names."""
        async with self._lock:
            return list(self._data.keys())
    
    async def get_label_keys(self, metric_name: Optional[str] = None) -> List[str]:
        """Get all available label keys."""
        async with self._lock:
            keys = set()
            
            if metric_name:
                if metric_name in self._label_index:
                    keys.update(self._label_index[metric_name].keys())
            else:
                for metric_index in self._label_index.values():
                    keys.update(metric_index.keys())
                    
            return list(keys)
    
    async def get_label_values(self, label_key: str, metric_name: Optional[str] = None) -> List[str]:
        """Get all available values for a label key."""
        async with self._lock:
            values = set()
            
            if metric_name:
                if metric_name in self._label_index and label_key in self._label_index[metric_name]:
                    values.update(self._label_index[metric_name][label_key].keys())
            else:
                for metric_index in self._label_index.values():
                    if label_key in metric_index:
                        values.update(metric_index[label_key].keys())
                        
            return list(values)
    
    async def apply_retention_policy(self) -> int:
        """Apply retention policy to stored metrics."""
        removed_count = 0
        current_time = datetime.now()
        
        async with self._lock:
            for metric_name, series_dict in list(self._data.items()):
                for label_hash, points in list(series_dict.items()):
                    # Filter points based on retention policy
                    retained_points = [
                        (ts, val) for ts, val in points
                        if self.retention_policy.should_retain(ts, current_time)
                    ]
                    
                    removed_count += len(points) - len(retained_points)          
          
                    if not retained_points:
                        # Remove empty series
                        del self._data[metric_name][label_hash]
                        
                        # Clean up label index
                        labels_dict = dict(json.loads(label_hash))
                        for key, value in labels_dict.items():
                            if (key in self._label_index.get(metric_name, {}) and 
                                value in self._label_index[metric_name].get(key, {}) and
                                label_hash in self._label_index[metric_name][key].get(value, set())):
                                self._label_index[metric_name][key][value].remove(label_hash)
                                
                                # Clean up empty sets
                                if not self._label_index[metric_name][key][value]:
                                    del self._label_index[metric_name][key][value]
                                
                                if not self._label_index[metric_name][key]:
                                    del self._label_index[metric_name][key]
                    else:
                        # Update with retained points
                        self._data[metric_name][label_hash] = retained_points
                        
                        # Apply downsampling if needed
                        if (self.retention_policy.should_downsample(retained_points) and 
                            self.retention_policy.downsampling_interval and 
                            self.retention_policy.max_points_per_series):
                            
                            # Sort by timestamp
                            retained_points.sort(key=lambda x: x[0])
                            
                            # Downsample by keeping every Nth point
                            target_count = self.retention_policy.max_points_per_series
                            if len(retained_points) > target_count:
                                step = len(retained_points) // target_count
                                downsampled = [retained_points[i] for i in range(0, len(retained_points), step)]
                                
                                # Always keep the most recent point
                                if retained_points[-1] not in downsampled:
                                    downsampled.append(retained_points[-1])
                                    
                                self._data[metric_name][label_hash] = downsampled
                                removed_count += len(retained_points) - len(downsampled)
                
                # Remove empty metrics
                if not self._data[metric_name]:
                    del self._data[metric_name]
                    if metric_name in self._label_index:
                        del self._label_index[metric_name]
                        
        return removed_count
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about the storage."""
        async with self._lock:
            metric_count = len(self._data)
            series_count = sum(len(series) for series in self._data.values())
            point_count = sum(
                sum(len(points) for points in series.values())
                for series in self._data.values()
            ) 
           
            # Calculate approximate memory usage
            # This is a rough estimate
            memory_bytes = (
                # Data structure overhead
                sys.getsizeof(self._data) +
                sys.getsizeof(self._label_index) +
                
                # Metric names
                sum(sys.getsizeof(name) for name in self._data) +
                
                # Label hashes
                sum(
                    sum(sys.getsizeof(hash_key) for hash_key in series)
                    for series in self._data.values()
                ) +
                
                # Data points (timestamp + value)
                sum(
                    sum(
                        sum(sys.getsizeof(ts) + sys.getsizeof(val) for ts, val in points)
                        for points in series.values()
                    )
                    for series in self._data.values()
                )
            )
            
            return {
                "metric_count": metric_count,
                "series_count": series_count,
                "point_count": point_count,
                "memory_bytes": memory_bytes,
                "retention_policy": self.retention_policy.to_dict()
            }