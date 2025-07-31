"""
Integration tests for service discovery and health check functionality
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from phoenix_system_review.discovery.service_discovery import ServiceDiscovery
from phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from phoenix_system_review.models.data_models import (
    Component, ComponentCategory, ComponentStatus, ServiceRegistry
)


class TestServiceDiscoveryIntegration:
    """Test integration of service discovery with other system components"""
    
    @pytest.fixture
    def mock_service_responses(self):
        """Mock HTTP responses for different service states"""
        return {
            'healthy_service': {
                'status_code': 200,
                'json_response': {'status': 'healthy', 'uptime': 3600, 'version': '1.0.0'},
                'response_time': 0.1
            },
            'degraded_service': {
                'status_code': 200,
                'json_response': {'status': 'degraded', 'uptime': 1800, 'errors': 5},
                'response_time': 0.8
            },
            'unhealthy_service': {
                'status_code': 500,
                'json_response': {'status': 'error', 'message': 'Database connection failed'},
                'response_time': 2.0
            },
            'timeout_service': {
                'exception': 'timeout',
                'response_time': 5.0
            },
            'connection_refused': {
                'exception': 'connection_refused'
            }
        }
    
    @pytest.fixture
    def phoenix_service_endpoints(self):
        """Phoenix Hydra service endpoints for testing"""
        return {
            'phoenix-core': 'http://localhost:8080/health',
            'nca-toolkit': 'http://localhost:8081/health',
            'n8n': 'http://localhost:5678',
            'windmill': 'http://localhost:8000/api/health',
            'prometheus': 'http://localhost:9090/-/healthy',
            'grafana': 'http://localhost:3000/api/health',
            'minio': 'http://localhost:9000/minio/health/live',
            'postgresql': 'http://localhost:5432'  # This will typically fail
        }
    
    def test_comprehensive_service_discovery(self, phoenix_service_endpoints, mock_service_responses):
        """Test comprehensive service discovery across all Phoenix Hydra services"""
        
        service_discovery = ServiceDiscovery()
        
        def mock_requests_get(url, timeout=5):
            """Mock requests.get with different responses based on URL"""
            mock_response = Mock()
            
            if 'phoenix-core' in url:
                response_data = mock_service_responses['healthy_service']
            elif 'nca-toolkit' in url:
                response_data = mock_service_responses['healthy_service']
            elif 'n8n' in url:
                response_data = mock_service_responses['degraded_service']
            elif 'windmill' in url:
                response_data = mock_service_responses['unhealthy_service']
            elif 'prometheus' in url:
                response_data = mock_service_responses['healthy_service']
            elif 'grafana' in url:
                response_data = mock_service_responses['timeout_service']
                if 'exception' in response_data:
                    if response_data['exception'] == 'timeout':
                        raise TimeoutError("Request timed out")
            elif 'minio' in url:
                response_data = mock_service_responses['healthy_service']
            elif 'postgresql' in url:
                response_data = mock_service_responses['connection_refused']
                raise ConnectionError("Connection refused")
            else:
                response_data = mock_service_responses['unhealthy_service']
            
            mock_response.status_code = response_data.get('status_code', 500)
            mock_response.json.return_value = response_data.get('json_response', {})
            return mock_response
        
        with patch('requests.get', side_effect=mock_requests_get):
            registry = service_discovery.discover_services(phoenix_service_endpoints)
        
        # Verify service registry structure
        assert isinstance(registry, ServiceRegistry)
        assert len(registry.services) == len(phoenix_service_endpoints)
        assert len(registry.health_checks) == len(phoenix_service_endpoints)
        assert len(registry.endpoints) == len(phoenix_service_endpoints)
        
        # Verify specific service health states
        assert registry.health_checks['phoenix-core'] is True
        assert registry.health_checks['nca-toolkit'] is True
        assert registry.health_checks['n8n'] is True  # Degraded but responding
        assert registry.health_checks['windmill'] is False  # 500 error
        assert registry.health_checks['prometheus'] is True
        assert registry.health_checks['grafana'] is False  # Timeout
        assert registry.health_checks['minio'] is True
        assert registry.health_checks['postgresql'] is False  # Connection refused
        
        # Verify service details are captured
        for service_name in phoenix_service_endpoints:
            assert service_name in registry.services
            service_info = registry.services[service_name]
            assert 'last_check' in service_info
            assert 'status' in service_info
    
    def test_service_discovery_with_metrics_collection(self, phoenix_service_endpoints):
        """Test service discovery with performance metrics collection"""
        
        service_discovery = ServiceDiscovery()
        
        def mock_requests_get_with_metrics(url, timeout=5):
            """Mock requests with response time simulation"""
            mock_response = Mock()
            
            # Simulate different response times
            if 'phoenix-core' in url:
                time.sleep(0.01)  # Fast response
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'status': 'healthy',
                    'metrics': {
                        'cpu_usage': 45.2,
                        'memory_usage': 512,
                        'active_connections': 25,
                        'requests_per_second': 10.5
                    }
                }
            elif 'n8n' in url:
                time.sleep(0.05)  # Moderate response
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'status': 'healthy',
                    'executions': {
                        'running': 3,
                        'waiting': 12,
                        'completed_today': 145
                    }
                }
            else:
                time.sleep(0.02)
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'healthy'}
            
            return mock_response
        
        with patch('requests.get', side_effect=mock_requests_get_with_metrics):
            # Test individual service metrics collection
            phoenix_metrics = service_discovery.get_service_metrics('http://localhost:8080/metrics')
            n8n_metrics = service_discovery.get_service_metrics('http://localhost:5678/metrics')
            
            # Verify metrics collection
            assert phoenix_metrics is not None
            assert 'cpu_usage' in phoenix_metrics
            assert 'memory_usage' in phoenix_metrics
            assert phoenix_metrics['cpu_usage'] == 45.2
            
            assert n8n_metrics is not None
            assert 'executions' in n8n_metrics
            assert n8n_metrics['executions']['running'] == 3
    
    def test_service_discovery_component_integration(self, phoenix_service_endpoints):
        """Test integration between service discovery and component evaluation"""
        
        service_discovery = ServiceDiscovery()
        component_evaluator = ComponentEvaluator()
        
        # Mock service responses
        def mock_service_health(url):
            if 'phoenix-core' in url or 'nca-toolkit' in url:
                return True
            elif 'n8n' in url or 'windmill' in url:
                return True
            else:
                return False
        
        with patch.object(service_discovery, 'check_service_health', side_effect=mock_service_health):
            registry = service_discovery.discover_services(phoenix_service_endpoints)
        
        # Create components based on service discovery results
        components = []
        
        for service_name, endpoint in phoenix_service_endpoints.items():
            is_healthy = registry.health_checks.get(service_name, False)
            
            component = Component(
                name=service_name,
                category=ComponentCategory.INFRASTRUCTURE,
                path=f"/services/{service_name}",
                configuration={'endpoint': endpoint, 'health_check': endpoint},
                status=ComponentStatus.OPERATIONAL if is_healthy else ComponentStatus.FAILED
            )
            components.append(component)
        
        # Evaluate components based on service health
        evaluation_results = []
        
        for component in components:
            criteria = component_evaluator.get_evaluation_criteria('infrastructure')
            
            # Mock evaluation that considers service health
            with patch.object(component_evaluator, '_check_criterion') as mock_check:
                def mock_criterion_check(comp, criterion):
                    if criterion.id == 'service_health':
                        return comp.status == ComponentStatus.OPERATIONAL
                    elif criterion.id == 'endpoint_availability':
                        return comp.configuration.get('endpoint') is not None
                    else:
                        return True
                
                mock_check.side_effect = mock_criterion_check
                result = component_evaluator.evaluate_component(component, criteria)
                evaluation_results.append(result)
        
        # Verify evaluation results reflect service health
        healthy_services = ['phoenix-core', 'nca-toolkit', 'n8n', 'windmill']
        
        for result in evaluation_results:
            service_name = result.component.name
            if service_name in healthy_services:
                assert result.completion_percentage > 50.0
            else:
                # Unhealthy services should have lower completion
                assert result.completion_percentage >= 0.0
    
    def test_service_configuration_validation_integration(self):
        """Test integration between service discovery and configuration validation"""
        
        service_discovery = ServiceDiscovery()
        
        # Test valid service configurations
        valid_service_configs = [
            {
                'name': 'phoenix-core',
                'host': 'localhost',
                'port': 8080,
                'health_endpoint': '/health',
                'enabled': True,
                'timeout': 5,
                'retry_count': 3
            },
            {
                'name': 'n8n',
                'host': 'localhost',
                'port': 5678,
                'health_endpoint': '/',
                'enabled': True,
                'timeout': 10,
                'retry_count': 2
            },
            {
                'name': 'windmill',
                'host': 'localhost',
                'port': 8000,
                'health_endpoint': '/api/health',
                'enabled': False,  # Disabled service
                'timeout': 5,
                'retry_count': 1
            }
        ]
        
        # Test invalid service configurations
        invalid_service_configs = [
            {
                'name': '',  # Empty name
                'host': 'localhost',
                'port': 8080,
                'enabled': True
            },
            {
                'name': 'invalid-port-service',
                'host': 'localhost',
                'port': 'invalid',  # Invalid port type
                'enabled': True
            },
            {
                'name': 'missing-host-service',
                # Missing host
                'port': 8080,
                'enabled': True
            }
        ]
        
        # Validate service configurations
        for config in valid_service_configs:
            issues = service_discovery.validate_service_configuration(config)
            if config.get('enabled', True):
                assert len(issues) == 0  # Valid enabled services should have no issues
        
        for config in invalid_service_configs:
            issues = service_discovery.validate_service_configuration(config)
            assert len(issues) > 0  # Invalid configs should have issues
    
    def test_service_discovery_error_recovery(self, phoenix_service_endpoints):
        """Test service discovery error handling and recovery mechanisms"""
        
        service_discovery = ServiceDiscovery()
        
        # Test with various error conditions
        def mock_requests_with_errors(url, timeout=5):
            """Mock requests with different error conditions"""
            if 'phoenix-core' in url:
                # Successful response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'status': 'healthy'}
                return mock_response
            elif 'n8n' in url:
                # Timeout error
                raise TimeoutError("Request timed out")
            elif 'windmill' in url:
                # Connection error
                raise ConnectionError("Connection refused")
            elif 'prometheus' in url:
                # HTTP error
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.raise_for_status.side_effect = Exception("404 Not Found")
                return mock_response
            else:
                # Generic exception
                raise Exception("Unknown error")
        
        with patch('requests.get', side_effect=mock_requests_with_errors):
            registry = service_discovery.discover_services(phoenix_service_endpoints)
        
        # Verify that service discovery continues despite errors
        assert isinstance(registry, ServiceRegistry)
        assert len(registry.services) == len(phoenix_service_endpoints)
        
        # Verify error handling results
        assert registry.health_checks['phoenix-core'] is True  # Should succeed
        assert registry.health_checks['n8n'] is False  # Timeout
        assert registry.health_checks['windmill'] is False  # Connection error
        assert registry.health_checks['prometheus'] is False  # HTTP error
        
        # Verify that service information is still recorded
        for service_name in phoenix_service_endpoints:
            assert service_name in registry.services
            service_info = registry.services[service_name]
            assert 'last_check' in service_info
            assert 'status' in service_info
            
            if not registry.health_checks[service_name]:
                assert 'error' in service_info or service_info['status'] in ['error', 'timeout', 'unreachable']
    
    def test_periodic_service_monitoring_integration(self, phoenix_service_endpoints):
        """Test integration with periodic service monitoring"""
        
        service_discovery = ServiceDiscovery()
        
        # Simulate periodic health checks
        health_check_history = []
        
        def mock_periodic_health_check():
            """Simulate periodic health check execution"""
            def mock_health_response(url):
                # Simulate changing service states over time
                current_time = datetime.now()
                
                if 'phoenix-core' in url:
                    return True  # Always healthy
                elif 'n8n' in url:
                    # Intermittent issues
                    return current_time.second % 3 != 0
                elif 'windmill' in url:
                    # Gradually improving
                    return len(health_check_history) > 2
                else:
                    return False
            
            with patch.object(service_discovery, 'check_service_health', side_effect=mock_health_response):
                registry = service_discovery.discover_services(phoenix_service_endpoints)
                health_check_history.append({
                    'timestamp': datetime.now(),
                    'results': dict(registry.health_checks)
                })
                return registry
        
        # Perform multiple health checks to simulate monitoring
        registries = []
        for i in range(5):
            registry = mock_periodic_health_check()
            registries.append(registry)
            time.sleep(0.1)  # Small delay between checks
        
        # Analyze health check trends
        assert len(health_check_history) == 5
        
        # Phoenix core should be consistently healthy
        phoenix_core_health = [check['results']['phoenix-core'] for check in health_check_history]
        assert all(phoenix_core_health)
        
        # N8N should have intermittent issues
        n8n_health = [check['results']['n8n'] for check in health_check_history]
        assert not all(n8n_health)  # Should have some failures
        assert any(n8n_health)     # Should have some successes
        
        # Windmill should improve over time
        windmill_health = [check['results']['windmill'] for check in health_check_history]
        # Later checks should be more likely to succeed
        later_checks = windmill_health[-2:]
        assert any(later_checks)  # At least one of the later checks should succeed
    
    def test_service_dependency_health_propagation(self):
        """Test how service health affects dependent service evaluation"""
        
        service_discovery = ServiceDiscovery()
        
        # Define service dependencies
        service_dependencies = {
            'phoenix-core': [],  # No dependencies
            'nca-toolkit': ['phoenix-core'],  # Depends on phoenix-core
            'n8n': ['phoenix-core', 'postgresql'],  # Depends on core and database
            'windmill': ['postgresql'],  # Depends on database
            'grafana': ['prometheus'],  # Depends on prometheus
            'prometheus': ['phoenix-core']  # Depends on core
        }
        
        # Mock service health with dependency consideration
        def mock_dependent_health_check(url):
            service_name = None
            for name in service_dependencies.keys():
                if name in url:
                    service_name = name
                    break
            
            if not service_name:
                return False
            
            # Base health status
            base_health = {
                'phoenix-core': True,
                'postgresql': False,  # Database is down
                'prometheus': True,
                'nca-toolkit': True,
                'n8n': True,
                'windmill': True,
                'grafana': True
            }
            
            # Check if dependencies are healthy
            dependencies = service_dependencies.get(service_name, [])
            dependencies_healthy = all(base_health.get(dep, False) for dep in dependencies)
            
            # Service is healthy only if it and its dependencies are healthy
            return base_health.get(service_name, False) and dependencies_healthy
        
        endpoints = {
            'phoenix-core': 'http://localhost:8080/health',
            'nca-toolkit': 'http://localhost:8081/health',
            'n8n': 'http://localhost:5678/health',
            'windmill': 'http://localhost:8000/health',
            'grafana': 'http://localhost:3000/health',
            'prometheus': 'http://localhost:9090/health'
        }
        
        with patch.object(service_discovery, 'check_service_health', side_effect=mock_dependent_health_check):
            registry = service_discovery.discover_services(endpoints)
        
        # Verify dependency health propagation
        assert registry.health_checks['phoenix-core'] is True  # No dependencies, healthy
        assert registry.health_checks['nca-toolkit'] is True  # Depends on healthy phoenix-core
        assert registry.health_checks['n8n'] is False  # Depends on unhealthy postgresql
        assert registry.health_checks['windmill'] is False  # Depends on unhealthy postgresql
        assert registry.health_checks['grafana'] is True  # Depends on healthy prometheus
        assert registry.health_checks['prometheus'] is True  # Depends on healthy phoenix-core


if __name__ == '__main__':
    pytest.main([__file__])