"""
Unit tests for Core Components (interfaces, error handling, logging)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import logging
from datetime import datetime

from phoenix_system_review.core.exceptions import (
    SystemReviewError, DiscoveryError, AnalysisError, AssessmentError, ReportingError
)
from phoenix_system_review.core.error_handler import ErrorHandler
from phoenix_system_review.core.logging_system import LoggingSystem
from phoenix_system_review.core.config_validator import ConfigValidator
from phoenix_system_review.models.data_models import Component, ComponentCategory, EvaluationResult


class TestSystemReviewExceptions:
    """Test cases for custom exceptions"""
    
    def test_system_review_error_creation(self):
        """Test creating SystemReviewError"""
        error = SystemReviewError(
            component="test-component",
            phase="discovery",
            message="Test error message"
        )
        
        assert error.component == "test-component"
        assert error.phase == "discovery"
        assert error.message == "Test error message"
        assert str(error) == "Test error message"
    
    def test_discovery_error_inheritance(self):
        """Test that DiscoveryError inherits from SystemReviewError"""
        error = DiscoveryError(
            component="test-component",
            phase="file_scanning",
            message="File not found"
        )
        
        assert isinstance(error, SystemReviewError)
        assert error.component == "test-component"
        assert error.phase == "file_scanning"
        assert error.message == "File not found"
    
    def test_analysis_error_inheritance(self):
        """Test that AnalysisError inherits from SystemReviewError"""
        error = AnalysisError(
            component="test-component",
            phase="evaluation",
            message="Evaluation failed"
        )
        
        assert isinstance(error, SystemReviewError)
        assert error.component == "test-component"
        assert error.phase == "evaluation"
    
    def test_assessment_error_inheritance(self):
        """Test that AssessmentError inherits from SystemReviewError"""
        error = AssessmentError(
            component="test-component",
            phase="gap_analysis",
            message="Gap analysis failed"
        )
        
        assert isinstance(error, SystemReviewError)
        assert error.component == "test-component"
        assert error.phase == "gap_analysis"
    
    def test_reporting_error_inheritance(self):
        """Test that ReportingError inherits from SystemReviewError"""
        error = ReportingError(
            component="test-component",
            phase="report_generation",
            message="Report generation failed"
        )
        
        assert isinstance(error, SystemReviewError)
        assert error.component == "test-component"
        assert error.phase == "report_generation"


class TestErrorHandler:
    """Test cases for ErrorHandler"""
    
    @pytest.fixture
    def error_handler(self):
        """Create ErrorHandler instance"""
        return ErrorHandler()
    
    def test_handle_discovery_error(self, error_handler):
        """Test handling discovery errors"""
        test_error = Exception("File not found")
        context = "scanning /src directory"
        
        result = error_handler.handle_discovery_error(test_error, context)
        
        # Should return None or partial results for graceful degradation
        assert result is None or isinstance(result, dict)
    
    def test_handle_analysis_error(self, error_handler):
        """Test handling analysis errors"""
        component = Component(
            name="test-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/test"
        )
        
        test_error = Exception("Analysis failed")
        
        result = error_handler.handle_analysis_error(test_error, component)
        
        # Should return None or a fallback EvaluationResult
        assert result is None or isinstance(result, EvaluationResult)
        
        if isinstance(result, EvaluationResult):
            assert result.component == component
            assert result.completion_percentage == 0.0
    
    def test_handle_assessment_error(self, error_handler):
        """Test handling assessment errors"""
        test_error = Exception("Assessment failed")
        context = "calculating completion percentage"
        
        result = error_handler.handle_assessment_error(test_error, context)
        
        # Should return None or fallback assessment data
        assert result is None or isinstance(result, dict)
    
    @patch('phoenix_system_review.core.logging_system.LoggingSystem.get_logger')
    def test_log_error(self, mock_get_logger, error_handler):
        """Test logging errors"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        test_error = Exception("Test error")
        context = "test context"
        severity = "ERROR"
        
        error_handler.log_error(test_error, context, severity)
        
        # Should call the logger with appropriate level
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test context" in call_args
        assert "Test error" in call_args
    
    def test_create_fallback_evaluation_result(self, error_handler):
        """Test creating fallback evaluation result"""
        component = Component(
            name="failed-component",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/src/failed"
        )
        
        fallback_result = error_handler.create_fallback_evaluation_result(component)
        
        assert isinstance(fallback_result, EvaluationResult)
        assert fallback_result.component == component
        assert fallback_result.completion_percentage == 0.0
        assert fallback_result.quality_score == 0.0
        assert len(fallback_result.criteria_met) == 0
        assert len(fallback_result.issues) > 0  # Should have error issue
    
    def test_should_retry_operation(self, error_handler):
        """Test determining if operation should be retried"""
        # Transient errors should be retried
        transient_error = ConnectionError("Connection refused")
        assert error_handler.should_retry_operation(transient_error) is True
        
        # Permanent errors should not be retried
        permanent_error = ValueError("Invalid configuration")
        assert error_handler.should_retry_operation(permanent_error) is False
        
        # File not found errors should not be retried
        file_error = FileNotFoundError("File not found")
        assert error_handler.should_retry_operation(file_error) is False


class TestLoggingSystem:
    """Test cases for LoggingSystem"""
    
    @pytest.fixture
    def logging_system(self):
        """Create LoggingSystem instance"""
        return LoggingSystem()
    
    def test_get_logger(self, logging_system):
        """Test getting a logger instance"""
        logger = logging_system.get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "phoenix_system_review.test_module"
    
    def test_configure_logging(self, logging_system):
        """Test configuring logging system"""
        config = {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "handlers": ["console", "file"]
        }
        
        # Should not raise an exception
        logging_system.configure_logging(config)
        
        # Verify logger configuration
        logger = logging_system.get_logger("test")
        assert logger.level <= logging.DEBUG
    
    def test_log_performance_metrics(self, logging_system):
        """Test logging performance metrics"""
        metrics = {
            "operation": "component_evaluation",
            "duration_ms": 150.5,
            "component_count": 10,
            "memory_usage_mb": 45.2
        }
        
        with patch.object(logging_system, 'get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_system.log_performance_metrics(metrics)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "component_evaluation" in call_args
            assert "150.5" in call_args
    
    def test_log_system_event(self, logging_system):
        """Test logging system events"""
        event = {
            "event_type": "discovery_started",
            "timestamp": datetime.now(),
            "details": {"root_path": "/src", "include_patterns": ["*.py"]}
        }
        
        with patch.object(logging_system, 'get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            logging_system.log_system_event(event)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "discovery_started" in call_args
    
    def test_create_structured_log_entry(self, logging_system):
        """Test creating structured log entries"""
        entry = logging_system.create_structured_log_entry(
            level="INFO",
            message="Test message",
            component="test-component",
            operation="test-operation",
            metadata={"key": "value"}
        )
        
        assert isinstance(entry, dict)
        assert entry["level"] == "INFO"
        assert entry["message"] == "Test message"
        assert entry["component"] == "test-component"
        assert entry["operation"] == "test-operation"
        assert entry["metadata"]["key"] == "value"
        assert "timestamp" in entry


class TestConfigValidator:
    """Test cases for ConfigValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create ConfigValidator instance"""
        return ConfigValidator()
    
    def test_validate_evaluation_criteria_config(self, validator):
        """Test validating evaluation criteria configuration"""
        valid_config = {
            "infrastructure": {
                "api_endpoints": {
                    "weight": 1.0,
                    "is_critical": True,
                    "description": "API endpoints are properly defined"
                },
                "health_checks": {
                    "weight": 0.8,
                    "is_critical": False,
                    "description": "Health check endpoints exist"
                }
            }
        }
        
        issues = validator.validate_evaluation_criteria_config(valid_config)
        assert len(issues) == 0
        
        invalid_config = {
            "infrastructure": {
                "invalid_criterion": {
                    "weight": "invalid",  # Should be float
                    "is_critical": "yes",  # Should be boolean
                    # Missing description
                }
            }
        }
        
        issues = validator.validate_evaluation_criteria_config(invalid_config)
        assert len(issues) > 0
        assert any("weight" in issue for issue in issues)
        assert any("is_critical" in issue for issue in issues)
        assert any("description" in issue for issue in issues)
    
    def test_validate_component_weights_config(self, validator):
        """Test validating component weights configuration"""
        valid_weights = {
            "infrastructure": 0.35,
            "monetization": 0.25,
            "automation": 0.20,
            "documentation": 0.10,
            "testing": 0.05,
            "security": 0.05
        }
        
        issues = validator.validate_component_weights_config(valid_weights)
        assert len(issues) == 0
        
        # Test weights that don't sum to 1.0
        invalid_weights = {
            "infrastructure": 0.5,
            "monetization": 0.3,
            "automation": 0.3  # Sum = 1.1, should be 1.0
        }
        
        issues = validator.validate_component_weights_config(invalid_weights)
        assert len(issues) > 0
        assert any("sum" in issue.lower() for issue in issues)
    
    def test_validate_service_endpoints_config(self, validator):
        """Test validating service endpoints configuration"""
        valid_endpoints = {
            "phoenix-core": "http://localhost:8080/health",
            "n8n": "http://localhost:5678",
            "windmill": "http://localhost:8000"
        }
        
        issues = validator.validate_service_endpoints_config(valid_endpoints)
        assert len(issues) == 0
        
        invalid_endpoints = {
            "invalid-service": "not-a-url",
            "empty-service": "",
            "missing-protocol": "localhost:8080"
        }
        
        issues = validator.validate_service_endpoints_config(invalid_endpoints)
        assert len(issues) > 0
        assert any("url" in issue.lower() for issue in issues)
    
    def test_validate_priority_rules_config(self, validator):
        """Test validating priority rules configuration"""
        valid_rules = {
            "impact_weights": {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            },
            "category_multipliers": {
                "security": 1.2,
                "infrastructure": 1.0,
                "monetization": 0.9,
                "automation": 0.8,
                "documentation": 0.6,
                "testing": 0.5
            },
            "effort_thresholds": {
                "small": 8,
                "medium": 24,
                "large": 40
            }
        }
        
        issues = validator.validate_priority_rules_config(valid_rules)
        assert len(issues) == 0
        
        invalid_rules = {
            "impact_weights": {
                "critical": "high",  # Should be numeric
                "high": -0.5  # Should be positive
            },
            "category_multipliers": {},  # Should not be empty
            # Missing effort_thresholds
        }
        
        issues = validator.validate_priority_rules_config(invalid_rules)
        assert len(issues) > 0
    
    def test_validate_complete_configuration(self, validator):
        """Test validating complete system configuration"""
        complete_config = {
            "evaluation_criteria": {
                "infrastructure": {
                    "api_endpoints": {
                        "weight": 1.0,
                        "is_critical": True,
                        "description": "API endpoints exist"
                    }
                }
            },
            "component_weights": {
                "infrastructure": 0.4,
                "monetization": 0.3,
                "automation": 0.2,
                "documentation": 0.1
            },
            "service_endpoints": {
                "phoenix-core": "http://localhost:8080/health"
            },
            "priority_rules": {
                "impact_weights": {
                    "critical": 1.0,
                    "high": 0.8,
                    "medium": 0.6,
                    "low": 0.4
                },
                "category_multipliers": {
                    "security": 1.2,
                    "infrastructure": 1.0
                },
                "effort_thresholds": {
                    "small": 8,
                    "medium": 24,
                    "large": 40
                }
            }
        }
        
        is_valid, issues = validator.validate_complete_configuration(complete_config)
        
        assert is_valid is True
        assert len(issues) == 0
    
    def test_get_configuration_schema(self, validator):
        """Test getting configuration schema"""
        schema = validator.get_configuration_schema()
        
        assert isinstance(schema, dict)
        assert "evaluation_criteria" in schema
        assert "component_weights" in schema
        assert "service_endpoints" in schema
        assert "priority_rules" in schema
        
        # Each section should have type and properties
        for section in schema.values():
            assert "type" in section
            assert "properties" in section or "items" in section


if __name__ == '__main__':
    pytest.main([__file__])