"""
API endpoints for metrics storage and retrieval.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..models import MetricValue
from ..storage import QueryEngine


class MetricResponse(BaseModel):
    """Response model for a metric."""
    name: str
    value: Union[float, int, str]
    timestamp: datetime
    labels: Dict[str, str] = Field(default_factory=dict)
    unit: Optional[str] = None


class MetricsQueryParams(BaseModel):
    """Query parameters for metrics API."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[str] = None  # Format: "1h", "30m", "1d"
    labels: Optional[Dict[str, str]] = None
    aggregation: Optional[str] = None
    limit: Optional[int] = None


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics."""
    metric_count: int
    series_count: int
    point_count: int
    memory_bytes: int
    retention_policy: Dict[str, Any]


def create_metrics_router(query_engine: QueryEngine) -> APIRouter:
    """
    Create a FastAPI router for metrics API endpoints.
    
    Args:
        query_engine: The query engine to use
        
    Returns:
        FastAPI router with metrics endpoints
    """
    router = APIRouter(prefix="/metrics", tags=["metrics"])
    logger = logging.getLogger("metrics.api")
    
    def parse_duration(duration_str: Optional[str]) -> Optional[timedelta]:
        """Parse duration string to timedelta."""
        if not duration_str:
            return None
            
        try:
            unit = duration_str[-1].lower()
            value = int(duration_str[:-1])
            
            if unit == "s":
                return timedelta(seconds=value)
            elif unit == "m":
                return timedelta(minutes=value)
            elif unit == "h":
                return timedelta(hours=value)
            elif unit == "d":
                return timedelta(days=value)
            else:
                raise ValueError(f"Unknown duration unit: {unit}")
        except (ValueError, IndexError) as e:
            logger.error(f"Failed to parse duration: {duration_str}, {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid duration format: {duration_str}. Use format like '1h', '30m', '1d'."
            )
    
    @router.get("/", response_model=List[str])
    async def get_metric_names():
        """Get all available metric names."""
        return await query_engine.get_metric_names()
    
    @router.get("/{metric_name}", response_model=List[MetricResponse])
    async def query_metrics(
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration: Optional[str] = None,
        aggregation: Optional[str] = None,
        limit: Optional[int] = Query(None, ge=1, le=10000),
        container_id: Optional[str] = None,
        container_name: Optional[str] = None,
        service: Optional[str] = None,
        host: Optional[str] = None
    ):
        """
        Query metrics by name, time range, and optional filters.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Optional start of time range
            end_time: Optional end of time range
            duration: Optional duration from end_time (or now) backwards (e.g., "1h", "30m")
            aggregation: Optional aggregation function (avg, sum, min, max, last)
            limit: Optional limit on number of results
            container_id: Optional container ID filter
            container_name: Optional container name filter
            service: Optional service name filter
            host: Optional host name filter
            
        Returns:
            List of matching metrics
        """
        # Parse duration
        duration_td = parse_duration(duration)
        
        # Build labels filter
        labels = {}
        if container_id:
            labels["container_id"] = container_id
        if container_name:
            labels["container_name"] = container_name
        if service:
            labels["service"] = service
        if host:
            labels["host"] = host
        
        # Query metrics
        try:
            results = await query_engine.query_metrics(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration_td,
                labels=labels or None,
                aggregation=aggregation,
                limit=limit
            )
            
            # Convert to response model
            return [
                MetricResponse(
                    name=metric.name,
                    value=metric.value,
                    timestamp=metric.timestamp,
                    labels=metric.labels,
                    unit=metric.unit
                )
                for metric in results
            ]
        except Exception as e:
            logger.error(f"Failed to query metrics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to query metrics: {str(e)}"
            )
    
    @router.get("/{metric_name}/latest", response_model=Optional[MetricResponse])
    async def get_latest_metric(
        metric_name: str,
        container_id: Optional[str] = None,
        container_name: Optional[str] = None,
        service: Optional[str] = None,
        host: Optional[str] = None
    ):
        """
        Get the latest value for a metric.
        
        Args:
            metric_name: Name of the metric to query
            container_id: Optional container ID filter
            container_name: Optional container name filter
            service: Optional service name filter
            host: Optional host name filter
            
        Returns:
            The latest metric value or None if not found
        """
        # Build labels filter
        labels = {}
        if container_id:
            labels["container_id"] = container_id
        if container_name:
            labels["container_name"] = container_name
        if service:
            labels["service"] = service
        if host:
            labels["host"] = host
        
        # Query latest metric
        try:
            result = await query_engine.query_latest(
                metric_name=metric_name,
                labels=labels or None
            )
            
            if result:
                return MetricResponse(
                    name=result.name,
                    value=result.value,
                    timestamp=result.timestamp,
                    labels=result.labels,
                    unit=result.unit
                )
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get latest metric: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get latest metric: {str(e)}"
            )
    
    @router.get("/{metric_name}/range", response_model=List[Dict[str, Any]])
    async def query_metric_range(
        metric_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        step: str = "5m",
        aggregation: str = "avg",
        container_id: Optional[str] = None,
        container_name: Optional[str] = None,
        service: Optional[str] = None,
        host: Optional[str] = None
    ):
        """
        Query metrics with regular time intervals.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Start of time range
            end_time: Optional end of time range (defaults to now)
            step: Time interval between points (e.g., "5m", "1h")
            aggregation: Aggregation function (avg, sum, min, max, last)
            container_id: Optional container ID filter
            container_name: Optional container name filter
            service: Optional service name filter
            host: Optional host name filter
            
        Returns:
            List of (timestamp, value) points at regular intervals
        """
        # Parse step
        step_td = parse_duration(step)
        if not step_td:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid step format: {step}. Use format like '1h', '5m', '30s'."
            )
        
        # Set default end_time to now
        if not end_time:
            end_time = datetime.now()
        
        # Build labels filter
        labels = {}
        if container_id:
            labels["container_id"] = container_id
        if container_name:
            labels["container_name"] = container_name
        if service:
            labels["service"] = service
        if host:
            labels["host"] = host
        
        # Query range
        try:
            results = await query_engine.query_range(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                step=step_td,
                labels=labels or None,
                aggregation=aggregation
            )
            
            # Convert to response format
            return [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in results
            ]
        except Exception as e:
            logger.error(f"Failed to query metric range: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to query metric range: {str(e)}"
            )
    
    @router.get("/labels/keys", response_model=List[str])
    async def get_label_keys(metric_name: Optional[str] = None):
        """
        Get all available label keys.
        
        Args:
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label keys
        """
        return await query_engine.get_label_keys(metric_name)
    
    @router.get("/labels/values/{label_key}", response_model=List[str])
    async def get_label_values(
        label_key: str,
        metric_name: Optional[str] = None
    ):
        """
        Get all available values for a label key.
        
        Args:
            label_key: The label key to get values for
            metric_name: Optional metric name to filter by
            
        Returns:
            List of label values
        """
        return await query_engine.get_label_values(label_key, metric_name)
    
    @router.get("/storage/stats", response_model=StorageStatsResponse)
    async def get_storage_stats():
        """
        Get statistics about the metrics storage.
        
        Returns:
            Dictionary with storage statistics
        """
        return await query_engine.get_storage_stats()
    
    return router