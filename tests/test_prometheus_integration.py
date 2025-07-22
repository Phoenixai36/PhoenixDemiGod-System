"""
Unit tests for Prometheus integration.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.metrics.models import MetricValue
from src.metrics.prometheus import (
    PrometheusFormatter,
    PrometheusRegistry,
    PrometheusExporter,
    SimpleScrapeEndpoint
)


class TestPrometheusFormatter:
    """Test cases for PrometheusFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create formatter for testing."""
        return PrometheusFormatter()
    
    def test_sanitize_metric_name(self, formatter):
        """Test metric name sanitization."""
        test_cases = [
            ("valid_metric_name", "valid_metric_name"),
            ("metric-with-dashes", "metric_with_dashes"),
            ("metric.with.dots", "metric_with_dots"),
            ("123invalid", "_123invalid"),
            ("metric__with__multiple__underscores", "metric_with_multiple_underscores"),
            ("metric_ending_with_underscore_", "metric_ending_with_underscore"),
            ("", "unnamed_metric")
        ]
        
        for input_name, expected in test_cases:
            result = formatter._sanitize_metric_name(input_name)
            assert result == expected, f"Failed for input: {input_name}"
    
    def test_sanitize_label_name(self, formatter):
        """Test label name sanitization."""
        test_cases = [
            ("valid_label", "valid_label"),
            ("label-with-dashes", "label_with_dashes"),
            ("123invalid", "_123invalid"),
            ("", "unnamed_label")
        ]
        
        for input_name, expected in test_cases:
            result = formatter._sanitize_label_name(input_name)
            assert result == expected
    
    def test_escape_label_value(self, formatter):
        """Test label value escaping."""
        test_cases = [
            ("simple_value", "simple_value"),
            ("value with spaces", "value with spaces"),
            ('value with "quotes"', 'value with \\"quotes\\"'),
            ("value\nwith\nnewlines", "value\\nwith\\nnewlines"),
            ("value\twith\ttabs", "value\\twith\\ttabs"),
            ("value\\with\\backslashes", "value\\\\with\\\\backslashes")
        ]
        
        for input_value, expected in test_cases:
            result = formatter._escape_label_value(input_value)
            assert result == expected
    
    def test_format_single_metric(self, formatter):
        """Test formatting a single metric."""
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            labels={"container": "web-1", "service": "nginx"},
            unit="percent"
        )
        
        result = formatter.format_single_metric(metric, include_timestamp=True)
        
        assert "test_metric" in result
        assert "42.5" in result
        assert 'container="web-1"' in result
        assert 'service="nginx"' in result
        assert "1672574400000" in result  # Timestamp in milliseconds
    
    def test_format_single_metric_without_timestamp(self, formatter):
        """Test formatting metric without timestamp."""
        metric = MetricValue(
            name="test_metric",
            value=42.5,
            timestamp=datetime.now(),
            labels={"container": "web-1"}
        )
        
        result = formatter.format_single_metric(metric, include_timestamp=False)
        
        assert "test_metric" in result
        assert "42.5" in result
        # Should not contain timestamp
        assert not any(char.isdigit() and len([c for c in result.split() if c.isdigit() and len(c) > 10]) > 0 for char in result)
    
    def test_format_metrics_with_help(self, formatter):
        """Test formatting multiple metrics with help text."""
        metrics = [
            MetricValue("cpu_usage", 50.0, datetime.now(), {"container": "web-1"}),
            MetricValue("cpu_usage", 60.0, datetime.now(), {"container": "web-2"}),
            MetricValue("memory_usage", 70.0, datetime.now(), {"container": "web-1"})
        ]
        
        result = formatter.format_metrics(metrics, include_help=True)
        
        # Should contain TYPE and HELP comments
        assert "# TYPE cpu_usage" in result
        assert "# HELP cpu_usage" in result
        assert "# TYPE memory_usage" in result
        assert "# HELP memory_usage" in result
        
        # Should contain metric values
        assert "cpu_usage" in result
        assert "memory_usage" in result
        assert "50" in result
        assert "70" in result
    
    def test_format_metrics_without_help(self, formatter):
        """Test formatting metrics without help text."""
        metrics = [
            MetricValue("test_metric", 42.0, datetime.now(), {"label": "value"})
        ]
        
        result = formatter.format_metrics(metrics, include_help=False)
        
        # Should not contain TYPE and HELP comments
        assert "# TYPE" not in result
        assert "# HELP" not in result
        
        # Should contain metric value
        assert "test_metric" in result
        assert "42" in result
    
    def test_infer_metric_type(self, formatter):
        """Test metric type inference."""
        test_cases = [
            ("requests_total", "counter"),
            ("cpu_usage_percent", "gauge"),
            ("memory_bytes", "gauge"),
            ("http_request_duration_bucket", "histogram"),
            ("response_time_sum", "histogram"),
            ("custom_metric", "gauge")  # Default
        ]
        
        for metric_name, expected_type in test_cases:
            metrics = [MetricValue(metric_name, 1.0, datetime.now())]
            result = formatter._infer_metric_type(metric_name, metrics)
            assert result == expected_type
    
    def test_validate_prometheus_format(self, formatter):
        """Test Prometheus format validation."""
        # Valid format
        valid_prometheus = """# HELP test_metric Test metric
# TYPE test_metric gauge
test_metric{label="value"} 42.5 1672574400000
"""
        
        issues = formatter.validate_prometheus_format(valid_prometheus)
        assert len(issues) == 0
        
        # Invalid format
        invalid_prometheus = """invalid-metric-name 42.5
test_metric invalid_value
"""
        
        issues = formatter.validate_prometheus_format(invalid_prometheus)
        assert len(issues) > 0
    
    def test_special_values(self, formatter):
        """Test formatting special float values."""
        special_metrics = [
            MetricValue("inf_metric", float('inf'), datetime.now()),
            MetricValue("neg_inf_metric", float('-inf'), datetime.now()),
            MetricValue("nan_metric", float('nan'), datetime.now()),
            MetricValue("bool_metric", True, datetime.now()),
            MetricValue("bool_false_metric", False, datetime.now())
        ]
        
        result = formatter.format_metrics(special_metrics, include_help=False)
        
        assert "+Inf" in result
        assert "-Inf" in result
        assert "NaN" in result
        assert "1" in result  # True -> 1
        assert "0" in result  # False -> 0


class TestPrometheusRegistry:
    """Test cases for PrometheusRegistry."""
    
    @pytest.fixture
    def registry(self):
        """Create registry for testing."""
        return PrometheusRegistry()
    
    def test_add_single_metric(self, registry):
        """Test adding a single metric."""
        metric = MetricValue("test_metric", 42.0, datetime.now(), {"label": "value"})
        
        registry.add_metric(metric)
        
        assert registry.get_metric_count() == 1
        assert "test_metric" in registry.get_metric_names()
    
    def test_add_multiple_metrics(self, registry):
        """Test adding multiple metrics."""
        metrics = [
            MetricValue("metric_1", 1.0, datetime.now()),
            MetricValue("metric_2", 2.0, datetime.now()),
            MetricValue("metric_1", 3.0, datetime.now())  # Same name
        ]
        
        registry.add_metrics(metrics)
        
        assert registry.get_metric_count() == 3
        assert len(registry.get_metric_names()) == 2  # Two unique names
    
    def test_register_collector(self, registry):
        """Test registering a collector function."""
        def test_collector():
            return [MetricValue("collector_metric", 100.0, datetime.now())]
        
        registry.register_collector(test_collector)
        
        metrics = registry.collect_metrics()
        
        # Should include metrics from collector
        collector_metrics = [m for m in metrics if m.name == "collector_metric"]
        assert len(collector_metrics) == 1
        assert collector_metrics[0].value == 100.0
    
    def test_global_labels(self, registry):
        """Test global labels functionality."""
        registry.set_global_labels({"environment": "test", "version": "1.0"})
        
        metric = MetricValue("test_metric", 42.0, datetime.now(), {"service": "web"})
        registry.add_metric(metric)
        
        metrics = registry.collect_metrics()
        
        # Should have both original and global labels
        test_metrics = [m for m in metrics if m.name == "test_metric"]
        assert len(test_metrics) == 1
        
        labels = test_metrics[0].labels
        assert labels["service"] == "web"
        assert labels["environment"] == "test"
        assert labels["version"] == "1.0"
    
    def test_metric_metadata(self, registry):
        """Test setting metric metadata."""
        registry.set_metric_metadata("test_metric", "counter", "Test counter metric")
        
        # Verify metadata is set in formatter
        assert "test_metric" in registry.formatter._metric_types
        assert registry.formatter._metric_types["test_metric"] == "counter"
        assert "test_metric" in registry.formatter._metric_help
        assert registry.formatter._metric_help["test_metric"] == "Test counter metric"
    
    def test_generate_prometheus_output(self, registry):
        """Test generating Prometheus output."""
        metrics = [
            MetricValue("cpu_usage", 50.0, datetime.now(), {"container": "web-1"}),
            MetricValue("memory_usage", 70.0, datetime.now(), {"container": "web-1"})
        ]
        
        registry.add_metrics(metrics)
        
        output = registry.generate_prometheus_output()
        
        assert "cpu_usage" in output
        assert "memory_usage" in output
        assert "50" in output
        assert "70" in output
        assert "# TYPE" in output
        assert "# HELP" in output
    
    def test_clear_metrics(self, registry):
        """Test clearing metrics."""
        metrics = [
            MetricValue("metric_1", 1.0, datetime.now()),
            MetricValue("metric_2", 2.0, datetime.now())
        ]
        
        registry.add_metrics(metrics)
        assert registry.get_metric_count() == 2
        
        # Clear specific metric
        registry.clear_metrics("metric_1")
        assert registry.get_metric_count() == 1
        assert "metric_1" not in registry.get_metric_names()
        
        # Clear all metrics
        registry.clear_metrics()
        assert registry.get_metric_count() == 0
    
    def test_registry_stats(self, registry):
        """Test getting registry statistics."""
        # Add some test data
        registry.add_metric(MetricValue("test_metric", 42.0, datetime.now()))
        
        def test_collector():
            return [MetricValue("collector_metric", 100.0, datetime.now())]
        
        registry.register_collector(test_collector)
        
        stats = registry.get_registry_stats()
        
        assert "total_metrics" in stats
        assert "metric_families" in stats
        assert "registered_collectors" in stats
        assert stats["registered_collectors"] == 1
        assert "collection_count" in stats
    
    def test_export_to_file(self, registry):
        """Test exporting metrics to file."""
        metric = MetricValue("test_metric", 42.0, datetime.now())
        registry.add_metric(metric)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            success = registry.export_to_file(temp_path)
            assert success is True
            
            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "test_metric" in content
                assert "42" in content
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestSimpleScrapeEndpoint:
    """Test cases for SimpleScrapeEndpoint."""
    
    @pytest.fixture
    def endpoint(self):
        """Create simple endpoint for testing."""
        registry = PrometheusRegistry()
        return SimpleScrapeEndpoint(registry)
    
    def test_get_metrics_text(self, endpoint):
        """Test getting metrics text."""
        # Add test metric to registry
        metric = MetricValue("test_metric", 42.0, datetime.now(), {"label": "value"})
        endpoint.registry.add_metric(metric)
        
        text = endpoint.get_metrics_text()
        
        assert "test_metric" in text
        assert "42" in text
        assert 'label="value"' in text
    
    def test_save_metrics_to_file(self, endpoint):
        """Test saving metrics to file."""
        metric = MetricValue("test_metric", 42.0, datetime.now())
        endpoint.registry.add_metric(metric)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            success = endpoint.save_metrics_to_file(temp_path)
            assert success is True
            
            # Verify file content
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "test_metric" in content
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestPrometheusExporter:
    """Test cases for PrometheusExporter."""
    
    @pytest.fixture
    def exporter(self):
        """Create exporter for testing."""
        config = {
            'enable_http_endpoint': False,  # Disable HTTP for testing
            'collection_interval': 1,  # Short interval for testing
            'global_labels': {'test': 'true'}
        }
        return PrometheusExporter(config=config)
    
    @pytest.mark.asyncio
    async def test_initialization(self, exporter):
        """Test exporter initialization."""
        success = await exporter.initialize()
        assert success is True
    
    def test_add_metrics(self, exporter):
        """Test adding metrics to exporter."""
        metrics = [
            MetricValue("cpu_usage", 50.0, datetime.now(), {"container": "web-1"}),
            MetricValue("memory_usage", 70.0, datetime.now(), {"container": "web-1"})
        ]
        
        exporter.add_metrics(metrics)
        
        # Verify metrics are in registry
        registry_metrics = exporter.registry.collect_metrics()
        assert len(registry_metrics) >= 2
        
        # Check for global labels
        for metric in registry_metrics:
            if metric.name in ["cpu_usage", "memory_usage"]:
                assert "test" in metric.labels
                assert metric.labels["test"] == "true"
    
    def test_register_collector(self, exporter):
        """Test registering custom collector."""
        def custom_collector():
            return [MetricValue("custom_metric", 123.0, datetime.now())]
        
        exporter.register_collector(custom_collector)
        
        # Collect metrics
        text = exporter.get_metrics_text()
        
        assert "custom_metric" in text
        assert "123" in text
    
    def test_set_metric_metadata(self, exporter):
        """Test setting metric metadata."""
        exporter.set_metric_metadata("test_metric", "counter", "Test counter")
        
        # Add metric and generate output
        exporter.add_metric(MetricValue("test_metric", 1.0, datetime.now()))
        text = exporter.get_metrics_text()
        
        assert "# TYPE test_metric counter" in text
        assert "# HELP test_metric Test counter" in text
    
    def test_get_metrics_text(self, exporter):
        """Test getting metrics text."""
        metric = MetricValue("test_metric", 42.0, datetime.now())
        exporter.add_metric(metric)
        
        text = exporter.get_metrics_text()
        
        assert "test_metric" in text
        assert "42" in text
    
    def test_export_to_file(self, exporter):
        """Test exporting to file."""
        metric = MetricValue("test_metric", 42.0, datetime.now())
        exporter.add_metric(metric)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_path = f.name
        
        try:
            success = exporter.export_to_file(temp_path)
            assert success is True
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "test_metric" in content
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_exporter_stats(self, exporter):
        """Test getting exporter statistics."""
        stats = exporter.get_exporter_stats()
        
        assert "exporter" in stats
        assert "registry" in stats
        assert "running" in stats["exporter"]
        assert "collection_interval_seconds" in stats["exporter"]
    
    def test_validate_metrics(self, exporter):
        """Test metrics validation."""
        # Add valid metric
        exporter.add_metric(MetricValue("valid_metric", 42.0, datetime.now()))
        
        issues = exporter.validate_metrics()
        
        # Should have no validation issues
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using exporter as context manager."""
        config = {'enable_http_endpoint': False}
        
        async with PrometheusExporter(config=config) as exporter:
            # Add metric
            exporter.add_metric(MetricValue("context_test", 1.0, datetime.now()))
            
            # Get metrics
            text = exporter.get_metrics_text()
            assert "context_test" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])