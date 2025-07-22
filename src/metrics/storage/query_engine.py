"""
Query engine for metrics data.

This module provides a query interface for retrieving and analyzing metrics data
from the time series storage.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

from ..models import MetricValue
from .time_series_storage import TimeSeriesStorage


class QueryEngine:
    """Query engine for metrics data."""
    
    def __init__(self, storage: TimeSeriesStorage):
        """
        Initialize the query engine.
        
        Args:
            storage: The time series storage to query
        """
        self.storage = storage
        self.logger = logging.getLogger("metrics.query_engine")
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: Optional[timedelta] = None,
        labels: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MetricValue]:
        """
        Query metrics with flexible time range options.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Optional start of time range
            end_time: Optional end of time range
            duration: Optional duration from end_time (or now) backwards
            labels: Optional label filters
            aggregation: Optional aggregation function (avg, sum, min, max, last)
            limit: Optional limit on number of results
            
        Returns:
            List of matching MetricValue objects
            
        Note:
            Time range can be specified in two ways:
            1. Explicit start_time and end_time
            2. end_time (or now) and duration
        """
        # Determine time range
        if end_time is None:
            end_time = datetime.now()
            
        if start_time is None and duration is not None:
            start_time = end_time - duration
        elif start_time is None:
            # Default to last hour
            start_time = end_time - timedelta(hours=1)
        
        # Validate time range
        if start_time > end_time:
            self.logger.warning(f"Invalid time range: {start_time} > {end_time}")
            return []
        
        # Query storage
        return await self.storage.query_metrics(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            labels=labels,
            aggregation=aggregation,
            limit=limit
        )
    
    async def query_latest(
        self,
        metric_name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Optional[MetricValue]:
        """
        Query the latest value for a metric.
        
        Args:
            metric_name: Name of the metric to query
            labels: Optional label filters
            
        Returns:
            The latest MetricValue or None if not found
        """
        # Query with limit=1 and sort by timestamp desc
        results = await self.storage.query_metrics(
            metric_name=metric_name,
            start_time=datetime.now() - timedelta(days=30),  # Reasonable default
            end_time=datetime.now(),
            labels=labels,
            aggregation="last",
            limit=1
        )
        
        return results[0] if results else None
    
    async def query_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        step: timedelta,
        labels: Optional[Dict[str, str]] = None,
        aggregation: str = "avg"
    ) -> List[Tuple[datetime, Union[float, int, str]]]:
        """
        Query metrics with regular time intervals.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Start of time range
            end_time: End of time range
            step: Time interval between points
            labels: Optional label filters
            aggregation: Aggregation function (avg, sum, min, max, last)
            
        Returns:
            List of (timestamp, value) tuples at regular intervals
        """
        results = []
        current_time = start_time
        
        while current_time <= end_time:
            # Query for this interval
            interval_end = min(current_time + step, end_time)
            
            metrics = await self.storage.query_metrics(
                metric_name=metric_name,
                start_time=current_time,
                end_time=interval_end,
                labels=labels,
                aggregation=aggregation,
                limit=1
            )
            
            if metrics:
                results.append((current_time, metrics[0].value))
            else:
                # No data for this interval
                results.append((current_time, None))
                
            current_time += step
            
        return results
    
    async def get_metric_names(self) -> List[str]:
        """
        Get all available metric names.
        
        Returns:
            List of metric names
        """
        return await self.storage.get_metric_names()
    
    async def get_label_keys(self, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available label keys.
        
        Args:
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label keys
        """
        return await self.storage.get_label_keys(metric_name)
    
    async def get_label_values(self, label_key: str, metric_name: Optional[str] = None) -> List[str]:
        """
        Get all available values for a label key.
        
        Args:
            label_key: The label key to get values for
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label values
        """
        return await self.storage.get_label_values(label_key, metric_name)
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the storage.
        
        Returns:
            Dictionary with storage statistics
        """
        return await self.storage.get_storage_stats()