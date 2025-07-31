"""
Custom exception classes for Phoenix Hydra System Review Tool

This module defines a hierarchy of custom exceptions for different error types
that can occur during system review operations, providing structured error
handling and recovery mechanisms.
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """Categories of errors that can occur"""
    DISCOVERY = "discovery"
    ANALYSIS = "analysis"
    ASSESSMENT = "assessment"
    REPORTING = "reporting"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"


class SystemReviewError(Exception):
    """Base exception class for all Phoenix System Review errors"""
    
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        phase: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.DISCOVERY,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.component = component
        self.phase = phase
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.recoverable = recoverable
        
    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}]"]
        if self.component:
            parts.append(f"Component: {self.component}")
        if self.phase:
            parts.append(f"Phase: {self.phase}")
        parts.append(self.message)
        return " - ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "component": self.component,
            "phase": self.phase,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "recoverable": self.recoverable
        }


class DiscoveryError(SystemReviewError):
    """Errors that occur during the discovery phase"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.DISCOVERY)
        kwargs.setdefault('phase', 'discovery')
        super().__init__(message, **kwargs)


class FileSystemError(DiscoveryError):
    """Errors related to file system operations"""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        kwargs.setdefault('category', ErrorCategory.FILE_SYSTEM)
        if file_path:
            kwargs.setdefault('context', {}).update({'file_path': file_path})
        if operation:
            kwargs.setdefault('context', {}).update({'operation': operation})
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation


class ConfigurationParsingError(DiscoveryError):
    """Errors that occur when parsing configuration files"""
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        line_number: Optional[int] = None,
        **kwargs
    ):
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        if config_file:
            kwargs.setdefault('context', {}).update({'config_file': config_file})
        if line_number:
            kwargs.setdefault('context', {}).update({'line_number': line_number})
        super().__init__(message, **kwargs)
        self.config_file = config_file
        self.line_number = line_number


class ServiceDiscoveryError(DiscoveryError):
    """Errors that occur during service discovery"""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        if service_name:
            kwargs.setdefault('context', {}).update({'service_name': service_name})
        if endpoint:
            kwargs.setdefault('context', {}).update({'endpoint': endpoint})
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.endpoint = endpoint


class AnalysisError(SystemReviewError):
    """Errors that occur during the analysis phase"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.ANALYSIS)
        kwargs.setdefault('phase', 'analysis')
        super().__init__(message, **kwargs)


class ComponentEvaluationError(AnalysisError):
    """Errors that occur when evaluating individual components"""
    
    def __init__(
        self,
        message: str,
        component_name: Optional[str] = None,
        criteria_id: Optional[str] = None,
        **kwargs
    ):
        if component_name:
            kwargs.setdefault('component', component_name)
            kwargs.setdefault('context', {}).update({'component_name': component_name})
        if criteria_id:
            kwargs.setdefault('context', {}).update({'criteria_id': criteria_id})
        super().__init__(message, **kwargs)
        self.component_name = component_name
        self.criteria_id = criteria_id


class DependencyAnalysisError(AnalysisError):
    """Errors that occur during dependency analysis"""
    
    def __init__(
        self,
        message: str,
        dependency_chain: Optional[List[str]] = None,
        **kwargs
    ):
        if dependency_chain:
            kwargs.setdefault('context', {}).update({'dependency_chain': dependency_chain})
        super().__init__(message, **kwargs)
        self.dependency_chain = dependency_chain


class QualityAssessmentError(AnalysisError):
    """Errors that occur during quality assessment"""
    
    def __init__(
        self,
        message: str,
        assessment_type: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs
    ):
        if assessment_type:
            kwargs.setdefault('context', {}).update({'assessment_type': assessment_type})
        if file_path:
            kwargs.setdefault('context', {}).update({'file_path': file_path})
        super().__init__(message, **kwargs)
        self.assessment_type = assessment_type
        self.file_path = file_path


class AssessmentError(SystemReviewError):
    """Errors that occur during the assessment phase"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.ASSESSMENT)
        kwargs.setdefault('phase', 'assessment')
        super().__init__(message, **kwargs)


class GapAnalysisError(AssessmentError):
    """Errors that occur during gap analysis"""
    
    def __init__(
        self,
        message: str,
        analysis_type: Optional[str] = None,
        **kwargs
    ):
        if analysis_type:
            kwargs.setdefault('context', {}).update({'analysis_type': analysis_type})
        super().__init__(message, **kwargs)
        self.analysis_type = analysis_type


class CompletionCalculationError(AssessmentError):
    """Errors that occur during completion percentage calculation"""
    
    def __init__(
        self,
        message: str,
        calculation_type: Optional[str] = None,
        component_scores: Optional[Dict[str, float]] = None,
        **kwargs
    ):
        if calculation_type:
            kwargs.setdefault('context', {}).update({'calculation_type': calculation_type})
        if component_scores:
            kwargs.setdefault('context', {}).update({'component_scores': component_scores})
        super().__init__(message, **kwargs)
        self.calculation_type = calculation_type
        self.component_scores = component_scores


class PriorityRankingError(AssessmentError):
    """Errors that occur during task priority ranking"""
    
    def __init__(
        self,
        message: str,
        ranking_criteria: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        if ranking_criteria:
            kwargs.setdefault('context', {}).update({'ranking_criteria': ranking_criteria})
        super().__init__(message, **kwargs)
        self.ranking_criteria = ranking_criteria


class ReportingError(SystemReviewError):
    """Errors that occur during the reporting phase"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.REPORTING)
        kwargs.setdefault('phase', 'reporting')
        super().__init__(message, **kwargs)


class TODOGenerationError(ReportingError):
    """Errors that occur during TODO checklist generation"""
    
    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        **kwargs
    ):
        if template_name:
            kwargs.setdefault('context', {}).update({'template_name': template_name})
        super().__init__(message, **kwargs)
        self.template_name = template_name


class StatusReportError(ReportingError):
    """Errors that occur during status report generation"""
    
    def __init__(
        self,
        message: str,
        report_type: Optional[str] = None,
        **kwargs
    ):
        if report_type:
            kwargs.setdefault('context', {}).update({'report_type': report_type})
        super().__init__(message, **kwargs)
        self.report_type = report_type


class RecommendationError(ReportingError):
    """Errors that occur during recommendation generation"""
    
    def __init__(
        self,
        message: str,
        recommendation_type: Optional[str] = None,
        **kwargs
    ):
        if recommendation_type:
            kwargs.setdefault('context', {}).update({'recommendation_type': recommendation_type})
        super().__init__(message, **kwargs)
        self.recommendation_type = recommendation_type


class ValidationError(SystemReviewError):
    """Errors that occur during data validation"""
    
    def __init__(
        self,
        message: str,
        validation_type: Optional[str] = None,
        invalid_data: Optional[Any] = None,
        **kwargs
    ):
        kwargs.setdefault('category', ErrorCategory.VALIDATION)
        if validation_type:
            kwargs.setdefault('context', {}).update({'validation_type': validation_type})
        if invalid_data is not None:
            kwargs.setdefault('context', {}).update({'invalid_data': str(invalid_data)})
        super().__init__(message, **kwargs)
        self.validation_type = validation_type
        self.invalid_data = invalid_data


class NetworkError(SystemReviewError):
    """Errors that occur during network operations"""
    
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        if url:
            kwargs.setdefault('context', {}).update({'url': url})
        if status_code:
            kwargs.setdefault('context', {}).update({'status_code': status_code})
        super().__init__(message, **kwargs)
        self.url = url
        self.status_code = status_code


class CriticalSystemError(SystemReviewError):
    """Critical errors that prevent system review from continuing"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('severity', ErrorSeverity.CRITICAL)
        kwargs.setdefault('recoverable', False)
        super().__init__(message, **kwargs)


class RecoverableError(SystemReviewError):
    """Errors that can be recovered from with graceful degradation"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('recoverable', True)
        super().__init__(message, **kwargs)


# Exception mapping for different error types
ERROR_TYPE_MAPPING = {
    'file_not_found': FileSystemError,
    'permission_denied': FileSystemError,
    'invalid_config': ConfigurationParsingError,
    'service_unavailable': ServiceDiscoveryError,
    'network_timeout': NetworkError,
    'validation_failed': ValidationError,
    'component_evaluation_failed': ComponentEvaluationError,
    'dependency_cycle': DependencyAnalysisError,
    'calculation_error': CompletionCalculationError,
    'report_generation_failed': ReportingError,
}


def create_error(
    error_type: str,
    message: str,
    **kwargs
) -> SystemReviewError:
    """Factory function to create appropriate error type"""
    error_class = ERROR_TYPE_MAPPING.get(error_type, SystemReviewError)
    return error_class(message, **kwargs)


def is_recoverable_error(error: Exception) -> bool:
    """Check if an error is recoverable"""
    if isinstance(error, SystemReviewError):
        return error.recoverable
    # Non-SystemReviewError exceptions are considered recoverable by default
    return True


def get_error_severity(error: Exception) -> ErrorSeverity:
    """Get the severity level of an error"""
    if isinstance(error, SystemReviewError):
        return error.severity
    # Default severity for non-SystemReviewError exceptions
    return ErrorSeverity.MEDIUM