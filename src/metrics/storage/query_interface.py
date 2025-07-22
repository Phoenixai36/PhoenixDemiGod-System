"""
Query interface for metrics data with advanced filtering and aggregation.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..models import MetricValue
from .time_series_storage import TimeSeriesStorage


class AggregationType(Enum):
    """Types of metric aggregations."""
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    STDDEV = "stddev"
    PERCENTILE_50 = "p50"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


class TimeRange(Enum):
    """Predefined time ranges."""
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"


@dataclass
class QueryFilter:
    """Filter criteria for metric queries."""
    metric_names: Optional[List[str]] = None
    metric_pattern: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    label_patterns: Optional[Dict[str, str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_range: Optional[TimeRange] = None
    limit: Optional[int] = None


@dataclass
class AggregationQuery:
    """Query for aggregated metrics."""
    metric_name: str
    aggregation: AggregationType
    interval: timedelta
    filters: Optional[QueryFilter] = None
    group_by_labels: Optional[List[str]] = None


@dataclass
class QueryResult:
    """Result of a metrics query."""
    metrics: List[MetricValue]
    total_count: int
    query_time_ms: float
    filters_applied: Dict[str, Any]


@dataclass
class AggregationResult:
    """Result of an aggregation query."""
    data_points: List[Tuple[datetime, float]]
    aggregation_type: AggregationType
    interval: timedelta
    total_samples: int
    query_time_ms: float
    group_by: Optional[Dict[str, Any]] = None


class MetricsQueryInterface:
    """Advanced query interface for metrics data."""
    
    def __init__(self, storage: TimeSeriesStorage):
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    def query(self, filters: QueryFilter) -> QueryResult:
        """
        Execute a metrics query with advanced filtering.
        
        Args:
            filters: Query filter criteria
            
        Returns:
            QueryResult with matching metrics
        """
        start_time = datetime.now()
        
        try:
            # Convert time range to actual times if specified
            if filters.time_range:
                end_time = datetime.now()
                start_time_filter = self._time_range_to_datetime(filters.time_range, end_time)
                
                if not filters.start_time:
                    filters.start_time = start_time_filter
                if not filters.end_time:
                    filters.end_time = end_time
            
            # Handle metric patterns
            metric_names = filters.metric_names
            if filters.metric_pattern and not metric_names:
                metric_names = self._find_metrics_by_pattern(filters.metric_pattern)
            
            all_metrics = []
            
            if metric_names:
                # Query each metric name
                for metric_name in metric_names:
                    metrics = self.storage.query_metrics(
                        metric_name=metric_name,
                        start_time=filters.start_time,
                        end_time=filters.end_time,
                        labels=filters.labels,
                        limit=filters.limit
                    )
                    all_metrics.extend(metrics)
            else:
                # Query all metrics with filters
                all_metrics = self.storage.query_metrics(
                    start_time=filters.start_time,
                    end_time=filters.end_time,
                    labels=filters.labels,
                    limit=filters.limit
                )
            
            # Apply additional filtering
            filtered_metrics = self._apply_advanced_filters(all_metrics, filters)
            
            # Calculate query time
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                metrics=filtered_metrics,
                total_count=len(filtered_metrics),
                query_time_ms=query_time,
                filters_applied={
                    "metric_names": metric_names,
                    "metric_pattern": filters.metric_pattern,
                    "labels": filters.labels,
                    "time_range": filters.time_range.value if filters.time_range else None,
                    "start_time": filters.start_time.isoformat() if filters.start_time else None,
                    "end_time": filters.end_time.isoformat() if filters.end_time else None,
                    "limit": filters.limit
                }
            )
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            return QueryResult(
                metrics=[],
                total_count=0,
                query_time_ms=0,
                filters_applied={}
            )
    
    def aggregate(self, query: AggregationQuery) -> AggregationResult:
        """
        Execute an aggregation query.
        
        Args:
            query: Aggregation query specification
            
        Returns:
            AggregationResult with aggregated data
        """
        start_time = datetime.now()
        
        try:
            # Determine time range
            if query.filters:
                if query.filters.time_range:
                    end_time = datetime.now()
                    start_time_filter = self._time_range_to_datetime(query.filters.time_range, end_time)
                    
                    if not query.filters.start_time:
                        query.filters.start_time = start_time_filter
                    if not query.filters.end_time:
                        query.filters.end_time = end_time
                
                query_start = query.filters.start_time or (datetime.now() - timedelta(hours=24))
                query_end = query.filters.end_time or datetime.now()
                labels = query.filters.labels
            else:
                query_start = datetime.now() - timedelta(hours=24)
                query_end = datetime.now()
                labels = None
            
            # Execute aggregation
            if query.aggregation in [AggregationType.AVG, AggregationType.SUM, 
                                   AggregationType.MIN, AggregationType.MAX, AggregationType.COUNT]:
                # Use built-in storage aggregation
                data_points = self.storage.aggregate_metrics(
                    metric_name=query.metric_name,
                    aggregation=query.aggregation.value,
                    start_time=query_start,
                    end_time=query_end,
                    interval=query.interval,
                    labels=labels
                )
            else:
                # Handle advanced aggregations
                data_points = self._advanced_aggregation(query, query_start, query_end, labels)
            
            # Calculate total samples
            total_samples = sum(1 for _, _ in data_points)
            
            # Calculate query time
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return AggregationResult(
                data_points=data_points,
                aggregation_type=query.aggregation,
                interval=query.interval,
                total_samples=total_samples,
                query_time_ms=query_time
            )
            
        except Exception as e:
            self.logger.error(f"Aggregation query failed: {str(e)}")
            return AggregationResult(
                data_points=[],
                aggregation_type=query.aggregation,
                interval=query.interval,
                total_samples=0,
                query_time_ms=0
            )
    
    def get_metric_statistics(self, metric_name: str, 
                            time_range: Optional[TimeRange] = None) -> Dict[str, Any]:
        """Get statistical summary for a metric."""
        try:
            # Determine time range
            if time_range:
                end_time = datetime.now()
                start_time = self._time_range_to_datetime(time_range, end_time)
            else:
                start_time = datetime.now() - timedelta(hours=24)
                end_time = datetime.now()
            
            # Get metrics
            metrics = self.storage.query_metrics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time
            )
            
            if not metrics:
                return {"error": "No data found"}
            
            # Calculate statistics
            values = [m.value for m in metrics]
            
            stats = {
                "metric_name": metric_name,
                "sample_count": len(values),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "statistics": {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "sum": sum(values)
                }
            }
            
            # Calculate percentiles
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            stats["statistics"]["percentiles"] = {
                "p50": sorted_values[int(n * 0.5)],
                "p95": sorted_values[int(n * 0.95)],
                "p99": sorted_values[int(n * 0.99)]
            }
            
            # Calculate standard deviation
            mean = stats["statistics"]["avg"]
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            stats["statistics"]["stddev"] = variance ** 0.5
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics for {metric_name}: {str(e)}")
            return {"error": str(e)}
    
    def find_anomalies(self, metric_name: str, 
                      threshold_multiplier: float = 2.0,
                      time_range: Optional[TimeRange] = None) -> List[MetricValue]:
        """Find anomalous metric values using statistical analysis."""
        try:
            # Get statistics
            stats = self.get_metric_statistics(metric_name, time_range)
            
            if "error" in stats:
                return []
            
            mean = stats["statistics"]["avg"]
            stddev = stats["statistics"]["stddev"]
            threshold = stddev * threshold_multiplier
            
            # Get metrics in time range
            if time_range:
                end_time = datetime.now()
                start_time = self._time_range_to_datetime(time_range, end_time)
            else:
                start_time = datetime.now() - timedelta(hours=24)
                end_time = datetime.now()
            
            metrics = self.storage.query_metrics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time
            )
            
            # Find anomalies
            anomalies = []
            for metric in metrics:
                if abs(metric.value - mean) > threshold:
                    anomalies.append(metric)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Failed to find anomalies for {metric_name}: {str(e)}")
            return []
    
    def get_top_metrics(self, aggregation: AggregationType = AggregationType.AVG,
                       time_range: Optional[TimeRange] = None,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get top metrics by aggregated value."""
        try:
            # Determine time range
            if time_range:
                end_time = datetime.now()
                start_time = self._time_range_to_datetime(time_range, end_time)
            else:
                start_time = datetime.now() - timedelta(hours=24)
                end_time = datetime.now()
            
            # Get all metric names
            metric_names = self.storage.get_metric_names()
            
            # Calculate aggregated values for each metric
            metric_values = []
            
            for metric_name in metric_names:
                metrics = self.storage.query_metrics(
                    metric_name=metric_name,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if metrics:
                    values = [m.value for m in metrics]
                    
                    if aggregation == AggregationType.AVG:
                        agg_value = sum(values) / len(values)
                    elif aggregation == AggregationType.SUM:
                        agg_value = sum(values)
                    elif aggregation == AggregationType.MAX:
                        agg_value = max(values)
                    elif aggregation == AggregationType.MIN:
                        agg_value = min(values)
                    elif aggregation == AggregationType.COUNT:
                        agg_value = len(values)
                    else:
                        agg_value = sum(values) / len(values)  # Default to average
                    
                    metric_values.append({
                        "metric_name": metric_name,
                        "aggregated_value": agg_value,
                        "sample_count": len(values),
                        "aggregation_type": aggregation.value
                    })
            
            # Sort by aggregated value and return top N
            metric_values.sort(key=lambda x: x["aggregated_value"], reverse=True)
            return metric_values[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get top metrics: {str(e)}")
            return []
    
    def _find_metrics_by_pattern(self, pattern: str) -> List[str]:
        """Find metric names matching a pattern."""
        import fnmatch
        
        all_metrics = self.storage.get_metric_names()
        return [name for name in all_metrics if fnmatch.fnmatch(name, pattern)]
    
    def _apply_advanced_filters(self, metrics: List[MetricValue], 
                              filters: QueryFilter) -> List[MetricValue]:
        """Apply advanced filtering to metrics."""
        filtered = metrics
        
        # Apply label pattern filters
        if filters.label_patterns:
            import fnmatch
            
            def matches_label_patterns(metric_labels: Dict[str, str]) -> bool:
                for key, pattern in filters.label_patterns.items():
                    if key not in metric_labels:
                        return False
                    if not fnmatch.fnmatch(metric_labels[key], pattern):
                        return False
                return True
            
            filtered = [m for m in filtered if matches_label_patterns(m.labels)]
        
        return filtered
    
    def _time_range_to_datetime(self, time_range: TimeRange, end_time: datetime) -> datetime:
        """Convert TimeRange enum to datetime."""
        range_map = {
            TimeRange.LAST_HOUR: timedelta(hours=1),
            TimeRange.LAST_6_HOURS: timedelta(hours=6),
            TimeRange.LAST_24_HOURS: timedelta(hours=24),
            TimeRange.LAST_7_DAYS: timedelta(days=7),
            TimeRange.LAST_30_DAYS: timedelta(days=30),
            TimeRange.LAST_90_DAYS: timedelta(days=90)
        }
        
        delta = range_map.get(time_range, timedelta(hours=24))
        return end_time - delta
    
    def _advanced_aggregation(self, query: AggregationQuery, 
                            start_time: datetime, end_time: datetime,
                            labels: Optional[Dict[str, str]]) -> List[Tuple[datetime, float]]:
        """Handle advanced aggregation types."""
        # Get raw metrics
        metrics = self.storage.query_metrics(
            metric_name=query.metric_name,
            start_time=start_time,
            end_time=end_time,
            labels=labels
        )
        
        if not metrics:
            return []
        
        # Group metrics by time intervals
        interval_seconds = int(query.interval.total_seconds())
        buckets = {}
        
        for metric in metrics:
            bucket_start = int(metric.timestamp.timestamp() // interval_seconds) * interval_seconds
            bucket_time = datetime.fromtimestamp(bucket_start)
            
            if bucket_time not in buckets:
                buckets[bucket_time] = []
            buckets[bucket_time].append(metric.value)
        
        # Calculate aggregations
        results = []
        
        for bucket_time, values in sorted(buckets.items()):
            if query.aggregation == AggregationType.STDDEV:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                agg_value = variance ** 0.5
            elif query.aggregation == AggregationType.PERCENTILE_50:
                sorted_values = sorted(values)
                agg_value = sorted_values[int(len(sorted_values) * 0.5)]
            elif query.aggregation == AggregationType.PERCENTILE_95:
                sorted_values = sorted(values)
                agg_value = sorted_values[int(len(sorted_values) * 0.95)]
            elif query.aggregation == AggregationType.PERCENTILE_99:
                sorted_values = sorted(values)
                agg_value = sorted_values[int(len(sorted_values) * 0.99)]
            else:
                agg_value = sum(values) / len(values)  # Default to average
            
            results.append((bucket_time, agg_value))
        
        return results